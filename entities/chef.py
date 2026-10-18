
import pygame
from pathlib import Path

from entities.character import SpriteStrip


class Chef:
    def __init__(self, frame_duration=0.15, path=None):
        path = path or Path(__file__).resolve().parents[1] / 'assets/Chef_SpriteSheet.png'
        self.frames = SpriteStrip(path, frame_count=3, painted_width=3187).frames

        self.current_frame = 0
        self.elapsed = 0.0
        self.frame_duration = frame_duration
        self.animating = False

    def play(self):
        self.current_frame = 0
        self.elapsed = 0.0
        self.animating = True

    def reset(self):
        self.current_frame = 0
        self.elapsed = 0.0
        self.animating = False

    def update(self, dt):
        if not self.animating:
            return

        self.elapsed += max(0, dt)

        while self.elapsed >= self.frame_duration and self.animating:
            self.elapsed -= self.frame_duration
            self.current_frame += 1

            if self.current_frame >= len(self.frames):
                self.current_frame = 0
                self.animating = False

    def draw(self, screen, position=(108, 119), scale=1.0):
        # Select the current animation frame
        frame = self.frames[self.current_frame]

        # Resize the sprite if needed
        if scale != 1:
            frame = pygame.transform.smoothscale(
                frame,
                (
                    round(frame.get_width() * scale),
                    round(frame.get_height() * scale),
                ),
            )

        # Draw the chef on the screen
        screen.blit(frame, position)
