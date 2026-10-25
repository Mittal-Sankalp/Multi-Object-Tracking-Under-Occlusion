"""
MarketQuest - Dialogue System & Interaction Tree
Handles branching conversations, character portraits, typewriter text animation, and event triggers.
Strictly respects UI container bounds, wrapping text and choices to prevent overflow.
"""

import json
import pygame
from typing import Dict, List, Optional, Any, Tuple
from config import (
    COLOR_PANEL_BG, COLOR_PANEL_ALT, COLOR_BORDER, COLOR_BORDER_ACCENT,
    COLOR_TEXT_WHITE, COLOR_TEXT_MUTED, COLOR_TEXT_GOLD, COLOR_SHADOW,
    DEFAULT_TEXT_SPEED, DATA_DIR, SPRITES_DIR
)
from src.sound import SoundManager
from src.text_util import wrap_text, truncate_text

class DialogueManager:
    def __init__(self, font: pygame.font.Font, small_font: pygame.font.Font):
        self.font = font
        self.small_font = small_font
        self.data: Dict[str, Any] = {}
        self.active: bool = False
        
        # Current conversation state
        self.current_npc_id: str = ""
        self.npc_name: str = ""
        self.npc_title: str = ""
        self.avatar_color: Tuple[int, int, int] = (200, 200, 200)
        self.current_node_id: str = "start"
        self.current_text: str = ""
        self.displayed_chars: float = 0.0
        self.text_speed: float = float(DEFAULT_TEXT_SPEED)
        self.choices: List[Dict[str, str]] = []
        self.selected_choice: int = 0
        self.is_finished_typing: bool = False
        self.waiting_for_advance: bool = False
        
        # Trigger hooks
        self.pending_event: Optional[str] = None
        self.pending_mission: Optional[str] = None
        self.pending_clue: Optional[str] = None

        self.load_dialogue_data()

    def load_dialogue_data(self, path: Optional[Any] = None):
        p = path or (DATA_DIR / "dialogue.json")
        if p.exists():
            with open(p, 'r', encoding='utf-8') as f:
                self.data = json.load(f)

    def start_conversation(self, npc_id: str, npc_name: str = "", npc_title: str = "", 
                           avatar_color: Tuple[int, int, int] = (200, 200, 200)):
        self.active = True
        self.current_npc_id = npc_id
        
        npc_cfg = self.data.get("npcs", {}).get(npc_id, {})
        self.npc_name = npc_name or npc_cfg.get("name", "Financial Resident")
        self.npc_title = npc_title or npc_cfg.get("title", "Market Participant")
        self.avatar_color = avatar_color or tuple(npc_cfg.get("avatar_color", [200, 200, 200]))
        
        self.set_node("start")

    def set_node(self, node_id: str):
        self.current_node_id = node_id
        npc_nodes = self.data.get("npcs", {}).get(self.current_npc_id, {}).get("dialogues", {})
        node = npc_nodes.get(node_id, {})

        if not node:
            if node_id == "close":
                self.close()
                return
            self.current_text = f"Greetings! I'm {self.npc_name}, {self.npc_title}. Financial markets move on corporate earnings and macro policy—stay disciplined, inspect company fundamentals, and verify the facts."
            self.displayed_chars = 0.0
            self.is_finished_typing = False
            self.choices = [{"text": "Thank you for the advice.", "close": True}]
            self.selected_choice = 0
            self.waiting_for_advance = False
            return

        self.current_text = node.get("text", "")
        self.displayed_chars = 0.0
        self.is_finished_typing = False
        self.choices = node.get("choices", [])
        self.selected_choice = 0
        self.waiting_for_advance = len(self.choices) == 0

        # Check triggers
        if "trigger_event" in node:
            self.pending_event = node["trigger_event"]
        if "trigger_mission" in node:
            self.pending_mission = node["trigger_mission"]
        if "trigger_clue" in node:
            self.pending_clue = node["trigger_clue"]
        if node.get("close", False) and not self.choices:
            self.waiting_for_advance = True

    def close(self):
        self.active = False
        self.current_npc_id = ""
        self.current_text = ""

    def update(self, dt: float):
        if not self.active:
            return

        if not self.is_finished_typing:
            prev_int = int(self.displayed_chars)
            self.displayed_chars += self.text_speed * dt
            new_int = int(self.displayed_chars)
            
            if new_int > prev_int and new_int % 3 == 0:
                SoundManager.get_instance().play("dialog")

            if self.displayed_chars >= len(self.current_text):
                self.displayed_chars = float(len(self.current_text))
                self.is_finished_typing = True

    def handle_input(self, event: pygame.event.Event) -> bool:
        """Handle keyboard and mouse events. Returns True if event consumed."""
        if not self.active:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_e):
                if not self.is_finished_typing:
                    # Skip typewriter directly to full text
                    self.displayed_chars = float(len(self.current_text))
                    self.is_finished_typing = True
                    return True
                else:
                    if self.choices:
                        choice = self.choices[self.selected_choice]
                        SoundManager.get_instance().play("click")
                        if choice.get("close", False) or "next" not in choice:
                            self.close()
                        else:
                            self.set_node(choice["next"])
                        return True
                    else:
                        SoundManager.get_instance().play("click")
                        self.close()
                        return True

            elif event.key == pygame.K_UP or event.key == pygame.K_w:
                if self.is_finished_typing and self.choices:
                    self.selected_choice = (self.selected_choice - 1) % len(self.choices)
                    SoundManager.get_instance().play("click")
                    return True

            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                if self.is_finished_typing and self.choices:
                    self.selected_choice = (self.selected_choice + 1) % len(self.choices)
                    SoundManager.get_instance().play("click")
                    return True

            elif event.key == pygame.K_ESCAPE:
                self.close()
                return True

            elif self.is_finished_typing and self.choices and pygame.K_1 <= event.key <= pygame.K_9:
                idx = event.key - pygame.K_1
                if idx < len(self.choices):
                    self.selected_choice = idx
                    choice = self.choices[idx]
                    SoundManager.get_instance().play("click")
                    if choice.get("close", False) or "next" not in choice:
                        self.close()
                    else:
                        self.set_node(choice["next"])
                    return True

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.is_finished_typing:
                self.displayed_chars = float(len(self.current_text))
                self.is_finished_typing = True
                return True

        return True

    def draw(self, surface: pygame.Surface, screen_w: int, screen_h: int):
        if not self.active:
            return

        box_margin = 10
        # Calculate dynamic height based on choices count to prevent bottom overflow
        extra_h = len(self.choices) * 16 if self.is_finished_typing and self.choices else 0
        box_h = min(140, 105 + extra_h)
        box_w = screen_w - (box_margin * 2)
        box_rect = pygame.Rect(box_margin, screen_h - box_h - box_margin - 4, box_w, box_h)

        # 1. Main Frame
        pygame.draw.rect(surface, (12, 18, 36), box_rect, border_radius=6)
        pygame.draw.rect(surface, COLOR_BORDER, box_rect, width=2, border_radius=6)
        pygame.draw.rect(surface, COLOR_BORDER_ACCENT, box_rect.inflate(-4, -4), width=1, border_radius=4)

        # 2. Character Portrait Box (Left)
        avatar_w = 54
        avatar_h = 54
        avatar_rect = pygame.Rect(box_rect.x + 10, box_rect.y + 10, avatar_w, avatar_h)
        pygame.draw.rect(surface, (18, 26, 48), avatar_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_BORDER, avatar_rect, width=1, border_radius=4)

        # Draw portrait avatar
        pygame.draw.circle(surface, self.avatar_color, avatar_rect.center, 20)
        pygame.draw.circle(surface, (245, 195, 150), avatar_rect.center, 15)
        pygame.draw.circle(surface, (20, 20, 30), (avatar_rect.centerx - 4, avatar_rect.centery - 2), 2)
        pygame.draw.circle(surface, (20, 20, 30), (avatar_rect.centerx + 4, avatar_rect.centery - 2), 2)
        pygame.draw.arc(surface, (20, 20, 30), (avatar_rect.centerx - 5, avatar_rect.centery + 1, 10, 6), 3.14, 0, 1)

        # 3. Name & Title Banner
        text_x = avatar_rect.right + 12
        max_text_width = box_rect.right - text_x - 14

        name_surf = self.font.render(self.npc_name, True, COLOR_TEXT_GOLD)
        title_str = truncate_text(f"[{self.npc_title}]", self.small_font, max_text_width - name_surf.get_width() - 8)
        title_surf = self.small_font.render(title_str, True, COLOR_TEXT_MUTED)

        surface.blit(name_surf, (text_x, box_rect.y + 8))
        surface.blit(title_surf, (text_x + name_surf.get_width() + 8, box_rect.y + 10))

        # Divider line
        pygame.draw.line(surface, COLOR_BORDER, (text_x, box_rect.y + 26), (box_rect.right - 14, box_rect.y + 26), 1)

        # 4. Typewriter Dialogue Text with Font-Metric Word Wrap
        content_to_show = self.current_text[:int(self.displayed_chars)]
        lines = wrap_text(content_to_show, self.small_font, max_text_width)

        line_y = box_rect.y + 32
        max_lines_allowed = 3 if self.choices and self.is_finished_typing else 4
        
        orig_clip = surface.get_clip()
        surface.set_clip(box_rect.inflate(-8, -8))

        try:
            for line in lines[:max_lines_allowed]:
                line_surf = self.small_font.render(line, True, COLOR_TEXT_WHITE)
                surface.blit(line_surf, (text_x, line_y))
                line_y += 14

            # 5. Choices or Advance Indicator
            if self.is_finished_typing:
                if self.choices:
                    choice_y = line_y + 4
                    for idx, c in enumerate(self.choices):
                        if choice_y + 13 > box_rect.bottom - 4:
                            break
                        is_sel = (idx == self.selected_choice)
                        prefix = "▶ " if is_sel else "  "
                        col = COLOR_TEXT_GOLD if is_sel else COLOR_TEXT_MUTED
                        c_text = truncate_text(f"{prefix}{idx+1}. {c['text']}", self.small_font, max_text_width)
                        c_surf = self.small_font.render(c_text, True, col)
                        surface.blit(c_surf, (text_x, choice_y))
                        choice_y += 14
                else:
                    cont_text = "[SPACE / ENTER / E to Continue]"
                    pulse_color = COLOR_TEXT_GOLD if (pygame.time.get_ticks() % 800 < 400) else COLOR_TEXT_MUTED
                    cont_surf = self.small_font.render(cont_text, True, pulse_color)
                    surface.blit(cont_surf, (box_rect.right - cont_surf.get_width() - 14, box_rect.bottom - 18))
        finally:
            surface.set_clip(orig_clip)
