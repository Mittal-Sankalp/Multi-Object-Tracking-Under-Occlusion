"""
MarketQuest - Automated Tests for A* Pathfinding
"""

import unittest
import pygame
from src.pathfinding import GridPathfinder
from config import TILE_SIZE


class TestPathfinding(unittest.TestCase):
    def test_straight_line_path(self):
        """Test simple path with no obstacles."""
        solids = []
        pf = GridPathfinder(tile_cols=10, tile_rows=10, solids=solids)
        start = (1 * TILE_SIZE, 1 * TILE_SIZE)
        goal = (5 * TILE_SIZE, 1 * TILE_SIZE)
        path = pf.find_path(start, goal)
        self.assertTrue(len(path) >= 2)
        self.assertEqual(path[-1], goal)

    def test_avoids_wall_obstacle(self):
        """Test path navigates around a solid wall barrier."""
        # Solid vertical wall from row 1 to row 4 at col 3
        solids = [
            pygame.Rect(3 * TILE_SIZE, 1 * TILE_SIZE, TILE_SIZE, 4 * TILE_SIZE)
        ]
        pf = GridPathfinder(tile_cols=10, tile_rows=10, solids=solids)
        start = (1 * TILE_SIZE, 2 * TILE_SIZE)
        goal = (5 * TILE_SIZE, 2 * TILE_SIZE)
        path = pf.find_path(start, goal)

        self.assertTrue(len(path) > 0)
        # Verify no waypoint in path intersects the solid rect
        for pt in path:
            pt_rect = pygame.Rect(pt[0] - 2, pt[1] - 2, 4, 4)
            for s in solids:
                self.assertFalse(s.colliderect(pt_rect), f"Path intersected solid wall at {pt}")

    def test_blocked_goal_finds_nearest_neighbor(self):
        """Test that if the goal itself is inside a solid (e.g. NPC collider), it navigates adjacent."""
        solids = [
            pygame.Rect(5 * TILE_SIZE, 5 * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        ]
        pf = GridPathfinder(tile_cols=10, tile_rows=10, solids=solids)
        start = (1 * TILE_SIZE, 1 * TILE_SIZE)
        goal = (5 * TILE_SIZE + 12, 5 * TILE_SIZE + 12)
        path = pf.find_path(start, goal)
        self.assertTrue(len(path) >= 2)

    def test_completely_enclosed_unreachable(self):
        """Test unreachable destination returns empty path without crashing."""
        # Enclose the goal completely
        solids = [
            pygame.Rect(4 * TILE_SIZE, 4 * TILE_SIZE, 3 * TILE_SIZE, TILE_SIZE),
            pygame.Rect(4 * TILE_SIZE, 6 * TILE_SIZE, 3 * TILE_SIZE, TILE_SIZE),
            pygame.Rect(4 * TILE_SIZE, 4 * TILE_SIZE, TILE_SIZE, 3 * TILE_SIZE),
            pygame.Rect(6 * TILE_SIZE, 4 * TILE_SIZE, TILE_SIZE, 3 * TILE_SIZE),
        ]
        pf = GridPathfinder(tile_cols=10, tile_rows=10, solids=solids)
        start = (1 * TILE_SIZE, 1 * TILE_SIZE)
        goal = (5 * TILE_SIZE + 12, 5 * TILE_SIZE + 12)
        path = pf.find_path(start, goal)
        self.assertEqual(path, [])


if __name__ == "__main__":
    unittest.main()
