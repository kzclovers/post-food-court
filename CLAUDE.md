# Portable software-repo harness

## Project

- Food Court is a browser-packaged Pygame game about logical fallacies. Python 3.11, pygame-ce, and Pygbag are the stack; pip installs from `requirements.txt`.
- Prefer the existing style of the repo you landed in.

## Commands

- Install: `py -3.11 -m venv .venv`, activate it, then `python -m pip install -r requirements.txt`.
- Desktop run: `python main.py`.
- Browser preview: from the parent directory, `python -m pygbag "TEST-Food-Court"`.
- Test: `python -m unittest discover -s tests`.
- Run relevant checks before finishing a task. Loop until they pass.

## Conventions

- Surgical diffs; no drive-by refactors.
- Do not commit secrets, `.env`, keys, or credentials.
- Match existing formatting.

## PRs

- Title and description should say why, not dump the diff.
- Do not force-push main/master.

Claude Code: `CLAUDE.md` should symlink to this file after copy (`ln -sfn AGENTS.md CLAUDE.md`).
