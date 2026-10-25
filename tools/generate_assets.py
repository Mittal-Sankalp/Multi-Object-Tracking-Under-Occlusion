"""
MarketQuest - Enhanced Retro Pixel-Art Asset Generator
Generates pixel-art characters, architectural landmarks, bull statue, banyan tree,
and street decorations for Wall Street and Dalal Street.
"""

import os
from pathlib import Path
import pygame

def create_pixel_surfaces():
    pygame.init()
    base_dir = Path(__file__).resolve().parent.parent
    sprites_dir = base_dir / "assets" / "sprites"
    sprites_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------
    # 1. PLAYER SPRITE SHEET (4 directions x 4 frames: stand, step1, stand, step2)
    # Size: 16x24 per frame
    # -------------------------------------------------------------
    p_sheet = pygame.Surface((16 * 4, 24 * 4), pygame.SRCALPHA)
    directions = ["down", "up", "left", "right"]

    for row, d in enumerate(directions):
        for col in range(4):
            fx = col * 16
            fy = row * 24

            # Shadow at feet
            pygame.draw.ellipse(p_sheet, (10, 14, 25, 140), (fx + 2, fy + 20, 12, 4))

            # Suit & Coat (Charcoal navy blazer, crisp white shirt, gold tie)
            pygame.draw.rect(p_sheet, (24, 45, 85), (fx + 2, fy + 8, 12, 9), border_radius=2)
            pygame.draw.rect(p_sheet, (240, 245, 255), (fx + 5, fy + 8, 6, 4))  # White shirt collar
            pygame.draw.line(p_sheet, (255, 185, 30), (fx + 7, fy + 9), (fx + 7, fy + 14), 2)  # Gold tie

            # Head & Hair (Warm skin, groomed brown hair)
            pygame.draw.rect(p_sheet, (245, 195, 150), (fx + 3, fy + 2, 10, 7), border_radius=1)
            pygame.draw.rect(p_sheet, (75, 45, 25), (fx + 3, fy + 1, 10, 3), border_radius=1)

            # Directional Face details
            if d == "down":
                p_sheet.set_at((fx + 5, fy + 5), (30, 30, 45))
                p_sheet.set_at((fx + 6, fy + 5), (30, 30, 45))
                p_sheet.set_at((fx + 9, fy + 5), (30, 30, 45))
                p_sheet.set_at((fx + 10, fy + 5), (30, 30, 45))
            elif d == "left":
                p_sheet.set_at((fx + 4, fy + 5), (30, 30, 45))
                p_sheet.set_at((fx + 5, fy + 5), (30, 30, 45))
            elif d == "right":
                p_sheet.set_at((fx + 10, fy + 5), (30, 30, 45))
                p_sheet.set_at((fx + 11, fy + 5), (30, 30, 45))
            elif d == "up":
                # Back of hair
                pygame.draw.rect(p_sheet, (75, 45, 25), (fx + 3, fy + 2, 10, 5))

            # Trousers & Stepping animation
            leg_l_off = 0
            leg_r_off = 0
            if col == 1:
                leg_l_off = 1
                leg_r_off = -1
            elif col == 3:
                leg_l_off = -1
                leg_r_off = 1

            pygame.draw.rect(p_sheet, (20, 26, 40), (fx + 3, fy + 17, 4, 6 + leg_l_off))
            pygame.draw.rect(p_sheet, (20, 26, 40), (fx + 9, fy + 17, 4, 6 + leg_r_off))
            # Black polished shoes
            pygame.draw.rect(p_sheet, (10, 10, 15), (fx + 2, fy + 22 + leg_l_off, 5, 2))
            pygame.draw.rect(p_sheet, (10, 10, 15), (fx + 9, fy + 22 + leg_r_off, 5, 2))

    pygame.image.save(p_sheet, str(sprites_dir / "player_sheet.png"))
    print("Generated player_sheet.png")

    # -------------------------------------------------------------
    # 2. DISTINCT NPC SPRITES
    # -------------------------------------------------------------
    # Arthur Pendelton: Gray hair, long camel wool trench coat, burgundy scarf
    arthur_surf = pygame.Surface((16, 24), pygame.SRCALPHA)
    pygame.draw.ellipse(arthur_surf, (10, 14, 25, 140), (2, 20, 12, 4))
    pygame.draw.rect(arthur_surf, (160, 120, 70), (2, 7, 12, 12), border_radius=2)  # Trench coat
    pygame.draw.rect(arthur_surf, (130, 20, 40), (5, 7, 6, 4))  # Scarf
    pygame.draw.rect(arthur_surf, (240, 190, 150), (3, 2, 10, 6))  # Face
    pygame.draw.rect(arthur_surf, (180, 185, 195), (3, 1, 10, 3))  # Silver hair
    arthur_surf.set_at((5, 4), (20, 20, 30))
    arthur_surf.set_at((9, 4), (20, 20, 30))
    pygame.draw.rect(arthur_surf, (40, 35, 30), (3, 19, 4, 4))
    pygame.draw.rect(arthur_surf, (40, 35, 30), (9, 19, 4, 4))
    pygame.image.save(arthur_surf, str(sprites_dir / "npc_arthur.png"))

    # Sterling Vance: Black turtleneck, sleek dark swept-back hair, dark slacks
    sterling_surf = pygame.Surface((16, 24), pygame.SRCALPHA)
    pygame.draw.ellipse(sterling_surf, (10, 14, 25, 140), (2, 20, 12, 4))
    pygame.draw.rect(sterling_surf, (25, 25, 30), (3, 7, 10, 10), border_radius=1)  # Turtleneck
    pygame.draw.rect(sterling_surf, (245, 195, 155), (4, 2, 8, 6))  # Face
    pygame.draw.rect(sterling_surf, (30, 25, 25), (4, 1, 8, 3))  # Black hair
    sterling_surf.set_at((5, 4), (40, 40, 50))
    sterling_surf.set_at((8, 4), (40, 40, 50))
    pygame.draw.rect(sterling_surf, (50, 60, 75), (4, 17, 3, 6))
    pygame.draw.rect(sterling_surf, (50, 60, 75), (9, 17, 3, 6))
    pygame.image.save(sterling_surf, str(sprites_dir / "npc_sterling.png"))

    # Victoria Vance: Sharp amethyst blazer, pearl necklace, tablet clipboard
    victoria_surf = pygame.Surface((16, 24), pygame.SRCALPHA)
    pygame.draw.ellipse(victoria_surf, (10, 14, 25, 140), (2, 20, 12, 4))
    pygame.draw.rect(victoria_surf, (90, 45, 110), (3, 7, 10, 10), border_radius=2)  # Purple blazer
    pygame.draw.rect(victoria_surf, (250, 200, 160), (4, 2, 8, 6))
    pygame.draw.rect(victoria_surf, (120, 65, 30), (3, 1, 10, 4))  # Auburn hair
    victoria_surf.set_at((5, 4), (30, 30, 40))
    victoria_surf.set_at((8, 4), (30, 30, 40))
    pygame.draw.rect(victoria_surf, (220, 220, 230), (1, 10, 3, 5))  # Tablet in hand
    pygame.draw.rect(victoria_surf, (30, 30, 40), (4, 17, 3, 6))
    pygame.draw.rect(victoria_surf, (30, 30, 40), (9, 17, 3, 6))
    pygame.image.save(victoria_surf, str(sprites_dir / "npc_victoria.png"))

    # Priya Sharma: Formal Indian attire (saffron & gold kurta), press ID badge
    priya_surf = pygame.Surface((16, 24), pygame.SRCALPHA)
    pygame.draw.ellipse(priya_surf, (10, 14, 25, 140), (2, 20, 12, 4))
    pygame.draw.rect(priya_surf, (230, 95, 35), (3, 7, 10, 11), border_radius=2)  # Saffron kurta
    pygame.draw.line(priya_surf, (255, 215, 60), (7, 8), (7, 17), 2)  # Gold embroidery
    pygame.draw.rect(priya_surf, (220, 160, 115), (4, 2, 8, 6))  # Warm complexion
    pygame.draw.rect(priya_surf, (25, 20, 20), (3, 1, 10, 4))  # Dark lustrous hair
    priya_surf.set_at((5, 4), (20, 20, 20))
    priya_surf.set_at((8, 4), (20, 20, 20))
    pygame.draw.rect(priya_surf, (240, 240, 240), (10, 11, 4, 3))  # Press pass
    pygame.draw.rect(priya_surf, (240, 230, 210), (4, 18, 3, 5))
    pygame.draw.rect(priya_surf, (240, 230, 210), (9, 18, 3, 5))
    pygame.image.save(priya_surf, str(sprites_dir / "npc_priya.png"))

    # Devendra Patel: Stately ivory/teal Nehru jacket, pocket square, spectacles
    devendra_surf = pygame.Surface((16, 24), pygame.SRCALPHA)
    pygame.draw.ellipse(devendra_surf, (10, 14, 25, 140), (2, 20, 12, 4))
    pygame.draw.rect(devendra_surf, (35, 125, 110), (3, 7, 10, 11), border_radius=2)  # Teal Nehru jacket
    pygame.draw.rect(devendra_surf, (255, 70, 70), (5, 9, 2, 2))  # Red silk pocket square
    pygame.draw.rect(devendra_surf, (225, 170, 120), (4, 2, 8, 6))
    pygame.draw.rect(devendra_surf, (190, 190, 200), (4, 1, 8, 3))  # Graying neat hair
    # Spectacles
    devendra_surf.set_at((5, 4), (240, 210, 50))
    devendra_surf.set_at((8, 4), (240, 210, 50))
    pygame.draw.rect(devendra_surf, (220, 215, 200), (4, 18, 3, 5))
    pygame.draw.rect(devendra_surf, (220, 215, 200), (9, 18, 3, 5))
    pygame.image.save(devendra_surf, str(sprites_dir / "npc_devendra.png"))

    # Charlie the Floor Trader: Striped trader smock, headset, pencil
    charlie_surf = pygame.Surface((16, 24), pygame.SRCALPHA)
    pygame.draw.ellipse(charlie_surf, (10, 14, 25, 140), (2, 20, 12, 4))
    pygame.draw.rect(charlie_surf, (220, 180, 50), (3, 7, 10, 10), border_radius=1)  # Yellow trader vest
    pygame.draw.line(charlie_surf, (30, 30, 40), (5, 7), (5, 16), 1)
    pygame.draw.line(charlie_surf, (30, 30, 40), (8, 7), (8, 16), 1)
    pygame.draw.rect(charlie_surf, (245, 195, 150), (4, 2, 8, 6))
    pygame.draw.rect(charlie_surf, (150, 75, 30), (4, 1, 8, 3))
    # Headset
    pygame.draw.rect(charlie_surf, (80, 80, 90), (3, 2, 2, 4))
    charlie_surf.set_at((5, 4), (20, 20, 30))
    charlie_surf.set_at((8, 4), (20, 20, 30))
    pygame.draw.rect(charlie_surf, (40, 40, 55), (4, 17, 3, 6))
    pygame.draw.rect(charlie_surf, (40, 40, 55), (9, 17, 3, 6))
    pygame.image.save(charlie_surf, str(sprites_dir / "npc_charlie.png"))

    # President Donald Vance (Inspired by Trump): Navy suit, long red tie, golden hair
    us_surf = pygame.Surface((16, 24), pygame.SRCALPHA)
    pygame.draw.ellipse(us_surf, (10, 14, 25, 140), (2, 20, 12, 4))
    pygame.draw.rect(us_surf, (20, 35, 70), (2, 7, 12, 10), border_radius=2)  # Navy suit
    pygame.draw.rect(us_surf, (250, 250, 250), (5, 7, 6, 3))  # White shirt collar
    pygame.draw.line(us_surf, (220, 40, 45), (7, 8), (7, 17), 2)  # Red tie
    pygame.draw.rect(us_surf, (250, 195, 150), (4, 2, 8, 6))  # Face
    pygame.draw.rect(us_surf, (240, 200, 70), (3, 1, 10, 4))  # Golden swept hair
    us_surf.set_at((5, 4), (25, 25, 35))
    us_surf.set_at((8, 4), (25, 25, 35))
    pygame.draw.rect(us_surf, (20, 30, 55), (3, 17, 4, 6))
    pygame.draw.rect(us_surf, (20, 30, 55), (9, 17, 4, 6))
    pygame.image.save(us_surf, str(sprites_dir / "npc_leader_us.png"))

    # PM Narendra Deshmukh (Inspired by Modi): Crisp white kurta, saffron vest, silver hair/beard
    ind_surf = pygame.Surface((16, 24), pygame.SRCALPHA)
    pygame.draw.ellipse(ind_surf, (10, 14, 25, 140), (2, 20, 12, 4))
    pygame.draw.rect(ind_surf, (250, 250, 250), (2, 7, 12, 11), border_radius=2)  # White kurta
    pygame.draw.rect(ind_surf, (240, 130, 40), (4, 7, 8, 9), border_radius=1)  # Saffron vest
    pygame.draw.rect(ind_surf, (225, 175, 125), (4, 2, 8, 6))  # Face
    pygame.draw.rect(ind_surf, (230, 230, 235), (4, 1, 8, 3))  # Silver hair
    pygame.draw.rect(ind_surf, (230, 230, 235), (5, 6, 6, 2))  # Neat silver beard
    ind_surf.set_at((5, 4), (25, 25, 30))
    ind_surf.set_at((8, 4), (25, 25, 30))
    pygame.draw.rect(ind_surf, (245, 245, 245), (3, 18, 4, 5))
    pygame.draw.rect(ind_surf, (245, 245, 245), (9, 18, 4, 5))
    pygame.image.save(ind_surf, str(sprites_dir / "npc_leader_india.png"))

    # Elena Rostova: Lab coat over violet turtleneck
    elena_surf = pygame.Surface((16, 24), pygame.SRCALPHA)
    pygame.draw.ellipse(elena_surf, (10, 14, 25, 140), (2, 20, 12, 4))
    pygame.draw.rect(elena_surf, (240, 245, 250), (2, 7, 12, 10), border_radius=2)  # White lab coat
    pygame.draw.rect(elena_surf, (120, 45, 140), (6, 7, 4, 8))  # Violet top
    pygame.draw.rect(elena_surf, (245, 200, 160), (4, 2, 8, 6))
    pygame.draw.rect(elena_surf, (50, 30, 25), (3, 1, 10, 4))  # Dark brown bob
    elena_surf.set_at((5, 4), (30, 30, 40))
    elena_surf.set_at((8, 4), (30, 30, 40))
    pygame.draw.rect(elena_surf, (30, 40, 60), (4, 17, 3, 6))
    pygame.draw.rect(elena_surf, (30, 40, 60), (9, 17, 3, 6))
    pygame.image.save(elena_surf, str(sprites_dir / "npc_elena.png"))

    print("Generated all NPC sprites.")

    # -------------------------------------------------------------
    # 3. PROMINENT CHARGING BULL MONUMENT (72x48)
    # Tiered stone pedestal, plaque, muscular bronze bull, curved horns
    # -------------------------------------------------------------
    bull_surf = pygame.Surface((72, 48), pygame.SRCALPHA)
    # 1. Shadow
    pygame.draw.ellipse(bull_surf, (10, 14, 25, 150), (4, 34, 64, 12))
    # 2. Multi-tiered Granite Pedestal
    pygame.draw.rect(bull_surf, (110, 115, 130), (8, 34, 56, 10), border_radius=2)
    pygame.draw.rect(bull_surf, (140, 145, 160), (12, 30, 48, 6), border_radius=1)
    # Brass plaque on pedestal
    pygame.draw.rect(bull_surf, (218, 165, 32), (24, 36, 24, 5), border_radius=1)
    pygame.draw.rect(bull_surf, (160, 110, 20), (24, 36, 24, 5), width=1)

    # 3. Bronze Charging Bull Body (Muscular, low forward-charging stance)
    # Torso & Shoulders
    pygame.draw.ellipse(bull_surf, (185, 115, 35), (14, 10, 42, 22))  # Main body
    pygame.draw.circle(bull_surf, (165, 95, 25), (46, 20), 11)        # Powerful shoulder hunch
    pygame.draw.ellipse(bull_surf, (205, 135, 45), (18, 12, 34, 14))  # Highlight
    # Head lowered forward
    pygame.draw.polygon(bull_surf, (185, 115, 35), [(46, 16), (62, 24), (54, 30), (44, 26)])
    # Sharp forward-curving horns
    pygame.draw.polygon(bull_surf, (245, 195, 80), [(50, 16), (58, 8), (56, 17)])
    pygame.draw.polygon(bull_surf, (245, 195, 80), [(54, 20), (66, 12), (60, 22)])
    # Snout
    pygame.draw.circle(bull_surf, (150, 85, 20), (61, 26), 4)
    # Sturdy bronze legs
    # Forelegs braced
    pygame.draw.rect(bull_surf, (160, 95, 25), (42, 24, 5, 10))
    pygame.draw.rect(bull_surf, (140, 80, 20), (50, 24, 5, 9))
    # Hindlegs pushing
    pygame.draw.rect(bull_surf, (160, 95, 25), (16, 24, 5, 10))
    pygame.draw.rect(bull_surf, (140, 80, 20), (24, 23, 5, 10))
    # Tail curling
    pygame.draw.arc(bull_surf, (160, 95, 25), (8, 14, 12, 16), 1.0, 4.0, 2)

    pygame.image.save(bull_surf, str(sprites_dir / "bull_monument.png"))
    print("Generated bull_monument.png")

    # -------------------------------------------------------------
    # 4. HISTORIC DALAL STREET BANYAN TREE (72x72)
    # Massive sprawling canopy, aerial roots, stone seating ring
    # -------------------------------------------------------------
    banyan_surf = pygame.Surface((72, 72), pygame.SRCALPHA)
    # Shadow
    pygame.draw.ellipse(banyan_surf, (12, 16, 28, 150), (4, 46, 64, 22))
    # Stone seating ring around trunk (where 1875 brokers sat!)
    pygame.draw.ellipse(banyan_surf, (180, 155, 125), (18, 50, 36, 16))
    pygame.draw.ellipse(banyan_surf, (130, 105, 80), (18, 50, 36, 16), width=2)
    # Brass historic plaque
    pygame.draw.rect(banyan_surf, (220, 175, 40), (30, 58, 12, 4))

    # Gnarled trunk & aerial prop roots
    pygame.draw.rect(banyan_surf, (95, 60, 40), (30, 32, 12, 24), border_radius=2)
    # Hanging prop roots
    for rx_off in [22, 27, 44, 49]:
        pygame.draw.line(banyan_surf, (80, 50, 32), (rx_off, 30), (rx_off, 56), 2)

    # Lush leafy canopy layers
    pygame.draw.circle(banyan_surf, (28, 85, 48), (36, 24), 28)
    pygame.draw.circle(banyan_surf, (36, 110, 60), (28, 20), 22)
    pygame.draw.circle(banyan_surf, (44, 125, 68), (44, 22), 20)
    pygame.draw.circle(banyan_surf, (52, 145, 78), (36, 14), 16)
    # Highlights
    pygame.draw.circle(banyan_surf, (70, 165, 95), (32, 12), 8)
    pygame.draw.circle(banyan_surf, (70, 165, 95), (42, 16), 6)

    pygame.image.save(banyan_surf, str(sprites_dir / "banyan_historic.png"))
    print("Generated banyan_historic.png")

    # -------------------------------------------------------------
    # 5. STREET FURNITURE & DECORATIONS
    # Street lamp (with light cone), bench, chai kettle stall
    # -------------------------------------------------------------
    # Street Lamp (16x32)
    lamp_surf = pygame.Surface((16, 32), pygame.SRCALPHA)
    pygame.draw.rect(lamp_surf, (40, 45, 55), (7, 6, 2, 24))  # Pole
    pygame.draw.rect(lamp_surf, (30, 35, 45), (5, 28, 6, 4))  # Base
    pygame.draw.polygon(lamp_surf, (30, 35, 45), [(4, 6), (12, 6), (8, 2)])  # Cap
    pygame.draw.rect(lamp_surf, (255, 235, 140), (5, 6, 6, 6), border_radius=1)  # Glowing lantern
    pygame.image.save(lamp_surf, str(sprites_dir / "street_lamp.png"))

    # Bench (24x16)
    bench_surf = pygame.Surface((24, 16), pygame.SRCALPHA)
    pygame.draw.rect(bench_surf, (140, 90, 50), (2, 4, 20, 5), border_radius=1)  # Wood seat
    pygame.draw.rect(bench_surf, (120, 75, 40), (2, 0, 20, 4), border_radius=1)  # Backrest
    pygame.draw.rect(bench_surf, (30, 35, 45), (3, 8, 2, 7))  # Iron legs
    pygame.draw.rect(bench_surf, (30, 35, 45), (19, 8, 2, 7))
    pygame.image.save(bench_surf, str(sprites_dir / "street_bench.png"))

    print("All graphic assets successfully created!")

if __name__ == "__main__":
    create_pixel_surfaces()
