
import math
from pathlib import Path

import pygame
from entities.character import SpriteStrip


class Tomato:
    def __init__(self, path=None):
        path = path or Path(__file__).resolve().parents[1] / 'assets/Tomato_SpriteSheet.png'
        self.frames = SpriteStrip(path, frame_count=5, painted_width=5585).frames
        self.scaled_frames = {}

    def draw(
        self,
        screen,
        hp,
        anchor,
        width=220,
        mistake=False,
        shake_time=0,
        shake_duration=1,
    ):
        # Choose the expression inside Tomato.
        frame_index = (
            len(self.frames) - 1
            if mistake
            else min(len(self.frames) - 2, max(0, 6 - hp))
        )

        # Reuse scaled frames. draw() runs every frame, so scaling here without a
        # cache created a fresh image surface continuously even at the default size.
        key = (frame_index, width)
        frame = self.scaled_frames.get(key)
        if frame is None:
            source = self.frames[frame_index]
            height = round(source.get_height() * width / source.get_width())
            frame = pygame.transform.smoothscale(source, (width, height))
            self.scaled_frames[key] = frame

        # Shake the tomato during the mistake animation.
        x, y = anchor

        if mistake and shake_duration > 0:
            decay = max(0, 1 - shake_time / shake_duration)
            x += round(math.sin(shake_time * 48) * 7 * decay)
            y += round((math.cos(shake_time * 48) - 1) * 2 * decay)

        # Anchor represents the bottom-center of the tomato.
        position = (x - width // 2, y - frame.get_height())

        screen.blit(frame, position)
