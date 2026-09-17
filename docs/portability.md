# Portability notes

## Directly portable

The five game-development skills are instruction-and-reference packages. Their only runtime requirement is an Agent that supports `SKILL.md` discovery.

## Refactored portable skills

The four workflow skills accept structured inputs rather than reading the original project's SQLite database or calling its browser and notification integrations. Integrators should provide a thin adapter for their own data source and destination.

## Deliberately excluded

The original BOSS/Zhipin browser-operation skills and the 16 UTM/macOS submission skills are not copied into this repository because they depend on live accounts, VM state, host secrets, platform-specific scripts, or project-specific orchestration contracts. They should be distributed as complete application bundles, not as isolated instruction folders.
