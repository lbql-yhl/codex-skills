#!/usr/bin/env python3
"""Index GitHub repositories and their SKILL.md files into a local JSON memory."""

from __future__ import annotations

import argparse
import base64
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlencode, urlparse
from urllib.request import Request, urlopen

API_ROOT = "https://api.github.com"
DEFAULT_MEMORY_PATH = Path.home() / ".codex" / "memory" / "github-projects.json"
OWNER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")


class GitHubError(RuntimeError):
    """A safe, user-facing GitHub API error that never contains auth headers."""


class GitHubClient:
    def __init__(self, token: str | None = None, timeout: int = 30) -> None:
        self.token = token
        self.timeout = timeout
        self.rate_warning: str | None = None

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = API_ROOT + path
        if params:
            clean = {key: value for key, value in params.items() if value is not None}
            if clean:
                url += "?" + urlencode(clean)
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "github-project-memory-skill",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(url, headers=headers, method="GET")
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
                self._observe_rate_limit(response.headers)
        except HTTPError as exc:
            self._observe_rate_limit(exc.headers)
            message = self._error_message(exc)
            if exc.code == 401:
                raise GitHubError("GitHub 认证失败，请重新登录或检查本地令牌。") from None
            if exc.code == 403:
                raise GitHubError(f"GitHub 拒绝了请求（403）：{message}") from None
            if exc.code == 404:
                raise GitHubError("GitHub 找不到目标资源，或当前账号无权查看它。") from None
            raise GitHubError(f"GitHub API 请求失败（HTTP {exc.code}）：{message}") from None
        except URLError as exc:
            raise GitHubError(f"无法连接 GitHub：{exc.reason}") from None
        except TimeoutError:
            raise GitHubError("连接 GitHub 超时，请稍后重试。") from None
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise GitHubError("GitHub 返回了无法解析的响应。") from exc

    def _observe_rate_limit(self, headers: Any) -> None:
        value = headers.get("X-RateLimit-Remaining") or headers.get("x-ratelimit-remaining")
        try:
            remaining = int(value)
        except (TypeError, ValueError):
            return
        if remaining <= 10 and self.rate_warning is None:
            self.rate_warning = f"GitHub API 剩余请求次数较低（{remaining}）。"

    @staticmethod
    def _error_message(exc: HTTPError) -> str:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
            message = payload.get("message")
            return str(message) if message else "请检查权限和请求参数"
        except Exception:
            return "请检查权限和请求参数"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def memory_path(value: str | None) -> Path:
    configured = value or os.environ.get("GITHUB_PROJECT_MEMORY_PATH")
    return Path(configured).expanduser() if configured else DEFAULT_MEMORY_PATH


def parse_owner(value: str) -> str:
    """Accept a GitHub username or a github.com profile URL and return the username."""
    raw = value.strip()
    if raw.startswith("@"):  # convenient, but still explicit user input
        raw = raw[1:]
    if "://" in raw or raw.startswith("www."):
        candidate = raw if "://" in raw else "https://" + raw
        parsed = urlparse(candidate)
        if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
            raise ValueError("只支持 github.com 的用户主页 URL。")
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) != 1:
            raise ValueError("请输入 GitHub 用户名，或形如 https://github.com/用户名 的主页 URL。")
        raw = parts[0]
    if not OWNER_RE.fullmatch(raw):
        raise ValueError("GitHub 用户名格式不合法。")
    return raw


def discover_token() -> tuple[str | None, str | None]:
    """Find a token without ever printing it or writing it to the memory file."""
    for variable in ("GITHUB_TOKEN", "GH_TOKEN"):
        value = os.environ.get(variable, "").strip()
        if value:
            return value, variable
    gh = shutil.which("gh")
    if gh:
        try:
            result = subprocess.run(
                [gh, "auth", "token"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=10,
                check=False,
            )
            value = result.stdout.strip()
            if result.returncode == 0 and value:
                return value, "gh auth token"
        except (OSError, subprocess.SubprocessError):
            pass
    return None, None


def paginate(client: GitHubClient, path: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    page = 1
    results: list[dict[str, Any]] = []
    while True:
        payload = client.get(path, {**params, "page": page, "per_page": 100})
        if not isinstance(payload, list):
            raise GitHubError("GitHub 返回的仓库列表格式不正确。")
        results.extend(item for item in payload if isinstance(item, dict))
        if len(payload) < 100:
            return results
        page += 1


def parse_skill_frontmatter(text: str, fallback_name: str) -> tuple[str, str]:
    """Extract name and description from the frontmatter of a SKILL.md file."""
    lines = text.replace("\r\n", "\n").splitlines()
    name = ""
    description = ""
    if lines and lines[0].strip() == "---":
        end = next((index for index in range(1, len(lines)) if lines[index].strip() == "---"), len(lines))
        frontmatter = lines[1:end]
        for index, line in enumerate(frontmatter):
            name_match = re.match(r"^\s*name\s*:\s*(.*?)\s*$", line, re.IGNORECASE)
            if name_match:
                name = name_match.group(1).strip().strip("\"'")
                continue
            description_match = re.match(r"^\s*description\s*:\s*(.*?)\s*$", line, re.IGNORECASE)
            if description_match:
                value = description_match.group(1).strip().strip("\"'")
                if value in {">", ">-", ">+", "|", "|-", "|+"}:
                    continuation: list[str] = []
                    for following in frontmatter[index + 1 :]:
                        if re.match(r"^\s*[A-Za-z0-9_-]+\s*:", following):
                            break
                        if following.strip():
                            continuation.append(following.strip())
                    value = " ".join(continuation)
                description = value
    if not name:
        heading = next((line.strip().lstrip("#").strip() for line in lines if line.strip().startswith("#")), "")
        name = heading or fallback_name
    if not description:
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith(("#", "---")):
                description = stripped[:500]
                break
    return name[:200], description[:1000]


def skill_records_from_tree(
    client: GitHubClient,
    owner: str,
    repo: str,
    tree: list[dict[str, Any]],
    warnings: list[str],
) -> list[dict[str, Any]]:
    paths = sorted(
        str(item.get("path"))
        for item in tree
        if item.get("type") == "blob" and isinstance(item.get("path"), str)
    )
    skill_paths = [path for path in paths if posixpath.basename(path).lower() == "skill.md"]
    path_set = set(paths)
    records: list[dict[str, Any]] = []
    for skill_path in skill_paths:
        parent = posixpath.dirname(skill_path)
        fallback = posixpath.basename(parent) or repo
        try:
            payload = client.get(f"/repos/{quote(owner, safe='')}/{quote(repo, safe='')}/contents/{quote(skill_path, safe='/')}")
            content = ""
            if isinstance(payload, dict) and payload.get("encoding") == "base64":
                content = base64.b64decode(str(payload.get("content", "")), validate=False).decode("utf-8", errors="replace")
            name, description = parse_skill_frontmatter(content, fallback)
        except (GitHubError, ValueError, base64.binascii.Error) as exc:
            warnings.append(f"{owner}/{repo}:{skill_path} 无法读取 Skill 元数据（{exc}）。")
            name, description = fallback, ""
        ref_prefix = f"{parent}/references/" if parent else "references/"
        script_prefix = f"{parent}/scripts/" if parent else "scripts/"
        records.append(
            {
                "name": name,
                "description": description,
                "path": skill_path,
                "references": [path for path in paths if path.startswith(ref_prefix) and path in path_set],
                "scripts": [path for path in paths if path.startswith(script_prefix) and path in path_set],
            }
        )
    return records


def scan_repositories(owner_value: str, scope: str, path_value: str | None = None) -> dict[str, Any]:
    owner = parse_owner(owner_value)
    token, token_source = discover_token()
    warnings: list[str] = []
    client = GitHubClient(token)
    authenticated_user: str | None = None
    if token:
        try:
            user = client.get("/user")
            if isinstance(user, dict):
                authenticated_user = str(user.get("login") or "") or None
        except GitHubError:
            if scope == "all":
                raise GitHubError("当前本地 GitHub 登录无效，无法扫描 private/all 仓库。请重新执行 gh auth login。") from None
            warnings.append("本地认证令牌验证失败；本次已改用公开 GitHub API。")
            client = GitHubClient(None)
    if scope == "all":
        if not token or not authenticated_user:
            raise GitHubError("扫描 scope=all 需要已认证的 GitHub 账号，请先执行 gh auth login 或设置 GITHUB_TOKEN。")
        if authenticated_user.lower() != owner.lower():
            raise GitHubError(f"已登录账号是 {authenticated_user}，但请求扫描的是 {owner}。为避免越权，请明确切换到目标账号后再扫描。")
        repos = paginate(client, "/user/repos", {"visibility": "all", "affiliation": "owner", "sort": "updated"})
    else:
        repos = paginate(client, f"/users/{quote(owner, safe='')}/repos", {"type": "public", "sort": "updated"})
    if client.rate_warning:
        warnings.append(client.rate_warning)

    records: list[dict[str, Any]] = []
    for repo in repos:
        name = str(repo.get("name") or "")
        if not name:
            continue
        full_name = str(repo.get("full_name") or f"{owner}/{name}")
        repo_warnings: list[str] = []
        branch = str(repo.get("default_branch") or "main")
        skills: list[dict[str, Any]] = []
        try:
            tree_payload = client.get(
                f"/repos/{quote(owner, safe='')}/{quote(name, safe='')}/git/trees/{quote(branch, safe='')}",
                {"recursive": "1"},
            )
            tree_items = tree_payload.get("tree", []) if isinstance(tree_payload, dict) else []
            if not isinstance(tree_items, list):
                tree_items = []
            if isinstance(tree_payload, dict) and tree_payload.get("truncated"):
                repo_warnings.append("Git tree 被 GitHub 截断，Skill 清单可能不完整。")
            skills = skill_records_from_tree(client, owner, name, tree_items, repo_warnings)
        except GitHubError as exc:
            repo_warnings.append(f"无法扫描 Git tree：{exc}")
        if repo_warnings:
            warnings.extend(f"{full_name}: {item}" for item in repo_warnings)
        records.append(
            {
                "full_name": full_name,
                "visibility": "private" if bool(repo.get("private")) else "public",
                "private": bool(repo.get("private")),
                "html_url": repo.get("html_url") or f"https://github.com/{full_name}",
                "description": repo.get("description") or "",
                "default_branch": branch,
                "updated_at": repo.get("updated_at"),
                "skills": skills,
            }
        )
    memory = {
        "schema_version": 1,
        "owner": owner,
        "authenticated_user": authenticated_user,
        "scope": scope,
        "scanned_at": utc_now(),
        "repositories": records,
        "warnings": warnings,
    }
    save_memory(memory, path_value)
    return memory


def save_memory(memory: dict[str, Any], path_value: str | None = None) -> Path:
    destination = memory_path(path_value)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(memory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(destination)
    return destination


def load_memory(path_value: str | None = None) -> dict[str, Any]:
    destination = memory_path(path_value)
    if not destination.is_file():
        raise GitHubError(f"本地记忆不存在：{destination}。请先执行 scan。")
    try:
        payload = json.loads(destination.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GitHubError(f"无法读取本地记忆：{destination}（{exc}）。") from None
    if not isinstance(payload, dict) or not isinstance(payload.get("repositories"), list):
        raise GitHubError("本地记忆格式不受支持，请重新执行 scan。")
    return payload


def find_matches(memory: dict[str, Any], query: str) -> dict[str, list[dict[str, Any]]]:
    needle = query.strip().casefold()
    if not needle:
        return {"repositories": [], "skills": []}
    repositories: list[dict[str, Any]] = []
    skills: list[dict[str, Any]] = []
    for repo in memory.get("repositories", []):
        if not isinstance(repo, dict):
            continue
        repo_text = " ".join(str(repo.get(key) or "") for key in ("full_name", "description", "html_url")).casefold()
        if needle in repo_text:
            repositories.append(repo)
        for skill in repo.get("skills", []):
            if not isinstance(skill, dict):
                continue
            skill_text = " ".join(str(skill.get(key) or "") for key in ("name", "description", "path")).casefold()
            if needle in skill_text or needle in str(repo.get("full_name") or "").casefold():
                skills.append({"repository": repo.get("full_name"), **skill})
    return {"repositories": repositories, "skills": skills}


def print_inventory(memory: dict[str, Any]) -> None:
    repos = memory.get("repositories", [])
    skill_count = sum(len(repo.get("skills", [])) for repo in repos if isinstance(repo, dict))
    print(f"账号: {memory.get('owner')}")
    print(f"扫描时间: {memory.get('scanned_at')}")
    print(f"范围: {memory.get('scope')}")
    print(f"项目/仓库: {len(repos)} | Skills: {skill_count}")
    for repo in repos:
        if not isinstance(repo, dict):
            continue
        skills = repo.get("skills", [])
        visibility = repo.get("visibility", "unknown")
        print(f"\n- {repo.get('full_name')} [{visibility}] — {repo.get('description') or '无描述'}")
        print(f"  {repo.get('html_url')}")
        if skills:
            for skill in skills:
                print(f"  Skill: {skill.get('name')} ({skill.get('path')})")
        else:
            print("  Skill: 无")
    warnings = memory.get("warnings") or []
    if warnings:
        print("\n警告:")
        for warning in warnings:
            print(f"- {warning}")


def print_matches(matches: dict[str, list[dict[str, Any]]], query: str) -> None:
    print(f"查询: {query}")
    print(f"匹配仓库: {len(matches['repositories'])} | 匹配 Skills: {len(matches['skills'])}")
    for repo in matches["repositories"]:
        print(f"\n仓库: {repo.get('full_name')} — {repo.get('description') or '无描述'}")
        print(f"  {repo.get('html_url')}")
    for skill in matches["skills"]:
        print(f"\nSkill: {skill.get('name')} @ {skill.get('repository')}")
        print(f"  路径: {skill.get('path')}")
        if skill.get("description"):
            print(f"  说明: {skill.get('description')}")
        if skill.get("references"):
            print(f"  references: {', '.join(skill['references'])}")
        if skill.get("scripts"):
            print(f"  scripts: {', '.join(skill['scripts'])}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="扫描 GitHub 项目和 SKILL.md，并保存本地记忆。")
    subparsers = parser.add_subparsers(dest="command", required=True)
    auth = subparsers.add_parser("auth", help="验证当前 GitHub 登录账号")
    auth.add_argument("--json", action="store_true", help="以 JSON 输出账号信息")
    scan = subparsers.add_parser("scan", help="扫描指定账号的仓库和 Skills")
    scan.add_argument("--owner", required=True, help="GitHub 用户名或用户主页 URL")
    scan.add_argument("--scope", choices=("public", "all"), default="public")
    scan.add_argument("--memory-path", help="覆盖默认本地记忆路径")
    listing = subparsers.add_parser("list", help="从本地记忆列出仓库和 Skills")
    listing.add_argument("--memory-path", help="覆盖默认本地记忆路径")
    find = subparsers.add_parser("find", help="从本地记忆查询仓库或 Skill")
    find.add_argument("query")
    find.add_argument("--memory-path", help="覆盖默认本地记忆路径")
    find.add_argument("--json", action="store_true", help="以 JSON 输出匹配结果")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    try:
        if args.command == "auth":
            token, source = discover_token()
            if not token:
                raise GitHubError("未找到 GitHub 登录凭据。请先执行 gh auth login，或在本地设置 GITHUB_TOKEN/GH_TOKEN。")
            user = GitHubClient(token).get("/user")
            result = {"login": user.get("login") if isinstance(user, dict) else None, "token_source": source}
            if args.json:
                print(json.dumps(result, ensure_ascii=False))
            else:
                print(f"已登录 GitHub 账号: {result['login']}")
                print(f"凭据来源: {source}")
            return 0
        if args.command == "scan":
            memory = scan_repositories(args.owner, args.scope, args.memory_path)
            destination = memory_path(args.memory_path)
            skill_count = sum(len(repo.get("skills", [])) for repo in memory["repositories"])
            print(f"扫描完成：{len(memory['repositories'])} 个仓库，{skill_count} 个 Skill。")
            print(f"本地记忆：{destination}")
            if memory["warnings"]:
                print(f"警告：{len(memory['warnings'])} 条；可查看 list 输出。")
            return 0
        if args.command == "list":
            print_inventory(load_memory(args.memory_path))
            return 0
        if args.command == "find":
            matches = find_matches(load_memory(args.memory_path), args.query)
            if args.json:
                print(json.dumps(matches, ensure_ascii=False, indent=2))
            else:
                print_matches(matches, args.query)
            return 0
    except (GitHubError, ValueError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
