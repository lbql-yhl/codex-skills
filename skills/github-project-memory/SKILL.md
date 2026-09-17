---
name: github-project-memory
description: Connect to a specified GitHub account, verify the user's authenticated session, inventory repositories and repository Skills, save a privacy-conscious local memory index, and quickly answer later questions about projects and Skills from that index. Use when the user asks to log in to GitHub, inspect their repositories, remember project/Skill structure, refresh the inventory, or find a known project or Skill quickly.
---

# GitHub project memory

Maintain a local, refreshable index of the GitHub account and repositories the user explicitly names. Use the index for fast follow-up answers instead of rescanning every repository on every turn.

## Safety and authentication

- Treat GitHub login as an account action. Never ask the user to paste a password, recovery code, personal access token, SSH private key, or browser cookies into chat.
- Prefer an existing authenticated `gh` session or an approved browser login. If authentication is missing, tell the user to complete GitHub login in the browser or with `gh auth login`, then verify the account with the helper script.
- Do not save tokens, cookies, credentials, raw repository contents, or private source code in the memory index.
- Only inspect repositories belonging to the owner/account explicitly provided by the user. Do not expand to unrelated organizations or collaborators without explicit scope.
- For private repositories, explain that metadata and Skill paths are being recorded locally and keep the index on the user's machine.

## First use or explicit refresh

1. Resolve the GitHub owner from the user's explicit username or profile URL. If absent, ask for it; do not infer an account from an email address.
2. Check authentication with:

   ```text
   python scripts/github_project_memory.py auth
   ```

3. If the user requested private or all repositories, require an authenticated session. Public-only inventory may use the public GitHub API.
4. Scan the requested account:

   ```text
   python scripts/github_project_memory.py scan --owner <username> --scope all
   ```

   Use `--scope public` when the user only wants public repositories.
5. Report the repository count, Skill count, repositories without Skills, and any rate-limit or truncated-tree warnings.
6. Tell the user where the local memory index was written, without exposing tokens or private file contents.

The helper finds `SKILL.md` files anywhere in each repository and extracts only Skill name, description, path, and lightweight metadata. It recognizes common layouts such as `.codex/skills`, `.agents/skills`, `.opencode/skills`, and `skills`.

## Later use

Before rescanning, load the memory index:

```text
python scripts/github_project_memory.py list
python scripts/github_project_memory.py find <query>
```

Use the saved index when it is present and the user asks a lookup question. Refresh when:

- the user explicitly asks to rescan, update, or check the latest state;
- the index is missing or malformed;
- the user names a repository not in the index;
- the index is older than 7 days and the answer depends on current repository state.

When the index is stale but the user only asks for a quick lookup, answer from memory and clearly state the scan date.

## Response format

For a repository lookup, return:

- repository name and URL;
- visibility and last scanned/updated time when available;
- description;
- discovered Skill names and paths;
- whether the Skill appears portable, project-coupled, or unknown based only on recorded metadata.

For a Skill lookup, return:

- Skill name;
- repository;
- exact path;
- description;
- related references/scripts if recorded;
- a short portability note, avoiding unsupported claims.

For a complete inventory, use a compact table followed by a list of Skills grouped by repository.

## Implementation notes

The bundled helper is intentionally dependency-free Python. It uses an existing `gh` token when available, otherwise a public GitHub API request. Its default memory path is `~/.codex/memory/github-projects.json`; override it with `GITHUB_PROJECT_MEMORY_PATH` or `--memory-path`.

Read `references/memory-schema.md` only when changing the index format or integrating the memory with another tool.
