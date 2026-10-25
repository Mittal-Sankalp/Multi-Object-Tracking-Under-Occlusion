"""
MarketQuest - Stock Market Simulation Engine
Transparent, mathematically defined multi-factor stock return model.

Formula:
r(i,t) = clamp(
    F(i,t) + N(i,t) + P(i,t) + M(i,t) + H(i,t) + epsilon(i,t),
    lower_bound(i),
    upper_bound(i)
)
price(i,t+1) = max(MIN_STOCK_PRICE, price(i,t) * (1 + r(i,t)))

Where:
- F: Fundamental performance contribution (revenue growth, margins, earnings surprise)
- N: News & events contribution (headline surprise, sensitivity, exponential age decay)
- P: Political & macroeconomic policy contribution (subsidies, tariffs, rate cycles)
- M: Broad market and sector factor (beta-weighted market and sector sentiment)
- H: Historical momentum / mean reversion signal from moving averages
- epsilon: Seeded stochastic uncertainty / noise factor (truncated Gaussian luck)
"""

import json
import random
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
from config import MIN_STOCK_PRICE, MAX_STOCK_PRICE, PRICE_HISTORY_LENGTH, DATA_DIR

# Tunable Global Weights for Return Engine
WEIGHT_FUNDAMENTALS = 0.15
WEIGHT_NEWS = 0.25
WEIGHT_POLICY = 0.20
WEIGHT_MARKET = 0.15
WEIGHT_MOMENTUM = 0.10
WEIGHT_NOISE = 0.15
EVENT_DECAY_RATE = 0.70


@dataclass
class ReturnBreakdown:
    symbol: str
    fundamental: float          # F(i,t) in decimal return units
    news: float                 # N(i,t) in decimal return units
    political: float            # P(i,t) in decimal return units
    market_sector: float        # M(i,t) in decimal return units
    historical_momentum: float  # H(i,t) in decimal return units
    noise_luck: float           # epsilon(i,t) in decimal return units
    raw_return: float           # F + N + P + M + H + epsilon
    clamped_return: float       # clamp(raw, lower_bound, upper_bound)
    was_clamped: bool           # Whether return was capped by circuit breaker bounds
    old_price: float            # Price before simulation step
    new_price: float            # Price after simulation step
    explanation: str            # Plain-English narrative for player education
    step: int                   # Simulation day/step

    @property
    def fundamental_pct(self) -> float:
        return round(self.fundamental * 100.0, 2)

    @property
    def news_pct(self) -> float:
        return round(self.news * 100.0, 2)

    @property
    def political_pct(self) -> float:
        return round(self.political * 100.0, 2)

    @property
    def market_sector_pct(self) -> float:
        return round(self.market_sector * 100.0, 2)

    @property
    def historical_pct(self) -> float:
        return round(self.historical_momentum * 100.0, 2)

    @property
    def noise_pct(self) -> float:
        return round(self.noise_luck * 100.0, 2)

    @property
    def raw_return_pct(self) -> float:
        return round(self.raw_return * 100.0, 2)

    @property
    def clamped_return_pct(self) -> float:
        return round(self.clamped_return * 100.0, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "fundamental": self.fundamental,
            "news": self.news,
            "political": self.political,
            "market_sector": self.market_sector,
            "historical_momentum": self.historical_momentum,
            "noise_luck": self.noise_luck,
            "raw_return": self.raw_return,
            "clamped_return": self.clamped_return,
            "was_clamped": self.was_clamped,
            "old_price": self.old_price,
            "new_price": self.new_price,
            "explanation": self.explanation,
            "step": self.step
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReturnBreakdown':
        return cls(
            symbol=data["symbol"],
            fundamental=float(data.get("fundamental", 0.0)),
            news=float(data.get("news", 0.0)),
            political=float(data.get("political", 0.0)),
            market_sector=float(data.get("market_sector", 0.0)),
            historical_momentum=float(data.get("historical_momentum", 0.0)),
            noise_luck=float(data.get("noise_luck", 0.0)),
            raw_return=float(data.get("raw_return", 0.0)),
            clamped_return=float(data.get("clamped_return", 0.0)),
            was_clamped=bool(data.get("was_clamped", False)),
            old_price=float(data.get("old_price", 0.0)),
            new_price=float(data.get("new_price", 0.0)),
            explanation=data.get("explanation", ""),
            step=int(data.get("step", 1))
        )


@dataclass
class Company:
    symbol: str
    name: str
    sector: str
    price: float
    volatility: float
    description: str
    pe_ratio: float = 20.0
    dividend_yield: float = 1.0
    market_cap: str = "100B"
    volatility_class: str = "Medium"
    headquarters: str = "Financial District"
    products: List[str] = field(default_factory=list)
    growth_drivers: str = ""
    risks: str = ""
    previous_price: float = 0.0
    high: float = 0.0
    low: float = 0.0
    open_price: float = 0.0
    price_history: List[float] = field(default_factory=list)

    # Multi-Factor Model Parameters
    revenue_growth_rate: float = 0.10      # Annualized organic revenue growth (e.g. 0.14 = +14%)
    profit_margin_delta: float = 0.01      # Margin trend (e.g. +0.02 = +2% expansion)
    earnings_surprise: float = 0.01        # Latest reported earnings surprise vs consensus
    business_quality: float = 0.80         # Quality score (0.0 to 1.0, e.g. moat, returns on capital)
    fundamental_risk: float = 0.30         # Risk score (0.0 to 1.0, e.g. debt leverage, cyclicality)
    beta_market: float = 1.00              # Sensitivity to broad market index
    beta_sector: float = 1.00              # Sensitivity to sector peer group
    policy_sensitivity: Dict[str, float] = field(default_factory=dict) # Policy sensitivities
    event_sensitivity: float = 1.00        # Sensitivity multiplier for breaking news
    lower_bound: float = -0.15             # Maximum 1-step downside limit (-15%)
    upper_bound: float = 0.15              # Maximum 1-step upside circuit breaker (+15%)

    latest_breakdown: Optional[ReturnBreakdown] = None

    def __post_init__(self):
        if not self.previous_price:
            self.previous_price = self.price
        if not self.high:
            self.high = self.price
        if not self.low:
            self.low = self.price
        if not self.open_price:
            self.open_price = self.price
        if not self.price_history:
            self.price_history = [self.price]

    @property
    def change(self) -> float:
        return self.price - self.previous_price

    @property
    def pct_change(self) -> float:
        if self.previous_price <= 0:
            return 0.0
        return (self.change / self.previous_price) * 100.0

    @property
    def sentiment(self) -> str:
        """Categorize short-term market sentiment."""
        pct = self.pct_change
        if pct >= 1.5:
            return "Bullish"
        elif pct <= -1.5:
            return "Bearish"
        return "Neutral"

    @property
    def historical_volatility_pct(self) -> float:
        """Calculate annualized historical volatility percentage from price history."""
        step_vol = self.step_volatility
        annualized = step_vol * math.sqrt(252) * 100.0
        return round(max(5.0, min(150.0, annualized)), 1)

    @property
    def step_volatility(self) -> float:
        """
        Calculate sample standard deviation of per-step simple returns:
        sigma = sqrt( sum( (r_k - mean_r)^2 ) / (n - 1) )
        """
        if len(self.price_history) < 3:
            return self.volatility

        returns = []
        for i in range(1, len(self.price_history)):
            p0 = self.price_history[i - 1]
            p1 = self.price_history[i]
            if p0 > 0:
                returns.append((p1 - p0) / p0)

        if len(returns) < 2:
            return self.volatility

        n = len(returns)
        mean_r = sum(returns) / n
        variance = sum((r - mean_r) ** 2 for r in returns) / (n - 1)
        return math.sqrt(max(0.000001, variance))

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "symbol": self.symbol,
            "name": self.name,
            "sector": self.sector,
            "price": round(self.price, 2),
            "volatility": self.volatility,
            "volatility_class": self.volatility_class,
            "headquarters": self.headquarters,
            "description": self.description,
            "products": self.products,
            "growth_drivers": self.growth_drivers,
            "risks": self.risks,
            "pe_ratio": self.pe_ratio,
            "dividend_yield": self.dividend_yield,
            "market_cap": self.market_cap,
            "previous_price": round(self.previous_price, 2),
            "high": round(self.high, 2),
            "low": round(self.low, 2),
            "open_price": round(self.open_price, 2),
            "price_history": [round(p, 2) for p in self.price_history],
            "revenue_growth_rate": self.revenue_growth_rate,
            "profit_margin_delta": self.profit_margin_delta,
            "earnings_surprise": self.earnings_surprise,
            "business_quality": self.business_quality,
            "fundamental_risk": self.fundamental_risk,
            "beta_market": self.beta_market,
            "beta_sector": self.beta_sector,
            "policy_sensitivity": self.policy_sensitivity,
            "event_sensitivity": self.event_sensitivity,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
        }
        if self.latest_breakdown:
            d["latest_breakdown"] = self.latest_breakdown.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Company':
        comp = cls(
            symbol=data["symbol"],
            name=data["name"],
            sector=data["sector"],
            price=float(data["price"]),
            volatility=float(data.get("volatility", 0.03)),
            volatility_class=data.get("volatility_class", "Medium"),
            headquarters=data.get("headquarters", "Financial District"),
            description=data.get("description", ""),
            products=data.get("products", []),
            growth_drivers=data.get("growth_drivers", ""),
            risks=data.get("risks", ""),
            pe_ratio=float(data.get("pe_ratio", 20.0)),
            dividend_yield=float(data.get("dividend_yield", 1.0)),
            market_cap=data.get("market_cap", "100B"),
            previous_price=float(data.get("previous_price", data["price"])),
            high=float(data.get("high", data["price"])),
            low=float(data.get("low", data["price"])),
            open_price=float(data.get("open_price", data["price"])),
            price_history=[float(p) for p in data.get("price_history", [data["price"]])],
            revenue_growth_rate=float(data.get("revenue_growth_rate", 0.10)),
            profit_margin_delta=float(data.get("profit_margin_delta", 0.01)),
            earnings_surprise=float(data.get("earnings_surprise", 0.01)),
            business_quality=float(data.get("business_quality", 0.80)),
            fundamental_risk=float(data.get("fundamental_risk", 0.30)),
            beta_market=float(data.get("beta_market", 1.00)),
            beta_sector=float(data.get("beta_sector", 1.00)),
            policy_sensitivity=data.get("policy_sensitivity", {}),
            event_sensitivity=float(data.get("event_sensitivity", 1.00)),
            lower_bound=float(data.get("lower_bound", -0.15)),
            upper_bound=float(data.get("upper_bound", 0.15))
        )
        if "latest_breakdown" in data and data["latest_breakdown"]:
            comp.latest_breakdown = ReturnBreakdown.from_dict(data["latest_breakdown"])
        return comp


@dataclass
class MarketEvent:
    id: str
    headline: str
    explanation: str
    affected_type: str  # "company", "sector", "all"
    target: str         # symbol, sector name, or "ALL"
    impact: float       # percentage impact, e.g. 0.15 = +15%
    duration_days: int
    education: str
    category: str = "Market News"
    exchange_region: str = "Global"
    direction: str = "Positive"
    disclaimer: str = "Fictional in-game simulation event."
    anticipated: bool = False
    policy_key: str = ""


@dataclass
class ActiveEvent:
    event: MarketEvent
    age_steps: int = 0
    duration_steps: int = 2

    @property
    def current_strength(self) -> float:
        """Decaying impact strength over simulation steps: strength = 0.70^age."""
        return max(0.05, EVENT_DECAY_RATE ** self.age_steps)


class MarketEngine:
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
        self.companies: Dict[str, Company] = {}
        self.events_catalog: Dict[str, MarketEvent] = {}
        self.active_events: List[ActiveEvent] = []
        self.news_feed: List[Dict[str, Any]] = []
        self.day: int = 1

        # Current Macroeconomic Environment State
        self.macro_policy = {
            "active_policy": "none",
            "policy_magnitude": 0.0,
            "interest_rate_delta": 0.0,
            "infrastructure_spend": 0.0
        }

        self.load_catalogs()

    def set_seed(self, seed: int):
        self.rng = random.Random(seed)

    def load_catalogs(self, companies_path: Optional[Path] = None, events_path: Optional[Path] = None):
        c_path = companies_path or (DATA_DIR / "companies.json")
        e_path = events_path or (DATA_DIR / "events.json")

        if c_path.exists():
            with open(c_path, 'r', encoding='utf-8') as f:
                c_data = json.load(f)
                for item in c_data:
                    comp = Company(
                        symbol=item["symbol"],
                        name=item["name"],
                        sector=item["sector"],
                        price=float(item["price"]),
                        volatility=float(item["volatility"]),
                        volatility_class=item.get("volatility_class", "Medium"),
                        headquarters=item.get("headquarters", "Financial District"),
                        description=item["description"],
                        products=item.get("products", []),
                        growth_drivers=item.get("growth_drivers", ""),
                        risks=item.get("risks", ""),
                        pe_ratio=float(item.get("pe_ratio", 20.0)),
                        dividend_yield=float(item.get("dividend_yield", 1.0)),
                        market_cap=item.get("market_cap", "100B"),
                        revenue_growth_rate=float(item.get("revenue_growth_rate", 0.10)),
                        profit_margin_delta=float(item.get("profit_margin_delta", 0.01)),
                        earnings_surprise=float(item.get("earnings_surprise", 0.01)),
                        business_quality=float(item.get("business_quality", 0.80)),
                        fundamental_risk=float(item.get("fundamental_risk", 0.30)),
                        beta_market=float(item.get("beta_market", 1.00)),
                        beta_sector=float(item.get("beta_sector", 1.00)),
                        policy_sensitivity=item.get("policy_sensitivity", {}),
                        event_sensitivity=float(item.get("event_sensitivity", 1.00)),
                        lower_bound=float(item.get("lower_bound", -0.15)),
                        upper_bound=float(item.get("upper_bound", 0.15))
                    )
                    self.companies[comp.symbol] = comp

        if e_path.exists():
            with open(e_path, 'r', encoding='utf-8') as f:
                e_data = json.load(f)
                for item in e_data:
                    ev = MarketEvent(
                        id=item["id"],
                        headline=item["headline"],
                        explanation=item["explanation"],
                        affected_type=item["affected_type"],
                        target=item["target"],
                        impact=float(item["impact"]),
                        duration_days=int(item.get("duration_days", 2)),
                        education=item["education"],
                        category=item.get("category", "General"),
                        exchange_region=item.get("exchange_region", "Global"),
                        direction=item.get("direction", "Positive"),
                        disclaimer=item.get("disclaimer", "Fictional simulation scenario."),
                        anticipated=bool(item.get("anticipated", False)),
                        policy_key=item.get("policy_key", "")
                    )
                    self.events_catalog[ev.id] = ev

        if self.companies:
            self.generate_initial_history()

    def generate_initial_history(self, points: int = PRICE_HISTORY_LENGTH):
        """Generate smooth historical price history for charting at game start."""
        for comp in self.companies.values():
            base = comp.price
            temp_prices = []
            p = base
            for _ in range(points - 1):
                pct = self.rng.gauss(0.0002, comp.volatility * 0.4)
                p = max(MIN_STOCK_PRICE, min(MAX_STOCK_PRICE, p * (1.0 + pct)))
                temp_prices.append(p)

            scale = base / temp_prices[-1] if temp_prices and temp_prices[-1] > 0 else 1.0
            norm_history = [round(max(MIN_STOCK_PRICE, min(MAX_STOCK_PRICE, x * scale)), 2) for x in temp_prices]
            norm_history.append(round(base, 2))

            comp.price_history = norm_history[-points:]
            comp.previous_price = comp.price_history[-2] if len(comp.price_history) >= 2 else base
            comp.high = max(comp.price_history)
            comp.low = min(comp.price_history)
            comp.open_price = comp.price_history[0]

    def set_macro_policy(self, policy_key: str, magnitude: float, interest_rate_delta: float = 0.0):
        """Set active macroeconomic policy environment."""
        self.macro_policy["active_policy"] = policy_key
        self.macro_policy["policy_magnitude"] = magnitude
        self.macro_policy["interest_rate_delta"] = interest_rate_delta

    def tick(self) -> List[Dict[str, Any]]:
        """
        Advance the market simulation by 1 simulation step.
        Computes the transparent multi-factor return:
        r(i,t) = clamp(F + N + P + M + H + epsilon, lower_bound, upper_bound)
        price(i,t+1) = max(MIN_STOCK_PRICE, price(i,t) * (1 + r(i,t)))
        """
        self.day += 1
        daily_reports = []

        # 1. Broad Market Factor (N(0.0004, 0.004))
        broad_market_return = self.rng.gauss(0.0004, 0.004)

        # 2. Sector Specific Factors
        sectors = set(c.sector for c in self.companies.values())
        sector_returns = {sec: self.rng.gauss(0.0001, 0.005) for sec in sectors}

        # 3. Compute returns for each company
        for comp in self.companies.values():
            old_price = comp.price
            comp.previous_price = old_price

            # Term 1: Fundamentals F(i,t)
            # Driven by changes in revenue growth vs benchmark (8%), margin expansion, and earnings surprise
            benchmark_growth = 0.08
            fund_rev = (comp.revenue_growth_rate - benchmark_growth) * 0.35
            fund_margin = comp.profit_margin_delta * 0.35
            fund_surprise = comp.earnings_surprise * 0.30
            quality_mod = comp.business_quality / max(0.2, comp.fundamental_risk)
            f_component = WEIGHT_FUNDAMENTALS * (fund_rev + fund_margin + fund_surprise) * min(1.5, quality_mod)
            f_component = max(-0.04, min(0.04, f_component))

            # Term 2: News & Events N(i,t) with decay
            n_component = 0.0
            news_notes = []
            for active in self.active_events:
                ev = active.event
                applies = False
                if ev.affected_type == "company" and ev.target.upper() == comp.symbol.upper():
                    applies = True
                elif ev.affected_type == "sector" and ev.target.lower() == comp.sector.lower():
                    applies = True
                elif ev.affected_type == "all":
                    applies = True

                if applies:
                    # If anticipated, market already priced in 60%, surprise is 40%
                    surprise_factor = 0.40 if ev.anticipated else 1.00
                    decayed_impact = ev.impact * surprise_factor * active.current_strength
                    term = comp.event_sensitivity * decayed_impact * WEIGHT_NEWS
                    n_component += term
                    news_notes.append(f"{ev.headline[:24]} ({round(term*100, 1)}%)")

            n_component = max(-0.08, min(0.08, n_component))

            # Term 3: Political & Macroeconomic P(i,t)
            p_component = 0.0
            pol_key = self.macro_policy.get("active_policy", "none")
            pol_mag = self.macro_policy.get("policy_magnitude", 0.0)
            rate_delta = self.macro_policy.get("interest_rate_delta", 0.0)

            if pol_key in comp.policy_sensitivity:
                p_component += comp.policy_sensitivity[pol_key] * pol_mag
            if "interest_rates" in comp.policy_sensitivity:
                p_component += comp.policy_sensitivity["interest_rates"] * rate_delta

            p_component = p_component * WEIGHT_POLICY
            p_component = max(-0.05, min(0.05, p_component))

            # Term 4: Market & Sector M(i,t)
            sec_return = sector_returns.get(comp.sector, 0.0)
            m_component = (comp.beta_market * broad_market_return + comp.beta_sector * sec_return) * WEIGHT_MARKET
            m_component = max(-0.04, min(0.04, m_component))

            # Term 5: Historical Momentum & Mean Reversion H(i,t)
            h_component = 0.0
            if len(comp.price_history) >= 5:
                window = comp.price_history[-10:] if len(comp.price_history) >= 10 else comp.price_history
                sma = sum(window) / len(window)
                if sma > 0:
                    distance_from_sma = (comp.price - sma) / sma
                    if abs(distance_from_sma) > 0.08:
                        # Mean reversion pull
                        h_component = -0.15 * distance_from_sma
                    else:
                        # Short term momentum continuation
                        h_component = 0.10 * distance_from_sma

            h_component = h_component * WEIGHT_MOMENTUM
            h_component = max(-0.025, min(0.025, h_component))

            # Term 6: Seeded Uncertainty / Noise epsilon(i,t)
            # Truncated Gaussian: standard normal clipped to [-2.5, 2.5]
            z = max(-2.5, min(2.5, self.rng.gauss(0.0, 1.0)))
            noise_scale = comp.volatility * 0.25 * WEIGHT_NOISE
            epsilon_component = noise_scale * z
            epsilon_component = max(-0.03, min(0.03, epsilon_component))

            # Total Raw Return
            raw_return = f_component + n_component + p_component + m_component + h_component + epsilon_component

            # Clamp Return to Configured Bounds
            clamped_return = max(comp.lower_bound, min(comp.upper_bound, raw_return))
            was_clamped = (clamped_return != raw_return)

            # Update Price: price(t+1) = max(MIN_STOCK_PRICE, price(t) * (1 + r))
            new_price = max(MIN_STOCK_PRICE, min(MAX_STOCK_PRICE, round(old_price * (1.0 + clamped_return), 2)))
            comp.price = new_price

            comp.price_history.append(new_price)
            if len(comp.price_history) > PRICE_HISTORY_LENGTH:
                comp.price_history.pop(0)

            comp.high = max(comp.high, new_price)
            comp.low = min(comp.low, new_price)

            # Educational narrative explaining factors
            narrative_parts = []
            if abs(f_component) > 0.003:
                sign = "supported" if f_component > 0 else "pressured"
                narrative_parts.append(f"Core fundamentals {sign} valuation")
            if abs(n_component) > 0.003:
                sign = "boosted by" if n_component > 0 else "dragged down by"
                narrative_parts.append(f"{sign} news catalysts")
            if abs(p_component) > 0.003:
                sign = "tailwinds" if p_component > 0 else "headwinds"
                narrative_parts.append(f"macro policy {sign}")
            if abs(m_component) > 0.003:
                sign = "tailwind" if m_component > 0 else "drag"
                narrative_parts.append(f"sector {sign}")
            if abs(epsilon_component) > 0.005:
                narrative_parts.append("random stochastic variance")

            if not narrative_parts:
                narrative = "Stable trading session with low fundamental variance."
            else:
                narrative = ", and ".join(narrative_parts).capitalize() + "."

            # Attach full ReturnBreakdown dataclass to company
            comp.latest_breakdown = ReturnBreakdown(
                symbol=comp.symbol,
                fundamental=f_component,
                news=n_component,
                political=p_component,
                market_sector=m_component,
                historical_momentum=h_component,
                noise_luck=epsilon_component,
                raw_return=raw_return,
                clamped_return=clamped_return,
                was_clamped=was_clamped,
                old_price=old_price,
                new_price=new_price,
                explanation=narrative,
                step=self.day
            )

            daily_reports.append({
                "symbol": comp.symbol,
                "price": comp.price,
                "change": comp.change,
                "pct_change": comp.pct_change,
                "breakdown": comp.latest_breakdown
            })

        # 4. Advance Age of Active Events and prune expired
        surviving_events = []
        for active in self.active_events:
            active.age_steps += 1
            if active.age_steps < active.duration_steps:
                surviving_events.append(active)
        self.active_events = surviving_events

        return daily_reports

    def apply_event(self, event: MarketEvent) -> Dict[str, Any]:
        """
        Apply a market event immediately, adding it to active events with decay,
        updating affected stock prices, and recording in news feed.
        """
        # Register as active event for multi-step decay
        active_ev = ActiveEvent(event=event, age_steps=0, duration_steps=event.duration_days + 1)
        self.active_events.append(active_ev)

        # Immediate first-order price impact
        affected_symbols = []
        if event.affected_type == "company":
            if event.target in self.companies:
                affected_symbols.append(event.target)
        elif event.affected_type == "sector":
            for c in self.companies.values():
                if c.sector.lower() == event.target.lower():
                    affected_symbols.append(c.symbol)
        elif event.affected_type == "all":
            affected_symbols = list(self.companies.keys())

        for sym in affected_symbols:
            comp = self.companies[sym]
            comp.previous_price = comp.price
            impact_scale = comp.event_sensitivity * event.impact
            # If anticipated, initial shock is lower
            if event.anticipated:
                impact_scale *= 0.40
            clamped_impact = max(comp.lower_bound, min(comp.upper_bound, impact_scale))
            new_price = max(MIN_STOCK_PRICE, min(MAX_STOCK_PRICE, round(comp.price * (1.0 + clamped_impact), 2)))
            comp.price = new_price
            comp.price_history.append(comp.price)
            if len(comp.price_history) > PRICE_HISTORY_LENGTH:
                comp.price_history.pop(0)
            comp.high = max(comp.high, comp.price)
            comp.low = min(comp.low, comp.price)

            # Generate breakdown for this event shock
            comp.latest_breakdown = ReturnBreakdown(
                symbol=comp.symbol,
                fundamental=0.0,
                news=impact_scale,
                political=0.0,
                market_sector=0.0,
                historical_momentum=0.0,
                noise_luck=0.0,
                raw_return=impact_scale,
                clamped_return=clamped_impact,
                was_clamped=(impact_scale != clamped_impact),
                old_price=comp.previous_price,
                new_price=comp.price,
                explanation=f"Immediate market reaction to headline: {event.headline}",
                step=self.day
            )

        impact_sign = "+" if event.impact >= 0 else ""
        impact_str = f"{impact_sign}{round(event.impact * 100, 1)}%"

        news_item = {
            "day": self.day,
            "headline": event.headline,
            "explanation": event.explanation,
            "education": event.education,
            "category": event.category,
            "exchange_region": event.exchange_region,
            "direction": event.direction,
            "target": event.target,
            "impact_str": impact_str,
            "impact": event.impact,
            "affected_symbols": affected_symbols,
            "disclaimer": event.disclaimer
        }
        self.news_feed.insert(0, news_item)
        if len(self.news_feed) > 40:
            self.news_feed.pop()

        return news_item

    def trigger_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        ev = self.events_catalog.get(event_id)
        if ev:
            return self.apply_event(ev)
        return None

    def trigger_random_event(self) -> Optional[Dict[str, Any]]:
        if not self.events_catalog:
            return None
        ev = self.rng.choice(list(self.events_catalog.values()))
        return self.apply_event(ev)

    def get_company(self, symbol: str) -> Optional[Company]:
        if not symbol:
            return None
        return self.companies.get(symbol.upper())

    def get_all_companies(self) -> List[Company]:
        return list(self.companies.values())

    def get_breakdown(self, symbol: str) -> Optional[ReturnBreakdown]:
        comp = self.get_company(symbol)
        if comp:
            return comp.latest_breakdown
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "day": self.day,
            "companies": {sym: comp.to_dict() for sym, comp in self.companies.items()},
            "news_feed": self.news_feed,
            "macro_policy": self.macro_policy
        }

    def load_state(self, state: Dict[str, Any]):
        self.day = int(state.get("day", 1))
        comp_data = state.get("companies", {})
        for sym, c_dict in comp_data.items():
            self.companies[sym] = Company.from_dict(c_dict)
        self.news_feed = state.get("news_feed", [])
        self.macro_policy = state.get("macro_policy", {
            "active_policy": "none",
            "policy_magnitude": 0.0,
            "interest_rate_delta": 0.0,
            "infrastructure_spend": 0.0
        })
