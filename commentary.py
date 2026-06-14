import random
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class CommentaryEngine:
    def __init__(self):
        # Tracking recently spoken templates to prevent repetition within the last 10 lines
        self.last_10_spoken = []
        self.turn_counter = 0

        # Define templates for each mode and narrative state
        self.templates = {
            "sports": {
                "game_start": [
                    "Green light! We are underway on the RoadCaster highway!",
                    "And they're off! Let's see if this driver has what it takes!",
                    "Engine roaring, tires biting the asphalt, the journey begins!",
                    "The lights are green and we are live from the fastest highway on earth!"
                ],
                "Crash": [
                    "OH NO! A COLLISION! AAAAAAH! HA HA HA! GAME OVER!",
                    "DEVASTATING COLLISION! AAAAH! HA HA HA! Absolute catastrophe on the highway!",
                    "SMASH! HA HA HA! The physics engine wins this round! What a spectacular wreck!",
                    "AND HE'S OUT! WRECKED! AAAAH! HA HA HA! SPECTACULAR DESTRUCTION!"
                ],
                "Extreme Near Miss": [
                    "GOOD HEAVENS! THAT WAS CENTIMETERS FROM AN ABSOLUTE DISASTER!",
                    "OH! THEY TRADED PAINT! Absolute heart-in-mouth moment!",
                    "INCHES FROM DISASTER! That gap barely existed and they STILL found a way through!",
                    "HOLY MOLY! How did they dodge that?! Absolute nerves of steel!"
                ],
                "Recovery Phase": [
                    "WHAT A SAVE! Composure restored after a near-disaster!",
                    "DISASTER AVERTED! Composure regained and control re-established!",
                    "REGAINED CONTROL! The driver resets their focus and stabilizes!"
                ],
                "Total Control": [
                    "THIS IS A DEMONSTRATION OF TOTAL CONTROL! Absolutely flawless driving!",
                    "THE DRIVER IS DICTATING THE TERMS! Total control of the vehicle!",
                    "Flawless execution! They have complete command of this highway!",
                    "No mistakes, no panic. Just absolute, total control at {speed} km/h!"
                ],
                "Masterclass": [
                    "THIS IS BECOMING A MASTERCLASS IN HIGHWAY CONTROL!",
                    "EVERY DECISION IS THE RIGHT ONE! Locked in masterclass driving!",
                    "THE DRIVER LOOKS COMPLETELY LOCKED IN! A master at work!",
                    "A CLINICAL TUTORIAL ON CONTROL! Not a single mistake for 25 seconds!"
                ],
                "Flow State": [
                    "EVERYTHING IS CLICKING RIGHT NOW! The driver is in flow state!",
                    "THE DRIVER IS OPERATING ON INSTINCT! It all looks effortless!",
                    "IN THE ZONE! Every decision, every swerve, completely locked in!"
                ],
                "High Score": [
                    "NEW HIGH SCORE! The driver is rewriting the history books!",
                    "HISTORY IS MADE! A new benchmark has been set!",
                    "UNPRECEDENTED HEIGHTS! They've just beaten the record!"
                ],
                "Building Momentum->Traffic Surgeon": [
                    "The confidence is growing now! Threading through lanes like a pro!",
                    "Excellent transition! Building momentum has led to clinical traffic surgery!"
                ]
            },
            "narrator": {
                "game_start": [
                    "A lone driver starts the ignition. The asphalt awaits.",
                    "Into the neon-lit abyss we go.",
                    "Under the shadow of the day, the journey begins."
                ],
                "Crash": [
                    "A sudden impact. Screams, chrome, and... ha... ha... ha... silence.",
                    "The highway always wins. In the end. Ha... ha... ha...",
                    "A flash of chrome, a screech of tires, and then... ha ha ha... silence.",
                    "The run ends as all fast runs must: in spectacular ruin. Ha ha ha."
                ],
                "Extreme Near Miss": [
                    "Death whispered, but the driver didn't listen.",
                    "A close encounter with fate, resolved in milliseconds.",
                    "The gap was narrow. The survival, narrower."
                ],
                "Recovery Phase": [
                    "Composure returns, if only temporarily.",
                    "Control is re-established. The pulse begins to slow."
                ],
                "Total Control": [
                    "A serene exhibition of control.",
                    "Flawless and silent. The driver is completely synchronized with the highway.",
                    "No mistakes. No hesitation."
                ],
                "Masterclass": [
                    "This is a masterclass in motion.",
                    "Not a single misstep for twenty-five seconds. Remarkable.",
                    "An exhibition of pure, uninterrupted focus."
                ],
                "Flow State": [
                    "Instinct has taken over. Thought is no longer required.",
                    "Operating in the zone. Every action is second nature."
                ],
                "High Score": [
                    "A new record. The boundaries have been pushed further.",
                    "A milestone has been reached."
                ],
                "Building Momentum->Traffic Surgeon": [
                    "Momentum translates into surgical precision.",
                    "The velocity is rising, and the lanes are being cut cleanly."
                ],
                "Traffic Surgeon->Highway Wizard": [
                    "Surgical turns elevate into highway wizardry.",
                    "Precision gives way to absolute art on the road."
                ],
                "Highway Wizard->Clutch Survival": [
                    "The line between magic and disaster grows thin.",
                    "Danger levels are rising quickly."
                ],
                "Clutch Survival->Recovery Phase": [
                    "The danger passes. Control is restored.",
                    "Composure is regained."
                ],
                "*->Recovery Phase": [
                    "The situation stabilizes.",
                    "The run is brought back under control."
                ],
                "*->Total Control": [
                    "Complete calm returns to the driver.",
                    "A return to total, unwavering control."
                ],
                "*->Clutch Survival": [
                    "The pressure mounts. The margins are now minimal.",
                    "The driver enters a state of critical evasion."
                ]
            },
            "savage": {
                "game_start": [
                    "Oh look, someone else trying to drive fast. Let's see how long this lasts.",
                    "Starting the engine. Hope you have insurance.",
                    "Here we go again. Another generic run."
                ],
                "Crash": [
                    "HA HA HA! Wrecked! Absolutely predictable.",
                    "HA HA HA! Back to the lobby for you! Absolute disaster.",
                    "HA HA HA! Look at that spectacular wreck! You actually failed!",
                    "HA HA HA! Wrecked! Hope you have insurance, because that was pathetic!"
                ],
                "Extreme Near Miss": [
                    "Missed by a hair. Your luck won't last forever.",
                    "That was stupidly close. Try looking at the screen.",
                    "Nearly ended it all right there. Slow down."
                ],
                "Recovery Phase": [
                    "Oh, you survived? Color me surprised.",
                    "Congratulations on not dying. Yet."
                ],
                "Total Control": [
                    "Boringly safe. Are you going to speed up or what?",
                    "Driving like a grandmother. Flawless, but slow.",
                    "Not hitting anything. How thrilling."
                ],
                "Masterclass": [
                    "Twenty-five seconds without hitting anything. Want a medal?",
                    "A masterclass in safety. Wake me up when something happens."
                ],
                "Flow State": [
                    "Locked in? Or just staring blankly?",
                    "You think you're in the zone. You're just lucky."
                ],
                "High Score": [
                    "A new high score. Still won't get you a real racing license.",
                    "You beat your own low standard. Great job."
                ],
                "Building Momentum->Traffic Surgeon": [
                    "Going faster just to look fancy. Typical.",
                    "Surgical weaving. Sure, whatever helps you sleep."
                ],
                "Traffic Surgeon->Highway Wizard": [
                    "Now you're a 'wizard'. Hope your magic wand doesn't hit a bus.",
                    "Wizardry? Looks more like reckless driving to me."
                ],
                "Highway Wizard->Clutch Survival": [
                    "From magic to panic. That was fast.",
                    "Walking a tightrope. Hope you fall."
                ],
                "Clutch Survival->Recovery Phase": [
                    "Saved it. Unfortunately.",
                    "The run survives. Yay."
                ],
                "*->Recovery Phase": [
                    "Somehow, you didn't crash. Good job staying lucky.",
                    "Back to safety. Yawns all around."
                ],
                "*->Total Control": [
                    "Back to driving safely. Wake me when you crash.",
                    "Stabilized. Boring."
                ],
                "*->Clutch Survival": [
                    "Here comes the panic. Let's see if you choke.",
                    "Surviving by the skin of your teeth. Pitiful."
                ]
            }
        }

        # Voice mappings for the modes
        self.voices = {
            "sports": "Jasper",
            "narrator": "Hugo",
            "savage": "Kiki"
        }

        # Excitement level mappings for narrative states and transitions
        self.excitement_levels = {
            "game_start": "Calm",
            "Crash": "Hype",
            "Extreme Near Miss": "Hype",
            "Clutch Survival": "Hype",
            "Panic Driving": "Hype",
            "Traffic Chaos": "Hype",
            "High Risk Driving": "Hype",
            "High Combo": "Hype",
            "Elite Reactions": "Hype",
            "Untouchable": "Hype",
            "Dominant Run": "Hype",
            "Highway Wizard": "Excited",
            "Traffic Surgeon": "Excited",
            "Precision Driving": "Excited",
            "Flow State": "Excited",
            "Masterclass": "Calm",
            "Total Control": "Calm",
            "Controlled Aggression": "Excited",
            "Record Pace": "Excited",
            "Building Momentum": "Excited",
            "Traffic Weaving": "Excited",
            "Perfect Rhythm": "Calm",
            "Recovery Phase": "Calm",
            "High Score": "Excited",
            
            # Transition excitation levels
            "Building Momentum->Traffic Surgeon": "Excited",
            "Traffic Surgeon->Highway Wizard": "Excited",
            "Highway Wizard->Clutch Survival": "Hype",
            "Clutch Survival->Recovery Phase": "Calm",
            "*->Recovery Phase": "Calm",
            "*->Total Control": "Calm",
            "*->Clutch Survival": "Hype"
        }

    def generate(self, narrative_data: Dict[str, Any], mode: str = "sports", voice: str = None) -> Dict[str, Any]:
        self.turn_counter += 1
        mode = mode.lower()
        if mode not in self.templates:
            mode = "sports"

        # Check if we got a raw event-style dictionary or a NarrativeResult
        if "state" in narrative_data:
            state = narrative_data["state"]
            stats = narrative_data.get("stats", {})
            speed = stats.get("avg_speed", 0)
            combo = stats.get("combo_peak", 0)
            context_tags = narrative_data.get("context_tags", [])
        else:
            # Fallback wrapper for raw events
            state = narrative_data.get("event", "Masterclass")
            speed = int(narrative_data.get("speed", 0))
            combo = int(narrative_data.get("combo", 0))
            context_tags = []
            stats = {
                "avg_speed": speed,
                "combo_peak": combo,
            }

        # Check if we got a transition and try to find a transition pool
        transition = narrative_data.get("transition") if isinstance(narrative_data, dict) else None
        pool = None
        pool_name = None
        
        if transition:
            from_state = transition.get("from")
            to_state = transition.get("to")
            transition_key = f"{from_state}->{to_state}"
            wildcard_key = f"*->{to_state}"
            
            if transition_key in self.templates[mode]:
                pool_name = transition_key
                pool = self.templates[mode][transition_key]
            elif wildcard_key in self.templates[mode]:
                pool_name = wildcard_key
                pool = self.templates[mode][wildcard_key]

        if pool is None:
            # Normalize state names to keys in template pool
            pool_name = state
            if pool_name not in self.templates[mode]:
                # Try mapping legacy state names
                mapping = {
                    "near_miss": "High Risk Driving",
                    "extreme_near_miss": "Extreme Near Miss",
                    "overtake": "Building Momentum",
                    "multi_overtake": "Building Momentum",
                    "combo_milestone": "Clutch Survival",
                    "recovery": "Recovery Phase",
                    "traffic_weave": "Traffic Weaving",
                    "clean_streak": "Masterclass",
                    "speed_milestone": "Record Pace",
                    "high_score": "High Score",
                    "crash": "Crash",
                    "Total Control": "Total Control",
                    "Elite Reactions": "Elite Reactions",
                    "Clutch Survival": "Clutch Survival",
                    "Panic Driving": "Panic Driving",
                    "Traffic Chaos": "Traffic Chaos",
                    "High Risk Driving": "High Risk Driving",
                    "High Combo": "High Combo",
                    "Untouchable": "Untouchable",
                    "Dominant Run": "Dominant Run",
                    "Highway Wizard": "Highway Wizard",
                    "Traffic Surgeon": "Traffic Surgeon",
                    "Precision Driving": "Precision Driving",
                    "Flow State": "Flow State",
                    "Masterclass": "Masterclass",
                    "Controlled Aggression": "Controlled Aggression",
                    "Record Pace": "Record Pace",
                    "Building Momentum": "Building Momentum",
                    "Traffic Weaving": "Traffic Weaving",
                    "Perfect Rhythm": "Perfect Rhythm",
                    "Recovery Phase": "Recovery Phase"
                }
                pool_name = mapping.get(state, "Masterclass")
            pool = self.templates[mode].get(pool_name, self.templates[mode]["Masterclass"])

        # Select template with strict anti-repetition check (last 10 spoken lines global memory)
        selected_template = self._weighted_select_history(pool)

        # Format template
        formatted_commentary = selected_template.format(
            speed=speed,
            combo=combo,
            overtakes=stats.get("overtakes_in_window", 0),
            near_misses=stats.get("near_misses_in_window", 0),
            near_miss_count=stats.get("near_miss_count", stats.get("near_misses_in_window", 0)),
            traffic_density=stats.get("traffic_density", "low"),
            danger_level=stats.get("danger_level", "safe"),
            clean_driving_seconds=stats.get("clean_driving_seconds", 0.0),
            state_duration=round(narrative_data.get("state_duration", 0.0), 1) if isinstance(narrative_data, dict) else 0.0,
            score=narrative_data.get("total_score", stats.get("total_score", 0)),
            distance=stats.get("distance_survived", 0)
        )

        # Apply Commentator Memory prefix
        memory_prefix = ""
        if "pressure_rising" in context_tags:
            memory_prefix = "The pressure is rising now! "
        elif "masterclass_streak" in context_tags:
            memory_prefix = "This has been a masterclass in control! "
        
        final_commentary = memory_prefix + formatted_commentary

        # Voice assignment
        if voice is None:
            voice = self.voices.get(mode, "Jasper")

        # Determine excitement level
        excitement = self.excitement_levels.get(pool_name, "Calm")

        # Determine backend momentum label for compatibility
        momentum = "calm"
        if excitement == "Hype":
            momentum = "rising"
        elif excitement == "Calm" and pool_name == "Masterclass":
            momentum = "falling"

        # Update last 10 spoken lines cache
        self.last_10_spoken.append(selected_template)
        if len(self.last_10_spoken) > 10:
            self.last_10_spoken.pop(0)

        return {
            "commentary": final_commentary,
            "event_type": pool_name,
            "context_tags": context_tags,
            "momentum": momentum,
            "mode": mode,
            "pool_used": pool_name,
            "voice": voice,
            "excitement": excitement
        }

    def _weighted_select_history(self, pool: List[str]) -> str:
        # Filter pool against the last 10 spoken lines global history
        eligible_pool = [t for t in pool if t not in self.last_10_spoken]
        
        # Fallback if all templates in the pool were recently used (e.g. small pool)
        if not eligible_pool:
            eligible_pool = pool
            
        return random.choice(eligible_pool)
