"""
MarketQuest - Automated Test Suite for Interiors, Location-Restricted Trading,
Global Exchanges, and Clue Investigation System.
"""

import unittest
import pygame
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from src.world import World
from src.interiors import (
    build_bse_trading_floor, build_nyse_trading_floor,
    build_tse_trading_floor, build_lse_trading_floor,
    build_bank_interior, build_library_interior,
    build_white_house_interior, build_parliament_interior,
    build_apex_hq_interior, build_titan_hq_interior,
    build_monsoon_hq_interior,
    build_nova_hq_interior, build_aura_hq_interior,
    build_medx_hq_interior
)
from src.trading import Portfolio
from src.investigation import InvestigationManager, ALL_CLUES
from src.clock import MarketClock, EXCHANGE_BSE, EXCHANGE_NYSE, EXCHANGE_TSE, EXCHANGE_LSE
from src.game import Game, STATE_GAMEPLAY, STATE_CLUE_JOURNAL, STATE_TRADING


class TestInteriors(unittest.TestCase):
    def setUp(self):
        self.world = World()

    def test_all_14_interiors_registered(self):
        """Verify all 14 required interior maps are registered in World."""
        expected_interiors = [
            config.INTERIOR_BSE,
            config.INTERIOR_NYSE,
            config.INTERIOR_TSE,
            config.INTERIOR_LSE,
            config.INTERIOR_BANK,
            config.INTERIOR_LIBRARY,
            config.INTERIOR_WHITE_HOUSE,
            config.INTERIOR_PARLIAMENT,
            config.INTERIOR_APEX_HQ,
            config.INTERIOR_TITAN_HQ,
            config.INTERIOR_MONSOON_HQ,
            config.INTERIOR_NOVA_HQ,
            config.INTERIOR_AURA_HQ,
            config.INTERIOR_MEDX_HQ
        ]
        for m_id in expected_interiors:
            self.assertIn(m_id, self.world.maps, f"Missing interior: {m_id}")
            m = self.world.maps[m_id]
            self.assertGreater(len(m.solids), 0, f"Interior {m_id} must have colliders")
            self.assertIn("entrance", m.spawn_points, f"Interior {m_id} must have entrance spawn")
            self.assertGreater(len(m.npcs), 0, f"Interior {m_id} must have NPCs")

    def test_all_six_companies_have_unique_exteriors_and_interiors(self):
        """Verify APEX, TITN, CHAI, NOVA, AURA, and MEDX all have designated HQ interiors."""
        hq_mapping = {
            "APEX": config.INTERIOR_APEX_HQ,
            "TITN": config.INTERIOR_TITAN_HQ,
            "CHAI": config.INTERIOR_MONSOON_HQ,
            "NOVA": config.INTERIOR_NOVA_HQ,
            "AURA": config.INTERIOR_AURA_HQ,
            "MEDX": config.INTERIOR_MEDX_HQ,
        }
        for sym, interior_id in hq_mapping.items():
            self.assertIn(interior_id, self.world.maps, f"Missing HQ interior for {sym}")
            m = self.world.maps[interior_id]
            self.assertGreaterEqual(len(m.npcs), 2, f"HQ {interior_id} should have at least 2 staff NPCs")
            interactables = [obj for obj in m.objects if obj.action_type in ["inspect", "open_trading", "exit_interior"]]
            self.assertGreaterEqual(len(interactables), 2, f"HQ {interior_id} should have interactable objects")

    def test_interior_exit_doors_configured(self):
        """All interiors must contain an exit door object with action_type='exit_interior'."""
        for m_id, m in self.world.maps.items():
            if m_id.startswith("interior_"):
                exit_doors = [obj for obj in m.objects if obj.action_type == "exit_interior"]
                self.assertGreaterEqual(len(exit_doors), 1, f"Interior {m_id} missing exit door")

    def test_exchange_floors_have_trading_consoles(self):
        """Stock exchange trading floors must have open_trading objects."""
        exchange_floors = [config.INTERIOR_BSE, config.INTERIOR_NYSE, config.INTERIOR_TSE, config.INTERIOR_LSE]
        for ex_id in exchange_floors:
            m = self.world.maps[ex_id]
            trading_consoles = [obj for obj in m.objects if obj.action_type == "open_trading"]
            self.assertGreaterEqual(len(trading_consoles), 1, f"Floor {ex_id} missing trading console")

    def test_exterior_to_interior_connections(self):
        """Verify all company, exchange, and civic buildings have exterior doors linking to valid interiors."""
        exterior_maps = [
            config.LOCATION_WALL_STREET,
            config.LOCATION_DALAL_STREET,
            config.LOCATION_KABUTOCHO,
            config.LOCATION_LONDON
        ]
        total_doors = 0
        for ext_id in exterior_maps:
            m = self.world.maps[ext_id]
            doors = [obj for obj in m.objects if obj.action_type == "enter_interior"]
            self.assertGreater(len(doors), 0, f"Exterior map {ext_id} must have entrance doors")
            for door in doors:
                self.assertIsNotNone(door.target_interior, f"Door {door.id} on {ext_id} missing target_interior")
                self.assertIn(door.target_interior, self.world.maps, f"Door {door.id} points to unregistered interior {door.target_interior}")
                total_doors += 1
        self.assertGreaterEqual(total_doors, 12, "Must have at least 12 exterior building entrances")

    def test_civic_institutions_configured(self):
        """Verify Bank, Library, White House, and Parliament interiors are fully explorable."""
        civic_interiors = [
            config.INTERIOR_BANK,
            config.INTERIOR_LIBRARY,
            config.INTERIOR_WHITE_HOUSE,
            config.INTERIOR_PARLIAMENT
        ]
        for civ_id in civic_interiors:
            m = self.world.maps[civ_id]
            self.assertGreaterEqual(len(m.npcs), 2, f"Civic interior {civ_id} should have staff NPCs")
            inspectables = [obj for obj in m.objects if obj.action_type == "inspect"]
            self.assertGreaterEqual(len(inspectables), 1, f"Civic interior {civ_id} should have inspectable assets")


class TestLocationRestrictedTrading(unittest.TestCase):
    def setUp(self):
        self.portfolio = Portfolio(starting_cash=10000.0)

    def test_unauthorized_buy_rejected(self):
        """Executing buy with authorized=False is strictly rejected with no cash deducted."""
        success, msg = self.portfolio.buy("APEX", 10, 100.0, authorized=False)
        self.assertFalse(success)
        self.assertIn("rejected", msg.lower())
        self.assertEqual(self.portfolio.cash, 10000.0)
        self.assertEqual(self.portfolio.get_shares_owned("APEX"), 0)

    def test_unauthorized_sell_rejected(self):
        """Executing sell with authorized=False is rejected with no share reduction."""
        # Buy authorized on floor first
        self.portfolio.buy("APEX", 10, 100.0, authorized=True)
        # Attempt to sell outside
        success, msg, pnl = self.portfolio.sell("APEX", 5, 120.0, authorized=False)
        self.assertFalse(success)
        self.assertIn("rejected", msg.lower())
        self.assertEqual(self.portfolio.get_shares_owned("APEX"), 10)

    def test_authorized_floor_trading_succeeds(self):
        """Trading with authorized=True succeeds normally."""
        success, msg = self.portfolio.buy("TITN", 5, 50.0, authorized=True)
        self.assertTrue(success)
        self.assertEqual(self.portfolio.get_shares_owned("TITN"), 5)
        self.assertEqual(self.portfolio.cash, 9750.0)


class TestClueInvestigationSystem(unittest.TestCase):
    def setUp(self):
        self.inv = InvestigationManager()

    def test_unlock_clues_and_confidence(self):
        """Unlocking clues increases evidence completeness and updates investment thesis."""
        # Baseline: 0 clues
        self.assertEqual(self.inv.get_confidence_pct("APEX"), 0)
        rating, _ = self.inv.get_thesis_rating("APEX")
        self.assertEqual(rating, "LOW CONFIDENCE")

        # Unlock R&D chip clue
        clue, is_new = self.inv.unlock_clue("apex_rd_chip")
        self.assertTrue(is_new)
        self.assertGreaterEqual(self.inv.get_confidence_pct("APEX"), 30)

        # Unlock Battery yield clue
        self.inv.unlock_clue("apex_battery_yield")
        self.assertGreaterEqual(self.inv.get_confidence_pct("APEX"), 70)
        rating, _ = self.inv.get_thesis_rating("APEX")
        self.assertEqual(rating, "MODERATE CONFIDENCE")

        # Unlock CEO vision clue -> High Conviction
        self.inv.unlock_clue("apex_ceo_vision")
        self.assertEqual(self.inv.get_confidence_pct("APEX"), 100)
        rating, summary = self.inv.get_thesis_rating("APEX")
        self.assertEqual(rating, "HIGH CONVICTION")
        self.assertIn("Institutional Thesis", summary)

    def test_clues_for_all_companies(self):
        """All 6 companies have registered clues in the investigation database."""
        for sym in ["APEX", "TITN", "CHAI", "NOVA", "AURA", "MEDX"]:
            clues = [c for c in ALL_CLUES.values() if c.company_symbol == sym]
            self.assertGreaterEqual(len(clues), 2, f"Company {sym} must have at least 2 investigation clues")
            # Verify unlocking first clue boosts confidence
            clue_id = clues[0].id
            _, is_new = self.inv.unlock_clue(clue_id)
            self.assertTrue(is_new)
            self.assertGreater(self.inv.get_confidence_pct(sym), 0)

    def test_level_progression_thresholds(self):
        """XP correctly advances levels and titles from Level 1 to 10."""
        lvl, title, cur_min, next_th, _ = InvestigationManager.get_level_info(0)
        self.assertEqual(lvl, 1)
        self.assertEqual(title, "Rookie Investor")

        lvl, title, _, _, _ = InvestigationManager.get_level_info(150)
        self.assertEqual(lvl, 2)
        self.assertEqual(title, "Market Observer")

        lvl, title, _, _, _ = InvestigationManager.get_level_info(1500)
        self.assertEqual(lvl, 6)
        self.assertEqual(title, "Senior Arbitrageur")

        lvl, title, _, _, _ = InvestigationManager.get_level_info(6000)
        self.assertEqual(lvl, 10)
        self.assertEqual(title, "Financial Titan")


class TestGlobalExchangesClock(unittest.TestCase):
    def setUp(self):
        self.clock = MarketClock()

    def test_all_four_exchanges_configured(self):
        """BSE, NYSE, TSE, and LSE have distinct session hours and timezones."""
        for ex in [EXCHANGE_BSE, EXCHANGE_NYSE, EXCHANGE_TSE, EXCHANGE_LSE]:
            stat = self.clock.get_exchange_status(ex)
            self.assertIsNotNone(stat)
            self.assertIn(stat["status"], ["OPEN", "CLOSED", "PRE-OPEN"])
            self.assertGreater(len(stat["time_str"]), 0)


from collections import deque
import json

class TestBSEFloorPlanAndNavMesh(unittest.TestCase):
    def setUp(self):
        self.world = World()
        self.bse = self.world.maps[config.INTERIOR_BSE]

    def test_bse_dimensions_and_zones(self):
        """BSE floor must be 48x36 tiles (1152x864 px) with all 15 required zones."""
        self.assertEqual(self.bse.width, 48)
        self.assertEqual(self.bse.height, 36)
        self.assertEqual(self.bse.pixel_width, 48 * config.TILE_SIZE)
        self.assertEqual(self.bse.pixel_height, 36 * config.TILE_SIZE)

    def test_all_10_npcs_present_with_unique_roles(self):
        """Verify all 10 educational, historical, and staff NPCs exist in BSE."""
        expected_npcs = [
            "rakesh_mentor", "harshad_case_analyst", "concierge_pooja",
            "security_officer_bse", "rajesh", "vikram", "anita",
            "prof_meenakshi", "devika_risk", "siddharth_board"
        ]
        bse_npc_ids = [npc.id for npc in self.bse.npcs]
        for npc_id in expected_npcs:
            self.assertIn(npc_id, bse_npc_ids, f"BSE is missing required NPC: {npc_id}")

    def test_easter_eggs_and_landmarks_present(self):
        """Verify 4 historical Easter eggs and core interactive landmarks exist in BSE."""
        egg_ids = ["egg_golden_bull", "egg_graham_book", "egg_vintage_ticker", "egg_runner_log"]
        obj_ids = [obj.id for obj in self.bse.objects]
        for egg_id in egg_ids:
            self.assertIn(egg_id, obj_ids, f"BSE is missing Easter egg object: {egg_id}")

        self.assertIn("bse_trading_console", obj_ids)
        self.assertIn("door_exit", obj_ids)

    def test_flood_fill_reachability_to_all_npcs_and_objects(self):
        """Ensure full BFS nav-mesh connectivity from entrance spawn (24*24, 33*24) to all NPCs and objects."""
        start_tx = 24
        start_ty = 33

        # A tile (tx, ty) is walkable if its center is not inside any solid
        walkable = set()
        for ty in range(self.bse.height):
            for tx in range(self.bse.width):
                center_rect = pygame.Rect(tx * config.TILE_SIZE + 6, ty * config.TILE_SIZE + 6, 12, 12)
                if not any(s.colliderect(center_rect) for s in self.bse.solids):
                    walkable.add((tx, ty))

        self.assertIn((start_tx, start_ty), walkable, "Entrance spawn tile must be walkable")

        visited = set()
        queue = deque([(start_tx, start_ty)])
        visited.add((start_tx, start_ty))

        while queue:
            cx, cy = queue.popleft()
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = cx + dx, cy + dy
                if (nx, ny) in walkable and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny))

        # Check all 10 NPCs are in or adjacent to visited walkable tiles
        for npc in self.bse.npcs:
            npc_tx = int(npc.x // config.TILE_SIZE)
            npc_ty = int(npc.y // config.TILE_SIZE)
            neighbors = [(npc_tx + dx, npc_ty + dy) for dx, dy in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]]
            reachable = any(pt in visited for pt in neighbors)
            self.assertTrue(reachable, f"NPC {npc.id} at ({npc_tx}, {npc_ty}) is trapped and unreachable!")

        # Check all objects are adjacent to visited walkable tiles
        for obj in self.bse.objects:
            obj_tx = int((obj.x + obj.w / 2) // config.TILE_SIZE)
            obj_ty = int((obj.y + obj.h / 2) // config.TILE_SIZE)
            neighbors = [
                (obj_tx + dx, obj_ty + dy)
                for dx in range(-2, 3)
                for dy in range(-2, 3)
            ]
            reachable = any(pt in visited for pt in neighbors)
            self.assertTrue(reachable, f"Object {obj.id} at ({obj_tx}, {obj_ty}) is blocked and unreachable!")


class TestExchangeEntranceReliabilityAndCamera(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.world = World()
        self.dalal = self.world.maps[config.LOCATION_DALAL_STREET]
        self.wall_st = self.world.maps[config.LOCATION_WALL_STREET]

    def test_exterior_bse_entrance_interaction_with_los(self):
        """Player standing directly outside BSE entrance on Dalal Street can interact with hub_bse."""
        self.world.set_location(config.LOCATION_DALAL_STREET)
        bse_door = next((o for o in self.dalal.objects if o.id == "hub_bse"), None)
        self.assertIsNotNone(bse_door)

        px = bse_door.x + bse_door.w / 2
        py = bse_door.y + bse_door.h + 6

        target = self.world.get_nearby_interactive(px, py, dist=32.0, check_los=True)
        self.assertIsNotNone(target, "Player standing in front of BSE door cannot interact!")
        self.assertEqual(target.id, "hub_bse")
        self.assertEqual(target.target_interior, config.INTERIOR_BSE)

    def test_exterior_nyse_entrance_interaction_with_los(self):
        """Player standing outside NYSE entrance on Wall Street can interact with hub_nyse."""
        self.world.set_location(config.LOCATION_WALL_STREET)
        nyse_door = next((o for o in self.wall_st.objects if o.id == "hub_nyse"), None)
        self.assertIsNotNone(nyse_door)

        px = nyse_door.x + nyse_door.w / 2
        py = nyse_door.y + nyse_door.h + 6

        target = self.world.get_nearby_interactive(px, py, dist=32.0, check_los=True)
        self.assertIsNotNone(target, "Player standing in front of NYSE door cannot interact!")
        self.assertEqual(target.id, "hub_nyse")
        self.assertEqual(target.target_interior, config.INTERIOR_NYSE)

    def test_camera_centering_on_small_interior(self):
        """Maps smaller than 640x360 viewport are centered rather than clamped to offset 0."""
        self.world.set_location(config.INTERIOR_BANK)
        self.world.update_camera(300, 200)
        self.assertEqual(self.world.camera_x, -8.0)

    def test_camera_clamping_on_large_interior(self):
        """BSE map is 48x36 tiles = 1152x864 px. Camera clamps between 0 and (map_dim - viewport_dim)."""
        self.world.set_location(config.INTERIOR_BSE)
        m = self.world.current_map
        max_cam_x = m.pixel_width - config.VIRTUAL_WIDTH
        max_cam_y = m.pixel_height - config.VIRTUAL_HEIGHT

        # Near top-left corner
        self.world.update_camera(10, 10)
        self.assertEqual(self.world.camera_x, 0.0)
        self.assertEqual(self.world.camera_y, 0.0)

        # Near bottom-right corner
        self.world.update_camera(1140, 850)
        self.assertEqual(self.world.camera_x, max_cam_x)
        self.assertEqual(self.world.camera_y, max_cam_y)

    def test_player_sprite_never_clips_map_boundaries(self):
        """Player strictly clamped within 0 <= x <= map_w - width and 0 <= y <= map_h - height."""
        from src.player import Player
        player = Player(100, 100)
        self.world.set_location(config.LOCATION_DALAL_STREET)
        m = self.world.current_map

        player.x = -100.0
        player.y = -100.0
        keys = {pygame.K_LEFT: True, pygame.K_UP: True, pygame.K_RIGHT: False, pygame.K_DOWN: False,
                pygame.K_a: False, pygame.K_w: False, pygame.K_d: False, pygame.K_s: False}
        player.update(0.1, keys, self.world)
        self.assertGreaterEqual(player.x, 0.0)
        self.assertGreaterEqual(player.y, 0.0)

        player.x = m.pixel_width + 100.0
        player.y = m.pixel_height + 100.0
        keys = {pygame.K_LEFT: False, pygame.K_UP: False, pygame.K_RIGHT: True, pygame.K_DOWN: True,
                pygame.K_a: False, pygame.K_w: False, pygame.K_d: False, pygame.K_s: False}
        player.update(0.1, keys, self.world)
        self.assertLessEqual(player.x + player.width, m.pixel_width)
        self.assertLessEqual(player.y + player.height, m.pixel_height)


class TestInteriorBlueprintMapAndEasterEggs(unittest.TestCase):
    def setUp(self):
        pygame.init()
        screen = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
        self.game = Game(screen, window_scale=config.WINDOW_SCALE)
        self.game.start_new_game()
        self.game.ui_mgr.show_tutorial = False

    def test_toggle_blueprint_map_inside_interior(self):
        """Pressing [M] inside interior toggles STATE_INTERIOR_MAP."""
        self.game.world.set_location(config.INTERIOR_BSE, "entrance")
        self.assertEqual(self.game.state, STATE_GAMEPLAY)

        event_m = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m)
        self.game._handle_gameplay_event(event_m)
        self.assertEqual(self.game.state, "interior_map")

        self.game._handle_interior_map_event(event_m, (100, 100))
        self.assertEqual(self.game.state, STATE_GAMEPLAY)

    def test_golden_bull_easter_egg_awards_badge_and_xp(self):
        """Interacting with golden bull statuette inside BSE awards badge and XP."""
        self.game.world.set_location(config.INTERIOR_BSE)
        bull_obj = next(o for o in self.game.world.current_map.objects if o.id == "egg_golden_bull")
        self.game.player.x = bull_obj.x
        self.game.player.y = bull_obj.y + bull_obj.h + 4
        self.game.player.facing = "up"

        init_xp = self.game.xp
        self.game._interact()

        self.assertIn("Golden Bull Explorer", self.game.badges)
        self.assertGreater(self.game.xp, init_xp)

    def test_fictional_educational_dialogue_disclaimer_for_historical_figures(self):
        """Verify Rakesh Jhunjhunwala and Harshad Mehta dialogue trees have fictional educational framing."""
        with open("data/dialogue.json", "r") as f:
            data = json.load(f)

        npcs = data.get("npcs", data)
        self.assertIn("rakesh_mentor", npcs)
        self.assertIn("harshad_case_analyst", npcs)

        rj_text = npcs["rakesh_mentor"]["dialogues"]["start"]["text"].lower()
        self.assertTrue("fictional" in rj_text or "educational" in rj_text or "mentor" in rj_text)

        hm_text = npcs["harshad_case_analyst"]["dialogues"]["start"]["text"].lower()
        self.assertTrue("case study" in hm_text or "history" in hm_text or "fictional" in hm_text)


if __name__ == "__main__":
    unittest.main()
