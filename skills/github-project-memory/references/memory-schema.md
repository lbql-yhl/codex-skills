# Memory schema

The local index is JSON with this shape:

```json
{
  "schema_version": 1,
  "owner": "example",
  "authenticated_user": "example",
  "scope": "public|all",
  "scanned_at": "2026-09-17T00:00:00Z",
  "repositories": [
    {
      "full_name": "example/project",
      "visibility": "public",
      "private": false,
      "html_url": "https://github.com/example/project",
      "description": "...",
      "default_branch": "main",
      "updated_at": "...",
      "skills": [
        {
          "name": "example-skill",
          "description": "...",
          "path": "skills/example-skill/SKILL.md",
          "references": ["skills/example-skill/references/guide.md"],
          "scripts": ["skills/example-skill/scripts/run.py"]
        }
      ]
    }
  ],
  "warnings": []
}
```

Do not add access tokens, cookie values, raw resume data, raw source files, or full private repository contents to this file.
