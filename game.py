from typing import Dict, Any, Tuple

# Schema definition for events
REQUIRED_FIELDS = ["event", "speed", "combo", "vehicle_type", "total_score", "distance_survived"]

def validate_event_data(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validates the incoming gameplay event data schema."""
    if not isinstance(data, dict):
        return False, "Data must be a JSON object"
        
    for field in REQUIRED_FIELDS:
        if field not in data:
            return False, f"Missing required field: {field}"
            
    # Check types
    if not isinstance(data["event"], str):
        return False, "event field must be a string"
    if not isinstance(data["speed"], (int, float)):
        return False, "speed field must be a number"
    if not isinstance(data["combo"], (int, float)):
        return False, "combo field must be a number"
    if not isinstance(data["vehicle_type"], str):
        return False, "vehicle_type field must be a string"
    if not isinstance(data["total_score"], (int, float)):
        return False, "total_score field must be a number"
    if not isinstance(data["distance_survived"], (int, float)):
        return False, "distance_survived field must be a number"
        
    return True, ""

def compute_server_bonus(event_type: str, combo: int) -> int:
    """Computes event score bonuses on the server side to verify client scoring."""
    base_bonuses = {
        "near_miss": 10,
        "overtake": 5,
        "multi_overtake": 25,
        "recovery": 20,
        "traffic_weave": 30,
        "crash": 0,
        "game_start": 0
    }
    bonus = base_bonuses.get(event_type, 0)
    # Apply combo multiplier
    multiplier = max(1, combo)
    return bonus * multiplier
