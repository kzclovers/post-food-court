# Food Court — Game Specification

## Concept and objective

Food Court is a fast-paced educational courtroom game about identifying logical fallacies. The player controls a tomato defendant facing kitchen appliances and utensils that shout argumentative claims. The chef is the juror. The player must identify the fallacy in each claim before time runs out, complete all three levels, and defeat all three enemies.

## Screens

### Gameplay screen

- Kitchen background.
- Chef/juror in the center.
- Tomato/player and the current utensil or appliance enemy on opposing sides.
- Five-piece carrot health bar at the top.
- Timer, current progress, and moving answer papers.

### Fallacy dictionary screen

The dictionary is a book containing every fallacy collected so far. Each entry includes the fallacy name and definition. New fallacies are introduced through definition pop-up cards, then added to the dictionary. The dictionary is available between encounters without resetting progress.

## Progression

There are six levels. Each introduces three new fallacies, in this exact order, and each enemy hosts two consecutive levels:

| Level | Enemy | New fallacies | Total available |
|---|---|---|---:|
| 1 | Vegetable Peeler | 1–3 | 3 |
| 2 | Vegetable Peeler | 4–6 | 6 |
| 3 | Knife | 7–9 | 9 |
| 4 | Knife | 10–12 | 12 |
| 5 | Boiling Pot | 13–15 | 15 |
| 6 | Boiling Pot | 16–18 | 18 |

Each level runs in three stages:

1. **Introduction:** all three new fallacy cards appear side by side. The player adds each one to the dictionary.
2. **Warm-up:** one question per new fallacy. Misses and timeouts cost no health; the same fallacy is asked again until answered correctly.
3. **Official round:** questions are drawn from every fallacy unlocked up to and including this level, weighted toward unmastered and frequently missed ones.

Levels unlock in order: a level opens once the previous one is completed.

1. Personal Attack (Ad Hominem) — attacking the person instead of the argument.
2. Bandwagon (Appeal to Popularity) — claiming something is true because many people believe it.
3. Appeal to Pity — using sympathy instead of relevant evidence.
4. Appeal to Irrelevant Authority — treating an unqualified opinion as proof.
5. False Dilemma — presenting only two choices when more possibilities exist.
6. Hasty Generalization — drawing a broad conclusion from too little evidence.
7. Straw Man — distorting an argument to make it easier to attack.
8. Red Herring — introducing an irrelevant issue to distract from the question.
9. Whataboutism (Tu Quoque) — deflecting criticism by pointing to similar wrongdoing.
10. Circular Reasoning — using the conclusion itself as support for the conclusion.
11. Appeal to Ignorance — treating a claim as true because it has not been disproven, or vice versa.
12. False Cause (Post Hoc) — assuming one event caused another because it came first.
13. Slippery Slope — claiming one step will lead to an extreme outcome without enough support.
14. False Analogy — treating two things as equivalent despite important differences.
15. Equivocation — switching between meanings of the same word.
16. Loaded Question — asking a question that assumes an unproven claim.
17. Cherry-Picking — selecting supporting evidence while ignoring relevant contrary evidence.
18. Moving the Goalposts — changing the standard of proof after it has been met.

If a level is failed and restarted, all fallacies already collected in that level and earlier levels remain in the dictionary. Later-level fallacies remain locked.

## Core gameplay loop

1. The prosecution enemy makes a claim containing one logical fallacy.
2. The player reads or hears the claim.
3. Fallacy names appear on papers flying around the screen.
4. The player clicks the matching fallacy before the timer expires.
5. A correct answer shows `CORRECT` and restores or awards health.
6. An incorrect answer or timeout shows `INCORRECT` and removes health.
7. The character that lost the exchange briefly switches to a red sprite and plays a losing animation.
8. The next claim begins.
9. After the available fallacies are mastered, the enemy is defeated and the level is complete.

## Health, timer, and failure

- In main levels, both the player (five carrot pieces, top left) and the opponent (five pips, top right) have health bars. Neither ever heals.
- A wrong answer or timeout in the official round removes one player piece; a correct answer removes one opponent pip.
- The level ends when either bar is empty: the opponent's empty bar completes the level, the player's empty bar fails it. Fallacy mastery is still tracked but no longer decides the win.
- Infinite mode keeps the original rule instead: only the player has a health bar, a correct answer restores one piece (up to five), and a wrong answer removes one.
- The health bar is drawn from the five individual carrot illustrations in `carrot_heath_bar.png`, one distinct illustration per health-piece slot, rather than five copies of a single icon.
- Each claim has its own countdown; a timeout counts as an incorrect answer.
- Completing Level 3 completes the game.

The exact timer length, health restoration amount, and number of correct answers needed to master each fallacy are tuning values. The first prototype may require one correct answer per available fallacy.

## Fallacy learning

When a fallacy is introduced, a pop-up card displays its number, name, definition, and two example claims. After the player dismisses the card, it is added to the dictionary. Mastery requires correctly identifying the fallacy during gameplay; reading the card alone is not mastery.

### Teaching card layout

- A white, rounded-corner card centered on a dark backdrop, with a small orange sparkle/asterisk accent near each of the card's four corners.
- Header row: the fallacy's number and name in large bold text, followed by its parenthetical alternate name (when it has one, e.g. "Bandwagon (Appeal to Popularity)") in smaller bold text on the same line.
- One line of plain text giving the fallacy's definition.
- An "Example" label in bold, followed by two quoted example claims, each demonstrating the fallacy in the current enemy's voice.
- A full-width orange rounded button in title case reading "Add To Your Dictionary" that closes the card and adds the fallacy to the dictionary.

## Difficulty

Answer choices are deliberately not a static multiple-choice list. Papers move around the screen, requiring quick visual search. Early encounters use fewer papers. As the level progresses, more papers appear and movement becomes harder to track, while the correct answer remains readable and clickable.

## Characters and tone

- **Tomato:** player character and defendant.
- **Chef:** central juror.
- **Kitchen appliances and utensils:** prosecution enemies, each with distinct claims and personality.

The game should feel energetic, humorous, and fast-paced while keeping definitions and feedback clear enough to support learning.

## Feedback requirements

Every answer must provide immediate feedback through:

- A `CORRECT` or `INCORRECT` bar that spans the full width of the screen and animates sliding across it, rather than a small centered banner.
- Health bar update.
- A short red losing-character sprite animation.
- A clear transition to the next claim.

The player must always understand whether the answer was correct, why health changed, and when the next challenge begins.

## Asset mapping

| Assets | Use |
|---|---|
| `Background.png`, `background_faded.png` | Kitchen and overlay backgrounds |
| `Chef_SpriteSheet.png` | Chef/juror |
| `Knife_SpriteSheet.png`, `Peeler_SpriteSheet.png`, `Pot_SpriteSheet.png`, `Tomato_SpriteSheet.png` | Tools, enemies, and character animations |
| `DictionaryCard01.png`–`DictionaryCard18.png` | Fallacy introduction/dictionary cards |
| `#01.png`–`#18.png` | Fallacy or encounter illustrations |
| `carrot_heath_bar.png` | Player health UI -- source of the five distinct health-piece illustrations |
| `healthbar_carrot.png` | Unused single carrot icon, kept for reference |
| `dictionary icon.PNG` | Dictionary button |

## First playable milestone

- One enemy and all six Level 1 fallacies are playable.
- Introduction cards add fallacies to the dictionary.
- Claims can be answered by clicking moving fallacy papers.
- Correct, incorrect, timeout, health, and red losing-animation states work.
- Level failure/restart preserves the correct dictionary entries.
- Level completion advances to the next level state.

## Open implementation decisions

- Exact Python web framework and package manager.
- Exact claim text and number of claims per fallacy.
- Timer duration and paper movement patterns.
- Final audio assets and sound direction.

## Confirmed implementation decisions

### Platform and technology

- The game will be written in Python and run in a web browser.
- Interaction is mouse-click only.
- The implementation should use a Python web-compatible game approach and keep gameplay state separate from rendering and UI state.

### Enemy progression

| Level | Enemy |
|---|---|
| 1 | Vegetable peeler |
| 2 | Knife |
| 3 | Boiling pot |

Each level contains one continuous enemy encounter. The encounter continues until the player demonstrates mastery of every fallacy available in that level, similar to a Quizlet learning session.

### Mastery and health

- A fallacy is mastered after three correct guesses involving that fallacy.
- Correct answers restore exactly one carrot health piece, up to the five-piece maximum.
- Incorrect answers remove one carrot health piece.
- Running out of time removes one carrot health piece.
- The player loses the level when all five carrot pieces are depleted.

### Claims and speaker presentation

- Claims appear as readable text rather than relying on voice acting.
- Every enemy creates kitchen-, food-, vegetable-, chef-, tomato-, or enemy-specific claims.
- Claims must be educationally strict: each claim has one clearly correct fallacy and should not be ambiguous.
- Claims may still be humorous.
- A voice box at the bottom of the gameplay screen identifies the current speaker and displays the claim.

### Fallacy introduction and dictionary

- New fallacies are introduced in the order listed in this specification.
- During gameplay, available fallacies may appear in any order.
- A new-fallacy pop-up must include the fallacy number, name, parenthetical alternate name (when applicable), definition, and two example claims, styled as described in [Teaching card layout](#teaching-card-layout).
- The player must click the `Add To Your Dictionary` button to close the pop-up and continue.
- Each dictionary entry contains the fallacy definition and the two example claims shown when the fallacy was introduced.

### Visual direction

The supplied reference screens establish the visual language for the game:

- Warm brown kitchen background with cream paper panels.
- Orange/brown rounded buttons and circular icon buttons.
- Large, friendly, readable typography.
- Menu screen with logo, How to Play, Dictionary, Settings, and Start options.
- Level-select screen with three enemy portraits; later levels can be locked until prior levels are complete.
- Level-failed screen with `LEVEL FAILED`, home, and try-again controls.
- Level-complete screen with `LEVEL COMPLETE`, home, and next-level controls.
- New UI pieces that do not exist in the provided assets should match this paper-and-kitchen visual style.

### Audio

- The game includes sound effects.
- At minimum, provide feedback sounds for selecting an answer, correct answers, incorrect answers, health loss, dictionary confirmation, level failure, and level completion.
- Background music and separate sound-effect volume controls may be included in Settings.

## Finalized technical and interaction decisions

### Runtime

- Use Pygame for the game implementation.
- Package the Pygame game so it runs in the browser without requiring a Python server during gameplay. The browser build must load the game and assets directly.
- Omit the username/profile field from Settings for the first version.

### Opening flow

1. The Food Court logo fills the entire page.
2. The logo transitions/morphs into the main menu.
3. The main menu follows the supplied reference design, including Start, How to Play, Dictionary, and Settings options where implemented.

### Dictionary behavior

- The dictionary is designed as a book with previous-page and next-page controls.
- Pages show collected fallacy names, definitions, and the two example claims shown when the fallacy was first introduced.
- Dictionary progress persists when the player closes and reopens the browser.
- Settings includes a confirmed reset-game action that clears the persisted dictionary and progression. The username/profile control is intentionally omitted for now.

### Answer papers

- Papers move continuously around the gameplay area.
- Every question always has exactly one correct answer.
- Levels 1–2 (Peeler) display one correct answer and three incorrect answers.
- Levels 3–4 (Knife) display one correct answer and five incorrect answers.
- Levels 5–6 (Boiling Pot) display one correct answer and seven incorrect answers.
- Clicking an incorrect paper makes all papers disappear, applies one health-piece of damage, and advances to the feedback/next-question state.
- A correct click also ends the current paper sequence and advances after feedback.

### Fallacy selection and mastery

- The selection system is Quizlet-inspired: unmastered or frequently missed fallacies are weighted more heavily.
- Random review questions are occasionally inserted so the player cannot predict the next fallacy.
- After three correct guesses for a fallacy, a mastery pop-up appears.
- A mastered fallacy remains eligible for review but appears at approximately half its previous frequency.
- The player begins every level with a full five-piece carrot health bar.

### Enemy identities and personalities

Enemy names are simply their object names. Their initial personalities are:

| Level | Enemy | Personality |
|---|---|---|
| 1 | Vegetable Peeler | Nervous, defensive, and eager to redirect blame before anyone notices its scratches. |
| 2 | Knife | Overconfident, sharp-tongued, and convinced that intimidation counts as evidence. |
| 3 | Boiling Pot | Dramatic, impatient, and prone to escalating every small kitchen problem into a catastrophe. |

Each enemy has a unique claim set, even when testing the same fallacy. Claims should reference the enemy’s personality, the kitchen, food, vegetables, the chef, or Tomato.

### Claim presentation

- Claims appear as text in the voice box/text box at the bottom of the gameplay screen.
- The voice box clearly identifies the speaking enemy.
- Claims are not ambiguous: each claim must be authored and reviewed so one fallacy is the defensible answer.

### Audio

- Include background music during menus and gameplay.
- Include sound effects for paper movement/selection, correct answers, incorrect answers, health loss, dictionary additions, mastery, level transitions, failure, and completion.
- Music and sound effects should be independently toggleable or volume-adjustable when Settings is implemented.

## Browser, layout, and timing specifications

- Package the Pygame project for the browser with **Pygbag/WebAssembly**.
- Use a responsive fullscreen layout that scales to the browser viewport.
- Support landscape orientation only. Show a landscape-orientation prompt or pause state when the viewport is portrait.
- Keep the gameplay composition readable at different aspect ratios; do not stretch character sprites non-uniformly.

### Opening transition

- Display the full-page logo opening screen for one second.
- Then morph or transition into the main menu.

### Question timing

- Each question has a ten-second timer.
- When the player clicks a correct answer, papers remain briefly while the correct feedback is displayed.
- `CORRECT` and `INCORRECT` are shown as a full-width bar that animates sliding across the entire screen, remains visible for two seconds, then animates off-screen.
- When the timer reaches zero, all papers disappear and a `TIME OUT` message is shown.
- A timeout is treated as an incorrect result and removes one carrot health piece.

### Paper difficulty

- The number of answer papers may increase as the player progresses through a level.
- The level-specific minimum answer counts remain one correct answer plus three, five, or seven incorrect answers for Levels 1, 2, and 3 respectively.

### Mastery notifications

- When a fallacy reaches three correct guesses, show a non-blocking achievement-style notification near the top of the screen.
- The notification remains visible for a few seconds and must not obscure the claim, answer papers, health bar, or important controls.
- The notification does not pause the question timer.

### Dictionary access

- The dictionary is accessible only between questions, never while the player is actively selecting an answer.
- Navigate dictionary pages with on-screen left/right arrow buttons and clickable page corners.

## Replay and infinite mode

- Completed levels remain replayable in normal mode.
- Dictionary entries, fallacy mastery counts, and level completion data are preserved during replay.
- Infinite mode is its own button at the top of the level-select screen. It unlocks after the first completed level.
- Infinite mode introduces no new fallacies; it quizzes only fallacies already in the dictionary.
- Each question is delivered by a random enemy from the levels completed so far.
- Answer papers start at four (one correct) and grow by one every two correct answers, up to eight.
- Infinite mode gradually shortens the time available for each guess.
- Infinite mode continues until the player loses all carrot health; the best survival time is saved.

## Pause

- Every level and infinite mode has a pause button in the top-left corner. Pausing freezes the timer and hides the answer papers.
- The pause popup offers **Continue** and **Exit Game**. Exiting a main level shows the Level Failed card; exiting infinite mode returns to level select with no popup.

## Character emotion states

- Existing red sprite variants should be used for losing reactions.
- Enemies have multiple emotional/distress variants. The more often an enemy loses, the more distressed its displayed variant becomes.
- Tomato also has multiple emotional/distress variants, using the same progression principle.
- The chef/juror does not animate after every question.
- At the end of a level, whether the player wins or loses, the chef strikes the knife-gavel on the stand before the level-complete or level-failed card appears.

## Persistence and audio placeholders

- Store progression in browser local storage, including dictionary entries, mastery counts, completed levels, and replay/infinite-mode availability.
- The Settings reset action must ask for confirmation before erasing saved progress.
- Generate temporary background music for the initial build so it can be replaced later.
- Generate temporary sound effects for the initial build because no sound-effect files currently exist.

## Prototype scope decisions

- Use Python 3.11 for development.
- Use Pygame for game rendering, input, animation, and audio.
- Use Pygbag to package the Pygame project for browser/WebAssembly execution.
- Infinite mode may reduce the timer to extremely short durations; there is no required minimum timer.
- Save the player’s best infinite-mode survival time in browser local storage.
- Display the best infinite-mode time during the level’s infinite-mode replay/results state.
- The three enemies may each have a distinct background music track.
- In the normal game, new fallacies are introduced gradually throughout the level rather than all at the beginning.
- The first code milestone is a playable Level 1 prototype. The full main menu and broader navigation flow will be added later.

### Level 1 prototype requirements

- Vegetable Peeler is the active enemy.
- The prototype introduces the first six fallacies throughout the level in the specified order.
- Each introduced fallacy receives a pop-up card and must be added to the dictionary before play continues.
- The player can answer claims using one correct and three or more incorrect moving papers.
- Fallacy mastery, carrot health, ten-second questions, feedback bars, timeout handling, enemy emotion variants, and the chef’s end-of-level gavel animation are included.
- The prototype saves dictionary progress, mastery counts, Level 1 completion, and best infinite-mode survival time locally.

## Main menu, level select, and settings screens

- The app boots directly to the main menu, which has How to Play, Dictionary, and Settings links plus a Start button; Start goes to the level-select screen.
- The level-select screen shows a circle per level. Level 1 is always open. Levels 2 and 3 stay locked (no claim content has been written for Knife or Boiling Pot yet) until their claim banks exist, at which point they unlock automatically rather than through a separate flag.
- Selecting an already-completed level from level-select starts it in infinite mode rather than normal progression, per [Replay and infinite mode](#replay-and-infinite-mode).
- Settings is reached from the main menu or from the in-level gear icon, and returns to wherever it was opened from. It is intentionally minimal: Music and Sound Effects on/off toggles and a confirmed Reset Game Progress action. No username field and no screen-brightness control are included.
- How to Play is a static instructions screen reachable from the main menu.
- Icons (home, back/return, next-level, lock) are short text labels for now (e.g. "Back", "LOCKED") rather than custom glyph art, pending real icon assets.
- Not yet implemented: the one-second full-page logo opening screen that morphs into the main menu described in [Opening flow](#opening-flow) -- the app currently opens straight to the menu screen itself.

### Dialogue timing

- When a question begins, the claim appears centered on screen (not yet in the voice box) for three seconds.
- It then animates sliding down into the voice box at the bottom of the screen.
- Only once it settles into the voice box do the answer papers appear and the question's countdown timer start -- the three-second centered read and the slide are "free" time that doesn't consume the answer timer.
