
import pygame


class SpriteStrip:
    def __init__(self, path, frame_count=5, painted_width=5586):
        self.frames = []

        try:
            sheet = pygame.image.load(str(path)).convert_alpha()

            for index in range(frame_count):
                left = round(index * painted_width / frame_count)
                right = round((index + 1) * painted_width / frame_count)

                cell = sheet.subsurface(
                    (left, 0, right - left, sheet.get_height())
                ).copy()

                bounds = cell.get_bounding_rect()
                if bounds.width == 0 or bounds.height == 0:
                    raise ValueError(f"Sprite frame {index} is empty")

                self.frames.append(cell.subsurface(bounds).copy())

        except (pygame.error, OSError, ValueError) as error:
            raise RuntimeError(
                f"Failed to load or process sprite sheet '{path}': {error}"
            ) from error

        # Align frames to a shared canvas so characters don't jump
        # as their expressions change.
        width = max(frame.get_width() for frame in self.frames)
        height = max(frame.get_height() for frame in self.frames)

        aligned_frames = []
        for frame in self.frames:
            aligned = pygame.Surface((width, height), pygame.SRCALPHA)
            aligned.blit(
                frame,
                ((width - frame.get_width()) // 2, height - frame.get_height())
            )
            aligned_frames.append(aligned)

        self.frames = aligned_frames

    def draw(self, screen, index, position=(0, 0), scale=1.0):
        """Draw a selected frame at a top-left position."""
        frame = self.frames[index]

        if scale != 1.0:
            frame = pygame.transform.smoothscale(
                frame,
                (
                    round(frame.get_width() * scale),
                    round(frame.get_height() * scale)
                )
            )

        screen.blit(frame, position)
