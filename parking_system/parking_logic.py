import datetime

class ParkingLotManager:
    def __init__(self):
        # הגדרת התעריף השעתי - 20 ש"ח כפי שסוכם בתיעוד האג'נטי
        self.hourly_fee = 20
        self.active_parkings = {}

    def register_entry(self, vehicle_id):
        """רישום כניסת רכב לפי מספר לוחית רישוי"""
        self.active_parkings[vehicle_id] = datetime.datetime.now()
        return f"Vehicle {vehicle_id} entered at {self.active_parkings[vehicle_id]}"

    def calculate_payment(self, vehicle_id):
        """חישוב תשלום לפי זמן שהייה בפועל"""
        if vehicle_id not in self.active_parkings:
            return "Vehicle not found."
        
        entry_time = self.active_parkings.pop(vehicle_id)
        duration = datetime.datetime.now() - entry_time
        hours = max(1, duration.total_seconds() / 3600)
        return hours * self.hourly_fee