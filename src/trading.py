"""
MarketQuest - Trading Engine & Portfolio Accounting
Authoritative trade validation and portfolio ledger.
Prevents invalid orders, tracks average cost basis, and computes exact realized/unrealized P&L.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from config import INITIAL_CASH

@dataclass
class Position:
    symbol: str
    shares: int = 0
    total_cost_basis: float = 0.0

    @property
    def avg_cost(self) -> float:
        if self.shares <= 0:
            return 0.0
        return self.total_cost_basis / self.shares

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "shares": self.shares,
            "total_cost_basis": round(self.total_cost_basis, 2)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Position':
        return cls(
            symbol=data["symbol"],
            shares=int(data["shares"]),
            total_cost_basis=float(data.get("total_cost_basis", 0.0))
        )


@dataclass
class TradeRecord:
    day: int
    symbol: str
    action: str  # "BUY" or "SELL"
    shares: int
    price: float
    total: float
    realized_pnl: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "day": self.day,
            "symbol": self.symbol,
            "action": self.action,
            "shares": self.shares,
            "price": round(self.price, 2),
            "total": round(self.total, 2),
            "realized_pnl": round(self.realized_pnl, 2)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradeRecord':
        return cls(
            day=int(data["day"]),
            symbol=data["symbol"],
            action=data["action"],
            shares=int(data["shares"]),
            price=float(data["price"]),
            total=float(data["total"]),
            realized_pnl=float(data.get("realized_pnl", 0.0))
        )


class Portfolio:
    def __init__(self, starting_cash: float = INITIAL_CASH):
        self.starting_cash: float = round(float(starting_cash), 2)
        self.cash: float = round(float(starting_cash), 2)
        self.positions: Dict[str, Position] = {}
        self.realized_pnl: float = 0.0
        self.trade_history: List[TradeRecord] = []

    def get_position(self, symbol: str) -> Position:
        symbol = symbol.upper()
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol=symbol)
        return self.positions[symbol]

    def get_shares_owned(self, symbol: str) -> int:
        pos = self.positions.get(symbol.upper())
        return pos.shares if pos else 0

    def validate_buy(self, symbol: str, shares: Any, current_price: float, authorized: bool = True) -> Tuple[bool, str]:
        """Validate if a buy order can be executed."""
        if not authorized:
            return False, "Order rejected: You must be present on an authorized Stock Exchange trading floor (BSE, NYSE, TSE, LSE) to execute equity orders."
        if not isinstance(shares, int) or shares <= 0:
            return False, "Order quantity must be a positive whole integer."
        if current_price <= 0:
            return False, "Invalid share price."
        
        cost = round(shares * current_price, 2)
        if self.cash < cost:
            return False, f"Insufficient cash! Cost: ${cost:,.2f}, Available: ${self.cash:,.2f}."
        
        return True, "Valid order."

    def buy(self, symbol: str, shares: int, current_price: float, day: int = 1, authorized: bool = True) -> Tuple[bool, str]:
        """Execute a buy order."""
        valid, msg = self.validate_buy(symbol, shares, current_price, authorized=authorized)
        if not valid:
            return False, msg

        symbol = symbol.upper()
        cost = round(shares * current_price, 2)
        self.cash = round(self.cash - cost, 2)

        pos = self.get_position(symbol)
        pos.shares += shares
        pos.total_cost_basis = round(pos.total_cost_basis + cost, 2)

        record = TradeRecord(
            day=day,
            symbol=symbol,
            action="BUY",
            shares=shares,
            price=round(current_price, 2),
            total=cost,
            realized_pnl=0.0
        )
        self.trade_history.append(record)
        return True, f"Bought {shares} shares of {symbol} for ${cost:,.2f}."

    def validate_sell(self, symbol: str, shares: Any, current_price: float, authorized: bool = True) -> Tuple[bool, str]:
        """Validate if a sell order can be executed."""
        if not authorized:
            return False, "Order rejected: You must be present on an authorized Stock Exchange trading floor (BSE, NYSE, TSE, LSE) to execute equity orders."
        if not isinstance(shares, int) or shares <= 0:
            return False, "Order quantity must be a positive whole integer."
        if current_price <= 0:
            return False, "Invalid share price."

        symbol = symbol.upper()
        owned = self.get_shares_owned(symbol)
        if owned < shares:
            return False, f"Cannot sell {shares} shares. You only own {owned} shares of {symbol}."

        return True, "Valid order."

    def sell(self, symbol: str, shares: int, current_price: float, day: int = 1, authorized: bool = True) -> Tuple[bool, str, float]:
        """Execute a sell order and calculate realized P&L."""
        valid, msg = self.validate_sell(symbol, shares, current_price, authorized=authorized)
        if not valid:
            return False, msg, 0.0

        symbol = symbol.upper()
        pos = self.get_position(symbol)
        avg_cost = pos.avg_cost
        cost_basis_sold = round(avg_cost * shares, 2)
        proceeds = round(shares * current_price, 2)
        trade_pnl = round(proceeds - cost_basis_sold, 2)

        self.cash = round(self.cash + proceeds, 2)
        self.realized_pnl = round(self.realized_pnl + trade_pnl, 2)

        pos.shares -= shares
        pos.total_cost_basis = round(max(0.0, pos.total_cost_basis - cost_basis_sold), 2)
        if pos.shares == 0:
            pos.total_cost_basis = 0.0

        record = TradeRecord(
            day=day,
            symbol=symbol,
            action="SELL",
            shares=shares,
            price=round(current_price, 2),
            total=proceeds,
            realized_pnl=trade_pnl
        )
        self.trade_history.append(record)

        sign = "+" if trade_pnl >= 0 else "-"
        msg = f"Sold {shares} shares of {symbol} for ${proceeds:,.2f} (Realized P&L: {sign}${abs(trade_pnl):,.2f})."
        return True, msg, trade_pnl

    def get_market_value(self, market: Any) -> float:
        """Total current market value of all active holdings."""
        total = 0.0
        for sym, pos in self.positions.items():
            if pos.shares > 0:
                comp = market.get_company(sym)
                price = comp.price if comp else 0.0
                total += pos.shares * price
        return round(total, 2)

    def get_total_cost_basis(self) -> float:
        """Sum of remaining cost basis across active holdings."""
        total = sum(pos.total_cost_basis for pos in self.positions.values() if pos.shares > 0)
        return round(total, 2)

    def get_unrealized_pnl(self, market: Any) -> float:
        """Market value minus active cost basis."""
        return round(self.get_market_value(market) - self.get_total_cost_basis(), 2)

    def get_total_value(self, market: Any) -> float:
        """Cash + market value of holdings."""
        return round(self.cash + self.get_market_value(market), 2)

    def get_total_return(self, market: Any) -> float:
        """Total portfolio value - starting cash."""
        return round(self.get_total_value(market) - self.starting_cash, 2)

    def get_total_return_pct(self, market: Any) -> float:
        if self.starting_cash <= 0:
            return 0.0
        return round((self.get_total_return(market) / self.starting_cash) * 100.0, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "starting_cash": self.starting_cash,
            "cash": self.cash,
            "realized_pnl": self.realized_pnl,
            "positions": {sym: pos.to_dict() for sym, pos in self.positions.items() if pos.shares > 0},
            "trade_history": [t.to_dict() for t in self.trade_history]
        }

    def load_state(self, data: Dict[str, Any]):
        self.starting_cash = float(data.get("starting_cash", INITIAL_CASH))
        self.cash = float(data.get("cash", INITIAL_CASH))
        self.realized_pnl = float(data.get("realized_pnl", 0.0))
        self.positions = {}
        for sym, p_dict in data.get("positions", {}).items():
            self.positions[sym] = Position.from_dict(p_dict)
        self.trade_history = [TradeRecord.from_dict(t) for t in data.get("trade_history", [])]
