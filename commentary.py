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
        self.cooldown_turns = 6

        # Define templates for each mode and narrative state
        self.templates = {
            "sports": {
                "game_start": [
                    "Green light! We are underway on the RoadCaster highway!",
                    "And they're off! Let's see if this driver has what it takes!",
                    "Engine roaring, tires biting the asphalt, the journey begins!",
                    "The lights are green and we are live from the fastest highway on earth!",
                    "We're rolling! Fasten your seatbelts, this is going to be intense!"
                ],
                "crash": [
                    "And that's the end of the line! What a run it was!",
                    "Contact! The incredible run comes to a dramatic end!",
                    "A devastating crash! The physics engine wins this round!",
                    "Oh! A catastrophic collision! That's game over folks!",
                    "Smash! The highway finally claims its victim. What a spectacle!"
                ],
                "TRAFFIC_CHAOS": [
                    "This is absolute CHAOS on the highway! Evasions left and right!",
                    "The traffic density is off the charts! How are they surviving this?",
                    "Unbelievable traffic chaos! The driver is dodging cars like a madman!",
                    "Absolute madness! It's a miracle they haven't crashed yet!"
                ],
                "HIGH_RISK_DRIVING": [
                    "They are playing with fire! High speed near misses at {speed} km/h!",
                    "That is high-risk, high-reward driving! The adrenaline must be pumping!",
                    "Threading the needle at {speed} km/h! Absolutely fearless!",
                    "High velocity, high danger! This is incredibly tense!"
                ],
                "CLUTCH_PERFORMANCE": [
                    "A masterclass in reflexes! A peak combo of {combo} close calls!",
                    "A combo of {combo}! The driver is in an absolute flow state!",
                    "Incredible clutch play! That's {combo} consecutive close shaves!",
                    "Unstoppable flow! That is a massive combo of {combo}!"
                ],
                "AGGRESSIVE_DRIVING": [
                    "Carving through traffic! Overtaking everything in the blink of an eye!",
                    "The driver is on an absolute tear, slicing through the slow lanes!",
                    "Making aggressive passes left and right, leaving traffic in the dust!",
                    "Absolutely dominant driving! Just slicing through the pack!"
                ],
                "BUILDING_MOMENTUM": [
                    "The pace is ramping up, and the momentum is clearly building!",
                    "Finding the rhythm now! Overtakes and dodges working in perfect harmony!",
                    "Starting to cook! The driver is warming up on this stretch!",
                    "Building speed and confidence with every passing second."
                ],
                "RECORD_PACE": [
                    "Cruising at record pace! Pushing {speed} km/h on a clean run!",
                    "Blistering speed! {speed} km/h and making it look like a walk in the park!",
                    "This is championship pace! Absolutely flying down the asphalt!",
                    "Setting the road on fire! The speedometer is screaming!"
                ],
                "RECOVERY_PHASE": [
                    "A breath of fresh air after a near-disaster. Great job to stabilize!",
                    "A crucial recovery. The driver cools things down and regains control.",
                    "Excellent composure to recover from that chaotic sequence.",
                    "Disaster averted! The driver successfully resets their focus."
                ],
                "TOTAL_CONTROL": [
                    "Total control. A clean driving masterclass by this driver.",
                    "Smooth, clean, and clinical. That is how you dominate the highway.",
                    "No mistakes, pure execution. A master at work.",
                    "A clinic in precision driving. Not a single scratch on the paint."
                ],
                "CALM_CRUISING": [
                    "Cruising along the highway, waiting for the next opportunity.",
                    "A temporary lull in the traffic. A chance to prepare for what lies ahead.",
                    "A smooth, steady cruise on the open asphalt.",
                    "Just settling in. Enjoying the hum of the engine on this stretch."
                ]
            },
            "narrator": {
                "game_start": [
                    "Under the shadow of the day, the engine ignites.",
                    "The highway stretch lies ahead, open and unforgiving.",
                    "A lone driver starts the ignition. The asphalt awaits.",
                    "The journey begins in silence, but the speed will speak.",
                    "Into the vast horizon we go."
                ],
                "crash": [
                    "The highway always wins. In the end.",
                    "A flash of chrome, a screech of tires, and then... silence.",
                    "The run ends as all fast runs must: in spectacular ruin.",
                    "An abrupt end to a beautiful defiance."
                ],
                "TRAFFIC_CHAOS": [
                    "Chaos surrounds them. The metal giants close in, yet the path remains.",
                    "Surrounded by moving walls. Every direction is a hazard.",
                    "The road is alive with movement, testing the limits of survival.",
                    "A storm of steel and exhaust. A test of pure instinct."
                ],
                "HIGH_RISK_DRIVING": [
                    "At {speed} km/h, the line between brave and foolish disappears.",
                    "Velocity increases. Risk expands. Evasion becomes a necessity.",
                    "Brushing past disaster at {speed} km/h. A dance with the void.",
                    "The speedometer rises, and with it, the gravity of every move."
                ],
                "CLUTCH_PERFORMANCE": [
                    "A streak of {combo}. Evasion has become second nature.",
                    "A peak of {combo} close calls. A testament to absolute focus.",
                    "Defying the odds, {combo} times over."
                ],
                "AGGRESSIVE_DRIVING": [
                    "They move through traffic like a ghost in the daylight.",
                    "A sequence of execution. Slicing past one, then another.",
                    "The mirrors fill with those left behind. Progress is swift."
                ],
                "BUILDING_MOMENTUM": [
                    "The rhythm is established. The pace quickens.",
                    "A quiet confidence builds. The driver is finding their flow.",
                    "Energy builds. The highway responds to the driver's intent."
                ],
                "RECORD_PACE": [
                    "Flying at {speed} km/h. The world outside is a blur of colors.",
                    "Unmatched speed. Unbroken focus. The road belongs to them.",
                    "Testing the physical limits of the machine at {speed} km/h."
                ],
                "RECOVERY_PHASE": [
                    "The storm passes. The heartbeat slows. Order returns.",
                    "A critical escape. The driver breathes and resets.",
                    "Composure is regained in the aftermath of chaos."
                ],
                "TOTAL_CONTROL": [
                    "A clean line. A silent masterclass in precision.",
                    "Total control. The car is an extension of the mind.",
                    "No wasted motion. Pure, unadulterated execution."
                ],
                "CALM_CRUISING": [
                    "A temporary peace. The calm before the next storm.",
                    "For a moment, the road is quiet.",
                    "Steady progress. The highway stretches out, peaceful."
                ]
            },
            "savage": {
                "game_start": [
                    "Oh good, another driver who thinks they're in a movie.",
                    "Let's see how long it takes to turn this car into scrap metal.",
                    "Starting a fresh run. The local body shops are excited.",
                    "We are live. Place your bets on when the crash happens."
                ],
                "crash": [
                    "Well, physics wins again. Who saw that coming? Everyone.",
                    "And that, ladies and gentlemen, is why we have seatbelts.",
                    "Beautifully done. The car is now a modern art installation.",
                    "Game over. The towing company is on the way.",
                    "A crash at that speed? Yep, that'll buff right out."
                ],
                "TRAFFIC_CHAOS": [
                    "Look at this mess. You're basically playing pinball with real cars.",
                    "Are you trying to dodge traffic or collect insurance payouts?",
                    "Traffic chaos! Try not to hit the side of a bus, okay?",
                    "Absolute disaster area. Your driver's license should be archived."
                ],
                "HIGH_RISK_DRIVING": [
                    "Doing {speed} km/h and dodging cars? Your insurance company is crying.",
                    "High-risk driving. I hope you signed your organ donor card.",
                    "Squeezing through gaps at {speed} km/h. Bold choice, let's see if it pays off.",
                    "At this speed, you're one sneeze away from a spectacular bonfire."
                ],
                "CLUTCH_PERFORMANCE": [
                    "A combo of {combo}? Cute. Your guardian angel deserves a raise.",
                    "Peak combo of {combo}. Don't get cocky, it was 90% luck.",
                    "You dodged {combo} cars in a row? Who wrote this script?"
                ],
                "AGGRESSIVE_DRIVING": [
                    "Aggressive passes. Calm down, Vin Diesel, it's just traffic.",
                    "Overtaking left and right. Are we in a rush to get to a red light?",
                    "Slicing through traffic. You're really trying hard to look cool, huh?"
                ],
                "BUILDING_MOMENTUM": [
                    "Oh look, we're actually making progress. Don't ruin it.",
                    "Momentum is building. Let's see how fast you can mess this up.",
                    "Ramping up the speed. The tow truck driver is putting his boots on."
                ],
                "RECORD_PACE": [
                    "Record pace at {speed} km/h? Hope the police aren't watching.",
                    "Flying at {speed} km/h. If you crash now, they'll need a shovel, not a tow truck.",
                    "Speeding down the highway. Groundbreaking stuff here."
                ],
                "RECOVERY_PHASE": [
                    "Wow, you actually saved it. I'm almost disappointed.",
                    "Look who managed to not crash after that mess. Impressive.",
                    "A successful recovery. Back to the boring cruising state, I guess."
                ],
                "TOTAL_CONTROL": [
                    "Total control. Boring! Bring back the near misses!",
                    "A clean streak. Did you forget where the accelerator pedal is?",
                    "Driving normally. Very exciting. Ten out of ten."
                ],
                "CALM_CRUISING": [
                    "Boring. Where are the close calls? I'm falling asleep here.",
                    "A whole stretch of sensible driving. Absolutely thrilling.",
                    "Just cruising. Slower than my grandma on a Sunday morning."
                ]
            }
        }

        # Voice mappings for the modes
        self.voices = {
            "sports": "Jasper",
            "narrator": "Hugo",
            "savage": "Kiki"
        }

    def generate(self, narrative_data: Dict[str, Any], mode: str = "sports") -> Dict[str, Any]:
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
            # Fallback wrapper for raw events (e.g. crash, game_start)
            state = narrative_data.get("event", "CALM_CRUISING")
            speed = int(narrative_data.get("speed", 0))
            combo = int(narrative_data.get("combo", 0))
            context_tags = []
            stats = {
                "avg_speed": speed,
                "combo_peak": combo,
                "overtakes_in_window": 1 if state in ("overtake", "multi_overtake") else 0,
                "near_misses_in_window": 1 if state in ("near_miss", "recovery") else 0,
            }

        # Safe fallback if pool doesn't exist
        pool_name = state
        if pool_name not in self.templates[mode]:
            # Try mapping raw event names to narrative states
            if "near" in pool_name or pool_name == "recovery":
                pool_name = "HIGH_RISK_DRIVING"
            elif pool_name in ("overtake", "multi_overtake", "traffic_weave"):
                pool_name = "AGGRESSIVE_DRIVING"
            elif pool_name == "game_start":
                pool_name = "game_start"
            elif pool_name == "crash":
                pool_name = "crash"
            else:
                pool_name = "CALM_CRUISING"

        pool = self.templates[mode][pool_name]

        # Select template with anti-repetition weighted check
        selected_template = self._weighted_select(pool)

        # Format template
        formatted_commentary = selected_template.format(
            speed=speed,
            combo=combo,
            overtakes=stats.get("overtakes_in_window", 0),
            near_misses=stats.get("near_misses_in_window", 0),
            score=narrative_data.get("total_score", stats.get("total_score", 0)),
            distance=stats.get("distance_survived", 0)
        )

        # Voice assignment
        voice = self.voices.get(mode, "Jasper")

        # Determine backend momentum label for frontend compatibility
        momentum = "calm"
        if state in ("TRAFFIC_CHAOS", "HIGH_RISK_DRIVING", "AGGRESSIVE_DRIVING", "CLUTCH_PERFORMANCE"):
            momentum = "rising"
        elif state == "CALM_CRUISING":
            momentum = "falling"

        return {
            "commentary": formatted_commentary,
            "event_type": state,
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
