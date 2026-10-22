# -*- coding: utf-8 -*-
"""Food Court.

Run on desktop with `python main.py`. Packaged for the browser with
Pygbag (see README.md). Six levels (two per enemy) each teach three
fallacies, run a no-damage warm-up, then an official round where both
sides lose health. Infinite mode reviews everything unlocked so far.
"""

from __future__ import annotations

import asyncio
from functools import lru_cache
import math
import random
import sys
from pathlib import Path

import pygame

import game_data
import game_rules
from audio import AudioManager
from game_data import FALLACIES, FALLACIES_BY_ID
from game_rules import FallacySelector
from entities.chef import Chef
from entities.peeler import Peeler
from entities.tomato import Tomato
from progress import Progress

ASSET_DIR = Path(__file__).parent / "assets"
VIRTUAL_W, VIRTUAL_H = 1280, 720

# --- design tokens ------------------------------------------------------
# One warm palette shared by every screen so panels, buttons and text match.
INK = (52, 33, 22)            # primary text on light surfaces
INK_SOFT = (120, 96, 76)      # secondary text, captions
SURFACE = (251, 246, 236)     # cards and panels
SURFACE_ALT = (240, 230, 211)  # insets, slider tracks, locked tiles
LINE = (222, 205, 178)        # hairlines inside cards
LINE_STRONG = (176, 146, 110)  # card and control outlines
PRIMARY = (210, 88, 52)       # tomato red: main actions
PRIMARY_DARK = (148, 54, 30)
SECONDARY = (88, 146, 96)     # sage green: success / completed
SECONDARY_DARK = (52, 98, 60)
GOLD = (242, 186, 72)
DANGER = (192, 62, 48)
DANGER_DARK = (128, 36, 26)
HUD_DARK = (38, 24, 16)
SHADOW = (20, 10, 4)
TEXT_ON_DARK = (255, 248, 238)
RADIUS_CONTROL = 12
RADIUS_PANEL = 20

BG = (60, 38, 26)
PANEL_CREAM = SURFACE
PANEL_BORDER = LINE_STRONG
TEXT_DARK = INK
BUTTON_FILL = PRIMARY
BUTTON_BORDER = PRIMARY_DARK
BUTTON_TEXT = TEXT_ON_DARK
CORRECT_COLOR = (74, 148, 86)
INCORRECT_COLOR = (178, 58, 46)
PAPER_FILL = (250, 244, 228)
PAPER_BORDER = (150, 110, 60)
CARD_WHITE = (252, 251, 247)
SPARKLE_COLOR = PRIMARY
OVERLAY_DARK = (16, 10, 8)

FLASH_DURATION = 0.5
GAVEL_DURATION = 1.2
TOAST_DURATION = 2.0
FEEDBACK_ENTER_SECONDS = 0.3
FEEDBACK_EXIT_SECONDS = 0.3
DIALOGUE_CENTER_SECONDS = 0.1
DIALOGUE_MOVE_SECONDS = 1.0
PAGE_TURN_SECONDS = 0.65
CARDS_PER_SPREAD = 4  # two dictionary cards on each page of the open book

# Open-book art (`Untitled_Artwork 9.png`) uses a 3300x2550 canvas. These
# rects are in source-image pixels: the crop contains the full book and the
# page areas leave room for the rings and page edges.
BOOK_CROP = pygame.Rect(108, 0, 3084, 2550)
LEFT_PAGE_SRC = pygame.Rect(264, 684, 1252, 1680)
RIGHT_PAGE_SRC = pygame.Rect(1789, 684, 1230, 1680)
BOOK_MAX = (1080, 690)

# The kitchen art is 4:3, so it is cover-scaled to 16:9 and cropped from the
# top (the bottom edge stays put). These anchors are in that cropped space:
# the table tops run from y≈434 (back edge) to y≈541 (front edge).
CHEF_ANCHOR = (640, VIRTUAL_H // 2 + 300 )
TOMATO_ANCHOR = (175, 496)
ENEMY_ANCHOR = (1100, 496)
CHARACTER_SIZE = 230
CHEF_SIZE = 450

# Gameplay layout. The claim sits in a box between the two tables and the
# answer papers float in the open area above it, never underneath it.
DIALOGUE_RECT = pygame.Rect(290, 552, 700, 156)
PAPER_BOUNDS = pygame.Rect(300, 232, 680, DIALOGUE_RECT.top - 20 - 232)

# Fighting-game HUD: two health bars meet at a centre timer medallion.
HUD_BAR_LEFT = pygame.Rect(110, 28, 420, 72)
HUD_BAR_RIGHT = pygame.Rect(VIRTUAL_W - 110 - 420, 28, 420, 72)
HUD_BAR_SLANT = 16
HUD_PORTRAIT_D = 80
HUD_PORTRAIT_LEFT = (60, 44)
HUD_PORTRAIT_RIGHT = (VIRTUAL_W - 60, 44)
HUD_TIMER_CENTER = (VIRTUAL_W // 2, 64)
HUD_TIMER_RADIUS = 38
GAMEPLAY_PAN_PIXELS = 40
GAMEPLAY_PAN_SPEED = 200.0
FOREGROUND_PAN_SPEED = 90.0
CHEF_PAN_SPEED = 90.0
# Foreground props and characters move farther than the distant room art,
# creating a parallax depth cue while keeping every layer moving together.
FOREGROUND_PAN_RATIO = 0.5
CHEF_PAN_RATIO = 0.5

LEVEL_TILE_SIZE = (170, 280)
# Six level cards uniformly centered across the screen
LEVEL_CIRCLE_RECTS = [
    pygame.Rect(70 + i * 194, VIRTUAL_H //2 - LEVEL_TILE_SIZE[1] //2, *LEVEL_TILE_SIZE) for i in range(6)
]
LEVEL_PORTRAIT_D = 116
# Level-select carousel of restaurant-ticket cards.
TICKET_SIZE = (300, 410)
TICKET_CENTER = (VIRTUAL_W // 2, 352)
CAROUSEL_SPACING = (0, 330, 560)  # x offset of the center, neighbor and far tickets
CAROUSEL_SCALE = (1.0, 0.72, 0.52)
CAROUSEL_DIM = (0, 70, 130)  # darkening alpha for tickets off center
CAROUSEL_SPEED = 10.0
CAROUSEL_ARROW_RECTS = (
    pygame.Rect(TICKET_CENTER[0] - TICKET_SIZE[0] // 2 - 70, TICKET_CENTER[1] - 28, 56, 56),
    pygame.Rect(TICKET_CENTER[0] + TICKET_SIZE[0] // 2 + 14, TICKET_CENTER[1] - 28, 56, 56),
)
LEVEL_STAMPS = {"Vegetable Peeler": "skinner_stamp.png", "Knife": "knife_stamp.png", "Boiling Pot": "pot_stamp.png"}
TICKET_PAPER = (248, 242, 228)
TICKET_BORDER = (110, 98, 88)
TICKET_TABLE = (222, 212, 196)
TICKET_RULE = (184, 170, 152)
TICKET_RED = (214, 118, 106)
TICKET_INK = (84, 84, 84)
INFINITE_BUTTON_RECT = pygame.Rect(330, 580, 620, 100)
RETURN_BUTTON_RECT = pygame.Rect(32, 28, 124, 48)
PAUSE_BUTTON_RECT = pygame.Rect(HUD_TIMER_CENTER[0] + 50, 40, 44, 44)
PAUSE_POPUP_RECT = pygame.Rect(440, 140, 400, 440)
DICTIONARY_HUD_RECT = pygame.Rect(HUD_TIMER_CENTER[0] - 100, 40, 44, 44)

INFINITE_SAVE_KEY = 0  # infinite mode is one shared run, not per level
ENEMY_SHEETS = {
    "Vegetable Peeler": "Peeler_SpriteSheet.png",
    "Knife": "Knife_SpriteSheet.png",
    "Boiling Pot": "Pot_SpriteSheet.png",
}
# Knife and pot sprites have lots of empty width, so they draw wider to
# cover about the same area as the peeler.
ENEMY_DRAW_WIDTHS = {"Knife": 420, "Boiling Pot": 300}
SETTINGS_PAPER_RECT = pygame.Rect(440, 56, 400, 608)
SETTINGS_RESET_RECT = pygame.Rect(472, 596, 336, 46)
DEV_INPUT_RECT = pygame.Rect(472, 436, 336, 42)
DEV_SWITCH_RECT = pygame.Rect(752, 498, 56, 30)
DEV_PASSWORD = "dev67"
HOVER_SCALE = 1.05
MENU_LOGO_WIDTH = 380
MENU_CARD_RECT = pygame.Rect(480, 316, 320, 300)
# Where _draw_menu puts the logo, and the startup splash that glides into it.
MENU_LOGO_CENTER = (VIRTUAL_W // 2, 240)
INTRO_LOGO_WIDTH = 640
INTRO_HOLD_SECONDS = 2.0
INTRO_MOVE_SECONDS = 0.6
INFO_BUTTON_RECT = pygame.Rect(SETTINGS_PAPER_RECT.left + 16, SETTINGS_PAPER_RECT.top + 16, 40, 40)
CREDITS_LINES = (
    ("Developers", "Lina, Sophii, Ryan, Kenzie"),
    ("Audio", "Courtesy of the YouTube Studio Audio Library"),
    ("Event", "DubHacks 2026"),
)
SETTINGS_ROW_RECTS = [pygame.Rect(472, 250, 336, 50), pygame.Rect(472, 318, 336, 50)]
# Slider track per settings row: the label sits above, the track below it.
SETTINGS_SLIDER_RECTS = [pygame.Rect(r.left + 8, r.bottom - 12, r.width - 16, 8) for r in SETTINGS_ROW_RECTS]
# The pause pop-up repeats the same two volume rows.
PAUSE_ROW_RECTS = [pygame.Rect(472, 254, 336, 50), pygame.Rect(472, 322, 336, 50)]
PAUSE_SLIDER_RECTS = [pygame.Rect(r.left + 8, r.bottom - 12, r.width - 16, 8) for r in PAUSE_ROW_RECTS]
# Gold ribbon announcing the warm-up and the official round.
ANNOUNCE_COLOR = (222, 146, 48)
ANNOUNCE_SECONDS = 1.8
# Music track per level; infinite mode uses its own theme.
LEVEL_MUSIC = {1: "veggie_skinner", 2: "veggie_skinner", 3: "knife", 4: "knife", 5: "boiling_pot", 6: "boiling_pot"}
LEVEL_MUSIC_STATES = ("TEACHING", "GAMEPLAY", "FEEDBACK", "GAVEL")

# Sprite bounds in HealthBar_SpriteSheet.png, ordered left to right from the
# full carrot to the most depleted stub.
HEALTH_ICON_RECTS = [
    (133, 282, 2068, 442),
    (2552, 295, 1821, 442),
    (4686, 291, 1668, 442),
    (6661, 293, 1483, 442),
    (8563, 287, 1227, 442),
    (10202, 290, 949, 443),
]

TYPEWRITER_CHARS_PER_SEC = 32.0

# Dialogue scripts loaded from game_data.py
JUDGE_OPENINGS = game_data.JUDGE_OPENINGS
JUDGE_INFINITE_OPENING = game_data.JUDGE_INFINITE_OPENING
JUDGE_CORRECT_REACTIONS = game_data.JUDGE_CORRECT_REACTIONS
JUDGE_WRONG_REACTIONS = game_data.JUDGE_WRONG_REACTIONS
JUDGE_WIN_STATEMENT = game_data.JUDGE_WIN_STATEMENT


# --- asset helpers -------------------------------------------------------


def load_image(name: str, fallback_size=(128, 128), fallback_color=(200, 120, 80)):
    path = ASSET_DIR / name
    try:
        return pygame.image.load(str(path)).convert_alpha()
    except Exception:
        surf = pygame.Surface(fallback_size, pygame.SRCALPHA)
        surf.fill(fallback_color)
        return surf


def slice_sheet(sheet: pygame.Surface, count: int, cell: int = 1024) -> list[pygame.Surface]:
    frames = []
    for i in range(count):
        rect = pygame.Rect(i * cell, 0, cell, cell)
        if rect.right <= sheet.get_width():
            frames.append(sheet.subsurface(rect).copy())
    return frames


_SCALE_CACHE: dict[tuple[int, tuple[int, int]], tuple[pygame.Surface, pygame.Surface]] = {}
_SCALE_CACHE_LIMIT = 256


def cached_smoothscale(img: pygame.Surface, size: tuple[int, int]) -> pygame.Surface:
    """smoothscale for long-lived images drawn every frame.

    smoothscale is the dominant per-frame cost; in the browser it starved the
    audio callback and made sound crackle. Results are cached by source and size.
    The returned surface is shared, so callers must copy() before mutating it.
    """
    key = (id(img), (int(size[0]), int(size[1])))
    hit = _SCALE_CACHE.get(key)
    if hit is not None and hit[0] is img:
        return hit[1]
    if len(_SCALE_CACHE) >= _SCALE_CACHE_LIMIT:
        _SCALE_CACHE.clear()
    scaled = pygame.transform.smoothscale(img, key[1])
    _SCALE_CACHE[key] = (img, scaled)
    return scaled


def scale_square(img: pygame.Surface, size: int) -> pygame.Surface:
    return pygame.transform.smoothscale(img, (size, size))


def cover_scale(img: pygame.Surface, size: tuple[int, int], anchor_y: float = 0.5) -> pygame.Surface:
    """Scale to fill `size` keeping the aspect ratio and crop the overflow.

    `anchor_y` picks which part survives a vertical crop: 0.5 keeps the
    middle, 1.0 keeps the bottom edge (used for the gameplay scene so the
    tables reach the bottom of the screen).
    """
    scale = max(size[0] / img.get_width(), size[1] / img.get_height())
    scaled = pygame.transform.smoothscale(
        img, (max(size[0], round(img.get_width() * scale)), max(size[1], round(img.get_height() * scale)))
    )
    crop = pygame.Rect(0, 0, *size)
    crop.centerx = scaled.get_width() // 2
    crop.top = round((scaled.get_height() - size[1]) * max(0.0, min(1.0, anchor_y)))
    return scaled.subsurface(crop).copy()


def add_vertical_overscan(img: pygame.Surface, margin: int) -> pygame.Surface:
    """Pad an image vertically so small camera pans do not expose blank edges."""
    expanded = pygame.Surface((img.get_width(), img.get_height() + margin * 2), pygame.SRCALPHA)
    top_row = img.subsurface(pygame.Rect(0, 0, img.get_width(), 1))
    bottom_row = img.subsurface(pygame.Rect(0, img.get_height() - 1, img.get_width(), 1))
    for y in range(margin):
        expanded.blit(top_row, (0, y))
        expanded.blit(bottom_row, (0, margin + img.get_height() + y))
    expanded.blit(img, (0, margin))
    return expanded


def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    # Callers re-wrap the same strings every frame; font.size is too slow for that in the browser.
    return list(_wrap_text_cached(text, font, max_width))


@lru_cache(maxsize=4096)
def _word_width(font: pygame.font.Font, word: str) -> int:
    return font.size(word)[0]


@lru_cache(maxsize=512)
def _wrap_text_cached(text: str, font: pygame.font.Font, max_width: int) -> tuple[str, ...]:
    words = text.split(" ")
    lines: list[str] = []
    current = ""
    current_w = 0
    space_w = font.size(" ")[0]
    for word in words:
        # Sum per-word widths rather than re-measuring the growing line.
        word_w = _word_width(font, word)
        trial_w = current_w + space_w + word_w if current else word_w
        if trial_w <= max_width or not current:
            current = f"{current} {word}".strip()
            current_w = trial_w
        else:
            lines.append(current)
            current = word
            current_w = word_w
    if current:
        lines.append(current)
    return tuple(lines)


def wrap_text_progressive(full_text: str, chars_to_show: int, font: pygame.font.Font, max_width: int) -> list[str]:
    """Wraps the full string to lock in consistent line breaks, revealing characters progressively without jumping."""
    full_lines = wrap_text(full_text, font, max_width)
    result: list[str] = []
    remaining = chars_to_show
    for line in full_lines:
        if remaining <= 0:
            break
        # +1 accounts for the space between wrapped lines in full text
        line_cost = len(line) + 1
        if remaining >= len(line):
            result.append(line)
            remaining -= line_cost
        else:
            result.append(line[:remaining])
            remaining = 0
            break
    return result


@lru_cache(maxsize=256)
def _rounded_rect_surface(
    size: tuple[int, int], fill: tuple[int, ...], radius: int,
    border: tuple[int, ...] | None, border_width: int,
) -> pygame.Surface:
    supersample = 2
    width, height = size
    surface = pygame.Surface((width * supersample, height * supersample), pygame.SRCALPHA)
    full = surface.get_rect()
    if border is not None and border_width > 0:
        pygame.draw.rect(surface, border, full, border_radius=radius * supersample)
        inset = border_width * supersample
        inner = full.inflate(-inset * 2, -inset * 2)
        if inner.width > 0 and inner.height > 0:
            pygame.draw.rect(
                surface, fill, inner,
                border_radius=max(0, radius - border_width) * supersample,
            )
    else:
        pygame.draw.rect(surface, fill, full, border_radius=radius * supersample)
    return pygame.transform.smoothscale(surface, size)


def draw_rounded_rect(
    surf: pygame.Surface,
    rect: pygame.Rect,
    fill: tuple[int, ...],
    radius: int = 0,
    border: tuple[int, ...] | None = None,
    border_width: int = 0,
) -> None:
    rect = pygame.Rect(rect)
    if rect.width <= 0 or rect.height <= 0:
        return
    image = _rounded_rect_surface(
        rect.size, tuple(fill), max(0, radius), tuple(border) if border is not None else None,
        max(0, border_width),
    )
    surf.blit(image, rect)


@lru_cache(maxsize=128)
def _circle_surface(radius: int, fill: tuple[int, ...], border: tuple[int, ...] | None, border_width: int) -> pygame.Surface:
    supersample = 4
    size = radius * 2 * supersample
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    center = (size // 2, size // 2)
    r = radius * supersample
    if border is not None and border_width > 0:
        pygame.draw.circle(surface, border, center, r)
        inner_r = max(0, r - border_width * supersample)
        if inner_r > 0:
            pygame.draw.circle(surface, fill, center, inner_r)
    else:
        pygame.draw.circle(surface, fill, center, r)
    return pygame.transform.smoothscale(surface, (radius * 2, radius * 2))


def draw_smooth_circle(
    surf: pygame.Surface,
    color: tuple[int, ...],
    center: tuple[int, int],
    radius: int,
    border: tuple[int, ...] | None = None,
    border_width: int = 0,
) -> None:
    """Draw smooth, anti-aliased circles without pixelated stepping."""
    if radius <= 0:
        return
    circ_surf = _circle_surface(radius, tuple(color), tuple(border) if border is not None else None, border_width)
    surf.blit(circ_surf, (center[0] - radius, center[1] - radius))


def window_to_virtual(pos: tuple[float, float], window_size: tuple[int, int]) -> tuple[float, float]:
    """Map display/window pixels to virtual canvas coordinates (1280x720)."""
    win_w, win_h = window_size
    scale = min(win_w / VIRTUAL_W, win_h / VIRTUAL_H)
    offset_x = (win_w - VIRTUAL_W * scale) / 2
    offset_y = (win_h - VIRTUAL_H * scale) / 2
    vx = (pos[0] - offset_x) / scale
    vy = (pos[1] - offset_y) / scale
    return vx, vy


def draw_panel(surf: pygame.Surface, rect: pygame.Rect, radius: int = 18) -> None:
    draw_card(surf, rect, radius)


def mix(a: tuple[int, ...], b: tuple[int, ...], t: float) -> tuple[int, ...]:
    """Blend colour `a` toward `b` by `t` (0..1)."""
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


@lru_cache(maxsize=64)
def _soft_shadow(size: tuple[int, int], radius: int, alpha: int, blur: int) -> pygame.Surface:
    """Layered rounded rects that fade outward: a cheap blur that works in Pygbag."""
    width, height = size
    surface = pygame.Surface((width + blur * 2, height + blur * 2), pygame.SRCALPHA)
    steps = max(1, blur // 2)
    for i in range(steps):
        inset = round(i * blur / steps)
        rect = surface.get_rect().inflate(-inset * 2, -inset * 2)
        pygame.draw.rect(surface, (*SHADOW, max(1, alpha // steps)), rect,
                         border_radius=radius + blur - inset)
    return surface


def draw_shadow(surf: pygame.Surface, rect: pygame.Rect, radius: int = RADIUS_PANEL,
                offset: tuple[int, int] = (0, 8), alpha: int = 110, blur: int = 14) -> None:
    rect = pygame.Rect(rect)
    if rect.width <= 0 or rect.height <= 0:
        return
    shadow = _soft_shadow(rect.size, radius, alpha, blur)
    surf.blit(shadow, (rect.left - blur + offset[0], rect.top - blur + offset[1]))


def draw_card(surf: pygame.Surface, rect: pygame.Rect, radius: int = RADIUS_PANEL, fill=SURFACE,
              border=LINE_STRONG, shadow: bool = False) -> None:
    """The one panel style: soft shadow, warm surface, thin outline, top highlight."""
    rect = pygame.Rect(rect)
    if shadow:
        draw_shadow(surf, rect, radius)
    draw_rounded_rect(surf, rect, fill, radius, border, 2 if border is not None else 0)
    highlight = mix(fill[:3], (255, 255, 255), 0.6)
    pygame.draw.line(surf, highlight, (rect.left + radius, rect.top + 3), (rect.right - radius, rect.top + 3), 1)


def draw_text(surf: pygame.Surface, font: pygame.font.Font, text: str, color, **anchor) -> pygame.Rect:
    """Render `text` and place it with any pygame.Rect anchor, e.g. center=(x, y)."""
    label = font.render(text, True, color)
    rect = label.get_rect(**anchor)
    surf.blit(label, rect)
    return rect


def draw_shadow_text(surf: pygame.Surface, font: pygame.font.Font, text: str, color=TEXT_ON_DARK,
                     offset: int = 2, alpha: int = 150, **anchor) -> pygame.Rect:
    """Light text over artwork, lifted with a soft drop shadow instead of a hard outline."""
    shade = font.render(text, True, SHADOW)
    shade.set_alpha(alpha)
    rect = shade.get_rect(**anchor)
    surf.blit(shade, rect.move(0, offset))
    surf.blit(font.render(text, True, color), rect)
    return rect


def draw_chip(surf: pygame.Surface, font: pygame.font.Font, text: str, fill, color, **anchor) -> pygame.Rect:
    """Small rounded label, e.g. 'COMPLETED' on a level tile."""
    label = font.render(text, True, color)
    rect = label.get_rect().inflate(20, 8)
    rect = pygame.Rect(rect)
    setattr(rect, *next(iter(anchor.items())))
    draw_rounded_rect(surf, rect, fill, rect.height // 2)
    surf.blit(label, label.get_rect(center=rect.center))
    return rect


def smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def book_display_size() -> tuple[int, int]:
    scale = min(BOOK_MAX[0] / BOOK_CROP.width, BOOK_MAX[1] / BOOK_CROP.height)
    return (
        max(1, int(BOOK_CROP.width * scale)),
        max(1, int(BOOK_CROP.height * scale)),
    )


def lerp_rect(a: pygame.Rect, b: pygame.Rect, t: float) -> pygame.Rect:
    t = max(0.0, min(1.0, t))
    return pygame.Rect(
        round(a.left + (b.left - a.left) * t),
        round(a.top + (b.top - a.top) * t),
        round(a.width + (b.width - a.width) * t),
        round(a.height + (b.height - a.height) * t),
    )


def draw_icon(surf: pygame.Surface, name: str, center: tuple[int, int], size: int, color) -> None:
    """Simple line icons in the mockups' style, drawn instead of image assets."""
    cx, cy = center
    s = size
    w = max(2, s // 8)
    if name == "home":
        roof = [(cx - s * 0.55, cy - s * 0.02), (cx, cy - s * 0.5), (cx + s * 0.55, cy - s * 0.02)]
        pygame.draw.lines(surf, color, False, roof, w)
        body = pygame.Rect(0, 0, round(s * 0.75), round(s * 0.55))
        body.midtop = (cx, round(cy - s * 0.12))
        pygame.draw.rect(surf, color, body, w, border_radius=3)
        door = pygame.Rect(0, 0, round(s * 0.22), round(s * 0.3))
        door.midbottom = body.midbottom
        pygame.draw.rect(surf, color, door, w)
    elif name == "return":
        r = round(s * 0.42)
        rect = pygame.Rect(cx - r, cy - r, r * 2, r * 2)
        pygame.draw.arc(surf, color, rect, math.radians(-200), math.radians(110), w)
        tip = (cx - r * 0.35, cy - r)
        pygame.draw.polygon(surf, color, [
            (tip[0] - s * 0.18, tip[1]), (tip[0] + s * 0.08, tip[1] - s * 0.18), (tip[0] + s * 0.08, tip[1] + s * 0.18)
        ])
    elif name in ("next", "prev"):
        d = 1 if name == "next" else -1
        pygame.draw.line(surf, color, (cx - d * s * 0.4, cy), (cx + d * s * 0.35, cy), w)
        pygame.draw.lines(surf, color, False, [
            (cx + d * s * 0.05, cy - s * 0.32), (cx + d * s * 0.38, cy), (cx + d * s * 0.05, cy + s * 0.32)
        ], w)
    elif name == "lock":
        body = pygame.Rect(0, 0, round(s * 0.8), round(s * 0.6))
        body.midtop = (cx, round(cy - s * 0.05))
        pygame.draw.rect(surf, color, body, w, border_radius=max(2, s // 10))
        shackle = pygame.Rect(0, 0, round(s * 0.5), round(s * 0.6))
        shackle.midbottom = (cx, body.top + w)
        pygame.draw.arc(surf, color, shackle, 0, math.pi, w)
        pygame.draw.line(surf, color, (shackle.left + w // 2, shackle.centery), (shackle.left + w // 2, body.top), w)
        pygame.draw.line(surf, color, (shackle.right - w // 2 - 1, shackle.centery), (shackle.right - w // 2 - 1, body.top), w)
    elif name == "pause":
        bar = pygame.Rect(0, 0, max(4, round(s * 0.18)), round(s * 0.62))
        for dx in (-s * 0.17, s * 0.17):
            bar.center = (round(cx + dx), cy)
            pygame.draw.rect(surf, color, bar, border_radius=2)
    elif name == "check":
        pygame.draw.lines(surf, color, False, [(cx - s * 0.4, cy), (cx - s * 0.1, cy + s * 0.3), (cx + s * 0.45, cy - s * 0.35)], w + 2)
    elif name == "gear":
        r = s * 0.3
        for i in range(8):
            a = i * math.pi / 4
            pygame.draw.line(surf, color, (cx + math.cos(a) * r, cy + math.sin(a) * r),
                             (cx + math.cos(a) * s * 0.48, cy + math.sin(a) * s * 0.48), w + 2)
        pygame.draw.circle(surf, color, (cx, cy), round(r), w)
    elif name == "book":
        left = pygame.Rect(0, 0, round(s * 0.42), round(s * 0.7))
        left.topright = (cx, round(cy - s * 0.35))
        right = left.copy()
        right.topleft = (cx, left.top)
        pygame.draw.rect(surf, color, left, w, border_radius=2)
        pygame.draw.rect(surf, color, right, w, border_radius=2)
    elif name == "info":
        pygame.draw.circle(surf, color, (cx, round(cy - s * 0.3)), max(2, round(s * 0.09)))
        pygame.draw.line(surf, color, (cx, cy - s * 0.08), (cx, cy + s * 0.38), w + 1)
    elif name == "play":
        pygame.draw.polygon(surf, color, [
            (cx - s * 0.28, cy - s * 0.36), (cx + s * 0.38, cy), (cx - s * 0.28, cy + s * 0.36)
        ])


def draw_outlined_text(surf, font, text, center, fill=(255, 255, 255), outline=(60, 34, 20), width=1) -> None:
    base = font.render(text, True, outline)
    rect = base.get_rect(center=center)
    for dx in range(-width, width + 1):
        for dy in range(-width, width + 1):
            if dx * dx + dy * dy <= width * width:
                surf.blit(base, rect.move(dx, dy))
    surf.blit(font.render(text, True, fill), rect)


def circle_portrait(sprite: pygame.Surface, diameter: int, bg=(245, 242, 236), darken: bool = False) -> pygame.Surface:
    portrait = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
    draw_smooth_circle(portrait, bg, (diameter // 2, diameter // 2), diameter // 2)
    scale = diameter * 1.05 / max(sprite.get_width(), sprite.get_height())
    img = pygame.transform.smoothscale(
        sprite, (max(1, round(sprite.get_width() * scale)), max(1, round(sprite.get_height() * scale)))
    )
    portrait.blit(img, img.get_rect(center=(diameter // 2, round(diameter * 0.58))))
    if darken:
        shade = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        shade.fill((40, 40, 40, 170))
        portrait.blit(shade, (0, 0))
    # Smooth supersampled mask to eliminate pixelated edges
    supersample = 4
    mask_big = pygame.Surface((diameter * supersample, diameter * supersample), pygame.SRCALPHA)
    pygame.draw.circle(mask_big, (255, 255, 255, 255), (diameter * supersample // 2, diameter * supersample // 2), diameter * supersample // 2)
    mask = pygame.transform.smoothscale(mask_big, (diameter, diameter))
    portrait.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return portrait


def draw_sparkle(surf: pygame.Surface, center: tuple[int, int], size: int, color) -> None:
    """A small four-line asterisk/sparkle accent, as seen on teaching cards."""
    cx, cy = center
    for angle_deg in (0, 45, 90, 135):
        angle = math.radians(angle_deg)
        dx, dy = math.cos(angle) * size, math.sin(angle) * size
        pygame.draw.line(surf, color, (cx - dx, cy - dy), (cx + dx, cy + dy), 3)


class Button:
    """Styles: "pill" (rounded orange), "icon" (orange circle + vector icon,
    label drawn underneath as a caption), "link" (checkbox + underlined text
    on paper), "hidden" (hit area only; the screen draws the visuals)."""

    __slots__ = ("rect", "label", "action", "enabled", "radius", "style", "icon", "fill", "border", "image",
                 "hovered")

    def __init__(self, rect: pygame.Rect, label: str, action, enabled: bool = True, radius: int = 14,
                 style: str = "pill", icon: str = "", fill=None, border=None, image=None):
        self.rect = rect
        self.label = label
        self.action = action
        self.enabled = enabled
        self.radius = radius
        self.style = style
        self.icon = icon
        self.fill = fill
        self.border = border
        self.image = image
        self.hovered = False

    def _draw_rect(self) -> pygame.Rect:
        """Enabled buttons grow slightly while the cursor is over them."""
        if not (self.hovered and self.enabled):
            return self.rect
        grown = pygame.Rect(0, 0, round(self.rect.width * HOVER_SCALE), round(self.rect.height * HOVER_SCALE))
        grown.center = self.rect.center
        return grown

    def draw(self, surf: pygame.Surface, font: pygame.font.Font, bold_font: pygame.font.Font | None = None) -> None:
        if self.style == "hidden":
            return
        if self.style == "link":
            # Notebook checklist item: the text sits on the ruled line, which
            # runs to the paper's right margin. Hover bolds it and ticks the box.
            hover = self.hovered and bold_font is not None
            text_font = bold_font if hover else font
            baseline = self.rect.bottom - 4
            box = pygame.Rect(self.rect.left, 0, 22, 22)
            box.bottom = baseline - 4
            draw_rounded_rect(surf, box, (0, 0, 0, 0), 3, (90, 70, 50), 2)
            if hover:
                draw_icon(surf, "check", (box.centerx + 2, box.centery - 1), 20, (0, 0, 0))
            label = text_font.render(self.label, True, (90, 70, 50))
            pos = label.get_rect(left=box.right + 14, top=baseline - text_font.get_ascent())
            surf.blit(label, pos)
            pygame.draw.line(surf, (110, 90, 70), (pos.left, baseline + 2), (self.rect.right, baseline + 2), 2)
            return
        rect = self._draw_rect()
        if self.style == "icon":
            r = rect.width // 2
            # Clean elevated round button with subtle shadow
            shadow_surf = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
            pygame.draw.circle(shadow_surf, (*SHADOW, 70 if self.hovered else 40), (r + 4, r + 6), r)
            surf.blit(shadow_surf, (rect.centerx - r - 4, rect.centery - r - 4))

            fill = (225, 98, 60) if (self.hovered and self.enabled) else BUTTON_FILL
            if not self.enabled:
                fill = (140, 125, 115)
            pygame.draw.circle(surf, fill, rect.center, r)
            pygame.draw.circle(surf, mix(fill, (255, 255, 255), 0.35), rect.center, r, 2)
            icon_col = TEXT_ON_DARK if self.enabled else (200, 190, 180)
            draw_icon(surf, self.icon, rect.center, round(r * 1.05), icon_col)
            if self.label:
                draw_shadow_text(surf, font, self.label, TEXT_ON_DARK, offset=1, alpha=130, center=(rect.centerx, rect.bottom + 16))
            return
        if self.style == "todo":
            fill = (255, 255, 255) if (self.hovered and self.enabled) else (252, 248, 238)
            border = PRIMARY if (self.hovered and self.enabled) else (180, 160, 140)
            draw_shadow(surf, rect, radius=self.radius, offset=(0, 3), alpha=45 if self.hovered else 25, blur=6)
            draw_rounded_rect(surf, rect, fill, self.radius, border, 2)
            # To-do checkbox on the left
            box_sz = 22
            box = pygame.Rect(rect.left + 16, rect.centery - box_sz // 2, box_sz, box_sz)
            box_fill = (255, 245, 235) if self.hovered else (245, 240, 230)
            box_border = PRIMARY if self.hovered else (150, 130, 110)
            draw_rounded_rect(surf, box, box_fill, 4, box_border, 2)
            if self.hovered:
                draw_icon(surf, "check", (box.centerx + 1, box.centery), 18, PRIMARY)
            # Label
            text_col = PRIMARY if (self.hovered and self.enabled) else INK
            label = font.render(self.label, True, text_col if self.enabled else INK_SOFT)
            surf.blit(label, label.get_rect(midleft=(box.right + 14, rect.centery)))
            return
        if self.style == "secondary":
            fill = (255, 255, 255) if (self.hovered and self.enabled) else SURFACE
            border = PRIMARY if (self.hovered and self.enabled) else LINE_STRONG
            draw_shadow(surf, rect, radius=self.radius, offset=(0, 3), alpha=40, blur=6)
            draw_rounded_rect(surf, rect, fill, self.radius, border, 2)
            text_col = PRIMARY if (self.hovered and self.enabled) else INK
            label = font.render(self.label, True, text_col if self.enabled else INK_SOFT)
            label_rect = label.get_rect(center=rect.center)
            if self.icon:
                icon_size = round(rect.height * 0.45)
                label_rect.centerx += (icon_size + 8) // 2
                draw_icon(surf, self.icon, (label_rect.left - 8 - icon_size // 2, rect.centery), icon_size, text_col)
            surf.blit(label, label_rect)
            return
        if self.image is not None:
            image = cached_smoothscale(self.image, rect.size)
            if not self.enabled:
                image = image.copy()
                image.fill((140, 140, 140), special_flags=pygame.BLEND_RGB_MULT)
            surf.blit(image, rect)
            draw_outlined_text(surf, font, self.label, rect.center, fill=TEXT_DARK, outline=PAPER_FILL, width=2)
            return
        fill = (self.fill or BUTTON_FILL) if self.enabled else (150, 130, 110)
        border = (self.border or BUTTON_BORDER) if self.enabled else (110, 95, 80)
        if self.hovered and self.enabled and self.fill is None:
            fill = (228, 102, 64)
            border = (160, 60, 36)
        draw_shadow(surf, rect, radius=self.radius, offset=(0, 4), alpha=60 if self.enabled else 20, blur=8)
        draw_rounded_rect(
            surf, rect, fill, self.radius, border,
            2,
        )
        # Subtle top highlight inside button
        hi_col = mix(fill[:3], (255, 255, 255), 0.3)
        pygame.draw.line(surf, hi_col, (rect.left + self.radius, rect.top + 2), (rect.right - self.radius, rect.top + 2), 1)
        label = font.render(self.label, True, BUTTON_TEXT if self.enabled else (220, 210, 200))
        surf.blit(label, label.get_rect(center=rect.center))


class Paper:
    def __init__(
        self,
        text: str,
        is_correct: bool,
        bounds: pygame.Rect,
        rng: random.Random,
        backgrounds: list[pygame.Surface] | None = None,
    ):
        self.text = text
        self.is_correct = is_correct
        self.w, self.h = 196, 64
        background = rng.choice(backgrounds) if backgrounds else None
        self.background = (
            pygame.transform.smoothscale(background, (self.w, self.h))
            if background is not None else None
        )
        self.x = rng.uniform(bounds.left, max(bounds.left, bounds.right - self.w))
        self.y = rng.uniform(bounds.top, max(bounds.top, bounds.bottom - self.h))
        angle = rng.uniform(0, 2 * math.pi)
        speed = rng.uniform(55, 100)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.bounds = bounds

    def update(self, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.x < self.bounds.left:
            self.x = self.bounds.left
            self.vx *= -1
        elif self.x + self.w > self.bounds.right:
            self.x = self.bounds.right - self.w
            self.vx *= -1
        if self.y < self.bounds.top:
            self.y = self.bounds.top
            self.vy *= -1
        elif self.y + self.h > self.bounds.bottom:
            self.y = self.bounds.bottom - self.h
            self.vy *= -1

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def draw(self, surf: pygame.Surface, font: pygame.font.Font) -> None:
        r = self.rect()
        if self.background is not None:
            surf.blit(self.background, r)
        else:
            draw_rounded_rect(surf, r, SURFACE, 12, LINE_STRONG, 2)
        lines = wrap_text(self.text, font, r.width - 20)[:3]
        line_h = font.get_height()
        total_h = len(lines) * line_h
        y = r.centery - total_h // 2
        for line in lines:
            draw_outlined_text(
                surf,
                font,
                line,
                (r.centerx, y + line_h // 2),
                fill=INK,
                outline=(255, 252, 246),
                width=2,
            )
            y += line_h

class Game:
    def __init__(self) -> None:
        self.rng = random.Random()
        self.progress = Progress()
        self.audio = AudioManager(self.progress.music_volume, self.progress.sfx_volume)
        self.dragging_slider: int | None = None
        self.selector = FallacySelector()

        # Keep the selected font files inside the project so desktop and browser
        # builds use the same Nunito faces.
        font_dir = ASSET_DIR / "Nunito" / "static"
        self.fonts = {
            "title": pygame.font.Font(str(font_dir / "Nunito-Bold.ttf"), 54),
            "large": pygame.font.Font(str(font_dir / "Nunito-Regular.ttf"), 40),
            "body": pygame.font.Font(str(font_dir / "Nunito-Regular.ttf"), 28),
            "small": pygame.font.Font(str(font_dir / "Nunito-Regular.ttf"), 22),
            "paper": pygame.font.Font(str(font_dir / "Nunito-Regular.ttf"), 18),
        }
        self.fonts["title_bold"] = pygame.font.Font(str(font_dir / "Nunito-ExtraBold.ttf"), 54)
        self.fonts["body_bold"] = pygame.font.Font(str(font_dir / "Nunito-Bold.ttf"), 28)
        self.fonts["large_bold"] = pygame.font.Font(str(font_dir / "Nunito-Bold.ttf"), 40)
        self.dialogue_fonts = [
            pygame.font.Font(str(font_dir / "Nunito-Regular.ttf"), size)
            for size in (28, 26, 24, 22, 20, 18)
        ]
        self.banner_cache: dict[tuple[str, tuple[int, int, int]], pygame.Surface] = {}
        self.banner_font = pygame.font.Font(str(font_dir / "Nunito-ExtraBold.ttf"), 84)

        self._load_assets()

        self.buttons: list[Button] = []
        self.show_dictionary = False
        self.dictionary_page = 0  # spread index; four cards, two on each page
        self.page_anim = None
        self.zoomed_card: int | None = None
        self.zoom_t = 1.0
        self._card_cache: dict = {}
        self.review_fallacy_id: int | None = None
        self.review_age = 0.0
        self.show_reset_confirm = False
        self.pre_settings_state = "MENU"
        self.mouse_pos: tuple[float, float] = (-1, -1)
        # Dev mode is a session-only overlay. Saved progress is never touched,
        # so switching it off restores exactly what was there before.
        self.dev_unlocked = False
        self.dev_mode = False
        self.dev_input = ""
        self.dev_input_active = False
        self.dev_error = False

        self.state = "MENU"
        self.level = 1
        self.carousel_index = 0
        self.carousel_pos = 0.0
        self._ticket_cache: dict[tuple[int, bool, bool], pygame.Surface] = {}
        self.infinite = False
        self.health = game_rules.HEALTH_MAX
        self.enemy_health = game_rules.OPPONENT_HEALTH_MAX
        self.fallacy_ids: list[int] = []
        self.enemy_name = ""
        self.phase = "WARMUP"  # main levels: "WARMUP" then "ROUND"
        self.teaching_ids: list[int] = []
        self.teaching_added: set[int] = set()
        self.warmup_queue: list[int] = []
        self.paused = False
        self.fail_reason = ""
        self.infinite_correct = 0
        self.question_index = 0
        self.current_fallacy_id: int | None = None
        self.current_claim = ""
        self.last_claim_for: dict[int, str] = {}
        self.papers: list[Paper] = []
        self.timer = 0.0
        self.timer_max = game_rules.QUESTION_SECONDS
        self.answered = False
        self.result_label = ""
        self.result_correct = False
        self.feedback_timer = 0.0
        self.enemy_losses = 0
        self.enemy_flash = 0.0
        self.tomato_flash = 0.0
        self.toasts: list[list] = []
        self.gavel_timer = 0.0
        self.gavel_target = "MENU"
        self.infinite_final_correct = 0
        self.infinite_is_best = False
        self.intro_t = 0.0
        self.announce_text = ""
        self.announce_timer = 0.0
        self.dialogue_phase = "DONE"
        self.dialogue_timer = 0.0
        self.dialogue_speaker = ""
        self.dialogue_text = ""
        self.dialogue_char_count = 0.0
        self.dialogue_level_opened = False
        self.camera_y = 0.0
        self.foreground_camera_y = 0.0
        self.chef_camera_y = 0.0

    # -- asset loading ---------------------------------------------------

    def _load_assets(self) -> None:
        raw_bg = load_image("Background.png", (VIRTUAL_W, VIRTUAL_H - 400), (60, 38, 26))
        self.bg = cover_scale(raw_bg, (VIRTUAL_W, VIRTUAL_H), anchor_y=0.0)
        self.bg_gameplay = self.bg.copy()
        light_overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        light_overlay.fill((255, 255, 200, 32))
        self.bg_gameplay.blit(light_overlay, (0, 0))
        self.bg_pan = add_vertical_overscan(self.bg_gameplay, GAMEPLAY_PAN_PIXELS)
        # Each moving answer paper gets one randomly chosen food-themed backdrop.
        self.fallacy_paper_backgrounds = [
            load_image(f"bg_fallacies/{name}_bg.png")
            for name in ("bread", "lettuce", "cheese", "bacon")
        ]
        self.bg_faded = cover_scale(
            load_image("background_faded.png", (VIRTUAL_W, VIRTUAL_H - 200  ), (90, 60, 40)), (VIRTUAL_W, VIRTUAL_H), anchor_y=0.0
        )
        self.logo = load_image("LOGO_food_court.png", (600, 460), (214, 122, 54))
        # The intro animates the logo's size each frame; scaling from this copy
        # instead of the full-resolution original keeps that cheap.
        self.logo_intro = pygame.transform.smoothscale(
            self.logo, (INTRO_LOGO_WIDTH, round(INTRO_LOGO_WIDTH * self.logo.get_height() / self.logo.get_width()))
        )
        self.logo_small = pygame.transform.smoothscale(
            self.logo, (110, round(110 * self.logo.get_height() / self.logo.get_width()))
        )
        self.logo_small_faded = self.logo_small.copy()
        self.logo_small_faded.set_alpha(128)
        self.bread_button = self.fallacy_paper_backgrounds[0]
        # Align tables with the exact same cover crop as Background.png
        raw_tables = load_image("tables.png", (VIRTUAL_W, VIRTUAL_H), (0, 0, 0, 0))
        self.tables = cover_scale(raw_tables, (VIRTUAL_W, VIRTUAL_H), anchor_y=1.0)
        self.tables_pan = add_vertical_overscan(
            self.tables, round(GAMEPLAY_PAN_PIXELS * FOREGROUND_PAN_RATIO)
        )
        self.level_stamps = {
            enemy: load_image(name, (150, 150), (0, 0, 0, 0)) for enemy, name in LEVEL_STAMPS.items()
        }
        self.dictionary_icon = load_image("dictionary icon.PNG", (48, 64), (214, 122, 54))
        book = load_image("Untitled_Artwork 9.png", BOOK_CROP.size, (255, 247, 206))
        if book.get_width() >= BOOK_CROP.right and book.get_height() >= BOOK_CROP.bottom:
            book = book.subsurface(BOOK_CROP).copy()
        self.book_image = pygame.transform.smoothscale(book, book_display_size())
        width, height = self.book_image.get_size()
        gutter = max(10, width // 24)
        mid = width // 2
        self.page_gutter = gutter
        self.page_halves = (
            self.book_image.subsurface(pygame.Rect(0, 0, mid - gutter, height)).copy(),
            self.book_image.subsurface(pygame.Rect(mid + gutter, 0, width - mid - gutter, height)).copy(),
        )
        self.book_stitch = self.book_image.subsurface(
            pygame.Rect(mid - gutter, 0, gutter * 2, height)
        ).copy()
        # Numbered files run backwards: #18 / DictionaryCard18 is fallacy 1.
        self.dictionary_cards = {
            fid: load_image(f"DictionaryCard{19 - fid:02d}.png", (480, 390), CARD_WHITE)
            for fid in range(1, 19)
        }
        self.detail_cards = {
            fid: load_image(f"Dictionary Card/#{19 - fid:02d}.png", (602, 376), CARD_WHITE)
            for fid in range(1, 19)
        }
        self.add_cards = {
            fid: load_image(f"Add cards/#{19 - fid:02d}.png", (602, 472), CARD_WHITE)
            for fid in range(1, 19)
        }

        health_sheet = load_image("HealthBar_SpriteSheet.png", (11264, 1024), (214, 1122, 54))
        self.health_frames: list[pygame.Surface] = []
        target_h = 60
        for x, y, w, h in HEALTH_ICON_RECTS:
            rect = pygame.Rect(x, y, w, h).clip(health_sheet.get_rect())
            piece = health_sheet.subsurface(rect).copy()
            target_w = max(1, round(piece.get_width() * target_h / piece.get_height()))
            self.health_frames.append(pygame.transform.smoothscale(piece, (target_w, target_h)))

        self.peeler = Peeler(ASSET_DIR / "Peeler_SpriteSheet.png")
        self.peeler_frames = self.peeler.frames
        self.tomato = Tomato(ASSET_DIR / "Tomato_SpriteSheet.png")
        tomato_order = [1, 0, *range(2, len(self.tomato.frames))]
        self.tomato.frames = [self.tomato.frames[index] for index in tomato_order]
        self.chef = Chef(path=ASSET_DIR / "Chef_SpriteSheet.png")
        self.tomato_frames = self.tomato.frames
        self.chef_frames = self.chef.frames
        self.smashed_tomato = load_image("smashed tomato.png", (160, 160), (180, 50, 40, 0))

        # The Peeler class only wraps a five-frame strip, so it draws every enemy.
        self.enemies = {"Vegetable Peeler": self.peeler}
        for name, sheet in ENEMY_SHEETS.items():
            if name not in self.enemies:
                try:
                    self.enemies[name] = Peeler(ASSET_DIR / sheet)
                except RuntimeError:
                    self.enemies[name] = self.peeler
        diameter = LEVEL_CIRCLE_RECTS[0].width
        self.enemy_portraits = {
            name: circle_portrait(enemy.frames[0], diameter) for name, enemy in self.enemies.items()
        }
        self.enemy_portraits_locked = {
            name: circle_portrait(enemy.frames[0], diameter, bg=(70, 70, 70), darken=True)
            for name, enemy in self.enemies.items()
        }

        self.tomato_frames = [scale_square(f, CHARACTER_SIZE) for f in self.tomato_frames]
        self.chef_frames = [
            pygame.transform.smoothscale(
                frame,
                (
                    max(1, round(frame.get_width() * CHEF_SIZE / frame.get_height())),
                    CHEF_SIZE,
                ),
            )
            for frame in self.chef_frames
        ]

    # -- level/session setup ---------------------------------------------

    def _reset_session(self) -> None:
        self.health = game_rules.HEALTH_MAX
        self.enemy_health = game_rules.OPPONENT_HEALTH_MAX
        self.selector = FallacySelector()
        for fid in range(1, len(FALLACIES) + 1):
            stats = self.selector.stats_for(fid)
            stats.correct = self.progress.mastery_counts.get(fid, 0)
            stats.mastered = (
                fid in self.progress.mastered_ids or stats.correct >= game_rules.MASTERY_TARGET
            )
        self.question_index = 0
        self.infinite_correct = 0
        self.announce_timer = 0.0
        self.papers = []
        self.enemy_losses = 0
        self.enemy_flash = 0.0
        self.tomato_flash = 0.0
        self.toasts = []
        self.last_claim_for = {}
        self.show_dictionary = False
        self.page_anim = None
        self.zoomed_card = None
        self.review_fallacy_id = None
        self.review_age = 0.0
        self.show_reset_confirm = False
        self.paused = False
        self.fail_reason = ""
        self.dialogue_phase = "DONE"
        self.dialogue_timer = 0.0
        self.dialogue_speaker = ""
        self.dialogue_text = ""
        self.dialogue_char_count = 0.0
        self.dialogue_level_opened = False
        self.camera_y = 0.0
        self.foreground_camera_y = 0.0
        self.chef_camera_y = 0.0

    def start_level(self, level: int) -> None:
        """Main level: meet all three new fallacies, warm up, then fight."""
        self._reset_session()
        self.level = level
        self.infinite = False
        self.fallacy_ids = game_data.LEVELS[level]["fallacy_ids"]
        self.enemy_name = game_data.enemy_for_level(level)
        self.teaching_ids = list(self.fallacy_ids)
        self.teaching_added = set()
        self.warmup_queue = []
        if all(fid in self._dictionary_ids() for fid in self.fallacy_ids):
            # Nothing new to learn, so skip the cards and the warm-up.
            self.phase = "ROUND"
            self._announce("OFFICIAL ROUND — FIGHT!")
            self.next_question()
            return
        self.phase = "WARMUP"
        self.state = "TEACHING"

    def start_infinite(self) -> None:
        """Endless review of unlocked fallacies against beaten enemies."""
        self._reset_session()
        self.infinite = True
        self.phase = "ROUND"
        self.fallacy_ids = self._infinite_fallacy_ids()
        self.next_question()

    def _dictionary_ids(self) -> set[int]:
        if self.dev_mode:
            return {f.id for f in FALLACIES}
        return self.progress.dictionary_ids

    def _completed_enemies(self) -> list[str]:
        levels = sorted(game_data.LEVELS) if self.dev_mode else sorted(self.progress.completed_levels)
        names = [game_data.enemy_for_level(lvl) for lvl in levels if lvl in game_data.LEVELS]
        return list(dict.fromkeys(names))

    def _infinite_fallacy_ids(self) -> list[int]:
        return sorted(self._dictionary_ids())

    def _infinite_available(self) -> bool:
        return bool(self._completed_enemies()) and bool(self._infinite_fallacy_ids())

    def _quizzable_ids(self) -> list[int]:
        if self.infinite:
            return self._infinite_fallacy_ids()
        if self.phase == "WARMUP":
            return self.warmup_queue[:1]
        # Official round: everything unlocked up to and including this level.
        newest = max(self.fallacy_ids)
        return [fid for fid in sorted(self._dictionary_ids()) if fid <= newest] or list(self.fallacy_ids)

    def on_add_to_dictionary(self, fid: int | None = None) -> None:
        """Collect one of the three new cards; once all are in, warm up."""
        if self.state != "TEACHING":
            return
        if fid is None:
            remaining = [f for f in self.teaching_ids if f not in self.teaching_added]
            if not remaining:
                return
            fid = remaining[0]
        if fid not in self.teaching_ids or fid in self.teaching_added:
            return
        self.teaching_added.add(fid)
        self.progress.add_to_dictionary(fid)
        self.audio.play_sfx("dictionary")
        if len(self.teaching_added) == len(self.teaching_ids):
            self.warmup_queue = list(self.teaching_ids)
            self.rng.shuffle(self.warmup_queue)
            self.phase = "WARMUP"
            self._announce("WARM-UP: NO TIMER, NO DAMAGE")
            self.next_question()

    # -- questions ---------------------------------------------------

    def _pick_infinite_enemy(self, fid: int) -> str:
        enemies = self._completed_enemies() or [game_data.enemy_for_fallacy(fid)]
        with_claims = [name for name in enemies if game_data.claims_for(name, fid)]
        return self.rng.choice(with_claims or enemies)

    def next_question(self) -> None:
        pool = self._quizzable_ids()
        if not pool:
            return
        if self.phase == "WARMUP" and not self.infinite:
            fid = pool[0]
        else:
            fid = self.selector.choose(pool, self.rng)
        if self.infinite:
            self.enemy_name = self._pick_infinite_enemy(fid)
        bank = game_data.claims_for(self.enemy_name, fid) or game_data.claims_for(
            game_data.enemy_for_fallacy(fid), fid
        )
        if bank:
            last = self.last_claim_for.get(fid)
            choices = [c for c in bank if c != last] or bank
            claim = self.rng.choice(choices)
            self.last_claim_for[fid] = claim
        else:
            claim = f"({FALLACIES_BY_ID[fid].name} claim text pending for {self.enemy_name}.)"

        self.current_fallacy_id = fid
        self.current_claim = claim
        self.papers = []

        if self.infinite:
            self.timer_max = game_rules.infinite_question_seconds(self.question_index)
        else:
            self.timer_max = game_rules.QUESTION_SECONDS
        self.timer = self.timer_max
        self.answered = False

        if not self.dialogue_level_opened:
            self.dialogue_level_opened = True
            opening_text = JUDGE_INFINITE_OPENING if self.infinite else JUDGE_OPENINGS.get(self.level, JUDGE_OPENINGS[1])
            self._set_dialogue("Judge", opening_text, next_phase="OPPONENT_INTRO")
        else:
            self._set_dialogue(self.enemy_name or "Opponent", self.current_claim, next_phase="DONE")
        self.state = "GAMEPLAY"

    def _set_dialogue(self, speaker: str, text: str, next_phase: str) -> None:
        self.audio.stop_sfx("text")
        self.dialogue_speaker = speaker
        self.dialogue_text = text
        self.dialogue_char_count = 0.0
        self.dialogue_target_phase = next_phase
        self.dialogue_phase = "CENTER"
        self.dialogue_timer = DIALOGUE_CENTER_SECONDS

    def _advance_dialogue(self, dt: float) -> None:
        self.dialogue_timer -= dt
        self._advance_dialogue_text(dt)

        if self.dialogue_timer <= 0:
            if self.dialogue_phase == "CENTER":
                self.dialogue_phase = "MOVING"
                self.dialogue_timer = DIALOGUE_MOVE_SECONDS
            elif self.dialogue_phase == "MOVING":
                # Keep both Judge and opponent lines on screen until the
                # player finishes the dialogue and clicks to continue.
                self.dialogue_phase = "WAIT_CLICK"

    def _advance_dialogue_text(self, dt: float) -> None:
        full_len = len(self.dialogue_text)
        if self.dialogue_char_count >= full_len:
            self.audio.stop_sfx("text")
            return
        self.audio.play_sfx_loop("text")
        self.dialogue_char_count = min(
            float(full_len), self.dialogue_char_count + dt * TYPEWRITER_CHARS_PER_SEC
        )
        if self.dialogue_char_count >= full_len:
            self.audio.stop_sfx("text")

    def _dismiss_dialogue(self) -> None:
        """Called when player clicks through dialogue or tests advance."""
        full_len = len(self.dialogue_text)
        if int(self.dialogue_char_count) < full_len:
            # Complete the typing animation immediately on first click
            self.dialogue_char_count = float(full_len)
            self.audio.stop_sfx("text")
            return

        # Advance to next phase
        if self.dialogue_target_phase == "ACTIVE":
            self.audio.stop_sfx("text")
            self.after_feedback()
            return
        if self.dialogue_speaker == "Judge":
            # The Judge's intro click starts the opponent's line. Papers wait
            # for a separate click after that line has finished typing.
            self._set_dialogue(self.enemy_name or "Opponent", self.current_claim, next_phase="DONE")
        elif self.dialogue_phase in ("CENTER", "MOVING", "WAIT_CLICK", "OPPONENT_INTRO", "DONE"):
            self.dialogue_phase = "DONE"
            if not self.papers and self.current_fallacy_id:
                self._build_papers(self.current_fallacy_id)
            self.timer = self.timer_max

    def _build_papers(self, correct_id: int) -> None:
        if self.infinite:
            wrong_count = game_rules.infinite_option_count(self.infinite_correct) - 1
        else:
            wrong_count = game_rules.wrong_option_count(self.level)
        other_ids = [f.id for f in FALLACIES if f.id != correct_id]
        wrong_ids = self.rng.sample(other_ids, min(wrong_count, len(other_ids)))
        entries = [(FALLACIES_BY_ID[correct_id].name, True)]
        entries += [(FALLACIES_BY_ID[i].name, False) for i in wrong_ids]
        self.rng.shuffle(entries)
        
        self.papers = [
            Paper(text, is_correct, PAPER_BOUNDS, self.rng, self.fallacy_paper_backgrounds)
            for text, is_correct in entries
        ]

    def handle_paper_click(self, pos: tuple[int, int]) -> bool:
        if self.state != "GAMEPLAY" or self.answered or self.dialogue_phase not in ("DONE", "ACTIVE"):
            return False
        for paper in self.papers:
            if paper.rect().collidepoint(pos):
                self.resolve_answer(paper.is_correct, timeout=False)
                return True
        return False

    def resolve_answer(self, correct: bool, timeout: bool) -> None:
        self.answered = True
        self.chef.play()
        self.papers = []
        fid = self.current_fallacy_id
        assert fid is not None
        mastery_hit = self.selector.register_answer(fid, correct)
        stats = self.selector.stats_for(fid)
        self.progress.record_mastery(fid, stats.correct)

        warmup = self.phase == "WARMUP" and not self.infinite
        if correct:
            if self.infinite:
                # Infinite mode keeps the old rule: correct answers heal.
                self.health = min(game_rules.HEALTH_MAX, self.health + 1)
                self.infinite_correct += 1
            elif warmup:
                if self.warmup_queue and self.warmup_queue[0] == fid:
                    self.warmup_queue.pop(0)
                self.enemy_health = max(0, self.enemy_health - 1)
            else:
                self.enemy_health = max(0, self.enemy_health - 1)
            self.enemy_losses += 1
            self.enemy_flash = FLASH_DURATION
            self.result_label = "CORRECT"
            self.review_fallacy_id = None
            self.audio.play_sfx("correct")
        else:
            # The warm-up is practice: misses repeat the card but cost nothing.
            if not warmup:
                self.health = max(0, self.health - 1)
            self.audio.play_sfx("chomp")
            self.tomato_flash = FLASH_DURATION
            self.result_label = "TIME OUT" if timeout else "INCORRECT"
            # Show the matching dictionary card. It is not collected.
            self.review_fallacy_id = fid
            self.review_age = 0.0
            self.audio.play_sfx("incorrect")

        self.result_correct = correct
        if mastery_hit:
            self.toasts.append([f"{FALLACIES_BY_ID[fid].name} mastered!", TOAST_DURATION])
            self.audio.play_sfx("mastery")

        # Judge reacts to player's answer
        if correct:
            reaction = self.rng.choice(JUDGE_CORRECT_REACTIONS)
        else:
            reaction = self.rng.choice(JUDGE_WRONG_REACTIONS)
        self._set_dialogue("Judge", reaction, next_phase="ACTIVE")
        self.dialogue_phase = "WAIT_CLICK"
        self.dialogue_timer = 0.0

        self.feedback_timer = game_rules.FEEDBACK_HOLD_SECONDS
        self.question_index += 1
        self.state = "FEEDBACK"

    def after_feedback(self) -> None:
        self.review_fallacy_id = None
        if self.health <= 0:
            if self.infinite:
                self.finish_infinite()
            else:
                self.fail_reason = "You were turned into puree - try again!."
                self.start_gavel("LEVEL_FAILED")
            return

        if not self.infinite and self.enemy_health <= 0:
            self.progress.complete_level(self.level)
            self.toasts.append(["Judge: " + JUDGE_WIN_STATEMENT, TOAST_DURATION * 2])
            self.start_gavel("LEVEL_COMPLETE")
            return

        if not self.infinite and self.phase == "WARMUP" and not self.warmup_queue:
            self.phase = "ROUND"
            self._announce("OFFICIAL ROUND — FIGHT!")

        self.next_question()

    def _announce(self, text: str) -> None:
        """Slide a gold ribbon across; the next question waits until it leaves."""
        self.announce_text = text
        self.announce_timer = ANNOUNCE_SECONDS

    def start_gavel(self, target: str) -> None:
        self.gavel_target = target
        self.gavel_timer = GAVEL_DURATION
        self.state = "GAVEL"
        self.audio.play_sfx("knife_hit")

    def finish_infinite(self) -> None:
        self.infinite_final_correct = self.infinite_correct
        self.infinite_is_best = self.progress.record_infinite_result(INFINITE_SAVE_KEY, self.infinite_correct)
        self.start_gavel("INFINITE_RESULTS")

    def reset_game(self) -> None:
        self.progress.reset()
        self.state = "MENU"

    # -- pause ---------------------------------------------------

    def _can_pause(self) -> bool:
        return self.state in ("TEACHING", "GAMEPLAY", "FEEDBACK") and not self.show_dictionary

    def _pause(self) -> None:
        if self._can_pause():
            self.paused = True
            self.audio.stop_sfx("text")

    def _resume(self) -> None:
        self.paused = False

    def _exit_level(self) -> None:
        """Exit Game always returns to the levels page without a result popup.

        Infinite mode still saves the run's score if it is a new best.
        """
        self.paused = False
        self.papers = []
        self.review_fallacy_id = None
        if self.infinite:
            self.progress.record_infinite_result(INFINITE_SAVE_KEY, self.infinite_correct)
        self.state = "LEVEL_SELECT"

    # -- update ---------------------------------------------------

    def _desired_music(self) -> str | None:
        state = self.pre_settings_state if self.state in ("SETTINGS", "CREDITS") else self.state
        if state in LEVEL_MUSIC_STATES:
            return "infinite" if self.infinite else LEVEL_MUSIC.get(self.level, "main")
        return "main"

    def update(self, dt: float) -> None:
        track = self._desired_music()
        if track is not None:
            self.audio.play_music(track)
        self.audio.update(dt)
        if self.state == "LEVEL_SELECT":
            self.carousel_pos += (self.carousel_index - self.carousel_pos) * min(1.0, dt * CAROUSEL_SPEED)
        if self.state == "INTRO":
            # Cap the step so a slow first frame cannot skip the splash.
            self.intro_t += min(dt, 0.1)
            if self.intro_t >= INTRO_HOLD_SECONDS + INTRO_MOVE_SECONDS:
                self.state = "MENU"
        if self.state in ("GAMEPLAY", "FEEDBACK", "GAVEL"):
            target_camera_y = (
                GAMEPLAY_PAN_PIXELS if self.dialogue_speaker == "Judge"
                else -GAMEPLAY_PAN_PIXELS if self.dialogue_speaker else 0.0
            )
        else:
            target_camera_y = 0.0
        target_foreground_y = target_camera_y * FOREGROUND_PAN_RATIO
        target_chef_camera_y = -target_camera_y
        camera_step = GAMEPLAY_PAN_SPEED * dt
        if self.camera_y < target_camera_y:
            self.camera_y = min(target_camera_y, self.camera_y + camera_step)
        else:
            self.camera_y = max(target_camera_y, self.camera_y - camera_step)
        foreground_step = FOREGROUND_PAN_SPEED * dt
        if self.foreground_camera_y < target_foreground_y:
            self.foreground_camera_y = min(target_foreground_y, self.foreground_camera_y + foreground_step)
        else:
            self.foreground_camera_y = max(target_foreground_y, self.foreground_camera_y - foreground_step)
        chef_step = CHEF_PAN_SPEED * dt
        if self.chef_camera_y < target_chef_camera_y:
            self.chef_camera_y = min(target_chef_camera_y, self.chef_camera_y + chef_step)
        else:
            self.chef_camera_y = max(target_chef_camera_y, self.chef_camera_y - chef_step)
        if self.paused:
            return
        self.chef.update(dt)
        if self.announce_timer > 0:
            self.announce_timer = max(0.0, self.announce_timer - dt)
        elif self.state == "GAMEPLAY" and (not self.answered or self.dialogue_target_phase == "ACTIVE"):
            if self.dialogue_phase not in ("DONE", "ACTIVE"):
                self._advance_dialogue(dt)
            else:
                if self.dialogue_phase == "DONE":
                    self._advance_dialogue_text(dt)
                if self._timer_running():
                    self.timer -= dt
                if self.timer <= 0:
                    self.timer = 0
                    self.resolve_answer(False, timeout=True)
                else:
                    for paper in self.papers:
                        paper.update(dt)
        elif self.state == "FEEDBACK":
            self._advance_dialogue_text(dt)
            if self.review_fallacy_id is not None:
                self.review_age += dt
            else:
                self.feedback_timer = max(0.0, self.feedback_timer - dt)
        elif self.state == "GAVEL":
            self.gavel_timer -= dt
            if self.gavel_timer <= 0:
                self.state = self.gavel_target

        if self.page_anim is not None:
            self.page_anim["t"] += dt / PAGE_TURN_SECONDS
            if self.page_anim["t"] >= 1.0:
                self.dictionary_page = self.page_anim["target"]
                self.page_anim = None

        if self.zoomed_card is not None:
            self.zoom_t = min(1.0, self.zoom_t + dt / 0.18)

        self.enemy_flash = max(0.0, self.enemy_flash - dt)
        self.tomato_flash = max(0.0, self.tomato_flash - dt)
        for toast in self.toasts:
            toast[1] -= dt
        self.toasts = [t for t in self.toasts if t[1] > 0]

    def _timer_running(self) -> bool:
        """Warm-up questions have no time limit."""
        return self.infinite or self.phase != "WARMUP"

    # -- frame emotion mapping ---------------------------------------------------

    def _enemy_frame_index(self) -> int:
        if self.enemy_flash > 0:
            return 4
        if self.infinite:
            return min(3, self.enemy_losses // 3)
        return min(3, game_rules.OPPONENT_HEALTH_MAX - self.enemy_health)

    def _tomato_frame(self) -> pygame.Surface:
        if self.tomato_flash > 0:
            return self.tomato_frames[min(4, len(self.tomato_frames) - 1)]
        idx = min(3, max(0, game_rules.HEALTH_MAX - self.health))
        return self.tomato_frames[min(idx, len(self.tomato_frames) - 1)]

    # -- button layout ---------------------------------------------------

    def layout_buttons(self) -> None:
        self.buttons = []

        if self.state == "SETTINGS":
            self._layout_settings_buttons()
            return
        if self.show_dictionary:
            self._layout_dictionary_buttons()
            return

        if self.paused:
            cont = pygame.Rect(0, 0, 260, 58)
            cont.center = (PAUSE_POPUP_RECT.centerx, PAUSE_POPUP_RECT.top + 296)
            leave = cont.copy()
            leave.center = (PAUSE_POPUP_RECT.centerx, PAUSE_POPUP_RECT.top + 372)
            self.buttons.append(Button(cont, "Continue", self._resume))
            self.buttons.append(Button(leave, "Exit Game", self._exit_level))
            return

        if self._can_pause():
            self.buttons.append(Button(PAUSE_BUTTON_RECT, "", self._pause, style="icon", icon="pause"))
            self.buttons.append(Button(DICTIONARY_HUD_RECT, "", self._open_dictionary, style="icon", icon="book"))

        if self.state in ("LEVEL_COMPLETE", "LEVEL_FAILED", "INFINITE_RESULTS"):
            self.buttons.append(Button(pygame.Rect(1006, 18, 56, 56), "", self._open_dictionary,
                                       style="icon", icon="book"))
            self.buttons.append(Button(pygame.Rect(1126, 18, 56, 56), "", self._open_settings,
                                       style="icon", icon="gear"))

        if self.state == "MENU":
            self.buttons.extend(self._menu_buttons())
        elif self.state == "CREDITS":
            self.buttons.append(Button(RETURN_BUTTON_RECT, "Back", self._close_credits, style="secondary", radius=12))
        elif self.state == "HOW_TO_PLAY":
            self.buttons.append(Button(RETURN_BUTTON_RECT, "Back", self._go_menu, style="secondary", radius=12))
        elif self.state == "LEVEL_SELECT":
            self.buttons.append(Button(RETURN_BUTTON_RECT, "Back", self._go_menu, style="secondary", radius=12))
            self.buttons.append(Button(INFINITE_BUTTON_RECT, "Infinite Mode", self.start_infinite,
                                       enabled=self._infinite_available(), style="hidden"))
            levels = sorted(game_data.LEVELS)
            if self.carousel_index > 0:
                self.buttons.append(Button(CAROUSEL_ARROW_RECTS[0], "", lambda: self._scroll_carousel(-1),
                                           style="icon", icon="prev"))
            if self.carousel_index < len(levels) - 1:
                self.buttons.append(Button(CAROUSEL_ARROW_RECTS[1], "", lambda: self._scroll_carousel(1),
                                           style="icon", icon="next"))
            for i, level in enumerate(levels):
                offset = i - self.carousel_index
                if abs(offset) > 1:
                    continue
                if offset == 0:
                    unlocked = self._level_unlocked(level)
                    action = (lambda lvl=level: self._select_level(lvl)) if unlocked else self._noop
                    enabled = unlocked
                else:
                    action = lambda d=offset: self._scroll_carousel(d)
                    enabled = True
                self.buttons.append(Button(self._ticket_rect(offset), "", action, enabled=enabled, style="hidden"))
        elif self.state == "TEACHING":
            for fid in self.teaching_ids:
                if fid in self.teaching_added:
                    continue
                _card, button_rect = self._add_card_layout(fid)
                self.buttons.append(
                    Button(button_rect, "Add to Dictionary", lambda fid=fid: self.on_add_to_dictionary(fid), radius=14)
                )
        elif self.state in ("LEVEL_COMPLETE", "LEVEL_FAILED", "INFINITE_RESULTS"):
            home = pygame.Rect(460, 440, 160, 52)
            other = pygame.Rect(640, 440, 180, 52)
            self.buttons.append(Button(home, "Return", self._open_level_select, style="secondary", radius=12,
                                       icon="return"))
            if self.state == "LEVEL_COMPLETE":
                self.buttons.append(Button(other, "Next Level", self._next_level, radius=12))
            elif self.state == "LEVEL_FAILED":
                self.buttons.append(Button(other, "Try Again", self._try_again, radius=12))
            else:
                self.buttons.append(Button(other, "Play Again", self._replay_infinite, radius=12))

    def _layout_dictionary_buttons(self) -> None:
        self.buttons.append(Button(RETURN_BUTTON_RECT, "Back", self._close_dictionary, style="secondary", radius=12))

        if self.zoomed_card is not None:
            self.buttons.append(
                Button(pygame.Rect(0, 0, VIRTUAL_W, VIRTUAL_H), "", self._close_zoom, style="hidden")
            )
            return
        origin, left_rect, right_rect = self._book_geometry()
        turning = self.page_anim is not None
        if not turning:
            self._layout_card_buttons(left_rect, right_rect)
        if self._spread_count() <= 1:
            return
        left_half, right_half = self._half_rects(origin)
        self.buttons.append(
            Button(pygame.Rect(left_half.left - 80, left_half.centery - 36, 72, 72), "", self._prev_page,
                   enabled=not turning, style="icon", icon="prev")
        )
        self.buttons.append(
            Button(pygame.Rect(right_half.right + 8, right_half.centery - 36, 72, 72), "", self._next_page,
                   enabled=not turning, style="icon", icon="next")
        )
        self.buttons.append(Button(left_half, "", self._prev_page, enabled=not turning, style="hidden"))
        self.buttons.append(Button(right_half, "", self._next_page, enabled=not turning, style="hidden"))

    def _layout_card_buttons(self, left_rect: pygame.Rect, right_rect: pygame.Rect) -> None:
        ids = self._spread_ids(self.dictionary_page)
        slots = self._page_slots(left_rect) + self._page_slots(right_rect)
        for fid, slot in zip(ids, slots):
            if fid is None:
                continue
            hit = self._fitted_rect(self.dictionary_cards[fid], slot)
            self.buttons.append(Button(hit, "", lambda fid=fid: self._open_card(fid), style="hidden"))

    def _menu_buttons(self) -> list[Button]:
        # Dirty recipe book card layout with todo-list checklist buttons
        cx = MENU_CARD_RECT.centerx
        top = MENU_CARD_RECT.top + 60
        return [
            Button(pygame.Rect(cx - 130, top, 260, 50), "Play", self._open_level_select, style="pill", radius=10),
            Button(pygame.Rect(cx - 130, top + 62, 260, 50), "Instructions", self._open_how_to_play, style="todo", radius=10),
            Button(pygame.Rect(cx - 130, top + 124, 260, 50), "Dictionary", self._open_dictionary, style="todo", radius=10),
            Button(pygame.Rect(cx - 130, top + 186, 260, 50), "Settings", self._open_settings, style="todo", radius=10),
        ]

    def _layout_settings_buttons(self) -> None:
        self.buttons.append(Button(RETURN_BUTTON_RECT, "Back", self._close_settings,
                                   style="secondary", radius=12))
        self.buttons.append(Button(INFO_BUTTON_RECT, "", self._open_credits, style="icon", icon="info"))
        self.buttons.append(Button(DEV_INPUT_RECT, "", self._focus_dev_input, style="hidden"))
        if self.dev_unlocked:
            self.buttons.append(Button(DEV_SWITCH_RECT, "", self._toggle_dev_mode, style="hidden"))
        red = dict(fill=DANGER, border=DANGER_DARK, radius=10)
        if self.show_reset_confirm:
            half_w = (SETTINGS_RESET_RECT.width - 12) // 2
            r1 = pygame.Rect(SETTINGS_RESET_RECT.left, SETTINGS_RESET_RECT.top, half_w, SETTINGS_RESET_RECT.height)
            r2 = pygame.Rect(SETTINGS_RESET_RECT.left + half_w + 12, SETTINGS_RESET_RECT.top, half_w, SETTINGS_RESET_RECT.height)
            self.buttons.append(Button(r1, "Yes, Reset", self._confirm_reset, **red))
            self.buttons.append(Button(r2, "Cancel", self._cancel_reset, style="secondary", radius=10))
        else:
            self.buttons.append(Button(SETTINGS_RESET_RECT, "Reset All Progress", self._ask_reset, **red))

    # -- button callbacks ---------------------------------------------------

    def _open_dictionary(self) -> None:
        self.show_dictionary = True
        self.dictionary_page = 0
        self.page_anim = None
        self.zoomed_card = None

    def _close_dictionary(self) -> None:
        self.show_dictionary = False
        self.page_anim = None
        self.zoomed_card = None

    def _open_card(self, fid: int) -> None:
        if self.page_anim is not None:
            return
        self.zoomed_card = fid
        self.zoom_t = 0.0

    def _close_zoom(self) -> None:
        self.zoomed_card = None

    def _dictionary_entries(self) -> list[int]:
        return sorted(self._dictionary_ids())

    def _spread_starts(self) -> list[int]:
        """Each picture is a window of four cards, two on each page.

        Windows step forward, and the last one is pulled back so it is
        still four cards whenever that many have been collected.
        """
        count = len(self._dictionary_entries())
        if count == 0:
            return []
        if count <= CARDS_PER_SPREAD:
            return [0]
        last = count - CARDS_PER_SPREAD
        starts = list(range(0, last + 1, 2))
        if starts[-1] != last:
            starts.append(last)
        return starts

    def _spread_count(self) -> int:
        return len(self._spread_starts())

    def _turn_page(self, direction: int) -> None:
        if self.page_anim is not None or self.zoomed_card is not None:
            return
        spreads = self._spread_count()
        if spreads <= 1:
            return
        self.page_anim = {
            "t": 0.0,
            "direction": direction,
            "from": self.dictionary_page,
            "target": (self.dictionary_page + direction) % spreads,
        }

    def _prev_page(self) -> None:
        self._turn_page(-1)

    def _next_page(self) -> None:
        self._turn_page(1)

    def _open_settings(self) -> None:
        self.pre_settings_state = self.state
        self.show_reset_confirm = False
        self.state = "SETTINGS"

    def _close_settings(self) -> None:
        self.show_reset_confirm = False
        self.dev_input_active = False
        self.state = self.pre_settings_state

    def _open_credits(self) -> None:
        self.show_reset_confirm = False
        self.dev_input_active = False
        self.state = "CREDITS"

    def _close_credits(self) -> None:
        self.state = "SETTINGS"

    def prewarm(self) -> None:
        """Build the level-select tickets before play starts.

        The first frame of level select built every ticket at once; in the
        browser that frame ran long enough to make the audio hitch on click.
        """
        self._draw_level_select(pygame.Surface((VIRTUAL_W, VIRTUAL_H)))

    def start_intro(self) -> None:
        """Startup splash: a big centered logo that glides into the menu."""
        self.intro_t = 0.0
        self.state = "INTRO"

    def _focus_dev_input(self) -> None:
        self.dev_input_active = True

    def _toggle_dev_mode(self) -> None:
        self.dev_mode = not self.dev_mode
        self._card_cache.clear()

    def handle_key(self, event: pygame.event.Event) -> None:
        """Typing into the dev password box on the settings page."""
        if self.state == "LEVEL_SELECT" and event.type == pygame.KEYDOWN and not self.show_dictionary:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self._scroll_carousel(-1)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self._scroll_carousel(1)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self._select_level(sorted(game_data.LEVELS)[self.carousel_index])
            return
        if self.state != "SETTINGS" or not self.dev_input_active:
            return
        if event.type == pygame.TEXTINPUT:
            if len(self.dev_input) < 20:
                self.dev_input += event.text
            self.dev_error = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.dev_input = self.dev_input[:-1]
                self.dev_error = False
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.submit_dev_password()
            elif event.key == pygame.K_ESCAPE:
                self.dev_input_active = False

    def submit_dev_password(self) -> None:
        if self.dev_input == DEV_PASSWORD:
            self.dev_unlocked = True
            self.dev_input_active = False
            self.dev_error = False
        else:
            self.dev_error = True
        self.dev_input = ""

    def _volume_rows(self) -> tuple[list[pygame.Rect], list[pygame.Rect]] | None:
        """Row and track rects of the volume sliders on screen, if any."""
        if self.state == "SETTINGS":
            return SETTINGS_ROW_RECTS, SETTINGS_SLIDER_RECTS
        if self.paused:
            return PAUSE_ROW_RECTS, PAUSE_SLIDER_RECTS
        return None

    def _set_slider(self, index: int, x: float) -> None:
        rows = self._volume_rows()
        if rows is None:
            return
        track = rows[1][index]
        volume = max(0.0, min(1.0, (x - track.left) / track.width))
        if index == 0:
            self.audio.set_music_volume(volume)
        else:
            self.audio.set_sfx_volume(volume)

    def _save_volumes(self) -> None:
        self.progress.music_volume = self.audio.music_volume
        self.progress.sfx_volume = self.audio.sfx_volume
        self.progress.save()

    def handle_press(self, pos: tuple[int, int]) -> bool:
        """Handle press-time interactions and report whether one consumed it."""
        rows = self._volume_rows()
        if rows is not None:
            for i, row in enumerate(rows[0]):
                if row.inflate(0, 10).collidepoint(pos):
                    self.dragging_slider = i
                    self._set_slider(i, pos[0])
                    return True
        # Route buttons, dialogue advances, and answer papers through one
        # press-time path so the matching release cannot count as a second click.
        return self.handle_click(pos)

    def handle_drag(self, pos: tuple[int, int]) -> None:
        if self.dragging_slider is not None:
            self._set_slider(self.dragging_slider, pos[0])

    def handle_release(self) -> None:
        if self.dragging_slider is not None:
            self.dragging_slider = None
            self._save_volumes()
            self.audio.play_sfx("click")

    def _ask_reset(self) -> None:
        self.show_reset_confirm = True

    def _cancel_reset(self) -> None:
        self.show_reset_confirm = False

    def _confirm_reset(self) -> None:
        self.reset_game()

    def _replay_infinite(self) -> None:
        self.start_infinite()

    def _try_again(self) -> None:
        self.start_level(self.level)

    def _go_home(self) -> None:
        self.state = "MENU"

    def _go_menu(self) -> None:
        self.state = "MENU"

    def _open_how_to_play(self) -> None:
        self.state = "HOW_TO_PLAY"

    def _open_level_select(self) -> None:
        # Open the carousel on the furthest level the player can play.
        levels = sorted(game_data.LEVELS)
        self.carousel_index = max(i for i, lvl in enumerate(levels) if self._level_unlocked(lvl))
        self.carousel_pos = float(self.carousel_index)
        self.state = "LEVEL_SELECT"

    def _scroll_carousel(self, step: int) -> None:
        self.carousel_index = max(0, min(len(game_data.LEVELS) - 1, self.carousel_index + step))

    def _ticket_rect(self, offset: float) -> pygame.Rect:
        """Screen rect of a carousel ticket `offset` slots from the center."""
        d = min(abs(offset), 2.0)
        i = min(int(d), 1)
        t = d - i
        x = CAROUSEL_SPACING[i] + (CAROUSEL_SPACING[i + 1] - CAROUSEL_SPACING[i]) * t
        scale = CAROUSEL_SCALE[i] + (CAROUSEL_SCALE[i + 1] - CAROUSEL_SCALE[i]) * t
        rect = pygame.Rect(0, 0, round(TICKET_SIZE[0] * scale), round(TICKET_SIZE[1] * scale))
        rect.center = (round(TICKET_CENTER[0] + x * (1 if offset >= 0 else -1)), TICKET_CENTER[1])
        return rect

    def _level_unlocked(self, level: int) -> bool:
        """Levels open in order: each needs the previous one completed."""
        if level not in game_data.LEVELS:
            return False
        return self.dev_mode or level == 1 or (level - 1) in self.progress.completed_levels

    def _select_level(self, level: int) -> None:
        if self._level_unlocked(level):
            self.start_level(level)

    def _next_level(self) -> None:
        next_level = self.level + 1
        if self._level_unlocked(next_level):
            self.start_level(next_level)
        else:
            self.state = "LEVEL_SELECT"

    def _noop(self) -> None:
        pass

    # -- event handling ---------------------------------------------------

    def handle_click(self, pos: tuple[int, int]) -> bool:
        if self.state == "SETTINGS" and not DEV_INPUT_RECT.collidepoint(pos):
            self.dev_input_active = False
        for button in self.buttons:
            if button.enabled and button.rect.collidepoint(pos):
                self.audio.play_sfx("click")
                button.action()
                return True
        if self.state == "FEEDBACK":
            self._dismiss_dialogue()
            return True
        if not self.paused and not self.show_dictionary and self.state != "SETTINGS":
            if self.state == "GAMEPLAY" and self.dialogue_phase in ("WAIT_CLICK", "OPPONENT_INTRO", "POST_VERDICT_WIN", "POST_VERDICT_LOSE"):
                self._dismiss_dialogue()
                return True
            return self.handle_paper_click(pos)
        return False

    # -- drawing ---------------------------------------------------

    def draw(self, surf: pygame.Surface) -> None:
        if self.show_dictionary:
            surf.blit(self.bg, (0, 0))
            self._draw_dictionary(surf)
            self._draw_ui_buttons(surf)
            return

        faded_states = ("INTRO", "MENU", "HOW_TO_PLAY", "LEVEL_SELECT", "SETTINGS", "CREDITS",
                        "LEVEL_COMPLETE", "LEVEL_FAILED", "INFINITE_RESULTS")
        gameplay_states = ("GAMEPLAY", "FEEDBACK", "GAVEL")
        if self.state in gameplay_states:
            source_y = GAMEPLAY_PAN_PIXELS - round(self.camera_y)
            surf.blit(self.bg_pan, (0, 0), pygame.Rect(0, source_y, VIRTUAL_W, VIRTUAL_H))
        else:
            surf.blit(self.bg_faded if self.state in faded_states else self.bg, (0, 0))
        if self.state in ("LEVEL_SELECT", "LEVEL_COMPLETE", "LEVEL_FAILED", "INFINITE_RESULTS"):
            logo = self.logo_small_faded if self.state == "LEVEL_SELECT" else self.logo_small
            surf.blit(logo, logo.get_rect(bottomright=(VIRTUAL_W - 24, VIRTUAL_H - 16)))

        if self.state == "INTRO":
            self._draw_intro(surf)
        elif self.state == "MENU":
            self._draw_menu(surf)
        elif self.state == "CREDITS":
            self._draw_credits(surf)
        elif self.state == "HOW_TO_PLAY":
            self._draw_how_to_play(surf)
        elif self.state == "LEVEL_SELECT":
            self._draw_level_select(surf)
        elif self.state == "SETTINGS":
            self._draw_settings(surf)
        elif self.state == "TEACHING":
            self._draw_hud(surf)
            self._draw_teaching_cards(surf)
        elif self.state in ("GAMEPLAY", "FEEDBACK"):
            self._draw_gameplay(surf)
        elif self.state == "GAVEL":
            self._draw_gameplay_frozen(surf)
            self._draw_gavel(surf)
        elif self.state == "LEVEL_COMPLETE":
            self._draw_result_card(surf, "LEVEL COMPLETE", CORRECT_COLOR)
        elif self.state == "LEVEL_FAILED":
            self._draw_result_card(surf, "LEVEL FAILED", INCORRECT_COLOR)
        elif self.state == "INFINITE_RESULTS":
            self._draw_infinite_results(surf)
        self._draw_toasts(surf)

        if self.paused:
            self._draw_pause_popup(surf)

        self._draw_ui_buttons(surf)

        # Draw the answer banner last so review cards, toasts, and controls
        # cannot cover it during the feedback state.
        if self.state == "FEEDBACK":
            self._draw_feedback_banner(surf)
        if self.announce_timer > 0 and self.state == "GAMEPLAY":
            self._draw_announce_banner(surf)

    def _is_hovered(self, rect: pygame.Rect) -> bool:
        return rect.collidepoint(self.mouse_pos)

    def _draw_ui_buttons(self, surf: pygame.Surface, buttons: list[Button] | None = None) -> None:
        for button in self.buttons if buttons is None else buttons:
            button.hovered = button.style != "hidden" and self._is_hovered(button.rect)
            if button.style == "icon":
                font = self.fonts["body_bold"]
            elif button.style == "link":
                font = self.fonts["large"]
            elif button.label in ("Play", "Enter"):
                font = self.fonts["body_bold"]
            elif button.rect.height < 30:
                font = self.fonts["paper"]
            elif button.image is not None:
                font = self.fonts["body_bold"]
            else:
                font = self.fonts["body_bold"] if button.style == "secondary" else self.fonts["body"]
            button.draw(surf, font, self.fonts["large_bold"])

    def _draw_pause_popup(self, surf: pygame.Surface) -> None:
        dim = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        dim.fill((*OVERLAY_DARK, 180))
        surf.blit(dim, (0, 0))
        draw_card(surf, PAUSE_POPUP_RECT, radius=RADIUS_PANEL)
        draw_text(surf, self.fonts["title_bold"], "PAUSED", PRIMARY, center=(PAUSE_POPUP_RECT.centerx, PAUSE_POPUP_RECT.top + 56))
        pygame.draw.line(surf, LINE, (PAUSE_POPUP_RECT.left + 36, PAUSE_POPUP_RECT.top + 92),
                         (PAUSE_POPUP_RECT.right - 36, PAUSE_POPUP_RECT.top + 92), 1)
        self._draw_volume_sliders(surf, PAUSE_ROW_RECTS, PAUSE_SLIDER_RECTS)

    def _draw_intro(self, surf: pygame.Surface) -> None:
        move = max(0.0, min(1.0, (self.intro_t - INTRO_HOLD_SECONDS) / INTRO_MOVE_SECONDS))
        ease = 1 - (1 - move) ** 3
        if move > 0:
            # The menu fades in underneath while the logo glides into place.
            layer = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
            self._draw_menu(layer, draw_logo=False)
            self._draw_ui_buttons(layer, self._menu_buttons())
            layer.set_alpha(round(255 * ease))
            surf.blit(layer, (0, 0))
        logo_w = round(INTRO_LOGO_WIDTH + (MENU_LOGO_WIDTH - INTRO_LOGO_WIDTH) * ease)
        logo_h = round(logo_w * self.logo.get_height() / self.logo.get_width())
        center = (
            round(VIRTUAL_W // 2 + (MENU_LOGO_CENTER[0] - VIRTUAL_W // 2) * ease),
            round(VIRTUAL_H // 2 + (MENU_LOGO_CENTER[1] - VIRTUAL_H // 2) * ease),
        )
        logo = cached_smoothscale(self.logo_intro, (logo_w, logo_h))
        surf.blit(logo, logo.get_rect(center=center))

    def _draw_credits(self, surf: pygame.Surface) -> None:
        paper = SETTINGS_PAPER_RECT
        draw_card(surf, paper, radius=RADIUS_PANEL)
        draw_text(surf, self.fonts["title_bold"], "Information", INK, center=(paper.centerx, paper.top + 70))
        pygame.draw.line(surf, LINE, (paper.left + 36, paper.top + 110), (paper.right - 36, paper.top + 110), 1)
        y = paper.top + 150
        for heading, text in CREDITS_LINES:
            draw_text(surf, self.fonts["body_bold"], heading, PRIMARY, center=(paper.centerx, y))
            for line in wrap_text(text, self.fonts["small"], paper.width - 72):
                y += 30
                draw_text(surf, self.fonts["small"], line, INK, center=(paper.centerx, y))
            y += 64

    def _draw_menu(self, surf: pygame.Surface, draw_logo: bool = True) -> None:
        # Dirty recipe book overlay behind the logo and menu settings
        book_rect = pygame.Rect(VIRTUAL_W // 2 - 250, 40, 500, 630)
        draw_shadow(surf, book_rect, radius=20, offset=(0, 6), alpha=90, blur=12)
        # Warm dirty recipe book paper base
        paper_bg = (248, 242, 226)
        draw_rounded_rect(surf, book_rect, paper_bg, radius=20, border=(188, 168, 144), border_width=2)
        # Faint ruled recipe lines
        for y_line in range(book_rect.top + 220, book_rect.bottom - 40, 28):
            pygame.draw.line(surf, (228, 218, 202), (book_rect.left + 24, y_line), (book_rect.right - 24, y_line), 1)
        # Subtle coffee/grease stain ring accent in the corner
        draw_smooth_circle(surf, (215, 192, 165, 35), (book_rect.right - 60, book_rect.top + 70), 38, border=(195, 170, 140, 45), border_width=3)
        draw_smooth_circle(surf, (215, 192, 165, 35), (book_rect.right - 30, book_rect.top + 90), 20, border=(195, 170, 140, 45), border_width=3)
        draw_smooth_circle(surf, (215, 192, 165, 25), (book_rect.left + 50, book_rect.bottom - 70), 28, border=(195, 170, 140, 35), border_width=2)
        draw_smooth_circle(surf, (215, 192, 165, 25), (book_rect.left + 90, book_rect.bottom - 50), 40, border=(195, 170, 140, 35), border_width=2)
        # Recipe header text
        draw_text(surf, self.fonts["paper"], "RECIPE FOR LOGICAL FALLACIES", (160, 138, 116), center=(book_rect.centerx, book_rect.top + 34))

        # Main Logo scaled nicely in the recipe book
        logo_w = MENU_LOGO_WIDTH
        logo_h = int(logo_w * self.logo.get_height() / self.logo.get_width())
        if draw_logo:
            logo_scaled = cached_smoothscale(self.logo, (logo_w, logo_h))
            surf.blit(logo_scaled, logo_scaled.get_rect(center=MENU_LOGO_CENTER))

    def _draw_how_to_play(self, surf: pygame.Surface) -> None:
        panel = pygame.Rect(180, 50, 920, 620)
        draw_card(surf, panel, radius=RADIUS_PANEL)
        draw_text(surf, self.fonts["title_bold"], "How to Play", INK, center=(panel.centerx, panel.top + 46))
        pygame.draw.line(surf, LINE, (panel.left + 40, panel.top + 78), (panel.right - 40, panel.top + 78), 2)

        steps = [
            ("1. Learn New Fallacies", "Each level introduces three new fallacies. Add them to your dictionary to use as reference during the trial."),
            ("2. Warm-Up Round", "Practice identifying the new fallacies with no timer and no health damage."),
            ("3. Official Kitchen Trial", "Read the opponent's argument and click the ingredient with the corresponding fallacy before the timer expires!"),
            ("4. Win the Trail", "Correct answers damage the opponent; wrong answers or running out of time damage you. Complete the first level to unlock Infinite Mode!"),
        ]

        y = panel.top + 94
        for title, desc in steps:
            # Bullet badge
            chip_rect = pygame.Rect(panel.left + 48, y, 420, 45)
            draw_rounded_rect(surf, chip_rect, SURFACE_ALT, radius=6, border=LINE, border_width=1)
            draw_text(surf, self.fonts["body_bold"], title, PRIMARY, midleft=(chip_rect.left + 12, chip_rect.centery))
            
            wrapped = wrap_text(desc, self.fonts["body"], panel.width - 120)
            for j, line in enumerate(wrapped):
                draw_text(surf, self.fonts["body"], line, INK, topleft=(panel.left + 52, y + 34 + j * 24))
            y += 38 + len(wrapped) * 24 + 10

    def _draw_level_select(self, surf: pygame.Surface) -> None:
        # Title
        draw_shadow_text(surf, self.fonts["title_bold"], "Select a Level", TEXT_ON_DARK, offset=2, alpha=160, center=(VIRTUAL_W // 2, 70))
        draw_shadow_text(surf, self.fonts["small"], "Master all logical fallacies across 6 culinary trials", TEXT_ON_DARK, offset=1, alpha=140, center=(VIRTUAL_W // 2, 110))

        # Ticket carousel, drawn farthest first so the center ticket sits on top
        levels = sorted(game_data.LEVELS)
        order = sorted(range(len(levels)), key=lambda i: -abs(i - self.carousel_pos))
        for i in order:
            offset = i - self.carousel_pos
            if abs(offset) > 2.4:
                continue
            level = levels[i]
            rect = self._ticket_rect(offset)
            if abs(offset) < 0.5 and self._level_unlocked(level) and self._is_hovered(rect):
                rect = rect.inflate(10, 14)
            draw_shadow(surf, rect, radius=4, offset=(0, 6), alpha=80, blur=10)
            ticket = cached_smoothscale(self._ticket_surface(level), rect.size)
            d = min(abs(offset), 2.0)
            k = min(int(d), 1)
            dim = round(CAROUSEL_DIM[k] + (CAROUSEL_DIM[k + 1] - CAROUSEL_DIM[k]) * (d - k))
            surf.blit(ticket, rect)
            if dim:
                # Shade on the screen, not the shared cached ticket.
                shade = pygame.Surface(rect.size, pygame.SRCALPHA)
                shade.fill((*OVERLAY_DARK, dim))
                surf.blit(shade, rect)

        # Infinite Mode banner card below
        inf_card = INFINITE_BUTTON_RECT
        inf_avail = self._infinite_available()
        inf_hover = inf_avail and self._is_hovered(inf_card)
        bg_col = (255, 255, 255) if inf_hover else (SURFACE if inf_avail else SURFACE_ALT)
        b_col = GOLD if (inf_avail and inf_hover) else (LINE_STRONG if inf_avail else LINE)
        draw_card(surf, inf_card, radius=18, fill=bg_col, border=b_col)

        inf_title_col = INK if inf_avail else INK_SOFT
        draw_text(surf, self.fonts["large_bold"], "Infinite Mode", inf_title_col, topleft=(inf_card.left + 32, inf_card.top + 20))
        if inf_avail:
            best = self.progress.infinite_best_correct.get(INFINITE_SAVE_KEY, 0)
            hint = f"Endless survival | Best: {best} correct" if best else "Endless survival trial"
            draw_text(surf, self.fonts["small"], hint, INK_SOFT, topleft=(inf_card.left + 34, inf_card.top + 60))
            draw_chip(surf, self.fonts["body_bold"], "PLAY ∞", fill=PRIMARY, color=TEXT_ON_DARK, center=(inf_card.right - 90, inf_card.centery))
        else:
            draw_text(surf, self.fonts["small"], "Defeat Level 1 to unlock Infinite Mode", INK_SOFT, topleft=(inf_card.left + 34, inf_card.top + 50))
            draw_chip(surf, self.fonts["body_bold"], "LOCKED", fill=(180, 170, 160), color=TEXT_ON_DARK, center=(inf_card.right - 90, inf_card.centery))

    def _ticket_surface(self, level: int) -> pygame.Surface:
        """A level's restaurant-ticket card at full size, cached per lock state."""
        unlocked = self._level_unlocked(level)
        key = (level, unlocked, level in self.progress.completed_levels)
        if key in self._ticket_cache:
            return self._ticket_cache[key]
        w, h = TICKET_SIZE
        ticket = pygame.Surface((w, h), pygame.SRCALPHA)
        ticket.fill(TICKET_PAPER)
        # Header: "LEVEL #n", then the order slip's little boxes
        draw_text(ticket, self.fonts["title_bold"], f"LEVEL #{level}", TICKET_RED, midleft=(22, 52))
        pygame.draw.line(ticket, TICKET_RULE, (0, 96), (w, 96), 2)
        for x in (round(w * 0.2), round(w * 0.42)):
            pygame.draw.line(ticket, TICKET_RULE, (x, 96), (x, 136), 2)
        # Ruled table area
        table = pygame.Rect(0, 136, w, h - 136 - 28)
        pygame.draw.rect(ticket, TICKET_TABLE, table)
        pygame.draw.line(ticket, TICKET_RULE, (0, table.top), (w, table.top), 2)
        for y in range(table.top + 48, table.bottom - 8, 52):
            pygame.draw.line(ticket, TICKET_RULE, (0, y), (w, y - 4), 2)
        pygame.draw.line(ticket, TICKET_RULE, (round(w * 0.75), table.top), (round(w * 0.75), table.bottom), 2)
        # The order: tomato v. <opponent>
        enemy = game_data.enemy_for_level(level)
        font = self.fonts["body_bold"]
        lines = ["tomato", "v."] + wrap_text(enemy.lower(), font, round(w * 0.7))
        y = table.top + 30
        for j, line in enumerate(lines):
            draw_text(ticket, font, line, TICKET_INK, midleft=(24 + min(j, 2) * 26, y))
            y += 36
        if level in self.progress.completed_levels:
            draw_chip(ticket, self.fonts["paper"], "CLEARED", fill=SECONDARY, color=TEXT_ON_DARK,
                      center=(round(w * 0.71), 116))
        stamp = self.level_stamps.get(enemy)
        if stamp is not None:
            stamp = pygame.transform.smoothscale(stamp, (112, 112))
            stamp.set_alpha(215)
            ticket.blit(stamp, stamp.get_rect(bottomright=(w - 10, h - 34)))
        pygame.draw.rect(ticket, TICKET_BORDER, ticket.get_rect(), 3)
        if not unlocked:
            ticket = pygame.transform.grayscale(ticket)
            fog = pygame.Surface((w, h), pygame.SRCALPHA)
            fog.fill((255, 255, 255, 90))
            ticket.blit(fog, (0, 0))
            center = (w // 2, h // 2 + 20)
            draw_smooth_circle(ticket, (70, 66, 64, 220), center, 52)
            draw_icon(ticket, "lock", center, 54, (240, 240, 240))
        self._ticket_cache[key] = ticket
        return ticket

    def _fitted_card(self, image: pygame.Surface, max_size: tuple[int, int], center: tuple[int, int]) -> pygame.Rect:
        fit = min(max_size[0] / image.get_width(), max_size[1] / image.get_height())
        rect = pygame.Rect(0, 0, max(1, round(image.get_width() * fit)), max(1, round(image.get_height() * fit)))
        rect.center = center
        return rect

    def _add_card_layout(self, fid: int) -> tuple[pygame.Rect, pygame.Rect]:
        image = self.add_cards[fid]
        count = max(1, len(self.teaching_ids))
        index = self.teaching_ids.index(fid) if fid in self.teaching_ids else 0
        slot_w = (VIRTUAL_W - 60) // count
        center = (30 + slot_w * index + slot_w // 2, 360)
        card = self._fitted_card(image, (slot_w - 20, 390), center)
        button = pygame.Rect(0, 0, card.width - 24, 50)
        button.midtop = (card.centerx, card.bottom + 16)
        return card, button

    def _draw_teaching_cards(self, surf: pygame.Surface) -> None:
        overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        overlay.fill((*OVERLAY_DARK, 180))
        surf.blit(overlay, (0, 0))
        draw_shadow_text(surf, self.fonts["title_bold"], "New Fallacies!", TEXT_ON_DARK, offset=2, alpha=160, center=(VIRTUAL_W // 2, 120))
        added_txt = f"Add all three to your dictionary to start the warm-up ({len(self.teaching_added)}/{len(self.teaching_ids)})"
        draw_shadow_text(surf, self.fonts["body"], added_txt, TEXT_ON_DARK, offset=1, alpha=140, center=(VIRTUAL_W // 2, 164))

        for fid in self.teaching_ids:
            image = self.add_cards.get(fid)
            if image is None:
                continue
            card, button = self._add_card_layout(fid)
            draw_shadow(surf, card, radius=16, offset=(0, 6), alpha=70, blur=10)
            surf.blit(cached_smoothscale(image, card.size), card)
            if fid in self.teaching_added:
                draw_rounded_rect(surf, button, SECONDARY, 12, SECONDARY_DARK, 2)
                draw_icon(surf, "check", (button.centerx - 50, button.centery), 24, TEXT_ON_DARK)
                draw_text(surf, self.fonts["body_bold"], "Added", TEXT_ON_DARK, center=(button.centerx + 14, button.centery))

    def _draw_hud(self, surf: pygame.Surface) -> None:
        # Fighting game health bar stretching across top, featuring HealthBar_SpriteSheet frames
        # Left bar: Tomato
        # Right bar: Opponent
        # Center: Timer ring/medallion & Mode / Level pill

        # Bar dimensions & geometry (moved down for balanced vertical breathing room)
        bar_h = HUD_BAR_LEFT.height
        center_x = HUD_TIMER_CENTER[0]

        left_track = HUD_BAR_LEFT
        right_track = HUD_BAR_RIGHT

        # Select the matching sprite-sheet frame for each current health value.
        # The frames are stretched into the enlarged slots; no empty track is
        # drawn behind them.
        player_idx = min(len(self.health_frames) - 1, max(0, game_rules.HEALTH_MAX - self.health))
        left_sprite = self.health_frames[player_idx]
        target_h = bar_h
        left_w = max(1, round(left_sprite.get_width() * target_h / left_sprite.get_height()))
        # Scale the cached original, then flip the small result.
        left_scaled = pygame.transform.flip(cached_smoothscale(left_sprite, (left_w, target_h)), True, False)
        # Keep the outside edge fixed so damage makes the bar recede inward.
        surf.blit(left_scaled, (left_track.left, left_track.top))

        opp_hp = self.enemy_health if not self.infinite else max(1, 5 - (self.enemy_losses % 5))
        opponent_max = 5 if self.infinite else game_rules.OPPONENT_HEALTH_MAX
        opponent_idx = min(
            len(self.health_frames) - 1,
            max(0, round((opponent_max - opp_hp) * (len(self.health_frames) - 1) / opponent_max)),
        )
        right_sprite = self.health_frames[opponent_idx]
        right_w = max(1, round(right_sprite.get_width() * target_h / right_sprite.get_height()))
        right_scaled = cached_smoothscale(right_sprite, (right_w, target_h))
        # Mirror the player bar's inward retreat from the right screen edge.
        surf.blit(right_scaled, (right_track.right - right_w, right_track.top))

        # Names with soft drop shadow underneath
        draw_shadow_text(surf, self.fonts["body_bold"], "Tomato", TEXT_ON_DARK, offset=2, alpha=160, topleft=(left_track.left + 4, left_track.bottom + 8))
        opp_display_name = self.enemy_name or "Opponent"
        draw_shadow_text(surf, self.fonts["body_bold"], opp_display_name, TEXT_ON_DARK, offset=2, alpha=160, topright=(right_track.right - 4, right_track.bottom + 8))

        # Round Portraits on the far left and far right with smooth circle borders
        # Left: Tomato
        tomato_p = circle_portrait(self.tomato_frames[0], HUD_PORTRAIT_D)
        p_rect_left = tomato_p.get_rect(center=HUD_PORTRAIT_LEFT)
        draw_shadow(surf, p_rect_left, radius=HUD_PORTRAIT_D // 2, offset=(0, 4), alpha=80, blur=6)
        surf.blit(tomato_p, p_rect_left)
        draw_smooth_circle(surf, (0, 0, 0, 0), HUD_PORTRAIT_LEFT, HUD_PORTRAIT_D // 2, border=LINE_STRONG, border_width=3)

        # Right: Opponent
        opp_portrait = self.enemy_portraits.get(self.enemy_name, self.enemy_portraits["Vegetable Peeler"])
        opp_p = cached_smoothscale(opp_portrait, (HUD_PORTRAIT_D, HUD_PORTRAIT_D))
        p_rect_right = opp_p.get_rect(center=HUD_PORTRAIT_RIGHT)
        draw_shadow(surf, p_rect_right, radius=HUD_PORTRAIT_D // 2, offset=(0, 4), alpha=80, blur=6)
        surf.blit(opp_p, p_rect_right)
        draw_smooth_circle(surf, (0, 0, 0, 0), HUD_PORTRAIT_RIGHT, HUD_PORTRAIT_D // 2, border=LINE_STRONG, border_width=3)

        # Center Fighting Game Medallion / Timer with anti-aliased smooth circles
        medallion_r = HUD_TIMER_RADIUS
        med_center = HUD_TIMER_CENTER
        med_rect = pygame.Rect(0, 0, medallion_r * 2, medallion_r * 2)
        med_rect.center = med_center
        draw_shadow(surf, med_rect, radius=medallion_r, offset=(0, 4), alpha=90, blur=8)
        draw_smooth_circle(surf, (48, 30, 20), med_center, medallion_r, border=GOLD, border_width=3)

        if self._timer_running():
            secs = max(0, int(math.ceil(self.timer)))
            secs_str = f"{secs:02d}"
            draw_text(surf, self.fonts["large_bold"], secs_str, GOLD, center=med_center)
        else:
            draw_text(surf, self.fonts["large_bold"], "∞", GOLD, center=(med_center[0], med_center[1] - 2))

        # Title Pill under timer medallion
        if self.infinite:
            title = "Infinite Mode"
        else:
            title = f"Level {self.level}" + (" · Warm-up" if self.phase == "WARMUP" else "")
        draw_chip(surf, self.fonts["small"], title, fill=(42, 28, 18), color=TEXT_ON_DARK, midtop=(center_x, med_rect.bottom + 6))

    def _draw_gameplay(self, surf: pygame.Surface) -> None:
        scene_y = round(self.foreground_camera_y)
        chef_y = round(self.chef_camera_y * CHEF_PAN_RATIO)
        chef = self.chef_frames[self.chef.current_frame]
        chef_anchor = (CHEF_ANCHOR[0], CHEF_ANCHOR[1] + chef_y)
        surf.blit(chef, chef.get_rect(midbottom=chef_anchor))
        table_margin = round(GAMEPLAY_PAN_PIXELS * FOREGROUND_PAN_RATIO)
        table_source_y = table_margin - scene_y
        surf.blit(self.tables_pan, (0, 0), pygame.Rect(0, table_source_y, VIRTUAL_W, VIRTUAL_H))

        self.tomato.draw(
            surf,
            self.health,
            (TOMATO_ANCHOR[0], TOMATO_ANCHOR[1] + scene_y),
            width=CHARACTER_SIZE,
            mistake=self.tomato_flash > 0,
            shake_time=FLASH_DURATION - self.tomato_flash,
            shake_duration=FLASH_DURATION,
        )

        enemy_width = ENEMY_DRAW_WIDTHS.get(self.enemy_name, CHARACTER_SIZE)
        enemy_anchor = (
            min(ENEMY_ANCHOR[0], VIRTUAL_W - 10 - enemy_width // 2),
            ENEMY_ANCHOR[1] + scene_y,
        )
        self.enemies.get(self.enemy_name, self.peeler).draw(
            surf, self._enemy_frame_index(), enemy_anchor,
            enemy_width,
            flip_x=True,
            damaged=self.enemy_flash > 0,
            shake_time=FLASH_DURATION - self.enemy_flash,
            shake_duration=FLASH_DURATION,
        )

        if self.state == "FEEDBACK":
            if self.review_fallacy_id is not None:
                # Dim the gameplay and show the review card beneath the Judge's dialogue.
                overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
                overlay_alpha = min(160, int(160 * (self.review_age / FEEDBACK_ENTER_SECONDS))) if self.review_age < FEEDBACK_ENTER_SECONDS else 160
                overlay.fill((*OVERLAY_DARK, overlay_alpha))
                surf.blit(overlay, (0, 0))
                self._draw_review_flashcard(surf)

        claim_box = DIALOGUE_RECT

        # Floating answer papers: bounded above the claim box so they never collide or overlap!
        if self.state == "GAMEPLAY" and self.dialogue_phase in ("DONE", "ACTIVE"):
            if not self.paused:
                for paper in self.papers:
                    paper.draw(surf, self.fonts["paper"])

        # Dialogue Card with speaker tab
        draw_card(surf, claim_box, radius=RADIUS_PANEL)
        tab_rect = pygame.Rect(claim_box.left + 24, claim_box.top - 14, 180, 28)
        speaker_txt = self.dialogue_speaker or self.enemy_name or "Judge"
        tab_color = (68, 120, 190) if speaker_txt == "Judge" else PRIMARY
        draw_rounded_rect(surf, tab_rect, tab_color, radius=8)
        draw_text(surf, self.fonts["small"], speaker_txt, TEXT_ON_DARK, center=tab_rect.center)

        # Typewriter text display with stable layout (no glitching/jumping)
        displayed_text = self.dialogue_text or self.current_claim
        text_left = claim_box.left + 28
        text_top = claim_box.top + 20
        text_width = claim_box.width - 56
        text_height = claim_box.height - 36
        dialogue_font = self.dialogue_fonts[-1]
        full_lines = wrap_text(displayed_text, dialogue_font, text_width)
        for candidate in self.dialogue_fonts:
            candidate_lines = wrap_text(displayed_text, candidate, text_width)
            if len(candidate_lines) * candidate.get_linesize() <= text_height:
                dialogue_font = candidate
                full_lines = candidate_lines
                break

        if self.dialogue_phase != "ACTIVE":
            chars_to_show = max(0, min(len(displayed_text), int(self.dialogue_char_count)))
            claim_lines = wrap_text_progressive(displayed_text, chars_to_show, dialogue_font, text_width)
        else:
            claim_lines = full_lines

        line_height = dialogue_font.get_linesize()
        text_y = text_top + max(0, (text_height - len(full_lines) * line_height) // 2)
        for i, line in enumerate(claim_lines):
            draw_text(surf, dialogue_font, line, INK, topleft=(text_left, text_y + i * line_height))

        # Sideways triangle (▶) continue indicator when typewriter finishes
        if self.state in ("GAMEPLAY", "FEEDBACK") and self.dialogue_phase in ("WAIT_CLICK", "OPPONENT_INTRO", "POST_VERDICT_WIN", "POST_VERDICT_LOSE"):
            if int(self.dialogue_char_count) >= len(displayed_text):
                # Gentle breathing/bobbing indicator in bottom right corner
                pulse = int(math.sin(pygame.time.get_ticks() / 150.0) * 4)
                tri_cx = claim_box.right - 36 + pulse
                tri_cy = claim_box.bottom - 28
                tri_pts = [
                    (tri_cx - 7, tri_cy - 9),
                    (tri_cx + 7, tri_cy),
                    (tri_cx - 7, tri_cy + 9)
                ]
                pygame.draw.polygon(surf, tab_color, tri_pts)

        # Render HUD on top of gameplay layer
        self._draw_hud(surf)
    def _draw_gameplay_frozen(self, surf: pygame.Surface) -> None:
        self.state, saved = "GAMEPLAY", self.state
        self.papers = []
        self._draw_gameplay(surf)
        self.state = saved

    def _draw_feedback_banner(self, surf: pygame.Surface) -> None:
        color = CORRECT_COLOR if self.result_correct else INCORRECT_COLOR
        image = self._banner_surface(self.result_label, color)
        if self.review_fallacy_id is not None:
            elapsed = self.review_age
            if elapsed < FEEDBACK_ENTER_SECONDS:
                t = elapsed / FEEDBACK_ENTER_SECONDS
                u = t - 1
                settle = 1 + 1.18 * u ** 3 + 0.18 * u ** 2
                x_offset = -image.get_width() + (image.get_width() - 24) * settle
            else:
                x_offset = -24
        else:
            total = game_rules.FEEDBACK_HOLD_SECONDS
            elapsed = max(0.0, total - self.feedback_timer)

            if elapsed < FEEDBACK_ENTER_SECONDS:
                t = elapsed / FEEDBACK_ENTER_SECONDS
                u = t - 1
                settle = 1 + 1.18 * u ** 3 + 0.18 * u ** 2
                x_offset = -image.get_width() + (image.get_width() - 24) * settle
            elif elapsed > total - FEEDBACK_EXIT_SECONDS:
                t = (elapsed - (total - FEEDBACK_EXIT_SECONDS)) / FEEDBACK_EXIT_SECONDS
                x_offset = -24 + (VIRTUAL_W + 24) * t ** 3
            else:
                x_offset = -24

        surf.blit(image, (round(x_offset), 150 - image.get_height() // 2))

    def _draw_announce_banner(self, surf: pygame.Surface) -> None:
        image = self._banner_surface(self.announce_text, ANNOUNCE_COLOR)
        elapsed = ANNOUNCE_SECONDS - self.announce_timer
        if elapsed < FEEDBACK_ENTER_SECONDS:
            u = elapsed / FEEDBACK_ENTER_SECONDS - 1
            settle = 1 + 1.18 * u ** 3 + 0.18 * u ** 2
            x_offset = -image.get_width() + (image.get_width() - 24) * settle
        elif elapsed > ANNOUNCE_SECONDS - FEEDBACK_EXIT_SECONDS:
            t = (elapsed - (ANNOUNCE_SECONDS - FEEDBACK_EXIT_SECONDS)) / FEEDBACK_EXIT_SECONDS
            x_offset = -24 + (VIRTUAL_W + 24) * t ** 3
        else:
            x_offset = -24
        surf.blit(image, (round(x_offset), 150 - image.get_height() // 2))

    def _banner_surface(
        self, text: str, background: tuple[int, int, int]
    ) -> pygame.Surface:
        """Return a cached red or green result ribbon with its message."""
        key = (text, background)
        if key not in self.banner_cache:
            width, height = VIRTUAL_W + 48, 120
            image = pygame.Surface((width, height + 14), pygame.SRCALPHA)
            pygame.draw.polygon(
                image,
                (39, 12, 9, 100),
                [(0, 12), (width, height // 2 + 12), (width, height + 12), (0, height + 12)],
            )

            if background == CORRECT_COLOR:
                edge, highlight, shade, accent = (30, 96, 59), (134, 190, 145), (23, 77, 48), (78, 153, 104)
            elif background == ANNOUNCE_COLOR:
                edge, highlight, shade, accent = (168, 98, 24), (248, 202, 122), (132, 74, 16), (238, 172, 76)
            else:
                edge, highlight, shade, accent = (164, 47, 42), (237, 141, 106), (121, 39, 31), (218, 101, 83)

            pygame.draw.polygon(
                image,
                edge,
                [(0, 0), (width, 0), (width - 20, height // 2), (width, height), (0, height), (20, height // 2)],
            )
            pygame.draw.rect(image, background, (20, 9, width - 40, height - 18))
            pygame.draw.line(image, highlight, (24, 12), (width - 24, 12), 2)
            pygame.draw.line(image, shade, (24, height - 10), (width - 24, height - 10), 3)
            for x in (75, 105, width - 125, width - 95):
                pygame.draw.polygon(
                    image,
                    accent,
                    [(x, 28), (x + 10, 28), (x - 14, height - 28), (x - 24, height - 28)],
                )

            label = self.banner_font.render(text, True, (255, 246, 229))
            max_w = width - 320
            if label.get_width() > max_w:
                label = pygame.transform.smoothscale(
                    label, (max_w, round(label.get_height() * max_w / label.get_width()))
                )
            image.blit(label, label.get_rect(center=(width // 2, height // 2)))
            self.banner_cache[key] = image
        return self.banner_cache[key]

    def _draw_gavel(self, surf: pygame.Surface) -> None:
        progress = 1 - max(0.0, self.gavel_timer) / GAVEL_DURATION
        frame_idx = min(len(self.chef_frames) - 1, int(progress * len(self.chef_frames)))
        chef = self.chef_frames[frame_idx]
        overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        overlay.fill((20, 12, 8, 140))
        surf.blit(overlay, (0, 0))
        big = pygame.transform.smoothscale(chef, (chef.get_width() * 2, chef.get_height() * 2))
        surf.blit(big, big.get_rect(center=(VIRTUAL_W // 2, VIRTUAL_H // 2)))

    def _draw_white_card(self, surf: pygame.Surface, card: pygame.Rect) -> None:
        shadow = pygame.Surface(card.size, pygame.SRCALPHA)
        draw_rounded_rect(shadow, shadow.get_rect(), (0, 0, 0, 80), 18)
        surf.blit(shadow, card.move(6, 8))
        draw_rounded_rect(surf, card, CARD_WHITE, 18)
        for x in (card.left + 18, card.right - 18):
            for y in (card.top + 18, card.bottom - 18):
                pygame.draw.circle(surf, SPARKLE_COLOR, (x, y), 4)

    def _draw_result_card(self, surf: pygame.Surface, title: str, color: tuple) -> None:
        dim = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        dim.fill((*OVERLAY_DARK, 180))
        surf.blit(dim, (0, 0))

        card = pygame.Rect(380, 110, 520, 420)
        draw_card(surf, card, radius=RADIUS_PANEL)
        draw_text(surf, self.fonts["title_bold"], title, color, center=(card.centerx, card.top + 50))

        if title == "LEVEL FAILED":
            tomato_img = self.smashed_tomato
        else:
            tomato_img = self.tomato_frames[0]
        tomato_rect = self._fitted_card(tomato_img, (160, 160), (card.centerx, card.top + 175))
        tomato_img = cached_smoothscale(tomato_img, tomato_rect.size)
        surf.blit(tomato_img, tomato_rect)

        if title == "LEVEL COMPLETE":
            sub = f"Judge: \"{JUDGE_WIN_STATEMENT}\""
            wrapped = wrap_text(sub, self.fonts["small"], card.width - 40)
            for j, line in enumerate(wrapped):
                draw_text(surf, self.fonts["small"], line, INK, center=(card.centerx, card.top + 270 + j * 20))
        else:
            sub = self.fail_reason or "Health depleted — review and try again!"
            draw_text(surf, self.fonts["small"], sub, INK_SOFT, center=(card.centerx, card.top + 280))

    def _draw_infinite_results(self, surf: pygame.Surface) -> None:
        dim = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        dim.fill((*OVERLAY_DARK, 180))
        surf.blit(dim, (0, 0))

        card = pygame.Rect(380, 110, 520, 420)
        draw_card(surf, card, radius=RADIUS_PANEL)
        draw_text(surf, self.fonts["title_bold"], "Infinite Mode", PRIMARY, center=(card.centerx, card.top + 50))
        
        draw_text(surf, self.fonts["small"], "Correct Answers", INK_SOFT, center=(card.centerx, card.top + 105))
        draw_text(surf, self.banner_font, str(self.infinite_final_correct), INK, center=(card.centerx, card.top + 165))
        
        best = self.progress.infinite_best_correct.get(INFINITE_SAVE_KEY, 0)
        best_str = f"Personal Best: {best} correct"
        draw_text(surf, self.fonts["body_bold"], best_str, INK_SOFT, center=(card.centerx, card.top + 230))
        if self.infinite_is_best:
            draw_chip(surf, self.fonts["small"], "NEW BEST RECORD", fill=GOLD, color=(48, 30, 12), center=(card.centerx, card.top + 272))

    def _draw_toasts(self, surf: pygame.Surface) -> None:
        y = 110
        for text, remaining in self.toasts:
            alpha = 255 if remaining > 0.6 else int(255 * (remaining / 0.6))
            lines = wrap_text(text, self.fonts["paper"], 480)
            box_h = 24 + len(lines) * 22
            box = pygame.Rect(0, 0, 520, box_h)
            box.midtop = (VIRTUAL_W // 2, y)
            panel = pygame.Surface(box.size, pygame.SRCALPHA)
            draw_rounded_rect(panel, panel.get_rect(), (*SURFACE, alpha), 12, (*LINE_STRONG, alpha), 2)
            surf.blit(panel, box)
            for i, line in enumerate(lines):
                label = self.fonts["paper"].render(line, True, PRIMARY)
                label.set_alpha(alpha)
                surf.blit(label, label.get_rect(center=(box.centerx, box.top + 16 + i * 22)))
            y += box_h + 8

    def _book_geometry(self) -> tuple[tuple[int, int], pygame.Rect, pygame.Rect]:
        bw, bh = self.book_image.get_size()
        origin = ((VIRTUAL_W - bw) // 2, (VIRTUAL_H - bh) // 2 - 16)
        scale_x = bw / BOOK_CROP.width
        scale_y = bh / BOOK_CROP.height

        def map_rect(src: pygame.Rect) -> pygame.Rect:
            return pygame.Rect(
                origin[0] + round((src.left - BOOK_CROP.left) * scale_x),
                origin[1] + round((src.top - BOOK_CROP.top) * scale_y),
                max(1, round(src.width * scale_x)),
                max(1, round(src.height * scale_y)),
            )

        return origin, map_rect(LEFT_PAGE_SRC), map_rect(RIGHT_PAGE_SRC)

    def _half_rects(self, origin: tuple[int, int]) -> tuple[pygame.Rect, pygame.Rect]:
        width, height = self.book_image.get_size()
        mid = width // 2
        gutter = self.page_gutter
        left = pygame.Rect(origin[0], origin[1], mid - gutter, height)
        right = pygame.Rect(origin[0] + mid + gutter, origin[1], width - mid - gutter, height)
        return left, right

    def _spread_ids(self, spread: int) -> tuple[int | None, ...]:
        entries = self._dictionary_entries()
        starts = self._spread_starts()
        if not starts:
            return (None, None, None, None)
        start = starts[spread % len(starts)]
        window = entries[start:start + CARDS_PER_SPREAD]
        placed: list[int | None] = [None, None, None, None]
        for offset, slot in enumerate((0, 2, 1, 3)):
            if offset < len(window):
                placed[slot] = window[offset]
        return tuple(placed)

    def _page_slots(self, page: pygame.Rect) -> tuple[pygame.Rect, pygame.Rect]:
        gap = max(6, page.height // 28)
        slot_h = (page.height - gap) // 2
        top = pygame.Rect(page.left, page.top, page.width, slot_h)
        bottom = pygame.Rect(page.left, top.bottom + gap, page.width, page.bottom - (top.bottom + gap))
        return top, bottom

    def _fitted_rect(self, image: pygame.Surface, slot: pygame.Rect) -> pygame.Rect:
        scale = min(slot.width / image.get_width(), slot.height / image.get_height())
        size = (max(1, int(image.get_width() * scale)), max(1, int(image.get_height() * scale)))
        rect = pygame.Rect(0, 0, size[0], size[1])
        rect.center = slot.center
        return rect

    def _blit_fitted(self, surf: pygame.Surface, image: pygame.Surface, slot: pygame.Rect) -> None:
        rect = self._fitted_rect(image, slot)
        surf.blit(cached_smoothscale(image, rect.size), rect)

    def _compose_page(self, card_ids: tuple[int | None, int | None], size: tuple[int, int]) -> pygame.Surface:
        key = ("page", card_ids, size)
        cached = self._card_cache.get(key)
        if cached is not None:
            return cached
        page = pygame.Surface(size, pygame.SRCALPHA)
        local = pygame.Rect(0, 0, size[0], size[1])
        for fid, slot in zip(card_ids, self._page_slots(local)):
            if fid is not None:
                self._blit_fitted(page, self.dictionary_cards[fid], slot)
        self._card_cache[key] = page
        return page

    def _turning_sheet(
        self,
        side: int,
        card_ids: tuple[int | None, int | None],
        half_rect: pygame.Rect,
        card_page: pygame.Rect,
    ) -> pygame.Surface:
        key = ("sheet", side, card_ids, half_rect.size)
        cached = self._card_cache.get(key)
        if cached is not None:
            return cached
        sheet = self.page_halves[side].copy()
        local_page = card_page.move(-half_rect.left, -half_rect.top)
        for fid, slot in zip(card_ids, self._page_slots(local_page)):
            if fid is not None:
                self._blit_fitted(sheet, self.dictionary_cards[fid], slot)
        self._card_cache[key] = sheet
        return sheet

    def _hinge_blit(
        self,
        surf: pygame.Surface,
        image: pygame.Surface,
        rect: pygame.Rect,
        scale: float,
        hinge: str,
    ) -> None:
        scale = max(0.0, min(1.0, scale))
        if scale <= 0.02:
            return
        new_w = max(1, int(rect.width * scale))
        scaled = pygame.transform.smoothscale(image, (new_w, rect.height))
        x = rect.left if hinge == "left" else rect.right - new_w
        surf.blit(scaled, (x, rect.top))
        shade = pygame.Surface((new_w, rect.height), pygame.SRCALPHA)
        shade.fill((48, 28, 12, int(110 * (1 - scale))))
        surf.blit(shade, (x, rect.top))

    def _draw_spread(self, surf: pygame.Surface, spread: int, left_rect: pygame.Rect, right_rect: pygame.Rect) -> None:
        ids = self._spread_ids(spread)
        surf.blit(self._compose_page(ids[0:2], left_rect.size), left_rect)
        surf.blit(self._compose_page(ids[2:4], right_rect.size), right_rect)

    def _draw_stitch(self, surf: pygame.Surface, origin: tuple[int, int]) -> None:
        mid = self.book_image.get_width() // 2
        surf.blit(self.book_stitch, (origin[0] + mid - self.page_gutter, origin[1]))

    def _draw_page_turn(self, surf: pygame.Surface, left_rect: pygame.Rect, right_rect: pygame.Rect) -> None:
        origin, _, _ = self._book_geometry()
        left_half, right_half = self._half_rects(origin)
        anim = self.page_anim
        t = max(0.0, min(1.0, anim["t"]))
        src_ids = self._spread_ids(anim["from"])
        dst_ids = self._spread_ids(anim["target"])
        src_left = self._turning_sheet(0, src_ids[0:2], left_half, left_rect)
        src_right = self._turning_sheet(1, src_ids[2:4], right_half, right_rect)
        dst_left = self._turning_sheet(0, dst_ids[0:2], left_half, left_rect)
        dst_right = self._turning_sheet(1, dst_ids[2:4], right_half, right_rect)
        if anim["direction"] > 0:
            surf.blit(self.page_halves[0], left_half)
            surf.blit(dst_right, right_half)
            self._draw_stitch(surf, origin)
            surf.blit(self._compose_page(src_ids[0:2], left_rect.size), left_rect)
            if t < 0.5:
                self._hinge_blit(surf, src_right, right_half, 1 - smoothstep(t / 0.5), "left")
            else:
                self._hinge_blit(surf, dst_left, left_half, smoothstep((t - 0.5) / 0.5), "right")
        else:
            surf.blit(dst_left, left_half)
            surf.blit(self.page_halves[1], right_half)
            self._draw_stitch(surf, origin)
            surf.blit(self._compose_page(src_ids[2:4], right_rect.size), right_rect)
            if t < 0.5:
                self._hinge_blit(surf, src_left, left_half, 1 - smoothstep(t / 0.5), "right")
            else:
                self._hinge_blit(surf, dst_right, right_half, smoothstep((t - 0.5) / 0.5), "left")

    def _draw_dictionary(self, surf: pygame.Surface) -> None:
        origin, left_rect, right_rect = self._book_geometry()
        turning = self.page_anim is not None
        if not turning:
            surf.blit(self.book_image, origin)

        entries = self._dictionary_entries()
        if not entries:
            empty = self.fonts["body"].render("No fallacies collected yet.", True, TEXT_DARK)
            surf.blit(empty, empty.get_rect(center=self.book_image.get_rect(topleft=origin).center))
            return

        spreads = self._spread_count()
        self.dictionary_page %= spreads
        if not turning:
            self._draw_spread(surf, self.dictionary_page, left_rect, right_rect)
            if self.zoomed_card is None:
                self._draw_hovered_card(surf, left_rect, right_rect)
            shown = self.dictionary_page
        else:
            self._draw_page_turn(surf, left_rect, right_rect)
            shown = self.page_anim["from"]

        shown_ids = [fid for fid in self._spread_ids(shown) if fid is not None]
        positions = [entries.index(fid) + 1 for fid in shown_ids]
        book_rect = self.book_image.get_rect(topleft=origin)
        # Place page count cleanly in a floating chip at the bottom
        page_badge = f"Cards {min(positions)}–{max(positions)} of {len(entries)}"
        draw_chip(surf, self.fonts["small"], page_badge, fill=SURFACE, color=INK, center=(book_rect.centerx, VIRTUAL_H - 30))
        if self.zoomed_card is not None:
            self._draw_zoomed_card(surf)

    def _draw_hovered_card(self, surf: pygame.Surface, left_rect: pygame.Rect, right_rect: pygame.Rect) -> None:
        """Redraw the card under the cursor slightly larger, on top of the page."""
        ids = self._spread_ids(self.dictionary_page)
        slots = self._page_slots(left_rect) + self._page_slots(right_rect)
        for fid, slot in zip(ids, slots):
            if fid is None:
                continue
            rect = self._fitted_rect(self.dictionary_cards[fid], slot)
            if self._is_hovered(rect):
                grown = pygame.Rect(0, 0, round(rect.width * HOVER_SCALE), round(rect.height * HOVER_SCALE))
                grown.center = rect.center
                surf.blit(cached_smoothscale(self.dictionary_cards[fid], grown.size), grown)
                return

    def _draw_zoomed_card(self, surf: pygame.Surface) -> None:
        image = self.detail_cards.get(self.zoomed_card)
        if image is None:
            return
        dim = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        dim.fill((16, 10, 8, 150))
        surf.blit(dim, (0, 0))
        fit = min(980 / image.get_width(), 620 / image.get_height())
        scale = 0.72 + 0.28 * smoothstep(self.zoom_t)
        width = max(1, int(image.get_width() * fit * scale))
        height = max(1, int(image.get_height() * fit * scale))
        scaled = pygame.transform.smoothscale(image, (width, height))
        surf.blit(scaled, scaled.get_rect(center=(VIRTUAL_W // 2, VIRTUAL_H // 2)))

    def _draw_review_flashcard(self, surf: pygame.Surface) -> None:
        image = self.detail_cards.get(self.review_fallacy_id)
        if image is None:
            return

        if self.review_age < FEEDBACK_ENTER_SECONDS:
            scale = 0.6 + 0.24 * (self.review_age / FEEDBACK_ENTER_SECONDS)
        else:
            scale = 0.88

        #location
        dest = self._fitted_card(image, (820, 350), (VIRTUAL_W // 2, 200))
        dest = pygame.Rect(0, 0, max(1, int(dest.width * scale)), max(1, int(dest.height * scale)))
        dest.center = (VIRTUAL_W // 2, 370)
        scaled = pygame.transform.smoothscale(image, dest.size)
        shadow = pygame.Surface(scaled.get_size(), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (20, 10, 6, 80), shadow.get_rect(), border_radius=18)
        surf.blit(shadow, dest.move(0, 8))
        surf.blit(scaled, dest)

    def _draw_settings(self, surf: pygame.Surface) -> None:
        paper = SETTINGS_PAPER_RECT
        draw_card(surf, paper, radius=RADIUS_PANEL)

        tomato = cached_smoothscale(self.tomato_frames[0], (96, 96))
        surf.blit(tomato, tomato.get_rect(center=(paper.centerx, paper.top + 76)))
        draw_text(surf, self.fonts["title_bold"], "Settings", INK, center=(paper.centerx, paper.top + 150))
        pygame.draw.line(surf, LINE, (paper.left + 36, paper.top + 176), (paper.right - 36, paper.top + 176), 1)

        self._draw_volume_sliders(surf, SETTINGS_ROW_RECTS, SETTINGS_SLIDER_RECTS)

        self._draw_dev_controls(surf)

        if self.show_reset_confirm:
            warn_rect = pygame.Rect(paper.left + 32, SETTINGS_RESET_RECT.top - 46, paper.width - 64, 38)
            draw_rounded_rect(surf, warn_rect, (253, 237, 237), radius=8, border=DANGER, border_width=1)
            draw_icon(surf, "alert", (warn_rect.left + 20, warn_rect.centery), 18, DANGER)
            draw_text(surf, self.fonts["paper"], "Reset all progress & cards?", DANGER, midleft=(warn_rect.left + 36, warn_rect.centery))

    def _draw_volume_sliders(self, surf: pygame.Surface, row_rects, slider_rects) -> None:
        rows = (("Music Volume", self.audio.music_volume), ("Sound Effects", self.audio.sfx_volume))
        for rect, track, (text, volume) in zip(row_rects, slider_rects, rows):
            draw_text(surf, self.fonts["body_bold"], text, INK, topleft=(rect.left, rect.top - 6))
            pct_txt = f"{round(volume * 100)}%"
            draw_text(surf, self.fonts["body"], pct_txt, PRIMARY, topright=(rect.right, rect.top - 6))
            
            # Slider track background
            draw_rounded_rect(surf, track, SURFACE_ALT, radius=track.height // 2, border=LINE, border_width=1)
            # Filled portion
            fill_w = round(track.width * volume)
            if fill_w > 0:
                filled = pygame.Rect(track.left, track.top, fill_w, track.height)
                draw_rounded_rect(surf, filled, PRIMARY, radius=track.height // 2)
            # Knob
            knob_x = track.left + fill_w
            knob = (knob_x, track.centery)
            pygame.draw.circle(surf, (0, 0, 0, 40), (knob[0], knob[1] + 2), 11)
            pygame.draw.circle(surf, (255, 255, 255), knob, 10)
            pygame.draw.circle(surf, PRIMARY, knob, 10, 2)
            pygame.draw.circle(surf, PRIMARY, knob, 4)

    def _draw_dev_controls(self, surf: pygame.Surface) -> None:
        box = DEV_INPUT_RECT
        draw_text(surf, self.fonts["small"], "Developer Access", (110, 95, 80), bottomleft=(box.left, box.top - 4))
        border_col = PRIMARY if self.dev_input_active else LINE
        bg_col = (255, 255, 255) if self.dev_input_active else SURFACE_ALT
        draw_rounded_rect(surf, box, bg_col, radius=8, border=border_col, border_width=2 if self.dev_input_active else 1)
        
        masked = "•" * len(self.dev_input)
        if self.dev_input_active and (pygame.time.get_ticks() // 500) % 2 == 0:
            masked += "|"
        if not self.dev_input and not self.dev_input_active:
            draw_text(surf, self.fonts["small"], "Enter dev code...", (160, 150, 140), midleft=(box.left + 12, box.centery))
        else:
            draw_text(surf, self.fonts["body_bold"], masked, INK, midleft=(box.left + 12, box.centery))
            
        if self.dev_error:
            draw_text(surf, self.fonts["paper"], "Invalid code", DANGER, topright=(box.right, box.bottom + 3))
        if not self.dev_unlocked:
            return
        switch = DEV_SWITCH_RECT
        draw_text(surf, self.fonts["body_bold"], "Unlock All Content", SECONDARY_DARK if self.dev_mode else INK, midleft=(box.left, switch.centery))
        track_col = SECONDARY if self.dev_mode else (200, 195, 185)
        pygame.draw.rect(surf, track_col, switch, border_radius=switch.height // 2)
        r = switch.height // 2 - 3
        knob_x = switch.right - r - 3 if self.dev_mode else switch.left + r + 3
        pygame.draw.circle(surf, (0, 0, 0, 40), (knob_x, switch.centery + 1), r)
        pygame.draw.circle(surf, (255, 255, 255), (knob_x, switch.centery), r)


async def main() -> None:
    # A larger mixer buffer keeps browser audio from underrunning (crackling)
    # when a frame runs long.
    pygame.mixer.pre_init(44100, -16, 2, 4096 if sys.platform == "emscripten" else 1024)
    pygame.init()
    if sys.platform == "emscripten":
        # Pygbag's page already called pygame.init() before this file ran, so
        # pre_init had no effect and the mixer kept its tiny default buffer.
        # Restart it so the larger buffer actually applies.
        pygame.mixer.quit()
        pygame.mixer.init(44100, -16, 2, 4096)
    pygame.display.set_caption("Food Court")
    # Let SDL scale the virtual canvas and synchronize presentation to the
    # display when the active renderer supports it.
    if sys.platform == "emscripten":
        # pygbag CSS-scales the canvas; SCALED/RESIZABLE/vsync fail to create
        # a renderer there (newer platform_wasm strips them for this reason).
        screen = pygame.display.set_mode((VIRTUAL_W, VIRTUAL_H))
    else:
        display_flags = pygame.RESIZABLE | pygame.SCALED
        screen = pygame.display.set_mode((VIRTUAL_W, VIRTUAL_H), display_flags, vsync=1)
    clock = pygame.time.Clock()
    canvas = pygame.Surface((VIRTUAL_W, VIRTUAL_H))

    game = Game()
    game.prewarm()
    game.start_intro()
    game.layout_buttons()

    running = True
    mouse_press_seen = False
    while running:
        dt = clock.tick(60 if sys.platform == "emscripten" else 120) / 1000.0
        window_size = pygame.display.get_window_size()
        portrait = window_size[1] > window_size[0]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not portrait:
                # Activate on press, then suppress the release half of the same
                # click. Keep the release fallback for focus clicks on platforms
                # that swallow mouse-down while the window gains focus.
                mouse_press_seen = True
                if game.handle_press(event.pos):
                    game.layout_buttons()
            elif event.type == pygame.MOUSEMOTION:
                game.mouse_pos = event.pos
                game.handle_drag(game.mouse_pos)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if game.dev_input_active:
                    game.handle_key(event)
                else:
                    running = False
            elif event.type in (pygame.KEYDOWN, pygame.TEXTINPUT):
                game.handle_key(event)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if not mouse_press_seen and game.dragging_slider is None and not portrait:
                    game.handle_click(event.pos)
                    game.layout_buttons()
                game.handle_release()
                mouse_press_seen = False

        if not portrait:
            game.update(dt)
            game.layout_buttons()

        canvas.fill(BG)
        if portrait:
            font = pygame.font.Font(None, 36)
            msg = font.render("Please rotate your device to landscape", True, (240, 230, 210))
            canvas.blit(msg, msg.get_rect(center=(VIRTUAL_W // 2, VIRTUAL_H // 2)))
        else:
            game.draw(canvas)

        screen.fill((0, 0, 0))
        screen.blit(canvas, (0, 0))

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
