"""Audio playback used by main.py.

Music plays as a Sound on a reserved channel rather than through
pygame.mixer.music: Pygbag's mixer.music ignores set_volume, so the music
slider had no effect in the browser. A channel also lets tracks fade out and
in frame by frame. Sound effects are preloaded Sound objects. Every call is safe when the mixer is unavailable (headless
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
    "main": "main theme.ogg",
    "infinite": "infinite theme.ogg",
    "veggie_skinner": "veggie skinner theme.ogg",
    "knife": "knife theme.ogg",
    "boiling_pot": "boiling pot theme.ogg",
}

SFX_FILES = {
    "chomp": "carrot chomp.ogg",
    "knife_hit": "Chef knife hit.ogg",
    "click": "click.ogg",
    "text": "text.ogg",
    "knife_correct_1": "knife1.ogg",
    "knife_correct_2": "knife2.ogg",
    "knife_correct_3": "knife3.ogg",
}
SFX_GROUPS = {
    "correct": ("knife_correct_1", "knife_correct_2", "knife_correct_3"),
}

DEFAULT_VOLUME = 0.7
# The music files are mastered loud, so the slider's 100% plays at half volume.
MUSIC_GAIN = 0.5
# Seconds for the old track to fade out, then again for the new one to fade in.
MUSIC_FADE_SECONDS = 1.0


def clamp_volume(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


class AudioManager:
    def __init__(self, music_volume: float = DEFAULT_VOLUME, sfx_volume: float = DEFAULT_VOLUME) -> None:
        self.music_volume = clamp_volume(music_volume)
        self.sfx_volume = clamp_volume(sfx_volume)
        self.current_track: str | None = None  # the track requested last
        self.playing_track: str | None = None  # the track actually on the channel
        self.music_level = 0.0  # fade multiplier, 0..1
        self.music_channel: pygame.mixer.Channel | None = None
        self.music_sounds: dict[str, pygame.mixer.Sound] = {}
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.looping_sfx: dict[str, pygame.mixer.Channel] = {}
        self._last_group_choice: dict[str, str] = {}
        self.enabled = self._init_mixer()
        if self.enabled:
            pygame.mixer.set_reserved(1)
            self.music_channel = pygame.mixer.Channel(0)
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
        """Switch to a looping track; the change fades out then in via update()."""
        if track == self.current_track or not self.enabled or track not in MUSIC_FILES:
            return
        self.current_track = track

    def stop_music(self) -> None:
        self.current_track = None

    def update(self, dt: float) -> None:
        """Advance music fades. Call once per frame."""
        if self.music_channel is None:
            return
        step = dt / MUSIC_FADE_SECONDS
        if self.playing_track != self.current_track and self.playing_track is not None:
            self.music_level = max(0.0, self.music_level - step)
            if self.music_level <= 0.0:
                self.music_channel.stop()
                self.playing_track = None
        if self.playing_track is None and self.current_track is not None:
            sound = self._music_sound(self.current_track)
            if sound is None:
                self.current_track = None
            else:
                self.music_level = 0.0
                self.music_channel.play(sound, loops=-1)
                self.playing_track = self.current_track
        elif self.playing_track is not None and self.playing_track == self.current_track:
            self.music_level = min(1.0, self.music_level + step)
        self._apply_music_volume()

    def _music_sound(self, track: str) -> pygame.mixer.Sound | None:
        sound = self.music_sounds.get(track)
        if sound is None:
            try:
                sound = pygame.mixer.Sound(str(MUSIC_DIR / MUSIC_FILES[track]))
            except (pygame.error, FileNotFoundError):
                return None
            self.music_sounds[track] = sound
        return sound

    def _apply_music_volume(self) -> None:
        if self.music_channel is not None:
            self.music_channel.set_volume(self.music_volume * MUSIC_GAIN * self.music_level)

    def set_music_volume(self, volume: float) -> None:
        self.music_volume = clamp_volume(volume)
        self._apply_music_volume()

    def set_sfx_volume(self, volume: float) -> None:
        self.sfx_volume = clamp_volume(volume)
        for channel in self.looping_sfx.values():
            channel.set_volume(self.sfx_volume)
