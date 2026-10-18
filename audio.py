"""Audio playback used by main.py.

Music streams through pygame.mixer.music; sound effects are preloaded
Sound objects. Every call is safe when the mixer is unavailable (headless
tests, blocked browser audio), and unknown sound names are ignored so
main.py can call effects that have no file yet.
"""

from __future__ import annotations

import random
from pathlib import Path

import pygame

ASSET_DIR = Path(__file__).resolve().parent / "assets"
MUSIC_DIR = ASSET_DIR / "music"
SFX_DIR = ASSET_DIR / "sound effects"

MUSIC_FILES = {
    "main": "main theme.mp3",
    "infinite": "infinite theme.mp3",
    "veggie_skinner": "veggie skinner theme.mp3",
    "knife": "knife theme.mp3",
    "boiling_pot": "boiling pot theme.mp3",
}

SFX_FILES = {
    "chomp": "carrot chomp.mp3",
    "knife_hit": "Chef knife hit.mp3",
    "click": "click.mp3",
    "text": "text.mp3",
    "knife_correct_1": "knife1.mp3",
    "knife_correct_2": "knife2.mp3",
    "knife_correct_3": "knife3.mp3",
}
SFX_GROUPS = {
    "correct": ("knife_correct_1", "knife_correct_2", "knife_correct_3"),
}

DEFAULT_VOLUME = 0.7
# The music files are mastered loud, so the slider's 100% plays at half volume.
MUSIC_GAIN = 0.5


def clamp_volume(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


class AudioManager:
    def __init__(self, music_volume: float = DEFAULT_VOLUME, sfx_volume: float = DEFAULT_VOLUME) -> None:
        self.music_volume = clamp_volume(music_volume)
        self.sfx_volume = clamp_volume(sfx_volume)
        self.current_track: str | None = None
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.looping_sfx: dict[str, pygame.mixer.Channel] = {}
        self._last_group_choice: dict[str, str] = {}
        self.enabled = self._init_mixer()
        if self.enabled:
            for name, filename in SFX_FILES.items():
                try:
                    self.sounds[name] = pygame.mixer.Sound(str(SFX_DIR / filename))
                except (pygame.error, FileNotFoundError):
                    pass

    @staticmethod
    def _init_mixer() -> bool:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            return True
        except pygame.error:
            return False

    def play_sfx(self, name: str) -> None:
        choices = SFX_GROUPS.get(name)
        if choices:
            group = name
            previous = self._last_group_choice.get(group)
            available = tuple(choice for choice in choices if choice != previous) or choices
            name = random.choice(available)
            self._last_group_choice[group] = name
        sound = self.sounds.get(name)
        if sound is None or self.sfx_volume <= 0:
            return
        sound.set_volume(self.sfx_volume)
        sound.play()

    def play_sfx_loop(self, name: str) -> None:
        sound = self.sounds.get(name)
        if sound is None or self.sfx_volume <= 0:
            return
        channel = self.looping_sfx.get(name)
        if channel is not None and channel.get_busy():
            return
        sound.set_volume(self.sfx_volume)
        channel = sound.play(loops=-1)
        if channel is not None:
            self.looping_sfx[name] = channel

    def stop_sfx(self, name: str) -> None:
        channel = self.looping_sfx.pop(name, None)
        if channel is not None:
            channel.stop()

    def play_music(self, track: str) -> None:
        """Loop a named track; calling again with the playing track is a no-op."""
        if track == self.current_track or not self.enabled:
            return
        filename = MUSIC_FILES.get(track)
        if filename is None:
            return
        try:
            pygame.mixer.music.load(str(MUSIC_DIR / filename))
            pygame.mixer.music.set_volume(self.music_volume * MUSIC_GAIN)
            pygame.mixer.music.play(loops=-1)
        except (pygame.error, FileNotFoundError):
            return
        self.current_track = track

    def stop_music(self) -> None:
        if self.enabled:
            pygame.mixer.music.stop()
        self.current_track = None

    def set_music_volume(self, volume: float) -> None:
        self.music_volume = clamp_volume(volume)
        if self.enabled:
            pygame.mixer.music.set_volume(self.music_volume * MUSIC_GAIN)

    def set_sfx_volume(self, volume: float) -> None:
        self.sfx_volume = clamp_volume(volume)
        for channel in self.looping_sfx.values():
            channel.set_volume(self.sfx_volume)
