import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class NarrativeEngine:
    def __init__(self, window_seconds: float = 18.0):
        self.window_seconds = window_seconds
        self.event_history: List[Dict[str, Any]] = []
        
        # State tracking
        self.last_state = "Normal Driving"
        self.state_start_time = 0.0
        self.consecutive_state_count = 0
        self.last_spoken_state = None
        
        # Commentator memory
        self.previous_traffic_level = "low"
        self.clean_period_triggered = False

    def reset(self):
        """Resets the history and state tracking."""
        self.event_history.clear()
        self.last_state = "Normal Driving"
        self.state_start_time = 0.0
        self.consecutive_state_count = 0
        self.last_spoken_state = None
        self.previous_traffic_level = "low"
        self.clean_period_triggered = False

    def evaluate(self, new_events: List[Dict[str, Any]], current_time: float, current_speed: float, current_combo: int, critical: bool = False, actions: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Processes new events, updates history, prunes old events,
        determines the current narrative state and whether to generate commentary.
        """
        # Append new events
        for ev in new_events:
            if "timestamp" not in ev:
                ev["timestamp"] = current_time
            self.event_history.append(ev)

        # Prune old events outside the 18s window
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
        has_extreme_near_miss = False
        has_crash = False
        has_high_score = False
        has_game_start = False

        for e in self.event_history:
            evt_type = e.get("event")
            if evt_type == "crash":
                has_crash = True
            if evt_type == "extreme_near_miss":
                has_extreme_near_miss = True
                near_misses += 1
            if evt_type in ("near_miss", "recovery"):
                near_misses += 1
                evt_time = e.get("timestamp", 0)
                if last_danger_time is None or evt_time > last_danger_time:
                    last_danger_time = evt_time
            if evt_type == "traffic_weave":
                lane_changes += 1
            if evt_type in ("overtake", "multi_overtake"):
                overtakes += 1
            if evt_type == "high_score":
                has_high_score = True
            if evt_type == "game_start":
                has_game_start = True
            
            combo_peak = max(combo_peak, e.get("combo", 0))
            if "speed" in e:
                speeds.append(e["speed"])

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

        # Commentator Memory 1: Enters heavy traffic
        traffic_level = "low"
        if total_events >= 6:
            traffic_level = "heavy"
        elif total_events >= 3:
            traffic_level = "moderate"

        pressure_rising = False
        if traffic_level == "heavy" and self.previous_traffic_level in ("low", "moderate"):
            pressure_rising = True
        self.previous_traffic_level = traffic_level

        # Commentator Memory 2: Masterclass clean driving
        masterclass_streak = False
        if clean_driving_seconds >= 20.0 and not self.clean_period_triggered and current_time > 10.0:
            masterclass_streak = True
            self.clean_period_triggered = True
        elif clean_driving_seconds < 5.0:
            self.clean_period_triggered = False

        # Calculate danger level classification
        danger_level = "safe"
        if has_crash:
            danger_level = "critical"
        elif near_misses >= 3 or has_extreme_near_miss:
            danger_level = "critical"
        elif near_misses >= 1 or avg_speed > 150:
            danger_level = "high"
        elif avg_speed > 100:
            danger_level = "moderate"

        # Priority-ordered rule engine for narrative state derivation
        state = "Normal Driving"

        # 1. Crash always overrides
        if has_crash:
            state = "Crash"
        # 2. Extreme Near Miss
        elif has_extreme_near_miss:
            state = "Extreme Near Miss"
        # 2b. High Combo
        elif combo_peak >= 10:
            state = "High Combo"
        # 3. Clutch Survival / Panic Driving / Traffic Chaos
        elif near_misses >= 3 or combo_peak >= 8:
            state = "Clutch Survival"
        elif total_events >= 5 and avg_speed < 80 and near_misses >= 1:
            state = "Panic Driving"
        elif total_events >= 6 and avg_speed > 130:
            state = "Traffic Chaos"
        # 4. High Risk Driving
        elif near_misses >= 1 and avg_speed > 140:
            state = "High Risk Driving"
        # 5. Elite Reactions
        elif combo_peak >= 5:
            state = "Elite Reactions"
        # 6. Untouchable / Dominant Run / Highway Wizard
        elif clean_driving_seconds >= 15.0 and overtakes >= 4:
            state = "Untouchable"
        elif avg_speed > 150 and overtakes >= 5:
            state = "Dominant Run"
        elif lane_changes >= 3 and overtakes >= 3:
            state = "Highway Wizard"
        # 7. Traffic Surgeon / Precision Driving
        elif lane_changes >= 2 and overtakes >= 2 and near_misses == 0:
            state = "Traffic Surgeon"
        elif clean_driving_seconds >= 15.0 and lane_changes >= 2 and overtakes >= 1:
            state = "Precision Driving"
        # 8. Total Control / Masterclass / Flow State
        elif clean_driving_seconds >= 30.0:
            state = "Total Control"
        elif clean_driving_seconds >= 25.0:
            state = "Masterclass"
        elif clean_driving_seconds >= 20.0 and overtakes >= 2:
            state = "Flow State"
        # 9. Controlled Aggression
        elif overtakes >= 4 and near_misses == 0:
            state = "Controlled Aggression"
        # 10. Record Pace
        elif current_speed > 175:
            state = "Record Pace"
        # 11. Building Momentum / Traffic Weaving
        elif overtakes >= 3:
            state = "Building Momentum"
        elif lane_changes >= 2:
            state = "Traffic Weaving"
        # 12. Perfect Rhythm
        elif clean_driving_seconds >= 10.0 and overtakes >= 2:
            state = "Perfect Rhythm"
        # 13. Recovery Phase / High Score / game_start
        elif self.last_state in ("High Risk Driving", "Traffic Chaos", "Clutch Survival", "Panic Driving") and near_misses == 0:
            state = "Recovery Phase"
        elif has_high_score:
            state = "High Score"
        elif has_game_start:
            state = "game_start"

        # Update consecutive states and track transitions
        previous_state = self.last_state
        state_duration = current_time - self.state_start_time
        transition = None

        if state != self.last_state:
            # Transition occurred
            transition = {
                "from": previous_state,
                "to": state,
                "duration": state_duration
            }
            self.last_state = state
            self.state_start_time = current_time
            self.consecutive_state_count = 1
        else:
            self.consecutive_state_count += 1

        # Control speaking vs silence
        should_speak = True
        
        # Silence normal driving completely
        if state == "Normal Driving":
            should_speak = False
            
        # Prevent speaking consecutive recovery or total control / masterclass
        if state in ("Recovery Phase", "Total Control", "Masterclass", "Flow State") and self.consecutive_state_count > 1:
            should_speak = False

        # Critical bypasses
        if critical or state in ("Crash", "Extreme Near Miss", "High Score"):
            should_speak = True

        if should_speak:
            self.last_spoken_state = state

        # Compile context tags
        context_tags = []
        if pressure_rising:
            context_tags.append("pressure_rising")
        if masterclass_streak:
            context_tags.append("masterclass_streak")
        if avg_speed > 150:
            context_tags.append("high_speed")
        if combo_peak >= 5:
            context_tags.append("combo_5")

        return {
            "state": state,
            "previous_state": previous_state,
            "state_duration": round(state_duration, 1),
            "transition": transition,
            "should_speak": should_speak,
            "bypass_cooldown": critical or state in ("Crash", "Extreme Near Miss", "High Score"),
            "stats": {
                "actions_per_second": round(len(actions) / 3.5, 2) if actions else 0.0,
                "action_count": len(actions) if actions else 0,
                "overtakes_in_window": overtakes,
                "near_misses_in_window": near_misses,
                "lane_changes_in_window": lane_changes,
                "combo_peak": combo_peak,
                "avg_speed": round(avg_speed),
                "clean_driving_seconds": round(clean_driving_seconds, 1),
                "total_events_in_window": total_events,
                "traffic_density": traffic_level,
                "danger_level": danger_level,
                "near_miss_count": near_misses
            },
            "context_tags": context_tags
        }
