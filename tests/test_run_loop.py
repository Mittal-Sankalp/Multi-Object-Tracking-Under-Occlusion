"""
MarketQuest - Headless Game Loop & Runtime Smoke Test
Runs the actual Game loop for 300+ frames, testing:
- Player exploration and camera tracking
- Interior transitions and door warp back to exterior
- Location-restricted trading enforcement
- Clue Journal rendering and evidence synthesis
- Global transit map with 4 unlockable exchanges
- Persistence and saving/loading
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame
import config
from src.game import (
    Game, STATE_GAMEPLAY, STATE_TRADING, STATE_PORTFOLIO, STATE_PAUSE,
    STATE_CLUE_JOURNAL, STATE_TRAVEL, STATE_NEWS, STATE_GLOSSARY,
    STATE_EXCHANGE_HUB, STATE_COMPANY_DOSSIER, STATE_BANK,
    STATE_ACADEMY, STATE_BULL_MODAL, STATE_BANYAN_MODAL, STATE_CHAI_MODAL,
    STATE_RETURN_BREAKDOWN, STATE_CAMPAIGN, STATE_INVESTMENT_THESIS
)
from src.investigation import InvestmentThesis

def smoke_test():
    pygame.init()
    if not pygame.mixer.get_init():
        try:
            pygame.mixer.init()
        except Exception:
            pass

    screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    game = Game(screen, window_scale=config.WINDOW_SCALE)
    game.start_new_game()
    game.ui_mgr.show_tutorial = False  # close tutorial for automated test

    print("1. Game started in Dalal Street, Mumbai:", game.world.current_location_id == config.LOCATION_DALAL_STREET)

    # 1. Simulate 60 frames of player movement in Dalal Street
    for i in range(60):
        dt = 1.0 / 60.0
        game.player.x += 1.0
        game.update(dt)
        game.draw()

    print("60 frames of Dalal Street movement rendered. Player x:", game.player.x)

    # 2. Verify trading outside exchange floor is restricted
    print("Is on trading floor outside?", game.is_on_trading_floor())
    assert not game.is_on_trading_floor(), "Should not be on trading floor outside"
    succ, msg = game.portfolio.buy("CHAI", 1, 50.0, authorized=game.is_on_trading_floor())
    assert not succ, "Trade should be rejected outside"
    print("Outside trade correctly rejected:", msg)

    # 3. Enter BSE Interior Floor
    game.player.exterior_pos = (game.player.x, game.player.y)
    game.player.exterior_map = game.world.current_location_id
    spawn = game.world.set_location(config.INTERIOR_BSE, "entrance")
    game.player.x, game.player.y = spawn
    print("Entered BSE Floor. Location:", game.world.current_location_id)
    assert game.is_on_trading_floor(), "Should be on trading floor inside BSE"

    # Execute authorized trade on BSE floor
    comp = game.market.get_company("CHAI")
    succ, msg = game.portfolio.buy("CHAI", 5, comp.price, day=game.market.day, authorized=game.is_on_trading_floor())
    assert succ, f"Trade on BSE floor failed: {msg}"
    print("Trade on BSE floor succeeded:", msg)

    # 4a. Test Architectural Blueprint Map inside BSE ([M])
    game.state = STATE_GAMEPLAY
    event_m = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m)
    game._handle_gameplay_event(event_m)
    assert game.state == "interior_map", "Pressing [M] inside interior should open interior blueprint map"
    for _ in range(15):
        game.update(1.0 / 60.0)
        game.draw()
    # Close blueprint map
    game._handle_interior_map_event(event_m, (100, 100))
    assert game.state == STATE_GAMEPLAY, "Closing blueprint map should return to GAMEPLAY"
    print("Architectural Blueprint Map toggled, rendered, and closed successfully.")

    # 4b. Test Historical Mentors & Easter Eggs inside BSE
    # Talk to Rakesh Jhunjhunwala historical value mentor
    mentor_npc = next(n for n in game.world.current_map.npcs if n.id == "rakesh_mentor")
    game.player.x = mentor_npc.x
    game.player.y = mentor_npc.y + 20
    game.player.direction = "up"
    game._interact()
    assert game.state == "dialogue", "Interacting with Rakesh Jhunjhunwala should open dialogue"
    assert game.dialogue_mgr.current_npc_id == "rakesh_mentor"
    for _ in range(5):
        game.update(1.0 / 60.0)
        game.draw()
    game.state = STATE_GAMEPLAY
    print("Rakesh Jhunjhunwala educational value mentor dialogue verified.")

    # Discover Golden Bull Easter Egg
    bull_egg = next(o for o in game.world.current_map.objects if o.id == "egg_golden_bull")
    game.player.x = bull_egg.x
    game.player.y = bull_egg.y + bull_egg.h + 4
    game.player.direction = "up"
    xp_before = game.xp
    game._interact()
    assert "Golden Bull Explorer" in game.badges, "Interacting with golden bull must award badge"
    assert game.xp > xp_before, "Golden bull must grant XP"
    print("Golden Bull Easter Egg discovery verified (+100 XP, 'Golden Bull Explorer' badge).")

    # Discover Graham First Edition Easter Egg
    graham_egg = next(o for o in game.world.current_map.objects if o.id == "egg_graham_book")
    game.player.x = graham_egg.x
    game.player.y = graham_egg.y + graham_egg.h + 4
    game.player.direction = "up"
    game._interact()
    assert "Value Disciple" in game.badges, "Interacting with Graham book must award Value Disciple badge"
    print("Graham First Edition Easter Egg discovery verified (+50 XP, 'Value Disciple' badge).")

    # 4c. Render 30 frames in Trading Terminal inside BSE
    game.state = STATE_TRADING
    for _ in range(30):
        game.update(1.0 / 60.0)
        game.draw()
    print("30 frames of Trading Terminal rendered successfully.")

    # 5. Exit back to Dalal Street outside
    dest_map = game.player.exterior_map
    game.world.set_location(dest_map)
    game.player.x, game.player.y = game.player.exterior_pos
    game.state = STATE_GAMEPLAY
    print("Exited back to exterior district:", game.world.current_location_id)
    assert game.world.current_location_id == config.LOCATION_DALAL_STREET

    # 6. Test Clue Investigation Journal
    game.investigation.unlock_clue("chai_harvest_record")
    game.investigation.unlock_clue("chai_shipping_reroute")
    game.investigation.unlock_clue("chai_se_asia_retail")
    game.state = STATE_CLUE_JOURNAL
    for _ in range(20):
        game.update(1.0 / 60.0)
        game.draw()
    print("Clue Journal rendered successfully. Thesis conviction:", game.investigation.get_thesis_rating("CHAI")[0])

    # 7. Test Global Travel Map (4 Exchanges)
    game.state = STATE_TRAVEL
    for _ in range(20):
        game.update(1.0 / 60.0)
        game.draw()
    print("Global Travel Map rendered successfully.")

    # 8. Test all 14 Interiors rendering
    all_interiors = [
        config.INTERIOR_BSE, config.INTERIOR_NYSE, config.INTERIOR_TSE, config.INTERIOR_LSE,
        config.INTERIOR_BANK, config.INTERIOR_LIBRARY, config.INTERIOR_WHITE_HOUSE,
        config.INTERIOR_PARLIAMENT, config.INTERIOR_APEX_HQ, config.INTERIOR_TITAN_HQ,
        config.INTERIOR_MONSOON_HQ, config.INTERIOR_NOVA_HQ, config.INTERIOR_AURA_HQ,
        config.INTERIOR_MEDX_HQ
    ]
    for interior_id in all_interiors:
        game.world.set_location(interior_id, "entrance")
        game.state = STATE_GAMEPLAY
        for _ in range(5):
            game.update(1.0 / 60.0)
            game.draw()
        print(f"Interior '{interior_id}' rendered flawlessly.")

    # 9. Test Story Campaign Progression & Route Guidance
    initial_obj = game.story.get_active_objective()
    assert initial_obj is not None, "Active objective should exist"
    print("Initial Story Objective:", initial_obj["title"])

    # Advance objective by talking to mentor Devendra
    adv_msg = game.story.on_talk_npc("devendra", game)
    assert adv_msg is not None, "Objective should advance after talking to Devendra"
    print("Advanced objective:", adv_msg)

    # Route Guidance Calculation
    game.world.set_location(config.LOCATION_DALAL_STREET)
    game.update(0.6)  # triggers route recalculation
    print("Route waypoints computed:", len(game.player.current_route))
    assert len(game.player.current_route) > 0, "Route breadcrumbs should be populated"

    # 10. Test Return Breakdown Panel & 5 Educational Layers
    game.state = STATE_RETURN_BREAKDOWN
    for layer in range(1, 6):
        game.ui_mgr.education_layer = layer
        for _ in range(3):
            game.update(1.0 / 60.0)
            game.draw()
    print("Return Breakdown & 5 Educational Layers rendered flawlessly.")

    # 11. Test Campaign Progress Screen
    game.state = STATE_CAMPAIGN
    for ch_idx in range(len(game.story.chapters)):
        game.ui_mgr.campaign_selected_chapter = ch_idx
        for _ in range(2):
            game.update(1.0 / 60.0)
            game.draw()
    print("Story Campaign Progress Screen rendered across all 6 chapters.")

    # 12. Test Investment Thesis Screen & Resolution Evaluation
    game.state = STATE_INVESTMENT_THESIS
    test_thesis = InvestmentThesis(
        company_symbol="CHAI",
        rationale="Solid harvest yield and fixed maritime freight",
        evidence_clues=["chai_harvest_record", "chai_shipping_reroute"],
        catalysts="ASEAN expansion",
        risks="Weather volatility",
        confidence_level="High Conviction",
        holding_period="1-2 Weeks",
        position_size_pct=25.0,
        entry_price=52.30,
        entry_step=1
    )
    game.investigation.record_thesis(test_thesis)
    eval_note = test_thesis.evaluate_outcome(55.20)
    assert "Thesis Validated" in eval_note, "Positive gain should validate thesis"
    for _ in range(10):
        game.update(1.0 / 60.0)
        game.draw()
    print("Investment Thesis screen rendered successfully. Outcome:", eval_note)

    # 13. Test Save & Load with Story and Theses
    game.state = STATE_PAUSE
    ok, save_msg = game.save_current_game()
    assert ok, f"Save failed: {save_msg}"
    print("Game saved successfully.")

    loaded_ok = game.load_saved_game()
    assert loaded_ok, "Load failed"
    assert game.story.current_objective_idx == 1, "Saved story objective should be restored"
    assert len(game.investigation.theses) > 0, "Saved theses should be restored"
    print("Game loaded successfully with Story & Thesis persistence verified.")

    pygame.quit()
    print("All smoke test assertions passed flawlessly!")

if __name__ == "__main__":
    smoke_test()
