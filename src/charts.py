"""
MarketQuest - Retro Stock Chart Renderer
Renders custom, high-contrast retro stock price charts directly onto Pygame surfaces.
Includes grid lines, price scales, gradient area fills, trend coloring, and highlighted endpoints.
"""

import pygame
from typing import List, Tuple
from config import (
    COLOR_PANEL_BG, COLOR_PANEL_ALT, COLOR_BORDER, COLOR_BORDER_ACCENT,
    COLOR_TEXT_WHITE, COLOR_TEXT_MUTED, COLOR_TEXT_GOLD,
    COLOR_GAIN_BRIGHT, COLOR_LOSS_BRIGHT
)

class StockChartRenderer:
    def __init__(self, font: pygame.font.Font, small_font: pygame.font.Font):
        self.font = font
        self.small_font = small_font

    def draw_chart(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        price_history: List[float],
        current_price: float,
        ticker: str = ""
    ):
        """Draw a retro financial line chart inside the given bounding rect."""
        # 1. Background Panel with beveled border
        pygame.draw.rect(surface, (14, 20, 38), rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_BORDER, rect, width=1, border_radius=4)

        if not price_history:
            price_history = [current_price]

        # Chart inner padding
        pad_left = 52
        pad_right = 16
        pad_top = 22
        pad_bottom = 22

        plot_rect = pygame.Rect(
            rect.x + pad_left,
            rect.y + pad_top,
            rect.width - pad_left - pad_right,
            rect.height - pad_top - pad_bottom
        )

        if plot_rect.width <= 10 or plot_rect.height <= 10:
            return

        min_val = min(price_history)
        max_val = max(price_history)
        
        # Add safety margin around bounds
        if max_val == min_val:
            min_val = max(1.0, min_val * 0.95)
            max_val = max_val * 1.05
        else:
            spread = max_val - min_val
            min_val = max(1.0, min_val - spread * 0.08)
            max_val = max_val + spread * 0.08

        # 2. Draw Horizontal Grid Lines and Price Labels
        grid_steps = 4
        for i in range(grid_steps + 1):
            ratio = i / grid_steps
            y_pos = int(plot_rect.bottom - ratio * plot_rect.height)
            price_at_y = min_val + ratio * (max_val - min_val)

            # Dashed line
            dash_len = 4
            space_len = 4
            x = plot_rect.left
            while x < plot_rect.right:
                pygame.draw.line(surface, (26, 38, 66), (x, y_pos), (min(x + dash_len, plot_rect.right), y_pos), 1)
                x += dash_len + space_len

            # Label on left
            lbl = f"${price_at_y:.1f}"
            lbl_surf = self.small_font.render(lbl, True, COLOR_TEXT_MUTED)
            lbl_rect = lbl_surf.get_rect(right=plot_rect.left - 6, centery=y_pos)
            surface.blit(lbl_surf, lbl_rect)

        # 3. Determine Trend Color (Green if latest >= first, Red if down)
        first_p = price_history[0]
        last_p = price_history[-1]
        is_up = last_p >= first_p
        line_color = COLOR_GAIN_BRIGHT if is_up else COLOR_LOSS_BRIGHT
        fill_color = (18, 48, 38) if is_up else (52, 22, 28)

        # 4. Map Price Points to Screen Coordinates
        num_points = len(price_history)
        coords: List[Tuple[int, int]] = []
        step_x = plot_rect.width / max(1, num_points - 1)

        for idx, price in enumerate(price_history):
            cx = int(plot_rect.left + idx * step_x)
            val_norm = (price - min_val) / (max_val - min_val) if max_val != min_val else 0.5
            cy = int(plot_rect.bottom - val_norm * plot_rect.height)
            coords.append((cx, cy))

        # 5. Draw Filled Area Under Line
        if len(coords) >= 2:
            poly_points = [(plot_rect.left, plot_rect.bottom)] + coords + [(plot_rect.right, plot_rect.bottom)]
            fill_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            local_poly = [(px - rect.x, py - rect.y) for px, py in poly_points]
            pygame.draw.polygon(fill_surf, (*fill_color, 110), local_poly)
            surface.blit(fill_surf, rect.topleft)

        # 6. Draw Connected Line Graph
        if len(coords) >= 2:
            pygame.draw.lines(surface, line_color, False, coords, width=2)
        elif len(coords) == 1:
            pygame.draw.circle(surface, line_color, coords[0], 3)

        # 7. Highlight Latest Point with Glowing Reticle
        if coords:
            latest_x, latest_y = coords[-1]
            pygame.draw.circle(surface, (255, 255, 255), (latest_x, latest_y), 4)
            pygame.draw.circle(surface, line_color, (latest_x, latest_y), 2)

            # Floating current price tag
            tag_text = f"${last_p:,.2f}"
            tag_surf = self.small_font.render(tag_text, True, COLOR_TEXT_WHITE)
            tag_bg = pygame.Rect(0, 0, tag_surf.get_width() + 8, tag_surf.get_height() + 4)
            tag_bg.center = (min(rect.right - 26, latest_x), max(plot_rect.top + 8, latest_y - 12))
            pygame.draw.rect(surface, (12, 16, 28), tag_bg, border_radius=3)
            pygame.draw.rect(surface, line_color, tag_bg, width=1, border_radius=3)
            surface.blit(tag_surf, (tag_bg.x + 4, tag_bg.y + 2))

        # 8. Time Axis Labels at the Bottom
        t_start = self.small_font.render(f"-{num_points}d", True, COLOR_TEXT_MUTED)
        t_mid = self.small_font.render(f"-{num_points//2}d", True, COLOR_TEXT_MUTED)
        t_end = self.small_font.render("Today", True, COLOR_TEXT_GOLD)

        surface.blit(t_start, (plot_rect.left, plot_rect.bottom + 4))
        surface.blit(t_mid, (plot_rect.centerx - t_mid.get_width() // 2, plot_rect.bottom + 4))
        surface.blit(t_end, (plot_rect.right - t_end.get_width(), plot_rect.bottom + 4))
