import random
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class CommentaryEngine:
    def __init__(self):
        # Tracking recent history for anti-repetition
        # key: template string, value: turn counter when it was last used
        self.used_templates = {}
        self.turn_counter = 0
        self.cooldown_turns = 8

        # Define templates for each mode
        self.templates = {
            "sports": {
                "game_start": [
                    "Green light! We are underway on the RoadCaster highway!",
                    "And they're off! Let's see if this driver has what it takes!",
                    "Engine roaring, tires biting the asphalt, the journey begins!",
                    "The lights are green and we are live from the fastest highway on earth!",
                    "We're rolling! Fasten your seatbelts, this is going to be intense!"
                ],
                "near_miss": [
                    "INCREDIBLE reflexes! That was centimeters from disaster!",
                    "That gap barely existed and they STILL found a way through!",
                    "OH! The paint is trading between those two vehicles!",
                    "How did they get through that?! Absolutely outrageous!",
                    "The driver is living on the edge and LOVING it!",
                    "A hair's breadth away from a massive pile-up!",
                    "Talk about threading the needle! Magnificent car control!",
                    "He squeezed through! My word, that was close!",
                    "Unbelievable presence of mind to dodge that {vehicle}!",
                    "Absolute nerves of steel from the driver there!",
                    "The crowd is gasping! That was a coat of paint away from a crash!",
                    "Dodge of the day! How did he avoid that {vehicle}?!"
                ],
                "near_miss_truck": [
                    "Squeezing past a heavy TRUCK at these speeds! The courage is unreal!",
                    "That truck nearly swallowed them whole! What a dodge!",
                    "Dodging an absolute titan of the road! Brilliant reflexes!",
                    "They just shook hands with a semi-truck and walked away!"
                ],
                "near_miss_bus": [
                    "Slicing right past the commuter bus! That was way too close!",
                    "A massive bus in the way, but they slip past like a shadow!",
                    "My word, that bus almost ended the broadcast early!"
                ],
                "overtake": [
                    "A clean pass! Just leaves them in the dust!",
                    "Overtakes another one! Smooth as silk!",
                    "Cruising past the traffic, making it look easy!",
                    "Another vehicle neutralized! The driver is on a mission!",
                    "Beautifully executed overtake there!",
                    "Just flies past! The speed difference is massive!",
                    "Leaving traffic behind like they're standing still!"
                ],
                "multi_overtake": [
                    "Triple overtake! The driver is CARVING through traffic!",
                    "Three vehicles beaten in seconds! This is championship driving!",
                    "A flurry of passes! Absolute mastery on the highway!",
                    "They are slicing through traffic like a hot knife through butter!"
                ],
                "combo_milestone": [
                    "A combo of {combo}! The driver is in absolute FLOW state!",
                    "Double digits on the combo! This is historic driving!",
                    "Five near misses in a row! The driver is untouchable right now!",
                    "Unstoppable! {combo} straight close calls and the crowd is going wild!"
                ],
                "speed_milestone": [
                    "Breaking past {speed} km/h! This is territory for the brave!",
                    "The speedometer is screaming! {speed} km/h and rising!",
                    "We have entered hyperspeed! Absolute rocketship pace!",
                    "Crossing {speed} km/h! The scenery is just a blur now!"
                ],
                "clean_streak": [
                    "Cruising along nicely. A brief moment of calm on the highway.",
                    "A clean run so far. The driver is picking their battles wisely.",
                    "Showing some mature driving here, keeping a safe distance for now."
                ],
                "traffic_weave": [
                    "Left, right, left! That is a masterclass in traffic weaving!",
                    "Weaving through lanes like a professional slalom driver!",
                    "A rapid-fire slalom! The agility of this car is breathtaking!"
                ],
                "recovery": [
                    "Double trouble! A near-crash followed by another immediate dodge!",
                    "Saved it! Recovered from one near-miss and executed another!",
                    "Unbelievable recovery! Evasion after evasion!"
                ],
                "high_score": [
                    "NEW HIGH SCORE! The driver is rewriting the history books!",
                    "History is made! A new benchmark has been set!",
                    "Unprecedented heights! They've just beaten the record!"
                ],
                "crash": [
                    "And that's the end of the line! What a run it was!",
                    "Contact! The incredible run comes to a dramatic end!",
                    "A devastating crash! The physics engine wins this round!",
                    "Oh! A catastrophic collision! That's game over folks!",
                    "Smash! The highway finally claims its victim. What a spectacle!"
                ]
            },
            "narrator": {
                "game_start": [
                    "Under the shadow of the night, the engine ignites.",
                    "The highway stretch lies ahead, dark and unforgiving.",
                    "A lone driver starts the ignition. The asphalt awaits.",
                    "The journey begins in silence, but the speed will speak.",
                    "Into the neon-lit abyss we go."
                ],
                "near_miss": [
                    "At this speed, every decision is life or death.",
                    "The highway refuses to show mercy, but the driver refuses to stop.",
                    "Another inch. Another heartbeat. Another escape.",
                    "A dance with gravity, won by a fraction of a second.",
                    "The gap was narrow. The survival, narrower.",
                    "A close encounter with fate, resolved in milliseconds.",
                    "Death whispered, but the driver didn't listen.",
                    "A brushes-with-death simulator, played out in real time.",
                    "The metal groaned, but the path remained clear."
                ],
                "near_miss_truck": [
                    "The steel behemoth almost crushed the dream, but they slipped by.",
                    "Dangling in the blind spot of a giant, they find escape."
                ],
                "near_miss_bus": [
                    "A wall of glass and steel avoided. Barely."
                ],
                "overtake": [
                    "Another soul left behind in the dark.",
                    "A silent pass in the night.",
                    "The taillights of others fade into the background.",
                    "Progress is measured in the headlights left behind."
                ],
                "multi_overtake": [
                    "They are moving through the traffic like a ghost.",
                    "Three cars passed. The momentum is undeniable.",
                    "A sequence of execution. Perfect. Precise."
                ],
                "combo_milestone": [
                    "A streak of {combo}. Evasion has become second nature.",
                    "Ten close calls. A testament to absolute focus.",
                    "They are defying the odds, one close call at a time."
                ],
                "speed_milestone": [
                    "The speed dials up to {speed}. The risk grows exponentially.",
                    "At {speed} km/h, the highway becomes a tunnel of light."
                ],
                "clean_streak": [
                    "A temporary peace. The calm before the storm.",
                    "For a moment, the road is quiet."
                ],
                "traffic_weave": [
                    "Rapid lane shifts. A kinetic symphony."
                ],
                "recovery": [
                    "Chaos compound. One near miss morphs into another."
                ],
                "high_score": [
                    "A new record. They have pushed past the known limits."
                ],
                "crash": [
                    "The highway always wins. In the end.",
                    "A flash of chrome, a screech of tires, and then... silence.",
                    "The run ends as all fast runs must: in spectacular ruin.",
                    "An abrupt end to a beautiful defiance."
                ]
            },
            "savage": {
                "game_start": [
                    "Oh good, another driver who thinks they're in a movie.",
                    "Let's see how long it takes to turn this car into scrap metal.",
                    "Starting a fresh run. The local body shops are excited.",
                    "We are live. Place your bets on when the crash happens."
                ],
                "near_miss": [
                    "The insurance company has officially stopped watching.",
                    "Several traffic laws are now filing for emotional distress.",
                    "Nice dodge. Don't get cocky, it was 90% luck.",
                    "Are we driving or trying to test the air bags?",
                    "That was close enough to smell the other driver's cologne.",
                    "A spectacular display of physics-defying stupidity.",
                    "Almost a hood ornament! Try that again, I dare you.",
                    "If you wanted to die, there are less expensive ways.",
                    "The grim reaper is currently checking his watch.",
                    "Close! But unfortunately for the viewers, you survived."
                ],
                "near_miss_truck": [
                    "Almost got squashed like a bug by that semi. Cute.",
                    "Trying to play chicken with a multi-ton truck. Bold strategy."
                ],
                "near_miss_bus": [
                    "That bus nearly became your permanent address.",
                    "Almost passenger of the month on that public transport!"
                ],
                "overtake": [
                    "Passing granny in the slow lane. Groundbreaking.",
                    "Wow, you overtook a car. Give yourself a medal.",
                    "Another vehicle left wondering who taught you how to drive.",
                    "Look at you go, overtaking traffic like a real driver."
                ],
                "multi_overtake": [
                    "Look at the zigzag champion go. Calm down, Vin Diesel.",
                    "Passing three cars at once. Show-off."
                ],
                "combo_milestone": [
                    "A combo of {combo}. You're really stretching your guardian angel's patience.",
                    "Double digit combo. The collision is going to be hilarious when it happens."
                ],
                "speed_milestone": [
                    "Doing {speed} km/h? Your parents must be so proud.",
                    "At {speed} km/h, your insurance premium just reached escape velocity."
                ],
                "clean_streak": [
                    "Boring. Where are the close calls? I'm falling asleep here.",
                    "A whole 10 seconds of sensible driving. Who are you and what did you do with the driver?"
                ],
                "traffic_weave": [
                    "Weaving like a drunk driver at a slalom event."
                ],
                "recovery": [
                    "Two near misses? Double the luck, zero the skill."
                ],
                "high_score": [
                    "New high score. Great, now you'll never stop playing."
                ],
                "crash": [
                    "Well, physics wins again. Who saw that coming? Everyone.",
                    "And that, ladies and gentlemen, is why we have seatbelts.",
                    "Beautifully done. The car is now a modern art installation.",
                    "Game over. The towing company is on the way.",
                    "A crash at that speed? Yep, that'll buff right out."
                ]
            }
        }

        # Voice mappings for the modes
        self.voices = {
            "sports": "Jasper",
            "narrator": "Hugo",
            "savage": "Kiki"
        }

    def generate(self, event_data: Dict[str, Any], mode: str = "sports") -> Dict[str, Any]:
        self.turn_counter += 1
        mode = mode.lower()
        if mode not in self.templates:
            mode = "sports"

        event = event_data.get("event", "overtake")
        speed = int(event_data.get("speed", 0))
        combo = int(event_data.get("combo", 0))
        vehicle_type = event_data.get("vehicle_type", "car").lower()
        distance = event_data.get("distance", 0.5)

        # Build context tags
        context_tags = []
        if speed > 150:
            context_tags.append("high_speed")
        if speed > 200:
            context_tags.append("extreme_speed")
        if event_data.get("traffic_density") == "high":
            context_tags.append("heavy_traffic")
        if combo >= 10:
            context_tags.append("combo_10")
        elif combo >= 5:
            context_tags.append("combo_5")
        if event_data.get("is_high_score"):
            context_tags.append("high_score")

        # Determine momentum
        recent_events = event_data.get("recent_events", [])
        exciting_events = {"near_miss", "multi_overtake", "recovery", "traffic_weave"}
        exciting_count = sum(1 for e in recent_events[-3:] if e in exciting_events)
        if exciting_count >= 2:
            momentum = "rising"
        elif exciting_count == 0:
            momentum = "falling"
        else:
            momentum = "calm"

        # Determine which template pool to use
        pool_name = event
        
        # Override pool based on specific context for near misses
        if event == "near_miss":
            if vehicle_type == "truck" and f"near_miss_truck" in self.templates[mode]:
                pool_name = "near_miss_truck"
            elif vehicle_type == "bus" and f"near_miss_bus" in self.templates[mode]:
                pool_name = "near_miss_bus"

        # Safe fallback if pool doesn't exist
        if pool_name not in self.templates[mode]:
            pool_name = "near_miss" if "near" in pool_name else "overtake"
            if pool_name not in self.templates[mode]:
                pool_name = list(self.templates[mode].keys())[0]

        pool = self.templates[mode][pool_name]

        # Select template with anti-repetition weighted check
        selected_template = self._weighted_select(pool)

        # Format template
        formatted_commentary = selected_template.format(
            vehicle=vehicle_type,
            speed=speed,
            combo=combo,
            score=event_data.get("total_score", 0),
            distance=int(event_data.get("distance_survived", 0))
        )

        # Voice assignment
        voice = self.voices.get(mode, "Jasper")

        return {
            "commentary": formatted_commentary,
            "event_type": event,
            "context_tags": context_tags,
            "momentum": momentum,
            "mode": mode,
            "pool_used": pool_name,
            "voice": voice
        }

    def _weighted_select(self, pool: List[str]) -> str:
        weights = []
        for t in pool:
            # Check if template is on cooldown
            last_used = self.used_templates.get(t, -9999)
            turns_since_use = self.turn_counter - last_used
            
            if turns_since_use < self.cooldown_turns:
                # Apply heavy penalty to cooldown templates
                weights.append(0.05)
            else:
                weights.append(1.0)

        # Select based on weights
        chosen = random.choices(pool, weights=weights, k=1)[0]
        
        # Update cooldown
        self.used_templates[chosen] = self.turn_counter
        return chosen
