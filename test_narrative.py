import pytest
from narrative import NarrativeEngine

def test_narrative_default_driving():
    engine = NarrativeEngine(window_seconds=18.0)
    # Start at t=0, speed=100, combo=0, empty batch -> Normal Driving
    res = engine.evaluate([], current_time=0.0, current_speed=100.0, current_combo=0)
    assert res["state"] == "Normal Driving"
    assert res["should_speak"] is False # Ignored/silenced
    assert res["stats"]["traffic_density"] == "low"
    assert res["stats"]["danger_level"] == "safe"
    assert res["stats"]["near_miss_count"] == 0

def test_narrative_building_momentum():
    engine = NarrativeEngine(window_seconds=18.0)
    events = [
        {"event": "overtake", "speed": 120, "combo": 0, "timestamp": 1.0},
        {"event": "overtake", "speed": 120, "combo": 0, "timestamp": 2.0},
        {"event": "overtake", "speed": 120, "combo": 0, "timestamp": 3.0},
    ]
    res = engine.evaluate(events, current_time=4.0, current_speed=120.0, current_combo=0)
    assert res["state"] == "Building Momentum"
    assert res["should_speak"] is True

def test_narrative_traffic_weaving():
    engine = NarrativeEngine(window_seconds=18.0)
    events = [
        {"event": "traffic_weave", "speed": 110, "combo": 0, "timestamp": 1.0},
        {"event": "traffic_weave", "speed": 110, "combo": 0, "timestamp": 2.0},
    ]
    res = engine.evaluate(events, current_time=4.0, current_speed=110.0, current_combo=0)
    assert res["state"] == "Traffic Weaving"
    assert res["should_speak"] is True

def test_narrative_clutch_survival():
    engine = NarrativeEngine(window_seconds=18.0)
    # 3 near misses in window
    events = [
        {"event": "near_miss", "speed": 100, "combo": 1, "timestamp": 1.0},
        {"event": "near_miss", "speed": 100, "combo": 2, "timestamp": 2.0},
        {"event": "near_miss", "speed": 100, "combo": 3, "timestamp": 3.0},
    ]
    res = engine.evaluate(events, current_time=4.0, current_speed=100.0, current_combo=3)
    assert res["state"] == "Clutch Survival"
    assert res["should_speak"] is True

def test_narrative_high_risk_driving():
    engine = NarrativeEngine(window_seconds=18.0)
    # 1 near miss at high speed
    events = [
        {"event": "near_miss", "speed": 150, "combo": 1, "timestamp": 1.0},
    ]
    res = engine.evaluate(events, current_time=2.0, current_speed=150.0, current_combo=1)
    assert res["state"] == "High Risk Driving"
    assert res["should_speak"] is True
    assert res["stats"]["danger_level"] == "high"

def test_narrative_elite_reactions():
    engine = NarrativeEngine(window_seconds=18.0)
    # Combo peak of 5 triggers Elite Reactions
    res = engine.evaluate([], current_time=2.0, current_speed=120.0, current_combo=5)
    assert res["state"] == "Elite Reactions"
    assert res["should_speak"] is True

def test_narrative_high_combo():
    engine = NarrativeEngine(window_seconds=18.0)
    # Combo peak of 10 triggers High Combo
    res = engine.evaluate([], current_time=2.0, current_speed=120.0, current_combo=10)
    assert res["state"] == "High Combo"
    assert res["should_speak"] is True

def test_narrative_total_control():
    engine = NarrativeEngine(window_seconds=18.0)
    # Clean driving for >= 30 seconds
    res = engine.evaluate([], current_time=32.0, current_speed=120.0, current_combo=0)
    assert res["state"] == "Total Control"
    assert res["should_speak"] is True

def test_narrative_traffic_chaos():
    engine = NarrativeEngine(window_seconds=18.0)
    # High event count + high speed
    events = [
        {"event": "overtake", "speed": 140, "combo": 0, "timestamp": 1.0},
        {"event": "overtake", "speed": 140, "combo": 0, "timestamp": 2.0},
        {"event": "overtake", "speed": 140, "combo": 0, "timestamp": 3.0},
        {"event": "overtake", "speed": 140, "combo": 0, "timestamp": 4.0},
        {"event": "overtake", "speed": 140, "combo": 0, "timestamp": 5.0},
        {"event": "overtake", "speed": 140, "combo": 0, "timestamp": 6.0},
    ]
    res = engine.evaluate(events, current_time=7.0, current_speed=140.0, current_combo=0)
    assert res["state"] == "Traffic Chaos"
    assert res["should_speak"] is True
    assert res["stats"]["traffic_density"] == "heavy"

def test_narrative_recovery_phase():
    engine = NarrativeEngine(window_seconds=18.0)
    
    # 1. Trigger High Risk Driving
    res1 = engine.evaluate([{"event": "near_miss", "speed": 150, "combo": 1, "timestamp": 1.0}], current_time=2.0, current_speed=150.0, current_combo=1)
    assert res1["state"] == "High Risk Driving"
    
    # 2. Quiet driving after 18s window has passed, causing near_miss to be pruned
    res2 = engine.evaluate([], current_time=22.0, current_speed=100.0, current_combo=0)
    assert res2["state"] == "Recovery Phase"
    assert res2["should_speak"] is True

def test_narrative_commentator_memory():
    engine = NarrativeEngine(window_seconds=18.0)
    
    # Check masterclass_streak after 20s of clean driving
    res = engine.evaluate([{"event": "overtake", "speed": 100, "combo": 0, "timestamp": 2.0}], current_time=22.0, current_speed=100.0, current_combo=0)
    assert "masterclass_streak" in res["context_tags"]
    
    # Check pressure_rising when traffic jumps to heavy
    events = [
        {"event": "overtake", "speed": 120, "combo": 0, "timestamp": 23.0},
        {"event": "overtake", "speed": 120, "combo": 0, "timestamp": 24.0},
        {"event": "overtake", "speed": 120, "combo": 0, "timestamp": 25.0},
        {"event": "overtake", "speed": 120, "combo": 0, "timestamp": 26.0},
        {"event": "overtake", "speed": 120, "combo": 0, "timestamp": 27.0},
        {"event": "overtake", "speed": 120, "combo": 0, "timestamp": 28.0},
    ]
    res_pressure = engine.evaluate(events, current_time=29.0, current_speed=120.0, current_combo=0)
    assert "pressure_rising" in res_pressure["context_tags"]

def test_narrative_transitions():
    engine = NarrativeEngine(window_seconds=18.0)
    
    # 1. Initial State: Normal Driving (at t=0)
    res1 = engine.evaluate([], current_time=0.0, current_speed=100.0, current_combo=0)
    assert res1["state"] == "Normal Driving"
    assert res1["previous_state"] == "Normal Driving"
    assert res1["state_duration"] == 0.0
    assert res1["transition"] is None
    
    # 2. Trigger Building Momentum at t=5.0
    events = [
        {"event": "overtake", "speed": 120, "combo": 0, "timestamp": 1.0},
        {"event": "overtake", "speed": 120, "combo": 0, "timestamp": 2.0},
        {"event": "overtake", "speed": 120, "combo": 0, "timestamp": 3.0},
    ]
    res2 = engine.evaluate(events, current_time=5.0, current_speed=120.0, current_combo=0)
    assert res2["state"] == "Building Momentum"
    assert res2["previous_state"] == "Normal Driving"
    assert res2["state_duration"] == 5.0
    assert res2["transition"] is not None
    assert res2["transition"]["from"] == "Normal Driving"
    assert res2["transition"]["to"] == "Building Momentum"
    assert res2["transition"]["duration"] == 5.0

    # 3. Maintain state at t=10.0
    res3 = engine.evaluate([], current_time=10.0, current_speed=120.0, current_combo=0)
    assert res3["state"] == "Building Momentum"
    assert res3["previous_state"] == "Building Momentum"
    assert res3["state_duration"] == 5.0 # Since t=5.0
    assert res3["transition"] is None
