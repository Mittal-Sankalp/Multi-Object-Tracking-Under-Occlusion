"""
MarketQuest - Player Entity & Movement
Handles frame-rate-independent movement, collision resolution, direction, and animation.
"""

import pygame
from typing import Tuple, Dict, Any, Optional
from config import PLAYER_SPEED, TILE_SIZE

class Player:
    def __init__(self, x: float, y: float):
        self.x: float = float(x)
        self.y: float = float(y)
        self.width: int = 16
        self.height: int = 22
        
        # Collision box is smaller and centered at feet
        self.col_w: int = 12
        self.col_h: int = 10
        self.col_offset_x: int = 2
        self.col_offset_y: int = 12

        self.speed: float = float(PLAYER_SPEED)
        self.direction: str = "down"
        self.moving: bool = False
        
        # Animation state
        self.anim_timer: float = 0.0
        self.anim_frame: int = 0  # 0: stand, 1: step A, 2: step B
        self.idle_timer: float = 0.0
        self.footstep_particles: list = []  # [x, y, life, max_life]
        self.sprites: Optional[Dict[str, list[pygame.Surface]]] = None
        self._load_sprites()

        # Exterior memory for returning outside buildings
        self.exterior_pos: Tuple[float, float] = (self.x, self.y)
        self.exterior_map: str = "dalal_street"

        # Route guidance navigation
        self.route_guidance_active: bool = True
        self.current_route: list = []
        self.route_pulse_timer: float = 0.0

    @property
    def facing(self) -> str:
        return self.direction

    @facing.setter
    def facing(self, val: str):
        self.direction = val

    def _load_sprites(self):
        try:
            from config import SPRITES_DIR
            sheet_path = SPRITES_DIR / "player_sheet.png"
            if sheet_path.exists():
                sheet = pygame.image.load(str(sheet_path)).convert_alpha()
                directions = ["down", "up", "left", "right"]
                self.sprites = {}
                for row, d in enumerate(directions):
                    frames = []
                    for col in range(4):
                        rect = pygame.Rect(col * 16, row * 24, 16, 24)
                        frame_surf = pygame.Surface((16, 24), pygame.SRCALPHA)
                        frame_surf.blit(sheet, (0, 0), rect)
                        frames.append(frame_surf)
                    self.sprites[d] = frames
        except Exception:
            self.sprites = None

    @property
    def collision_rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.x + self.col_offset_x),
            int(self.y + self.col_offset_y),
            self.col_w,
            self.col_h
        )

    @property
    def bounds_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def get_interaction_point(self) -> Tuple[float, float]:
        """Get the point in front of the player where interaction occurs."""
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        reach = 18.0
        if self.direction == "up":
            return cx, cy - reach
        elif self.direction == "down":
            return cx, cy + reach
        elif self.direction == "left":
            return cx - reach, cy
        elif self.direction == "right":
            return cx + reach, cy
        return cx, cy

    def update(self, dt: float, keys: pygame.key.ScancodeWrapper, world: Any):
        dx = 0.0
        dy = 0.0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= 1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += 1.0
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= 1.0
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += 1.0

        if dx != 0.0 and dy != 0.0:
            # Diagonal normalisation
            dx *= 0.7071
            dy *= 0.7071

        self.moving = (dx != 0.0 or dy != 0.0)

        # Update facing direction
        if abs(dx) > abs(dy) and dx != 0:
            self.direction = "right" if dx > 0 else "left"
        elif dy != 0:
            self.direction = "down" if dy > 0 else "up"

        # Animation timing
        if self.moving:
            self.anim_timer += dt * 8.0
            self.anim_frame = int(self.anim_timer) % 4
            self.idle_timer = 0.0
            # Pattern: 0 (idle), 1 (step L), 0 (idle), 2 (step R)
            if self.anim_frame == 3:
                self.anim_frame = 1

            # Emit small subtle footstep dust every half step
            if int(self.anim_timer * 2) % 2 == 1 and len(self.footstep_particles) < 6:
                foot_x = self.x + (4 if self.anim_frame == 1 else 12)
                foot_y = self.y + self.height - 2
                self.footstep_particles.append([foot_x, foot_y, 0.20, 0.20])
        else:
            self.anim_timer = 0.0
            self.anim_frame = 0
            self.idle_timer += dt

        # Update footstep dust particles
        alive_particles = []
        for p in self.footstep_particles:
            p[2] -= dt
            if p[2] > 0:
                alive_particles.append(p)
        self.footstep_particles = alive_particles

        # Axis-independent collision resolution (sliding along walls)
        map_w = float(world.current_map.pixel_width)
        map_h = float(world.current_map.pixel_height)

        move_dist_x = dx * self.speed * dt
        if move_dist_x != 0:
            target_x = max(0.0, min(map_w - float(self.width), self.x + move_dist_x))
            new_col_x = pygame.Rect(
                int(target_x + self.col_offset_x),
                int(self.y + self.col_offset_y),
                self.col_w,
                self.col_h
            )
            if not world.check_collision(new_col_x):
                self.x = target_x

        move_dist_y = dy * self.speed * dt
        if move_dist_y != 0:
            target_y = max(0.0, min(map_h - float(self.height), self.y + move_dist_y))
            new_col_y = pygame.Rect(
                int(self.x + self.col_offset_x),
                int(target_y + self.col_offset_y),
                self.col_w,
                self.col_h
            )
            if not world.check_collision(new_col_y):
                self.y = target_y

        # Unconditionally ensure player sprite stays 100% within valid map pixels
        self.x = max(0.0, min(map_w - float(self.width), self.x))
        self.y = max(0.0, min(map_h - float(self.height), self.y))

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[int, int]):
        # Draw footstep dust particles first (behind player feet)
        for px, py, life, max_life in self.footstep_particles:
            rx = int(px - camera_offset[0])
            ry = int(py - camera_offset[1])
            alpha_ratio = max(0.0, life / max_life)
            radius = int(1 + (1.0 - alpha_ratio) * 2)
            c_val = int(120 + alpha_ratio * 40)
            pygame.draw.circle(surface, (c_val, c_val, c_val), (rx, ry), radius)

        render_x = int(self.x - camera_offset[0])
        render_y = int(self.y - camera_offset[1])

        # Subtle idle breathing bob (1 pixel up/down every 1.5 seconds)
        bob_y = 0
        if not self.moving and (int(self.idle_timer * 1.8) % 2 == 1):
            bob_y = -1

        # If sprite sheet available, draw frame
        if self.sprites and self.direction in self.sprites:
            frames = self.sprites[self.direction]
            f_idx = min(self.anim_frame, len(frames) - 1)
            surface.blit(frames[f_idx], (render_x, render_y + bob_y))
            return

        # Procedural fallback retro character rendering:
        # 1. Shadow at feet
        shadow_rect = pygame.Rect(render_x + 1, render_y + self.height - 4, self.width - 2, 4)
        pygame.draw.ellipse(surface, (10, 14, 25), shadow_rect)

        # 2. Body / Coat (Navy/Teal blazer with gold tie)
        torso_rect = pygame.Rect(render_x + 2, render_y + 8, self.width - 4, 9)
        pygame.draw.rect(surface, (30, 80, 140), torso_rect, border_radius=2)
        # Gold tie / collar
        pygame.draw.line(surface, (255, 200, 50), (render_x + self.width // 2, render_y + 9), (render_x + self.width // 2, render_y + 13), 1)

        # 3. Head & Hair (neat brown/amber hair with skin tone)
        head_rect = pygame.Rect(render_x + 3, render_y + 2, self.width - 6, 7)
        pygame.draw.rect(surface, (245, 195, 150), head_rect)
        hair_rect = pygame.Rect(render_x + 3, render_y + 1, self.width - 6, 3)
        pygame.draw.rect(surface, (80, 45, 25), hair_rect)

        # 4. Eyes based on direction
        if self.direction == "down":
            pygame.draw.line(surface, (20, 20, 30), (render_x + 5, render_y + 5), (render_x + 6, render_y + 5), 1)
            pygame.draw.line(surface, (20, 20, 30), (render_x + 9, render_y + 5), (render_x + 10, render_y + 5), 1)
        elif self.direction == "left":
            pygame.draw.line(surface, (20, 20, 30), (render_x + 4, render_y + 5), (render_x + 5, render_y + 5), 1)
        elif self.direction == "right":
            pygame.draw.line(surface, (20, 20, 30), (render_x + 10, render_y + 5), (render_x + 11, render_y + 5), 1)

        # 5. Legs / Walking step offset
        leg_offset = 0
        if self.moving:
            leg_offset = 1 if (self.anim_frame == 1) else -1

        leg_left = pygame.Rect(render_x + 3, render_y + 17, 4, 5 + leg_offset)
        leg_right = pygame.Rect(render_x + self.width - 7, render_y + 17, 4, 5 - leg_offset)
        pygame.draw.rect(surface, (20, 30, 50), leg_left)
        pygame.draw.rect(surface, (20, 30, 50), leg_right)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "x": self.x,
            "y": self.y,
            "direction": self.direction,
            "exterior_pos": list(self.exterior_pos),
            "exterior_map": self.exterior_map
        }

    def load_state(self, state: Dict[str, Any]):
        self.x = float(state.get("x", self.x))
        self.y = float(state.get("y", self.y))
        self.direction = state.get("direction", "down")
        ext_p = state.get("exterior_pos")
        if ext_p and len(ext_p) == 2:
            self.exterior_pos = (float(ext_p[0]), float(ext_p[1]))
        self.exterior_map = state.get("exterior_map", "dalal_street")
