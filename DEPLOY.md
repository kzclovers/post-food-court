# Deploying to Render

Food Court runs in the browser as a [Pygbag](https://pygame-web.github.io/wiki/pygbag/)
build: `python -m pygbag --build .` packages `main.py`, `entities/`, `game_data.py`,
`game_rules.py`, `audio.py`, `progress.py`, and `assets/` into `build/web/`, which
holds exactly three files:

| File | What it is |
|---|---|
| `index.html` | The page. Loads the pygame-web runtime (`pythons.js`, `browserfs.min.js`) from `pygame-web.github.io`, then mounts the `.apk` below. |
| `food-court.apk` | A renamed zip of the project's Python source and `assets/`. Not an Android package — Pygbag's own archive format. |
| `favicon.png` | Tab icon. |

Because the runtime itself is fetched from pygame-web's CDN at load time, Render
only needs to host those three static files — this is a **Static Site**, not a
Python web service, and Render never runs `main.py` itself. This was verified
locally: `python -m pygbag --build .` run from the repo root produces
`build/web/index.html`, `build/web/favicon.png`, and `build/web/food-court.apk`
with no errors, packing all 128 tracked source/asset files.

Players need a network connection on first load (to fetch the CDN runtime);
gameplay is local after that, same as the Pygbag dev server already documented
in [README.md](README.md).

## Option A — Blueprint (recommended)

This repo includes [`render.yaml`](render.yaml), so Render can configure the
service for you:

1. Push this repo to GitHub if it isn't already there (`git remote -v` shows
   `origin` is `https://github.com/kzclovers/TEST-Food-Court.git`).
2. Log in to [dashboard.render.com](https://dashboard.render.com) (create a
   free account if you don't have one — GitHub sign-in is the fastest path).
3. Click **New +** -> **Blueprint**.
4. Connect your GitHub account if prompted, then pick the `TEST-Food-Court`
   repository. Render reads `render.yaml` automatically and shows a preview
   of the one service it will create (`food-court`, a static site).
5. Click **Apply**. Render clones the repo, runs the build command, and
   publishes `build/web/`.
6. When the build finishes (a few minutes — mostly spent downloading the
   pygame-web runtime template and caching it), open the `.onrender.com` URL
   Render gives the service.

Every push to `main` redeploys automatically from then on.

## Option B — Manual static site

If you'd rather not commit to a Blueprint, or want to tweak settings as you
go:

1. Log in to [dashboard.render.com](https://dashboard.render.com).
2. **New +** -> **Static Site**.
3. Connect the `TEST-Food-Court` GitHub repo.
4. Fill in:
   - **Name**: `food-court` (or anything you like — this sets the
     `*.onrender.com` subdomain).
   - **Branch**: `main`.
   - **Build Command**: `pip install pygbag==0.9.2 && python -m pygbag --build .`
   - **Publish Directory**: `build/web`
5. Under **Environment Variables**, add:
   - `PYTHON_VERSION` = `3.11.11`
   - `SKIP_INSTALL_DEPS` = `true`
6. Click **Create Static Site**.

Render's static-site build environment has Python 3 and pip available by
default (confirmed by Render users building other Python-based static sites,
e.g. MkDocs, the same way) — no extra runtime selection is needed. `PYTHON_VERSION`
pins that default to a known-good 3.11.x instead of whatever Render's current
default happens to be. `SKIP_INSTALL_DEPS` turns off Render's own dependency
auto-detection (which runs before the build command and can misread a project
that isn't a typical `requirements.txt`-driven web app), so installing
`pygbag` is entirely up to the build command.

## Notes and troubleshooting

- **Build command**: only `pygbag` is installed, not the full
  `requirements.txt` — `pygame-ce` runs client-side in the browser, never on
  Render's build machine, so installing it there only slows the build down
  (and `SKIP_INSTALL_DEPS` means nothing installs it for you implicitly).
- **First build is slower**: Pygbag downloads and caches a runtime template
  from `pygame-web.github.io` the first time it runs in a fresh environment.
  Render's build cache may or may not persist this between deploys depending
  on your plan; either way it's a one-time cost per build, not per player.
- **Repo size**: the packaged `.apk` is roughly 45 MB, mostly the music
  tracks in `assets/music/`. Well within Render's static-site limits, but
  worth knowing if you add more audio.
- **Changing the app/output name**: Pygbag names the `.apk` after the
  project's folder name (`test-food-court.apk` here, lowercased). If you
  rename the repo, the `.apk` filename changes too, but `index.html`
  references it by the name Pygbag just generated, so nothing needs updating
  by hand.
- **`tests/` and `SPEC.md` ship inside the `.apk`**: Pygbag packs every
  tracked file under the project root, including `tests/`. It's inert dead
  weight in the browser build (nothing imports it at runtime) rather than a
  functional problem, so it's not worth excluding unless the extra few KB
  start to matter.

## What I can't do for you

Creating and configuring the Render service requires signing in to Render
with your own account — I have no Render account access or API token, and I
won't ask you to paste a password or API key into chat. Walk through
Option A or B above in your own browser; if Render shows an error partway
through, paste the error text here and I'll help you fix it.
