import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class NarrativeEngine:
    def __init__(self, window_seconds: float = 15.0):
        self.window_seconds = window_seconds
        self.event_history: List[Dict[str, Any]] = []
        
        # State tracking
        self.last_state = "CALM_CRUISING"
        self.consecutive_state_count = 0
        self.last_spoken_state = None

    def reset(self):
        """Resets the history and state tracking."""
        self.event_history.clear()
        self.last_state = "CALM_CRUISING"
        self.consecutive_state_count = 0
        self.last_spoken_state = None

    def evaluate(self, new_events: List[Dict[str, Any]], current_time: float, current_speed: float, current_combo: int) -> Dict[str, Any]:
        """
        Processes new events, updates history, prunes old events,
        determines the current narrative state and whether to generate commentary.
        """
        # Append new events
        for ev in new_events:
            # Ensure it has a timestamp
            if "timestamp" not in ev:
                ev["timestamp"] = current_time
            self.event_history.append(ev)

        # Prune old events outside the 15s window
        self.event_history = [
            e for e in self.event_history
            if current_time - e.get("timestamp", 0) <= self.window_seconds
        ]

        # Calculate stats
        overtakes = 0
        near_misses = 0
        lane_changes = 0
        combo_peak = current_combo
        speeds = []

        last_danger_time = None

        for e in self.event_history:
            evt_type = e.get("event")
            if evt_type in ("overtake", "multi_overtake"):
                overtakes += 1
            if evt_type in ("near_miss", "recovery"):
                near_misses += 1
                evt_time = e.get("timestamp", 0)
                if last_danger_time is None or evt_time > last_danger_time:
                    last_danger_time = evt_time
            if evt_type == "traffic_weave":
                lane_changes += 1
            
            combo_peak = max(combo_peak, e.get("combo", 0))
            if "speed" in e:
                speeds.append(e["speed"])

        # Determine average speed
        if speeds:
            avg_speed = sum(speeds) / len(speeds)
        else:
            avg_speed = current_speed

        # Calculate clean driving seconds
        if last_danger_time is not None:
            clean_driving_seconds = current_time - last_danger_time
        else:
            clean_driving_seconds = current_time

        total_events = len(self.event_history)

        # Priority-ordered rule engine for narrative state
        state = "CALM_CRUISING"

        if near_misses >= 3 and total_events >= 6:
            state = "TRAFFIC_CHAOS"
        elif near_misses >= 2 and avg_speed > 150:
            state = "HIGH_RISK_DRIVING"
        elif combo_peak >= 8:
            state = "CLUTCH_PERFORMANCE"
        elif overtakes >= 5:
            state = "AGGRESSIVE_DRIVING"
        elif overtakes >= 3 and near_misses >= 1:
            state = "BUILDING_MOMENTUM"
        elif avg_speed > 180 and clean_driving_seconds > 5:
            state = "RECORD_PACE"
        elif self.last_state in ("HIGH_RISK_DRIVING", "TRAFFIC_CHAOS") and near_misses == 0:
            state = "RECOVERY_PHASE"
        elif clean_driving_seconds > 10 and overtakes >= 2:
            state = "TOTAL_CONTROL"

        # Update consecutive state counts
        if state == self.last_state:
            self.consecutive_state_count += 1
        else:
            self.last_state = state
            self.consecutive_state_count = 1

        # Determine if we should speak (anti-repetition logic)
        should_speak = True
        
        # Don't speak CALM_CRUISING consecutively
        if state == "CALM_CRUISING" and self.consecutive_state_count > 1:
            should_speak = False
        # Limit repeat spoken state
        elif state == self.last_spoken_state and self.consecutive_state_count > 2:
            should_speak = False

        if should_speak:
            self.last_spoken_state = state

        # Context tags for debugging/extra templates
        context_tags = []
        if avg_speed > 150:
            context_tags.append("high_speed")
        if avg_speed > 180:
            context_tags.append("extreme_speed")
        if total_events >= 8:
            context_tags.append("heavy_traffic")
        if combo_peak >= 5:
            context_tags.append("combo_5")
        if combo_peak >= 10:
            context_tags.append("combo_10")

        return {
            "state": state,
            "should_speak": should_speak,
            "stats": {
                "overtakes_in_window": overtakes,
                "near_misses_in_window": near_misses,
                "lane_changes_in_window": lane_changes,
                "combo_peak": combo_peak,
                "avg_speed": round(avg_speed),
                "clean_driving_seconds": round(clean_driving_seconds, 1),
                "total_events_in_window": total_events
            },
            "context_tags": context_tags
        }
