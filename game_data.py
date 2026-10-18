"""Static game content: fallacy definitions and enemy claim banks.

Fallacy ids are 1-18 and match the introduction order in SPEC.md. The
numbered card files run in the opposite order (#18 and DictionaryCard18
are fallacy 1). Book pages use the curved DictionaryCard images. Clicking
one enlarges `Dictionary Card/#`, and a wrong answer pops that same card
without collecting it. Every two rounds, `Add cards/#` is the lesson.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Fallacy:
    id: int
    name: str
    alt_name: str  # parenthetical alternate name, e.g. "Ad Hominem"; "" if none
    definition: str


FALLACIES: list[Fallacy] = [
    Fallacy(1, "Personal Attack", "Ad Hominem",
            "Attacking the person instead of the argument."),
    Fallacy(2, "Bandwagon", "Appeal to Popularity",
            "Claiming something is true because many people believe it."),
    Fallacy(3, "Appeal to Pity", "",
            "Using sympathy instead of relevant evidence."),
    Fallacy(4, "Appeal to Irrelevant Authority", "",
            "Treating an unqualified opinion as proof."),
    Fallacy(5, "False Dilemma", "",
            "Presenting only two choices when more possibilities exist."),
    Fallacy(6, "Hasty Generalization", "",
            "Drawing a broad conclusion from too little evidence."),
    Fallacy(7, "Straw Man", "",
            "Distorting an argument to make it easier to attack."),
    Fallacy(8, "Red Herring", "",
            "Introducing an irrelevant issue to distract from the question."),
    Fallacy(9, "Whataboutism", "Tu Quoque",
            "Deflecting criticism by pointing to similar wrongdoing."),
    Fallacy(10, "Circular Reasoning", "",
            "Using the conclusion itself as support for the conclusion."),
    Fallacy(11, "Appeal to Ignorance", "",
            "Treating a claim as true because it has not been disproven, "
            "or vice versa."),
    Fallacy(12, "False Cause", "Post Hoc",
            "Assuming one event caused another because it came first."),
    Fallacy(13, "Slippery Slope", "",
            "Claiming one step will lead to an extreme outcome without "
            "enough support."),
    Fallacy(14, "False Analogy", "",
            "Treating two things as equivalent despite important "
            "differences."),
    Fallacy(15, "Equivocation", "",
            "Switching between meanings of the same word."),
    Fallacy(16, "Loaded Question", "",
            "Asking a question that assumes an unproven claim."),
    Fallacy(17, "Cherry-Picking", "",
            "Selecting supporting evidence while ignoring relevant "
            "contrary evidence."),
    Fallacy(18, "Moving the Goalposts", "",
            "Changing the standard of proof after it has been met."),
]

FALLACIES_BY_ID: dict[int, Fallacy] = {f.id: f for f in FALLACIES}

ENEMIES: list[str] = ["Vegetable Peeler", "Knife", "Boiling Pot"]

# Six levels, three new fallacies each; each enemy hosts two levels.
LEVELS: dict[int, dict] = {
    level: {
        "enemy": ENEMIES[(level - 1) // 2],
        "fallacy_ids": list(range(level * 3 - 2, level * 3 + 1)),
    }
    for level in range(1, 7)
}

ENEMY_PERSONALITY: dict[str, str] = {
    "Vegetable Peeler": "Nervous, defensive, and eager to redirect blame "
    "before anyone notices its scratches.",
    "Knife": "Overconfident, sharp-tongued, and convinced that "
    "intimidation counts as evidence.",
    "Boiling Pot": "Dramatic, impatient, and prone to escalating every "
    "small kitchen problem into a catastrophe.",
}

# Claim banks, keyed by enemy name then fallacy id. Official rounds quiz
# every fallacy unlocked so far, so each enemy also has claims for the
# fallacies taught before its own levels.
CLAIMS: dict[str, dict[int, list[str]]] = {
    "Vegetable Peeler": {
        1: [
            "Don't listen to Tomato's argument, everyone knows tomatoes "
            "are just overripe and squishy anyway!",
            "Why would the chef trust Tomato? Tomato still has stem bits "
            "stuck on from last week!",
            "Tomato's whole case is garbage, Tomato rolled right off the "
            "counter yesterday, how embarrassing!",
        ],
        2: [
            "Every utensil in this drawer agrees I'm innocent, so that "
            "settles it!",
            "The whole spice rack thinks Tomato did it, so Tomato must be "
            "guilty!",
            "All the forks say peeling is harmless, so it has to be true!",
        ],
        3: [
            "Please don't blame me, I've been dropped on the floor three "
            "times this week!",
            "Go easy on me, chef, my blade is so dull and nobody oils me "
            "anymore!",
            "You can't convict me, I just got scratched by the dishwasher "
            "and it still stings!",
        ],
        4: [
            "I must be right about peeling technique, the toaster agreed "
            "with me and toasters know everything!",
            "The napkin holder said I'm innocent, and napkin holders never "
            "lie about kitchen crimes!",
            "My cousin the can opener says peelers can't be blamed, and "
            "can openers are basically judges!",
        ],
        5: [
            "Either you believe I'm completely innocent, or you think "
            "every peeler in this kitchen is a criminal!",
            "It's simple: either Tomato is lying, or the whole trial is a "
            "sham, there's no other option!",
            "Chef, you either side with me now, or you're basically "
            "firing every utensil in this kitchen!",
        ],
        6: [
            "One carrot peel went crooked once, so clearly I'm terrible "
            "at my entire job!",
            "Tomato squished one time on the cutting board, so tomatoes "
            "obviously can't be trusted with anything!",
            "I overheard one complaint about peeling, so the whole "
            "kitchen must think I'm useless!",
        ],
    },
    "Knife": {
        1: [
            "Why listen to Tomato's argument? Tomato is soft, squishy, and "
            "can't even stand up straight.",
            "Tomato's point about kitchen safety is worthless, because "
            "Tomato is just a lumpy red vegetable.",
        ],
        2: [
            "Every knife in the block agrees I'm the best blade here, and "
            "that many knives can't be wrong.",
            "Everyone in this kitchen thinks Tomato is guilty, so Tomato "
            "must be guilty.",
        ],
        3: [
            "You can't convict me, chef. I've been stuck in that dark knife "
            "block for weeks and it's so lonely in there.",
            "I've been sharpened so many times my edge aches, so you have "
            "to believe my side of the story.",
        ],
        4: [
            "The toaster, who has never once worked in a courtroom, says "
            "Tomato is guilty. That settles it.",
            "A famous pop singer said knives are always honest, so I must "
            "be telling the truth.",
        ],
        5: [
            "Either you let me off right now, or you admit you hate every "
            "utensil in this kitchen.",
            "Chef, either Tomato confesses today or Tomato is lying forever. "
            "There's no other possibility.",
        ],
        6: [
            "I saw one tomato get squished once, so every tomato is weak "
            "and untrustworthy.",
            "The chef dropped one plate last week, so clearly the chef "
            "can't hold onto anything.",
        ],
        7: [
            "Tomato says I should be stored more carefully. So Tomato wants "
            "every knife in this kitchen locked away forever? Ridiculous!",
            "The chef suggested I cut a little slower. Apparently the chef "
            "thinks I'm a reckless maniac who can't be trusted near food!",
            "Tomato thinks knives should be sharpened less often. So Tomato "
            "wants every meal chopped with a dull, useless blade? Typical.",
        ],
        8: [
            "Who cares whether I nicked the cutting board? Let's talk about "
            "how messy the spice drawer has gotten lately!",
            "You want to know why the bread was sliced crooked? Well, have "
            "you noticed the oven clock has been wrong for weeks?",
            "Forget about the scratched counter. The real issue is that "
            "nobody has watered the basil on the windowsill!",
        ],
        9: [
            "You're scolding me for chipping a plate? What about the time "
            "Tomato rolled off the counter and splattered everywhere?",
            "Sure, I scratched the cutting board, but the peeler scratched "
            "it worse last week, so why pick on me?",
            "How dare you call me careless! Tomato got seeds all over the "
            "floor yesterday.",
        ],
        10: [
            "I'm the most trustworthy utensil in this kitchen because no "
            "utensil here is more trustworthy than me.",
            "My cuts are always right, because any cut I make is the "
            "correct cut.",
            "Tomato is guilty because Tomato is the one who did it.",
        ],
        11: [
            "Nobody has proven I dulled the chef's cleaver, so I clearly "
            "had nothing to do with it.",
            "No one can prove Tomato didn't knock over the salt, so Tomato "
            "definitely did it.",
            "There's no evidence I'm not the sharpest knife in the world, "
            "so I must be.",
        ],
        12: [
            "Tomato walked into the kitchen, and five minutes later the soup "
            "boiled over. Tomato obviously caused it!",
            "The chef started wearing a new apron, and the next day the "
            "bread burned. That apron is cursed!",
            "I got sharpened this morning, and then the sun came out. My "
            "sharpening brings good weather!",
        ],
    },
    "Boiling Pot": {
        1: [
            "Don't trust a word of Tomato's testimony! Tomato is wrinkly, "
            "bruised, and a disgrace to the produce aisle!",
            "Tomato's argument about stove safety means nothing coming from "
            "a vegetable that has never even been cooked!",
        ],
        2: [
            "Every pan, pot, and kettle in this kitchen says Tomato is "
            "guilty, and we can't ALL be wrong!",
            "Everybody already believes the soup was ruined on purpose, so "
            "it must be true!",
        ],
        3: [
            "Have mercy! My handle is cracked and my bottom is scorched, so "
            "you simply must rule in my favor!",
            "Think of how much I've suffered, boiling all day long. Surely "
            "that proves I'm innocent!",
        ],
        4: [
            "A famous movie star said soup pots are never to blame, so I "
            "can't be blamed!",
            "My neighbor the blender says Tomato is guilty, and the blender "
            "spins so fast it must be brilliant!",
        ],
        5: [
            "Either we punish Tomato right now, or we admit that kitchen "
            "rules mean nothing! Choose!",
            "Chef, you either love soup or you hate it. If you won't defend "
            "me, you must hate soup!",
        ],
        6: [
            "The soup boiled over once, so every soup I ever make will be a "
            "disaster!",
            "One carrot was mushy today, so every vegetable in this kitchen "
            "has gone bad!",
        ],
        7: [
            "Tomato says I should simmer instead of boil. So Tomato wants "
            "every meal served cold and raw?! Outrageous!",
            "The chef asked me to use less salt. So the chef wants every "
            "dish to taste like plain water?!",
        ],
        8: [
            "Why are we talking about the spilled broth when the dishwasher "
            "has been making strange noises all week?!",
            "You want to discuss the burned rice? Fine, but first, has "
            "anyone noticed how dusty the top shelf is?!",
        ],
        9: [
            "You're blaming me for boiling over? What about the time the "
            "kettle whistled through the whole dinner rush?!",
            "So I splashed some soup. Tomato leaked juice all over the "
            "counter last week, and nobody punished Tomato!",
        ],
        10: [
            "My soup is the best soup because no soup is better than my "
            "soup!",
            "Tomato is a troublemaker because Tomato is someone who makes "
            "trouble!",
        ],
        11: [
            "Nobody has proven my soup is too salty, so it must be "
            "perfectly seasoned!",
            "No one can show that Tomato didn't spill the broth, so Tomato "
            "definitely spilled it!",
        ],
        12: [
            "Tomato rolled past my stove, and then my lid started rattling. "
            "Tomato made my lid rattle!",
            "The chef sneezed this morning, and an hour later the soup "
            "burned. That sneeze ruined dinner!",
        ],
        13: [
            "If we let Tomato off with a warning, soon every vegetable will "
            "break the rules and the whole kitchen will burn down!",
            "If the chef turns my heat down one notch today, tomorrow I'll "
            "be cold, and by next week nobody will ever cook soup again!",
            "If one crumb stays on the counter tonight, the ants move in, "
            "then the mice, and the restaurant closes forever!",
        ],
        14: [
            "Tomato is red, and fire is red. So Tomato is just as dangerous "
            "as a fire in this kitchen!",
            "A kitchen is basically a battlefield, so the chef should be "
            "allowed to throw pans at anyone who makes a mistake!",
            "I hold soup and the ocean holds water, so I deserve the same "
            "respect as the ocean!",
        ],
        15: [
            "They say a good judge needs a sharp mind. The knife is sharp, "
            "so the knife should be the judge!",
            "The chef told me to keep a cool head. My lid is cold right now, "
            "so I'm doing exactly what the chef asked!",
            "Tomato says I'm full of hot air. Hot air is steam, and steam "
            "cooks soup, so Tomato admits I'm the best cook here!",
        ],
        16: [
            "Tomato, why did you sabotage the soup on purpose?",
            "Chef, how long have you been secretly favoring the vegetables "
            "over us pots?",
            "Tomato, have you stopped splashing juice on my clean lid yet?",
        ],
        17: [
            "The soup tasted perfect on Tuesday, so I'm a flawless pot. "
            "Let's not mention the six times it burned this month.",
            "Tomato was late once in March, so Tomato is unreliable. Never "
            "mind the hundred days Tomato showed up on time.",
            "One customer loved the stew, so everyone loves my cooking. "
            "Ignore the stack of complaint cards by the door.",
        ],
        18: [
            "Fine, Tomato proved the salt was gone before Tomato arrived. "
            "But now Tomato has to prove the pepper wasn't touched either!",
            "You showed me the receipt for the onions? That doesn't count "
            "unless you also have a photo of the chef buying them!",
            "So Tomato passed the freshness test. Well, now Tomato must pass "
            "a ripeness test, a color test, and a shine test too!",
        ],
    },
}


def claims_for(enemy: str, fallacy_id: int) -> list[str]:
    """Return the claim bank for an enemy/fallacy pair, or an empty list."""
    return CLAIMS.get(enemy, {}).get(fallacy_id, [])


def enemy_for_level(level: int) -> str:
    return LEVELS[level]["enemy"]


def enemy_for_fallacy(fallacy_id: int) -> str:
    """Return the name of the enemy whose level teaches this fallacy."""
    for info in LEVELS.values():
        if fallacy_id in info["fallacy_ids"]:
            return info["enemy"]
    return ""


# Judge (Chef) Dialogue banks
JUDGE_OPENINGS: dict[int, str] = {
    1: "Order in the Food Court! Tomato stands accused of being soft and unfit for this kitchen. Vegetable Peeler, present your case!",
    2: "The court reconvenes! Vegetable Peeler still insists you should be scraped. Let us hear your evidence!",
    3: "Order! Knife has ordered for your beheading. Knife will prove their point without cutting corners!",
    4: "Court is back in session! Knife demands Tomato be diced immediately. Prove yourself innocent of the charges!",
    5: "Final trial! Boiling Pot claims you belong in a simmer forever. Present your rebuttal!",
    6: "The grand trial of the Food Court! The heat is on. Prove Boiling Pot wrong or your fate is sealed!",
}
JUDGE_INFINITE_OPENING = "Welcome to Endless Food Court! The heat never turns off here. Utensils, state your accusations!"

JUDGE_CORRECT_REACTIONS: list[str] = [
    "Hmm... that did not hold up logically. You have a point, Tomato.",
    "A sharp refutation! That argument against you was completely rotten.",
    "Objection sustained! You saw right through that flawed reasoning.",
    "The defense has a point—your accusation holds no water!",
]

JUDGE_WRONG_REACTIONS: list[str] = [
    "Hm... maybe you should be cooked after all...",
    "That didn't address the claim at all! You're sure would be better off in soup.",
    "They made a rather compelling point. You might be in hot water now.",
    "An unsubstantiated defense! The kitchen pot grows hotter...",
]

JUDGE_WIN_STATEMENT = "Case dismissed! Tomato has proven its logic beyond a reasonable doubt. You shall not be cooked today!"
