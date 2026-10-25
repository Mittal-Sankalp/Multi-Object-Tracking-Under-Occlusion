"""
MarketQuest - Enhanced UI Component Library & Modals
Provides retro buttons, HUD with Live Clock, Trading Terminal with Confirmation,
Portfolio with Full Company Names, News Pop-up Toast, Exchange Hub, and Company Dossiers.
Strictly eliminates UI text overflow through font-metric wrapping and clipping.
"""

import pygame
import math
from typing import Dict, List, Tuple, Optional, Any
from config import (
    VIRTUAL_WIDTH, VIRTUAL_HEIGHT,
    COLOR_BG_DARK, COLOR_PANEL_BG, COLOR_PANEL_ALT, COLOR_BORDER, COLOR_BORDER_ACCENT,
    COLOR_TEXT_WHITE, COLOR_TEXT_MUTED, COLOR_TEXT_GOLD,
    COLOR_GAIN, COLOR_GAIN_BRIGHT, COLOR_LOSS, COLOR_LOSS_BRIGHT,
    LOCATION_WALL_STREET, LOCATION_DALAL_STREET, LOCATION_KABUTOCHO, LOCATION_LONDON,
    UNLOCK_PROFIT_NYSE, UNLOCK_PROFIT_TSE, UNLOCK_PROFIT_LSE,
    INTERIOR_BSE
)
from src.sound import SoundManager
from src.charts import StockChartRenderer
from src.text_util import wrap_text, truncate_text, render_wrapped_text
from src.clock import EXCHANGE_BSE, EXCHANGE_NYSE, EXCHANGE_TSE, EXCHANGE_LSE

class Button:
    def __init__(self, rect: pygame.Rect, text: str, font: pygame.font.Font,
                 bg_color: Tuple[int, int, int] = COLOR_PANEL_ALT,
                 hover_color: Tuple[int, int, int] = (38, 56, 102),
                 text_color: Tuple[int, int, int] = COLOR_TEXT_WHITE,
                 border_color: Tuple[int, int, int] = COLOR_BORDER,
                 enabled: bool = True):
        self.rect = rect
        self.text = text
        self.font = font
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.border_color = border_color
        self.enabled = enabled
        self.is_hovered = False

    def handle_event(self, event: pygame.event.Event, mouse_pos: Tuple[int, int]) -> bool:
        if not self.enabled:
            return False

        self.is_hovered = self.rect.collidepoint(mouse_pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                SoundManager.get_instance().play("click")
                return True
        return False

    def draw(self, surface: pygame.Surface):
        if not self.enabled:
            fill = (20, 24, 38)
            t_col = (80, 90, 110)
            b_col = (30, 36, 52)
        elif self.is_hovered:
            fill = self.hover_color
            t_col = COLOR_TEXT_GOLD
            b_col = COLOR_BORDER_ACCENT
        else:
            fill = self.bg_color
            t_col = self.text_color
            b_col = self.border_color

        pygame.draw.rect(surface, fill, self.rect, border_radius=4)
        pygame.draw.rect(surface, b_col, self.rect, width=1, border_radius=4)

        t_surf = self.font.render(self.text, True, t_col)
        t_rect = t_surf.get_rect(center=self.rect.center)
        surface.blit(t_surf, t_rect)


class UIManager:
    def __init__(self, font: pygame.font.Font, small_font: pygame.font.Font, title_font: pygame.font.Font):
        self.font = font
        self.small_font = small_font
        self.title_font = title_font
        self.chart_renderer = StockChartRenderer(font, small_font)

        # Trading state
        self.selected_symbol: str = "APEX"
        self.trade_qty: int = 1
        self.trade_status_msg: str = "Select a stock to view live charts and trade."
        self.trade_status_is_error: bool = False
        self.trade_status_timer: float = 0.0

        # Confirmation Dialog State
        self.pending_order: Optional[Dict[str, Any]] = None

        # Company Dossier Inspection State
        self.inspected_symbol: str = "APEX"

        # News Pop-up Toast State
        self.toast_item: Optional[Dict[str, Any]] = None
        self.toast_timer: float = 0.0

        # Scroll positions
        self.news_scroll_offset: int = 0
        self.portfolio_scroll_offset: int = 0
        self.trade_log_scroll_offset: int = 0

        # Tutorial modal
        self.show_tutorial: bool = False

        # Return Breakdown & Educational Layers state
        self.breakdown_symbol: str = "CHAI"
        self.education_layer: int = 1

        # Investment Thesis Formulation state
        self.thesis_symbol: str = "CHAI"
        self.thesis_confidence: str = "High"
        self.thesis_horizon: str = "1-2 Weeks"
        self.thesis_size_pct: float = 25.0

        # Story Campaign inspection state
        self.campaign_selected_chapter: int = 0

    def set_trade_message(self, msg: str, is_error: bool = False):
        self.trade_status_msg = msg
        self.trade_status_is_error = is_error
        self.trade_status_timer = 5.0

    def trigger_news_toast(self, news_item: Dict[str, Any]):
        self.toast_item = news_item
        self.toast_timer = 6.0

    def update(self, dt: float):
        if self.trade_status_timer > 0:
            self.trade_status_timer -= dt
        if self.toast_timer > 0:
            self.toast_timer -= dt
            if self.toast_timer <= 0:
                self.toast_item = None

    # -------------------------------------------------------------
    # HUD WITH PERSISTENT CLOCK & LIVE EXCHANGE SCHEDULE
    # -------------------------------------------------------------
    def draw_hud(self, surface: pygame.Surface, game_state: Any):
        m = game_state.market
        p = game_state.portfolio
        w = game_state.world
        clock = game_state.clock

        # Top Bar Background (h=26)
        top_bar = pygame.Rect(0, 0, VIRTUAL_WIDTH, 26)
        pygame.draw.rect(surface, (12, 18, 36), top_bar)
        pygame.draw.line(surface, COLOR_BORDER, (0, 26), (VIRTUAL_WIDTH, 26), 1)

        # 1. District Local Time & Exchange Status
        loc_time = clock.get_local_time_for_location(w.current_location_id)
        
        # Name resolution for outdoor & indoor locations
        loc_id = w.current_location_id
        if "wall_street" in loc_id or "nyse" in loc_id or "white_house" in loc_id or "apex" in loc_id:
            loc_name = "Wall Street, NYC"
            curr_ex = EXCHANGE_NYSE
        elif "kabutocho" in loc_id or "tse" in loc_id:
            loc_name = "Kabutocho, Tokyo"
            curr_ex = EXCHANGE_TSE
        elif "paternoster" in loc_id or "london" in loc_id or "lse" in loc_id:
            loc_name = "Paternoster Sq, London"
            curr_ex = EXCHANGE_LSE
        else:
            loc_name = "Dalal Street, Mumbai"
            curr_ex = EXCHANGE_BSE

        tz_str = loc_time.strftime("%H:%M %Z")
        ex_stat = clock.get_exchange_status(curr_ex)
        dot_col = (85, 230, 110) if ex_stat["status"] == "OPEN" else (255, 75, 92)

        # Draw status dot
        pygame.draw.circle(surface, dot_col, (10, 13), 4)
        clock_str = f"{loc_name} ({curr_ex}: {ex_stat['status']}) {tz_str}"
        surface.blit(self.small_font.render(clock_str, True, COLOR_TEXT_GOLD), (18, 6))

        # 2. Player Level & XP Badge
        lvl, title, cur_min, next_thresh, ratio = game_state.investigation.get_level_info(game_state.xp)
        lvl_str = f"Lvl {lvl} [{int(ratio * 100)}%]"
        surface.blit(self.small_font.render(lvl_str, True, COLOR_BORDER_ACCENT), (235, 6))

        # 3. Virtual Cash & Net Worth
        cash_str = f"${p.cash:,.0f}"
        net_worth = p.get_total_value(m)
        tot_ret_pct = p.get_total_return_pct(m)
        ret_sign = "+" if tot_ret_pct >= 0 else ""
        ret_col = COLOR_GAIN_BRIGHT if tot_ret_pct >= 0 else COLOR_LOSS_BRIGHT

        cash_surf = self.small_font.render(f"Cash: {cash_str}", True, COLOR_TEXT_WHITE)
        worth_str = f"Net: ${net_worth:,.0f} ({ret_sign}{tot_ret_pct:.1f}%)"
        worth_surf = self.small_font.render(worth_str, True, ret_col)

        surface.blit(cash_surf, (330, 6))
        surface.blit(worth_surf, (445, 6))

        # 4. Active Story Objective / Mission Card (Top-right pill)
        active_obj = None
        if hasattr(game_state, "story") and game_state.story:
            active_obj = game_state.story.get_active_objective()
        if not active_obj:
            active_obj = game_state.get_active_mission()

        if active_obj:
            m_title = active_obj.get("title", "")
            m_text = truncate_text(f"★ {m_title}", self.small_font, 210)
            m_surf = self.small_font.render(m_text, True, COLOR_TEXT_GOLD)
            m_bg = pygame.Rect(VIRTUAL_WIDTH - m_surf.get_width() - 14, 30, m_surf.get_width() + 10, 16)
            pygame.draw.rect(surface, (15, 24, 45), m_bg, border_radius=3)
            pygame.draw.rect(surface, COLOR_BORDER_ACCENT, m_bg, width=1, border_radius=3)
            surface.blit(m_surf, (m_bg.x + 5, m_bg.y + 2))

        # 4.5 Floor Trading Status & Route Guidance Badge (Top Left Pill)
        on_floor = game_state.is_on_trading_floor()
        floor_label = "FLOOR: ACTIVE" if on_floor else "FLOOR: RESTRICTED"
        floor_col = COLOR_GAIN_BRIGHT if on_floor else COLOR_TEXT_GOLD
        guide_on = getattr(game_state.player, "route_guidance_active", True)
        guide_label = "ROUTE [G]: ON" if guide_on else "ROUTE [G]: OFF"
        badge_txt = f"[{floor_label}]  [{guide_label}]"
        b_surf = self.small_font.render(badge_txt, True, floor_col)
        b_bg = pygame.Rect(8, 30, b_surf.get_width() + 10, 16)
        pygame.draw.rect(surface, (15, 24, 45), b_bg, border_radius=3)
        pygame.draw.rect(surface, COLOR_BORDER, b_bg, width=1, border_radius=3)
        surface.blit(b_surf, (b_bg.x + 5, b_bg.y + 2))

        # 5. Floating News Toast (Top-Right Pop-up)
        if self.toast_item and self.toast_timer > 0:
            self._draw_news_toast(surface)

        # 5.5 Interior Room Minimap (Bottom-Right Widget when inside an interior)
        if game_state.world.current_location_id.startswith("interior_"):
            mm_w = 84
            mm_h = 62
            mm_x = VIRTUAL_WIDTH - mm_w - 8
            mm_y = VIRTUAL_HEIGHT - mm_h - 22
            mm_rect = pygame.Rect(mm_x, mm_y, mm_w, mm_h)
            pygame.draw.rect(surface, (10, 16, 30), mm_rect, border_radius=4)
            pygame.draw.rect(surface, COLOR_BORDER_ACCENT, mm_rect, width=1, border_radius=4)
            
            m = game_state.world.current_map
            scale = min((mm_w - 6) / float(m.pixel_width), (mm_h - 6) / float(m.pixel_height))
            off_x = mm_x + 3
            off_y = mm_y + 3
            
            # Draw solids
            for s in m.solids:
                sx = int(off_x + s.x * scale)
                sy = int(off_y + s.y * scale)
                sw = max(1, int(s.w * scale))
                sh = max(1, int(s.h * scale))
                pygame.draw.rect(surface, (50, 70, 105), (sx, sy, sw, sh))
                
            # Draw player
            px = int(off_x + game_state.player.x * scale)
            py = int(off_y + game_state.player.y * scale)
            pygame.draw.circle(surface, COLOR_TEXT_GOLD, (px, py), 2)
            
            # Label
            mm_lbl = self.small_font.render("[M] Map", True, COLOR_BORDER_ACCENT)
            surface.blit(mm_lbl, (mm_x + mm_w - mm_lbl.get_width() - 3, mm_y + mm_h - 11))

        # 6. Bottom Controls Helper Bar
        bot_bar = pygame.Rect(0, VIRTUAL_HEIGHT - 18, VIRTUAL_WIDTH, 18)
        pygame.draw.rect(surface, (10, 15, 30), bot_bar)
        pygame.draw.line(surface, (25, 35, 60), (0, VIRTUAL_HEIGHT - 18), (VIRTUAL_WIDTH, VIRTUAL_HEIGHT - 18), 1)

        controls_str = "[WASD] Move  [E] Talk/Enter  [M] Map  [T] Terminal  [B] Breakdown  [J] Thesis  [C] Story  [G] Route  [ESC] Menu"
        ctrl_surf = self.small_font.render(controls_str, True, COLOR_TEXT_MUTED)
        surface.blit(ctrl_surf, (VIRTUAL_WIDTH // 2 - ctrl_surf.get_width() // 2, VIRTUAL_HEIGHT - 15))

    def _draw_news_toast(self, surface: pygame.Surface):
        item = self.toast_item
        if not item:
            return

        toast_w = 260
        toast_h = 48
        toast_x = VIRTUAL_WIDTH - toast_w - 10
        toast_y = 52

        box = pygame.Rect(toast_x, toast_y, toast_w, toast_h)
        pygame.draw.rect(surface, (14, 22, 42), box, border_radius=5)
        pygame.draw.rect(surface, COLOR_BORDER_ACCENT, box, width=1, border_radius=5)

        # Category and impact badge
        cat = item.get("category", "NEWS").upper()
        imp_str = item.get("impact_str", "")
        tgt = item.get("target", "")
        cat_surf = self.small_font.render(f"BREAKING: [{cat}] {imp_str} on {tgt}", True, COLOR_TEXT_GOLD)
        surface.blit(cat_surf, (toast_x + 8, toast_y + 5))

        # Wrapped headline
        head_text = truncate_text(item.get("headline", ""), self.small_font, toast_w - 16)
        surface.blit(self.small_font.render(head_text, True, COLOR_TEXT_WHITE), (toast_x + 8, toast_y + 19))

        # Prompt hint
        hint_surf = self.small_font.render("Press [N] to read full story", True, COLOR_TEXT_MUTED)
        surface.blit(hint_surf, (toast_x + 8, toast_y + 32))

    # -------------------------------------------------------------
    # TRADING TERMINAL SCREEN WITH CONFIRMATION MODAL
    # -------------------------------------------------------------
    def draw_trading_terminal(self, surface: pygame.Surface, game_state: Any, mouse_pos: Tuple[int, int]) -> List[Tuple[str, Button]]:
        buttons: List[Tuple[str, Button]] = []

        pygame.draw.rect(surface, COLOR_BG_DARK, (0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

        # Header
        h_rect = pygame.Rect(8, 6, VIRTUAL_WIDTH - 16, 26)
        pygame.draw.rect(surface, COLOR_PANEL_BG, h_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_BORDER, h_rect, width=1, border_radius=4)

        t_title = self.font.render("MARKET TERMINAL — ORDER EXECUTION", True, COLOR_TEXT_GOLD)
        surface.blit(t_title, (16, 10))

        cash_txt = self.small_font.render(f"Available Cash: ${game_state.portfolio.cash:,.2f}", True, COLOR_GAIN_BRIGHT)
        surface.blit(cash_txt, (VIRTUAL_WIDTH - cash_txt.get_width() - 80, 12))

        btn_close = Button(pygame.Rect(VIRTUAL_WIDTH - 70, 8, 56, 22), "ESC", self.small_font)
        buttons.append(("close", btn_close))

        # 1. Left Watchlist Panel
        w_rect = pygame.Rect(8, 36, 180, VIRTUAL_HEIGHT - 44)
        pygame.draw.rect(surface, COLOR_PANEL_BG, w_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_BORDER, w_rect, width=1, border_radius=4)

        w_head = self.small_font.render("WATCHLIST", True, COLOR_TEXT_MUTED)
        surface.blit(w_head, (16, 42))
        pygame.draw.line(surface, COLOR_BORDER, (8, 56), (188, 56), 1)

        comp_y = 60
        for comp in game_state.market.get_all_companies():
            is_sel = (comp.symbol == self.selected_symbol)
            row_rect = pygame.Rect(10, comp_y, 176, 38)
            row_btn = Button(row_rect, "", self.small_font,
                             bg_color=(28, 42, 78) if is_sel else (16, 24, 46),
                             hover_color=(36, 54, 98),
                             border_color=COLOR_BORDER_ACCENT if is_sel else COLOR_BORDER)
            buttons.append((f"select_{comp.symbol}", row_btn))
            row_btn.draw(surface)

            # Ticker & Sector
            sym_surf = self.font.render(comp.symbol, True, COLOR_TEXT_WHITE)
            sec_surf = self.small_font.render(comp.sector, True, COLOR_TEXT_MUTED)
            surface.blit(sym_surf, (14, comp_y + 4))
            surface.blit(sec_surf, (14, comp_y + 20))

            # Price & Change
            p_surf = self.small_font.render(f"${comp.price:.2f}", True, COLOR_TEXT_GOLD)
            sign = "+" if comp.change >= 0 else ""
            chg_col = COLOR_GAIN_BRIGHT if comp.change >= 0 else COLOR_LOSS_BRIGHT
            chg_surf = self.small_font.render(f"{sign}{comp.pct_change:.1f}%", True, chg_col)
            surface.blit(p_surf, (row_rect.right - p_surf.get_width() - 6, comp_y + 4))
            surface.blit(chg_surf, (row_rect.right - chg_surf.get_width() - 6, comp_y + 20))

            comp_y += 42

        # 2. Right Side: Chart & Company Info
        sel_comp = game_state.market.get_company(self.selected_symbol)
        if sel_comp:
            chart_rect = pygame.Rect(194, 36, VIRTUAL_WIDTH - 202, 175)
            self.chart_renderer.draw_chart(
                surface, chart_rect, sel_comp.price_history, sel_comp.price, sel_comp.symbol
            )

            # Company details badge
            info_rect = pygame.Rect(194, 215, VIRTUAL_WIDTH - 202, 42)
            pygame.draw.rect(surface, COLOR_PANEL_BG, info_rect, border_radius=4)
            pygame.draw.rect(surface, COLOR_BORDER, info_rect, width=1, border_radius=4)

            name_surf = self.font.render(f"{sel_comp.name} ({sel_comp.symbol})", True, COLOR_TEXT_WHITE)
            surface.blit(name_surf, (200, 218))

            btn_breakdown = Button(pygame.Rect(info_rect.right - 245, info_rect.top + 6, 80, 20), "FACTORS [B]", self.small_font)
            btn_thesis = Button(pygame.Rect(info_rect.right - 160, info_rect.top + 6, 65, 20), "THESIS [J]", self.small_font)
            btn_dossier = Button(pygame.Rect(info_rect.right - 90, info_rect.top + 6, 80, 20), "DOSSIER", self.small_font)
            buttons.extend([
                (f"breakdown_{sel_comp.symbol}", btn_breakdown),
                (f"thesis_{sel_comp.symbol}", btn_thesis),
                (f"inspect_{sel_comp.symbol}", btn_dossier)
            ])

            # Volatility badge & meta
            vol_str = f"Vol: {sel_comp.volatility_class} ({sel_comp.historical_volatility_pct}%)  |  P/E: {sel_comp.pe_ratio:.1f}  |  Cap: {sel_comp.market_cap}"
            meta_surf = self.small_font.render(vol_str, True, COLOR_TEXT_MUTED)
            surface.blit(meta_surf, (200, 238))

            # 3. Order Execution Box
            order_rect = pygame.Rect(194, 261, VIRTUAL_WIDTH - 202, VIRTUAL_HEIGHT - 269)
            pygame.draw.rect(surface, COLOR_PANEL_BG, order_rect, border_radius=4)
            pygame.draw.rect(surface, COLOR_BORDER, order_rect, width=1, border_radius=4)

            owned = game_state.portfolio.get_shares_owned(sel_comp.symbol)
            pos = game_state.portfolio.get_position(sel_comp.symbol)
            est_cost = round(self.trade_qty * sel_comp.price, 2)

            pos_txt = f"Owned: {owned} shs (Avg: ${pos.avg_cost:.2f})"
            pos_surf = self.small_font.render(pos_txt, True, COLOR_TEXT_WHITE)
            surface.blit(pos_surf, (200, 266))

            cost_txt = f"Total: {self.trade_qty} x ${sel_comp.price:.2f} = ${est_cost:,.2f}"
            cost_surf = self.small_font.render(cost_txt, True, COLOR_TEXT_GOLD)
            surface.blit(cost_surf, (200, 282))

            # Quantity Buttons
            q_minus = Button(pygame.Rect(375, 265, 24, 20), "-1", self.small_font)
            q_plus = Button(pygame.Rect(403, 265, 24, 20), "+1", self.small_font)
            q_plus10 = Button(pygame.Rect(431, 265, 30, 20), "+10", self.small_font)
            q_max = Button(pygame.Rect(465, 265, 34, 20), "MAX", self.small_font)
            buttons.extend([("qty_minus", q_minus), ("qty_plus", q_plus), ("qty_plus10", q_plus10), ("qty_max", q_max)])

            # BUY & SELL Buttons (Restricted to authorized exchange trading floors)
            on_floor = game_state.is_on_trading_floor()
            can_buy = on_floor and (game_state.portfolio.cash >= est_cost)
            can_sell = on_floor and (owned >= self.trade_qty)

            btn_buy = Button(pygame.Rect(506, 265, 58, 26), "BUY", self.font,
                             bg_color=(20, 110, 70), hover_color=(28, 150, 95), enabled=can_buy)
            btn_sell = Button(pygame.Rect(568, 265, 58, 26), "SELL", self.font,
                              bg_color=(140, 35, 45), hover_color=(185, 45, 58), enabled=can_sell)
            buttons.extend([("prompt_buy", btn_buy), ("prompt_sell", btn_sell)])

            # Status / Location Restriction Message
            if not on_floor:
                msg_col = COLOR_TEXT_GOLD
                msg_clean = "⚠️ TRADING RESTRICTED: Orders can only be placed on an active Exchange Floor (BSE, NYSE, TSE, LSE)."
            else:
                msg_col = COLOR_LOSS_BRIGHT if self.trade_status_is_error else COLOR_GAIN_BRIGHT
                msg_clean = truncate_text(self.trade_status_msg, self.small_font, order_rect.width - 20)
            msg_surf = self.small_font.render(msg_clean, True, msg_col)
            surface.blit(msg_surf, (200, 302))

        # Draw confirmation popup if pending
        if self.pending_order:
            self._draw_trade_confirmation(surface, buttons)

        # Draw all interactive action buttons (skip watchlist rows as they are rendered inline with text)
        for act, b in buttons:
            if not act.startswith("select_"):
                b.draw(surface)

        return buttons

    def _draw_trade_confirmation(self, surface: pygame.Surface, buttons: List[Tuple[str, Button]]):
        """Render modal trade confirmation dialog."""
        overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 12, 24, 200))
        surface.blit(overlay, (0, 0))

        box = pygame.Rect(VIRTUAL_WIDTH // 2 - 130, VIRTUAL_HEIGHT // 2 - 70, 260, 140)
        pygame.draw.rect(surface, COLOR_PANEL_BG, box, border_radius=6)
        pygame.draw.rect(surface, COLOR_BORDER_ACCENT, box, width=2, border_radius=6)

        order = self.pending_order
        action = order["action"]
        sym = order["symbol"]
        qty = order["qty"]
        price = order["price"]
        tot = order["total"]

        t_surf = self.font.render(f"CONFIRM {action} ORDER", True, COLOR_TEXT_GOLD)
        surface.blit(t_surf, (box.centerx - t_surf.get_width() // 2, box.top + 12))

        summary_txt = f"{action} {qty} shares of {sym} at ${price:.2f}"
        s_surf = self.small_font.render(summary_txt, True, COLOR_TEXT_WHITE)
        surface.blit(s_surf, (box.centerx - s_surf.get_width() // 2, box.top + 40))

        cost_txt = f"Estimated Total: ${tot:,.2f}"
        c_surf = self.font.render(cost_txt, True, COLOR_GAIN_BRIGHT if action == "SELL" else COLOR_TEXT_GOLD)
        surface.blit(c_surf, (box.centerx - c_surf.get_width() // 2, box.top + 58))

        btn_confirm = Button(pygame.Rect(box.left + 25, box.bottom - 42, 95, 28), "CONFIRM", self.font,
                             bg_color=(25, 110, 65), hover_color=(35, 145, 85))
        btn_cancel = Button(pygame.Rect(box.right - 120, box.bottom - 42, 95, 28), "CANCEL", self.font,
                            bg_color=(120, 35, 45), hover_color=(160, 45, 58))

        buttons.extend([("confirm_trade", btn_confirm), ("cancel_trade", btn_cancel)])

    # -------------------------------------------------------------
    # PORTFOLIO SCREEN WITH FULL COMPANY NAMES & RESOLUTION
    # -------------------------------------------------------------
    def draw_portfolio(self, surface: pygame.Surface, game_state: Any, mouse_pos: Tuple[int, int]) -> List[Tuple[str, Button]]:
        buttons: List[Tuple[str, Button]] = []
        p = game_state.portfolio
        m = game_state.market

        pygame.draw.rect(surface, COLOR_BG_DARK, (0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

        # Header
        h_rect = pygame.Rect(8, 6, VIRTUAL_WIDTH - 16, 26)
        pygame.draw.rect(surface, COLOR_PANEL_BG, h_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_BORDER, h_rect, width=1, border_radius=4)

        t_title = self.font.render("INVESTOR PORTFOLIO & ASSET LEDGER", True, COLOR_TEXT_GOLD)
        surface.blit(t_title, (16, 10))

        btn_close = Button(pygame.Rect(VIRTUAL_WIDTH - 70, 8, 56, 22), "ESC", self.small_font)
        buttons.append(("close", btn_close))

        # Summary Cards
        m_val = p.get_market_value(m)
        u_pnl = p.get_unrealized_pnl(m)
        r_pnl = p.realized_pnl
        net_val = p.get_total_value(m)
        tot_pct = p.get_total_return_pct(m)

        cards = [
            ("Virtual Cash", f"${p.cash:,.2f}", COLOR_TEXT_WHITE),
            ("Holdings Value", f"${m_val:,.2f}", COLOR_TEXT_GOLD),
            ("Unrealized P&L", f"{'+' if u_pnl >= 0 else ''}${u_pnl:,.2f}", COLOR_GAIN_BRIGHT if u_pnl >= 0 else COLOR_LOSS_BRIGHT),
            ("Realized P&L", f"{'+' if r_pnl >= 0 else ''}${r_pnl:,.2f}", COLOR_GAIN_BRIGHT if r_pnl >= 0 else COLOR_LOSS_BRIGHT),
            ("Net Worth", f"${net_val:,.2f} ({'+' if tot_pct >= 0 else ''}{tot_pct:.1f}%)", COLOR_GAIN_BRIGHT if tot_pct >= 0 else COLOR_LOSS_BRIGHT),
        ]

        card_w = (VIRTUAL_WIDTH - 16 - (len(cards) - 1) * 6) // len(cards)
        card_x = 8
        for label, val, val_col in cards:
            c_rect = pygame.Rect(card_x, 36, card_w, 42)
            pygame.draw.rect(surface, COLOR_PANEL_BG, c_rect, border_radius=4)
            pygame.draw.rect(surface, COLOR_BORDER, c_rect, width=1, border_radius=4)

            surface.blit(self.small_font.render(label, True, COLOR_TEXT_MUTED), (card_x + 6, 40))
            surface.blit(self.small_font.render(val, True, val_col), (card_x + 6, 56))
            card_x += card_w + 6

        # Holdings Table
        t_rect = pygame.Rect(8, 84, VIRTUAL_WIDTH - 16, VIRTUAL_HEIGHT - 92)
        pygame.draw.rect(surface, COLOR_PANEL_BG, t_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_BORDER, t_rect, width=1, border_radius=4)

        headers = [
            ("COMPANY & TICKER", 16),
            ("SECTOR", 175),
            ("SHARES", 245),
            ("AVG COST", 295),
            ("PRICE", 355),
            ("HOLDING VAL", 415),
            ("UNREALIZED P&L", 485),
            ("RETURN %", 570)
        ]
        for h_title, h_x in headers:
            surface.blit(self.small_font.render(h_title, True, COLOR_TEXT_MUTED), (h_x, 90))

        pygame.draw.line(surface, COLOR_BORDER, (8, 106), (VIRTUAL_WIDTH - 8, 106), 1)

        active_positions = [pos for pos in p.positions.values() if pos.shares > 0]
        if not active_positions:
            no_holdings = self.font.render("No active stock positions held. Open Trading Terminal [T] to buy shares!", True, COLOR_TEXT_MUTED)
            surface.blit(no_holdings, (VIRTUAL_WIDTH // 2 - no_holdings.get_width() // 2, 170))
        else:
            row_y = 112
            for pos in active_positions:
                comp = m.get_company(pos.symbol)
                cur_p = comp.price if comp else 0.0
                full_name = comp.name if comp else pos.symbol
                sector_name = comp.sector if comp else ""
                
                h_val = pos.shares * cur_p
                pos_u_pnl = h_val - pos.total_cost_basis
                pos_ret_pct = ((cur_p - pos.avg_cost) / pos.avg_cost * 100) if pos.avg_cost > 0 else 0.0

                pnl_col = COLOR_GAIN_BRIGHT if pos_u_pnl >= 0 else COLOR_LOSS_BRIGHT
                pnl_sign = "+" if pos_u_pnl >= 0 else ""

                row_rect = pygame.Rect(12, row_y, VIRTUAL_WIDTH - 24, 22)
                if row_rect.collidepoint(mouse_pos):
                    pygame.draw.rect(surface, COLOR_PANEL_ALT, row_rect, border_radius=2)

                # Full Company Name + Ticker with font-metric truncation
                display_name = truncate_text(f"{full_name} ({pos.symbol})", self.small_font, 155)
                surface.blit(self.small_font.render(display_name, True, COLOR_TEXT_GOLD), (16, row_y + 4))

                surface.blit(self.small_font.render(sector_name, True, COLOR_TEXT_MUTED), (175, row_y + 4))
                surface.blit(self.small_font.render(str(pos.shares), True, COLOR_TEXT_WHITE), (245, row_y + 4))
                surface.blit(self.small_font.render(f"${pos.avg_cost:.2f}", True, COLOR_TEXT_WHITE), (295, row_y + 4))
                surface.blit(self.small_font.render(f"${cur_p:.2f}", True, COLOR_TEXT_WHITE), (355, row_y + 4))
                surface.blit(self.small_font.render(f"${h_val:,.2f}", True, COLOR_TEXT_WHITE), (415, row_y + 4))
                surface.blit(self.small_font.render(f"{pnl_sign}${pos_u_pnl:,.2f}", True, pnl_col), (485, row_y + 4))
                surface.blit(self.small_font.render(f"{pnl_sign}{pos_ret_pct:.1f}%", True, pnl_col), (570, row_y + 4))

                row_y += 26

        for _, b in buttons:
            b.draw(surface)

        return buttons

    # -------------------------------------------------------------
    # INTERIOR ARCHITECTURAL BLUEPRINT MAP ([M] in Buildings)
    # -------------------------------------------------------------
    # -------------------------------------------------------------
    # NEWS FEED SCREEN WITH FONT-METRIC WORD WRAPPING
    # -------------------------------------------------------------
    def draw_news_feed(self, surface: pygame.Surface, game_state: Any, mouse_pos: Tuple[int, int]) -> List[Tuple[str, Button]]:
        buttons: List[Tuple[str, Button]] = []
        pygame.draw.rect(surface, COLOR_BG_DARK, (0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

        # Header
        h_rect = pygame.Rect(8, 6, VIRTUAL_WIDTH - 16, 26)
        pygame.draw.rect(surface, COLOR_PANEL_BG, h_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_BORDER, h_rect, width=1, border_radius=4)

        t_title = self.font.render("FINANCIAL NEWS WIRE — VERIFIED MARKET DISCLOSURES", True, COLOR_TEXT_GOLD)
        surface.blit(t_title, (16, 10))

        btn_close = Button(pygame.Rect(VIRTUAL_WIDTH - 70, 8, 56, 22), "ESC", self.small_font)
        buttons.append(("close", btn_close))

        feed_rect = pygame.Rect(8, 36, VIRTUAL_WIDTH - 16, VIRTUAL_HEIGHT - 44)
        pygame.draw.rect(surface, COLOR_PANEL_BG, feed_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_BORDER, feed_rect, width=1, border_radius=4)

        if not game_state.market.news_feed:
            no_news = self.font.render("No breaking news logged yet. Explore town, talk to executives and floor traders!", True, COLOR_TEXT_MUTED)
            surface.blit(no_news, (VIRTUAL_WIDTH // 2 - no_news.get_width() // 2, 160))
        else:
            item_y = 42
            for item in game_state.market.news_feed[:3]:  # Top 3 richly formatted stories
                card_h = 84
                box = pygame.Rect(16, item_y, VIRTUAL_WIDTH - 32, card_h)
                pygame.draw.rect(surface, COLOR_PANEL_ALT, box, border_radius=4)
                pygame.draw.rect(surface, COLOR_BORDER, box, width=1, border_radius=4)

                # Category, Region, and Headline
                cat = item.get("category", "NEWS").upper()
                reg = item.get("exchange_region", "GLOBAL")
                h_text = f"[{cat} | {reg}] Day {item['day']}: {item['headline']}"
                head_clean = truncate_text(h_text, self.font, box.width - 130)
                surface.blit(self.font.render(head_clean, True, COLOR_TEXT_WHITE), (24, item_y + 6))

                # Impact badge
                impact_col = COLOR_GAIN_BRIGHT if item.get("impact", 0) >= 0 else COLOR_LOSS_BRIGHT
                imp_surf = self.small_font.render(f"{item['impact_str']} on {item['target']}", True, impact_col)
                surface.blit(imp_surf, (box.right - imp_surf.get_width() - 10, item_y + 8))

                # Explanation wrapped strictly inside container width
                exp_rect = pygame.Rect(24, item_y + 24, box.width - 28, 28)
                render_wrapped_text(surface, item["explanation"], self.small_font, COLOR_TEXT_MUTED, exp_rect, max_lines=2)

                # Educational Takeaway
                edu_text = f"💡 Lesson: {item['education']} ({item.get('disclaimer', 'Fictional event.')})"
                edu_clean = truncate_text(edu_text, self.small_font, box.width - 28)
                surface.blit(self.small_font.render(edu_clean, True, COLOR_TEXT_GOLD), (24, item_y + 62))

                item_y += card_h + 6

        for _, b in buttons:
            b.draw(surface)

        return buttons

    # -------------------------------------------------------------
    # INTERIOR ARCHITECTURAL BLUEPRINT MAP ([M] in Buildings)
    # -------------------------------------------------------------
    # -------------------------------------------------------------
    # STOCK EXCHANGE HUB MODAL (NYSE & BSE LIVE SCHEDULE)
    # -------------------------------------------------------------
    def draw_exchange_hub(self, surface: pygame.Surface, game_state: Any, mouse_pos: Tuple[int, int]) -> List[Tuple[str, Button]]:
        buttons: List[Tuple[str, Button]] = []
        clock = game_state.clock

        # Dark overlay
        overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 12, 24, 210))
        surface.blit(overlay, (0, 0))

        box = pygame.Rect(24, 18, VIRTUAL_WIDTH - 48, VIRTUAL_HEIGHT - 36)
        pygame.draw.rect(surface, COLOR_PANEL_BG, box, border_radius=6)
        pygame.draw.rect(surface, COLOR_BORDER_ACCENT, box, width=2, border_radius=6)

        # Title
        t_surf = self.font.render("GLOBAL STOCK EXCHANGE TRADING FLOOR", True, COLOR_TEXT_GOLD)
        surface.blit(t_surf, (box.left + 16, box.top + 14))

        btn_close = Button(pygame.Rect(box.right - 64, box.top + 10, 52, 22), "ESC", self.small_font)
        buttons.append(("close_hub", btn_close))

        # Two Exchange Cards: NYSE and BSE
        exchanges = [EXCHANGE_NYSE, EXCHANGE_BSE]
        card_w = (box.width - 36) // 2
        for idx, ex_id in enumerate(exchanges):
            stat = clock.get_exchange_status(ex_id)
            c_x = box.left + 14 + idx * (card_w + 8)
            c_rect = pygame.Rect(c_x, box.top + 42, card_w, 185)
            pygame.draw.rect(surface, COLOR_PANEL_ALT, c_rect, border_radius=4)
            pygame.draw.rect(surface, COLOR_BORDER, c_rect, width=1, border_radius=4)

            # Exchange Title & City
            e_title = self.font.render(stat["name"], True, COLOR_TEXT_WHITE)
            surface.blit(e_title, (c_x + 10, c_rect.top + 8))

            # Status Badge
            is_open = (stat["status"] == "OPEN")
            s_col = COLOR_GAIN_BRIGHT if is_open else COLOR_LOSS_BRIGHT
            s_surf = self.font.render(f"STATUS: {stat['status']}", True, s_col)
            surface.blit(s_surf, (c_x + 10, c_rect.top + 28))

            # Time Details
            time_txt = f"Local Time: {stat['time_str']} ({stat['tz_name']})"
            surface.blit(self.small_font.render(time_txt, True, COLOR_TEXT_GOLD), (c_x + 10, c_rect.top + 48))
            surface.blit(self.small_font.render(stat['date_str'], True, COLOR_TEXT_MUTED), (c_x + 10, c_rect.top + 64))

            # Session Schedule
            if ex_id == EXCHANGE_NYSE:
                sch_txt = "Trading Hours: 09:30 - 16:00 EST/EDT (Mon-Fri)"
                idx_txt = "Wall Street 30 Index: 42,850.20 (+0.84%)"
            else:
                sch_txt = "Trading Hours: 09:15 - 15:30 IST (Mon-Fri)"
                idx_txt = "Dalal Street 50 Index: 24,185.60 (+1.15%)"

            surface.blit(self.small_font.render(sch_txt, True, COLOR_TEXT_WHITE), (c_x + 10, c_rect.top + 85))
            surface.blit(self.small_font.render(idx_txt, True, COLOR_GAIN_BRIGHT), (c_x + 10, c_rect.top + 102))

            # Next event countdown
            surface.blit(self.small_font.render(f"Countdown: {stat['next_event']}", True, COLOR_TEXT_GOLD), (c_x + 10, c_rect.top + 124))

            # Holiday notice
            hol_note = "Holiday schedule: Simplified offline calendar."
            surface.blit(self.small_font.render(hol_note, True, COLOR_TEXT_MUTED), (c_x + 10, c_rect.top + 144))

        # Bottom Control Actions: Fast Forward & Wait Buttons
        btn_ff = Button(pygame.Rect(box.left + 14, box.bottom - 46, 210, 32), "Fast Forward to Next Market Open", self.small_font)
        btn_wait = Button(pygame.Rect(box.left + 234, box.bottom - 46, 130, 32), "Wait 1 Hour", self.small_font)
        
        mode_label = f"Mode: {clock.mode.upper()}"
        btn_mode = Button(pygame.Rect(box.right - 180, box.bottom - 46, 166, 32), mode_label, self.small_font)

        buttons.extend([("ff_open", btn_ff), ("wait_hour", btn_wait), ("toggle_mode", btn_mode)])

        for _, b in buttons:
            b.draw(surface)

        return buttons

    # -------------------------------------------------------------
    # INTERIOR ARCHITECTURAL BLUEPRINT MAP ([M] in Buildings)
    # -------------------------------------------------------------
    # -------------------------------------------------------------
    # COMPANY DOSSIER INSPECTION MODAL
    # -------------------------------------------------------------
    def draw_company_dossier(self, surface: pygame.Surface, game_state: Any, mouse_pos: Tuple[int, int]) -> List[Tuple[str, Button]]:
        buttons: List[Tuple[str, Button]] = []
        comp = game_state.market.get_company(self.inspected_symbol)
        if not comp:
            comp = game_state.market.get_all_companies()[0]

        overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 12, 24, 210))
        surface.blit(overlay, (0, 0))

        box = pygame.Rect(20, 14, VIRTUAL_WIDTH - 40, VIRTUAL_HEIGHT - 28)
        pygame.draw.rect(surface, COLOR_PANEL_BG, box, border_radius=6)
        pygame.draw.rect(surface, COLOR_BORDER_ACCENT, box, width=2, border_radius=6)

        # Header
        t_surf = self.font.render(f"COMPANY DOSSIER: {comp.name} ({comp.symbol})", True, COLOR_TEXT_GOLD)
        surface.blit(t_surf, (box.left + 16, box.top + 12))

        btn_close = Button(pygame.Rect(box.right - 64, box.top + 10, 52, 22), "ESC", self.small_font)
        buttons.append(("close_dossier", btn_close))

        # Metrics bar
        m_txt = f"Sector: {comp.sector}  |  Price: ${comp.price:.2f}  |  P/E: {comp.pe_ratio:.1f}  |  Cap: {comp.market_cap}  |  Vol: {comp.volatility_class} ({comp.historical_volatility_pct}%)"
        surface.blit(self.small_font.render(m_txt, True, COLOR_TEXT_MUTED), (box.left + 16, box.top + 34))
        pygame.draw.line(surface, COLOR_BORDER, (box.left + 16, box.top + 48), (box.right - 16, box.top + 48), 1)

        # Left Column: Business Overview & Products
        col_w = (box.width - 48) // 2
        b_rect = pygame.Rect(box.left + 16, box.top + 54, col_w, 75)
        pygame.draw.rect(surface, COLOR_PANEL_ALT, b_rect, border_radius=4)
        surface.blit(self.small_font.render("BUSINESS OVERVIEW", True, COLOR_TEXT_GOLD), (b_rect.x + 8, b_rect.y + 6))
        render_wrapped_text(surface, comp.description, self.small_font, COLOR_TEXT_WHITE, pygame.Rect(b_rect.x + 8, b_rect.y + 20, b_rect.width - 16, 50))

        p_rect = pygame.Rect(box.left + 16, box.top + 135, col_w, 70)
        pygame.draw.rect(surface, COLOR_PANEL_ALT, p_rect, border_radius=4)
        surface.blit(self.small_font.render("FLAGSHIP PRODUCTS & SERVICES", True, COLOR_TEXT_GOLD), (p_rect.x + 8, p_rect.y + 6))
        prod_txt = " • " + "\n • ".join(comp.products) if comp.products else "Proprietary Commercial Solutions"
        render_wrapped_text(surface, prod_txt, self.small_font, COLOR_TEXT_WHITE, pygame.Rect(p_rect.x + 8, p_rect.y + 20, p_rect.width - 16, 45))

        # Right Column: Growth Drivers & Risks
        g_rect = pygame.Rect(box.left + 24 + col_w, box.top + 54, col_w, 75)
        pygame.draw.rect(surface, COLOR_PANEL_ALT, g_rect, border_radius=4)
        surface.blit(self.small_font.render("GROWTH CATALYSTS", True, COLOR_GAIN_BRIGHT), (g_rect.x + 8, g_rect.y + 6))
        render_wrapped_text(surface, comp.growth_drivers, self.small_font, COLOR_TEXT_WHITE, pygame.Rect(g_rect.x + 8, g_rect.y + 20, g_rect.width - 16, 50))

        r_rect = pygame.Rect(box.left + 24 + col_w, box.top + 135, col_w, 70)
        pygame.draw.rect(surface, COLOR_PANEL_ALT, r_rect, border_radius=4)
        surface.blit(self.small_font.render("KEY RISK FACTORS", True, COLOR_LOSS_BRIGHT), (r_rect.x + 8, r_rect.y + 6))
        render_wrapped_text(surface, comp.risks, self.small_font, COLOR_TEXT_WHITE, pygame.Rect(r_rect.x + 8, r_rect.y + 20, r_rect.width - 16, 45))

        # Disclaimer & Action
        disc_txt = "Simulated Educational Entity. Fictional valuation and pricing model."
        surface.blit(self.small_font.render(disc_txt, True, COLOR_TEXT_MUTED), (box.left + 16, box.bottom - 46))

        btn_trade = Button(pygame.Rect(box.right - 180, box.bottom - 44, 164, 30), "TRADE IN TERMINAL", self.font,
                           bg_color=(20, 110, 70), hover_color=(28, 150, 95))
        buttons.append((f"open_terminal_{comp.symbol}", btn_trade))

        for _, b in buttons:
            b.draw(surface)

        return buttons

    # -------------------------------------------------------------
    # INTERIOR ARCHITECTURAL BLUEPRINT MAP ([M] in Buildings)
    # -------------------------------------------------------------
    # -------------------------------------------------------------
    # BANK ACCOUNT & TRADE LEDGER MODAL
    # -------------------------------------------------------------
    def draw_bank_modal(self, surface: pygame.Surface, game_state: Any, mouse_pos: Tuple[int, int]) -> List[Tuple[str, Button]]:
        buttons: List[Tuple[str, Button]] = []
        p = game_state.portfolio

        overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 12, 24, 210))
        surface.blit(overlay, (0, 0))

        box = pygame.Rect(20, 14, VIRTUAL_WIDTH - 40, VIRTUAL_HEIGHT - 28)
        pygame.draw.rect(surface, COLOR_PANEL_BG, box, border_radius=6)
        pygame.draw.rect(surface, COLOR_BORDER_ACCENT, box, width=2, border_radius=6)

        t_surf = self.font.render("COMMERCIAL BANKING ACCOUNT & SETTLEMENT LEDGER", True, COLOR_TEXT_GOLD)
        surface.blit(t_surf, (box.left + 16, box.top + 12))

        btn_close = Button(pygame.Rect(box.right - 64, box.top + 10, 52, 22), "ESC", self.small_font)
        buttons.append(("close_bank", btn_close))

        # Account Balances Cards
        cards = [
            ("Virtual Cash Balance", f"${p.cash:,.2f}", COLOR_GAIN_BRIGHT),
            ("Starting Balance", f"${p.starting_cash:,.2f}", COLOR_TEXT_WHITE),
            ("Realized P&L", f"{'+' if p.realized_pnl >= 0 else ''}${p.realized_pnl:,.2f}", COLOR_GAIN_BRIGHT if p.realized_pnl >= 0 else COLOR_LOSS_BRIGHT),
            ("Total Transactions", str(len(p.trade_history)), COLOR_TEXT_GOLD)
        ]
        cw = (box.width - 32 - 18) // 4
        cx = box.left + 16
        for lbl, val, v_col in cards:
            c_rect = pygame.Rect(cx, box.top + 38, cw, 42)
            pygame.draw.rect(surface, COLOR_PANEL_ALT, c_rect, border_radius=4)
            surface.blit(self.small_font.render(lbl, True, COLOR_TEXT_MUTED), (cx + 6, box.top + 42))
            surface.blit(self.small_font.render(val, True, v_col), (cx + 6, box.top + 58))
            cx += cw + 6

        # Transaction History Table
        t_rect = pygame.Rect(box.left + 16, box.top + 88, box.width - 32, box.height - 100)
        pygame.draw.rect(surface, COLOR_PANEL_ALT, t_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_BORDER, t_rect, width=1, border_radius=4)

        t_headers = [("DAY", 24), ("ACTION", 70), ("TICKER", 130), ("SHARES", 195), ("PRICE", 255), ("TOTAL VALUE", 335), ("REALIZED P&L", 445)]
        for h_str, h_off in t_headers:
            surface.blit(self.small_font.render(h_str, True, COLOR_TEXT_MUTED), (box.left + h_off, box.top + 94))
        pygame.draw.line(surface, COLOR_BORDER, (box.left + 16, box.top + 108), (box.right - 16, box.top + 108), 1)

        if not p.trade_history:
            no_trades = self.small_font.render("No historical trades logged yet. Execute a trade in the Terminal [T]!", True, COLOR_TEXT_MUTED)
            surface.blit(no_trades, (box.centerx - no_trades.get_width() // 2, box.top + 140))
        else:
            tr_y = box.top + 114
            for tr in reversed(p.trade_history[-6:]):  # Latest 6 trades
                act_col = COLOR_GAIN_BRIGHT if tr.action == "BUY" else COLOR_LOSS_BRIGHT
                surface.blit(self.small_font.render(f"Day {tr.day}", True, COLOR_TEXT_WHITE), (box.left + 24, tr_y))
                surface.blit(self.small_font.render(tr.action, True, act_col), (box.left + 70, tr_y))
                surface.blit(self.font.render(tr.symbol, True, COLOR_TEXT_GOLD), (box.left + 130, tr_y - 2))
                surface.blit(self.small_font.render(str(tr.shares), True, COLOR_TEXT_WHITE), (box.left + 195, tr_y))
                surface.blit(self.small_font.render(f"${tr.price:.2f}", True, COLOR_TEXT_WHITE), (box.left + 255, tr_y))
                surface.blit(self.small_font.render(f"${tr.total:,.2f}", True, COLOR_TEXT_WHITE), (box.left + 335, tr_y))
                
                pnl_str = f"{'+' if tr.realized_pnl >= 0 else ''}${tr.realized_pnl:,.2f}" if tr.action == "SELL" else "--"
                surface.blit(self.small_font.render(pnl_str, True, COLOR_GAIN_BRIGHT if tr.realized_pnl >= 0 else COLOR_LOSS_BRIGHT), (box.left + 445, tr_y))
                tr_y += 20

        for _, b in buttons:
            b.draw(surface)

        return buttons

    # -------------------------------------------------------------
    # INTERIOR ARCHITECTURAL BLUEPRINT MAP ([M] in Buildings)
    # -------------------------------------------------------------
    # -------------------------------------------------------------
    # INVESTOR ACADEMY & EDUCATIONAL LIBRARY MODAL
    # -------------------------------------------------------------
    def draw_academy_modal(self, surface: pygame.Surface, game_state: Any, mouse_pos: Tuple[int, int]) -> List[Tuple[str, Button]]:
        buttons: List[Tuple[str, Button]] = []

        overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 12, 24, 210))
        surface.blit(overlay, (0, 0))

        box = pygame.Rect(20, 14, VIRTUAL_WIDTH - 40, VIRTUAL_HEIGHT - 28)
        pygame.draw.rect(surface, COLOR_PANEL_BG, box, border_radius=6)
        pygame.draw.rect(surface, COLOR_BORDER_ACCENT, box, width=2, border_radius=6)

        t_surf = self.font.render("INVESTOR ACADEMY & FINANCIAL CURRICULUM", True, COLOR_TEXT_GOLD)
        surface.blit(t_surf, (box.left + 16, box.top + 12))

        btn_close = Button(pygame.Rect(box.right - 64, box.top + 10, 52, 22), "ESC", self.small_font)
        buttons.append(("close_academy", btn_close))

        modules = [
            ("Shares & Fractional Ownership", "A share is legal fractional ownership of a productive enterprise. You share in business expansion, dividends, and earnings compounding."),
            ("Portfolio Diversification", "Allocating capital across uncorrelated sectors (Tech, Banking, Energy, Staples) protects your portfolio from catastrophic single-stock shocks."),
            ("Volatility & Risk Management", "Price swings represent market uncertainty, not guaranteed profits. Managing position sizing is the golden rule of wealth survival."),
            ("Price-to-Earnings (P/E) Metrics", "P/E reveals how many dollars the market pays per dollar of profit. High P/E signals growth expectations; low P/E signals value or cyclical risks."),
            ("Bull vs Bear Market Psychology", "Bull markets represent optimism, liquidity, and upward trends; Bear markets feature risk aversion, panic selling, and liquidation.")
        ]

        m_y = box.top + 42
        for title, desc in modules:
            m_box = pygame.Rect(box.left + 16, m_y, box.width - 32, 42)
            pygame.draw.rect(surface, COLOR_PANEL_ALT, m_box, border_radius=4)
            surface.blit(self.small_font.render(f"• {title}", True, COLOR_BORDER_ACCENT), (m_box.x + 8, m_y + 4))
            render_wrapped_text(surface, desc, self.small_font, COLOR_TEXT_WHITE, pygame.Rect(m_box.x + 8, m_y + 18, m_box.width - 16, 22))
            m_y += 48

        for _, b in buttons:
            b.draw(surface)

        return buttons

    # -------------------------------------------------------------
    # INTERIOR ARCHITECTURAL BLUEPRINT MAP ([M] in Buildings)
    # -------------------------------------------------------------
    # -------------------------------------------------------------
    # CHARGING BULL MONUMENT MODAL
    # -------------------------------------------------------------
    def draw_bull_modal(self, surface: pygame.Surface, game_state: Any, mouse_pos: Tuple[int, int]) -> List[Tuple[str, Button]]:
        buttons: List[Tuple[str, Button]] = []

        overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 12, 24, 210))
        surface.blit(overlay, (0, 0))

        box = pygame.Rect(VIRTUAL_WIDTH // 2 - 170, VIRTUAL_HEIGHT // 2 - 110, 340, 220)
        pygame.draw.rect(surface, COLOR_PANEL_BG, box, border_radius=6)
        pygame.draw.rect(surface, COLOR_BORDER_ACCENT, box, width=2, border_radius=6)

        t_surf = self.font.render("THE CHARGING BULL OF WALL STREET", True, COLOR_TEXT_GOLD)
        surface.blit(t_surf, (box.centerx - t_surf.get_width() // 2, box.top + 14))

        lore = (
            "Sculpted as a bronze tribute to the unyielding optimism and aggressive resilience of investors. "
            "A 'Bull' thrusts upward with its horns, representing a rising market! "
            "Legend says rubbing the bronze bull's horns bestows good financial fortune."
        )
        render_wrapped_text(surface, lore, self.small_font, COLOR_TEXT_WHITE, pygame.Rect(box.left + 16, box.top + 44, box.width - 32, 80))

        btn_rub = Button(pygame.Rect(box.centerx - 110, box.bottom - 50, 220, 32), "Rub the Bull's Horns for Luck", self.font,
                         bg_color=(160, 110, 35), hover_color=(205, 140, 45))
        btn_close = Button(pygame.Rect(box.right - 56, box.top + 8, 46, 20), "ESC", self.small_font)

        buttons.extend([("rub_bull_horns", btn_rub), ("close_bull", btn_close)])

        for _, b in buttons:
            b.draw(surface)

        return buttons

    # -------------------------------------------------------------
    # INTERIOR ARCHITECTURAL BLUEPRINT MAP ([M] in Buildings)
    # -------------------------------------------------------------
    # -------------------------------------------------------------
    # HISTORIC BANYAN TREE & CHAI MODALS
    # -------------------------------------------------------------
    def draw_banyan_modal(self, surface: pygame.Surface, game_state: Any, mouse_pos: Tuple[int, int]) -> List[Tuple[str, Button]]:
        buttons: List[Tuple[str, Button]] = []

        overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 12, 24, 210))
        surface.blit(overlay, (0, 0))

        box = pygame.Rect(VIRTUAL_WIDTH // 2 - 170, VIRTUAL_HEIGHT // 2 - 100, 340, 200)
        pygame.draw.rect(surface, COLOR_PANEL_BG, box, border_radius=6)
        pygame.draw.rect(surface, COLOR_BORDER_ACCENT, box, width=2, border_radius=6)

        t_surf = self.font.render("THE 1875 BANYAN TREE OF DALAL STREET", True, COLOR_TEXT_GOLD)
        surface.blit(t_surf, (box.centerx - t_surf.get_width() // 2, box.top + 14))

        lore = (
            "Beneath the sprawling canopy of this very banyan tree in 1875, five enterprising brokers "
            "conducted informal share auctions with cotton and gold merchants, founding the Bombay Stock Exchange—"
            "Asia's oldest equity market. The banyan tree symbolizes patience, deep roots, and generational compounding."
        )
        render_wrapped_text(surface, lore, self.small_font, COLOR_TEXT_WHITE, pygame.Rect(box.left + 16, box.top + 44, box.width - 32, 90))

        btn_close = Button(pygame.Rect(box.centerx - 50, box.bottom - 42, 100, 28), "Wise Words", self.font)
        buttons.append(("close_banyan", btn_close))

        for _, b in buttons:
            b.draw(surface)

        return buttons

    # -------------------------------------------------------------
    # INTERIOR ARCHITECTURAL BLUEPRINT MAP ([M] in Buildings)
    # -------------------------------------------------------------
    def draw_chai_modal(self, surface: pygame.Surface, game_state: Any, mouse_pos: Tuple[int, int]) -> List[Tuple[str, Button]]:
        buttons: List[Tuple[str, Button]] = []

        overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 12, 24, 210))
        surface.blit(overlay, (0, 0))

        box = pygame.Rect(VIRTUAL_WIDTH // 2 - 170, VIRTUAL_HEIGHT // 2 - 95, 340, 190)
        pygame.draw.rect(surface, COLOR_PANEL_BG, box, border_radius=6)
        pygame.draw.rect(surface, COLOR_BORDER_ACCENT, box, width=2, border_radius=6)

        t_surf = self.font.render("CUTTING CHAI POINT — STREET RUMORS", True, COLOR_TEXT_GOLD)
        surface.blit(t_surf, (box.centerx - t_surf.get_width() // 2, box.top + 14))

        lore = (
            "You enjoy a piping hot glass of spiced ginger cutting chai. "
            "A floor runner whispers nearby: 'Word on the street is that Monsoon Global Goods "
            "is planning a massive retail rollout in Southeast Asia! But remember: rumors are not confirmed news!'"
        )
        render_wrapped_text(surface, lore, self.small_font, COLOR_TEXT_WHITE, pygame.Rect(box.left + 16, box.top + 44, box.width - 32, 80))

        btn_close = Button(pygame.Rect(box.centerx - 60, box.bottom - 42, 120, 28), "Finish Chai", self.font)
        buttons.append(("close_chai", btn_close))

        for _, b in buttons:
            b.draw(surface)

        return buttons

    # -------------------------------------------------------------
    # INTERIOR ARCHITECTURAL BLUEPRINT MAP ([M] in Buildings)
    # -------------------------------------------------------------
    # -------------------------------------------------------------
    # 4-EXCHANGE GLOBAL TRANSIT MAP WITH UNLOCK PROGRESSION
    # -------------------------------------------------------------
    def draw_travel_map(self, surface: pygame.Surface, game_state: Any, mouse_pos: Tuple[int, int]) -> List[Tuple[str, Button]]:
        buttons: List[Tuple[str, Button]] = []
        pygame.draw.rect(surface, (8, 14, 28), (0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

        t_title = self.font.render("GLOBAL FINANCIAL HUBS & UNLOCKABLE EXCHANGES", True, COLOR_TEXT_GOLD)
        surface.blit(t_title, (VIRTUAL_WIDTH // 2 - t_title.get_width() // 2, 12))

        btn_close = Button(pygame.Rect(VIRTUAL_WIDTH - 70, 10, 56, 22), "ESC", self.small_font)
        buttons.append(("close", btn_close))

        realized_profit = game_state.portfolio.realized_pnl

        # 4 Global Exchanges configuration
        destinations = [
            {
                "id": LOCATION_DALAL_STREET,
                "name": "MUMBAI — BSE",
                "sub": "Dalal Street (Asia's Oldest Exchange)",
                "unlocked": True,
                "cost": 0,
                "pos": (85, 45, 225, 115),
                "action": "travel_dalal_street"
            },
            {
                "id": LOCATION_WALL_STREET,
                "name": "NEW YORK — NYSE",
                "sub": "Wall Street (Capital Liquidity)",
                "unlocked": realized_profit >= UNLOCK_PROFIT_NYSE or game_state.world.current_location_id == LOCATION_WALL_STREET,
                "cost": UNLOCK_PROFIT_NYSE,
                "pos": (330, 45, 225, 115),
                "action": "travel_wall_street"
            },
            {
                "id": LOCATION_KABUTOCHO,
                "name": "TOKYO — TSE",
                "sub": "Kabutocho (Precision Robotics & Tech)",
                "unlocked": realized_profit >= UNLOCK_PROFIT_TSE or game_state.world.current_location_id == LOCATION_KABUTOCHO,
                "cost": UNLOCK_PROFIT_TSE,
                "pos": (85, 175, 225, 115),
                "action": "travel_kabutocho"
            },
            {
                "id": LOCATION_LONDON,
                "name": "LONDON — LSE",
                "sub": "Paternoster Sq (Global Commodities)",
                "unlocked": realized_profit >= UNLOCK_PROFIT_LSE or game_state.world.current_location_id == LOCATION_LONDON,
                "cost": UNLOCK_PROFIT_LSE,
                "pos": (330, 175, 225, 115),
                "action": "travel_london"
            }
        ]

        cur_loc = game_state.world.current_location_id

        for d in destinations:
            dx, dy, dw, dh = d["pos"]
            card_rect = pygame.Rect(dx, dy, dw, dh)
            is_active_loc = (cur_loc == d["id"])
            border_c = COLOR_BORDER_ACCENT if is_active_loc else (COLOR_BORDER if d["unlocked"] else (40, 45, 65))
            bg_c = (20, 32, 60) if is_active_loc else (COLOR_PANEL_BG if d["unlocked"] else (14, 20, 32))

            pygame.draw.rect(surface, bg_c, card_rect, border_radius=6)
            pygame.draw.rect(surface, border_c, card_rect, width=2 if is_active_loc else 1, border_radius=6)

            # City Title
            title_c = COLOR_TEXT_GOLD if d["unlocked"] else COLOR_TEXT_MUTED
            surface.blit(self.font.render(d["name"], True, title_c), (dx + 12, dy + 10))
            surface.blit(self.small_font.render(d["sub"], True, COLOR_TEXT_MUTED), (dx + 12, dy + 28))

            if d["unlocked"]:
                status_txt = "[CURRENT LOCATION]" if is_active_loc else "[EXCHANGE UNLOCKED]"
                stat_col = COLOR_GAIN_BRIGHT if is_active_loc else COLOR_BORDER_ACCENT
                surface.blit(self.small_font.render(status_txt, True, stat_col), (dx + 12, dy + 48))

                btn_travel = Button(pygame.Rect(dx + 12, dy + 72, dw - 24, 28),
                                    "Travel Here" if not is_active_loc else "Exploring",
                                    self.font,
                                    enabled=(not is_active_loc))
                buttons.append((d["action"], btn_travel))
            else:
                pct = min(100, int((max(0.0, realized_profit) / d["cost"]) * 100))
                surface.blit(self.small_font.render(f"Locked: ${realized_profit:,.0f} / ${d['cost']:,.0f} Profit", True, COLOR_LOSS_BRIGHT), (dx + 12, dy + 48))
                
                # Progress bar
                p_bar = pygame.Rect(dx + 12, dy + 68, dw - 24, 8)
                pygame.draw.rect(surface, (25, 35, 55), p_bar, border_radius=3)
                fill_w = int((dw - 24) * (pct / 100.0))
                if fill_w > 0:
                    pygame.draw.rect(surface, COLOR_GAIN, (dx + 12, dy + 68, fill_w, 8), border_radius=3)

                btn_locked = Button(pygame.Rect(dx + 12, dy + 82, dw - 24, 22), f"Requires ${d['cost']:,.0f} P&L ({pct}%)", self.small_font, enabled=False)
                buttons.append(("locked", btn_locked))

        foot_txt = self.small_font.render("Realize trading profits on active floors to unlock international financial districts.", True, COLOR_TEXT_MUTED)
        surface.blit(foot_txt, (VIRTUAL_WIDTH // 2 - foot_txt.get_width() // 2, VIRTUAL_HEIGHT - 38))

        for _, b in buttons:
            b.draw(surface)

        return buttons

    # -------------------------------------------------------------
    # INTERIOR ARCHITECTURAL BLUEPRINT MAP ([M] in Buildings)
    # -------------------------------------------------------------
    def draw_interior_map(self, surface: pygame.Surface, game_state: Any, mouse_pos: Tuple[int, int]) -> List[Tuple[str, Button]]:
        buttons: List[Tuple[str, Button]] = []
        pygame.draw.rect(surface, (8, 14, 26), (0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

        m = game_state.world.current_map
        header_text = f"{m.name.upper()} — ARCHITECTURAL BLUEPRINT"
        t_title = self.font.render(header_text, True, COLOR_TEXT_GOLD)
        surface.blit(t_title, (VIRTUAL_WIDTH // 2 - t_title.get_width() // 2, 8))

        sub_txt = self.small_font.render("[M] / [ESC] Return to Floor  •  [R] Toggle Route Guidance  •  Live Interior Nav Mesh", True, COLOR_TEXT_MUTED)
        surface.blit(sub_txt, (VIRTUAL_WIDTH // 2 - sub_txt.get_width() // 2, 26))

        btn_close = Button(pygame.Rect(VIRTUAL_WIDTH - 65, 8, 52, 20), "ESC", self.small_font)
        buttons.append(("close", btn_close))

        # Main blueprint canvas
        canvas_rect = pygame.Rect(20, 44, VIRTUAL_WIDTH - 40, VIRTUAL_HEIGHT - 66)
        pygame.draw.rect(surface, (12, 18, 34), canvas_rect, border_radius=4)
        pygame.draw.rect(surface, (40, 65, 110), canvas_rect, width=1, border_radius=4)

        # Scale calculation to fit complete map without any cropping
        map_w = float(m.pixel_width)
        map_h = float(m.pixel_height)
        scale_x = (canvas_rect.width - 24) / map_w
        scale_y = (canvas_rect.height - 24) / map_h
        scale = min(scale_x, scale_y)

        draw_w = map_w * scale
        draw_h = map_h * scale
        origin_x = canvas_rect.centerx - draw_w / 2.0
        origin_y = canvas_rect.centery - draw_h / 2.0

        # Draw floor bounds
        floor_rect = pygame.Rect(int(origin_x), int(origin_y), int(draw_w), int(draw_h))
        pygame.draw.rect(surface, (20, 32, 54), floor_rect)
        pygame.draw.rect(surface, (30, 48, 80), floor_rect, width=1)

        # Draw room tint zones if BSE
        if m.id == INTERIOR_BSE:
            zones = [
                ("TRADING PIT", 15 * 24, 11 * 24, 18 * 24, 13 * 24, (55, 38, 25)),
                ("HISTORY GALLERY", 2 * 24, 11 * 24, 12 * 24, 23 * 24, (45, 30, 42)),
                ("EQUITY RESEARCH", 34 * 24, 11 * 24, 12 * 24, 13 * 24, (25, 42, 65)),
                ("RECEPTION LOBBY", 17 * 24, 25 * 24, 14 * 24, 9 * 24, (25, 52, 45)),
                ("SECRET VAULT", 18 * 24, 2 * 24, 12 * 24, 6 * 24, (65, 50, 20)),
                ("EDUCATION", 34 * 24, 25 * 24, 12 * 24, 9 * 24, (45, 25, 55)),
                ("RISK SUITE", 34 * 24, 2 * 24, 12 * 24, 6 * 24, (25, 35, 55)),
                ("BOARDROOM", 2 * 24, 2 * 24, 12 * 24, 6 * 24, (35, 30, 48))
            ]
            for z_name, zx, zy, zw, zh, zcol in zones:
                z_rect = pygame.Rect(int(origin_x + zx * scale), int(origin_y + zy * scale), int(zw * scale), int(zh * scale))
                pygame.draw.rect(surface, zcol, z_rect)
                pygame.draw.rect(surface, (min(255, zcol[0] + 30), min(255, zcol[1] + 30), min(255, zcol[2] + 30)), z_rect, width=1)
                lbl = self.small_font.render(z_name, True, (215, 225, 240))
                surface.blit(lbl, (z_rect.centerx - lbl.get_width() // 2, z_rect.centery - lbl.get_height() // 2))

        # Draw all solids / walls
        for s in m.solids:
            sx = int(origin_x + s.x * scale)
            sy = int(origin_y + s.y * scale)
            sw = max(2, int(s.w * scale))
            sh = max(2, int(s.h * scale))
            pygame.draw.rect(surface, (70, 95, 140), (sx, sy, sw, sh))
            pygame.draw.rect(surface, (100, 135, 195), (sx, sy, sw, sh), width=1)

        # Draw exit doors and terminals
        for obj in m.objects:
            ox = int(origin_x + obj.x * scale)
            oy = int(origin_y + obj.y * scale)
            ow = max(3, int(obj.w * scale))
            oh = max(3, int(obj.h * scale))
            if obj.action_type == "exit_interior":
                pygame.draw.rect(surface, (85, 230, 110), (ox, oy, ow, oh))
                ex_lbl = self.small_font.render("EXIT", True, (85, 230, 110))
                surface.blit(ex_lbl, (ox + ow // 2 - ex_lbl.get_width() // 2, oy - 11))
            elif obj.action_type == "open_trading":
                pygame.draw.rect(surface, COLOR_BORDER_ACCENT, (ox, oy, ow, oh))
                pygame.draw.circle(surface, (255, 255, 255), (ox + ow // 2, oy + oh // 2), 3)

        # Draw route guidance breadcrumbs if active
        if getattr(game_state.player, 'current_route', None):
            for pt in game_state.player.current_route:
                rx = int(origin_x + pt[0] * scale)
                ry = int(origin_y + pt[1] * scale)
                pygame.draw.circle(surface, (85, 230, 110), (rx, ry), 2)

        # Draw NPCs
        for npc in m.npcs:
            nx = int(origin_x + npc.x * scale)
            ny = int(origin_y + npc.y * scale)
            pygame.draw.circle(surface, npc.avatar_color, (nx + 2, ny + 2), 3)

        # Draw Player position with pulsing gold ring and "YOU" label
        px = int(origin_x + (game_state.player.x + game_state.player.width / 2.0) * scale)
        py = int(origin_y + (game_state.player.y + game_state.player.height / 2.0) * scale)
        pulse = 4 + int(math.sin(game_state.global_ticks * 0.2) * 2)
        pygame.draw.circle(surface, COLOR_TEXT_GOLD, (px, py), pulse, width=1)
        pygame.draw.circle(surface, (255, 255, 255), (px, py), 3)
        you_txt = self.small_font.render("YOU", True, COLOR_TEXT_GOLD)
        surface.blit(you_txt, (px - you_txt.get_width() // 2, py - 12))

        for _, b in buttons:
            b.draw(surface)

        return buttons

    # -------------------------------------------------------------
    # CLUE INVESTIGATION JOURNAL & INVESTMENT THESIS ([J])
    # -------------------------------------------------------------
    def draw_clue_journal(self, surface: pygame.Surface, game_state: Any, mouse_pos: Tuple[int, int]) -> List[Tuple[str, Button]]:
        buttons: List[Tuple[str, Button]] = []
        pygame.draw.rect(surface, COLOR_BG_DARK, (0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

        inv = game_state.investigation

        # Header
        h_rect = pygame.Rect(8, 6, VIRTUAL_WIDTH - 16, 26)
        pygame.draw.rect(surface, COLOR_PANEL_BG, h_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_BORDER, h_rect, width=1, border_radius=4)

        t_title = self.font.render("INVESTIGATION JOURNAL — FUNDAMENTAL THESIS BOARD", True, COLOR_TEXT_GOLD)
        surface.blit(t_title, (16, 10))

        btn_close = Button(pygame.Rect(VIRTUAL_WIDTH - 70, 8, 56, 22), "ESC", self.small_font)
        buttons.append(("close", btn_close))

        # Company Dossier Tabs
        tabs = [
            ("APEX", "Apex Dynamics"),
            ("TITN", "Titan Capital"),
            ("CHAI", "Monsoon Goods"),
            ("AURA", "Aurum Energy"),
            ("MACRO", "Macro Policy")
        ]

        tab_x = 8
        for sym, t_name in tabs:
            is_active_tab = (inv.selected_company == sym)
            t_btn = Button(pygame.Rect(tab_x, 36, 120, 24), f"{sym}", self.small_font,
                           bg_color=(28, 45, 85) if is_active_tab else (16, 24, 45),
                           border_color=COLOR_BORDER_ACCENT if is_active_tab else COLOR_BORDER)
            buttons.append((f"tab_{sym}", t_btn))
            t_btn.draw(surface)
            tab_x += 126

        # Left Panel: Clues List
        left_box = pygame.Rect(8, 64, 380, VIRTUAL_HEIGHT - 72)
        pygame.draw.rect(surface, COLOR_PANEL_BG, left_box, border_radius=4)
        pygame.draw.rect(surface, COLOR_BORDER, left_box, width=1, border_radius=4)

        sel_sym = inv.selected_company
        clues = inv.get_clues_for_company(sel_sym)
        tot_avail = inv.get_total_clues_for_company(sel_sym)

        surface.blit(self.font.render(f"FIELD EVIDENCE: {sel_sym} ({len(clues)}/{tot_avail} Found)", True, COLOR_TEXT_WHITE), (16, 70))

        if not clues:
            empty_msg = "No clues gathered for this entity yet. Visit the company headquarters, inspect lab equipment, and interview department heads to uncover field intelligence!"
            render_wrapped_text(surface, empty_msg, self.small_font, COLOR_TEXT_MUTED, pygame.Rect(16, 96, left_box.width - 32, 100))
        else:
            cy = 94
            for c in clues:
                c_card = pygame.Rect(14, cy, left_box.width - 28, 54)
                pygame.draw.rect(surface, (14, 22, 42), c_card, border_radius=4)
                pygame.draw.rect(surface, COLOR_BORDER, c_card, width=1, border_radius=4)

                imp_col = COLOR_GAIN_BRIGHT if c.impact == "BULLISH" else (COLOR_LOSS_BRIGHT if c.impact == "BEARISH" else COLOR_TEXT_GOLD)
                surface.blit(self.font.render(f"• {c.title}", True, COLOR_TEXT_GOLD), (20, cy + 4))
                surface.blit(self.small_font.render(f"[{c.category}] Source: {c.source}  |  Impact: {c.impact}", True, imp_col), (20, cy + 20))
                desc_tr = truncate_text(c.description, self.small_font, c_card.width - 16)
                surface.blit(self.small_font.render(desc_tr, True, COLOR_TEXT_WHITE), (20, cy + 36))
                cy += 60

        # Right Panel: Thesis Synthesis & Conviction Meter
        right_box = pygame.Rect(396, 64, VIRTUAL_WIDTH - 404, VIRTUAL_HEIGHT - 72)
        pygame.draw.rect(surface, COLOR_PANEL_BG, right_box, border_radius=4)
        pygame.draw.rect(surface, COLOR_BORDER, right_box, width=1, border_radius=4)

        surface.blit(self.font.render("INVESTMENT THESIS", True, COLOR_TEXT_GOLD), (408, 70))

        conf_pct = inv.get_confidence_pct(sel_sym)
        rating_label, thesis_text = inv.get_thesis_rating(sel_sym)

        # Confidence Bar
        surface.blit(self.small_font.render(f"Evidence Completeness: {conf_pct}%", True, COLOR_TEXT_WHITE), (408, 96))
        c_bar = pygame.Rect(408, 112, right_box.width - 24, 10)
        pygame.draw.rect(surface, (20, 28, 50), c_bar, border_radius=4)
        fill_w = int((right_box.width - 24) * (conf_pct / 100.0))
        if fill_w > 0:
            c_fill = COLOR_GAIN_BRIGHT if conf_pct >= 75 else (COLOR_TEXT_GOLD if conf_pct >= 35 else COLOR_LOSS_BRIGHT)
            pygame.draw.rect(surface, c_fill, (408, 112, fill_w, 10), border_radius=4)

        # Conviction Badge
        badge_col = COLOR_GAIN_BRIGHT if "HIGH" in rating_label else (COLOR_TEXT_GOLD if "MODERATE" in rating_label else COLOR_LOSS_BRIGHT)
        b_rect = pygame.Rect(408, 134, right_box.width - 24, 24)
        pygame.draw.rect(surface, (14, 24, 45), b_rect, border_radius=4)
        pygame.draw.rect(surface, badge_col, b_rect, width=1, border_radius=4)
        b_surf = self.font.render(f"CONVICTION: {rating_label}", True, badge_col)
        surface.blit(b_surf, b_surf.get_rect(center=b_rect.center))

        # Synthesis Summary Box
        synth_rect = pygame.Rect(408, 168, right_box.width - 24, 110)
        pygame.draw.rect(surface, (16, 24, 48), synth_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_BORDER, synth_rect, width=1, border_radius=4)

        render_wrapped_text(surface, thesis_text, self.small_font, COLOR_TEXT_WHITE, pygame.Rect(synth_rect.x + 8, synth_rect.y + 8, synth_rect.width - 16, synth_rect.height - 16))

        for act, b in buttons:
            if not act.startswith("tab_"):
                b.draw(surface)

        return buttons

    # -------------------------------------------------------------
    # HELP & EDUCATIONAL GLOSSARY SCREEN
    # -------------------------------------------------------------
    def draw_help_glossary(self, surface: pygame.Surface, mouse_pos: Tuple[int, int]) -> List[Tuple[str, Button]]:
        buttons: List[Tuple[str, Button]] = []
        pygame.draw.rect(surface, COLOR_BG_DARK, (0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

        h_rect = pygame.Rect(8, 6, VIRTUAL_WIDTH - 16, 26)
        pygame.draw.rect(surface, COLOR_PANEL_BG, h_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_BORDER, h_rect, width=1, border_radius=4)

        t_title = self.font.render("INVESTOR ACADEMY — CORE FINANCIAL CONCEPTS", True, COLOR_TEXT_GOLD)
        surface.blit(t_title, (16, 10))

        btn_close = Button(pygame.Rect(VIRTUAL_WIDTH - 70, 8, 56, 22), "ESC", self.small_font)
        buttons.append(("close", btn_close))

        topics = [
            ("Shares & Fractional Ownership", "A share represents fractional legal ownership of a business. As the company expands revenue, assets, and profits, the value of each share compounds."),
            ("Portfolio Diversification", "Spreading investments across uncorrelated industries (Tech, Banking, Energy, Consumer) prevents catastrophic losses when an individual sector stumbles."),
            ("Volatility & Beta", "Price fluctuations over time. Growth tech stocks typically feature higher volatility (beta > 1), while established consumer staples offer stability."),
            ("P/E Ratio (Price-to-Earnings)", "Measures market expectations. High P/E means investors expect rapid future earnings growth; low P/E suggests mature value or cyclical risk."),
            ("Realized vs Unrealized P&L", "Unrealized 'paper' gains fluctuate daily with market quotes. Gains or losses only become 'realized' when you execute a sell order."),
            ("Why Events Shake Prices", "Markets price in expectations. When actual earnings, rate cuts, or regulation diverge from consensus, rapid repricing occurs.")
        ]

        t_y = 38
        for title, body in topics:
            box = pygame.Rect(12, t_y, VIRTUAL_WIDTH - 24, 46)
            pygame.draw.rect(surface, COLOR_PANEL_BG, box, border_radius=3)
            pygame.draw.rect(surface, COLOR_BORDER, box, width=1, border_radius=3)

            surface.blit(self.font.render(f"• {title}", True, COLOR_BORDER_ACCENT), (18, t_y + 4))
            render_wrapped_text(surface, body, self.small_font, COLOR_TEXT_WHITE, pygame.Rect(18, t_y + 22, box.width - 24, 20))
            t_y += 52

        for _, b in buttons:
            b.draw(surface)

        return buttons

    # -------------------------------------------------------------
    # INTERIOR ARCHITECTURAL BLUEPRINT MAP ([M] in Buildings)
    # -------------------------------------------------------------
    # -------------------------------------------------------------
    # PAUSE MENU
    # -------------------------------------------------------------
    def draw_pause_menu(self, surface: pygame.Surface, mouse_pos: Tuple[int, int]) -> List[Tuple[str, Button]]:
        buttons: List[Tuple[str, Button]] = []

        overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 12, 24, 200))
        surface.blit(overlay, (0, 0))

        box = pygame.Rect(VIRTUAL_WIDTH // 2 - 110, VIRTUAL_HEIGHT // 2 - 120, 220, 240)
        pygame.draw.rect(surface, COLOR_PANEL_BG, box, border_radius=6)
        pygame.draw.rect(surface, COLOR_BORDER_ACCENT, box, width=2, border_radius=6)

        title = self.font.render("GAME PAUSED", True, COLOR_TEXT_GOLD)
        surface.blit(title, (box.centerx - title.get_width() // 2, box.top + 16))

        menu_items = [
            ("resume", "Resume"),
            ("save", "Save Game"),
            ("settings", "Settings"),
            ("title", "Quit to Title")
        ]

        by = box.top + 50
        for action_key, label in menu_items:
            b = Button(pygame.Rect(box.left + 25, by, 170, 32), label, self.font)
            buttons.append((action_key, b))
            b.draw(surface)
            by += 42

        return buttons

    # -------------------------------------------------------------
    # SETTINGS MENU
    # -------------------------------------------------------------
    def draw_settings_menu(self, surface: pygame.Surface, mouse_pos: Tuple[int, int], sound_mgr: SoundManager) -> List[Tuple[str, Button]]:
        buttons: List[Tuple[str, Button]] = []

        overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 12, 24, 210))
        surface.blit(overlay, (0, 0))

        box = pygame.Rect(VIRTUAL_WIDTH // 2 - 130, VIRTUAL_HEIGHT // 2 - 110, 260, 220)
        pygame.draw.rect(surface, COLOR_PANEL_BG, box, border_radius=6)
        pygame.draw.rect(surface, COLOR_BORDER_ACCENT, box, width=2, border_radius=6)

        title = self.font.render("AUDIO & GAME SETTINGS", True, COLOR_TEXT_GOLD)
        surface.blit(title, (box.centerx - title.get_width() // 2, box.top + 16))

        vol_pct = int(sound_mgr.sfx_volume * 100)
        surface.blit(self.small_font.render(f"Sound FX Volume: {vol_pct}%", True, COLOR_TEXT_WHITE), (box.left + 30, box.top + 60))

        btn_v_down = Button(pygame.Rect(box.left + 30, box.top + 80, 50, 26), "-10%", self.small_font)
        btn_v_up = Button(pygame.Rect(box.left + 90, box.top + 80, 50, 26), "+10%", self.small_font)
        btn_v_mute = Button(pygame.Rect(box.left + 150, box.top + 80, 75, 26), "MUTE" if vol_pct > 0 else "UNMUTE", self.small_font)
        buttons.extend([("vol_down", btn_v_down), ("vol_up", btn_v_up), ("vol_mute", btn_v_mute)])

        surface.blit(self.small_font.render("Display: 1280x720 Native (2x Nearest-Neighbor)", True, COLOR_TEXT_MUTED), (box.left + 20, box.top + 125))

        btn_back = Button(pygame.Rect(box.centerx - 60, box.bottom - 46, 120, 32), "Back", self.font)
        buttons.append(("back", btn_back))

        for _, b in buttons:
            b.draw(surface)

        return buttons

    # -------------------------------------------------------------
    # INTERIOR ARCHITECTURAL BLUEPRINT MAP ([M] in Buildings)
    # -------------------------------------------------------------
    # -------------------------------------------------------------
    # TITLE SCREEN
    # -------------------------------------------------------------
    def draw_title_screen(self, surface: pygame.Surface, mouse_pos: Tuple[int, int], has_save: bool, tick_count: int) -> List[Tuple[str, Button]]:
        buttons: List[Tuple[str, Button]] = []

        pygame.draw.rect(surface, (10, 16, 32), (0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

        for i in range(40):
            sx = (i * 37 + (tick_count // 3)) % VIRTUAL_WIDTH
            sy = (i * 23) % 180
            if (i + tick_count // 15) % 3 != 0:
                pygame.draw.circle(surface, (120, 160, 210), (sx, sy), 1)

        for b_idx in range(16):
            bx = b_idx * 42 - 10
            bw = 36
            bh = 90 + ((b_idx * 29) % 100)
            by = VIRTUAL_HEIGHT - 60 - bh
            pygame.draw.rect(surface, (18, 28, 54), (bx, by, bw, bh))
            for wy in range(by + 8, by + bh - 8, 14):
                for wx in range(bx + 6, bx + bw - 6, 10):
                    if (wx + wy + (tick_count // 30)) % 5 != 0:
                        pygame.draw.rect(surface, (255, 210, 100) if (wx + wy) % 7 == 0 else (72, 202, 228), (wx, wy, 4, 6))

        pygame.draw.rect(surface, (14, 20, 36), (0, VIRTUAL_HEIGHT - 60, VIRTUAL_WIDTH, 60))
        pygame.draw.line(surface, COLOR_BORDER, (0, VIRTUAL_HEIGHT - 60), (VIRTUAL_WIDTH, VIRTUAL_HEIGHT - 60), 2)

        ticker_items = "▲ APEX $145.50 (+18.2%)   ▼ TITN $64.00 (-2.1%)   ▲ NOVA $88.20 (+4.5%)   ▲ AURA $42.75 (+12.0%)   ▲ CHAI $52.30 (+1.4%)   ▼ MEDX $110.00 (-5.6%)   "
        tape_scroll = (tick_count * 2) % 400
        t_tape_surf = self.small_font.render(ticker_items + ticker_items, True, COLOR_GAIN_BRIGHT)
        surface.blit(t_tape_surf, (-tape_scroll, VIRTUAL_HEIGHT - 22))

        title_y = 35
        main_logo = self.title_font.render("MARKETQUEST", True, COLOR_TEXT_GOLD)
        shadow_logo = self.title_font.render("MARKETQUEST", True, (8, 12, 20))
        surface.blit(shadow_logo, (VIRTUAL_WIDTH // 2 - main_logo.get_width() // 2 + 2, title_y + 2))
        surface.blit(main_logo, (VIRTUAL_WIDTH // 2 - main_logo.get_width() // 2, title_y))

        tagline = self.small_font.render("Explore the Markets, Master Your Money — A Retro Financial Adventure", True, COLOR_BORDER_ACCENT)
        surface.blit(tagline, (VIRTUAL_WIDTH // 2 - tagline.get_width() // 2, title_y + 34))

        disclaimer = self.small_font.render("Educational Simulation — Fictional Virtual Credits Only", True, COLOR_TEXT_MUTED)
        surface.blit(disclaimer, (VIRTUAL_WIDTH // 2 - disclaimer.get_width() // 2, title_y + 50))

        btn_y = 125
        b_w = 160
        b_h = 28

        b_new = Button(pygame.Rect(VIRTUAL_WIDTH // 2 - b_w // 2, btn_y, b_w, b_h), "NEW GAME", self.font)
        b_cont = Button(pygame.Rect(VIRTUAL_WIDTH // 2 - b_w // 2, btn_y + 36, b_w, b_h), "CONTINUE", self.font, enabled=has_save)
        b_sett = Button(pygame.Rect(VIRTUAL_WIDTH // 2 - b_w // 2, btn_y + 72, b_w, b_h), "SETTINGS", self.font)
        b_quit = Button(pygame.Rect(VIRTUAL_WIDTH // 2 - b_w // 2, btn_y + 108, b_w, b_h), "QUIT", self.font)

        buttons.extend([("new_game", b_new), ("continue", b_cont), ("settings", b_sett), ("quit", b_quit)])

        for _, b in buttons:
            b.draw(surface)

        return buttons

    # -------------------------------------------------------------
    # INTERIOR ARCHITECTURAL BLUEPRINT MAP ([M] in Buildings)
    # -------------------------------------------------------------
    # -------------------------------------------------------------
    # TUTORIAL OVERLAY MODAL
    # -------------------------------------------------------------
    def draw_tutorial_modal(self, surface: pygame.Surface, mouse_pos: Tuple[int, int]) -> List[Tuple[str, Button]]:
        buttons: List[Tuple[str, Button]] = []

        overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 12, 24, 220))
        surface.blit(overlay, (0, 0))

        box = pygame.Rect(VIRTUAL_WIDTH // 2 - 180, VIRTUAL_HEIGHT // 2 - 120, 360, 240)
        pygame.draw.rect(surface, COLOR_PANEL_BG, box, border_radius=6)
        pygame.draw.rect(surface, COLOR_BORDER_ACCENT, box, width=2, border_radius=6)

        title = self.font.render("WELCOME TO MARKETQUEST!", True, COLOR_TEXT_GOLD)
        surface.blit(title, (box.centerx - title.get_width() // 2, box.top + 14))

        instructions = [
            "• Exploration: Use [WASD] or [Arrows] to explore Dalal St, Wall St, Tokyo & London.",
            "• Interiors: Press [E] at doors to enter Stock Exchanges, Banks, and Company HQs.",
            "• Trading: Buy & Sell orders are executed on active Stock Exchange Trading Floors.",
            "• Investigation: Press [J] to open your Clue Journal and build an Investment Thesis.",
            "• Progression: Complete field missions and trades to advance from Level 1 to 10!"
        ]

        iy = box.top + 40
        for inst in instructions:
            render_wrapped_text(surface, inst, self.small_font, COLOR_TEXT_WHITE, pygame.Rect(box.left + 14, iy, box.width - 28, 26))
            iy += 32

        btn_ok = Button(pygame.Rect(box.centerx - 60, box.bottom - 36, 120, 26), "Let's Play!", self.font)
        buttons.append(("close_tutorial", btn_ok))
        btn_ok.draw(surface)

        return buttons

    # -------------------------------------------------------------
    # STOCK RETURN BREAKDOWN & 5 EDUCATIONAL LAYERS
    # -------------------------------------------------------------
    def draw_return_breakdown(self, surface: pygame.Surface, game_state: Any, mouse_pos: Tuple[int, int]) -> List[Tuple[str, Button]]:
        buttons: List[Tuple[str, Button]] = []
        pygame.draw.rect(surface, COLOR_BG_DARK, (0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

        # 1. Header
        h_rect = pygame.Rect(8, 6, VIRTUAL_WIDTH - 16, 26)
        pygame.draw.rect(surface, COLOR_PANEL_BG, h_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_BORDER, h_rect, width=1, border_radius=4)
        surface.blit(self.font.render("STOCK RETURN BREAKDOWN — MULTI-FACTOR ENGINE", True, COLOR_TEXT_GOLD), (16, 10))

        btn_close = Button(pygame.Rect(VIRTUAL_WIDTH - 70, 8, 56, 22), "ESC", self.small_font)
        buttons.append(("close", btn_close))

        # 2. Company Tabs
        tabs = ["APEX", "NOVA", "TITN", "AURA", "CHAI", "MEDX"]
        tab_x = 8
        for sym in tabs:
            is_active = (sym == self.breakdown_symbol)
            comp_obj = game_state.market.get_company(sym)
            label = sym if not comp_obj else f"{sym} ${comp_obj.price:.1f}"
            t_btn = Button(pygame.Rect(tab_x, 36, 100, 24), label, self.small_font,
                           bg_color=(28, 45, 85) if is_active else (16, 24, 45),
                           border_color=COLOR_BORDER_ACCENT if is_active else COLOR_BORDER)
            buttons.append((f"breakdown_tab_{sym}", t_btn))
            t_btn.draw(surface)
            tab_x += 105

        comp = game_state.market.get_company(self.breakdown_symbol)
        if not comp:
            return buttons

        b = comp.latest_breakdown

        # 3. Left Panel: Multi-Factor Formula Waterfall
        left_box = pygame.Rect(8, 64, 385, VIRTUAL_HEIGHT - 72)
        pygame.draw.rect(surface, COLOR_PANEL_BG, left_box, border_radius=4)
        pygame.draw.rect(surface, COLOR_BORDER, left_box, width=1, border_radius=4)

        # Title & Price details
        ret_str = f"{comp.pct_change:+.2f}%"
        ret_col = COLOR_GAIN_BRIGHT if comp.pct_change >= 0 else COLOR_LOSS_BRIGHT
        head_txt = f"{comp.name} ({comp.symbol})  ${comp.price:.2f} ({ret_str})"
        surface.blit(self.font.render(head_txt, True, COLOR_TEXT_WHITE), (16, 70))

        if not b:
            surface.blit(self.small_font.render("Advance simulation time to generate factor breakdown.", True, COLOR_TEXT_MUTED), (16, 96))
        else:
            factors = [
                ("1. Fundamentals F(i,t)", b.fundamental_pct, "Rev growth, margins & earnings surprise", (72, 202, 228)),
                ("2. News Events N(i,t)", b.news_pct, "Headline surprise & exponential decay (0.70^t)", (255, 183, 3)),
                ("3. Policy / Macro P(i,t)", b.political_pct, "Clean energy subsidies, tariffs & rate delta", (160, 110, 240)),
                ("4. Market & Sector M(i,t)", b.market_sector_pct, "Beta-weighted index & peer sentiment", (46, 196, 182)),
                ("5. Momentum / Mean-Rev H(i,t)", b.historical_pct, "10-period SMA distance continuation", (230, 140, 60)),
                ("6. Stochastic Luck eps(i,t)", b.noise_pct, "Truncated Gaussian random uncertainty", (200, 200, 210))
            ]

            fy = 94
            for title, pct_val, subtext, color in factors:
                val_sign = "+" if pct_val >= 0 else ""
                val_col = COLOR_GAIN_BRIGHT if pct_val > 0 else (COLOR_LOSS_BRIGHT if pct_val < 0 else COLOR_TEXT_MUTED)
                val_str = f"{val_sign}{pct_val:.2f}%"

                # Factor Label and Value
                surface.blit(self.small_font.render(title, True, COLOR_TEXT_WHITE), (16, fy))
                surface.blit(self.small_font.render(val_str, True, val_col), (260, fy))

                # Mini Factor Bar
                bar_bg = pygame.Rect(310, fy + 2, 70, 8)
                pygame.draw.rect(surface, (14, 20, 36), bar_bg, border_radius=2)
                mid_x = bar_bg.x + 35
                pygame.draw.line(surface, (60, 75, 100), (mid_x, bar_bg.top), (mid_x, bar_bg.bottom), 1)
                bar_len = int(min(32, abs(pct_val) * 10))
                if pct_val > 0:
                    pygame.draw.rect(surface, color, (mid_x, bar_bg.top, bar_len, 8), border_radius=1)
                elif pct_val < 0:
                    pygame.draw.rect(surface, COLOR_LOSS_BRIGHT, (mid_x - bar_len, bar_bg.top, bar_len, 8), border_radius=1)

                surface.blit(self.small_font.render(subtext, True, COLOR_TEXT_MUTED), (16, fy + 14))
                fy += 32

            # Exact Reconciliation Box
            recon_box = pygame.Rect(14, fy + 4, left_box.width - 28, 48)
            pygame.draw.rect(surface, (14, 22, 42), recon_box, border_radius=4)
            pygame.draw.rect(surface, COLOR_BORDER_ACCENT, recon_box, width=1, border_radius=4)

            recon_txt = f"Sum = {b.raw_return_pct:+.2f}%  |  Clamped = {b.clamped_return_pct:+.2f}%  [{comp.lower_bound*100:+.0f}% to {comp.upper_bound*100:+.0f}%]"
            surface.blit(self.small_font.render(recon_txt, True, COLOR_TEXT_GOLD), (recon_box.x + 8, recon_box.y + 6))

            calc_txt = f"Old: ${b.old_price:.2f} x (1 + {b.clamped_return:+.4f}) = New: ${b.new_price:.2f}"
            surface.blit(self.small_font.render(calc_txt, True, COLOR_TEXT_WHITE), (recon_box.x + 8, recon_box.y + 24))

            # Narrative explanation
            expl_box = pygame.Rect(14, fy + 58, left_box.width - 28, 44)
            pygame.draw.rect(surface, (16, 24, 48), expl_box, border_radius=4)
            render_wrapped_text(surface, f"Insight: {b.explanation}", self.small_font, COLOR_TEXT_WHITE, expl_box.inflate(-8, -8))

        # 4. Right Panel: 5 Educational Layers
        right_box = pygame.Rect(401, 64, VIRTUAL_WIDTH - 409, VIRTUAL_HEIGHT - 72)
        pygame.draw.rect(surface, COLOR_PANEL_BG, right_box, border_radius=4)
        pygame.draw.rect(surface, COLOR_BORDER, right_box, width=1, border_radius=4)

        surface.blit(self.font.render("FINANCIAL LEARNING LAYERS", True, COLOR_TEXT_GOLD), (412, 70))

        # Layer Buttons (1-5)
        layer_w = 42
        lx = 412
        for l_num in range(1, 6):
            is_l_active = (self.education_layer == l_num)
            l_btn = Button(pygame.Rect(lx, 94, layer_w, 20), f"L{l_num}", self.small_font,
                           bg_color=(28, 45, 85) if is_l_active else (16, 24, 45),
                           border_color=COLOR_BORDER_ACCENT if is_l_active else COLOR_BORDER)
            buttons.append((f"layer_{l_num}", l_btn))
            l_btn.draw(surface)
            lx += layer_w + 5

        # Educational Content Card
        layer_card = pygame.Rect(412, 122, right_box.width - 24, right_box.height - 66)
        pygame.draw.rect(surface, (14, 22, 42), layer_card, border_radius=4)
        pygame.draw.rect(surface, COLOR_BORDER, layer_card, width=1, border_radius=4)

        layer_data = {
            1: (
                "Layer 1: Beginner Basics",
                [
                    "• Stocks represent partial ownership in a business.",
                    "• Price is set where buyers and sellers agree.",
                    "• Return % = (New Price - Old Price) / Old Price.",
                    "• Exchanges are physical trading floors where licensed brokers match orders.",
                    "• Trading rule: Orders can only be placed on an active Exchange Floor."
                ]
            ),
            2: (
                "Layer 2: Company Fundamentals",
                [
                    "• F(i,t) reflects real business growth and health.",
                    "• Revenue Growth: Sales expansion drives top line.",
                    "• Margin Delta: Wider profit margins boost net earnings.",
                    "• Earnings Surprise: Beating Wall St consensus creates positive price surges.",
                    "• P/E Ratio: Price paid per dollar of annual earnings."
                ]
            ),
            3: (
                "Layer 3: News & Politics",
                [
                    "• N(i,t) and P(i,t) reflect macro policy and news.",
                    "• Anticipated News: If 60% expected, surprise is 40%.",
                    "• 'Buy rumor, sell news': Good news can trigger selling if market priced in higher.",
                    "• Policy Subsidies: Fiscal bills directly lower clean energy and infrastructure costs.",
                    "• News Impact decays exponentially: 0.70^age."
                ]
            ),
            4: (
                "Layer 4: Statistics & Risk",
                [
                    "• Historical Volatility: Sample standard deviation sigma = sqrt(sum(r - mean)^2 / (n-1)).",
                    "• High Beta (APEX): Amplifies market moves.",
                    "• Low Beta (CHAI): Defensive anchor during sell-offs.",
                    "• Mean Reversion: Extreme price stretches pull back.",
                    "• Position Sizing: Never bet entire cash on 1 ticker."
                ]
            ),
            5: (
                "Layer 5: Master Strategy",
                [
                    "• Synthesize: F + N + P + M + H + luck.",
                    "• Formulate thesis before trading in Journal [J].",
                    "• Diversify across at least 3 distinct sectors.",
                    "• Reconcile returns: Compare predicted thesis to actual simulated price resolution.",
                    "• Manage drawdowns and build long-term wealth!"
                ]
            )
        }

        l_title, l_points = layer_data.get(self.education_layer, layer_data[1])
        surface.blit(self.font.render(l_title, True, COLOR_TEXT_GOLD), (layer_card.x + 8, layer_card.y + 8))

        ly = layer_card.y + 32
        for pt in l_points:
            render_wrapped_text(surface, pt, self.small_font, COLOR_TEXT_WHITE, pygame.Rect(layer_card.x + 8, ly, layer_card.width - 16, 32))
            ly += 30

        for act, b in buttons:
            if not act.startswith("breakdown_tab_") and not act.startswith("layer_"):
                b.draw(surface)

        return buttons

    # -------------------------------------------------------------
    # STORY CAMPAIGN PROGRESS SCREEN
    # -------------------------------------------------------------
    def draw_campaign_progress(self, surface: pygame.Surface, game_state: Any, mouse_pos: Tuple[int, int]) -> List[Tuple[str, Button]]:
        buttons: List[Tuple[str, Button]] = []
        pygame.draw.rect(surface, COLOR_BG_DARK, (0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

        story = game_state.story

        # 1. Header
        h_rect = pygame.Rect(8, 6, VIRTUAL_WIDTH - 16, 26)
        pygame.draw.rect(surface, COLOR_PANEL_BG, h_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_BORDER, h_rect, width=1, border_radius=4)
        surface.blit(self.font.render("STORY CAMPAIGN: FROM ROOKIE TO MARKET STRATEGIST", True, COLOR_TEXT_GOLD), (16, 10))

        btn_close = Button(pygame.Rect(VIRTUAL_WIDTH - 70, 8, 56, 22), "ESC", self.small_font)
        buttons.append(("close", btn_close))

        # 2. Left Panel: 6 Chapters Selector
        left_box = pygame.Rect(8, 36, 195, VIRTUAL_HEIGHT - 44)
        pygame.draw.rect(surface, COLOR_PANEL_BG, left_box, border_radius=4)
        pygame.draw.rect(surface, COLOR_BORDER, left_box, width=1, border_radius=4)

        surface.blit(self.font.render("CAMPAIGN CHAPTERS", True, COLOR_TEXT_WHITE), (16, 42))
        pygame.draw.line(surface, COLOR_BORDER, (8, 58), (203, 58), 1)

        cy = 64
        for idx, chap in enumerate(story.chapters):
            is_sel = (idx == self.campaign_selected_chapter)
            is_completed = (idx < story.current_chapter_idx) or story.campaign_completed
            is_active = (idx == story.current_chapter_idx) and not story.campaign_completed
            is_locked = (idx > story.current_chapter_idx) and not story.campaign_completed

            status_icon = "✓" if is_completed else ("★" if is_active else "🔒")
            btn_txt = f"{status_icon} Ch {idx + 1}"

            row_btn = Button(pygame.Rect(12, cy, 187, 42), "", self.small_font,
                             bg_color=(28, 45, 85) if is_sel else (16, 24, 45),
                             border_color=COLOR_BORDER_ACCENT if is_sel else COLOR_BORDER)
            buttons.append((f"sel_chapter_{idx}", row_btn))
            row_btn.draw(surface)

            # Titles inside row
            surface.blit(self.font.render(btn_txt, True, COLOR_GAIN_BRIGHT if is_completed else (COLOR_TEXT_GOLD if is_active else COLOR_TEXT_MUTED)), (18, cy + 4))
            sub = truncate_text(chap.get("subtitle", chap.get("title", "")), self.small_font, 175)
            surface.blit(self.small_font.render(sub, True, COLOR_TEXT_WHITE), (18, cy + 22))

            cy += 46

        # 3. Right Panel: Objectives Checklist & Educational Lesson
        right_box = pygame.Rect(209, 36, VIRTUAL_WIDTH - 217, VIRTUAL_HEIGHT - 44)
        pygame.draw.rect(surface, COLOR_PANEL_BG, right_box, border_radius=4)
        pygame.draw.rect(surface, COLOR_BORDER, right_box, width=1, border_radius=4)

        sel_chap = story.chapters[self.campaign_selected_chapter] if self.campaign_selected_chapter < len(story.chapters) else story.chapters[0]
        surface.blit(self.font.render(sel_chap["title"], True, COLOR_TEXT_GOLD), (220, 42))
        surface.blit(self.small_font.render(sel_chap.get("description", ""), True, COLOR_TEXT_MUTED), (220, 60))

        # Route Guidance Toggle Button
        guide_active = getattr(game_state.player, "route_guidance_active", True)
        g_btn_txt = "GUIDANCE [G]: ON" if guide_active else "GUIDANCE [G]: OFF"
        btn_guide = Button(pygame.Rect(right_box.right - 130, 40, 120, 22), g_btn_txt, self.small_font,
                           bg_color=(20, 100, 65) if guide_active else (80, 40, 45))
        buttons.append(("toggle_guidance", btn_guide))
        btn_guide.draw(surface)

        # Objectives List
        oy = 82
        for o_idx, obj in enumerate(sel_chap.get("objectives", [])):
            is_obj_done = obj["id"] in story.completed_objectives
            is_obj_active = (self.campaign_selected_chapter == story.current_chapter_idx) and (o_idx == story.current_objective_idx)

            card_bg = (24, 38, 70) if is_obj_active else (14, 22, 42)
            card_border = COLOR_TEXT_GOLD if is_obj_active else (COLOR_GAIN if is_obj_done else COLOR_BORDER)

            card_rect = pygame.Rect(218, oy, right_box.width - 18, 48)
            pygame.draw.rect(surface, card_bg, card_rect, border_radius=4)
            pygame.draw.rect(surface, card_border, card_rect, width=1, border_radius=4)

            chk = "✓" if is_obj_done else ("➤" if is_obj_active else "•")
            chk_col = COLOR_GAIN_BRIGHT if is_obj_done else (COLOR_TEXT_GOLD if is_obj_active else COLOR_TEXT_MUTED)
            surface.blit(self.font.render(f"{chk} {obj['title']}", True, chk_col), (226, oy + 4))

            # Reward Tag
            rw_str = f"+{obj.get('reward_xp', 0)} XP"
            if obj.get('reward_cash', 0) > 0:
                rw_str += f" | +${obj['reward_cash']:.0f}"
            surface.blit(self.small_font.render(rw_str, True, COLOR_BORDER_ACCENT), (card_rect.right - 100, oy + 4))

            # Desc
            desc_tr = truncate_text(obj.get("desc", ""), self.small_font, card_rect.width - 20)
            surface.blit(self.small_font.render(desc_tr, True, COLOR_TEXT_WHITE), (226, oy + 22))

            oy += 52

        # Bottom Lesson Card
        active_obj = story.get_active_objective()
        if active_obj and "lesson" in active_obj:
            less_rect = pygame.Rect(218, right_box.bottom - 46, right_box.width - 18, 40)
            pygame.draw.rect(surface, (18, 28, 54), less_rect, border_radius=4)
            pygame.draw.rect(surface, COLOR_BORDER_ACCENT, less_rect, width=1, border_radius=4)
            render_wrapped_text(surface, f"Strategy Rule: {active_obj['lesson']}", self.small_font, COLOR_TEXT_WHITE, less_rect.inflate(-8, -6))

        for act, b in buttons:
            if not act.startswith("sel_chapter_") and act != "toggle_guidance":
                b.draw(surface)

        return buttons

    # -------------------------------------------------------------
    # INVESTMENT THESIS FORMULATION & RESOLUTION SCREEN
    # -------------------------------------------------------------
    def draw_investment_thesis(self, surface: pygame.Surface, game_state: Any, mouse_pos: Tuple[int, int]) -> List[Tuple[str, Button]]:
        buttons: List[Tuple[str, Button]] = []
        pygame.draw.rect(surface, COLOR_BG_DARK, (0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

        inv = game_state.investigation

        # Header
        h_rect = pygame.Rect(8, 6, VIRTUAL_WIDTH - 16, 26)
        pygame.draw.rect(surface, COLOR_PANEL_BG, h_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_BORDER, h_rect, width=1, border_radius=4)
        surface.blit(self.font.render("INVESTMENT THESIS FORMULATION & RESOLUTION", True, COLOR_TEXT_GOLD), (16, 10))

        btn_close = Button(pygame.Rect(VIRTUAL_WIDTH - 70, 8, 56, 22), "ESC", self.small_font)
        buttons.append(("close", btn_close))

        # Stock Tabs
        tabs = ["APEX", "TITN", "CHAI", "AURA"]
        tab_x = 8
        for sym in tabs:
            is_active = (sym == self.thesis_symbol)
            t_btn = Button(pygame.Rect(tab_x, 36, 95, 24), sym, self.small_font,
                           bg_color=(28, 45, 85) if is_active else (16, 24, 45),
                           border_color=COLOR_BORDER_ACCENT if is_active else COLOR_BORDER)
            buttons.append((f"thesis_tab_{sym}", t_btn))
            t_btn.draw(surface)
            tab_x += 100

        comp = game_state.market.get_company(self.thesis_symbol)
        if not comp:
            return buttons

        # Left Panel: Formulate Thesis
        left_box = pygame.Rect(8, 64, 340, VIRTUAL_HEIGHT - 72)
        pygame.draw.rect(surface, COLOR_PANEL_BG, left_box, border_radius=4)
        pygame.draw.rect(surface, COLOR_BORDER, left_box, width=1, border_radius=4)

        surface.blit(self.font.render(f"FORMULATE THESIS: {comp.name}", True, COLOR_TEXT_WHITE), (16, 70))
        surface.blit(self.small_font.render(f"Current Market Price: ${comp.price:.2f}", True, COLOR_TEXT_GOLD), (16, 88))

        # Clues checklist
        clues = inv.get_clues_for_company(self.thesis_symbol)
        surface.blit(self.small_font.render(f"Evidence Collected: {len(clues)} Clues", True, COLOR_BORDER_ACCENT), (16, 106))
        cy = 124
        for c in clues[:3]:
            surface.blit(self.small_font.render(f"✓ {c.title}", True, COLOR_GAIN_BRIGHT), (20, cy))
            cy += 16
        if not clues:
            surface.blit(self.small_font.render("No field clues found. Interview leads at HQ!", True, COLOR_TEXT_MUTED), (20, cy))
            cy += 16

        # Confidence Rating
        rating_label, thesis_summary = inv.get_thesis_rating(self.thesis_symbol)
        surface.blit(self.small_font.render(f"Conviction Score: {rating_label}", True, COLOR_TEXT_GOLD), (16, cy + 8))

        # Position Sizing Buttons
        surface.blit(self.small_font.render("Target Portfolio Allocation:", True, COLOR_TEXT_WHITE), (16, cy + 28))
        sizes = [10.0, 25.0, 50.0, 100.0]
        sx = 16
        for sz in sizes:
            is_sz = (self.thesis_size_pct == sz)
            s_btn = Button(pygame.Rect(sx, cy + 44, 45, 20), f"{int(sz)}%", self.small_font,
                           bg_color=(28, 45, 85) if is_sz else (16, 24, 45),
                           border_color=COLOR_BORDER_ACCENT if is_sz else COLOR_BORDER)
            buttons.append((f"size_{int(sz)}", s_btn))
            s_btn.draw(surface)
            sx += 50

        # Holding Horizon Buttons
        surface.blit(self.small_font.render("Target Holding Horizon:", True, COLOR_TEXT_WHITE), (16, cy + 70))
        horizons = ["1-3 Days", "1-2 Weeks", "Long Term"]
        hx = 16
        for hz in horizons:
            is_hz = (self.thesis_horizon == hz)
            h_btn = Button(pygame.Rect(hx, cy + 86, 75, 20), hz, self.small_font,
                           bg_color=(28, 45, 85) if is_hz else (16, 24, 45),
                           border_color=COLOR_BORDER_ACCENT if is_hz else COLOR_BORDER)
            buttons.append((f"horizon_{hz}", h_btn))
            h_btn.draw(surface)
            hx += 80

        # Submit Thesis Button
        btn_submit = Button(pygame.Rect(16, left_box.bottom - 36, left_box.width - 32, 26), "RECORD THESIS (+100 XP)", self.font,
                            bg_color=(25, 110, 65), hover_color=(35, 145, 85))
        buttons.append(("record_thesis", btn_submit))
        btn_submit.draw(surface)

        # Right Panel: Recorded Theses History & Resolution
        right_box = pygame.Rect(356, 64, VIRTUAL_WIDTH - 364, VIRTUAL_HEIGHT - 72)
        pygame.draw.rect(surface, COLOR_PANEL_BG, right_box, border_radius=4)
        pygame.draw.rect(surface, COLOR_BORDER, right_box, width=1, border_radius=4)

        surface.blit(self.font.render("RECORDED THESES & RESOLUTIONS", True, COLOR_TEXT_GOLD), (368, 70))

        theses = inv.theses
        if not theses:
            msg = "No formal theses submitted yet. Formulate an investment thesis on the left panel to track prediction performance against real simulated outcomes!"
            render_wrapped_text(surface, msg, self.small_font, COLOR_TEXT_MUTED, pygame.Rect(368, 96, right_box.width - 24, 100))
        else:
            ty = 96
            for th in theses[:4]:
                th_comp = game_state.market.get_company(th.company_symbol)
                cur_p = th_comp.price if th_comp else th.entry_price
                outcome_text = th.evaluate_outcome(cur_p)

                th_box = pygame.Rect(366, ty, right_box.width - 20, 52)
                pygame.draw.rect(surface, (14, 22, 42), th_box, border_radius=4)
                pygame.draw.rect(surface, COLOR_BORDER, th_box, width=1, border_radius=4)

                pnl_pct = ((cur_p - th.entry_price) / max(0.01, th.entry_price)) * 100.0
                pnl_col = COLOR_GAIN_BRIGHT if pnl_pct >= 0 else COLOR_LOSS_BRIGHT

                surface.blit(self.font.render(f"{th.company_symbol} @ ${th.entry_price:.2f} -> Now: ${cur_p:.2f} ({pnl_pct:+.1f}%)", True, pnl_col), (372, ty + 4))
                surface.blit(self.small_font.render(f"Alloc: {th.position_size_pct:.0f}%  |  Horizon: {th.holding_period}  |  {th.confidence_level} Conviction", True, COLOR_BORDER_ACCENT), (372, ty + 20))
                surface.blit(self.small_font.render(outcome_text, True, COLOR_TEXT_WHITE), (372, ty + 34))

                ty += 56

        for act, b in buttons:
            if not act.startswith("thesis_tab_") and not act.startswith("size_") and not act.startswith("horizon_") and act != "record_thesis":
                b.draw(surface)

        return buttons

