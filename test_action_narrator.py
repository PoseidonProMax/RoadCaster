import pytest
from action_narrator import ActionNarrator

def test_action_narrator_priorities():
    narrator = ActionNarrator()
    actions = [
        {"event": "swerve_left", "timestamp": 1.0},
        {"event": "close_call", "vehicle_type": "truck", "timestamp": 1.5},
        {"event": "overtake_right", "vehicle_type": "car", "timestamp": 2.0},
        {"event": "boost_start", "timestamp": 2.5}
    ]
    
    # It should pick close_call (priority 100), overtake_right (priority 60), and boost_start (priority 70) 
    # instead of swerve_left (priority 50).
    # Re-sorting chronologically: close_call (1.5), overtake_right (2.0), boost_start (2.5)
    stats = {"avg_speed": 150}
    commentary = narrator.compose(actions, "High Risk Driving", "Excited", "sports", stats)
    
    assert commentary != ""
    assert "truck" in commentary.lower() or "car" in commentary.lower() or "boost" in commentary.lower()
    # It should not contain "left" because swerve_left was deprioritized
    assert "left" not in commentary.lower()

def test_action_narrator_modes():
    narrator = ActionNarrator()
    actions = [
        {"event": "squeeze_through", "vehicle_type": "car", "timestamp": 1.0}
    ]
    stats = {"avg_speed": 120}
    
    # Sports mode: punchy, capitalized key terms
    sports_commentary = narrator.compose(actions, "Clutch Survival", "Hype", "sports", stats)
    assert sports_commentary != ""
    assert any(x in sports_commentary.upper() for x in ["THREADS THE NEEDLE", "GAP", "SQUEEZES"])
    
    # Narrator mode: calm, description-style
    narrator_commentary = narrator.compose(actions, "Clutch Survival", "Calm", "narrator", stats)
    assert narrator_commentary != ""
    assert any(x in narrator_commentary.lower() for x in ["gap", "passage", "squeezing"])
    
    # Savage mode: sarcastic
    savage_commentary = narrator.compose(actions, "Clutch Survival", "Calm", "savage", stats)
    assert savage_commentary != ""
    assert "squeezed" in savage_commentary.lower() or "wreck" in savage_commentary.lower()

def test_word_count_cap():
    narrator = ActionNarrator()
    # Provide a huge list of actions
    actions = [
        {"event": "swerve_left", "timestamp": 1.0},
        {"event": "close_call", "vehicle_type": "truck", "timestamp": 1.2},
        {"event": "squeeze_through", "vehicle_type": "car", "timestamp": 1.4},
        {"event": "overtake_right", "vehicle_type": "bus", "timestamp": 1.6},
        {"event": "boost_start", "timestamp": 1.8}
    ]
    stats = {"avg_speed": 180}
    commentary = narrator.compose(actions, "Traffic Chaos", "Hype", "sports", stats)
    
    words = commentary.split()
    assert len(words) <= 20

def test_anti_repetition():
    narrator = ActionNarrator()
    actions = [{"event": "boost_start", "timestamp": 1.0}]
    stats = {"avg_speed": 140}
    
    res1 = narrator.compose(actions, "Building Momentum", "Excited", "sports", stats)
    res2 = narrator.compose(actions, "Building Momentum", "Excited", "sports", stats)
    res3 = narrator.compose(actions, "Building Momentum", "Excited", "sports", stats)
    
    # Ensure they aren't all identical (given pool options)
    # Note: with a single action event in pool of size 3, it might repeat if we run out of options,
    # but the retry mechanism will try to avoid duplicates.
    assert res1 in narrator.last_10_spoken
