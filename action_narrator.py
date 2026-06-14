import random
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ActionNarrator:
    def __init__(self):
        # Excitement levels per state
        self.state_excitement = {
            "Normal Driving": "Calm",
            "Recovery Phase": "Calm",
            "Perfect Rhythm": "Calm",
            "Masterclass": "Calm",
            "Total Control": "Calm",
            "Flow State": "Calm",
            
            "Building Momentum": "Excited",
            "Traffic Weaving": "Excited",
            "Elite Reactions": "Excited",
            "Traffic Chaos": "Excited",
            "High Risk Driving": "Excited",
            "Dominant Run": "Excited",
            "Highway Wizard": "Excited",
            "Traffic Surgeon": "Excited",
            "Precision Driving": "Excited",
            "Controlled Aggression": "Excited",
            "Record Pace": "Excited",
            "High Score": "Excited",
            
            "Crash": "Hype",
            "Extreme Near Miss": "Hype",
            "Clutch Survival": "Hype",
            "Panic Driving": "Hype",
            "High Combo": "Hype"
        }

        # Semantic grouped pools of templates without trailing punctuation
        self.grouped_pools = {
            "sports": {
                "overtake_single": ["blows past the {vehicle}", "passes on the {side}", "leaves the {vehicle} in the dust"],
                "overtake_multiple": ["carves through the pack, passing {count} cars", "blows past {count} vehicles", "slicing past multiple cars"],
                
                "dodge_single": ["DODGES the {vehicle}", "narrowly avoids the {vehicle}", "slips past the {vehicle}"],
                "dodge_multiple": ["evades multiple hazards", "dodges left and right under pressure", "two near misses in a row"],
                
                "swerve_single": ["cuts {side}", "sharp swerve to the {side}", "dives {side}"],
                "swerve_multiple": ["weaving left and right", "rapid lane changes", "zigzagging through traffic"],
                
                "close_call": ["inches from disaster", "trades paint with the {vehicle}", "millimeters away"],
                "squeeze_through": ["threads the needle", "slides through the gap", "squeezes between them"],
                
                "boost": ["hits the boost", "goes full throttle", "accelerates hard"],
                "surge": ["speed is surging", "redlines the engine at {speed} km/h", "flying forward"]
            },
            "narrator": {
                "overtake_single": ["glides past the {vehicle}", "a clean pass", "overtaking on the {side}"],
                "overtake_multiple": ["cleanly overtaking {count} vehicles", "moving past the traffic pack"],
                
                "dodge_single": ["narrowly avoiding the {vehicle}", "passing close to the {vehicle}"],
                "dodge_multiple": ["avoiding multiple close hazards", "a series of narrow escapes"],
                
                "swerve_single": ["a shift to the {side}", "moving {side}"],
                "swerve_multiple": ["weaving smoothly through lanes", "a sequence of lane changes"],
                
                "close_call": ["a brush with fate", "a very thin margin of safety"],
                "squeeze_through": ["a surgical passage between vehicles", "squeezing through a narrow gap"],
                
                "boost": ["engaging boost", "engine roars with a burst of speed"],
                "surge": ["speed climbs smoothly to {speed} km/h", "accelerating through the field"]
            },
            "savage": {
                "overtake_single": ["passed a {vehicle}, ground-breaking", "moves past the slow {vehicle}"],
                "overtake_multiple": ["passed {count} cars, bravo", "overtaking multiple slow pokes"],
                
                "dodge_single": ["almost died avoiding that {vehicle}", "lucky escape from the {vehicle}"],
                "dodge_multiple": ["almost crashed multiple times", "trying hard to get insurance money"],
                
                "swerve_single": ["yanks the wheel {side}", "jerks {side}"],
                "swerve_multiple": ["driving like a drunk slalom skier", "weaving erratically"],
                
                "close_call": ["that was dumb luck", "absolute miracle you didn't crash"],
                "squeeze_through": ["squeezed between them, how original", "nearly wrecked two other cars"],
                
                "boost": ["wasting fuel with boost", "flooring it, cute"],
                "surge": ["speeding up pointlessly", "going faster won't help you win"]
            }
        }

        # Situational closers for narrative flavor (without trailing punctuation)
        self.situational_closers = {
            "sports": {
                "Traffic Surgeon": ["clinical precision", "surgical work", "pure class"],
                "Highway Wizard": ["this is wizardry", "absolute magic", "unbelievable lines"],
                "Clutch Survival": ["how is he still alive", "unbelievable escape", "living on the edge"],
                "Extreme Near Miss": ["heart in mouth moment", "too close for comfort", "absolutely mental"],
                "High Combo": ["he's on fire", "unstoppable momentum", "sensational run"],
                "Dominant Run": ["leaving them in the dust", "a class apart"],
                "Traffic Chaos": ["absolute madness", "tearing the field apart"],
                "Flow State": ["completely locked in", "operates on instinct"],
                "Total Control": ["complete mastery", "driving school is in session"]
            },
            "narrator": {
                "Traffic Surgeon": ["executed with surgical precision", "a masterclass in lanes"],
                "Highway Wizard": ["an elegant sequence of weaves", "spells of brilliant control"],
                "Clutch Survival": ["narrowly escaping disaster", "living on the absolute edge"],
                "Extreme Near Miss": ["a very thin line between success and failure", "physics being pushed to the limit"],
                "High Combo": ["a remarkable run of clean driving", "momentum is fully established"],
                "Flow State": ["the driver is one with the machine", "a quiet confidence"]
            },
            "savage": {
                "Traffic Surgeon": ["showoff", "typical lane weaver"],
                "Highway Wizard": ["hope your luck holds up", "enjoy the spotlight while it lasts"],
                "Clutch Survival": ["must have closed their eyes and hoped", "a miracle they aren't in a wall"],
                "Extreme Near Miss": ["don't push your luck", "the tow truck is on standby"],
                "High Combo": ["still not a world record", "don't blink, it'll end soon"]
            }
        }

        # History tracker to prevent direct repetition
        self.last_10_spoken = []

    def compose(self, actions: List[Dict[str, Any]], state: str, excitement: str, mode: str, stats: Dict[str, Any]) -> str:
        """
        Creates a FIFA-style play-by-play commentary sentence from recent physical player actions,
        grouping repetitive events to maintain professional broadcast flow.
        """
        if not actions:
            return ""

        mode = mode.lower()
        if mode not in self.grouped_pools:
            mode = "sports"

        # Determine excitement level if not provided or override based on state
        state_exc = self.state_excitement.get(state, "Excited")
        if not excitement:
            excitement = state_exc

        # Categorize actions to group and summarize them
        overtakes = []
        dodges = []
        swerves = []
        boosts = []
        surges = []
        close_calls = []
        squeezes = []
        
        for a in actions:
            evt = a.get("event", "")
            if "overtake" in evt:
                overtakes.append(a)
            elif "dodge" in evt:
                dodges.append(a)
            elif "swerve" in evt:
                swerves.append(a)
            elif "boost" in evt:
                boosts.append(a)
            elif "speed_surge" in evt:
                surges.append(a)
            elif "close_call" in evt:
                close_calls.append(a)
            elif "squeeze_through" in evt:
                squeezes.append(a)

        # Perform composition in a loop to allow retries if the generated line is in the last_10_spoken
        for retry in range(3):
            phrases = []
            
            # 1. Squeezes / Close Calls
            if squeezes:
                pattern = random.choice(self.grouped_pools[mode]["squeeze_through"])
                phrases.append(pattern.format(vehicle=squeezes[0].get("vehicle_type", "car")))
            elif close_calls:
                pattern = random.choice(self.grouped_pools[mode]["close_call"])
                phrases.append(pattern.format(vehicle=close_calls[0].get("vehicle_type", "car")))
                
            # 2. Dodges
            if len(dodges) > 1:
                pattern = random.choice(self.grouped_pools[mode]["dodge_multiple"])
                phrases.append(pattern.format(count=len(dodges)))
            elif len(dodges) == 1:
                if not squeezes and not close_calls:
                    d = dodges[0]
                    side = "left" if "left" in d.get("event", "") else "right"
                    pattern = random.choice(self.grouped_pools[mode]["dodge_single"])
                    phrases.append(pattern.format(vehicle=d.get("vehicle_type", "car"), side=side))
                    
            # 3. Overtakes
            if len(overtakes) > 1:
                pattern = random.choice(self.grouped_pools[mode]["overtake_multiple"])
                phrases.append(pattern.format(count=len(overtakes)))
            elif len(overtakes) == 1:
                o = overtakes[0]
                side = "left" if "left" in o.get("event", "") else "right"
                pattern = random.choice(self.grouped_pools[mode]["overtake_single"])
                phrases.append(pattern.format(vehicle=o.get("vehicle_type", "car"), side=side))
                
            # 4. Boost / Surge
            if surges:
                pattern = random.choice(self.grouped_pools[mode]["surge"])
                phrases.append(pattern.format(speed=surges[0].get("to_speed", stats.get("avg_speed", 120))))
            elif boosts:
                pattern = random.choice(self.grouped_pools[mode]["boost"])
                phrases.append(pattern.format(speed=boosts[0].get("speed", stats.get("avg_speed", 120))))
                
            # 5. Swerves (only add if we don't have too many phrases to keep it concise)
            if len(phrases) < 2:
                if len(swerves) > 1:
                    pattern = random.choice(self.grouped_pools[mode]["swerve_multiple"])
                    phrases.append(pattern.format(count=len(swerves)))
                elif len(swerves) == 1:
                    s = swerves[0]
                    side = "left" if "left" in s.get("event", "") else "right"
                    pattern = random.choice(self.grouped_pools[mode]["swerve_single"])
                    phrases.append(pattern.format(side=side))

            # Limit to at most 2 semantic clauses for punchy narration
            selected_phrases = phrases[:2]

            if not selected_phrases:
                return ""

            # Apply casing and punctuation to phrases, then join them
            joined_text = ""
            if excitement == "Calm":
                processed_phrases = []
                for idx, p in enumerate(selected_phrases):
                    if idx > 0 and p and p[0].isupper():
                        processed_phrases.append(p)
                    else:
                        processed_phrases.append(p[0].lower() + p[1:] if p else "")
                
                if len(processed_phrases) == 1:
                    joined_text = processed_phrases[0]
                else:
                    joined_text = f"{processed_phrases[0]} and {processed_phrases[1]}"
                
                if joined_text:
                    joined_text = joined_text[0].upper() + joined_text[1:]

            elif excitement == "Excited":
                processed_phrases = []
                for p in selected_phrases:
                    if p:
                        processed_phrases.append(p[0].upper() + p[1:])

                if len(processed_phrases) == 1:
                    joined_text = processed_phrases[0]
                else:
                    connector = random.choice([" and ", " — ", ", "])
                    if connector == ", ":
                        second_phrase = processed_phrases[1][0].lower() + processed_phrases[1][1:] if processed_phrases[1] else ''
                        joined_text = f"{processed_phrases[0]}, {second_phrase}"
                    else:
                        joined_text = f"{processed_phrases[0]}{connector}{processed_phrases[1]}"

            else:  # Hype
                processed_phrases = []
                for p in selected_phrases:
                    if p:
                        val = p.upper() if mode == "sports" else (p[0].upper() + p[1:])
                        processed_phrases.append(val)

                if len(processed_phrases) == 1:
                    joined_text = processed_phrases[0]
                else:
                    joined_text = f"{processed_phrases[0]} AND STILL GOING — {processed_phrases[1]}"

            # Maybe append a situational closer
            closers_pool = self.situational_closers.get(mode, {}).get(state, [])
            if closers_pool and random.random() < 0.7:  # 70% chance to append a closer
                closer = random.choice(closers_pool)
                if mode == "sports" and excitement in ("Excited", "Hype"):
                    closer = closer.upper()
                else:
                    closer = closer[0].upper() + closer[1:]
                
                if excitement == "Calm":
                    joined_text = f"{joined_text}. {closer}."
                elif excitement == "Excited":
                    joined_text = f"{joined_text}! {closer}!"
                else: # Hype
                    joined_text = f"{joined_text}!! {closer}!!"
            else:
                # Add default end punctuation if no closer was appended
                if excitement == "Calm":
                    joined_text = f"{joined_text}."
                elif excitement == "Excited":
                    joined_text = f"{joined_text}!"
                else:
                    joined_text = f"{joined_text}!!"

            # Word count check: keep it under 20 words for natural TTS flow
            words = joined_text.split()
            if len(words) > 20:
                joined_text = " ".join(words[:18]) + "!"

            # Anti-repetition check
            if joined_text not in self.last_10_spoken:
                break
        
        # Save to history
        self.last_10_spoken.append(joined_text)
        if len(self.last_10_spoken) > 10:
            self.last_10_spoken.pop(0)

        return joined_text
