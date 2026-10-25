"""
MarketQuest - Global Market Clock & Exchange Schedules
Handles IANA time zones (Asia/Kolkata and America/New_York) with Daylight Saving Time.
Supports both Simulation Mode (with time acceleration & rest) and Real-Time Mode.
"""

import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Tuple, Optional, Any, List

# IANA Time Zones
TZ_MUMBAI = ZoneInfo("Asia/Kolkata")
TZ_NEW_YORK = ZoneInfo("America/New_York")
TZ_TOKYO = ZoneInfo("Asia/Tokyo")
TZ_LONDON = ZoneInfo("Europe/London")
TZ_UTC = ZoneInfo("UTC")

# Exchange IDs
EXCHANGE_BSE = "BSE"
EXCHANGE_NYSE = "NYSE"
EXCHANGE_TSE = "TSE"
EXCHANGE_LSE = "LSE"

# Mode Constants
MODE_SIMULATION = "simulation"
MODE_REALTIME = "realtime"

# Exchange Trading Sessions (Local time: 24h format)
# BSE: 09:15 - 15:30 IST (Pre-open: 09:00 - 09:15)
# NYSE: 09:30 - 16:00 EST/EDT (Pre-open: 09:00 - 09:30)
# TSE: 09:00 - 15:30 JST (Pre-open: 08:30 - 09:00)
# LSE: 08:00 - 16:30 GMT/BST (Pre-open: 07:50 - 08:00)
EXCHANGE_HOURS = {
    EXCHANGE_BSE: {
        "tz": TZ_MUMBAI,
        "name": "Bombay Stock Exchange (BSE)",
        "city": "Mumbai",
        "currency": "INR",
        "pre_open": datetime.time(9, 0),
        "open": datetime.time(9, 15),
        "close": datetime.time(15, 30),
    },
    EXCHANGE_NYSE: {
        "tz": TZ_NEW_YORK,
        "name": "New York Stock Exchange (NYSE)",
        "city": "New York",
        "currency": "USD",
        "pre_open": datetime.time(9, 0),
        "open": datetime.time(9, 30),
        "close": datetime.time(16, 0),
    },
    EXCHANGE_TSE: {
        "tz": TZ_TOKYO,
        "name": "Tokyo Stock Exchange (TSE)",
        "city": "Tokyo",
        "currency": "JPY",
        "pre_open": datetime.time(8, 30),
        "open": datetime.time(9, 0),
        "close": datetime.time(15, 30),
    },
    EXCHANGE_LSE: {
        "tz": TZ_LONDON,
        "name": "London Stock Exchange (LSE)",
        "city": "London",
        "currency": "GBP",
        "pre_open": datetime.time(7, 50),
        "open": datetime.time(8, 0),
        "close": datetime.time(16, 30),
    }
}

# Simplified/configurable holiday calendar (Month, Day)
EXCHANGE_HOLIDAYS = {
    EXCHANGE_BSE: [
        (1, 26),   # Republic Day
        (8, 15),   # Independence Day
        (10, 2),   # Gandhi Jayanti
        (11, 1),   # Diwali Laxmi Pujan (Simplified)
        (12, 25),  # Christmas
    ],
    EXCHANGE_NYSE: [
        (1, 1),    # New Year's Day
        (7, 4),    # Independence Day
        (11, 26),  # Thanksgiving
        (12, 25),  # Christmas
    ],
    EXCHANGE_TSE: [
        (1, 1),    # New Year's Day
        (2, 11),   # National Foundation Day
        (5, 3),    # Constitution Memorial Day
        (11, 23),  # Labor Thanksgiving Day
    ],
    EXCHANGE_LSE: [
        (1, 1),    # New Year's Day
        (5, 4),    # Early May Bank Holiday
        (8, 31),   # Summer Bank Holiday
        (12, 25),  # Christmas
    ]
}


class MarketClock:
    def __init__(self, mode: str = MODE_SIMULATION, time_scale: float = 60.0):
        self.mode = mode
        # 1 real second = time_scale game seconds (default 60x -> 1 sec = 1 min)
        self.time_scale = time_scale
        
        # In simulation mode, start on a Monday at 09:00 AM UTC
        # Monday, October 26, 2026 09:00:00 UTC
        self.sim_time_utc = datetime.datetime(2026, 10, 26, 9, 0, 0, tzinfo=TZ_UTC)
        
        # Previous statuses to detect transition events
        self.prev_status: Dict[str, str] = {
            EXCHANGE_BSE: "UNKNOWN",
            EXCHANGE_NYSE: "UNKNOWN",
            EXCHANGE_TSE: "UNKNOWN",
            EXCHANGE_LSE: "UNKNOWN"
        }
        
        # Notifications queue
        self.pending_notifications: List[Dict[str, str]] = []

    def set_mode(self, mode: str):
        if mode in (MODE_SIMULATION, MODE_REALTIME):
            self.mode = mode

    def get_current_time(self, tz: ZoneInfo) -> datetime.datetime:
        """Get current time converted to target timezone."""
        if self.mode == MODE_REALTIME:
            return datetime.datetime.now(tz)
        else:
            return self.sim_time_utc.astimezone(tz)

    def get_local_time_for_location(self, location_id: str) -> datetime.datetime:
        """Get appropriate time for current game district."""
        if "dalal" in location_id or "bse" in location_id or "parliament" in location_id or "monsoon" in location_id:
            return self.get_current_time(TZ_MUMBAI)
        elif "kabutocho" in location_id or "tse" in location_id:
            return self.get_current_time(TZ_TOKYO)
        elif "london" in location_id or "paternoster" in location_id or "lse" in location_id:
            return self.get_current_time(TZ_LONDON)
        else:
            return self.get_current_time(TZ_NEW_YORK)

    def is_holiday(self, exchange_id: str, dt: datetime.datetime) -> bool:
        """Check if date is a simplified exchange holiday."""
        holidays = EXCHANGE_HOLIDAYS.get(exchange_id, [])
        return (dt.month, dt.day) in holidays

    def get_exchange_status(self, exchange_id: str) -> Dict[str, Any]:
        """Compute live exchange status, session state, and countdown to next event."""
        info = EXCHANGE_HOURS.get(exchange_id)
        if not info:
            return {"status": "CLOSED", "time_str": "--:--", "countdown": ""}

        cur_dt = self.get_current_time(info["tz"])
        weekday = cur_dt.weekday()  # 0=Monday, 6=Sunday
        is_weekend = weekday >= 5
        is_hol = self.is_holiday(exchange_id, cur_dt)

        cur_t = cur_dt.time()
        pre_t = info["pre_open"]
        open_t = info["open"]
        close_t = info["close"]

        status = "CLOSED"
        next_event = ""
        countdown_sec = 0

        if is_weekend or is_hol:
            status = "CLOSED"
            reason = "Weekend" if is_weekend else "Holiday"
            next_event = f"Closed ({reason})"
        else:
            if pre_t <= cur_t < open_t:
                status = "PRE-OPEN"
                # Target: open_t today
                target_dt = cur_dt.replace(hour=open_t.hour, minute=open_t.minute, second=0, microsecond=0)
                diff = target_dt - cur_dt
                countdown_sec = max(0, int(diff.total_seconds()))
                next_event = f"Opens in {countdown_sec // 60}m {countdown_sec % 60}s"
            elif open_t <= cur_t < close_t:
                status = "OPEN"
                # Target: close_t today
                target_dt = cur_dt.replace(hour=close_t.hour, minute=close_t.minute, second=0, microsecond=0)
                diff = target_dt - cur_dt
                countdown_sec = max(0, int(diff.total_seconds()))
                hrs = countdown_sec // 3600
                mins = (countdown_sec % 3600) // 60
                next_event = f"Closes in {hrs}h {mins}m"
            else:
                status = "CLOSED"
                next_event = "Closed until next session"

        return {
            "exchange": exchange_id,
            "name": info["name"],
            "city": info["city"],
            "tz_name": cur_dt.tzname() or "TZ",
            "current_time": cur_dt,
            "time_str": cur_dt.strftime("%H:%M:%S"),
            "date_str": cur_dt.strftime("%a, %d %b %Y"),
            "status": status,
            "next_event": next_event,
            "is_open": (status == "OPEN")
        }

    def update(self, dt: float):
        """Advance time in simulation mode and detect open/close transitions."""
        if self.mode == MODE_SIMULATION:
            delta_sec = dt * self.time_scale
            self.sim_time_utc += datetime.timedelta(seconds=delta_sec)

        # Check for status changes on all exchanges
        for ex_id in [EXCHANGE_BSE, EXCHANGE_NYSE, EXCHANGE_TSE, EXCHANGE_LSE]:
            curr_stat = self.get_exchange_status(ex_id)["status"]
            prev_stat = self.prev_status[ex_id]
            if prev_stat != "UNKNOWN" and curr_stat != prev_stat:
                # Trigger a transition notification!
                ex_names = {
                    EXCHANGE_BSE: "BSE (Mumbai)",
                    EXCHANGE_NYSE: "NYSE (New York)",
                    EXCHANGE_TSE: "TSE (Tokyo)",
                    EXCHANGE_LSE: "LSE (London)"
                }
                ex_name = ex_names.get(ex_id, ex_id)
                if curr_stat == "OPEN":
                    self.pending_notifications.append({
                        "title": f"🔔 {ex_name} is NOW OPEN!",
                        "text": f"Regular trading session has commenced on {ex_name}.",
                        "type": "exchange_open"
                    })
                elif curr_stat == "CLOSED":
                    self.pending_notifications.append({
                        "title": f"🔔 {ex_name} is NOW CLOSED!",
                        "text": f"Regular trading session has concluded on {ex_name}.",
                        "type": "exchange_close"
                    })
            self.prev_status[ex_id] = curr_stat

    def advance_time(self, minutes: int):
        """Manually advance simulation time (e.g., waiting or sleeping)."""
        if self.mode == MODE_SIMULATION:
            self.sim_time_utc += datetime.timedelta(minutes=minutes)

    def advance_to_next_market_open(self, exchange_id: str = EXCHANGE_NYSE) -> str:
        """Fast-forward simulation time until the target exchange opens."""
        if self.mode != MODE_SIMULATION:
            return "Fast-forward only available in Simulation Mode."

        info = EXCHANGE_HOURS.get(exchange_id, EXCHANGE_HOURS[EXCHANGE_NYSE])
        tz = info["tz"]
        cur_local = self.get_current_time(tz)
        
        # Step forward day by day until a weekday that isn't a holiday
        target_local = cur_local
        open_t = info["open"]

        # If currently before open today, target today's open
        if target_local.weekday() < 5 and not self.is_holiday(exchange_id, target_local) and target_local.time() < open_t:
            target_local = target_local.replace(hour=open_t.hour, minute=open_t.minute, second=0, microsecond=0)
        else:
            # Advance to next day's open
            while True:
                target_local += datetime.timedelta(days=1)
                if target_local.weekday() < 5 and not self.is_holiday(exchange_id, target_local):
                    target_local = target_local.replace(hour=open_t.hour, minute=open_t.minute, second=0, microsecond=0)
                    break

        self.sim_time_utc = target_local.astimezone(TZ_UTC)
        return f"Advanced time to {info['name']} opening at {target_local.strftime('%a %H:%M %Z')}."

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "time_scale": self.time_scale,
            "sim_time_iso": self.sim_time_utc.isoformat()
        }

    def load_state(self, data: Dict[str, Any]):
        self.mode = data.get("mode", MODE_SIMULATION)
        self.time_scale = float(data.get("time_scale", 60.0))
        iso_str = data.get("sim_time_iso")
        if iso_str:
            try:
                self.sim_time_utc = datetime.datetime.fromisoformat(iso_str)
            except Exception:
                pass
