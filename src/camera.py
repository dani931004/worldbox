"""
This file contains the Camera class for handling pan and zoom.
"""
import pygame

MIN_ZOOM = 0.5
MAX_ZOOM = 3.0


class Camera:
    """Handles camera pan, zoom, and coordinate transformations."""

    def __init__(self, world_px_w: int, world_px_h: int, view_w: int, view_h: int):
        self.world_px_w = world_px_w
        self.world_px_h = world_px_h
        self.view_w = view_w
        self.view_h = view_h
        self.x = 0
        self.y = 0
        self.zoom = 1.0

    def set_view(self, view_w: int, view_h: int) -> None:
        """Update viewport size."""
        self.view_w = view_w
        self.view_h = view_h

    def clamp(self) -> None:
        """Keep camera inside world bounds."""
        src_w = int(self.view_w / self.zoom)
        src_h = int(self.view_h / self.zoom)
        self.x = max(0, min(self.x, self.world_px_w - src_w))
        self.y = max(0, min(self.y, self.world_px_h - src_h))

    def move(self, dx: int, dy: int) -> None:
        """Pan by pixels (pre-zoom movement)."""
        self.x += dx
        self.y += dy
        self.clamp()

    def zoom_by(self, dz: float) -> None:
        """Additively change zoom, clamped to [MIN_ZOOM, MAX_ZOOM]."""
        self.zoom = max(MIN_ZOOM, min(MAX_ZOOM, self.zoom + dz))
        self.clamp()

    def set_zoom(self, zoom: float) -> None:
        """Set zoom level, clamped to [MIN_ZOOM, MAX_ZOOM]."""
        self.zoom = max(MIN_ZOOM, min(MAX_ZOOM, zoom))
        self.clamp()

    def get_src_rect(self) -> pygame.Rect:
        """Returns source rect on world surface."""
        src_w = int(self.view_w / self.zoom)
        src_h = int(self.view_h / self.zoom)
        return pygame.Rect(self.x, self.y, src_w, src_h)

    def world_to_screen(self, wx_px: int, wy_px: int) -> tuple[int, int]:
        """Map world pixels to screen."""
        sx = int((wx_px - self.x) * self.zoom)
        sy = int((wy_px - self.y) * self.zoom)
        return sx, sy

    def screen_to_world(self, sx: int, sy: int) -> tuple[int, int]:
        """Map screen to world pixels."""
        wx = int(sx / self.zoom + self.x)
        wy = int(sy / self.zoom + self.y)
        return wx, wy