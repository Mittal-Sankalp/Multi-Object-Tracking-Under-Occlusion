"""
MarketQuest - Enhanced Game World, Tilemaps, Buildings & Landmark Interactions
Renders Wall Street (New York) and Dalal Street (Mumbai) with detailed architecture,
decorations, street furniture, landmarks, NPCs, and distinct interactive building hubs.
"""

import pygame
import math
from typing import Dict, List, Tuple, Optional, Any
from config import (
    TILE_SIZE, VIRTUAL_WIDTH, VIRTUAL_HEIGHT, SPRITES_DIR,
    COLOR_BG_DARK, COLOR_PANEL_BG, COLOR_BORDER, COLOR_BORDER_ACCENT,
    COLOR_TEXT_WHITE, COLOR_TEXT_GOLD, COLOR_GAIN, COLOR_LOSS_BRIGHT,
    LOCATION_WALL_STREET, LOCATION_DALAL_STREET, LOCATION_KABUTOCHO, LOCATION_LONDON,
    INTERIOR_BSE, INTERIOR_NYSE, INTERIOR_TSE, INTERIOR_LSE,
    INTERIOR_BANK, INTERIOR_LIBRARY, INTERIOR_WHITE_HOUSE, INTERIOR_PARLIAMENT,
    INTERIOR_APEX_HQ, INTERIOR_TITAN_HQ, INTERIOR_MONSOON_HQ,
    INTERIOR_NOVA_HQ, INTERIOR_AURA_HQ, INTERIOR_MEDX_HQ
)

class NPC:
    def __init__(self, npc_id: str, name: str, title: str, x: float, y: float, 
                 avatar_color: Tuple[int, int, int], dialogue_id: str = "start"):
        self.id = npc_id
        self.name = name
        self.title = title
        self.x = float(x)
        self.y = float(y)
        self.width = 16
        self.height = 24
        self.avatar_color = avatar_color
        self.dialogue_id = dialogue_id
        self.facing = "down"
        self.sprite: Optional[pygame.Surface] = None
        self._load_sprite()

    def _load_sprite(self):
        try:
            sp = SPRITES_DIR / f"npc_{self.id}.png"
            if sp.exists():
                self.sprite = pygame.image.load(str(sp)).convert_alpha()
        except Exception:
            self.sprite = None

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[int, int]):
        rx = int(self.x - camera_offset[0])
        ry = int(self.y - camera_offset[1])

        if self.sprite:
            surface.blit(self.sprite, (rx, ry))
            return

        # Procedural fallback
        shadow = pygame.Rect(rx + 2, ry + self.height - 4, self.width - 4, 4)
        pygame.draw.ellipse(surface, (8, 12, 22), shadow)

        body = pygame.Rect(rx + 2, ry + 8, self.width - 4, 10)
        pygame.draw.rect(surface, self.avatar_color, body, border_radius=2)

        head = pygame.Rect(rx + 3, ry + 2, self.width - 6, 7)
        pygame.draw.rect(surface, (245, 195, 150), head)
        hair = pygame.Rect(rx + 3, ry + 1, self.width - 6, 3)
        pygame.draw.rect(surface, (50, 40, 35), hair)

        pygame.draw.rect(surface, (20, 25, 40), (rx + 3, ry + 18, 4, 6))
        pygame.draw.rect(surface, (20, 25, 40), (rx + self.width - 7, ry + 18, 4, 6))


class WorldObject:
    def __init__(self, obj_id: str, obj_type: str, x: float, y: float, w: int, h: int, 
                 title: str, text: str = "", target_loc: Optional[str] = None,
                 action_type: str = "sign", target_symbol: str = "",
                 target_interior: Optional[str] = None):
        self.id = obj_id
        self.type = obj_type  # "building", "sign", "transit", "bull_statue", "landmark", "chai_stall", "deco", "door", "terminal"
        self.x = float(x)
        self.y = float(y)
        self.w = w
        self.h = h
        self.title = title
        self.text = text
        self.target_loc = target_loc
        self.action_type = action_type  # "enter_interior", "exit_interior", "open_trading", "open_academy", "company_dossier", "exchange_hub", "bank", "bull", "banyan", "chai", "news", "transit"
        self.target_symbol = target_symbol  # e.g. "APEX", "TITN"
        self.target_interior = target_interior

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)


class LocationMap:
    def __init__(self, map_id: str, name: str, width_tiles: int, height_tiles: int):
        self.id = map_id
        self.name = name
        self.width_tiles = width_tiles
        self.height_tiles = height_tiles
        self.pixel_width = width_tiles * TILE_SIZE
        self.pixel_height = height_tiles * TILE_SIZE

        # Tile grid: 0: asphalt road, 1: sidewalk, 2: grass park, 3: sandstone, 4: cobblestone
        self.tiles = [[1 for _ in range(width_tiles)] for _ in range(height_tiles)]
        self.solids: List[pygame.Rect] = []
        self.npcs: List[NPC] = []
        self.objects: List[WorldObject] = []
        self.spawn_points: Dict[str, Tuple[float, float]] = {}

    @property
    def width(self) -> int:
        return self.width_tiles

    @property
    def height(self) -> int:
        return self.height_tiles

    def is_solid(self, rect: pygame.Rect) -> bool:
        # Map borders: keep collision box safely within valid map pixels
        if rect.left < 0 or rect.right > self.pixel_width or rect.top < 0 or rect.bottom > self.pixel_height:
            return True
        for s in self.solids:
            if rect.colliderect(s):
                return True
        for npc in self.npcs:
            if rect.colliderect(npc.rect):
                return True
        return False


def build_wall_street_map() -> LocationMap:
    """Build Wall Street Financial District."""
    m = LocationMap(LOCATION_WALL_STREET, "Wall Street, New York", 38, 28)

    # 1. Tile Ground Layout
    for y in range(m.height_tiles):
        for x in range(m.width_tiles):
            if 11 <= y <= 15:
                m.tiles[y][x] = 0  # Asphalt Road
            elif 18 <= y <= 25 and 9 <= x <= 25:
                m.tiles[y][x] = 2  # Bowling Green Park Plaza (Grass)
            elif (y == 10 or y == 16) and (x % 3 == 0):
                m.tiles[y][x] = 4  # Cobblestone crosswalk accents
            else:
                m.tiles[y][x] = 1  # Granite Sidewalk

    # 2. Buildings & Colliders
    # NYSE (New York Stock Exchange) top center (x: 10..22, y: 1..7)
    nyse_rect = pygame.Rect(10 * TILE_SIZE, 1 * TILE_SIZE, 13 * TILE_SIZE, 7 * TILE_SIZE)
    m.solids.append(nyse_rect)
    m.objects.append(WorldObject(
        "hub_nyse", "building", 15 * TILE_SIZE, 7 * TILE_SIZE, 3 * TILE_SIZE, 24,
        "New York Stock Exchange (NYSE)",
        "Step inside the world's most prestigious equity trading floor. View market status, indices, and execute trades.",
        action_type="enter_interior", target_interior=INTERIOR_NYSE
    ))

    # Apex Dynamics Tech Tower top right (x: 25..35, y: 1..7)
    apex_rect = pygame.Rect(25 * TILE_SIZE, 1 * TILE_SIZE, 11 * TILE_SIZE, 7 * TILE_SIZE)
    m.solids.append(apex_rect)
    m.objects.append(WorldObject(
        "hq_apex", "building", 29 * TILE_SIZE, 7 * TILE_SIZE, 3 * TILE_SIZE, 24,
        "Apex Dynamics Global HQ",
        "Step inside the Autonomous Systems Lab. Inspect prototypes and interview AI engineers.",
        action_type="enter_interior", target_symbol="APEX", target_interior=INTERIOR_APEX_HQ
    ))

    # Titan Capital Bank top left (x: 1..8, y: 1..7)
    titn_rect = pygame.Rect(1 * TILE_SIZE, 1 * TILE_SIZE, 8 * TILE_SIZE, 7 * TILE_SIZE)
    m.solids.append(titn_rect)
    m.objects.append(WorldObject(
        "hq_titn", "building", 4 * TILE_SIZE, 7 * TILE_SIZE, 2 * TILE_SIZE, 24,
        "Titan Capital Merchant Bank HQ",
        "Step inside the executive merchant banking suite. Inspect M&A deals and underwriting books.",
        action_type="enter_interior", target_symbol="TITN", target_interior=INTERIOR_TITAN_HQ
    ))

    # Wall St Financial Academy / Library bottom left (x: 1..7, y: 19..25)
    academy_rect = pygame.Rect(1 * TILE_SIZE, 19 * TILE_SIZE, 7 * TILE_SIZE, 7 * TILE_SIZE)
    m.solids.append(academy_rect)
    m.objects.append(WorldObject(
        "bldg_academy", "building", 3 * TILE_SIZE, 18 * TILE_SIZE, 3 * TILE_SIZE, 24,
        "Wall Street Investor Academy & Library",
        "Step inside the research library. Study value investing, P/E ratios, and macro indicators.",
        action_type="enter_interior", target_interior=INTERIOR_LIBRARY
    ))

    # Nova Cloud Systems Tower bottom left-center (x: 8..13, y: 19..25)
    nova_rect = pygame.Rect(8 * TILE_SIZE, 19 * TILE_SIZE, 6 * TILE_SIZE, 7 * TILE_SIZE)
    m.solids.append(nova_rect)
    m.objects.append(WorldObject(
        "hq_nova", "building", 10 * TILE_SIZE, 18 * TILE_SIZE, 2 * TILE_SIZE, 24,
        "Nova Cloud Systems Tower",
        "Step inside the quantum datacenter and cloud operations center. Inspect uptime, server blades, and government cloud contracts.",
        action_type="enter_interior", target_symbol="NOVA", target_interior=INTERIOR_NOVA_HQ
    ))

    # The White House & Policy Bureau bottom right (x: 27..36, y: 19..25)
    wh_rect = pygame.Rect(27 * TILE_SIZE, 19 * TILE_SIZE, 9 * TILE_SIZE, 7 * TILE_SIZE)
    m.solids.append(wh_rect)
    m.objects.append(WorldObject(
        "bldg_white_house", "building", 30 * TILE_SIZE, 18 * TILE_SIZE, 3 * TILE_SIZE, 24,
        "The White House Briefing Suite",
        "Step inside the executive briefing room to review national economic orders and trade policy.",
        action_type="enter_interior", target_interior=INTERIOR_WHITE_HOUSE
    ))

    # 3. Bowling Green Plaza & Charging Bull Monument (x: 15..18, y: 20..22)
    bull_rect = pygame.Rect(15 * TILE_SIZE, 20 * TILE_SIZE, 4 * TILE_SIZE, 2 * TILE_SIZE)
    m.solids.append(bull_rect)
    m.objects.append(WorldObject(
        "bull_statue", "bull_statue", 15 * TILE_SIZE, 20 * TILE_SIZE, 4 * TILE_SIZE, 2 * TILE_SIZE,
        "Charging Bull Monument",
        "A monumental bronze sculpture symbolizing financial resilience, aggressive market optimism, and economic power.",
        action_type="bull_statue"
    ))

    # 4. Wall Street Transit / Subway Station (x: 23, y: 9)
    m.objects.append(WorldObject(
        "transit_mumbai", "transit", 23 * TILE_SIZE, 9 * TILE_SIZE, 28, 28,
        "Wall St Express Transit Portal",
        "High-speed international financial transit linking New York and Dalal Street, Mumbai.",
        target_loc=LOCATION_DALAL_STREET, action_type="transit"
    ))

    # 5. Street Furniture & Informational Signs
    m.objects.append(WorldObject(
        "sign_nyse", "sign", 13 * TILE_SIZE, 8 * TILE_SIZE + 4, 18, 18,
        "Wall Street Financial Landmark Plaque",
        "Wall Street: Established under the Buttonwood Agreement in 1792. Center of global capital liquidity.",
        action_type="sign"
    ))
    m.objects.append(WorldObject(
        "sign_bull", "sign", 13 * TILE_SIZE, 21 * TILE_SIZE, 18, 18,
        "Bowling Green Plaza Marker",
        "Bowling Green: New York's oldest public park. Home to the iconic Charging Bull.",
        action_type="sign"
    ))

    # 6. NPCs
    # Arthur Pendelton (Mentor) near NYSE
    m.npcs.append(NPC("arthur", "Arthur Pendelton", "Veteran Value Investor", 14 * TILE_SIZE, 8 * TILE_SIZE + 8, (218, 165, 32)))
    # Sterling Vance (Apex CEO) outside Apex HQ
    m.npcs.append(NPC("sterling", "Sterling Vance", "CEO, Apex Dynamics", 28 * TILE_SIZE, 8 * TILE_SIZE + 8, (72, 202, 228)))
    # Victoria Vance (Analyst) near Plaza
    m.npcs.append(NPC("victoria", "Victoria Vance", "Chief Market Strategist", 11 * TILE_SIZE, 17 * TILE_SIZE, (180, 100, 240)))
    # Floor Trader Charlie near Brokerage
    m.npcs.append(NPC("charlie", "Floor Trader Charlie", "Pit Arbitrageur", 21 * TILE_SIZE, 8 * TILE_SIZE + 8, (220, 180, 50)))

    m.spawn_points["default"] = (16 * TILE_SIZE, 10 * TILE_SIZE)
    m.spawn_points["from_transit"] = (23 * TILE_SIZE, 11 * TILE_SIZE)
    return m


def build_dalal_street_map() -> LocationMap:
    """Build Dalal Street Financial District."""
    m = LocationMap(LOCATION_DALAL_STREET, "Dalal Street, Mumbai", 38, 28)

    # 1. Tile Ground Layout
    for y in range(m.height_tiles):
        for x in range(m.width_tiles):
            if 11 <= y <= 15:
                m.tiles[y][x] = 0  # Main Street
            elif 18 <= y <= 25 and 10 <= x <= 24:
                m.tiles[y][x] = 4  # Historic Banyan Tree Plaza (Warm Cobblestone)
            else:
                m.tiles[y][x] = 3  # Sandstone Paving

    # 2. Buildings & Colliders
    # BSE Towers (Phiroze Jeejeebhoy Towers) top center (x: 10..22, y: 1..7)
    bse_rect = pygame.Rect(10 * TILE_SIZE, 1 * TILE_SIZE, 13 * TILE_SIZE, 7 * TILE_SIZE)
    m.solids.append(bse_rect)
    m.objects.append(WorldObject(
        "hub_bse", "building", 15 * TILE_SIZE, 7 * TILE_SIZE, 3 * TILE_SIZE, 24,
        "Bombay Stock Exchange (BSE)",
        "Step inside the historic BSE trading pit. Hear the bell, consult specialists, and trade Indian equities.",
        action_type="enter_interior", target_interior=INTERIOR_BSE
    ))

    # Monsoon Global Goods Headquarters top right (x: 25..35, y: 1..7)
    monsoon_rect = pygame.Rect(25 * TILE_SIZE, 1 * TILE_SIZE, 11 * TILE_SIZE, 7 * TILE_SIZE)
    m.solids.append(monsoon_rect)
    m.objects.append(WorldObject(
        "hq_chai", "building", 29 * TILE_SIZE, 7 * TILE_SIZE, 3 * TILE_SIZE, 24,
        "Monsoon Global Goods HQ",
        "Step inside the heritage trading house. Sample tea blends and interview supply chain heads.",
        action_type="enter_interior", target_symbol="CHAI", target_interior=INTERIOR_MONSOON_HQ
    ))

    # Aurum Clean Energy Headquarters top left (x: 1..8, y: 1..7)
    aurum_rect = pygame.Rect(1 * TILE_SIZE, 1 * TILE_SIZE, 8 * TILE_SIZE, 7 * TILE_SIZE)
    m.solids.append(aurum_rect)
    m.objects.append(WorldObject(
        "hq_aura", "building", 4 * TILE_SIZE, 7 * TILE_SIZE, 2 * TILE_SIZE, 24,
        "Aurum Clean Energy HQ",
        "Step inside the solar research pavilion and smart grid dispatch center. Inspect perovskite patents and mega-battery contracts.",
        action_type="enter_interior", target_symbol="AURA", target_interior=INTERIOR_AURA_HQ
    ))

    # State Financial Bank of Dalal Street bottom left (x: 1..6, y: 19..25)
    bank_rect = pygame.Rect(1 * TILE_SIZE, 19 * TILE_SIZE, 6 * TILE_SIZE, 7 * TILE_SIZE)
    m.solids.append(bank_rect)
    m.objects.append(WorldObject(
        "bank_dalal", "building", 3 * TILE_SIZE, 18 * TILE_SIZE, 2 * TILE_SIZE, 24,
        "Dalal Street Commercial Banking Center",
        "Step inside the banking hall. Inspect vaults, cash balance, and commercial credit.",
        action_type="enter_interior", target_interior=INTERIOR_BANK
    ))

    # Medix Synthetics Bio-Tech Center bottom left-center (x: 8..13, y: 19..25)
    medx_rect = pygame.Rect(8 * TILE_SIZE, 19 * TILE_SIZE, 6 * TILE_SIZE, 7 * TILE_SIZE)
    m.solids.append(medx_rect)
    m.objects.append(WorldObject(
        "hq_medx", "building", 10 * TILE_SIZE, 18 * TILE_SIZE, 2 * TILE_SIZE, 24,
        "Medix Synthetics Bio-Tech Center",
        "Step inside the genomics lab and clinical pharmacology vault. Inspect FDA Phase-3 trial records and synthetic oncology patents.",
        action_type="enter_interior", target_symbol="MEDX", target_interior=INTERIOR_MEDX_HQ
    ))

    # Parliament of India Liaison Pavilion bottom right-center (x: 20..25, y: 19..25)
    parl_rect = pygame.Rect(20 * TILE_SIZE, 19 * TILE_SIZE, 6 * TILE_SIZE, 7 * TILE_SIZE)
    m.solids.append(parl_rect)
    m.objects.append(WorldObject(
        "bldg_parliament", "building", 22 * TILE_SIZE, 18 * TILE_SIZE, 2 * TILE_SIZE, 24,
        "Parliament of India Liaison Pavilion",
        "Step inside the parliamentary committee chambers to review fiscal budgets, energy mandates, and national policy directives.",
        action_type="enter_interior", target_interior=INTERIOR_PARLIAMENT
    ))

    # Dalal Press Bureau bottom right (x: 27..36, y: 19..25)
    press_rect = pygame.Rect(27 * TILE_SIZE, 19 * TILE_SIZE, 10 * TILE_SIZE, 7 * TILE_SIZE)
    m.solids.append(press_rect)
    m.objects.append(WorldObject(
        "press_dalal", "building", 30 * TILE_SIZE, 18 * TILE_SIZE, 3 * TILE_SIZE, 24,
        "Dalal Street Financial Press Bureau",
        "Read breaking Mumbai news wires, monsoon economic forecasts, and corporate disclosures.",
        action_type="news_station"
    ))

    # 3. Historic 1875 Banyan Tree Landmark (x: 15..19, y: 19..23)
    banyan_rect = pygame.Rect(15 * TILE_SIZE, 19 * TILE_SIZE, 4 * TILE_SIZE, 4 * TILE_SIZE)
    m.solids.append(banyan_rect)
    m.objects.append(WorldObject(
        "banyan_tree", "landmark", 15 * TILE_SIZE, 19 * TILE_SIZE, 4 * TILE_SIZE, 4 * TILE_SIZE,
        "Historic 1875 Banyan Tree Plaza",
        "In 1875, five stockbrokers began gathering under this majestic banyan tree, eventually founding the Bombay Stock Exchange.",
        action_type="banyan_tree"
    ))

    # 4. Cutting Chai & Snack Stall (x: 13, y: 17)
    chai_rect = pygame.Rect(13 * TILE_SIZE, 17 * TILE_SIZE, 2 * TILE_SIZE, 2 * TILE_SIZE)
    m.solids.append(chai_rect)
    m.objects.append(WorldObject(
        "chai_stall", "chai_stall", 13 * TILE_SIZE, 17 * TILE_SIZE, 2 * TILE_SIZE, 2 * TILE_SIZE,
        "Chai Point & Floor Runner Corner",
        "Fresh steaming ginger-cardamom cutting chai! Floor runners gather here to trade informal market rumors.",
        action_type="chai_stall"
    ))

    # 5. International Transit Hub to Wall Street (x: 8, y: 9)
    m.objects.append(WorldObject(
        "transit_ny", "transit", 8 * TILE_SIZE, 9 * TILE_SIZE, 28, 28,
        "Dalal St Express Transit Portal",
        "High-speed international financial transit linking Dalal Street and Wall Street, New York.",
        target_loc=LOCATION_WALL_STREET, action_type="transit"
    ))

    # 6. Signs
    m.objects.append(WorldObject(
        "sign_bse", "sign", 14 * TILE_SIZE, 8 * TILE_SIZE + 4, 18, 18,
        "Dalal Street Historic Monument Plaque",
        "Dalal Street: The beating heart of Indian capitalism and the fastest-growing equity ecosystem in Asia.",
        action_type="sign"
    ))

    # 7. NPCs
    # Priya Sharma outside BSE
    m.npcs.append(NPC("priya", "Priya Sharma", "Dalal Street Financial Correspondent", 18 * TILE_SIZE, 8 * TILE_SIZE + 8, (245, 140, 50)))
    # Devendra Patel near Banyan Plaza
    m.npcs.append(NPC("devendra", "Devendra Patel", "Industrial Tycoon & Philanthropist", 12 * TILE_SIZE, 18 * TILE_SIZE, (46, 196, 182)))

    m.spawn_points["default"] = (16 * TILE_SIZE, 10 * TILE_SIZE)
    m.spawn_points["from_transit"] = (8 * TILE_SIZE, 11 * TILE_SIZE)
    return m


def build_kabutocho_map() -> LocationMap:
    """Build Kabutocho Financial District, Tokyo."""
    m = LocationMap(LOCATION_KABUTOCHO, "Kabutocho, Tokyo", 38, 28)

    # 1. Tile Ground Layout
    for y in range(m.height_tiles):
        for x in range(m.width_tiles):
            if 11 <= y <= 15:
                m.tiles[y][x] = 0  # Asphalt Road
            elif 18 <= y <= 25 and 10 <= x <= 24:
                m.tiles[y][x] = 2  # Zen Garden Plaza
            elif (y == 10 or y == 16) and (x % 3 == 0):
                m.tiles[y][x] = 4  # Granite Pavers
            else:
                m.tiles[y][x] = 1  # Sidewalk

    # 2. Buildings & Colliders
    # TSE Building (Tokyo Stock Exchange) top center (x: 10..22, y: 1..7)
    tse_rect = pygame.Rect(10 * TILE_SIZE, 1 * TILE_SIZE, 13 * TILE_SIZE, 7 * TILE_SIZE)
    m.solids.append(tse_rect)
    m.objects.append(WorldObject(
        "hub_tse", "building", 15 * TILE_SIZE, 7 * TILE_SIZE, 3 * TILE_SIZE, 24,
        "Tokyo Stock Exchange (TSE)",
        "Step inside the Arrows Arena of the Tokyo Stock Exchange. Home of the Nikkei 225.",
        action_type="enter_interior", target_interior=INTERIOR_TSE
    ))

    # Neo-Tokyo Tech Center top right (x: 25..35, y: 1..7)
    tech_rect = pygame.Rect(25 * TILE_SIZE, 1 * TILE_SIZE, 11 * TILE_SIZE, 7 * TILE_SIZE)
    m.solids.append(tech_rect)
    m.objects.append(WorldObject(
        "hq_tokyo_tech", "building", 29 * TILE_SIZE, 7 * TILE_SIZE, 3 * TILE_SIZE, 24,
        "Neo-Tokyo Advanced Robotics Center",
        "Inspect semiconductor fabrication agreements and industrial automation contracts.",
        action_type="company_dossier", target_symbol="APEX"
    ))

    # Kabutocho Merchant Bank top left (x: 1..8, y: 1..7)
    boj_rect = pygame.Rect(1 * TILE_SIZE, 1 * TILE_SIZE, 8 * TILE_SIZE, 7 * TILE_SIZE)
    m.solids.append(boj_rect)
    m.objects.append(WorldObject(
        "bank_tokyo", "building", 4 * TILE_SIZE, 7 * TILE_SIZE, 2 * TILE_SIZE, 24,
        "Kabutocho Merchant Bank",
        "Commercial yen liquidity and international clearing facilities.",
        action_type="enter_interior", target_interior=INTERIOR_BANK
    ))

    # Torii Gate / Historic Kabuto Shrine Landmark (x: 16..18, y: 20..22)
    torii_rect = pygame.Rect(16 * TILE_SIZE, 20 * TILE_SIZE, 3 * TILE_SIZE, 2 * TILE_SIZE)
    m.solids.append(torii_rect)
    m.objects.append(WorldObject(
        "torii_shrine", "landmark", 16 * TILE_SIZE, 20 * TILE_SIZE, 3 * TILE_SIZE, 2 * TILE_SIZE,
        "Kabuto Shrine Torii Monument",
        "A historic vermilion Torii gate where Tokyo stockbrokers have prayed for market fortune since 1878.",
        action_type="inspect"
    ))

    # Transit Portal (x: 8, y: 9)
    m.objects.append(WorldObject(
        "transit_tokyo", "transit", 8 * TILE_SIZE, 9 * TILE_SIZE, 28, 28,
        "Kabutocho Transit Portal",
        "High-speed international financial transit linking Tokyo to global exchanges.",
        target_loc=LOCATION_DALAL_STREET, action_type="transit"
    ))

    # NPCs
    m.npcs.append(NPC("kenji_ext", "Kenji Sato", "Chief Equity Strategist", 18 * TILE_SIZE, 8 * TILE_SIZE + 8, (46, 196, 182)))
    m.npcs.append(NPC("aoi_ext", "Aoi Tanaka", "Semiconductor Industry Analyst", 13 * TILE_SIZE, 17 * TILE_SIZE, (180, 100, 240)))

    m.spawn_points["default"] = (16 * TILE_SIZE, 10 * TILE_SIZE)
    m.spawn_points["from_transit"] = (8 * TILE_SIZE, 11 * TILE_SIZE)
    return m


def build_paternoster_square_map() -> LocationMap:
    """Build Paternoster Square Financial District, London."""
    m = LocationMap(LOCATION_LONDON, "Paternoster Square, London", 38, 28)

    # 1. Tile Ground Layout
    for y in range(m.height_tiles):
        for x in range(m.width_tiles):
            if 11 <= y <= 15:
                m.tiles[y][x] = 0  # London Cobblestone Road
            elif 18 <= y <= 25 and 10 <= x <= 24:
                m.tiles[y][x] = 4  # Paternoster Square Mosaic
            else:
                m.tiles[y][x] = 1  # Portland Stone Pavement

    # 2. Buildings & Colliders
    # LSE Building (London Stock Exchange) top center (x: 10..22, y: 1..7)
    lse_rect = pygame.Rect(10 * TILE_SIZE, 1 * TILE_SIZE, 13 * TILE_SIZE, 7 * TILE_SIZE)
    m.solids.append(lse_rect)
    m.objects.append(WorldObject(
        "hub_lse", "building", 15 * TILE_SIZE, 7 * TILE_SIZE, 3 * TILE_SIZE, 24,
        "London Stock Exchange (LSE)",
        "Step inside The Source Arena at Paternoster Square. Capital of European equity liquidity.",
        action_type="enter_interior", target_interior=INTERIOR_LSE
    ))

    # British Merchant Bank top left (x: 1..8, y: 1..7)
    bank_rect = pygame.Rect(1 * TILE_SIZE, 1 * TILE_SIZE, 8 * TILE_SIZE, 7 * TILE_SIZE)
    m.solids.append(bank_rect)
    m.objects.append(WorldObject(
        "bank_london", "building", 4 * TILE_SIZE, 7 * TILE_SIZE, 2 * TILE_SIZE, 24,
        "City of London Merchant Bank",
        "Inspect pound sterling liquidity, gilt yields, and global underwriting vaults.",
        action_type="enter_interior", target_interior=INTERIOR_BANK
    ))

    # British Commodity Trading HQ top right (x: 25..35, y: 1..7)
    comm_rect = pygame.Rect(25 * TILE_SIZE, 1 * TILE_SIZE, 11 * TILE_SIZE, 7 * TILE_SIZE)
    m.solids.append(comm_rect)
    m.objects.append(WorldObject(
        "hq_london_comm", "building", 29 * TILE_SIZE, 7 * TILE_SIZE, 3 * TILE_SIZE, 24,
        "Global Energy & Commodity Guild",
        "Inspect North Sea Brent crude, copper warehouses, and clean grid initiatives.",
        action_type="company_dossier", target_symbol="TITN"
    ))

    # Paternoster Column Monument (x: 16..18, y: 20..22)
    column_rect = pygame.Rect(16 * TILE_SIZE, 20 * TILE_SIZE, 3 * TILE_SIZE, 2 * TILE_SIZE)
    m.solids.append(column_rect)
    m.objects.append(WorldObject(
        "paternoster_column", "landmark", 16 * TILE_SIZE, 20 * TILE_SIZE, 3 * TILE_SIZE, 2 * TILE_SIZE,
        "Paternoster Square Column & Flaming Urn",
        "A 23-meter Corinthian column topped with a gilded flaming copper urn, overlooking St. Paul's Cathedral.",
        action_type="inspect"
    ))

    # Red Telephone Box (x: 22, y: 17)
    phone_rect = pygame.Rect(22 * TILE_SIZE, 17 * TILE_SIZE, 24, 24)
    m.solids.append(phone_rect)
    m.objects.append(WorldObject(
        "red_phone_box", "landmark", 22 * TILE_SIZE, 17 * TILE_SIZE, 24, 24,
        "Iconic British Red Telephone Kiosk",
        "Pick up the vintage receiver to hear an anonymous City broker whisper rumors about FTSE 100 mergers.",
        action_type="chai_stall"
    ))

    # Transit Portal (x: 8, y: 9)
    m.objects.append(WorldObject(
        "transit_london", "transit", 8 * TILE_SIZE, 9 * TILE_SIZE, 28, 28,
        "Paternoster Transit Portal",
        "High-speed international financial transit linking London to global exchanges.",
        target_loc=LOCATION_DALAL_STREET, action_type="transit"
    ))

    # NPCs
    m.npcs.append(NPC("alistair_ext", "Alistair Finch", "Senior Gilts & Sterling Trader", 13 * TILE_SIZE, 8 * TILE_SIZE + 8, (218, 165, 32)))
    m.npcs.append(NPC("beatrice_ext", "Beatrice Montgomery", "Global Energy & Mining Strategist", 20 * TILE_SIZE, 17 * TILE_SIZE, (72, 202, 228)))

    m.spawn_points["default"] = (16 * TILE_SIZE, 10 * TILE_SIZE)
    m.spawn_points["from_transit"] = (8 * TILE_SIZE, 11 * TILE_SIZE)
    return m


class World:
    def __init__(self):
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
        self.maps: Dict[str, LocationMap] = {
            LOCATION_WALL_STREET: build_wall_street_map(),
            LOCATION_DALAL_STREET: build_dalal_street_map(),
            LOCATION_KABUTOCHO: build_kabutocho_map(),
            LOCATION_LONDON: build_paternoster_square_map(),
            INTERIOR_BSE: build_bse_trading_floor(),
            INTERIOR_NYSE: build_nyse_trading_floor(),
            INTERIOR_TSE: build_tse_trading_floor(),
            INTERIOR_LSE: build_lse_trading_floor(),
            INTERIOR_BANK: build_bank_interior(),
            INTERIOR_LIBRARY: build_library_interior(),
            INTERIOR_WHITE_HOUSE: build_white_house_interior(),
            INTERIOR_PARLIAMENT: build_parliament_interior(),
            INTERIOR_APEX_HQ: build_apex_hq_interior(),
            INTERIOR_TITAN_HQ: build_titan_hq_interior(),
            INTERIOR_MONSOON_HQ: build_monsoon_hq_interior(),
            INTERIOR_NOVA_HQ: build_nova_hq_interior(),
            INTERIOR_AURA_HQ: build_aura_hq_interior(),
            INTERIOR_MEDX_HQ: build_medx_hq_interior(),
        }
        self.current_location_id: str = LOCATION_DALAL_STREET
        self.camera_x: float = 0.0
        self.camera_y: float = 0.0

        # Sprite image caches
        self._load_landmark_assets()

    def _load_landmark_assets(self):
        self.bull_img = None
        self.banyan_img = None
        self.lamp_img = None
        self.bench_img = None
        try:
            bp = SPRITES_DIR / "bull_monument.png"
            if bp.exists(): self.bull_img = pygame.image.load(str(bp)).convert_alpha()
            yp = SPRITES_DIR / "banyan_historic.png"
            if yp.exists(): self.banyan_img = pygame.image.load(str(yp)).convert_alpha()
            lp = SPRITES_DIR / "street_lamp.png"
            if lp.exists(): self.lamp_img = pygame.image.load(str(lp)).convert_alpha()
            sc = SPRITES_DIR / "street_bench.png"
            if sc.exists(): self.bench_img = pygame.image.load(str(sc)).convert_alpha()
        except Exception:
            pass

    @property
    def current_map(self) -> LocationMap:
        return self.maps[self.current_location_id]

    def set_location(self, loc_id: str, spawn_key: str = "default") -> Tuple[float, float]:
        if loc_id in self.maps:
            self.current_location_id = loc_id
            m = self.current_map
            return m.spawn_points.get(spawn_key, (16 * TILE_SIZE, 10 * TILE_SIZE))
        return (16 * TILE_SIZE, 10 * TILE_SIZE)

    def check_collision(self, rect: pygame.Rect) -> bool:
        return self.current_map.is_solid(rect)

    def has_line_of_sight(self, p1: Tuple[float, float], p2: Tuple[float, float], target_rect: Optional[pygame.Rect] = None) -> bool:
        """Raycast between player and target; returns False if a solid wall blocks line of sight."""
        steps = 5
        for i in range(1, steps):
            t = i / float(steps)
            tx = p1[0] + (p2[0] - p1[0]) * t
            ty = p1[1] + (p2[1] - p1[1]) * t
            for s in self.current_map.solids:
                if target_rect and (s == target_rect or s.colliderect(target_rect)):
                    continue
                if s.collidepoint(tx, ty):
                    return False
        return True

    def get_nearby_interactive(self, px: float, py: float, dist: float = 32.0, check_los: bool = True) -> Optional[Any]:
        """Find the closest NPC or interactive object within interaction range, with line of sight checking."""
        m = self.current_map
        best_candidate: Optional[Any] = None
        min_dist: float = float("inf")

        # 1. Check NPCs
        for npc in m.npcs:
            dx = max(npc.x - px, 0.0, px - (npc.x + npc.width))
            dy = max(npc.y - py, 0.0, py - (npc.y + npc.height))
            d = math.hypot(dx, dy)
            if d <= dist and d < min_dist:
                cx = npc.x + npc.width / 2.0
                cy = npc.y + npc.height / 2.0
                if not check_los or self.has_line_of_sight((px, py), (cx, cy), npc.rect):
                    min_dist = d
                    best_candidate = npc

        # 2. Check World Objects
        for obj in m.objects:
            is_door = obj.action_type in ("enter_interior", "exit_interior")
            allowed_dist = dist + 14.0 if is_door else dist

            dx = max(obj.x - px, 0.0, px - (obj.x + obj.w))
            dy = max(obj.y - py, 0.0, py - (obj.y + obj.h))
            d = math.hypot(dx, dy)

            if d <= allowed_dist and d < min_dist:
                cx = obj.x + obj.w / 2.0
                cy = obj.y + obj.h / 2.0
                # Doors do not require strict LOS through their own parent building
                los_needed = check_los and not is_door
                if not los_needed or self.has_line_of_sight((px, py), (cx, cy), obj.rect):
                    min_dist = d
                    best_candidate = obj

        return best_candidate

    def update_camera(self, target_x: float, target_y: float):
        """Center camera on player, smoothly clamped within map boundaries; centers small maps."""
        m = self.current_map
        
        # Horizontal
        if m.pixel_width <= VIRTUAL_WIDTH:
            self.camera_x = - (VIRTUAL_WIDTH - m.pixel_width) / 2.0
        else:
            desired_cam_x = target_x - VIRTUAL_WIDTH / 2.0
            max_x = float(m.pixel_width - VIRTUAL_WIDTH)
            self.camera_x = max(0.0, min(max_x, desired_cam_x))

        # Vertical
        if m.pixel_height <= VIRTUAL_HEIGHT:
            self.camera_y = - (VIRTUAL_HEIGHT - m.pixel_height) / 2.0
        else:
            desired_cam_y = target_y - VIRTUAL_HEIGHT / 2.0
            max_y = float(m.pixel_height - VIRTUAL_HEIGHT)
            self.camera_y = max(0.0, min(max_y, desired_cam_y))

    def get_pathfinder(self) -> Any:
        if not hasattr(self.current_map, '_pathfinder') or self.current_map._pathfinder is None:
            from src.pathfinding import GridPathfinder
            self.current_map._pathfinder = GridPathfinder(
                tile_cols=self.current_map.width_tiles,
                tile_rows=self.current_map.height_tiles,
                solids=self.current_map.solids
            )
        return self.current_map._pathfinder

    def calculate_route(self, start_pos: Tuple[float, float], goal_pos: Tuple[float, float]) -> List[Tuple[int, int]]:
        pf = self.get_pathfinder()
        return pf.find_path(start_pos, goal_pos)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, small_font: pygame.font.Font, player: Any, tick_count: int = 0):
        cam_offset = (int(self.camera_x), int(self.camera_y))
        m = self.current_map

        # Calculate visible tile range
        start_tx = max(0, int(self.camera_x // TILE_SIZE))
        end_tx = min(m.width_tiles, int((self.camera_x + VIRTUAL_WIDTH) // TILE_SIZE) + 2)
        start_ty = max(0, int(self.camera_y // TILE_SIZE))
        end_ty = min(m.height_tiles, int((self.camera_y + VIRTUAL_HEIGHT) // TILE_SIZE) + 2)

        # 1. Ground Tiles
        for ty in range(start_ty, end_ty):
            for tx in range(start_tx, end_tx):
                t_type = m.tiles[ty][tx]
                rx = tx * TILE_SIZE - cam_offset[0]
                ry = ty * TILE_SIZE - cam_offset[1]
                t_rect = pygame.Rect(rx, ry, TILE_SIZE, TILE_SIZE)

                if t_type == 0:  # Asphalt road
                    pygame.draw.rect(surface, (36, 40, 48), t_rect)
                    # Double yellow center divider
                    if ty == 13:
                        if (tx % 2) == 0:
                            pygame.draw.line(surface, (240, 200, 50), (rx, ry + 10), (rx + TILE_SIZE, ry + 10), 1)
                            pygame.draw.line(surface, (240, 200, 50), (rx, ry + 14), (rx + TILE_SIZE, ry + 14), 1)
                    # Manhole cover
                    if tx == 14 and ty == 12:
                        pygame.draw.circle(surface, (55, 60, 70), (rx + 12, ry + 12), 6)
                        pygame.draw.circle(surface, (30, 32, 40), (rx + 12, ry + 12), 6, width=1)
                elif t_type == 1:  # Granite Sidewalk
                    pygame.draw.rect(surface, (68, 76, 92), t_rect)
                    pygame.draw.rect(surface, (58, 65, 80), t_rect, width=1)
                elif t_type == 2:  # Grass Lawn / Park
                    pygame.draw.rect(surface, (32, 88, 52), t_rect)
                    if (tx * 7 + ty * 13) % 5 == 0:
                        pygame.draw.circle(surface, (45, 115, 70), (rx + 8, ry + 8), 2)
                elif t_type == 3:  # Sandstone Street (Mumbai)
                    pygame.draw.rect(surface, (145, 110, 78), t_rect)
                    pygame.draw.rect(surface, (128, 95, 66), t_rect, width=1)
                elif t_type == 4:  # Cobblestone Pavers
                    pygame.draw.rect(surface, (95, 90, 85), t_rect)
                    pygame.draw.rect(surface, (75, 70, 65), t_rect, width=1)

        # 1.5 Route Guidance Path
        if getattr(player, 'route_guidance_active', True) and getattr(player, 'current_route', None):
            from src.pathfinding import draw_route_guidance
            draw_route_guidance(surface, player.current_route, cam_offset, getattr(player, 'route_pulse_timer', 0.0))

        # 2. Buildings or Interior Architecture
        if m.id.startswith("interior_"):
            self._draw_interior_architecture(surface, cam_offset, m, tick_count, font, small_font, getattr(self, "market", None))
        else:
            self._draw_buildings(surface, cam_offset, m, tick_count)

        # 3. World Objects
        for obj in m.objects:
            self._draw_object(surface, cam_offset, obj, font, small_font, tick_count)

        # 4. NPCs
        for npc in m.npcs:
            npc.draw(surface, cam_offset)

        # 5. Player
        player.draw(surface, cam_offset)

        # 6. Interaction Prompt with target highlighting
        nearby = self.get_nearby_interactive(player.x + player.width / 2, player.y + player.height / 2)
        if nearby:
            self._draw_prompt(surface, cam_offset, nearby, font, small_font, tick_count)

    def _draw_buildings(self, surface: pygame.Surface, cam_offset: Tuple[int, int], m: LocationMap, tick_count: int):
        if m.id == LOCATION_WALL_STREET:
            # -------------------------------------------------------------
            # NYSE Facade
            # -------------------------------------------------------------
            nyse_rect = pygame.Rect(10 * TILE_SIZE - cam_offset[0], 1 * TILE_SIZE - cam_offset[1], 13 * TILE_SIZE, 7 * TILE_SIZE)
            # Shadow
            pygame.draw.rect(surface, (10, 14, 25), nyse_rect.inflate(4, 4), border_radius=2)
            # Granite facade
            pygame.draw.rect(surface, (205, 210, 220), nyse_rect)
            pygame.draw.rect(surface, (160, 165, 175), nyse_rect, width=2)
            
            # Neoclassical Pediment Triangle
            ped_points = [
                (nyse_rect.left, nyse_rect.top + 28),
                (nyse_rect.centerx, nyse_rect.top),
                (nyse_rect.right, nyse_rect.top + 28)
            ]
            pygame.draw.polygon(surface, (185, 190, 202), ped_points)
            pygame.draw.polygon(surface, (145, 150, 160), ped_points, width=2)

            # Columns (6 fluted Corinthian columns)
            for col_i in range(6):
                cx = nyse_rect.left + 20 + col_i * 48
                pygame.draw.rect(surface, (230, 235, 245), (cx, nyse_rect.top + 30, 14, nyse_rect.height - 32))
                pygame.draw.rect(surface, (165, 170, 185), (cx, nyse_rect.top + 30, 14, nyse_rect.height - 32), width=1)

            # Grand Brass Entrance Doors
            door_rect = pygame.Rect(nyse_rect.centerx - 22, nyse_rect.bottom - 28, 44, 28)
            pygame.draw.rect(surface, (110, 75, 30), door_rect, border_radius=2)
            pygame.draw.rect(surface, (218, 165, 32), door_rect, width=2, border_radius=2)
            pygame.draw.line(surface, (218, 165, 32), (door_rect.centerx, door_rect.top), (door_rect.centerx, door_rect.bottom), 2)

            # High-visibility Green Digital LED Ticker Tape Banner across Frieze
            banner_rect = pygame.Rect(nyse_rect.left + 14, nyse_rect.top + 30, nyse_rect.width - 28, 14)
            pygame.draw.rect(surface, (8, 14, 20), banner_rect)
            pygame.draw.rect(surface, (30, 80, 50), banner_rect, width=1)
            # Animated ticker dots
            ticker_step = (tick_count * 2) % (banner_rect.width - 10)
            pygame.draw.circle(surface, (85, 230, 110), (banner_rect.left + ticker_step, banner_rect.centery), 3)

            # -------------------------------------------------------------
            # Apex Tech Global Tower
            # -------------------------------------------------------------
            apex_rect = pygame.Rect(25 * TILE_SIZE - cam_offset[0], 1 * TILE_SIZE - cam_offset[1], 11 * TILE_SIZE, 7 * TILE_SIZE)
            pygame.draw.rect(surface, (18, 32, 58), apex_rect)
            pygame.draw.rect(surface, COLOR_BORDER_ACCENT, apex_rect, width=2)
            # Window Grid
            for wy in range(apex_rect.top + 10, apex_rect.bottom - 12, 16):
                for wx in range(apex_rect.left + 10, apex_rect.right - 10, 16):
                    pygame.draw.rect(surface, (72, 202, 228), (wx, wy, 10, 10))

            # Revolving Entrance Door
            a_door = pygame.Rect(apex_rect.centerx - 16, apex_rect.bottom - 24, 32, 24)
            pygame.draw.rect(surface, (10, 20, 35), a_door)
            pygame.draw.rect(surface, COLOR_BORDER_ACCENT, a_door, width=2)

            # -------------------------------------------------------------
            # Titan Capital Bank
            # -------------------------------------------------------------
            titn_rect = pygame.Rect(1 * TILE_SIZE - cam_offset[0], 1 * TILE_SIZE - cam_offset[1], 8 * TILE_SIZE, 7 * TILE_SIZE)
            pygame.draw.rect(surface, (50, 58, 72), titn_rect)
            pygame.draw.rect(surface, (35, 42, 54), titn_rect, width=2)
            t_door = pygame.Rect(titn_rect.centerx - 14, titn_rect.bottom - 24, 28, 24)
            pygame.draw.rect(surface, (160, 130, 50), t_door)
            pygame.draw.rect(surface, (100, 75, 25), t_door, width=2)

            # -------------------------------------------------------------
            # Academy, Nova Cloud Systems & White House Buildings
            # -------------------------------------------------------------
            acad_rect = pygame.Rect(1 * TILE_SIZE - cam_offset[0], 19 * TILE_SIZE - cam_offset[1], 7 * TILE_SIZE, 7 * TILE_SIZE)
            pygame.draw.rect(surface, (120, 50, 40), acad_rect)  # Red brick
            pygame.draw.rect(surface, (90, 35, 28), acad_rect, width=2)

            # Nova Cloud Systems Tower (x: 8..13, y: 19..25)
            nova_rect = pygame.Rect(8 * TILE_SIZE - cam_offset[0], 19 * TILE_SIZE - cam_offset[1], 6 * TILE_SIZE, 7 * TILE_SIZE)
            pygame.draw.rect(surface, (20, 30, 45), nova_rect)
            pygame.draw.rect(surface, (40, 160, 220), nova_rect, width=2)
            for ny in range(nova_rect.top + 8, nova_rect.bottom - 16, 14):
                for nx in range(nova_rect.left + 8, nova_rect.right - 8, 14):
                    pygame.draw.rect(surface, (45, 210, 255), (nx, ny, 8, 8))
            n_door = pygame.Rect(nova_rect.centerx - 12, nova_rect.bottom - 24, 24, 24)
            pygame.draw.rect(surface, (10, 20, 35), n_door)
            pygame.draw.rect(surface, (40, 160, 220), n_door, width=2)

            gaz_rect = pygame.Rect(27 * TILE_SIZE - cam_offset[0], 19 * TILE_SIZE - cam_offset[1], 9 * TILE_SIZE, 7 * TILE_SIZE)
            pygame.draw.rect(surface, (60, 70, 85), gaz_rect)
            pygame.draw.rect(surface, (45, 52, 65), gaz_rect, width=2)

        elif m.id == LOCATION_DALAL_STREET:
            # -------------------------------------------------------------
            # BSE Towers (Phiroze Jeejeebhoy Towers)
            # -------------------------------------------------------------
            bse_rect = pygame.Rect(10 * TILE_SIZE - cam_offset[0], 1 * TILE_SIZE - cam_offset[1], 13 * TILE_SIZE, 7 * TILE_SIZE)
            pygame.draw.rect(surface, (195, 75, 45), bse_rect)  # Terracotta red
            pygame.draw.rect(surface, (140, 45, 25), bse_rect, width=2)

            # Iconic Curved Rotunda Top
            rotunda_rect = pygame.Rect(bse_rect.centerx - 50, bse_rect.top - 18, 100, 36)
            pygame.draw.ellipse(surface, (225, 105, 75), rotunda_rect)
            pygame.draw.ellipse(surface, (150, 55, 35), rotunda_rect, width=2)

            # Digital Red LED Ticker Tape
            bse_ticker = pygame.Rect(bse_rect.left + 14, bse_rect.bottom - 22, bse_rect.width - 28, 14)
            pygame.draw.rect(surface, (16, 10, 14), bse_ticker)
            pygame.draw.rect(surface, COLOR_LOSS_BRIGHT, bse_ticker, width=1)

            # Entrance Doors
            b_door = pygame.Rect(bse_rect.centerx - 20, bse_rect.bottom - 26, 40, 26)
            pygame.draw.rect(surface, (120, 40, 25), b_door)
            pygame.draw.rect(surface, (230, 180, 80), b_door, width=2)

            # -------------------------------------------------------------
            # Monsoon Goods & Aurum Energy Buildings
            # -------------------------------------------------------------
            m_rect = pygame.Rect(25 * TILE_SIZE - cam_offset[0], 1 * TILE_SIZE - cam_offset[1], 11 * TILE_SIZE, 7 * TILE_SIZE)
            pygame.draw.rect(surface, (165, 135, 95), m_rect)  # Colonial teakwood sandstone
            pygame.draw.rect(surface, (125, 98, 68), m_rect, width=2)

            a_rect = pygame.Rect(1 * TILE_SIZE - cam_offset[0], 1 * TILE_SIZE - cam_offset[1], 8 * TILE_SIZE, 7 * TILE_SIZE)
            pygame.draw.rect(surface, (28, 95, 75), a_rect)  # Eco-green
            pygame.draw.rect(surface, (20, 70, 55), a_rect, width=2)

            # South Bank (x: 1..6, y: 19..25)
            s_bank = pygame.Rect(1 * TILE_SIZE - cam_offset[0], 19 * TILE_SIZE - cam_offset[1], 6 * TILE_SIZE, 7 * TILE_SIZE)
            pygame.draw.rect(surface, (150, 115, 80), s_bank)
            pygame.draw.rect(surface, (115, 85, 55), s_bank, width=2)

            # Medix Synthetics Bio-Tech Center (x: 8..13, y: 19..25)
            medx_rect = pygame.Rect(8 * TILE_SIZE - cam_offset[0], 19 * TILE_SIZE - cam_offset[1], 6 * TILE_SIZE, 7 * TILE_SIZE)
            pygame.draw.rect(surface, (230, 242, 245), medx_rect)
            pygame.draw.rect(surface, (46, 196, 182), medx_rect, width=2)
            cross_cx = medx_rect.centerx
            cross_cy = medx_rect.top + 24
            pygame.draw.rect(surface, (46, 196, 182), (cross_cx - 3, cross_cy - 10, 6, 20))
            pygame.draw.rect(surface, (46, 196, 182), (cross_cx - 10, cross_cy - 3, 20, 6))
            mx_door = pygame.Rect(medx_rect.centerx - 12, medx_rect.bottom - 24, 24, 24)
            pygame.draw.rect(surface, (180, 225, 230), mx_door)
            pygame.draw.rect(surface, (46, 196, 182), mx_door, width=2)

            # Parliament of India Liaison Pavilion (x: 20..25, y: 19..25)
            parl_rect = pygame.Rect(20 * TILE_SIZE - cam_offset[0], 19 * TILE_SIZE - cam_offset[1], 6 * TILE_SIZE, 7 * TILE_SIZE)
            pygame.draw.rect(surface, (175, 90, 65), parl_rect)
            pygame.draw.rect(surface, (130, 60, 40), parl_rect, width=2)
            for p_i in range(4):
                px = parl_rect.left + 12 + p_i * 32
                pygame.draw.rect(surface, (215, 175, 140), (px, parl_rect.top + 16, 10, parl_rect.height - 24))
            p_door = pygame.Rect(parl_rect.centerx - 12, parl_rect.bottom - 24, 24, 24)
            pygame.draw.rect(surface, (80, 35, 20), p_door)
            pygame.draw.rect(surface, (218, 165, 32), p_door, width=2)

            # Press Bureau (x: 27..36, y: 19..25)
            s_press = pygame.Rect(27 * TILE_SIZE - cam_offset[0], 19 * TILE_SIZE - cam_offset[1], 10 * TILE_SIZE, 7 * TILE_SIZE)
            pygame.draw.rect(surface, (140, 100, 70), s_press)
            pygame.draw.rect(surface, (105, 75, 50), s_press, width=2)

        elif m.id == LOCATION_KABUTOCHO:
            # TSE Building (x: 10..22, y: 1..7)
            tse_rect = pygame.Rect(10 * TILE_SIZE - cam_offset[0], 1 * TILE_SIZE - cam_offset[1], 13 * TILE_SIZE, 7 * TILE_SIZE)
            pygame.draw.rect(surface, (32, 38, 52), tse_rect)
            pygame.draw.rect(surface, (200, 40, 40), tse_rect, width=2)
            rot_rect = pygame.Rect(tse_rect.centerx - 40, tse_rect.top - 12, 80, 24)
            pygame.draw.ellipse(surface, (70, 90, 120), rot_rect)
            pygame.draw.ellipse(surface, (200, 40, 40), rot_rect, width=2)
            t_ticker = pygame.Rect(tse_rect.left + 14, tse_rect.top + 28, tse_rect.width - 28, 14)
            pygame.draw.rect(surface, (12, 16, 24), t_ticker)
            pygame.draw.rect(surface, (220, 60, 60), t_ticker, width=1)
            t_door = pygame.Rect(tse_rect.centerx - 20, tse_rect.bottom - 26, 40, 26)
            pygame.draw.rect(surface, (20, 24, 35), t_door)
            pygame.draw.rect(surface, (200, 40, 40), t_door, width=2)

            # Bank & Tech Center
            b_rect = pygame.Rect(1 * TILE_SIZE - cam_offset[0], 1 * TILE_SIZE - cam_offset[1], 8 * TILE_SIZE, 7 * TILE_SIZE)
            pygame.draw.rect(surface, (55, 65, 75), b_rect)
            pygame.draw.rect(surface, (40, 50, 60), b_rect, width=2)
            tech_rect = pygame.Rect(25 * TILE_SIZE - cam_offset[0], 1 * TILE_SIZE - cam_offset[1], 11 * TILE_SIZE, 7 * TILE_SIZE)
            pygame.draw.rect(surface, (24, 45, 65), tech_rect)
            pygame.draw.rect(surface, (46, 196, 182), tech_rect, width=2)

        elif m.id == LOCATION_LONDON:
            # LSE Building (x: 10..22, y: 1..7)
            lse_rect = pygame.Rect(10 * TILE_SIZE - cam_offset[0], 1 * TILE_SIZE - cam_offset[1], 13 * TILE_SIZE, 7 * TILE_SIZE)
            pygame.draw.rect(surface, (215, 215, 220), lse_rect)
            pygame.draw.rect(surface, (160, 165, 175), lse_rect, width=2)
            for pi in range(6):
                px = lse_rect.left + 18 + pi * 48
                pygame.draw.rect(surface, (235, 235, 242), (px, lse_rect.top + 26, 14, lse_rect.height - 28))
            l_ticker = pygame.Rect(lse_rect.left + 14, lse_rect.top + 28, lse_rect.width - 28, 14)
            pygame.draw.rect(surface, (10, 20, 40), l_ticker)
            pygame.draw.rect(surface, (60, 120, 230), l_ticker, width=1)
            l_door = pygame.Rect(lse_rect.centerx - 20, lse_rect.bottom - 26, 40, 26)
            pygame.draw.rect(surface, (70, 45, 30), l_door)
            pygame.draw.rect(surface, (218, 165, 32), l_door, width=2)

            # Bank & Commodity Guild
            lb_rect = pygame.Rect(1 * TILE_SIZE - cam_offset[0], 1 * TILE_SIZE - cam_offset[1], 8 * TILE_SIZE, 7 * TILE_SIZE)
            pygame.draw.rect(surface, (160, 150, 140), lb_rect)
            pygame.draw.rect(surface, (120, 110, 100), lb_rect, width=2)
            comm_rect = pygame.Rect(25 * TILE_SIZE - cam_offset[0], 1 * TILE_SIZE - cam_offset[1], 11 * TILE_SIZE, 7 * TILE_SIZE)
            pygame.draw.rect(surface, (75, 55, 45), comm_rect)
            pygame.draw.rect(surface, (218, 165, 32), comm_rect, width=2)

    def _draw_interior_architecture(self, surface: pygame.Surface, cam_offset: Tuple[int, int],
                                   m: LocationMap, tick_count: int, font: pygame.font.Font,
                                   small_font: pygame.font.Font, market: Optional[Any] = None):
        """Render high-detail perspective-consistent architectural pixel art inside buildings."""
        # 1. 3D Architectural Walls for all solid walls
        for s in m.solids:
            rx = int(s.x - cam_offset[0])
            ry = int(s.y - cam_offset[1])
            
            # Skip if outside viewport bounds
            if rx + s.w < -20 or rx > VIRTUAL_WIDTH + 20 or ry + s.h < -20 or ry > VIRTUAL_HEIGHT + 20:
                continue

            # Identify if this solid is a thin railing or broker desk rather than a tall wall
            is_thin_rail = (s.w <= 16 and s.h >= 24) or (s.h <= 24 and s.w >= 30 and s.y > 10 * TILE_SIZE)
            
            if is_thin_rail:
                if s.w <= 16:
                    # Brass pit vertical railing
                    pygame.draw.rect(surface, (140, 100, 30), (rx, ry, s.w, s.h), border_radius=2)
                    pygame.draw.rect(surface, (230, 185, 60), (rx + 2, ry, max(2, s.w - 4), s.h), width=1)
                else:
                    # Wooden broker desk surface
                    pygame.draw.rect(surface, (12, 16, 24), (rx, ry + s.h, s.w, 4)) # shadow
                    pygame.draw.rect(surface, (65, 45, 32), (rx, ry, s.w, s.h), border_radius=2)
                    pygame.draw.rect(surface, (95, 68, 48), (rx, ry, s.w, 3)) # desktop highlight
                    # Dual desktop monitors on desk
                    for d_i in range(min(2, s.w // 24)):
                        mx = rx + 8 + d_i * 26
                        my = ry - 8
                        pygame.draw.rect(surface, (18, 24, 36), (mx, my, 16, 12), border_radius=2)
                        scr_color = (46, 196, 182) if (tick_count + d_i * 10) % 40 < 20 else (85, 230, 110)
                        pygame.draw.rect(surface, scr_color, (mx + 2, my + 2, 12, 8))
                        pygame.draw.line(surface, (255, 255, 255), (mx + 3, my + 7), (mx + 13, my + 4), 1)
                continue

            # Main Architectural Walls
            # Floor drop shadow
            pygame.draw.rect(surface, (8, 12, 22), (rx, ry + s.h, s.w, 6))

            # Wall body palette based on interior location
            if m.id == INTERIOR_BSE:
                wall_body_col = (52, 42, 38)
                wall_trim_col = (185, 140, 70)
                cornice_col = (215, 185, 140)
            elif m.id in (INTERIOR_NYSE, INTERIOR_LSE, INTERIOR_BANK):
                wall_body_col = (48, 56, 70)
                wall_trim_col = (140, 155, 175)
                cornice_col = (205, 215, 228)
            else:
                wall_body_col = (38, 48, 64)
                wall_trim_col = (72, 202, 228)
                cornice_col = (180, 200, 220)

            # Draw Wall Face
            pygame.draw.rect(surface, wall_body_col, (rx, ry, s.w, s.h))
            
            # Wainscoting panels on large walls
            if s.h >= 32 and s.w >= 32:
                for wx in range(rx + 8, rx + s.w - 16, 24):
                    pygame.draw.rect(surface, (max(0, wall_body_col[0] - 12), max(0, wall_body_col[1] - 10), max(0, wall_body_col[2] - 10)), (wx, ry + 12, 18, s.h - 18), border_radius=1)
                    pygame.draw.rect(surface, wall_trim_col, (wx, ry + 12, 18, s.h - 18), width=1)

            # Top Cornice Molding
            pygame.draw.rect(surface, cornice_col, (rx, ry, s.w, 4))
            pygame.draw.rect(surface, (max(0, cornice_col[0] - 30), max(0, cornice_col[1] - 30), max(0, cornice_col[2] - 30)), (rx, ry + 4, s.w, 2))

            # Skirting Baseboard
            pygame.draw.rect(surface, wall_trim_col, (rx, ry + s.h - 4, s.w, 4))
            pygame.draw.rect(surface, (20, 24, 32), (rx, ry, s.w, s.h), width=1)

        # 2. BSE Signature Centerpiece & Environmental Enhancements
        if m.id == INTERIOR_BSE:
            # Grand Lobby Compass Rose (x=24, y=28)
            lx = int(24 * TILE_SIZE - cam_offset[0])
            ly = int(28 * TILE_SIZE - cam_offset[1])
            if -40 <= lx <= VIRTUAL_WIDTH + 40 and -40 <= ly <= VIRTUAL_HEIGHT + 40:
                pygame.draw.circle(surface, (140, 105, 45), (lx, ly), 22, width=2)
                pygame.draw.circle(surface, (218, 165, 32), (lx, ly), 16, width=1)
                for a_i in range(4):
                    ang = a_i * math.pi / 2.0
                    pygame.draw.line(surface, (245, 205, 80), (lx, ly), (int(lx + math.cos(ang) * 20), int(ly + math.sin(ang) * 20)), 2)
                    ang_sub = ang + math.pi / 4.0
                    pygame.draw.line(surface, (180, 140, 50), (lx, ly), (int(lx + math.cos(ang_sub) * 12), int(ly + math.sin(ang_sub) * 12)), 1)
                carpet_rect = pygame.Rect(int(23 * TILE_SIZE - cam_offset[0]), int(29 * TILE_SIZE - cam_offset[1]), 2 * TILE_SIZE, 5 * TILE_SIZE)
                pygame.draw.rect(surface, (135, 30, 35), carpet_rect)
                pygame.draw.rect(surface, (218, 165, 32), carpet_rect, width=1)

            # Fluted Pillars around Trading Hall
            pillars = [
                (16 * TILE_SIZE, 14 * TILE_SIZE),
                (16 * TILE_SIZE, 22 * TILE_SIZE),
                (32 * TILE_SIZE, 14 * TILE_SIZE),
                (32 * TILE_SIZE, 22 * TILE_SIZE)
            ]
            for px_t, py_t in pillars:
                prx = int(px_t - cam_offset[0])
                pry = int(py_t - cam_offset[1])
                pygame.draw.rect(surface, (190, 175, 150), (prx - 4, pry + 12, 24, 8), border_radius=1)
                pygame.draw.rect(surface, (230, 220, 205), (prx, pry - 12, 16, 24))
                pygame.draw.line(surface, (185, 170, 155), (prx + 5, pry - 12), (prx + 5, pry + 12), 1)
                pygame.draw.line(surface, (185, 170, 155), (prx + 11, pry - 12), (prx + 11, pry + 12), 1)
                pygame.draw.rect(surface, (218, 165, 32), (prx - 2, pry - 16, 20, 5), border_radius=1)

            # Giant Animated North Market Board & Ticker
            mb_rx = int(17 * TILE_SIZE - cam_offset[0])
            mb_ry = int(10 * TILE_SIZE - cam_offset[1])
            mb_w = 14 * TILE_SIZE
            mb_h = 24
            if -50 <= mb_rx <= VIRTUAL_WIDTH + 50 and -50 <= mb_ry <= VIRTUAL_HEIGHT + 50:
                pygame.draw.rect(surface, (6, 10, 18), (mb_rx, mb_ry, mb_w, mb_h), border_radius=2)
                pygame.draw.rect(surface, (30, 75, 50), (mb_rx, mb_ry, mb_w, mb_h), width=1, border_radius=2)
                
                sensex_val = 74820.0
                if market and hasattr(market, "companies") and market.companies:
                    total_price = sum(c.price for c in market.companies.values())
                    sensex_val = 50000.0 + total_price * 40.0
                    
                quotes_list = []
                if market and hasattr(market, "companies"):
                    for sym, c in list(market.companies.items())[:6]:
                        chg_sign = "+" if c.change_pct >= 0 else ""
                        quotes_list.append(f"{sym} ${c.price:.2f} ({chg_sign}{c.change_pct:.1f}%)")
                else:
                    quotes_list = ["APEX $142.50 (+3.2%)", "TITN $88.10 (-1.1%)", "CHAI $54.20 (+2.4%)", "NOVA $210.00 (+4.8%)"]
                
                ticker_str = f"● SENSEX {sensex_val:,.1f} ▲  •  " + "  •  ".join(quotes_list) + "  •  [BSE CASH PIT ACTIVE]"
                
                char_w = 7
                scroll_pix = (tick_count * 2) % max(1, len(ticker_str) * char_w)
                
                old_clip = surface.get_clip()
                surface.set_clip(pygame.Rect(mb_rx + 4, mb_ry + 2, mb_w - 8, mb_h - 4))
                t_surf = small_font.render(ticker_str + "    " + ticker_str, True, (85, 230, 110))
                surface.blit(t_surf, (mb_rx + 6 - scroll_pix, mb_ry + 4))
                surface.set_clip(old_clip)

            # Archway Entrance Overhead Signboards
            signs = [
                ("★ GRAND TRADING PIT ★", 24 * TILE_SIZE, 24 * TILE_SIZE, (218, 165, 32)),
                ("FINANCIAL HISTORY GALLERY", 14 * TILE_SIZE, 16 * TILE_SIZE, (200, 180, 140)),
                ("EQUITY RESEARCH LAB", 33 * TILE_SIZE, 16 * TILE_SIZE, (72, 202, 228)),
                ("INVESTOR EDUCATION HALL", 33 * TILE_SIZE, 26 * TILE_SIZE, (180, 140, 220)),
                ("RESTRICTED ARCHIVES", 24 * TILE_SIZE, 8 * TILE_SIZE, (230, 90, 80))
            ]
            for s_text, sx_t, sy_t, col in signs:
                srx = int(sx_t - cam_offset[0])
                sry = int(sy_t - cam_offset[1])
                if -100 <= srx <= VIRTUAL_WIDTH + 100 and -40 <= sry <= VIRTUAL_HEIGHT + 40:
                    badge_surf = small_font.render(s_text, True, col)
                    bw = badge_surf.get_width() + 10
                    pygame.draw.rect(surface, (12, 16, 26), (srx - bw // 2, sry - 12, bw, 14), border_radius=2)
                    pygame.draw.rect(surface, col, (srx - bw // 2, sry - 12, bw, 14), width=1, border_radius=2)
                    surface.blit(badge_surf, (srx - badge_surf.get_width() // 2, sry - 11))

    def _draw_object(self, surface: pygame.Surface, cam_offset: Tuple[int, int], 
                     obj: WorldObject, font: pygame.font.Font, small_font: pygame.font.Font, tick_count: int = 0):
        rx = int(obj.x - cam_offset[0])
        ry = int(obj.y - cam_offset[1])

        # Skip if outside viewport
        if rx + obj.w < -20 or rx > VIRTUAL_WIDTH + 20 or ry + obj.h < -20 or ry > VIRTUAL_HEIGHT + 20:
            return

        if obj.type == "door":
            # Polished wooden double door with brass framing and illuminated EXIT sign
            pygame.draw.rect(surface, (80, 48, 28), (rx, ry, obj.w, obj.h), border_radius=2)
            pygame.draw.rect(surface, (218, 165, 32), (rx, ry, obj.w, obj.h), width=2, border_radius=2)
            pygame.draw.line(surface, (218, 165, 32), (rx + obj.w // 2, ry), (rx + obj.w // 2, ry + obj.h), 2)
            pygame.draw.line(surface, (245, 205, 80), (rx + 4, ry + obj.h // 2), (rx + obj.w - 4, ry + obj.h // 2), 2)
            exit_box = pygame.Rect(rx + obj.w // 2 - 16, ry - 10, 32, 10)
            pygame.draw.rect(surface, (10, 35, 18), exit_box, border_radius=2)
            pygame.draw.rect(surface, (85, 230, 110), exit_box, width=1, border_radius=2)
            ex_txt = small_font.render("EXIT", True, (85, 230, 110))
            surface.blit(ex_txt, ex_txt.get_rect(center=exit_box.center))

        elif obj.type == "terminal":
            box = pygame.Rect(rx, ry, obj.w, obj.h)
            pygame.draw.rect(surface, (12, 18, 28), (rx, ry + obj.h, obj.w, 4)) # shadow
            pygame.draw.rect(surface, (24, 34, 50), box, border_radius=3)
            pygame.draw.rect(surface, COLOR_BORDER_ACCENT, box, width=2, border_radius=3)
            m1 = pygame.Rect(rx + 4, ry + 4, max(8, (obj.w - 12) // 2), max(6, obj.h - 14))
            m2 = pygame.Rect(rx + (obj.w - 12) // 2 + 8, ry + 4, max(8, (obj.w - 12) // 2), max(6, obj.h - 14))
            pygame.draw.rect(surface, (6, 12, 20), m1)
            pygame.draw.rect(surface, (6, 12, 20), m2)
            pygame.draw.rect(surface, (30, 90, 60), (m1.x + 2, m1.y + 2, max(2, m1.w - 4), 3))
            pygame.draw.line(surface, (85, 230, 110), (m1.x + 2, m1.y + m1.h - 4), (m1.right - 2, m1.y + 4), 1)
            pygame.draw.line(surface, (72, 202, 228), (m2.x + 2, m2.y + m2.h - 6), (m2.right - 2, m2.y + 3), 1)
            kb = pygame.Rect(rx + 6, ry + max(0, obj.h - 8), max(4, obj.w - 12), 4)
            pygame.draw.rect(surface, (45, 55, 70), kb)
            led_c = (85, 230, 110) if (tick_count % 30 < 15) else (255, 183, 3)
            pygame.draw.circle(surface, led_c, (rx + obj.w - 4, ry + 4), 2)

        elif obj.type == "ledger":
            box = pygame.Rect(rx, ry, obj.w, obj.h)
            pygame.draw.rect(surface, (75, 42, 25), box, border_radius=2)
            p1 = pygame.Rect(rx + 2, ry + 2, max(4, (obj.w - 6) // 2), max(4, obj.h - 4))
            p2 = pygame.Rect(rx + (obj.w - 6) // 2 + 4, ry + 2, max(4, (obj.w - 6) // 2), max(4, obj.h - 4))
            pygame.draw.rect(surface, (235, 225, 195), p1)
            pygame.draw.rect(surface, (235, 225, 195), p2)
            for ly in range(p1.top + 3, p1.bottom - 2, 3):
                pygame.draw.line(surface, (120, 100, 80), (p1.left + 2, ly), (p1.right - 2, ly), 1)
                pygame.draw.line(surface, (120, 100, 80), (p2.left + 2, ly), (p2.right - 2, ly), 1)
            pygame.draw.line(surface, (210, 45, 35), (rx + obj.w // 2, ry), (rx + obj.w // 2, ry + obj.h + 2), 2)

        elif obj.type == "screen":
            box = pygame.Rect(rx, ry, obj.w, obj.h)
            if "dupont" in obj.id or "blackboard" in obj.id:
                pygame.draw.rect(surface, (25, 45, 35), box, border_radius=2)
                pygame.draw.rect(surface, (120, 85, 55), box, width=2, border_radius=2)
                t_lbl = small_font.render("DUPONT: ROE = NetMargin x AssetTurnover x Leverage", True, (240, 240, 220))
                surface.blit(t_lbl, (rx + 4, ry + 3))
            elif "whiteboard" in obj.id:
                pygame.draw.rect(surface, (235, 240, 245), box, border_radius=2)
                pygame.draw.rect(surface, (70, 85, 105), box, width=2, border_radius=2)
                t_lbl = small_font.render("VALUATION: DCF = FCF / (WACC - g)", True, (25, 35, 55))
                surface.blit(t_lbl, (rx + 4, ry + 3))
            else:
                pygame.draw.rect(surface, (12, 18, 30), box, border_radius=2)
                pygame.draw.rect(surface, (40, 80, 120), box, width=1, border_radius=2)
                pygame.draw.line(surface, (72, 202, 228), (rx + 4, ry + obj.h // 2), (rx + obj.w - 4, ry + obj.h // 2 - 4), 1)

        elif obj.type == "bull_statue":
            if self.bull_img:
                surface.blit(self.bull_img, (rx, ry))
                return
            pygame.draw.rect(surface, (130, 85, 25), (rx, ry + obj.h - 10, obj.w, 10), border_radius=2)
            pygame.draw.ellipse(surface, (215, 145, 55), (rx + 6, ry + 4, obj.w - 12, obj.h - 12))

        elif obj.type == "landmark":
            if obj.id == "bse_bell":
                pygame.draw.rect(surface, (140, 100, 40), (rx + 4, ry + 6, max(4, obj.w - 8), max(4, obj.h - 8)), border_radius=2)
                pygame.draw.ellipse(surface, (245, 205, 80), (rx + 6, ry + 4, max(4, obj.w - 12), max(4, obj.h - 8)))
                pygame.draw.ellipse(surface, (218, 165, 32), (rx + 6, ry + 4, max(4, obj.w - 12), max(4, obj.h - 8)), width=2)
            elif "exhibit" in obj.id:
                pygame.draw.rect(surface, (12, 16, 24), (rx, ry + obj.h, obj.w, 4))
                pygame.draw.rect(surface, (75, 45, 30), (rx + 4, ry + obj.h // 2, max(4, obj.w - 8), max(4, obj.h // 2)), border_radius=2)
                pygame.draw.rect(surface, (180, 215, 240), (rx + 6, ry + 2, max(4, obj.w - 12), max(4, obj.h // 2 + 2)), border_radius=2)
                pygame.draw.rect(surface, (218, 165, 32), (rx + 6, ry + 2, max(4, obj.w - 12), max(4, obj.h // 2 + 2)), width=1, border_radius=2)
                pygame.draw.line(surface, (255, 255, 255), (rx + 8, ry + 4), (rx + min(obj.w - 8, 18), ry + 4), 1)
            elif "egg_golden_bull" in obj.id:
                pygame.draw.rect(surface, (45, 35, 25), (rx + 4, ry + obj.h - 8, max(4, obj.w - 8), 8), border_radius=1)
                pygame.draw.ellipse(surface, (255, 215, 0), (rx + 6, ry + 4, max(4, obj.w - 12), max(4, obj.h - 10)))
                shimmer = int(tick_count * 0.2) % 4
                pygame.draw.circle(surface, (255, 255, 255), (rx + 8 + shimmer * 6, ry + 6), 2)
            elif "egg_vintage_ticker" in obj.id:
                pygame.draw.rect(surface, (140, 100, 35), (rx + 4, ry + 6, max(4, obj.w - 8), max(4, obj.h - 8)), border_radius=2)
                pygame.draw.circle(surface, (230, 190, 60), (rx + obj.w // 2, ry + 10), 6)
                pygame.draw.line(surface, (245, 245, 230), (rx + obj.w // 2 + 4, ry + 10), (rx + obj.w - 2, ry + obj.h - 2), 2)
            elif "boardroom" in obj.id:
                pygame.draw.ellipse(surface, (85, 52, 35), (rx, ry, obj.w, obj.h))
                pygame.draw.ellipse(surface, (125, 78, 52), (rx + 3, ry + 3, max(2, obj.w - 6), max(2, obj.h - 6)), width=2)
            elif self.banyan_img and obj.id == "banyan_tree":
                surface.blit(self.banyan_img, (rx, ry))
            else:
                # Generic landmark fallback
                pygame.draw.rect(surface, (95, 60, 40), (rx + obj.w // 2 - 8, ry + obj.h // 2, 16, obj.h // 2))
                pygame.draw.circle(surface, (40, 115, 65), (rx + obj.w // 2, ry + obj.h // 2 - 6), 26)

        elif obj.type == "chai_stall":
            box = pygame.Rect(rx, ry, obj.w, obj.h)
            pygame.draw.rect(surface, (175, 60, 45), box, border_radius=2)
            for si in range(6):
                c_col = (245, 215, 80) if si % 2 == 0 else (210, 45, 35)
                pygame.draw.rect(surface, c_col, (rx + si * (obj.w // 6), ry, obj.w // 6, 8))
            pygame.draw.ellipse(surface, (215, 125, 45), (rx + obj.w // 2 - 6, ry + 12, 12, 12))

        elif obj.type == "transit":
            box = pygame.Rect(rx, ry, obj.w, obj.h)
            pygame.draw.rect(surface, (14, 20, 36), box, border_radius=4)
            pygame.draw.rect(surface, COLOR_BORDER_ACCENT, box, width=2, border_radius=4)
            m_surf = font.render("M", True, COLOR_BORDER_ACCENT)
            surface.blit(m_surf, m_surf.get_rect(center=box.center))

        elif obj.type == "sign":
            pygame.draw.rect(surface, (80, 50, 30), (rx + 7, ry + 8, 4, 10))
            pygame.draw.rect(surface, (215, 190, 145), (rx, ry, 18, 12), border_radius=2)
            pygame.draw.rect(surface, (70, 45, 25), (rx, ry, 18, 12), width=1, border_radius=2)

    def _draw_prompt(self, surface: pygame.Surface, cam_offset: Tuple[int, int], entity: Any, 
                     font: pygame.font.Font, small_font: pygame.font.Font, tick_count: int):
        """Draw hovering prompt with clear context-sensitive label and target highlight."""
        if hasattr(entity, 'width'):
            # NPC
            cx = entity.x + entity.width / 2 - cam_offset[0]
            top_y = entity.y - cam_offset[1]
            label = f"[E] Talk to {entity.name}"
            # Pulse highlight ring around feet
            pulse_r = 10 + int(math.sin(tick_count * 0.15) * 2)
            pygame.draw.ellipse(surface, (*COLOR_BORDER_ACCENT, 180), (cx - pulse_r, top_y + entity.height - 4, pulse_r * 2, 6), width=1)
        else:
            # World Object
            cx = entity.x + entity.w / 2 - cam_offset[0]
            top_y = entity.y - cam_offset[1]
            if entity.action_type == "enter_interior":
                label = f"[E] Enter {entity.title}"
            elif entity.action_type == "exit_interior":
                label = "[E] Exit to Street"
            elif entity.action_type == "open_trading":
                label = f"[E] Open Floor Trading Terminal"
            elif entity.action_type == "open_academy":
                label = f"[E] Access Research Archive"
            elif entity.action_type == "exchange_hub":
                label = f"[E] Enter {entity.title}"
            elif entity.action_type == "company_dossier":
                label = f"[E] Inspect {entity.title}"
            elif entity.action_type == "bull_statue":
                label = "[E] Inspect Charging Bull Monument"
            elif entity.action_type == "banyan_tree":
                label = "[E] Inspect Historic 1875 Banyan Tree"
            elif entity.action_type == "chai_stall":
                label = "[E] Order Cutting Chai & Hear Rumors"
            elif entity.action_type == "bank_account":
                label = f"[E] Enter {entity.title}"
            elif entity.action_type == "financial_academy":
                label = f"[E] Enter {entity.title}"
            elif entity.action_type == "news_station":
                label = f"[E] Enter {entity.title}"
            elif entity.action_type == "transit":
                label = f"[E] Travel ({entity.title})"
            else:
                label = f"[E] Inspect {entity.title}"

        # Draw glowing retro prompt pill
        txt_surf = font.render(label, True, COLOR_TEXT_WHITE)
        pill_rect = pygame.Rect(0, 0, txt_surf.get_width() + 14, txt_surf.get_height() + 8)
        pill_rect.centerx = int(cx)
        pill_rect.bottom = int(top_y - 6)

        # Keep pill on screen
        pill_rect.clamp_ip(surface.get_rect())

        pygame.draw.rect(surface, (12, 18, 36), pill_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_BORDER_ACCENT, pill_rect, width=1, border_radius=4)
        surface.blit(txt_surf, (pill_rect.x + 7, pill_rect.y + 4))
