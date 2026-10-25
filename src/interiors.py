"""
MarketQuest - Explorable Interior Maps & Landmarks
Provides fully navigable, collision-aware interior maps for:
1. Bombay Stock Exchange (BSE) Trading Floor
2. New York Stock Exchange (NYSE) Trading Floor
3. Tokyo Stock Exchange (TSE) Trading Floor
4. London Stock Exchange (LSE) Trading Floor
5. First Metropolitan Commercial Bank
6. Investor Archives & Research Library
7. The White House Press & Policy Suite
8. Parliament of India Central Briefing Hall
9. Apex Dynamics Autonomous Systems Lab
10. Titan Capital Merchant Bank Executive HQ
11. Monsoon Global Goods Heritage Trading House
"""

import pygame
from typing import Dict, List, Tuple, Optional, Any
from config import (
    TILE_SIZE, VIRTUAL_WIDTH, VIRTUAL_HEIGHT,
    COLOR_BG_DARK, COLOR_PANEL_BG, COLOR_PANEL_ALT, COLOR_BORDER, COLOR_BORDER_ACCENT,
    COLOR_TEXT_WHITE, COLOR_TEXT_GOLD, COLOR_GAIN, COLOR_GAIN_BRIGHT, COLOR_LOSS_BRIGHT,
    INTERIOR_BSE, INTERIOR_NYSE, INTERIOR_TSE, INTERIOR_LSE,
    INTERIOR_BANK, INTERIOR_LIBRARY, INTERIOR_WHITE_HOUSE, INTERIOR_PARLIAMENT,
    INTERIOR_APEX_HQ, INTERIOR_TITAN_HQ, INTERIOR_MONSOON_HQ,
    INTERIOR_NOVA_HQ, INTERIOR_AURA_HQ, INTERIOR_MEDX_HQ
)
from src.world import NPC, WorldObject, LocationMap


def create_interior_shell(map_id: str, name: str, width: int = 26, height: int = 16, floor_tile: int = 1) -> LocationMap:
    """Helper creating an enclosed room shell with perimeter walls and an exit door at the bottom."""
    m = LocationMap(map_id, name, width, height)

    # Fill floor
    for y in range(height):
        for x in range(width):
            m.tiles[y][x] = floor_tile

    # Outer perimeter walls (solid colliders)
    top_wall = pygame.Rect(0, 0, width * TILE_SIZE, 2 * TILE_SIZE)
    bot_left_wall = pygame.Rect(0, (height - 1) * TILE_SIZE, 11 * TILE_SIZE, TILE_SIZE)
    bot_right_wall = pygame.Rect(15 * TILE_SIZE, (height - 1) * TILE_SIZE, (width - 15) * TILE_SIZE, TILE_SIZE)
    left_wall = pygame.Rect(0, 0, TILE_SIZE, height * TILE_SIZE)
    right_wall = pygame.Rect((width - 1) * TILE_SIZE, 0, TILE_SIZE, height * TILE_SIZE)

    m.solids.extend([top_wall, bot_left_wall, bot_right_wall, left_wall, right_wall])

    # Exit Door trigger at bottom center (x: 12..14, y: 15)
    exit_obj = WorldObject(
        "door_exit", "door", 11.5 * TILE_SIZE, (height - 1) * TILE_SIZE, 3 * TILE_SIZE, TILE_SIZE,
        "Exit Door", "Step through the double doors to return to the city district.",
        action_type="exit_interior"
    )
    m.objects.append(exit_obj)

    # Spawn point when entering from outside
    m.spawn_points["entrance"] = (12.5 * TILE_SIZE, (height - 3) * TILE_SIZE)
    m.spawn_points["default"] = (12.5 * TILE_SIZE, (height - 3) * TILE_SIZE)

    return m


# -----------------------------------------------------------------
# 1. BOMBAY STOCK EXCHANGE (BSE) TRADING FLOOR — GRAND SIGNATURE LOCATION
# -----------------------------------------------------------------
def build_bse_trading_floor() -> LocationMap:
    """
    Substantial 48x36 interconnected interior for Bombay Stock Exchange:
    1. Main Entrance Vestibule & Turnstiles
    2. Grand Reception Lobby & Compass Rose
    3. Security & Visitor Badging Desk
    4. Main Trading Hall (Visual Centrepiece)
    5. Four Broker Desk Rows
    6. Large Animated Market Ticker Screens
    7. Wall-Mounted Market Displays
    8. Research & Fundamental Analysis Room (Rakesh Jhunjhunwala Educational Mentor)
    9. Financial History Gallery (1992 Scam Case Study & Harshad Mehta Case Analyst)
    10. Investor Education Classroom (DuPont Framework & Meenakshi)
    11. Portfolio & Risk Analysis Room (Beta & VaR Analysis)
    12. Executive Boardroom / Quiet Meeting Suite
    13. Cross-Building Staff Corridor
    14. Restricted Archive & Hidden Easter Egg Vault (Vintage Ticker, Graham Book, Bull Egg)
    15. Exit Doors to Dalal Street
    """
    m = LocationMap(INTERIOR_BSE, "Bombay Stock Exchange (BSE) — Phiroze Jeejeebhoy Floor", 48, 36)

    # 1. Custom Room Ground Tiles
    for y in range(36):
        for x in range(48):
            if 11 <= y <= 24 and 15 <= x <= 33:
                m.tiles[y][x] = 3  # Terracotta & Brass Trading Hall
            elif 25 <= y <= 34 and 17 <= x <= 31:
                m.tiles[y][x] = 1  # Italian Marble Lobby & Vestibule
            elif (11 <= y <= 34 and 2 <= x <= 14) or (2 <= y <= 7 and 18 <= x <= 30):
                m.tiles[y][x] = 4  # Parquet Wood (Museum, Library & Secret Vault)
            elif (11 <= y <= 34 and 34 <= x <= 46) or (2 <= y <= 8 and 2 <= x <= 14):
                m.tiles[y][x] = 2  # Blue Slate Carpet (Research Lab, Education & Boardroom)
            else:
                m.tiles[y][x] = 1  # Polished Stone Corridors

    # 2. Outer Perimeter Walls (solid)
    m.solids.extend([
        pygame.Rect(0, 0, 48 * TILE_SIZE, 2 * TILE_SIZE),                       # Top wall
        pygame.Rect(0, 0, 2 * TILE_SIZE, 36 * TILE_SIZE),                       # Left wall
        pygame.Rect(46 * TILE_SIZE, 0, 2 * TILE_SIZE, 36 * TILE_SIZE),          # Right wall
        pygame.Rect(0, 34 * TILE_SIZE, 22 * TILE_SIZE, 2 * TILE_SIZE),          # Bottom left wall
        pygame.Rect(26 * TILE_SIZE, 34 * TILE_SIZE, 22 * TILE_SIZE, 2 * TILE_SIZE) # Bottom right wall
    ])

    # 3. Internal Dividing Walls with Generous Walkable Openings
    # West Wing Divider (x = 14)
    m.solids.extend([
        pygame.Rect(14 * TILE_SIZE, 2 * TILE_SIZE, TILE_SIZE, 7 * TILE_SIZE),   # Boardroom divider
        pygame.Rect(14 * TILE_SIZE, 11 * TILE_SIZE, TILE_SIZE, 5 * TILE_SIZE),  # North gallery wall
        pygame.Rect(14 * TILE_SIZE, 19 * TILE_SIZE, TILE_SIZE, 6 * TILE_SIZE),  # Mid gallery wall
        pygame.Rect(14 * TILE_SIZE, 28 * TILE_SIZE, TILE_SIZE, 6 * TILE_SIZE),  # Library annex wall
    ])

    # East Wing Divider (x = 33)
    m.solids.extend([
        pygame.Rect(33 * TILE_SIZE, 2 * TILE_SIZE, TILE_SIZE, 7 * TILE_SIZE),   # Risk room divider
        pygame.Rect(33 * TILE_SIZE, 11 * TILE_SIZE, TILE_SIZE, 5 * TILE_SIZE),  # North research wall
        pygame.Rect(33 * TILE_SIZE, 19 * TILE_SIZE, TILE_SIZE, 6 * TILE_SIZE),  # Mid research wall
        pygame.Rect(33 * TILE_SIZE, 28 * TILE_SIZE, TILE_SIZE, 6 * TILE_SIZE),  # Education room wall
    ])

    # North Corridor Wall (y = 8)
    m.solids.extend([
        pygame.Rect(2 * TILE_SIZE, 8 * TILE_SIZE, 8 * TILE_SIZE, TILE_SIZE),    # Left corridor wall
        pygame.Rect(14 * TILE_SIZE, 8 * TILE_SIZE, 8 * TILE_SIZE, TILE_SIZE),   # Archive left wall
        pygame.Rect(26 * TILE_SIZE, 8 * TILE_SIZE, 8 * TILE_SIZE, TILE_SIZE),   # Archive right wall
        pygame.Rect(38 * TILE_SIZE, 8 * TILE_SIZE, 8 * TILE_SIZE, TILE_SIZE),   # Risk corridor wall
    ])

    # Trading Hall South Wall (y = 24)
    m.solids.extend([
        pygame.Rect(15 * TILE_SIZE, 24 * TILE_SIZE, 6 * TILE_SIZE, TILE_SIZE),  # South hall left
        pygame.Rect(27 * TILE_SIZE, 24 * TILE_SIZE, 6 * TILE_SIZE, TILE_SIZE),  # South hall right
    ])

    # Vestibule Walls (x = 19 and x = 28)
    m.solids.extend([
        pygame.Rect(19 * TILE_SIZE, 30 * TILE_SIZE, TILE_SIZE, 4 * TILE_SIZE),  # Vestibule left
        pygame.Rect(28 * TILE_SIZE, 30 * TILE_SIZE, TILE_SIZE, 4 * TILE_SIZE),  # Vestibule right
    ])

    # 4. Central Trading Pit Architecture & Terminal
    # Brass Railings & Pit Desks
    pit_rail_l = pygame.Rect(20 * TILE_SIZE, 16 * TILE_SIZE, 12, 5 * TILE_SIZE)
    pit_rail_r = pygame.Rect(27 * TILE_SIZE + 12, 16 * TILE_SIZE, 12, 5 * TILE_SIZE)
    m.solids.extend([pit_rail_l, pit_rail_r])

    # Central Interactive Order Terminal
    m.objects.append(WorldObject(
        "bse_trading_console", "terminal", 23 * TILE_SIZE, 17 * TILE_SIZE, 2 * TILE_SIZE, 2 * TILE_SIZE,
        "BSE Floor Specialist Terminal",
        "Direct access to Dalal Street order routing. Execute buy and sell orders on active Indian equities.",
        action_type="open_trading"
    ))

    # Broker Desk Rows
    desk1 = pygame.Rect(16 * TILE_SIZE, 15 * TILE_SIZE, 3 * TILE_SIZE, 20)
    desk2 = pygame.Rect(16 * TILE_SIZE, 21 * TILE_SIZE, 3 * TILE_SIZE, 20)
    desk3 = pygame.Rect(29 * TILE_SIZE, 15 * TILE_SIZE, 3 * TILE_SIZE, 20)
    desk4 = pygame.Rect(29 * TILE_SIZE, 21 * TILE_SIZE, 3 * TILE_SIZE, 20)
    m.solids.extend([desk1, desk2, desk3, desk4])

    # Ticker Screen Board on North Trading Hall Wall
    m.objects.append(WorldObject(
        "bse_ticker_wall", "screen", 17 * TILE_SIZE, 10 * TILE_SIZE, 14 * TILE_SIZE, 24,
        "Overhead Sensex & BSE 50 LED Electronic Board",
        "Live market order books and sector price quotes. Updated continuously with market simulation.",
        action_type="inspect"
    ))

    # Ceremonial BSE Opening Bell Podium
    m.objects.append(WorldObject(
        "bse_bell", "landmark", 16 * TILE_SIZE, 12 * TILE_SIZE, 2 * TILE_SIZE, 2 * TILE_SIZE,
        "Historic BSE Brass Ceremonial Gong",
        "The iconic ceremonial gong rung at 09:15 IST to open the Indian market session.",
        action_type="inspect"
    ))

    # 5. Financial History Gallery Exhibits (West Wing)
    m.objects.extend([
        WorldObject(
            "exhibit_banyan_1875", "landmark", 4 * TILE_SIZE, 13 * TILE_SIZE, 3 * TILE_SIZE, 2 * TILE_SIZE,
            "Exhibit: 1875 Banyan Tree Brokers' Union",
            "Archival records and photographs of the 318 native brokers who gathered under the Dalal Street banyan tree to form the Native Share & Stock Brokers' Association.",
            action_type="inspect"
        ),
        WorldObject(
            "exhibit_1992_scam", "landmark", 4 * TILE_SIZE, 18 * TILE_SIZE, 3 * TILE_SIZE, 2 * TILE_SIZE,
            "Exhibit: 1992 Securities Scam & Regulatory Genesis",
            "Forensic case study: How uncollateralized Bank Receipts (BRs) distorted credit liquidity, prompting the statutory founding of SEBI and electronic settlement. (Clue: bse_1992_case_study)",
            action_type="inspect"
        ),
        WorldObject(
            "exhibit_bolt_1995", "landmark", 4 * TILE_SIZE, 22 * TILE_SIZE, 3 * TILE_SIZE, 2 * TILE_SIZE,
            "Exhibit: 1995 Electronic BOLT Revolution",
            "Display of the BSE On-Line Trading system that retired open-outcry pit shouting in favor of millisecond electronic order matching.",
            action_type="inspect"
        ),
        WorldObject(
            "exhibit_crisis_2008", "landmark", 9 * TILE_SIZE, 22 * TILE_SIZE, 3 * TILE_SIZE, 2 * TILE_SIZE,
            "Exhibit: 2008 Contagion & Value Resilience",
            "Market charts proving that companies with durable cash flows and low debt survived the global credit shock and generated multi-bagger returns.",
            action_type="inspect"
        )
    ])

    # 6. Equity Research Lab (East Wing)
    res_table1 = pygame.Rect(36 * TILE_SIZE, 17 * TILE_SIZE, 3 * TILE_SIZE, 20)
    res_table2 = pygame.Rect(41 * TILE_SIZE, 17 * TILE_SIZE, 3 * TILE_SIZE, 20)
    m.solids.extend([res_table1, res_table2])

    m.objects.extend([
        WorldObject(
            "bse_whiteboard_valuation", "screen", 37 * TILE_SIZE, 11 * TILE_SIZE, 6 * TILE_SIZE, 20,
            "Valuation & Economic Moats Whiteboard",
            "Formula sheets comparing DCF free cash flow yields, ROIC vs WACC spreads, and pricing power indicators.",
            action_type="inspect"
        ),
        WorldObject(
            "bse_research_dossier", "ledger", 43 * TILE_SIZE, 13 * TILE_SIZE, 2 * TILE_SIZE, 24,
            "Institutional Equity Research Dossier",
            "Audited balance sheet analysis and margin expansion models across Dalal Street sectors. (Clue: bse_fundamental_model)",
            action_type="inspect"
        )
    ])

    # 7. Investor Education Room (South-East Wing)
    m.objects.extend([
        WorldObject(
            "bse_blackboard_dupont", "screen", 37 * TILE_SIZE, 26 * TILE_SIZE, 6 * TILE_SIZE, 20,
            "DuPont Framework & Financial Ratio Blackboard",
            "Deconstructing ROE into Profit Margin, Asset Turnover, and Financial Leverage to identify high-quality compounders.",
            action_type="inspect"
        ),
        WorldObject(
            "bse_edu_terminal", "terminal", 42 * TILE_SIZE, 29 * TILE_SIZE, 2 * TILE_SIZE, 24,
            "Interactive Value Investing Primer Station",
            "Interactive modules covering margin of safety, portfolio rebalancing, and avoiding speculative bull traps.",
            action_type="inspect"
        )
    ])

    # 8. Executive Boardroom & Risk Room (North Wing)
    conf_table = pygame.Rect(5 * TILE_SIZE, 4 * TILE_SIZE, 5 * TILE_SIZE, 2 * TILE_SIZE)
    m.solids.append(conf_table)
    m.objects.extend([
        WorldObject(
            "bse_boardroom_table", "landmark", 5 * TILE_SIZE, 4 * TILE_SIZE, 5 * TILE_SIZE, 2 * TILE_SIZE,
            "BSE Governing Council Teak Conference Table",
            "The historic boardroom where exchange listing rules, surveillance algorithms, and market circuit-breaker limits are formulated.",
            action_type="inspect"
        ),
        WorldObject(
            "bse_risk_terminal", "terminal", 38 * TILE_SIZE, 4 * TILE_SIZE, 3 * TILE_SIZE, 2 * TILE_SIZE,
            "Portfolio VaR & Stress Testing Console",
            "Institutional risk analytics calculating Value-at-Risk (VaR) and beta-hedging sensitivities.",
            action_type="inspect"
        )
    ])

    # 9. Restricted Archive & Hidden Easter Egg Vault (North-Center Wing, x: 18..30, y: 2..7)
    m.objects.extend([
        WorldObject(
            "egg_vintage_ticker", "landmark", 20 * TILE_SIZE, 3 * TILE_SIZE, 2 * TILE_SIZE, 2 * TILE_SIZE,
            "Vintage 1920s Telegraphic Stock Ticker Machine",
            "[EASTER EGG] An ornate brass telegraph ticker printing paper ribbon. Displays a nostalgic printout: 'BUY VALUE, IGNORE THE NOISE!'",
            action_type="inspect"
        ),
        WorldObject(
            "egg_graham_book", "ledger", 24 * TILE_SIZE, 3 * TILE_SIZE, 2 * TILE_SIZE, 24,
            "First Edition 'The Intelligent Investor'",
            "[EASTER EGG] A rare 1949 leatherbound first edition signed with a handwritten note: 'An investment operation is one which, upon thorough analysis, promises safety of principal and an adequate return.'",
            action_type="inspect"
        ),
        WorldObject(
            "egg_runner_log", "ledger", 27 * TILE_SIZE, 3 * TILE_SIZE, 2 * TILE_SIZE, 24,
            "Floor Runner Arbitrage Logbook",
            "[EASTER EGG] Handwritten trading diary of a legendary Dalal Street arbitrageur recording inter-exchange spreads from the 1960s. (Clue: bse_secret_ledger)",
            action_type="inspect"
        ),
        WorldObject(
            "egg_golden_bull", "landmark", 24 * TILE_SIZE, 5 * TILE_SIZE, 2 * TILE_SIZE, 2 * TILE_SIZE,
            "Commemorative Gilded Bull Statuette",
            "[EASTER EGG] A miniature solid bronze bull statue commemorating market resilience. Inspecting this grants +100 XP and the 'Golden Bull Explorer' honor!",
            action_type="inspect"
        )
    ])

    # 10. Reception Lobby & Entrance Vestibule (South Wing)
    lobby_desk = pygame.Rect(22 * TILE_SIZE, 27 * TILE_SIZE, 4 * TILE_SIZE, 20)
    m.solids.append(lobby_desk)
    m.objects.extend([
        WorldObject(
            "bse_lobby_plaque", "sign", 24 * TILE_SIZE, 25 * TILE_SIZE + 4, 18, 18,
            "Phiroze Jeejeebhoy Central Rotunda Marker",
            "Bombay Stock Exchange (Estd 1875). North: Trading Pit. West: Financial History Gallery. East: Research Lab.",
            action_type="sign"
        ),
        WorldObject(
            "door_exit", "door", 22 * TILE_SIZE, 34 * TILE_SIZE, 4 * TILE_SIZE, 24,
            "Grand Exit Doors to Dalal Street",
            "Step through the brass double doors to return to Dalal Street.",
            action_type="exit_interior"
        )
    ])

    # 11. NPCs Across All 15 Connected Zones
    m.npcs.extend([
        # Vestibule & Lobby
        NPC("security_officer_bse", "Inspector Kadam", "BSE Chief Security Inspector", 21 * TILE_SIZE, 32 * TILE_SIZE, (100, 120, 150)),
        NPC("concierge_pooja", "Pooja Varma", "Senior Exchange Concierge", 24 * TILE_SIZE, 28 * TILE_SIZE, (245, 140, 50)),
        
        # Main Trading Hall
        NPC("rajesh", "Rajesh Singhania", "Senior BSE Floor Arbitrageur", 22 * TILE_SIZE, 15 * TILE_SIZE, (218, 165, 32)),
        NPC("vikram", "Vikram Merchant", "Clearing Member Specialist", 18 * TILE_SIZE, 17 * TILE_SIZE, (46, 196, 182)),
        NPC("anita", "Anita Deshmukh", "Institutional Equity Broker", 30 * TILE_SIZE, 17 * TILE_SIZE, (245, 140, 50)),
        
        # Research & Analysis Lab (Signature Educational Mentor)
        NPC("rakesh_mentor", "Rakesh Jhunjhunwala (Historical Mentor)", "Legendary Value Investor & Bull [FICTIONAL EDUCATIONAL CHARACTER]", 40 * TILE_SIZE, 16 * TILE_SIZE, (218, 165, 32)),
        
        # History Gallery (1992 Case Study Curator)
        NPC("harshad_case_analyst", "Investigator K. V. Sharma", "Financial History Curator & Case Analyst", 8 * TILE_SIZE, 17 * TILE_SIZE, (200, 70, 60)),
        
        # Investor Education Classroom
        NPC("prof_meenakshi", "Professor Meenakshi", "Director of Investor Education", 40 * TILE_SIZE, 28 * TILE_SIZE, (180, 100, 240)),
        
        # Portfolio Risk Room
        NPC("devika_risk", "Devika Rao", "Chief Portfolio Risk Officer", 40 * TILE_SIZE, 5 * TILE_SIZE, (72, 202, 228)),
        
        # Executive Boardroom
        NPC("siddharth_board", "Siddharth Birla", "BSE Governing Council Member", 11 * TILE_SIZE, 4 * TILE_SIZE + 8, (160, 130, 50))
    ])

    # Spawn Points
    m.spawn_points["entrance"] = (24 * TILE_SIZE, 33 * TILE_SIZE)
    m.spawn_points["default"] = (24 * TILE_SIZE, 33 * TILE_SIZE)

    return m


# -----------------------------------------------------------------
# 2. NEW YORK STOCK EXCHANGE (NYSE) TRADING FLOOR
# -----------------------------------------------------------------
def build_nyse_trading_floor() -> LocationMap:
    m = create_interior_shell(INTERIOR_NYSE, "New York Stock Exchange (NYSE) — Main Floor", 26, 16, floor_tile=1)

    # Trading Post Pods (Colonnade structure)
    post_a = pygame.Rect(6 * TILE_SIZE, 5 * TILE_SIZE, 4 * TILE_SIZE, 3 * TILE_SIZE)
    post_b = pygame.Rect(16 * TILE_SIZE, 5 * TILE_SIZE, 4 * TILE_SIZE, 3 * TILE_SIZE)
    m.solids.extend([post_a, post_b])

    # Interactive NYSE Specialist Terminal (at Post A)
    m.objects.append(WorldObject(
        "nyse_trading_console", "terminal", 7 * TILE_SIZE, 5 * TILE_SIZE, 2 * TILE_SIZE, 2 * TILE_SIZE,
        "NYSE Designated Market Maker (DMM) Terminal",
        "Direct equity order routing console for Wall Street. Trade NYSE & NASDAQ equities.",
        action_type="open_trading"
    ))

    # Opening Bell Balcony Stairs top center
    m.solids.append(pygame.Rect(11 * TILE_SIZE, 2 * TILE_SIZE, 4 * TILE_SIZE, 2 * TILE_SIZE))
    m.objects.append(WorldObject(
        "nyse_bell_balcony", "landmark", 11 * TILE_SIZE, 2 * TILE_SIZE, 4 * TILE_SIZE, 2 * TILE_SIZE,
        "NYSE Opening Bell Balcony",
        "The world-famous rostrum where CEOs and market luminaries ring the brass bell at 09:30 EST.",
        action_type="inspect"
    ))

    # Bloomberg Multi-Screen Rig (at Post B)
    m.objects.append(WorldObject(
        "nyse_bloomberg", "screen", 17 * TILE_SIZE, 5 * TILE_SIZE, 2 * TILE_SIZE, 2 * TILE_SIZE,
        "Institutional Bloomberg Terminal Array",
        "Real-time level 2 market depth, yield curves, and macroeconomic liquidity flows.",
        action_type="inspect"
    ))

    # NPCs
    m.npcs.append(NPC("bob", "Bob Henderson", "NYSE Designated Market Maker", 8 * TILE_SIZE, 8 * TILE_SIZE + 4, (65, 105, 225)))
    m.npcs.append(NPC("sarah", "Sarah Vance", "Quantitative Algorithmic Trader", 18 * TILE_SIZE, 8 * TILE_SIZE + 4, (180, 100, 240)))
    m.npcs.append(NPC("charlie_nyse", "Floor Trader Charlie", "Pit Arbitrageur", 13 * TILE_SIZE, 8 * TILE_SIZE + 4, (220, 180, 50)))

    return m


# -----------------------------------------------------------------
# 3. FIRST METROPOLITAN COMMERCIAL BANK
# -----------------------------------------------------------------
def build_bank_interior() -> LocationMap:
    m = create_interior_shell(INTERIOR_BANK, "First Metropolitan Bank & Trust", 26, 16, floor_tile=4)

    # Long Teller Counter across the middle (x: 4..21, y: 5..6)
    teller_counter = pygame.Rect(4 * TILE_SIZE, 5 * TILE_SIZE, 18 * TILE_SIZE, 2 * TILE_SIZE)
    m.solids.append(teller_counter)

    # Steel Security Vault top right
    vault_rect = pygame.Rect(21 * TILE_SIZE, 2 * TILE_SIZE, 4 * TILE_SIZE, 3 * TILE_SIZE)
    m.solids.append(vault_rect)
    m.objects.append(WorldObject(
        "bank_vault", "vault", 21 * TILE_SIZE, 2 * TILE_SIZE, 4 * TILE_SIZE, 3 * TILE_SIZE,
        "Heavy Reinforced Steel Bullion Vault",
        "Holds virtual institutional reserve balances, gold bars, and clearing deposits.",
        action_type="inspect"
    ))

    # Bank Ledger Counter
    m.objects.append(WorldObject(
        "bank_counter", "counter", 10 * TILE_SIZE, 5 * TILE_SIZE, 6 * TILE_SIZE, 2 * TILE_SIZE,
        "Commercial Teller Window",
        "Deposit cash, review loan yields, and verify your virtual bank balance.",
        action_type="inspect"
    ))

    # NPCs
    m.npcs.append(NPC("grace", "Grace Adams", "Lead Commercial Teller", 12 * TILE_SIZE, 4 * TILE_SIZE, (46, 196, 182)))
    m.npcs.append(NPC("mr_sterling", "Mr. Sterling", "Wealth Management Director", 6 * TILE_SIZE, 4 * TILE_SIZE, (218, 165, 32)))

    return m


# -----------------------------------------------------------------
# 4. INVESTOR ARCHIVES & RESEARCH LIBRARY
# -----------------------------------------------------------------
def build_library_interior() -> LocationMap:
    m = create_interior_shell(INTERIOR_LIBRARY, "Center for Financial Studies & Historical Archives", 26, 16, floor_tile=3)

    # Bookcase arrays left and right
    bookcase_l1 = pygame.Rect(3 * TILE_SIZE, 3 * TILE_SIZE, 2 * TILE_SIZE, 6 * TILE_SIZE)
    bookcase_l2 = pygame.Rect(7 * TILE_SIZE, 3 * TILE_SIZE, 2 * TILE_SIZE, 6 * TILE_SIZE)
    bookcase_r1 = pygame.Rect(17 * TILE_SIZE, 3 * TILE_SIZE, 2 * TILE_SIZE, 6 * TILE_SIZE)
    bookcase_r2 = pygame.Rect(21 * TILE_SIZE, 3 * TILE_SIZE, 2 * TILE_SIZE, 6 * TILE_SIZE)
    m.solids.extend([bookcase_l1, bookcase_l2, bookcase_r1, bookcase_r2])

    # Reading Carrel center
    study_desk = pygame.Rect(11 * TILE_SIZE, 5 * TILE_SIZE, 4 * TILE_SIZE, 3 * TILE_SIZE)
    m.solids.append(study_desk)

    # Interactive Study Terminal
    m.objects.append(WorldObject(
        "library_terminal", "terminal", 12 * TILE_SIZE, 5 * TILE_SIZE, 2 * TILE_SIZE, 2 * TILE_SIZE,
        "Graham & Dodd Financial Research Terminal",
        "Access foundational texts on Security Analysis, P/E multiples, and fundamental margin of safety.",
        action_type="open_academy"
    ))

    # Macroeconomic Globe
    m.objects.append(WorldObject(
        "library_globe", "landmark", 12 * TILE_SIZE, 2 * TILE_SIZE, 2 * TILE_SIZE, 2 * TILE_SIZE,
        "Historic Illuminated Economic Globe",
        "Traces international maritime trade routes, sovereign debt cycles, and central bank hubs.",
        action_type="inspect"
    ))

    # NPCs
    m.npcs.append(NPC("eleanor", "Eleanor Vance", "Chief Financial Historian", 12 * TILE_SIZE, 9 * TILE_SIZE, (180, 100, 240)))
    m.npcs.append(NPC("dr_chen", "Dr. Chen", "Macroeconomic Fellow", 8 * TILE_SIZE, 9 * TILE_SIZE, (72, 202, 228)))

    return m


# -----------------------------------------------------------------
# 5. THE WHITE HOUSE PRESS & POLICY SUITE
# -----------------------------------------------------------------
def build_white_house_interior() -> LocationMap:
    m = create_interior_shell(INTERIOR_WHITE_HOUSE, "The White House — West Wing & Briefing Suite", 26, 16, floor_tile=1)

    # Press Briefing Room Podium top center
    podium_rect = pygame.Rect(11 * TILE_SIZE, 3 * TILE_SIZE, 4 * TILE_SIZE, 2 * TILE_SIZE)
    m.solids.append(podium_rect)

    m.objects.append(WorldObject(
        "wh_podium", "podium", 11 * TILE_SIZE, 3 * TILE_SIZE, 4 * TILE_SIZE, 2 * TILE_SIZE,
        "Presidential Briefing Podium [FICTIONAL SCENARIO]",
        "The official press lectern bearing the Presidential Seal. Used for major economic policy announcements.",
        action_type="inspect"
    ))

    # Executive Policy Desk left
    policy_desk = pygame.Rect(3 * TILE_SIZE, 4 * TILE_SIZE, 5 * TILE_SIZE, 2 * TILE_SIZE)
    m.solids.append(policy_desk)

    m.objects.append(WorldObject(
        "wh_policy_folder", "ledger", 4 * TILE_SIZE, 4 * TILE_SIZE, 3 * TILE_SIZE, 2 * TILE_SIZE,
        "National Manufacturing & Tariff Directive [FICTIONAL SCENARIO]",
        "Legislative review regarding semiconductor incentives and bilateral trade balances. (Clue: macro_fed_rates)",
        action_type="inspect"
    ))

    # Press Seating Rows bottom
    press_row1 = pygame.Rect(5 * TILE_SIZE, 8 * TILE_SIZE, 7 * TILE_SIZE, 24)
    press_row2 = pygame.Rect(14 * TILE_SIZE, 8 * TILE_SIZE, 7 * TILE_SIZE, 24)
    m.solids.extend([press_row1, press_row2])

    # NPCs
    # Presidential Figure (inspired by Donald Trump, with classic gestures and speech style)
    m.npcs.append(NPC("leader_us", "President Donald Vance", "Presidential Dealmaker [Fictional]", 12 * TILE_SIZE, 2 * TILE_SIZE + 4, (230, 57, 70)))
    # Press Secretary
    m.npcs.append(NPC("jennifer", "Jennifer Cole", "White House Press Secretary", 16 * TILE_SIZE, 3 * TILE_SIZE + 4, (72, 202, 228)))
    # Senior Economic Adviser
    m.npcs.append(NPC("marcus", "Marcus Reed", "Chief Economic Policy Adviser", 5 * TILE_SIZE, 6 * TILE_SIZE + 4, (218, 165, 32)))

    return m


# -----------------------------------------------------------------
# 6. PARLIAMENT OF INDIA CENTRAL BRIEFING HALL
# -----------------------------------------------------------------
def build_parliament_interior() -> LocationMap:
    m = create_interior_shell(INTERIOR_PARLIAMENT, "Parliament of India — Central Briefing Hall", 26, 16, floor_tile=3)

    # Speaker's Podium top center with Ashoka Lion emblem
    speaker_podium = pygame.Rect(11 * TILE_SIZE, 2 * TILE_SIZE, 4 * TILE_SIZE, 2 * TILE_SIZE)
    m.solids.append(speaker_podium)

    m.objects.append(WorldObject(
        "parliament_podium", "podium", 11 * TILE_SIZE, 2 * TILE_SIZE, 4 * TILE_SIZE, 2 * TILE_SIZE,
        "Lok Sabha Speaker's Rostrum [FICTIONAL SCENARIO]",
        "Elevated speaker's podium for national budget presentations and clean energy policy debates.",
        action_type="inspect"
    ))

    # Semicircular parliamentary benches
    bench_l = pygame.Rect(4 * TILE_SIZE, 6 * TILE_SIZE, 6 * TILE_SIZE, 2 * TILE_SIZE)
    bench_r = pygame.Rect(16 * TILE_SIZE, 6 * TILE_SIZE, 6 * TILE_SIZE, 2 * TILE_SIZE)
    m.solids.extend([bench_l, bench_r])

    # National Infrastructure & Clean Energy Bill dossier
    m.objects.append(WorldObject(
        "parliament_bill", "ledger", 6 * TILE_SIZE, 6 * TILE_SIZE, 2 * TILE_SIZE, 2 * TILE_SIZE,
        "National Clean Energy Corridor Bill [FICTIONAL SCENARIO]",
        "Government legislative bill allocating production subsidies to solar wafers and clean grid batteries (Clue: aura_solar_subsidies).",
        action_type="inspect"
    ))

    # NPCs
    # Prime Minister Figure (inspired by Narendra Modi, with visionary speeches on Make in India and Clean Energy)
    m.npcs.append(NPC("leader_india", "PM Narendra Deshmukh", "Prime Minister of India [Fictional]", 12 * TILE_SIZE, 4 * TILE_SIZE + 4, (245, 140, 50)))
    # Chief Economic Adviser
    m.npcs.append(NPC("subramanian", "Dr. Subramanian", "Chief Economic Adviser", 18 * TILE_SIZE, 5 * TILE_SIZE + 4, (46, 196, 182)))
    # Parliamentary Secretary
    m.npcs.append(NPC("ananya", "Ananya Sharma", "Parliamentary Secretary", 6 * TILE_SIZE, 5 * TILE_SIZE + 4, (218, 165, 32)))

    return m


# -----------------------------------------------------------------
# 7. APEX DYNAMICS AUTONOMOUS SYSTEMS LAB & HQ
# -----------------------------------------------------------------
def build_apex_hq_interior() -> LocationMap:
    m = create_interior_shell(INTERIOR_APEX_HQ, "Apex Dynamics Autonomous Systems Lab & HQ", 26, 16, floor_tile=0)

    # AI Server Racks along top wall
    server_racks = pygame.Rect(3 * TILE_SIZE, 2 * TILE_SIZE, 8 * TILE_SIZE, 2 * TILE_SIZE)
    m.solids.append(server_racks)

    m.objects.append(WorldObject(
        "apex_server_cluster", "screen", 3 * TILE_SIZE, 2 * TILE_SIZE, 8 * TILE_SIZE, 2 * TILE_SIZE,
        "Exaflop Neural Compute Cluster",
        "Pulsing neon blue server arrays processing real-time autonomous vehicle neural weights.",
        action_type="inspect"
    ))

    # Autonomous Vehicle Prototype Pod center right
    prototype_pod = pygame.Rect(16 * TILE_SIZE, 4 * TILE_SIZE, 6 * TILE_SIZE, 4 * TILE_SIZE)
    m.solids.append(prototype_pod)

    m.objects.append(WorldObject(
        "apex_proto_pod", "landmark", 16 * TILE_SIZE, 4 * TILE_SIZE, 6 * TILE_SIZE, 4 * TILE_SIZE,
        "Apex Cyberpod Gen-3 Autonomous Vehicle",
        "Sleek stainless-steel autonomous shuttle with steer-by-wire and solid-state battery architecture.",
        action_type="inspect"
    ))

    # Robotics R&D Workbench
    m.solids.append(pygame.Rect(4 * TILE_SIZE, 7 * TILE_SIZE, 5 * TILE_SIZE, 2 * TILE_SIZE))
    m.objects.append(WorldObject(
        "apex_chip_bench", "terminal", 4 * TILE_SIZE, 7 * TILE_SIZE, 5 * TILE_SIZE, 2 * TILE_SIZE,
        "Neural Vision Silicon Telemetry Workbench",
        "Bench testing logs show 42% lower thermal dissipation in autonomous vision chips. (Clue: apex_rd_chip).",
        action_type="inspect"
    ))

    # NPCs
    # Sterling Vance (inspired by Elon Musk - visionary tech CEO)
    m.npcs.append(NPC("sterling_hq", "Sterling Vance", "CEO, Apex Dynamics [Visionary]", 12 * TILE_SIZE, 5 * TILE_SIZE, (72, 202, 228)))
    # Elena Rostova (Lead AI Architect)
    m.npcs.append(NPC("elena", "Elena Rostova", "Lead AI Silicon Architect", 6 * TILE_SIZE, 9 * TILE_SIZE + 4, (180, 100, 240)))
    # Mark Chen (Powertrain Engineer)
    m.npcs.append(NPC("mark_chen", "Mark Chen", "Solid-State Powertrain Lead", 19 * TILE_SIZE, 9 * TILE_SIZE + 4, (46, 196, 182)))

    return m


# -----------------------------------------------------------------
# 8. TITAN CAPITAL MERCHANT BANK HQ
# -----------------------------------------------------------------
def build_titan_hq_interior() -> LocationMap:
    m = create_interior_shell(INTERIOR_TITAN_HQ, "Titan Capital Global Merchant Bank HQ", 26, 16, floor_tile=3)

    # Executive M&A Conference Table center
    conf_table = pygame.Rect(9 * TILE_SIZE, 4 * TILE_SIZE, 8 * TILE_SIZE, 3 * TILE_SIZE)
    m.solids.append(conf_table)

    m.objects.append(WorldObject(
        "titn_ma_dossier", "ledger", 11 * TILE_SIZE, 4 * TILE_SIZE, 4 * TILE_SIZE, 2 * TILE_SIZE,
        "Confidential Cross-Border M&A Memo",
        "Lead underwriter advisory agreement on a $24B acquisition generating $180M advisory fees. (Clue: titn_ma_deal).",
        action_type="inspect"
    ))

    # Treasury & Debt Underwriting Desk left
    treasury_desk = pygame.Rect(3 * TILE_SIZE, 4 * TILE_SIZE, 4 * TILE_SIZE, 2 * TILE_SIZE)
    m.solids.append(treasury_desk)

    m.objects.append(WorldObject(
        "titn_treasury_terminal", "terminal", 3 * TILE_SIZE, 4 * TILE_SIZE, 4 * TILE_SIZE, 2 * TILE_SIZE,
        "Global Treasury Repo Terminal",
        "Net interest margin audit indicating 280 bps spread on short-dated liquidity. (Clue: titn_nim_margin).",
        action_type="inspect"
    ))

    # Credit Risk Audit Bookshelf right
    risk_shelf = pygame.Rect(19 * TILE_SIZE, 4 * TILE_SIZE, 4 * TILE_SIZE, 2 * TILE_SIZE)
    m.solids.append(risk_shelf)

    m.objects.append(WorldObject(
        "titn_risk_shelf", "screen", 19 * TILE_SIZE, 4 * TILE_SIZE, 4 * TILE_SIZE, 2 * TILE_SIZE,
        "Credit Risk & Non-Performing Loan Audit",
        "Quarterly stress test showing rising provisions on metropolitan commercial debt. (Clue: titn_credit_risk).",
        action_type="inspect"
    ))

    # NPCs
    m.npcs.append(NPC("evelyn", "Evelyn Sterling", "Managing Director, M&A Syndicate", 13 * TILE_SIZE, 8 * TILE_SIZE, (218, 165, 32)))
    m.npcs.append(NPC("marcus_v", "Marcus Vance", "Senior Underwriter", 5 * TILE_SIZE, 7 * TILE_SIZE, (72, 202, 228)))
    m.npcs.append(NPC("chloe", "Chloe Bennett", "Lead Credit Risk Auditor", 21 * TILE_SIZE, 7 * TILE_SIZE, (230, 57, 70)))

    return m


# -----------------------------------------------------------------
# 9. MONSOON GLOBAL GOODS HERITAGE TRADING HOUSE
# -----------------------------------------------------------------
def build_monsoon_hq_interior() -> LocationMap:
    m = create_interior_shell(INTERIOR_MONSOON_HQ, "Monsoon Global Goods Heritage Trading House", 26, 16, floor_tile=3)

    # Assam & Darjeeling Tea Tasting Bar center
    tasting_bar = pygame.Rect(8 * TILE_SIZE, 4 * TILE_SIZE, 10 * TILE_SIZE, 2 * TILE_SIZE)
    m.solids.append(tasting_bar)

    m.objects.append(WorldObject(
        "monsoon_tasting_counter", "counter", 10 * TILE_SIZE, 4 * TILE_SIZE, 6 * TILE_SIZE, 2 * TILE_SIZE,
        "Estate Tea Cupping & Blend Counter",
        "Fresh harvest evaluation logs show specialty tea output rose 18%, dropping input costs across 200 hubs. (Clue: chai_harvest_record).",
        action_type="inspect"
    ))

    # Burlap Spice Sacks & Export Stacks left
    burlap_stacks = pygame.Rect(3 * TILE_SIZE, 4 * TILE_SIZE, 3 * TILE_SIZE, 4 * TILE_SIZE)
    m.solids.append(burlap_stacks)

    m.objects.append(WorldObject(
        "monsoon_spice_sacks", "landmark", 3 * TILE_SIZE, 4 * TILE_SIZE, 3 * TILE_SIZE, 4 * TILE_SIZE,
        "Export-Grade Spices & Tea Canisters",
        "Aromatic cardamom, black pepper, and premium CTC tea ready for containerized shipment.",
        action_type="inspect"
    ))

    # Maritime Container Route Wall Map right
    shipping_map = pygame.Rect(20 * TILE_SIZE, 3 * TILE_SIZE, 4 * TILE_SIZE, 24)
    m.objects.append(WorldObject(
        "monsoon_shipping_map", "screen", 20 * TILE_SIZE, 3 * TILE_SIZE, 4 * TILE_SIZE, 24,
        "Indian Ocean Maritime Shipping Route Map",
        "Logistics chart confirming 3-year fixed-rate freight charters shielding Monsoon from spot surges. (Clue: chai_shipping_reroute).",
        action_type="inspect"
    ))

    # NPCs
    m.npcs.append(NPC("anand", "Anand Singhania", "Founder & Master Tea Blender", 13 * TILE_SIZE, 7 * TILE_SIZE, (218, 165, 32)))
    m.npcs.append(NPC("meera", "Meera Sen", "Global Supply Chain Director", 21 * TILE_SIZE, 6 * TILE_SIZE, (46, 196, 182)))
    m.npcs.append(NPC("rajiv", "Rajiv Patel", "Commodities Buyer & ASEAN Liaison", 5 * TILE_SIZE, 9 * TILE_SIZE, (245, 140, 50)))

    return m


# -----------------------------------------------------------------
# 10. TOKYO STOCK EXCHANGE (TSE) TRADING FLOOR
# -----------------------------------------------------------------
def build_tse_trading_floor() -> LocationMap:
    m = create_interior_shell(INTERIOR_TSE, "Tokyo Stock Exchange (TSE) — Arrows Arena", 26, 16, floor_tile=1)

    # Arrows Glass Cylinder Ring center
    ring_left = pygame.Rect(9 * TILE_SIZE, 5 * TILE_SIZE, 2 * TILE_SIZE, 4 * TILE_SIZE)
    ring_right = pygame.Rect(15 * TILE_SIZE, 5 * TILE_SIZE, 2 * TILE_SIZE, 4 * TILE_SIZE)
    ring_top = pygame.Rect(11 * TILE_SIZE, 4 * TILE_SIZE, 4 * TILE_SIZE, 2 * TILE_SIZE)
    m.solids.extend([ring_left, ring_right, ring_top])

    # Interactive TSE Trading Console
    m.objects.append(WorldObject(
        "tse_trading_console", "terminal", 11 * TILE_SIZE, 4 * TILE_SIZE, 4 * TILE_SIZE, 2 * TILE_SIZE,
        "Tokyo Arrows Order Routing Terminal",
        "Trade Nikkei 225 & TOPIX listed equities directly on the Kabutocho trading floor.",
        action_type="open_trading"
    ))

    # Circular LED Stock Ring overhead
    m.objects.append(WorldObject(
        "tse_ticker_ring", "screen", 8 * TILE_SIZE, 1 * TILE_SIZE, 10 * TILE_SIZE, 24,
        "Tokyo Stock Exchange 360° Circular Chandelier Display",
        "High-frequency Japanese equities ticker and foreign exchange quotes (USD/JPY).",
        action_type="inspect"
    ))

    # NPCs
    m.npcs.append(NPC("kenji", "Kenji Sato", "Chief Equity Strategist", 13 * TILE_SIZE, 7 * TILE_SIZE, (46, 196, 182)))
    m.npcs.append(NPC("aoi", "Aoi Tanaka", "Semiconductor Industry Analyst", 6 * TILE_SIZE, 8 * TILE_SIZE, (180, 100, 240)))

    return m


# -----------------------------------------------------------------
# 11. LONDON STOCK EXCHANGE (LSE) TRADING FLOOR
# -----------------------------------------------------------------
def build_lse_trading_floor() -> LocationMap:
    m = create_interior_shell(INTERIOR_LSE, "London Stock Exchange (LSE) — The Source Arena", 26, 16, floor_tile=1)

    # "The Source" Kinetic Sculpture center
    source_monument = pygame.Rect(11 * TILE_SIZE, 4 * TILE_SIZE, 4 * TILE_SIZE, 4 * TILE_SIZE)
    m.solids.append(source_monument)

    m.objects.append(WorldObject(
        "lse_source", "landmark", 11 * TILE_SIZE, 4 * TILE_SIZE, 4 * TILE_SIZE, 4 * TILE_SIZE,
        "'The Source' Kinetic Glass Globe Monument",
        "A mesmerizing 9-meter kinetic sculpture of moving glass spheres reflecting live FTSE market movements.",
        action_type="inspect"
    ))

    # Interactive LSE Trading Desk
    m.solids.append(pygame.Rect(5 * TILE_SIZE, 5 * TILE_SIZE, 4 * TILE_SIZE, 2 * TILE_SIZE))
    m.objects.append(WorldObject(
        "lse_trading_console", "terminal", 5 * TILE_SIZE, 5 * TILE_SIZE, 4 * TILE_SIZE, 2 * TILE_SIZE,
        "LSE Turquoise International Trading Console",
        "Trade FTSE 100 and European equities with ultra-low latency.",
        action_type="open_trading"
    ))

    # Historic Timber Board right
    m.objects.append(WorldObject(
        "lse_timber_board", "screen", 18 * TILE_SIZE, 2 * TILE_SIZE, 6 * TILE_SIZE, 24,
        "Historic 1801 London Stock Board",
        "Lists sovereign gilts, merchant banking trusts, and North Sea commodity benchmarks.",
        action_type="inspect"
    ))

    # NPCs
    m.npcs.append(NPC("alistair", "Alistair Finch", "Senior Gilts & Sterling Trader", 7 * TILE_SIZE, 8 * TILE_SIZE, (218, 165, 32)))
    m.npcs.append(NPC("beatrice", "Beatrice Montgomery", "Global Energy & Mining Strategist", 18 * TILE_SIZE, 8 * TILE_SIZE, (72, 202, 228)))

    return m


# -----------------------------------------------------------------
# 12. NOVA CLOUD SYSTEMS — SOVEREIGN DATA CENTER & ENTERPRISE HQ
# -----------------------------------------------------------------
def build_nova_hq_interior() -> LocationMap:
    m = create_interior_shell(INTERIOR_NOVA_HQ, "Nova Cloud Systems — Sovereign Data Center & Enterprise HQ", 28, 18, floor_tile=1)

    # 1. Quantum Server Corridor Left (x: 2..8, y: 3..7)
    server_bank = pygame.Rect(3 * TILE_SIZE, 3 * TILE_SIZE, 6 * TILE_SIZE, 5 * TILE_SIZE)
    m.solids.append(server_bank)
    m.objects.append(WorldObject(
        "nova_quantum_servers", "terminal", 3 * TILE_SIZE, 3 * TILE_SIZE, 6 * TILE_SIZE, 5 * TILE_SIZE,
        "Quantum Cloud Distributed Compute Mesh",
        "Ultra-dense cryogenically cooled sovereign server racks hosting enterprise SaaS databases. (Clue: nova_quantum_mesh)",
        action_type="inspect"
    ))

    # 2. Cybersecurity Threat Operations Wall Right (x: 18..24, y: 3..7)
    cyber_wall = pygame.Rect(18 * TILE_SIZE, 3 * TILE_SIZE, 6 * TILE_SIZE, 5 * TILE_SIZE)
    m.solids.append(cyber_wall)
    m.objects.append(WorldObject(
        "nova_cyber_dashboard", "screen", 18 * TILE_SIZE, 3 * TILE_SIZE, 6 * TILE_SIZE, 5 * TILE_SIZE,
        "Sovereign Cyber Defense Operations Wall",
        "Live visual telemetry of global zero-trust threat mitigation with 99.999% uptime.",
        action_type="inspect"
    ))

    # 3. Executive Enterprise Contracts Desk Top Center (x: 11..16, y: 2..5)
    contracts_desk = pygame.Rect(11 * TILE_SIZE, 3 * TILE_SIZE, 6 * TILE_SIZE, 2 * TILE_SIZE)
    m.solids.append(contracts_desk)
    m.objects.append(WorldObject(
        "nova_enterprise_contract", "ledger", 11 * TILE_SIZE, 3 * TILE_SIZE, 6 * TILE_SIZE, 2 * TILE_SIZE,
        "Institutional Enterprise Cloud Contract Ledger",
        "Confidential multi-year federal sovereign database contracts yielding $620M ARR. (Clue: nova_gov_contract)",
        action_type="inspect"
    ))

    # NPCs
    m.npcs.append(NPC("maya_lin", "Maya Lin", "Chief Technology Officer", 6 * TILE_SIZE, 9 * TILE_SIZE, (72, 202, 228)))
    m.npcs.append(NPC("samuel_ross", "Samuel Ross", "Enterprise Sales Director", 21 * TILE_SIZE, 9 * TILE_SIZE, (100, 140, 210)))

    return m


# -----------------------------------------------------------------
# 13. AURUM CLEAN ENERGY — RENEWABLE GRID & PEROVSKITE LABS HQ
# -----------------------------------------------------------------
def build_aura_hq_interior() -> LocationMap:
    m = create_interior_shell(INTERIOR_AURA_HQ, "Aurum Clean Energy — Renewable Grid & Perovskite Labs HQ", 28, 18, floor_tile=3)

    # 1. Perovskite Solar Materials Lab Left (x: 3..8, y: 3..7)
    solar_lab = pygame.Rect(3 * TILE_SIZE, 3 * TILE_SIZE, 6 * TILE_SIZE, 5 * TILE_SIZE)
    m.solids.append(solar_lab)
    m.objects.append(WorldObject(
        "aura_perovskite_bench", "terminal", 3 * TILE_SIZE, 3 * TILE_SIZE, 6 * TILE_SIZE, 5 * TILE_SIZE,
        "Gen-3 Perovskite Solar Wafer Bench",
        "Certified laboratory testing unit confirming 29.4% sunlight-to-energy conversion efficiency. (Clue: aura_perovskite_efficiency)",
        action_type="inspect"
    ))

    # 2. AuraGrid Megawatt Storage Prototype Right (x: 18..24, y: 3..7)
    battery_bay = pygame.Rect(18 * TILE_SIZE, 3 * TILE_SIZE, 6 * TILE_SIZE, 5 * TILE_SIZE)
    m.solids.append(battery_bay)
    m.objects.append(WorldObject(
        "aura_megawatt_battery", "landmark", 18 * TILE_SIZE, 3 * TILE_SIZE, 6 * TILE_SIZE, 5 * TILE_SIZE,
        "AuraGrid Megawatt Storage Prototype",
        "Utility-scale lithium-iron storage container engineered to drop levelized cost to $68/kWh. (Clue: aura_battery_margin)",
        action_type="inspect"
    ))

    # 3. National Clean Energy Grid Dispatch Map Top Center (x: 11..16, y: 2..5)
    grid_map_rect = pygame.Rect(11 * TILE_SIZE, 3 * TILE_SIZE, 6 * TILE_SIZE, 2 * TILE_SIZE)
    m.solids.append(grid_map_rect)
    m.objects.append(WorldObject(
        "aura_grid_map", "screen", 11 * TILE_SIZE, 3 * TILE_SIZE, 6 * TILE_SIZE, 2 * TILE_SIZE,
        "National Clean Energy Grid Interconnection Map",
        "Telemetric display showing regional renewable energy dispatch and state tariff subsidies.",
        action_type="inspect"
    ))

    # NPCs
    m.npcs.append(NPC("dr_joshi", "Dr. Vikram Joshi", "Chief Materials Scientist", 6 * TILE_SIZE, 9 * TILE_SIZE, (46, 196, 182)))
    m.npcs.append(NPC("radhika", "Radhika Roy", "Grid Operations VP", 21 * TILE_SIZE, 9 * TILE_SIZE, (255, 183, 3)))

    return m


# -----------------------------------------------------------------
# 14. MEDIX SYNTHETICS — PRECISION ONCOLOGY & GENOMICS CENTER
# -----------------------------------------------------------------
def build_medx_hq_interior() -> LocationMap:
    m = create_interior_shell(INTERIOR_MEDX_HQ, "Medix Synthetics — Precision Oncology & Genomics Center", 28, 18, floor_tile=1)

    # 1. Molecular Genomics DNA Sequencer Left (x: 3..8, y: 3..7)
    sequencer_bench = pygame.Rect(3 * TILE_SIZE, 3 * TILE_SIZE, 6 * TILE_SIZE, 5 * TILE_SIZE)
    m.solids.append(sequencer_bench)
    m.objects.append(WorldObject(
        "medx_dna_sequencer", "terminal", 3 * TILE_SIZE, 3 * TILE_SIZE, 6 * TILE_SIZE, 5 * TILE_SIZE,
        "Ultra-High-Throughput Synthetic DNA Sequencer",
        "Robotic sequencer synthesizing precision monoclonal peptide vectors for targeted cancer therapies.",
        action_type="inspect"
    ))

    # 2. Oncology Phase-3 Trial Results Right (x: 18..24, y: 3..7)
    trial_desk = pygame.Rect(18 * TILE_SIZE, 3 * TILE_SIZE, 6 * TILE_SIZE, 5 * TILE_SIZE)
    m.solids.append(trial_desk)
    m.objects.append(WorldObject(
        "medx_trial_dossier", "ledger", 18 * TILE_SIZE, 3 * TILE_SIZE, 6 * TILE_SIZE, 5 * TILE_SIZE,
        "Phase-3 OncoSyn Clinical Trial Results Dossier",
        "Audited multicenter trial data demonstrating 84% objective solid tumor regression. (Clue: medx_phase3_oncology)",
        action_type="inspect"
    ))

    # 3. Cryogenic Bio-Vault Top Center (x: 11..16, y: 2..5)
    vault_rect = pygame.Rect(11 * TILE_SIZE, 3 * TILE_SIZE, 6 * TILE_SIZE, 2 * TILE_SIZE)
    m.solids.append(vault_rect)
    m.objects.append(WorldObject(
        "medx_cryo_vault", "landmark", 11 * TILE_SIZE, 3 * TILE_SIZE, 6 * TILE_SIZE, 2 * TILE_SIZE,
        "Cryogenic Monoclonal Peptide Storage Vault",
        "Secure cold-chain bio-vault storing temperature-sensitive synthetic gene delivery therapeutics. (Clue: medx_fda_expedited)",
        action_type="inspect"
    ))

    # NPCs
    m.npcs.append(NPC("dr_thorne", "Dr. Aris Thorne", "Chief Genomics Scientist", 6 * TILE_SIZE, 9 * TILE_SIZE, (230, 80, 110)))
    m.npcs.append(NPC("kavita", "Kavita Rao", "Clinical Trials Director", 21 * TILE_SIZE, 9 * TILE_SIZE, (180, 100, 220)))

    return m

