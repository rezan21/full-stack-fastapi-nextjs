---
name: library-skills
description: Use Library Skills to discover, install, refresh, repair, check, and manage agent skills from installed packages.
---

# Library Skills

Use this skill when a project might benefit from agent skills bundled by its installed packages, or when existing Library Skills-managed symlinks are stale, broken, orphaned, or need to be checked.

Run commands from the directory that holds the project's dependencies. The tool looks for packages in that directory's `.venv` or `node_modules` and creates its links beneath it.

Agents bundle their own skills by including an `.agents/skills` directory. More details in [Library Skills](https://library-skills.io).

## First-Time Setup

- Make sure project dependencies are installed first, for example with `uv sync` for Python projects or `bun install` for Node.js projects.
- Run `uvx library-skills` or `bunx library-skills` to discover skills bundled by the installed packages and install selected skills interactively.
- Use `uvx library-skills --all` or `bunx library-skills --all` only when all newly discovered skills should be installed without selecting individual skills.
- Use `uvx library-skills --tool-skill` or `bunx library-skills --tool-skill` to copy this Library Skills tool skill into the project so future agents know how to discover, install, update, repair, and check skills.

## Commands

- Run `uvx library-skills` or `bunx library-skills` to discover package-provided skills, install selected new skills, and reconcile existing managed symlinks.
- Run `uvx library-skills list` or `bunx library-skills list` to inspect discovered and installed skills.
- Run `uvx library-skills list --json` or `bunx library-skills list --json` for machine-readable installed status.
- Run `uvx library-skills scan --json` or `bunx library-skills scan --json` for discovery-only automation.
- Run `uvx library-skills --check` or `bunx library-skills --check` to validate managed skill symlink state without changing files.
- Run `uvx library-skills --yes` or `bunx library-skills --yes` to repair stale managed symlinks and remove orphaned managed symlinks non-interactively.
- Add `--claude` when `.claude/skills` should also be managed.
- Add `--skill NAME` to install a specific discovered skill by name.

## In this repository

The FastAPI and SQLModel skills come from the backend's packages, so run the tool from `backend/`. The repo root's `.venv` only holds repo tooling and has no skills to find. The tool is pinned in the root lockfile, so run it through `uv`:

```bash
cd backend
uv sync
uv run --project .. library-skills --claude --yes
uv run --project .. library-skills --check --claude
```

The links land in `backend/.agents/skills` and `backend/.claude/skills`, and the `local-library-skills` pre-commit hook runs the `--check` form. The frontend's packages ship no skills. The skills in the repo root's `.agents/skills` are not managed by this tool.

## Safety

- Prefer rerunning `library-skills` over editing managed symlinks manually.
- If installed skill symlinks are broken, dependencies may not be installed yet. Try the project's normal install command first, such as `uv sync` or `bun install`, then rerun `library-skills`.
- Do not delete or overwrite hand-authored skill directories.
- Library Skills only removes managed symlinks. It should not remove copied or hand-authored skill directories.
