# Food Court

A mouse-only logical fallacy game. This repository currently contains a playable Level 1 prototype against Vegetable Peeler. The later enemies and full menu are planned in [SPEC.md](SPEC.md).

## Run locally

Use Python **3.11**:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

For the browser build, run Pygbag from this project's **parent** directory. Quote the folder path because it contains spaces:

```powershell
python -m pygbag "TEST-Food-Court"
```

Open the URL printed by Pygbag. Pygbag serves files during local development; the packaged game itself uses WebAssembly and needs no Python server during play. To package for static hosting, use `python -m pygbag --archive "TEST-Food-Court"` from the parent directory. See the [Pygbag quick start](https://pygame-web.github.io/wiki/pygbag/) for hosting options.

The browser build requires a network connection on its first load for Pygbag's runtime assets. Gameplay is local after loading.

To host the browser build on Render, see [DEPLOY.md](DEPLOY.md).

## How the prototype works

The game starts at Level 1. Click **Continue**, read each new teaching card, and click **Add to Dictionary**. Read Vegetable Peeler's claim and click the moving paper that names its fallacy before the 10-second timer expires. Correct answers restore one carrot piece; wrong answers and timeouts remove one. Each fallacy is mastered after three correct identifications. Master all six to win. A completed level can be replayed in infinite mode.

The dictionary (book icon) and Settings (gear icon) open between questions, never while you're actively picking a paper. In the browser, progress is saved in `localStorage`. In the desktop test run, progress is saved to `.food_court_save.json`. Settings offers a confirmed reset of all saved progress.

## Where to revise the game

| File | What to change |
|---|---|
| `game_data.py` | Fallacy names, definitions, examples, explanations, and Peeler's claims |
| `game_rules.py` | Mastery target, question time, teaching cadence, and Quizlet-style weighting |
| `main.py` | Screens, layout, animations, input, sprites, and encounter flow |
| `audio.py` | Temporary generated music and sound effects |
| `progress.py` | Saved fields and browser/desktop persistence |
| `assets/` | Existing art; character frames are cropped from 1024-pixel cells |

The temporary music and sounds are generated in code and can be replaced with audio files later. Dictionary pages are drawn from `game_data.py`: the supplied numbered card images use a different fallacy order, so the prototype does not use them for teaching content.

## Check the rules

```powershell
python -m unittest discover -s tests
```

The first milestone is Level 1 only. The logo-to-menu animation, Knife, Boiling Pot, later fallacies, and their separate tracks belong to future milestones.
