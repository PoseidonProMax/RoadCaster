import pytest
from narrative import NarrativeEngine

def test_narrative_default_cruising():
    engine = NarrativeEngine(window_seconds=15.0)
    # Start at t=0, speed=100, combo=0, empty batch
    res = engine.evaluate([], current_time=0.0, current_speed=100.0, current_combo=0)
    assert res["state"] == "CALM_CRUISING"
    assert res["should_speak"] is True
    
    # Second evaluation with empty events -> consecutive CALM_CRUISING should be suppressed
    res2 = engine.evaluate([], current_time=4.0, current_speed=100.0, current_combo=0)
    assert res2["state"] == "CALM_CRUISING"
    assert res2["should_speak"] is False

def test_narrative_aggressive_driving():
    engine = NarrativeEngine(window_seconds=15.0)
    events = [
        {"event": "overtake", "speed": 120, "combo": 0, "timestamp": 1.0},
        {"event": "overtake", "speed": 120, "combo": 0, "timestamp": 2.0},
        {"event": "overtake", "speed": 120, "combo": 0, "timestamp": 3.0},
        {"event": "overtake", "speed": 120, "combo": 0, "timestamp": 4.0},
        {"event": "overtake", "speed": 120, "combo": 0, "timestamp": 5.0},
    ]
    res = engine.evaluate(events, current_time=6.0, current_speed=120.0, current_combo=0)
    assert res["state"] == "AGGRESSIVE_DRIVING"
    assert res["stats"]["overtakes_in_window"] == 5
    assert res["should_speak"] is True

def test_narrative_traffic_chaos():
    engine = NarrativeEngine(window_seconds=15.0)
    # Needs near_misses >= 3 and total_events >= 6
    events = [
        {"event": "near_miss", "speed": 100, "combo": 1, "timestamp": 1.0},
        {"event": "near_miss", "speed": 100, "combo": 2, "timestamp": 2.0},
        {"event": "near_miss", "speed": 100, "combo": 3, "timestamp": 3.0},
        {"event": "overtake", "speed": 100, "combo": 3, "timestamp": 4.0},
        {"event": "overtake", "speed": 100, "combo": 3, "timestamp": 5.0},
        {"event": "overtake", "speed": 100, "combo": 3, "timestamp": 6.0},
    ]
    res = engine.evaluate(events, current_time=7.0, current_speed=100.0, current_combo=3)
    assert res["state"] == "TRAFFIC_CHAOS"
    assert res["stats"]["near_misses_in_window"] == 3
    assert res["stats"]["total_events_in_window"] == 6
    assert res["should_speak"] is True

def test_narrative_high_risk():
    engine = NarrativeEngine(window_seconds=15.0)
    # Needs near_misses >= 2 and avg_speed > 150
    events = [
        {"event": "near_miss", "speed": 160, "combo": 1, "timestamp": 1.0},
        {"event": "near_miss", "speed": 160, "combo": 2, "timestamp": 2.0},
    ]
    res = engine.evaluate(events, current_time=3.0, current_speed=160.0, current_combo=2)
    assert res["state"] == "HIGH_RISK_DRIVING"
    assert res["should_speak"] is True

def test_narrative_window_pruning():
    engine = NarrativeEngine(window_seconds=10.0) # 10s window for test
    # Add an overtake at t=1.0
    engine.evaluate([{"event": "overtake", "speed": 100, "combo": 0, "timestamp": 1.0}], current_time=2.0, current_speed=100.0, current_combo=0)
    
    # At t=12.0, that overtake is 11s old and should be pruned (window=10s)
    res = engine.evaluate([], current_time=12.0, current_speed=100.0, current_combo=0)
    assert res["stats"]["overtakes_in_window"] == 0
    assert res["stats"]["total_events_in_window"] == 0

def test_narrative_clutch_performance():
    engine = NarrativeEngine(window_seconds=15.0)
    # Needs combo_peak >= 8
    res = engine.evaluate([], current_time=1.0, current_speed=100.0, current_combo=8)
    assert res["state"] == "CLUTCH_PERFORMANCE"

def test_narrative_recovery_phase():
    engine = NarrativeEngine(window_seconds=15.0)
    
    # Get into high risk driving state
    events = [
        {"event": "near_miss", "speed": 160, "combo": 1, "timestamp": 1.0},
        {"event": "near_miss", "speed": 160, "combo": 2, "timestamp": 2.0},
    ]
    res = engine.evaluate(events, current_time=3.0, current_speed=160.0, current_combo=2)
    assert res["state"] == "HIGH_RISK_DRIVING"
    
    # Clear history and simulate quiet time (prune danger events or verify state switch with 0 near_misses in current window)
    # If we evaluate with empty list at t=20, the events at t=1 and t=2 are pruned.
    # The previous state was HIGH_RISK_DRIVING.
    res2 = engine.evaluate([], current_time=20.0, current_speed=100.0, current_combo=0)
    assert res2["state"] == "RECOVERY_PHASE"
    assert res2["should_speak"] is True
