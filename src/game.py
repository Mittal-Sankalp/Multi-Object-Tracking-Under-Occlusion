"""
MarketQuest - Enhanced Core Game Engine & State Coordinator
Coordinates gameplay loops, live clocks, exchange schedules, landmark interactions,
news pop-ups, portfolio tracking, trade confirmations, and persistence.
"""

import pygame
import sys
from typing import Dict, List, Optional, Any, Tuple
from config import (
    VIRTUAL_WIDTH, VIRTUAL_HEIGHT,
    COLOR_BG_DARK, COLOR_TEXT_GOLD,
    LOCATION_WALL_STREET, LOCATION_DALAL_STREET, LOCATION_KABUTOCHO, LOCATION_LONDON,
    INTERIOR_BSE, INTERIOR_NYSE, INTERIOR_TSE, INTERIOR_LSE,
    MARKET_TICK_SECONDS, INITIAL_CASH
)
from src.player import Player
from src.world import World, NPC, WorldObject
from src.market import MarketEngine
from src.trading import Portfolio
from src.dialogue import DialogueManager
from src.ui import UIManager
from src.sound import SoundManager
from src.save_manager import SaveManager
from src.clock import MarketClock, EXCHANGE_BSE, EXCHANGE_NYSE, EXCHANGE_TSE, EXCHANGE_LSE, MODE_SIMULATION, MODE_REALTIME
from src.investigation import InvestigationManager, InvestmentThesis
from src.story import StoryManager

# Game States
STATE_TITLE = "title"
STATE_GAMEPLAY = "gameplay"
STATE_DIALOGUE = "dialogue"
STATE_TRADING = "trading"
STATE_PORTFOLIO = "portfolio"
STATE_CLUE_JOURNAL = "clue_journal"
STATE_NEWS = "news"
STATE_TRAVEL = "travel"
STATE_GLOSSARY = "glossary"
STATE_PAUSE = "pause"
STATE_SETTINGS = "settings"
STATE_EXCHANGE_HUB = "exchange_hub"
STATE_COMPANY_DOSSIER = "company_dossier"
STATE_BANK = "bank"
STATE_ACADEMY = "academy"
STATE_BULL_MODAL = "bull_modal"
STATE_BANYAN_MODAL = "banyan_modal"
STATE_CHAI_MODAL = "chai_modal"
STATE_RETURN_BREAKDOWN = "return_breakdown"
STATE_CAMPAIGN = "campaign"
STATE_INVESTMENT_THESIS = "investment_thesis"
STATE_INTERIOR_MAP = "interior_map"

class Game:
    def __init__(self, screen: pygame.Surface, window_scale: int = 2):
        self.screen = screen
        self.window_scale = window_scale
        self.virtual_surface = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
        self.clock_fps = pygame.time.Clock()
        self.running = True

        self._init_fonts()

        # Core Subsystems
        self.sound_mgr = SoundManager.get_instance()
        self.save_mgr = SaveManager()
        self.market = MarketEngine()
        self.portfolio = Portfolio(starting_cash=INITIAL_CASH)
        self.investigation = InvestigationManager()
        self.story = StoryManager()
        self.world = World()
        self.world.market = self.market
        self.player = Player(16 * 24, 10 * 24)
        self.dialogue_mgr = DialogueManager(self.font, self.small_font)
        self.ui_mgr = UIManager(self.font, self.small_font, self.title_font)
        self.clock = MarketClock(mode=MODE_SIMULATION, time_scale=60.0)
        self.route_recalc_timer = 0.0

        # State management
        self.state = STATE_TITLE
        self.previous_state = STATE_GAMEPLAY
        self.tick_timer = 0.0
        self.global_ticks = 0

        # Missions System
        self.xp = 0
        self.badges: List[str] = []
        self.missions = [
            {
                "id": "first_steps",
                "title": "First Steps on Wall St",
                "desc": "Talk to Arthur Pendelton near NYSE to learn what a share represents.",
                "completed": False,
                "reward_cash": 250.0,
                "reward_xp": 50,
                "reward_badge": "Junior Investor"
            },
            {
                "id": "first_trade",
                "title": "Becoming an Owner",
                "desc": "Open the Trading Terminal [T] and buy your first share of stock.",
                "completed": False,
                "reward_cash": 500.0,
                "reward_xp": 100,
                "reward_badge": "Shareholder"
            },
            {
                "id": "market_event",
                "title": "Riding the Waves",
                "desc": "Trigger a breaking market event by talking to CEO Vance or reporter Priya Sharma.",
                "completed": False,
                "reward_cash": 0.0,
                "reward_xp": 150,
                "reward_badge": "Market Savvy"
            },
            {
                "id": "visit_mumbai",
                "title": "Dalal Street Discovery",
                "desc": "Travel to Mumbai and explore Dalal Street using the transit portal [M].",
                "completed": False,
                "reward_cash": 300.0,
                "reward_xp": 150,
                "reward_badge": "Global Explorer"
            },
            {
                "id": "diversify",
                "title": "Diversified Tycoon",
                "desc": "Hold shares in at least 3 distinct market sectors simultaneously.",
                "completed": False,
                "reward_cash": 1000.0,
                "reward_xp": 250,
                "reward_badge": "Prudent Investor"
            }
        ]

        self.mission_complete_banner: Optional[str] = None
        self.mission_banner_timer = 0.0

    def _init_fonts(self):
        pygame.font.init()
        # Direct font initialization to avoid Darwin SysFont isolation permission error
        self.font = pygame.font.Font(None, 18)
        self.small_font = pygame.font.Font(None, 14)
        self.title_font = pygame.font.Font(None, 32)

    def get_active_mission(self) -> Optional[Dict[str, Any]]:
        for m in self.missions:
            if not m["completed"]:
                return m
        return None

    def is_on_trading_floor(self) -> bool:
        """Returns True only if player is physically inside an authorized Stock Exchange trading floor."""
        return self.world.current_location_id in (INTERIOR_BSE, INTERIOR_NYSE, INTERIOR_TSE, INTERIOR_LSE)

    def add_xp(self, amount: int, reason: str = ""):
        """Award XP and trigger Level Up celebration when reaching thresholds."""
        old_lvl, _, _, _, _ = self.investigation.get_level_info(self.xp)
        self.xp += amount
        new_lvl, new_title, _, _, _ = self.investigation.get_level_info(self.xp)
        if new_lvl > old_lvl:
            self.sound_mgr.play("fanfare")
            self.mission_complete_banner = f"⭐ LEVEL UP! You reached Level {new_lvl}: {new_title}!"
            self.mission_banner_timer = 5.0
        elif reason:
            self.mission_complete_banner = f"+{amount} XP ({reason})"
            self.mission_banner_timer = 3.0

    def complete_mission(self, mission_id: str):
        for m in self.missions:
            if m["id"] == mission_id and not m["completed"]:
                m["completed"] = True
                self.add_xp(m["reward_xp"], m["title"])
                if m["reward_cash"] > 0:
                    self.portfolio.cash = round(self.portfolio.cash + m["reward_cash"], 2)
                if m["reward_badge"] and m["reward_badge"] not in self.badges:
                    self.badges.append(m["reward_badge"])

                self.sound_mgr.play("fanfare")
                self.mission_complete_banner = f"MISSION COMPLETE: {m['title']} (+{m['reward_xp']} XP)"
                self.mission_banner_timer = 4.0
                break

    def check_portfolio_missions(self):
        if any(pos.shares > 0 for pos in self.portfolio.positions.values()) or self.portfolio.trade_history:
            self.complete_mission("first_trade")

        held_sectors = set()
        for sym, pos in self.portfolio.positions.items():
            if pos.shares > 0:
                comp = self.market.get_company(sym)
                if comp:
                    held_sectors.add(comp.sector)
        if len(held_sectors) >= 3:
            self.complete_mission("diversify")

    def start_new_game(self):
        self.market = MarketEngine()
        self.portfolio = Portfolio(starting_cash=INITIAL_CASH)
        self.investigation = InvestigationManager()
        self.story = StoryManager()
        self.world = World()
        spawn = self.world.set_location(LOCATION_DALAL_STREET, "default")
        self.player = Player(spawn[0], spawn[1])
        self.player.exterior_map = LOCATION_DALAL_STREET
        self.player.exterior_pos = spawn
        self.clock = MarketClock(mode=MODE_SIMULATION, time_scale=60.0)
        self.xp = 0
        self.badges = []
        for m in self.missions:
            m["completed"] = False
        self.state = STATE_GAMEPLAY
        self.ui_mgr.show_tutorial = True
        self.sound_mgr.play("buy")

    def load_saved_game(self) -> bool:
        data = self.save_mgr.load_game()
        if not data:
            return False

        try:
            loc_id = data.get("location", LOCATION_WALL_STREET)
            self.world.set_location(loc_id)
            p_data = data.get("player", {})
            self.player.x = float(p_data.get("x", 16 * 24))
            self.player.y = float(p_data.get("y", 10 * 24))
            self.player.direction = p_data.get("direction", "down")

            self.market.load_state(data.get("market", {}))
            self.portfolio.load_state(data.get("portfolio", {}))
            if "clock" in data:
                self.clock.load_state(data["clock"])

            if "investigation" in data:
                self.investigation.load_state(data["investigation"])

            if "story" in data:
                self.story.load_state(data["story"])

            self.xp = int(data.get("xp", 0))
            self.badges = data.get("badges", [])
            saved_missions = data.get("missions", {})
            for m in self.missions:
                if m["id"] in saved_missions:
                    m["completed"] = saved_missions[m["id"]]

            self.state = STATE_GAMEPLAY
            self.sound_mgr.play("buy")
            return True
        except Exception:
            return False

    def save_current_game(self) -> Tuple[bool, str]:
        state_dict = {
            "location": self.world.current_location_id,
            "player": self.player.to_dict(),
            "market": self.market.to_dict(),
            "portfolio": self.portfolio.to_dict(),
            "investigation": self.investigation.to_dict(),
            "story": self.story.to_dict(),
            "clock": self.clock.to_dict(),
            "xp": self.xp,
            "badges": self.badges,
            "missions": {m["id"]: m["completed"] for m in self.missions}
        }
        return self.save_mgr.save_game(state_dict)

    # -------------------------------------------------------------
    # EVENT HANDLING
    # -------------------------------------------------------------
    def handle_events(self):
        mouse_raw = pygame.mouse.get_pos()
        mouse_pos = (int(mouse_raw[0] / self.window_scale), int(mouse_raw[1] / self.window_scale))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if self.ui_mgr.show_tutorial:
                t_buttons = self.ui_mgr.draw_tutorial_modal(self.virtual_surface, mouse_pos)
                for b_action, btn in t_buttons:
                    if btn.handle_event(event, mouse_pos) and b_action == "close_tutorial":
                        self.ui_mgr.show_tutorial = False
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                    self.ui_mgr.show_tutorial = False
                continue

            # Route by State
            if self.state == STATE_TITLE:
                self._handle_title_event(event, mouse_pos)
            elif self.state == STATE_GAMEPLAY:
                self._handle_gameplay_event(event)
            elif self.state == STATE_DIALOGUE:
                self._handle_dialogue_event(event)
            elif self.state == STATE_TRADING:
                self._handle_trading_event(event, mouse_pos)
            elif self.state == STATE_PORTFOLIO:
                self._handle_portfolio_event(event, mouse_pos)
            elif self.state == STATE_CLUE_JOURNAL:
                self._handle_clue_journal_event(event, mouse_pos)
            elif self.state == STATE_NEWS:
                self._handle_news_event(event, mouse_pos)
            elif self.state == STATE_TRAVEL:
                self._handle_travel_event(event, mouse_pos)
            elif self.state == STATE_GLOSSARY:
                self._handle_glossary_event(event, mouse_pos)
            elif self.state == STATE_PAUSE:
                self._handle_pause_event(event, mouse_pos)
            elif self.state == STATE_SETTINGS:
                self._handle_settings_event(event, mouse_pos)
            elif self.state == STATE_EXCHANGE_HUB:
                self._handle_exchange_hub_event(event, mouse_pos)
            elif self.state == STATE_COMPANY_DOSSIER:
                self._handle_company_dossier_event(event, mouse_pos)
            elif self.state == STATE_BANK:
                self._handle_bank_event(event, mouse_pos)
            elif self.state == STATE_ACADEMY:
                self._handle_academy_event(event, mouse_pos)
            elif self.state == STATE_BULL_MODAL:
                self._handle_bull_event(event, mouse_pos)
            elif self.state == STATE_BANYAN_MODAL:
                self._handle_banyan_event(event, mouse_pos)
            elif self.state == STATE_CHAI_MODAL:
                self._handle_chai_event(event, mouse_pos)
            elif self.state == STATE_RETURN_BREAKDOWN:
                self._handle_return_breakdown_event(event, mouse_pos)
            elif self.state == STATE_CAMPAIGN:
                self._handle_campaign_event(event, mouse_pos)
            elif self.state == STATE_INVESTMENT_THESIS:
                self._handle_investment_thesis_event(event, mouse_pos)
            elif self.state == STATE_INTERIOR_MAP:
                self._handle_interior_map_event(event, mouse_pos)

    def _handle_title_event(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]):
        has_save = self.save_mgr.has_save()
        buttons = self.ui_mgr.draw_title_screen(self.virtual_surface, mouse_pos, has_save, self.global_ticks)
        for action, btn in buttons:
            if btn.handle_event(event, mouse_pos):
                if action == "new_game":
                    self.start_new_game()
                elif action == "continue":
                    if not self.load_saved_game():
                        self.start_new_game()
                elif action == "settings":
                    self.previous_state = STATE_TITLE
                    self.state = STATE_SETTINGS
                elif action == "quit":
                    self.running = False

    def _handle_gameplay_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e:
                self._interact()
            elif event.key == pygame.K_t:
                self.sound_mgr.play("click")
                self.state = STATE_TRADING
            elif event.key == pygame.K_p:
                self.sound_mgr.play("click")
                self.state = STATE_PORTFOLIO
            elif event.key == pygame.K_b:
                self.sound_mgr.play("click")
                self.state = STATE_RETURN_BREAKDOWN
                self.story.on_action_triggered("view_breakdown", self)
            elif event.key == pygame.K_c:
                self.sound_mgr.play("click")
                self.state = STATE_CAMPAIGN
            elif event.key == pygame.K_j:
                self.sound_mgr.play("click")
                self.state = STATE_INVESTMENT_THESIS
                self.story.on_action_triggered("open_journal", self)
            elif event.key == pygame.K_g:
                self.player.route_guidance_active = not getattr(self.player, "route_guidance_active", True)
                status_str = "ON" if self.player.route_guidance_active else "OFF"
                self.mission_complete_banner = f"Route Guidance: {status_str}"
                self.mission_banner_timer = 2.0
                self.sound_mgr.play("click")
            elif event.key == pygame.K_n:
                self.sound_mgr.play("click")
                self.state = STATE_NEWS
                self.story.on_action_triggered("open_news", self)
            elif event.key == pygame.K_m:
                self.sound_mgr.play("click")
                if self.world.current_location_id.startswith("interior_"):
                    self.state = STATE_INTERIOR_MAP
                else:
                    self.state = STATE_TRAVEL
            elif event.key == pygame.K_h:
                self.sound_mgr.play("click")
                self.state = STATE_GLOSSARY
            elif event.key == pygame.K_ESCAPE:
                self.sound_mgr.play("click")
                self.state = STATE_PAUSE

    def _interact(self):
        """Contextually interact with nearby NPC or WorldObject."""
        px, py = self.player.get_interaction_point()
        target = self.world.get_nearby_interactive(px, py, dist=32.0)

        if not target:
            target = self.world.get_nearby_interactive(
                self.player.x + self.player.width / 2,
                self.player.y + self.player.height / 2,
                dist=28.0
            )

        if isinstance(target, NPC):
            adv = self.story.on_talk_npc(target.id, self)
            if adv:
                self.mission_complete_banner = adv
                self.mission_banner_timer = 4.0

            self.dialogue_mgr.start_conversation(
                target.id, target.name, target.title, target.avatar_color
            )
            self.state = STATE_DIALOGUE
            self.sound_mgr.play("click")

        elif isinstance(target, WorldObject):
            self.sound_mgr.play("click")
            act = target.action_type

            adv = self.story.on_inspect_object(target.id, self)
            if adv:
                self.mission_complete_banner = adv
                self.mission_banner_timer = 4.0

            # Check if inspecting object unlocks an investigation clue
            if "(Clue:" in target.text:
                for c_id in ["apex_rd_chip", "apex_battery_yield", "apex_ceo_vision",
                             "titn_ma_deal", "titn_credit_risk", "titn_nim_margin",
                             "chai_harvest_record", "chai_shipping_reroute", "chai_se_asia_retail",
                             "aura_solar_subsidies", "macro_fed_rates",
                             "bse_rj_wisdom", "bse_1992_case_study", "bse_fundamental_model",
                             "bse_secret_ledger"]:
                    if c_id in target.text:
                        res = self.investigation.unlock_clue(c_id)
                        if res and res[1]:
                            self.add_xp(50, f"Clue: {res[0].title}")
                            self.sound_mgr.play("fanfare")
                            self.mission_complete_banner = f"CLUE LOGGED: {res[0].title} (+50 XP)"
                            self.mission_banner_timer = 4.0

            # Easter Egg Discovery
            if "egg_golden_bull" in target.id:
                if "Golden Bull Explorer" not in self.badges:
                    self.badges.append("Golden Bull Explorer")
                    self.add_xp(100, "Discovered Gilded Bull Statuette!")
                    self.mission_complete_banner = "EASTER EGG FOUND: Gilded Bull Statuette (+100 XP)!"
                    self.mission_banner_timer = 5.0
                    self.sound_mgr.play("fanfare")
            elif "egg_graham_book" in target.id:
                if "Value Disciple" not in self.badges:
                    self.badges.append("Value Disciple")
                    self.add_xp(50, "Read The Intelligent Investor 1st Edition")
                    self.mission_complete_banner = "EASTER EGG FOUND: Signed 1949 Graham First Edition (+50 XP)!"
                    self.mission_banner_timer = 5.0
                    self.sound_mgr.play("fanfare")

            if act == "enter_interior":
                if target.target_interior and target.target_interior in self.world.maps:
                    # Save exterior position and map
                    self.player.exterior_pos = (self.player.x, self.player.y)
                    self.player.exterior_map = self.world.current_location_id
                    new_spawn = self.world.set_location(target.target_interior, "entrance")
                    self.player.x, self.player.y = new_spawn
                    self.player.direction = "up"
                    self.world.update_camera(
                        self.player.x + self.player.width / 2.0,
                        self.player.y + self.player.height / 2.0
                    )
                    self.sound_mgr.play("travel")
                    door_adv = self.story.on_enter_map(target.target_interior, self)
                    if door_adv:
                        self.mission_complete_banner = door_adv
                        self.mission_banner_timer = 4.0
            elif act == "exit_interior":
                dest_map = getattr(self.player, "exterior_map", LOCATION_DALAL_STREET)
                if dest_map not in self.world.maps:
                    dest_map = LOCATION_DALAL_STREET
                self.world.set_location(dest_map)
                dest_pos = getattr(self.player, "exterior_pos", (16 * 24, 10 * 24))
                self.player.x, self.player.y = dest_pos
                self.player.direction = "down"
                self.world.update_camera(
                    self.player.x + self.player.width / 2.0,
                    self.player.y + self.player.height / 2.0
                )
                self.sound_mgr.play("travel")
            elif act == "open_trading":
                self.state = STATE_TRADING
            elif act == "open_academy":
                self.state = STATE_ACADEMY
            elif act == "exchange_hub":
                self.state = STATE_EXCHANGE_HUB
            elif act == "company_dossier":
                if target.target_symbol:
                    self.ui_mgr.inspected_symbol = target.target_symbol
                self.state = STATE_COMPANY_DOSSIER
            elif act == "bank_account":
                self.state = STATE_BANK
            elif act == "financial_academy":
                self.state = STATE_ACADEMY
            elif act == "bull_statue":
                self.state = STATE_BULL_MODAL
            elif act == "banyan_tree":
                self.state = STATE_BANYAN_MODAL
            elif act == "chai_stall":
                self.state = STATE_CHAI_MODAL
            elif act == "news_station":
                self.state = STATE_NEWS
            elif act == "transit":
                if target.target_loc:
                    self.sound_mgr.play("travel")
                    new_spawn = self.world.set_location(target.target_loc, "from_transit")
                    self.player.x, self.player.y = new_spawn
                    if target.target_loc == LOCATION_DALAL_STREET:
                        self.complete_mission("visit_mumbai")
                else:
                    self.state = STATE_TRAVEL
            else:
                self.dialogue_mgr.start_conversation(
                    "sign", target.title, "Information Marker", (180, 160, 120)
                )
                self.dialogue_mgr.current_text = target.text
                self.dialogue_mgr.displayed_chars = float(len(target.text))
                self.dialogue_mgr.is_finished_typing = True
                self.dialogue_mgr.choices = []
                self.state = STATE_DIALOGUE

    def _handle_dialogue_event(self, event: pygame.event.Event):
        self.dialogue_mgr.handle_input(event)
        if not self.dialogue_mgr.active:
            if self.dialogue_mgr.pending_event:
                ev_id = self.dialogue_mgr.pending_event
                self.dialogue_mgr.pending_event = None
                news_item = self.market.trigger_event_by_id(ev_id)
                if news_item:
                    self.ui_mgr.trigger_news_toast(news_item)
                self.complete_mission("market_event")
                self.sound_mgr.play("fanfare")

            if self.dialogue_mgr.pending_clue:
                clue_id = self.dialogue_mgr.pending_clue
                self.dialogue_mgr.pending_clue = None
                res = self.investigation.unlock_clue(clue_id)
                if res and res[1]:
                    self.add_xp(50, f"Field Clue: {res[0].title}")
                    self.sound_mgr.play("fanfare")
                    self.mission_complete_banner = f"CLUE LOGGED: {res[0].title} (+50 XP)"
                    self.mission_banner_timer = 4.0

            if self.dialogue_mgr.pending_mission == "mission_first_steps_complete":
                self.complete_mission("first_steps")
                self.dialogue_mgr.pending_mission = None

            self.state = STATE_GAMEPLAY

    def _handle_trading_event(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.ui_mgr.pending_order:
                self.ui_mgr.pending_order = None
            else:
                self.sound_mgr.play("click")
                self.state = STATE_GAMEPLAY
            return

        buttons = self.ui_mgr.draw_trading_terminal(self.virtual_surface, self, mouse_pos)
        sel_comp = self.market.get_company(self.ui_mgr.selected_symbol)
        cur_price = sel_comp.price if sel_comp else 100.0

        for action, btn in buttons:
            if btn.handle_event(event, mouse_pos):
                if action == "close":
                    self.state = STATE_GAMEPLAY
                elif action.startswith("select_"):
                    self.ui_mgr.selected_symbol = action.replace("select_", "")
                    self.ui_mgr.trade_qty = 1
                elif action.startswith("inspect_"):
                    self.ui_mgr.inspected_symbol = action.replace("inspect_", "")
                    self.state = STATE_COMPANY_DOSSIER
                elif action.startswith("breakdown_"):
                    self.ui_mgr.breakdown_symbol = action.replace("breakdown_", "")
                    self.state = STATE_RETURN_BREAKDOWN
                    self.story.on_action_triggered("view_breakdown", self)
                elif action.startswith("thesis_"):
                    self.ui_mgr.thesis_symbol = action.replace("thesis_", "")
                    self.state = STATE_INVESTMENT_THESIS
                    self.story.on_action_triggered("open_journal", self)
                elif action == "qty_minus":
                    self.ui_mgr.trade_qty = max(1, self.ui_mgr.trade_qty - 1)
                elif action == "qty_plus":
                    self.ui_mgr.trade_qty += 1
                elif action == "qty_plus10":
                    self.ui_mgr.trade_qty += 10
                elif action == "qty_max":
                    max_afford = int(self.portfolio.cash // cur_price) if cur_price > 0 else 1
                    owned = self.portfolio.get_shares_owned(self.ui_mgr.selected_symbol)
                    self.ui_mgr.trade_qty = max(1, max(max_afford, owned))
                elif action == "prompt_buy":
                    if not self.is_on_trading_floor():
                        self.sound_mgr.play("error")
                        self.ui_mgr.set_trade_message("⚠️ TRADING RESTRICTED: Orders can only be placed on an active Exchange Floor (BSE, NYSE, TSE, LSE).", is_error=True)
                        continue
                    tot = round(self.ui_mgr.trade_qty * cur_price, 2)
                    self.ui_mgr.pending_order = {
                        "action": "BUY",
                        "symbol": self.ui_mgr.selected_symbol,
                        "qty": self.ui_mgr.trade_qty,
                        "price": cur_price,
                        "total": tot
                    }
                elif action == "prompt_sell":
                    if not self.is_on_trading_floor():
                        self.sound_mgr.play("error")
                        self.ui_mgr.set_trade_message("⚠️ TRADING RESTRICTED: Orders can only be placed on an active Exchange Floor (BSE, NYSE, TSE, LSE).", is_error=True)
                        continue
                    tot = round(self.ui_mgr.trade_qty * cur_price, 2)
                    self.ui_mgr.pending_order = {
                        "action": "SELL",
                        "symbol": self.ui_mgr.selected_symbol,
                        "qty": self.ui_mgr.trade_qty,
                        "price": cur_price,
                        "total": tot
                    }
                elif action == "confirm_trade":
                    order = self.ui_mgr.pending_order
                    self.ui_mgr.pending_order = None
                    authorized = self.is_on_trading_floor()
                    if order["action"] == "BUY":
                        success, msg = self.portfolio.buy(order["symbol"], order["qty"], order["price"], day=self.market.day, authorized=authorized)
                        if success:
                            self.sound_mgr.play("buy")
                            self.add_xp(25, "Equity Purchase Order")
                            self.ui_mgr.set_trade_message(msg, is_error=False)
                            self.check_portfolio_missions()
                            adv = self.story.on_trade_executed(order["symbol"], order["qty"], order["price"], is_buy=True, game=self)
                            if adv:
                                self.mission_complete_banner = adv
                                self.mission_banner_timer = 4.0
                        else:
                            self.sound_mgr.play("error")
                            self.ui_mgr.set_trade_message(msg, is_error=True)
                    else:
                        success, msg, _ = self.portfolio.sell(order["symbol"], order["qty"], order["price"], day=self.market.day, authorized=authorized)
                        if success:
                            self.sound_mgr.play("sell")
                            self.add_xp(25, "Equity Liquidation Order")
                            self.ui_mgr.set_trade_message(msg, is_error=False)
                            self.check_portfolio_missions()
                            adv = self.story.on_trade_executed(order["symbol"], order["qty"], order["price"], is_buy=False, game=self)
                            if adv:
                                self.mission_complete_banner = adv
                                self.mission_banner_timer = 4.0
                        else:
                            self.sound_mgr.play("error")
                            self.ui_mgr.set_trade_message(msg, is_error=True)
                elif action == "cancel_trade":
                    self.ui_mgr.pending_order = None

    def _handle_portfolio_event(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_p):
            self.sound_mgr.play("click")
            self.state = STATE_GAMEPLAY
            return

        buttons = self.ui_mgr.draw_portfolio(self.virtual_surface, self, mouse_pos)
        for action, btn in buttons:
            if btn.handle_event(event, mouse_pos) and action == "close":
                self.state = STATE_GAMEPLAY

    def _handle_news_event(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_n):
            self.sound_mgr.play("click")
            self.state = STATE_GAMEPLAY
            return

        buttons = self.ui_mgr.draw_news_feed(self.virtual_surface, self, mouse_pos)
        for action, btn in buttons:
            if btn.handle_event(event, mouse_pos) and action == "close":
                self.state = STATE_GAMEPLAY

    def _handle_travel_event(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_m):
            self.sound_mgr.play("click")
            self.state = STATE_GAMEPLAY
            return

        buttons = self.ui_mgr.draw_travel_map(self.virtual_surface, self, mouse_pos)
        for action, btn in buttons:
            if btn.handle_event(event, mouse_pos):
                if action == "close":
                    self.state = STATE_GAMEPLAY
                elif action == "travel_wall_street":
                    self.sound_mgr.play("travel")
                    new_pos = self.world.set_location(LOCATION_WALL_STREET, "from_transit")
                    self.player.x, self.player.y = new_pos
                    self.player.exterior_map = LOCATION_WALL_STREET
                    self.player.exterior_pos = new_pos
                    self.state = STATE_GAMEPLAY
                elif action == "travel_dalal_street":
                    self.sound_mgr.play("travel")
                    new_pos = self.world.set_location(LOCATION_DALAL_STREET, "from_transit")
                    self.player.x, self.player.y = new_pos
                    self.player.exterior_map = LOCATION_DALAL_STREET
                    self.player.exterior_pos = new_pos
                    self.complete_mission("visit_mumbai")
                    self.state = STATE_GAMEPLAY
                elif action == "travel_kabutocho":
                    self.sound_mgr.play("travel")
                    new_pos = self.world.set_location(LOCATION_KABUTOCHO, "from_transit")
                    self.player.x, self.player.y = new_pos
                    self.player.exterior_map = LOCATION_KABUTOCHO
                    self.player.exterior_pos = new_pos
                    self.add_xp(100, "Tokyo Financial District Arrival")
                    self.state = STATE_GAMEPLAY
                elif action == "travel_london":
                    self.sound_mgr.play("travel")
                    new_pos = self.world.set_location(LOCATION_LONDON, "from_transit")
                    self.player.x, self.player.y = new_pos
                    self.player.exterior_map = LOCATION_LONDON
                    self.player.exterior_pos = new_pos
                    self.add_xp(100, "London Financial District Arrival")
                    self.state = STATE_GAMEPLAY

    def _handle_clue_journal_event(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_j):
            self.sound_mgr.play("click")
            self.state = STATE_GAMEPLAY
            return

        buttons = self.ui_mgr.draw_clue_journal(self.virtual_surface, self, mouse_pos)
        for action, btn in buttons:
            if btn.handle_event(event, mouse_pos):
                if action == "close":
                    self.state = STATE_GAMEPLAY
                elif action.startswith("tab_"):
                    self.investigation.selected_company = action.replace("tab_", "")

    def _handle_glossary_event(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_h):
            self.sound_mgr.play("click")
            self.state = STATE_GAMEPLAY
            return

        buttons = self.ui_mgr.draw_help_glossary(self.virtual_surface, mouse_pos)
        for action, btn in buttons:
            if btn.handle_event(event, mouse_pos) and action == "close":
                self.state = STATE_GAMEPLAY

    def _handle_exchange_hub_event(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.sound_mgr.play("click")
            self.state = STATE_GAMEPLAY
            return

        buttons = self.ui_mgr.draw_exchange_hub(self.virtual_surface, self, mouse_pos)
        for action, btn in buttons:
            if btn.handle_event(event, mouse_pos):
                if action == "close_hub":
                    self.state = STATE_GAMEPLAY
                elif action == "ff_open":
                    adv_msg = self.clock.advance_to_next_market_open(
                        EXCHANGE_NYSE if self.world.current_location_id == LOCATION_WALL_STREET else EXCHANGE_BSE
                    )
                    self.sound_mgr.play("fanfare")
                    self.mission_complete_banner = adv_msg
                    self.mission_banner_timer = 3.5
                    self.market.tick()
                elif action == "wait_hour":
                    self.clock.advance_time(60)
                    self.sound_mgr.play("click")
                    self.mission_complete_banner = "Advanced time by 1 hour."
                    self.mission_banner_timer = 2.5
                elif action == "toggle_mode":
                    new_mode = MODE_REALTIME if self.clock.mode == MODE_SIMULATION else MODE_SIMULATION
                    self.clock.set_mode(new_mode)
                    self.sound_mgr.play("click")

    def _handle_company_dossier_event(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.sound_mgr.play("click")
            self.state = STATE_GAMEPLAY
            return

        buttons = self.ui_mgr.draw_company_dossier(self.virtual_surface, self, mouse_pos)
        for action, btn in buttons:
            if btn.handle_event(event, mouse_pos):
                if action == "close_dossier":
                    self.state = STATE_GAMEPLAY
                elif action.startswith("open_terminal_"):
                    sym = action.replace("open_terminal_", "")
                    self.ui_mgr.selected_symbol = sym
                    self.state = STATE_TRADING

    def _handle_bank_event(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.sound_mgr.play("click")
            self.state = STATE_GAMEPLAY
            return

        buttons = self.ui_mgr.draw_bank_modal(self.virtual_surface, self, mouse_pos)
        for action, btn in buttons:
            if btn.handle_event(event, mouse_pos) and action == "close_bank":
                self.state = STATE_GAMEPLAY

    def _handle_academy_event(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.sound_mgr.play("click")
            self.state = STATE_GAMEPLAY
            return

        buttons = self.ui_mgr.draw_academy_modal(self.virtual_surface, self, mouse_pos)
        for action, btn in buttons:
            if btn.handle_event(event, mouse_pos) and action == "close_academy":
                self.state = STATE_GAMEPLAY

    def _handle_bull_event(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.sound_mgr.play("click")
            self.state = STATE_GAMEPLAY
            return

        buttons = self.ui_mgr.draw_bull_modal(self.virtual_surface, self, mouse_pos)
        for action, btn in buttons:
            if btn.handle_event(event, mouse_pos):
                if action == "close_bull":
                    self.state = STATE_GAMEPLAY
                elif action == "rub_bull_horns":
                    self.sound_mgr.play("fanfare")
                    self.portfolio.cash = round(self.portfolio.cash + 100.0, 2)
                    if "Bull Believer" not in self.badges:
                        self.badges.append("Bull Believer")
                    self.mission_complete_banner = "Rubbed the Bull's Horns! (+ $100 Lucky Grant, 'Bull Believer' Badge)"
                    self.mission_banner_timer = 4.0
                    self.state = STATE_GAMEPLAY

    def _handle_banyan_event(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.sound_mgr.play("click")
            self.state = STATE_GAMEPLAY
            return

        buttons = self.ui_mgr.draw_banyan_modal(self.virtual_surface, self, mouse_pos)
        for action, btn in buttons:
            if btn.handle_event(event, mouse_pos) and action == "close_banyan":
                self.state = STATE_GAMEPLAY

    def _handle_chai_event(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.sound_mgr.play("click")
            self.state = STATE_GAMEPLAY
            return

        buttons = self.ui_mgr.draw_chai_modal(self.virtual_surface, self, mouse_pos)
        for action, btn in buttons:
            if btn.handle_event(event, mouse_pos) and action == "close_chai":
                self.state = STATE_GAMEPLAY

    def _handle_pause_event(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.sound_mgr.play("click")
            self.state = STATE_GAMEPLAY
            return

        buttons = self.ui_mgr.draw_pause_menu(self.virtual_surface, mouse_pos)
        for action, btn in buttons:
            if btn.handle_event(event, mouse_pos):
                if action == "resume":
                    self.state = STATE_GAMEPLAY
                elif action == "save":
                    ok, _ = self.save_current_game()
                    if ok:
                        self.sound_mgr.play("fanfare")
                        self.mission_complete_banner = "GAME SAVED SUCCESSFULLY!"
                        self.mission_banner_timer = 3.0
                    else:
                        self.sound_mgr.play("error")
                    self.state = STATE_GAMEPLAY
                elif action == "settings":
                    self.previous_state = STATE_PAUSE
                    self.state = STATE_SETTINGS
                elif action == "title":
                    self.state = STATE_TITLE

    def _handle_settings_event(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.sound_mgr.play("click")
            self.state = self.previous_state
            return

        buttons = self.ui_mgr.draw_settings_menu(self.virtual_surface, mouse_pos, self.sound_mgr)
        for action, btn in buttons:
            if btn.handle_event(event, mouse_pos):
                if action == "back":
                    self.state = self.previous_state
                elif action == "vol_down":
                    self.sound_mgr.set_volume(self.sound_mgr.sfx_volume - 0.1)
                    self.sound_mgr.play("click")
                elif action == "vol_up":
                    self.sound_mgr.set_volume(self.sound_mgr.sfx_volume + 0.1)
                    self.sound_mgr.play("click")
                elif action == "vol_mute":
                    new_v = 0.0 if self.sound_mgr.sfx_volume > 0 else 0.7
                    self.sound_mgr.set_volume(new_v)
                    self.sound_mgr.play("click")

    def _handle_return_breakdown_event(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_b):
            self.sound_mgr.play("click")
            self.state = STATE_GAMEPLAY
            return

        buttons = self.ui_mgr.draw_return_breakdown(self.virtual_surface, self, mouse_pos)
        for action, btn in buttons:
            if btn.handle_event(event, mouse_pos):
                if action == "close":
                    self.state = STATE_GAMEPLAY
                elif action.startswith("breakdown_tab_"):
                    self.ui_mgr.breakdown_symbol = action.replace("breakdown_tab_", "")
                    self.sound_mgr.play("click")
                elif action.startswith("layer_"):
                    self.ui_mgr.education_layer = int(action.replace("layer_", ""))
                    self.sound_mgr.play("click")

    def _handle_campaign_event(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_c):
            self.sound_mgr.play("click")
            self.state = STATE_GAMEPLAY
            return

        buttons = self.ui_mgr.draw_campaign_progress(self.virtual_surface, self, mouse_pos)
        for action, btn in buttons:
            if btn.handle_event(event, mouse_pos):
                if action == "close":
                    self.state = STATE_GAMEPLAY
                elif action.startswith("sel_chapter_"):
                    self.ui_mgr.campaign_selected_chapter = int(action.replace("sel_chapter_", ""))
                    self.sound_mgr.play("click")
                elif action == "toggle_guidance":
                    self.player.route_guidance_active = not getattr(self.player, "route_guidance_active", True)
                    self.sound_mgr.play("click")

    def _handle_investment_thesis_event(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_j):
            self.sound_mgr.play("click")
            self.state = STATE_GAMEPLAY
            return

        buttons = self.ui_mgr.draw_investment_thesis(self.virtual_surface, self, mouse_pos)
        for action, btn in buttons:
            if btn.handle_event(event, mouse_pos):
                if action == "close":
                    self.state = STATE_GAMEPLAY
                elif action.startswith("thesis_tab_"):
                    self.ui_mgr.thesis_symbol = action.replace("thesis_tab_", "")
                    self.sound_mgr.play("click")
                elif action.startswith("size_"):
                    self.ui_mgr.thesis_size_pct = float(action.replace("size_", ""))
                    self.sound_mgr.play("click")
                elif action.startswith("horizon_"):
                    self.ui_mgr.thesis_horizon = action.replace("horizon_", "")
                    self.sound_mgr.play("click")
                elif action == "record_thesis":
                    sym = self.ui_mgr.thesis_symbol
                    comp = self.market.get_company(sym)
                    entry_p = comp.price if comp else 100.0
                    rating_lbl, summary = self.investigation.get_thesis_rating(sym)
                    clues = [c.title for c in self.investigation.get_clues_for_company(sym)]

                    new_thesis = InvestmentThesis(
                        company_symbol=sym,
                        rationale=summary,
                        evidence_clues=clues,
                        catalysts=comp.growth_drivers if comp else "Expansion catalyst",
                        risks=comp.risks if comp else "Market volatility",
                        confidence_level=rating_lbl,
                        holding_period=self.ui_mgr.thesis_horizon,
                        position_size_pct=self.ui_mgr.thesis_size_pct,
                        entry_price=entry_p,
                        entry_step=self.market.day
                    )
                    self.investigation.record_thesis(new_thesis)
                    self.add_xp(100, f"Investment Thesis: {sym}")
                    self.sound_mgr.play("fanfare")
                    self.mission_complete_banner = f"INVESTMENT THESIS RECORDED: {sym} (+100 XP)"
                    self.mission_banner_timer = 4.0
                    adv = self.story.on_action_triggered("submit_master_thesis", self)
                    if adv:
                        self.mission_complete_banner = adv

    def _handle_interior_map_event(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_m):
                self.sound_mgr.play("click")
                self.state = STATE_GAMEPLAY
                return
            elif event.key in (pygame.K_r, pygame.K_g):
                self.player.route_guidance_active = not getattr(self.player, "route_guidance_active", True)
                self.sound_mgr.play("click")
                return

        buttons = self.ui_mgr.draw_interior_map(self.virtual_surface, self, mouse_pos)
        for action, btn in buttons:
            if btn.handle_event(event, mouse_pos):
                if action == "close":
                    self.sound_mgr.play("click")
                    self.state = STATE_GAMEPLAY

    # -------------------------------------------------------------
    # UPDATE LOOP
    # -------------------------------------------------------------
    def update(self, dt: float):
        self.global_ticks += 1
        self.ui_mgr.update(dt)
        self.clock.update(dt)

        # Check for exchange transition notifications
        while self.clock.pending_notifications:
            notif = self.clock.pending_notifications.pop(0)
            self.ui_mgr.trigger_news_toast({
                "headline": notif["title"],
                "explanation": notif["text"],
                "category": "SCHEDULE",
                "impact_str": "MARKET BELL",
                "target": "ALL"
            })
            self.sound_mgr.play("fanfare")

        if self.mission_banner_timer > 0:
            self.mission_banner_timer -= dt

        if self.state == STATE_GAMEPLAY:
            keys = pygame.key.get_pressed()
            self.player.update(dt, keys, self.world)
            self.world.update_camera(
                self.player.x + self.player.width / 2,
                self.player.y + self.player.height / 2
            )

            # Route guidance calculation to current story objective
            if getattr(self.player, "route_guidance_active", True):
                self.player.route_pulse_timer = (getattr(self.player, "route_pulse_timer", 0.0) + dt) % 10.0
                self.route_recalc_timer += dt
                if self.route_recalc_timer >= 0.5:
                    self.route_recalc_timer = 0.0
                    active_obj = self.story.get_active_objective()
                    if active_obj:
                        target_pos = None
                        target_map = active_obj.get("target_map", "")
                        if target_map == self.world.current_location_id:
                            target_npc = active_obj.get("target_npc", "")
                            target_obj_id = active_obj.get("target_object", "")
                            if target_npc:
                                for npc in self.world.current_map.npcs:
                                    if npc.id.lower() == target_npc.lower():
                                        target_pos = (npc.x + 8, npc.y + 12)
                                        break
                            elif target_obj_id:
                                for obj in self.world.current_map.objects:
                                    if obj.id.lower() == target_obj_id.lower():
                                        target_pos = (obj.x + obj.w / 2, obj.y + obj.h / 2)
                                        break
                            if not target_pos and "target_pos" in active_obj:
                                target_pos = tuple(active_obj["target_pos"])
                        else:
                            for obj in self.world.current_map.objects:
                                if obj.target_interior == target_map or obj.target_loc == target_map:
                                    target_pos = (obj.x + obj.w / 2, obj.y + obj.h / 2)
                                    break
                                if obj.action_type == "exit_interior":
                                    target_pos = (obj.x + obj.w / 2, obj.y + obj.h / 2)
                                    break
                                if obj.action_type == "transit":
                                    target_pos = (obj.x + obj.w / 2, obj.y + obj.h / 2)
                                    break

                        if target_pos:
                            start_pt = (self.player.x + 8, self.player.y + 12)
                            self.player.current_route = self.world.calculate_route(start_pt, target_pos)
                        else:
                            self.player.current_route = []
                    else:
                        self.player.current_route = []

            self.tick_timer += dt
            if self.tick_timer >= MARKET_TICK_SECONDS:
                self.tick_timer = 0.0
                self.market.tick()
                if self.market.rng.random() < 0.20:
                    ev_item = self.market.trigger_random_event()
                    if ev_item:
                        self.ui_mgr.trigger_news_toast(ev_item)

        elif self.state == STATE_DIALOGUE:
            self.dialogue_mgr.update(dt)

    # -------------------------------------------------------------
    # RENDER PIPELINE
    # -------------------------------------------------------------
    def draw(self):
        mouse_raw = pygame.mouse.get_pos()
        mouse_pos = (int(mouse_raw[0] / self.window_scale), int(mouse_raw[1] / self.window_scale))

        if self.state == STATE_TITLE:
            has_save = self.save_mgr.has_save()
            self.ui_mgr.draw_title_screen(self.virtual_surface, mouse_pos, has_save, self.global_ticks)

        elif self.state == STATE_GAMEPLAY:
            self.virtual_surface.fill(COLOR_BG_DARK)
            self.world.draw(self.virtual_surface, self.font, self.small_font, self.player, self.global_ticks)
            self.ui_mgr.draw_hud(self.virtual_surface, self)

            if self.mission_banner_timer > 0 and self.mission_complete_banner:
                b_surf = self.font.render(self.mission_complete_banner, True, COLOR_TEXT_GOLD)
                b_rect = pygame.Rect(0, 0, b_surf.get_width() + 16, 24)
                b_rect.center = (VIRTUAL_WIDTH // 2, 44)
                pygame.draw.rect(self.virtual_surface, (12, 18, 38), b_rect, border_radius=4)
                pygame.draw.rect(self.virtual_surface, COLOR_TEXT_GOLD, b_rect, width=1, border_radius=4)
                self.virtual_surface.blit(b_surf, (b_rect.x + 8, b_rect.y + 4))

        elif self.state == STATE_DIALOGUE:
            self.virtual_surface.fill(COLOR_BG_DARK)
            self.world.draw(self.virtual_surface, self.font, self.small_font, self.player, self.global_ticks)
            self.ui_mgr.draw_hud(self.virtual_surface, self)
            self.dialogue_mgr.draw(self.virtual_surface, VIRTUAL_WIDTH, VIRTUAL_HEIGHT)

        elif self.state == STATE_TRADING:
            self.ui_mgr.draw_trading_terminal(self.virtual_surface, self, mouse_pos)

        elif self.state == STATE_PORTFOLIO:
            self.ui_mgr.draw_portfolio(self.virtual_surface, self, mouse_pos)

        elif self.state == STATE_CLUE_JOURNAL:
            self.ui_mgr.draw_clue_journal(self.virtual_surface, self, mouse_pos)

        elif self.state == STATE_NEWS:
            self.ui_mgr.draw_news_feed(self.virtual_surface, self, mouse_pos)

        elif self.state == STATE_TRAVEL:
            self.ui_mgr.draw_travel_map(self.virtual_surface, self, mouse_pos)

        elif self.state == STATE_GLOSSARY:
            self.ui_mgr.draw_help_glossary(self.virtual_surface, mouse_pos)

        elif self.state == STATE_EXCHANGE_HUB:
            self.world.draw(self.virtual_surface, self.font, self.small_font, self.player, self.global_ticks)
            self.ui_mgr.draw_hud(self.virtual_surface, self)
            self.ui_mgr.draw_exchange_hub(self.virtual_surface, self, mouse_pos)

        elif self.state == STATE_COMPANY_DOSSIER:
            self.world.draw(self.virtual_surface, self.font, self.small_font, self.player, self.global_ticks)
            self.ui_mgr.draw_hud(self.virtual_surface, self)
            self.ui_mgr.draw_company_dossier(self.virtual_surface, self, mouse_pos)

        elif self.state == STATE_BANK:
            self.world.draw(self.virtual_surface, self.font, self.small_font, self.player, self.global_ticks)
            self.ui_mgr.draw_hud(self.virtual_surface, self)
            self.ui_mgr.draw_bank_modal(self.virtual_surface, self, mouse_pos)

        elif self.state == STATE_ACADEMY:
            self.world.draw(self.virtual_surface, self.font, self.small_font, self.player, self.global_ticks)
            self.ui_mgr.draw_hud(self.virtual_surface, self)
            self.ui_mgr.draw_academy_modal(self.virtual_surface, self, mouse_pos)

        elif self.state == STATE_BULL_MODAL:
            self.world.draw(self.virtual_surface, self.font, self.small_font, self.player, self.global_ticks)
            self.ui_mgr.draw_hud(self.virtual_surface, self)
            self.ui_mgr.draw_bull_modal(self.virtual_surface, self, mouse_pos)

        elif self.state == STATE_BANYAN_MODAL:
            self.world.draw(self.virtual_surface, self.font, self.small_font, self.player, self.global_ticks)
            self.ui_mgr.draw_hud(self.virtual_surface, self)
            self.ui_mgr.draw_banyan_modal(self.virtual_surface, self, mouse_pos)

        elif self.state == STATE_CHAI_MODAL:
            self.world.draw(self.virtual_surface, self.font, self.small_font, self.player, self.global_ticks)
            self.ui_mgr.draw_hud(self.virtual_surface, self)
            self.ui_mgr.draw_chai_modal(self.virtual_surface, self, mouse_pos)

        elif self.state == STATE_RETURN_BREAKDOWN:
            self.ui_mgr.draw_return_breakdown(self.virtual_surface, self, mouse_pos)

        elif self.state == STATE_CAMPAIGN:
            self.ui_mgr.draw_campaign_progress(self.virtual_surface, self, mouse_pos)

        elif self.state == STATE_INVESTMENT_THESIS:
            self.ui_mgr.draw_investment_thesis(self.virtual_surface, self, mouse_pos)

        elif self.state == STATE_INTERIOR_MAP:
            self.ui_mgr.draw_interior_map(self.virtual_surface, self, mouse_pos)

        elif self.state == STATE_PAUSE:
            self.world.draw(self.virtual_surface, self.font, self.small_font, self.player, self.global_ticks)
            self.ui_mgr.draw_hud(self.virtual_surface, self)
            self.ui_mgr.draw_pause_menu(self.virtual_surface, mouse_pos)

        elif self.state == STATE_SETTINGS:
            self.ui_mgr.draw_settings_menu(self.virtual_surface, mouse_pos, self.sound_mgr)

        if self.ui_mgr.show_tutorial:
            self.ui_mgr.draw_tutorial_modal(self.virtual_surface, mouse_pos)

        pygame.transform.scale(self.virtual_surface, self.screen.get_size(), self.screen)
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock_fps.tick(60) / 1000.0
            dt = min(0.05, dt)
            self.handle_events()
            self.update(dt)
            self.draw()
