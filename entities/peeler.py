from pathlib import Path
import math

import pygame

from entities.character import SpriteStrip


class Peeler:
    """Peeler enemy sprites, cropped with the same strip loader as Tomato."""

    def __init__(self, path=None):
        path = path or Path(__file__).resolve().parents[1] / 'assets/Peeler_SpriteSheet.png'
        self.frames = SpriteStrip(path, frame_count=5, painted_width=5585).frames
        # The second source frame is the happy expression. Start there, then
        # move through the neutral and sad frames, leaving damage as the last.
        self.frames = [self.frames[1], self.frames[0], *self.frames[2:]]
        self.scaled_frames = {}

    def draw(
        self,
        screen,
        index,
        anchor,
        width=230,
        flip_x=False,
        damaged=False,
        shake_time=0,
        shake_duration=0.5,
    ):
        index = max(0, min(index, len(self.frames) - 1))
        key = (index, width, flip_x)
        frame = self.scaled_frames.get(key)
        if frame is None:
            source = self.frames[index]
            height = round(source.get_height() * width / source.get_width())
            frame = pygame.transform.smoothscale(source, (width, height))
            if flip_x:
                frame = pygame.transform.flip(frame, True, False)
            self.scaled_frames[key] = frame

        x, y = anchor
        if damaged and shake_duration > 0:
            decay = max(0, 1 - shake_time / shake_duration)
            x += round(math.sin(shake_time * 48) * 7 * decay)
            y += round((math.cos(shake_time * 48) - 1) * 2 * decay)
        screen.blit(frame, (x - width // 2, y - frame.get_height()))
