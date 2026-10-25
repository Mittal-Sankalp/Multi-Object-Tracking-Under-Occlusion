"""
MarketQuest - Predefined Story Campaign Engine ("From Rookie to Market Strategist")
Manages structured 6-chapter campaign progression, objectives, narrative milestones,
investment thesis recording, and post-campaign free exploration.
"""

import json
from typing import Dict, List, Optional, Any, Set, Tuple
from pathlib import Path
from config import DATA_DIR


class StoryManager:
    def __init__(self, campaign_path: Optional[Path] = None):
        self.campaign_path = campaign_path or (DATA_DIR / "story_campaign.json")
        self.chapters: List[Dict[str, Any]] = []
        self.title: str = "From Rookie to Market Strategist"
        self.current_chapter_idx: int = 0
        self.current_objective_idx: int = 0
        self.campaign_completed: bool = False
        self.completed_objectives: Set[str] = set()
        self.theses: List[Dict[str, Any]] = []

        self.load_campaign()

    def load_campaign(self):
        if self.campaign_path.exists():
            with open(self.campaign_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.title = data.get("title", self.title)
                self.chapters = data.get("chapters", [])

    def get_current_chapter(self) -> Optional[Dict[str, Any]]:
        if 0 <= self.current_chapter_idx < len(self.chapters):
            return self.chapters[self.current_chapter_idx]
        return None

    def get_active_objective(self) -> Optional[Dict[str, Any]]:
        chapter = self.get_current_chapter()
        if not chapter:
            return None
        objs = chapter.get("objectives", [])
        if 0 <= self.current_objective_idx < len(objs):
            return objs[self.current_objective_idx]
        return None

    def get_total_chapters(self) -> int:
        return len(self.chapters)

    def advance_objective(self, game) -> Optional[str]:
        """
        Marks active objective completed, awards XP/Cash/Badges/Clues,
        and advances to next objective or chapter.
        """
        active_obj = self.get_active_objective()
        if not active_obj:
            return None

        obj_id = active_obj["id"]
        self.completed_objectives.add(obj_id)

        # Rewards
        xp = active_obj.get("reward_xp", 0)
        cash = active_obj.get("reward_cash", 0.0)
        badge = active_obj.get("reward_badge", "")
        clue_id = active_obj.get("reward_clue", "")

        if xp > 0 and hasattr(game, "add_xp"):
            game.add_xp(xp, active_obj["title"])
        if cash > 0 and hasattr(game, "portfolio"):
            game.portfolio.cash = round(game.portfolio.cash + cash, 2)
        if badge and hasattr(game, "badges") and badge not in game.badges:
            game.badges.append(badge)
        if clue_id and hasattr(game, "investigation"):
            game.investigation.unlock_clue(clue_id)

        if hasattr(game, "sound_mgr"):
            game.sound_mgr.play("fanfare")

        banner_msg = f"OBJECTIVE COMPLETED: {active_obj['title']} (+{xp} XP)"

        # Advance to next objective
        chapter = self.get_current_chapter()
        objs = chapter.get("objectives", []) if chapter else []
        self.current_objective_idx += 1

        # Check if chapter complete
        if self.current_objective_idx >= len(objs):
            self.current_chapter_idx += 1
            self.current_objective_idx = 0
            if self.current_chapter_idx >= len(self.chapters):
                self.campaign_completed = True
                banner_msg = "🏆 CONGRATULATIONS! You have completed the MarketQuest Campaign! All Global Exchanges Unlocked!"
            else:
                next_chap = self.get_current_chapter()
                if next_chap:
                    banner_msg = f"🏆 CHAPTER COMPLETED! Started {next_chap['title']}!"

        return banner_msg

    def on_talk_npc(self, npc_id: str, game) -> Optional[str]:
        active_obj = self.get_active_objective()
        if not active_obj:
            return None
        target_npc = active_obj.get("target_npc", "").lower()
        nid = npc_id.lower()
        if target_npc and (target_npc == nid or target_npc.startswith(nid + "_") or nid.startswith(target_npc + "_") or target_npc.startswith(nid)):
            return self.advance_objective(game)
        return None

    def on_inspect_object(self, obj_id: str, game) -> Optional[str]:
        active_obj = self.get_active_objective()
        if not active_obj:
            return None
        target_obj = active_obj.get("target_object", "").lower()
        oid = obj_id.lower()
        if target_obj and (target_obj == oid or target_obj.startswith(oid + "_") or oid.startswith(target_obj + "_") or target_obj in oid or oid in target_obj):
            return self.advance_objective(game)
        return None

    def on_enter_map(self, map_id: str, game) -> Optional[str]:
        active_obj = self.get_active_objective()
        if not active_obj:
            return None
        # Check target door or map entrance
        target_map = active_obj.get("target_map", "")
        if target_map and target_map == map_id:
            # If objective specifically only requires entering this map
            if "target_npc" not in active_obj and "target_object" not in active_obj and "required_action" not in active_obj:
                return self.advance_objective(game)
        return None

    def on_trade_executed(self, symbol: str, shares: int, price: float, is_buy: bool, game) -> Optional[str]:
        active_obj = self.get_active_objective()
        if not active_obj:
            return None

        # Check specific trade requirements
        req_action = active_obj.get("required_action", "")
        target_sym = active_obj.get("target_symbol", "")
        min_shares = active_obj.get("min_shares", 1)

        if req_action == "buy" and is_buy:
            if (not target_sym or target_sym.upper() == symbol.upper()) and shares >= min_shares:
                return self.advance_objective(game)
        elif req_action == "trade_any":
            return self.advance_objective(game)
        elif req_action == "diversify_3_sectors":
            # Check if player holds 3 distinct sectors
            held_sectors = set()
            for s, pos in game.portfolio.positions.items():
                if pos.shares > 0:
                    c = game.market.get_company(s)
                    if c:
                        held_sectors.add(c.sector)
            if len(held_sectors) >= 3:
                return self.advance_objective(game)

        return None

    def on_action_triggered(self, action_name: str, game) -> Optional[str]:
        active_obj = self.get_active_objective()
        if not active_obj:
            return None
        req_action = active_obj.get("required_action", "")
        if req_action and req_action.lower() == action_name.lower():
            return self.advance_objective(game)
        return None

    def record_thesis(self, thesis_data: Dict[str, Any]):
        """Store recorded investment thesis."""
        self.theses.insert(0, thesis_data)
        if len(self.theses) > 20:
            self.theses.pop()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_chapter_idx": self.current_chapter_idx,
            "current_objective_idx": self.current_objective_idx,
            "campaign_completed": self.campaign_completed,
            "completed_objectives": list(self.completed_objectives),
            "theses": self.theses
        }

    def load_state(self, data: Dict[str, Any]):
        self.current_chapter_idx = int(data.get("current_chapter_idx", 0))
        self.current_objective_idx = int(data.get("current_objective_idx", 0))
        self.campaign_completed = bool(data.get("campaign_completed", False))
        self.completed_objectives = set(data.get("completed_objectives", []))
        self.theses = data.get("theses", [])
