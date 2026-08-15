class BigPlayersStrategy:
    def calculate_breakout_status(self, row: dict) -> str:
        low915 = float(row.get("low915", 0))
        price = float(row.get("Price", 0))
        today_low = float(row.get("todayLow", 0))
        if low915 <= 0 or price <= 0: return "Waiting"
        if price <= low915: return "Waiting"
        if today_low and today_low < low915: return "Active"
        return "Waiting"
    
    def calculate_support_price(self, row: dict) -> float | None:
        low = row.get("low915")
        return round(float(low), 2) if low else None
