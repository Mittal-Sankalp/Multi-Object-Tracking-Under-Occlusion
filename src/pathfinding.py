"""
MarketQuest - A* Grid Pathfinding & Route Guidance System
Provides tile-grid A* search across exterior districts and interior maps.
Calculates optimal collision-free routes and generates glowing navigation trails.
"""

import heapq
import math
from typing import List, Tuple, Optional, Set
import pygame
from config import TILE_SIZE, COLOR_BORDER_ACCENT, COLOR_TEXT_GOLD


class GridPathfinder:
    def __init__(self, tile_cols: int, tile_rows: int, solids: List[pygame.Rect]):
        self.cols = tile_cols
        self.rows = tile_rows
        self.solids = solids
        self._build_walkable_grid()

    def _build_walkable_grid(self):
        """Construct a 2D boolean grid where True = walkable, False = blocked by solid collider."""
        self.walkable = [[True for _ in range(self.cols)] for _ in range(self.rows)]
        for r in range(self.rows):
            for c in range(self.cols):
                tile_rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                for solid in self.solids:
                    # Check if solid collider overlaps this tile significantly
                    if tile_rect.colliderect(solid):
                        self.walkable[r][c] = False
                        break

    def is_tile_walkable(self, c: int, r: int) -> bool:
        if 0 <= c < self.cols and 0 <= r < self.rows:
            return self.walkable[r][c]
        return False

    def find_path(self, start_pos: Tuple[float, float], goal_pos: Tuple[float, float]) -> List[Tuple[int, int]]:
        """
        Find path from start_pos (pixel coordinates) to goal_pos (pixel coordinates).
        Returns a list of waypoint pixel coordinates [(x, y), ...].
        """
        start_c = max(0, min(self.cols - 1, int(start_pos[0] // TILE_SIZE)))
        start_r = max(0, min(self.rows - 1, int(start_pos[1] // TILE_SIZE)))
        goal_c = max(0, min(self.cols - 1, int(goal_pos[0] // TILE_SIZE)))
        goal_r = max(0, min(self.rows - 1, int(goal_pos[1] // TILE_SIZE)))

        # If goal tile itself is blocked (e.g. NPC or desk collider), find nearest walkable neighbor
        if not self.is_tile_walkable(goal_c, goal_r):
            best_dist = float('inf')
            alt_goal = None
            for dc, dr in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)]:
                nc, nr = goal_c + dc, goal_r + dr
                if self.is_tile_walkable(nc, nr):
                    dist = abs(nc - start_c) + abs(nr - start_r)
                    if dist < best_dist:
                        best_dist = dist
                        alt_goal = (nc, nr)
            if alt_goal:
                goal_c, goal_r = alt_goal
            else:
                return []

        # A* Priority Queue: (f_score, g_score, (col, row))
        start_node = (start_c, start_r)
        goal_node = (goal_c, goal_r)

        if start_node == goal_node:
            return [(int(goal_pos[0]), int(goal_pos[1]))]

        open_set = []
        heapq.heappush(open_set, (0, 0, start_node))
        came_from = {}
        g_scores = {start_node: 0.0}

        def heuristic(a, b):
            # Manhattan distance
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        visited = set()

        while open_set:
            _, current_g, current = heapq.heappop(open_set)

            if current in visited:
                continue
            visited.add(current)

            if current == goal_node:
                # Reconstruct path
                path_tiles = []
                curr = goal_node
                while curr in came_from:
                    path_tiles.append(curr)
                    curr = came_from[curr]
                path_tiles.append(start_node)
                path_tiles.reverse()

                # Convert tile centers to pixel coordinates
                pixel_path = []
                for tc, tr in path_tiles:
                    pixel_path.append((tc * TILE_SIZE + TILE_SIZE // 2, tr * TILE_SIZE + TILE_SIZE // 2))

                # Smoothly end at exact goal pos
                if pixel_path:
                    pixel_path[-1] = (int(goal_pos[0]), int(goal_pos[1]))

                return pixel_path

            # Cardinal 4-way neighbors (avoids cutting solid corners diagonally)
            for dc, dr in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor = (current[0] + dc, current[1] + dr)
                if not self.is_tile_walkable(neighbor[0], neighbor[1]):
                    continue

                tentative_g = current_g + 1.0
                if neighbor not in g_scores or tentative_g < g_scores[neighbor]:
                    came_from[neighbor] = current
                    g_scores[neighbor] = tentative_g
                    f_score = tentative_g + heuristic(neighbor, goal_node)
                    heapq.heappush(open_set, (f_score, tentative_g, neighbor))

        return []


def draw_route_guidance(surface: pygame.Surface, path: List[Tuple[int, int]], camera_offset: Tuple[int, int], anim_pulse: float = 0.0):
    """
    Renders an illuminated, glowing breadcrumb trail along the computed route.
    anim_pulse is a value between 0.0 and 1.0 used to create an animated flowing ripple effect.
    """
    if not path or len(path) < 2:
        return

    cam_x, cam_y = camera_offset
    points_on_screen = [(px - cam_x, py - cam_y) for px, py in path]

    # Draw breadcrumb glowing dots along waypoints
    pulse_offset = (anim_pulse * 10) % 6
    for i, pt in enumerate(points_on_screen):
        if i == 0:
            continue  # skip player's current position

        is_target = (i == len(points_on_screen) - 1)
        if is_target:
            # Draw target pulsing beacon
            radius = int(5 + math.sin(anim_pulse * 6.28) * 1.5)
            pygame.draw.circle(surface, (255, 183, 3), pt, radius)
            pygame.draw.circle(surface, (255, 255, 255), pt, max(2, radius - 2))
        else:
            # Subtle navigation breadcrumb
            dot_phase = (i + pulse_offset) % 3
            dot_color = (72, 202, 228) if dot_phase < 1.5 else (0, 180, 216)
            pygame.draw.circle(surface, dot_color, pt, 2)
