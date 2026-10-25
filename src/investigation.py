"""
MarketQuest - Clue Investigation & Investment Thesis System
Tracks field intelligence, corporate espionage clues, department interviews,
and synthesizes fundamental investment theses with confidence ratings.
Also manages the Player Level 1-10 progression engine.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

# Player Level Progression (Level 1 to 10)
LEVEL_THRESHOLDS = [
    (1, 0, "Rookie Investor"),
    (2, 100, "Market Observer"),
    (3, 250, "Equity Analyst"),
    (4, 500, "Floor Trader"),
    (5, 900, "Portfolio Strategist"),
    (6, 1400, "Senior Arbitrageur"),
    (7, 2000, "Fund Manager"),
    (8, 2800, "Managing Director"),
    (9, 3800, "Market Maker"),
    (10, 5000, "Financial Titan")
]


@dataclass
class Clue:
    id: str
    company_symbol: str   # "APEX", "TITN", "CHAI", "AURA", "MACRO"
    category: str         # "R&D", "Supply Chain", "Financials", "Executive", "Policy"
    title: str
    description: str
    source: str           # NPC or object inspected
    impact: str           # "BULLISH", "BEARISH", "NEUTRAL"
    confidence_pts: int = 34

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "company_symbol": self.company_symbol,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "source": self.source,
            "impact": self.impact,
            "confidence_pts": self.confidence_pts
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Clue':
        return cls(
            id=data["id"],
            company_symbol=data["company_symbol"],
            category=data["category"],
            title=data["title"],
            description=data["description"],
            source=data["source"],
            impact=data["impact"],
            confidence_pts=int(data.get("confidence_pts", 34))
        )


ALL_CLUES: Dict[str, Clue] = {
    # -------------------------------------------------------------
    # APEX DYNAMICS (APEX)
    # -------------------------------------------------------------
    "apex_rd_chip": Clue(
        id="apex_rd_chip",
        company_symbol="APEX",
        category="R&D",
        title="Neural Drive V4 Silicon Telemetry",
        description="Internal lab bench data indicates 42% lower thermal dissipation in autonomous vision chips, paving the way for commercial robotaxi certification.",
        source="Elena Rostova, AI Architect",
        impact="BULLISH",
        confidence_pts=35
    ),
    "apex_battery_yield": Clue(
        id="apex_battery_yield",
        company_symbol="APEX",
        category="Supply Chain",
        title="Gigafactory Solid-State Pack Yield",
        description="Prototype manufacturing logs reveal solid-state electrolyte pack yields rose to 88%, dropping pack cost below $70/kWh.",
        source="Mark Chen, Powertrain Engineer",
        impact="BULLISH",
        confidence_pts=35
    ),
    "apex_ceo_vision": Clue(
        id="apex_ceo_vision",
        company_symbol="APEX",
        category="Executive",
        title="CEO Vance Multi-Planetary Scaling Memo",
        description="Executive whiteboard notes outlining ambitious timeline to deploy 50,000 autonomous delivery pods before end of fiscal quarter.",
        source="Sterling Vance, CEO",
        impact="BULLISH",
        confidence_pts=30
    ),

    # -------------------------------------------------------------
    # TITAN CAPITAL (TITN)
    # -------------------------------------------------------------
    "titn_ma_deal": Clue(
        id="titn_ma_deal",
        company_symbol="TITN",
        category="Financials",
        title="Confidential Mega-Merger Syndicate Memo",
        description="Draft advisory agreement revealing Titan is lead underwriter on a $24B cross-border telecommunications acquisition, yielding $180M advisory fee.",
        source="Evelyn Sterling, M&A Director",
        impact="BULLISH",
        confidence_pts=35
    ),
    "titn_credit_risk": Clue(
        id="titn_credit_risk",
        company_symbol="TITN",
        category="Executive",
        title="Commercial Real Estate Loan Stress-Test",
        description="Internal risk dashboard indicates rising non-performing debt provisions across metropolitan office portfolios, mildly dampening return on equity.",
        source="Marcus Vance, Senior Underwriter",
        impact="BEARISH",
        confidence_pts=35
    ),
    "titn_nim_margin": Clue(
        id="titn_nim_margin",
        company_symbol="TITN",
        category="Financials",
        title="Treasury Net Interest Margin Audit",
        description="Central bank rate stability allows Titan's institutional repo desk to lock in a widened 280 bps spread on short-dated liquidity.",
        source="Chloe Bennett, Risk Auditor",
        impact="BULLISH",
        confidence_pts=30
    ),

    # -------------------------------------------------------------
    # MONSOON GLOBAL GOODS (CHAI)
    # -------------------------------------------------------------
    "chai_harvest_record": Clue(
        id="chai_harvest_record",
        company_symbol="CHAI",
        category="Supply Chain",
        title="Assam & Darjeeling Bumper Harvest Yield",
        description="Estate harvest tallies show specialty orthodox tea production exceeded projections by 18%, locking in lower input costs across 200 blending hubs.",
        source="Anand Singhania, Master Blender",
        impact="BULLISH",
        confidence_pts=35
    ),
    "chai_shipping_reroute": Clue(
        id="chai_shipping_reroute",
        company_symbol="CHAI",
        category="Supply Chain",
        title="Global Freight Rerouting Long-Term Charter",
        description="Port of Mumbai logistics manifest confirms 3-year fixed-rate maritime freight contracts, successfully insulating Monsoon from spot tanker surcharges.",
        source="Meera Sen, Supply Chain Director",
        impact="BULLISH",
        confidence_pts=35
    ),
    "chai_se_asia_retail": Clue(
        id="chai_se_asia_retail",
        company_symbol="CHAI",
        category="Executive",
        title="ASEAN Supermarket Exclusivity Contract",
        description="Signed distribution pact with 1,200 retail outlets in Singapore, Jakarta, and Kuala Lumpur, accelerating international revenue by 24%.",
        source="Rajiv Patel, Commodities Buyer",
        impact="BULLISH",
        confidence_pts=30
    ),

    # -------------------------------------------------------------
    # AURUM CLEAN ENERGY (AURA) & MACRO POLICY
    # -------------------------------------------------------------
    "aura_solar_subsidies": Clue(
        id="aura_solar_subsidies",
        company_symbol="AURA",
        category="Policy",
        title="National Solar Grid Incentive Tariff",
        description="Legislative draft confirms multi-billion dollar capex production-linked subsidies for domestic solar wafer manufacturing facilities.",
        source="Parliament Liaison Dossier",
        impact="BULLISH",
        confidence_pts=40
    ),
    "aura_perovskite_efficiency": Clue(
        id="aura_perovskite_efficiency",
        company_symbol="AURA",
        category="R&D",
        title="Tandem Perovskite 29.4% Solar Efficiency Benchmark",
        description="Laboratory bench test certified perovskite-silicon tandem cells reached 29.4% sunlight-to-power conversion, setting a commercial world record.",
        source="Dr. Vikram Joshi, Chief Materials Scientist",
        impact="BULLISH",
        confidence_pts=35
    ),
    "aura_battery_margin": Clue(
        id="aura_battery_margin",
        company_symbol="AURA",
        category="Supply Chain",
        title="AuraGrid Megawatt Storage Levelized Cost Audit",
        description="Lithium-iron battery pack integration costs dropped to $68/kWh, securing a 32% gross profit margin on utility-scale microgrid tenders.",
        source="Radhika Roy, Grid Operations VP",
        impact="BULLISH",
        confidence_pts=35
    ),

    # -------------------------------------------------------------
    # NOVA CLOUD SYSTEMS (NOVA)
    # -------------------------------------------------------------
    "nova_quantum_mesh": Clue(
        id="nova_quantum_mesh",
        company_symbol="NOVA",
        category="R&D",
        title="Quantum Cloud Mesh & Sovereign Database Latency",
        description="Internal telemetry proves distributed zero-trust cloud nodes achieve sub-millisecond failover across international financial datacenters.",
        source="Maya Lin, Chief Technology Officer",
        impact="BULLISH",
        confidence_pts=50
    ),
    "nova_gov_contract": Clue(
        id="nova_gov_contract",
        company_symbol="NOVA",
        category="Financials",
        title="Federal Sovereign Cloud Multi-Year Agreement",
        description="Confidential procurement contract guaranteeing $620M in recurrent annual cloud subscription revenue with 88% gross margins.",
        source="Samuel Ross, Enterprise Sales Director",
        impact="BULLISH",
        confidence_pts=50
    ),

    # -------------------------------------------------------------
    # MEDIX SYNTHETICS (MEDX)
    # -------------------------------------------------------------
    "medx_phase3_oncology": Clue(
        id="medx_phase3_oncology",
        company_symbol="MEDX",
        category="R&D",
        title="OncoSyn-4 Phase-3 Complete Tumor Remission Data",
        description="Double-blind clinical data showed 84% objective response rate with zero dose-limiting toxicity in advanced solid tumor cohorts.",
        source="Dr. Aris Thorne, Chief Genomics Scientist",
        impact="BULLISH",
        confidence_pts=50
    ),
    "medx_fda_expedited": Clue(
        id="medx_fda_expedited",
        company_symbol="MEDX",
        category="Executive",
        title="Global Health Authority Expedited Fast-Track Review",
        description="Regulatory authorities granted Priority Review and Breakthrough Therapy designation, accelerating commercial launch by 14 months.",
        source="Kavita Rao, Clinical Trials Director",
        impact="BULLISH",
        confidence_pts=50
    ),

    "macro_fed_rates": Clue(
        id="macro_fed_rates",
        company_symbol="MACRO",
        category="Policy",
        title="Federal Reserve Liquidity Policy Stance",
        description="Briefing folder detailing central bank trajectory toward rate stabilization, providing tailwinds for equity asset multiples.",
        source="White House Economic Adviser",
        impact="BULLISH",
        confidence_pts=50
    ),

    "bse_rj_wisdom": Clue(
        id="bse_rj_wisdom",
        company_symbol="BSE",
        category="Education",
        title="Big Bull's Compounding Rule: Value, Patience, and Moats",
        description="Investing masterclass memo: 'Markets are never wrong; human emotions are. High return on capital, pricing power, and visionary integrity compound over decades.'",
        source="Rakesh Jhunjhunwala (Historical Mentor)",
        impact="BULLISH",
        confidence_pts=50
    ),
    "bse_1992_case_study": Clue(
        id="bse_1992_case_study",
        company_symbol="BSE",
        category="History",
        title="1992 Scam Case Study: Liquidity Distortion vs Real Cash Flows",
        description="Forensic investigation exhibit detailing how uncollateralized Bank Receipts (BRs) created an artificial speculative mania, leading to the creation of SEBI, electronic BOLT matching, and dematerialized settlement.",
        source="Investigator K. V. Sharma, History Curator",
        impact="BEARISH",
        confidence_pts=50
    ),
    "bse_fundamental_model": Clue(
        id="bse_fundamental_model",
        company_symbol="BSE",
        category="Research",
        title="Institutional Equity Research & DCF Valuation Model",
        description="Audited financial model demonstrating discounted free cash flows, working capital cycles, and debt-service coverage for Dalal Street blue chips.",
        source="BSE Equity Research Lab",
        impact="BULLISH",
        confidence_pts=50
    ),
    "bse_secret_ledger": Clue(
        id="bse_secret_ledger",
        company_symbol="BSE",
        category="Archive",
        title="Historic Dalal Street Floor Runner Arbitrage Logbook",
        description="Rare archival ledger recording century-old triangular arbitrage spreads and settlement protocols discovered in the restricted vault.",
        source="Dalal Street Archival Vault",
        impact="BULLISH",
        confidence_pts=50
    )
}


class InvestigationManager:
    """Manages player evidence collection, thesis generation, and XP levels."""
    def __init__(self):
        self.unlocked_clues: Dict[str, Clue] = {}
        self.selected_company: str = "APEX"
        self.theses: List['InvestmentThesis'] = []

    def unlock_clue(self, clue_id: str) -> Optional[Tuple[Clue, bool]]:
        """
        Unlock a clue. Returns (Clue, is_new).
        Returns None if clue_id is invalid.
        """
        if clue_id not in ALL_CLUES:
            return None

        is_new = clue_id not in self.unlocked_clues
        clue = ALL_CLUES[clue_id]
        if is_new:
            self.unlocked_clues[clue_id] = clue
        return clue, is_new

    def get_clues_for_company(self, symbol: str) -> List[Clue]:
        return [c for c in self.unlocked_clues.values() if c.company_symbol == symbol]

    def get_total_clues_for_company(self, symbol: str) -> int:
        return sum(1 for c in ALL_CLUES.values() if c.company_symbol == symbol)

    def get_confidence_pct(self, symbol: str) -> int:
        clues = self.get_clues_for_company(symbol)
        total_pts = sum(c.confidence_pts for c in clues)
        return min(100, total_pts)

    def get_thesis_rating(self, symbol: str) -> Tuple[str, str]:
        """
        Returns (RatingLabel, ActionableThesisSummary).
        """
        pct = self.get_confidence_pct(symbol)
        clues = self.get_clues_for_company(symbol)

        if pct < 35:
            return "LOW CONFIDENCE", "Preliminary intelligence. Gather more evidence from company headquarters to build a reliable thesis."
        elif pct < 75:
            bullish_count = sum(1 for c in clues if c.impact == "BULLISH")
            bearish_count = sum(1 for c in clues if c.impact == "BEARISH")
            bias = "Cautiously Bullish" if bullish_count >= bearish_count else "Mixed / Defensive"
            return "MODERATE CONFIDENCE", f"{bias}: Substantial data gathered. Catalysts identified, but monitor regulatory headwinds and costs."
        else:
            return "HIGH CONVICTION", "Institutional Thesis: Multi-department alignment across R&D, supply chain, and executive leadership indicates high fundamental conviction."

    @staticmethod
    def get_level_info(xp: int) -> Tuple[int, str, int, int, float]:
        """
        Returns (current_level, title, current_level_xp, next_level_xp, progress_ratio).
        """
        lvl = 1
        title = LEVEL_THRESHOLDS[0][2]
        cur_min = 0
        next_threshold = LEVEL_THRESHOLDS[1][1]

        for i, (l_num, thresh, l_title) in enumerate(LEVEL_THRESHOLDS):
            if xp >= thresh:
                lvl = l_num
                title = l_title
                cur_min = thresh
                if i + 1 < len(LEVEL_THRESHOLDS):
                    next_threshold = LEVEL_THRESHOLDS[i + 1][1]
                else:
                    next_threshold = thresh  # max level reached

        if next_threshold > cur_min:
            ratio = min(1.0, max(0.0, (xp - cur_min) / (next_threshold - cur_min)))
        else:
            ratio = 1.0

        return lvl, title, cur_min, next_threshold, ratio

    def to_dict(self) -> Dict[str, Any]:
        return {
            "unlocked_clues": list(self.unlocked_clues.keys()),
            "selected_company": self.selected_company,
            "recorded_theses": [t.to_dict() for t in self.theses]
        }

    def load_state(self, data: Dict[str, Any]):
        self.unlocked_clues = {}
        for c_id in data.get("unlocked_clues", []):
            if c_id in ALL_CLUES:
                self.unlocked_clues[c_id] = ALL_CLUES[c_id]
        self.selected_company = data.get("selected_company", "APEX")
        self.theses = [InvestmentThesis.from_dict(t) for t in data.get("recorded_theses", [])]

    def record_thesis(self, thesis: 'InvestmentThesis'):
        self.theses.insert(0, thesis)
        if len(self.theses) > 20:
            self.theses.pop()

    def get_theses_for_company(self, symbol: str) -> List['InvestmentThesis']:
        return [t for t in self.theses if t.company_symbol == symbol]


@dataclass
class InvestmentThesis:
    company_symbol: str
    rationale: str
    evidence_clues: List[str]
    catalysts: str
    risks: str
    confidence_level: str
    holding_period: str
    position_size_pct: float
    entry_price: float
    entry_step: int
    resolution_price: Optional[float] = None
    resolved: bool = False
    outcome_notes: str = ""

    def evaluate_outcome(self, current_price: float) -> str:
        pct = ((current_price - self.entry_price) / max(0.01, self.entry_price)) * 100.0
        self.resolution_price = current_price
        self.resolved = True
        if pct > 0.5:
            self.outcome_notes = f"Thesis Validated: +{round(pct, 2)}% gain. Catalysts materialized as anticipated."
        elif pct < -0.5:
            self.outcome_notes = f"Thesis Challenged: {round(pct, 2)}% loss. Unforeseen headwinds or stochastic variance offset thesis."
        else:
            self.outcome_notes = f"Neutral Outcome: Price remained flat ({round(pct, 2)}%) over holding period."
        return self.outcome_notes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "company_symbol": self.company_symbol,
            "rationale": self.rationale,
            "evidence_clues": self.evidence_clues,
            "catalysts": self.catalysts,
            "risks": self.risks,
            "confidence_level": self.confidence_level,
            "holding_period": self.holding_period,
            "position_size_pct": self.position_size_pct,
            "entry_price": self.entry_price,
            "entry_step": self.entry_step,
            "resolution_price": self.resolution_price,
            "resolved": self.resolved,
            "outcome_notes": self.outcome_notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InvestmentThesis':
        return cls(
            company_symbol=data["company_symbol"],
            rationale=data.get("rationale", ""),
            evidence_clues=data.get("evidence_clues", []),
            catalysts=data.get("catalysts", ""),
            risks=data.get("risks", ""),
            confidence_level=data.get("confidence_level", "Moderate"),
            holding_period=data.get("holding_period", "1-2 Weeks"),
            position_size_pct=float(data.get("position_size_pct", 25.0)),
            entry_price=float(data.get("entry_price", 100.0)),
            entry_step=int(data.get("entry_step", 1)),
            resolution_price=data.get("resolution_price"),
            resolved=bool(data.get("resolved", False)),
            outcome_notes=data.get("outcome_notes", "")
        )

