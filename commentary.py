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
                    "The lights are green and we are live from the fastest highway on earth!",
                    "A clean start! Time to see if they can build some real momentum!",
                    "And the driver starts the run! The crowd is electric!"
                ],
                "Crash": [
                    "OH NO! A COLLISION! THE CAR IS IN RUINS! GAME OVER!",
                    "DEVASTATING COLLISION! Absolute catastrophe on the highway!",
                    "SMASH! The physics engine wins this round! A dramatic end to the run!",
                    "OH! A catastrophic pile-up! That is the end of the broadcast!",
                    "AND HE'S OUT! HE HITS THE VEHICLE AT SPEED! SPECTACULAR DESTRUCTION!",
                    "WHAT A SMASH! The car is absolutely pulverized! The run is over!",
                    "CRASHED! Screeching tires, flying debris, and the dream ends in steel!",
                    "ABSOLUTE CARNAGE! The vehicle is wrecked! A devastating crash!"
                ],
                "Extreme Near Miss": [
                    "GOOD HEAVENS! THAT WAS CENTIMETERS FROM AN ABSOLUTE DISASTER!",
                    "OH! THEY TRADED PAINT! Absolute heart-in-mouth moment!",
                    "INCHES FROM DISASTER! That gap barely existed and they STILL found a way through!",
                    "HOLY MOLY! How did they dodge that?! Absolute nerves of steel!",
                    "UNBELIEVABLE REFLEXES! He squeezed past with only a millimeter to spare!",
                    "THAT IS BEYOND BELIEF! Dodging that car at speed was absolute wizardry!",
                    "SPARKS ARE FLYING! Squeezing the boundaries of physics on that pass!",
                    "THAT WAS INCHES FROM A CATASTROPHIC COLLISION! What a dodge!"
                ],
                "Clutch Survival": [
                    "HE'S DEFYING GRAVITY! THREE NEAR MISSES IN A ROW! HOW IS HE ALIVE?!",
                    "OH MY WORD! THEY ARE TAKING BIGGER AND BIGGER RISKS OUT THERE!",
                    "UNBELIEVABLE EVASIONS! A peak combo of {combo}! The crowd is going wild!",
                    "ABSOLUTE FLOW STATE! {combo} consecutive close shaves! My heart is pounding!",
                    "CLUTCH ESCAPE! Evasions left and right under extreme pressure!",
                    "HOW DID HE SURVIVE THAT PACK?! Absolute clutch survival at its best!",
                    "RISKING IT ALL! Peak combo of {combo}! They are living on a knife-edge!",
                    "UNSTOPPABLE FLOW! Slicing through danger like a shadow!"
                ],
                "Panic Driving": [
                    "THE DRIVER IS TRAPPED! DENSE TRAFFIC AND THE PACE IS SLOWING DOWN!",
                    "HE'S SWERVING ERRATICALLY! The pressure is clearly getting to them!",
                    "PANIC DRIVING IN THE SLOW LANE! Trying to find a way out of this congestion!",
                    "TOO DENSE! The driver is swerving, trying to avoid being boxed in!",
                    "THE GAP IS CLOSING! Congested traffic is forcing erratic maneuvers!",
                    "RISKY SLOW MOVES! They're struggling to find clean air in this density!"
                ],
                "Traffic Chaos": [
                    "THE ROAD IS TURNING INTO COMPLETE CHAOS!",
                    "TRAFFIC IS CONGESTING BUT THE SPEED IS NOT DROPPING! THIS IS MADNESS!",
                    "GOOD HEAVENS! THE HIGHWAY IS IN COMPLETE CHAOS AND THE DRIVER IS TEARING IT TO PIECES!",
                    "Cars everywhere, engines screaming, the driver is carving them up!",
                    "ABSOLUTE CHAOS OUT THERE! Redlining the engine in heavy traffic!",
                    "THIS IS MADNESS! Cars to the left, cars to the right, absolute traffic congestion!",
                    "THE ROAD IS A WAR ZONE! But the driver refuses to lift the accelerator!",
                    "CONGESTION AT SPEED! Threading through high-density traffic like a madman!"
                ],
                "High Risk Driving": [
                    "THAT WAS INCHES FROM DISASTER AT {speed} KM/H!",
                    "THEY ARE PLAYING WITH FIRE AT THESE SPEEDS! Absolutely wild!",
                    "Squeezing through gaps at {speed} km/h! Living on the edge!",
                    "Risk level: MAXIMUM! They are dancing with the guardrails!",
                    "BLISTERING SPEED AND NEAR MISSES! A recipe for adrenaline!",
                    "HE IS LIVING DANGEROUSLY! Slicing past traffic at {speed} km/h!",
                    "NO ROOM FOR ERROR! That near miss at high speed was absolute insanity!",
                    "ONE MISTAKE AND IT'S OVER! Fearless driving at {speed} km/h!"
                ],
                "High Combo": [
                    "TEN CLEAN EVASIONS IN A ROW! ABSOLUTELY FLYING!",
                    "THE MOMENTUM IS UNSTOPPABLE! A massive combo of {combo}!",
                    "DANCING THROUGH TRAFFIC! A combo of {combo} close calls!",
                    "UNTOUCHABLE FLOW! Slicing past {combo} vehicles without a scratch!",
                    "THE COMBO COUNTER IS ON FIRE! Peak combo of {combo} reached!",
                    "ABSOLUTE MAGIC! Threading {combo} near misses in a row!"
                ],
                "Untouchable": [
                    "TRAFFIC CANNOT SEEM TO SLOW THEM DOWN! THEY ARE UNTOUCHABLE!",
                    "THEY HAVE AN ANSWER FOR EVERYTHING THE ROAD THROWS AT THEM!",
                    "THIS RUN IS REACHING ANOTHER LEVEL! Absolutely untouchable driving!",
                    "THE SCENERY IS A BLUR AND THE VEHICLES ARE STANDING STILL!",
                    "THEY ARE PLAYING A DIFFERENT GAME! Absolutely untouchable on this highway!",
                    "NO ONE CAN TOUCH THEM! car is carving through traffic with absolute ease!"
                ],
                "Dominant Run": [
                    "AN ABSOLUTELY DOMINANT RUN! Carving through the slower pack at {speed} km/h!",
                    "THEY ARE DOMINATING THE ASPHALT! {overtakes} passes in the last 15 seconds!",
                    "A SHOW OF ABSOLUTE DOMINANCE! Just leaving everyone in the dust!",
                    "THE DRIVER IS ON A Tear! Dominating every lane of this highway!",
                    "CHAMPIONSHIP PERFORMANCE! Total dominance of speed and control!",
                    "THEY ARE IN A LEAGUE OF THEIR OWN! Slicing through traffic like a laser!"
                ],
                "Highway Wizard": [
                    "A HIGHWAY WIZARD! Weaving and passing like a professional slalom driver!",
                    "ABSOLUTE WIZARD IN ACTION! Left, right, pass! Spellbinding car control!",
                    "THEY ARE CASTING A SPELL ON the ROAD! Beautiful weaving and overtakes!",
                    "MAGIC ON THE ASPHALT! Weaving through lanes and passing vehicles effortlessly!",
                    "WIZARD CLASS DRIVING! That slalom pass sequence was breathtaking!",
                    "HE'S PLAYING WITH THE TRAFFIC! Left, right, pass! Absolute highway wizard!"
                ],
                "Traffic Surgeon": [
                    "THE DRIVER IS THREADING THROUGH TRAFFIC BEAUTIFULLY!",
                    "THEY'RE FINDING GAPS THAT BARELY EXIST! Clinical traffic surgery!",
                    "THIS IS PRECISION DRIVING AT ITS FINEST! Slicing cleanly through lanes!",
                    "SURGICAL PRECISION! Cutting through the field without a single mistake!",
                    "THE GAPS ARE MINISCULE BUT THE SURGEON FINDS A WAY!",
                    "CLINICAL WORK! Lane changes and passes executed with absolute precision!"
                ],
                "Precision Driving": [
                    "A MASTERCLASS IN PRECISION DRIVING! Clean passes and perfect lines!",
                    "NO WASTED MOTION! Precision lane changes and clean driving!",
                    "MAKING IT LOOK EFFORTLESS! Pure precision on this stretch!",
                    "CLINICAL AND CLEAN! Every weave and pass executed beautifully!",
                    "THE PAINT IS NOT EVEN SCRATCHED! That is precision driving at its best!",
                    "PRACTICE MAKES PERFECT! A display of pure driving precision!"
                ],
                "Flow State": [
                    "EVERYTHING IS CLICKING RIGHT NOW! The driver is in flow state!",
                    "THE DRIVER IS OPERATING ON INSTINCT! It all looks effortless!",
                    "IT ALL LOOKS EFFORTLESS! Absolute flow state on the RoadCaster highway!",
                    "IN THE ZONE! Every decision, every swerve, completely locked in!",
                    "PURE INSTINCT! The driver and the machine are working as one!",
                    "THEY ARE FLOATING ON THE ASPHALT! Everything is clicking beautifully!"
                ],
                "Masterclass": [
                    "THIS IS BECOMING A MASTERCLASS IN HIGHWAY CONTROL!",
                    "EVERY DECISION IS THE RIGHT ONE! Locked in masterclass driving!",
                    "THE DRIVER LOOKS COMPLETELY LOCKED IN! A master at work!",
                    "A CLINICAL TUTORIAL ON CONTROL! Not a single mistake for 25 seconds!",
                    "THE SCENERY FAINTS BEHIND! Complete mastery of the highway!",
                    "UNPRECEDENTED FOCUS! Writing the manual on high-speed car control!"
                ],
                "Controlled Aggression": [
                    "CONTROLLED AGGRESSION! Slicing through traffic with confidence!",
                    "AGAINST THE FIELD! Aggressive passes but keeping it completely clean!",
                    "THEY'RE PUSHING THE VEHICLE! Controlled aggression at its best!",
                    "BOLD BUT CLINICAL! {overtakes} passes without a single near miss!",
                    "THE DRIVER IS DRIVING ON AN ABSOLUTE tear but keeping it clean!",
                    "AGGRESSIVE PASSES BUT TOTAL CONTROL! Leaving traffic behind!"
                ],
                "Record Pace": [
                    "RECORD-BREAKING VELOCITY! Flying at {speed} km/h!",
                    "THE SPEEDOMETER IS SCREAMING! Record pace on this stretch!",
                    "SCORES LIKE A ROCKET SCREECHING IN THE SKY! Record speed!",
                    "BLISTERING SPEED! The scenery is just a blur at {speed} km/h!"
                ],
                "Building Momentum": [
                    "THE CONFIDENCE IS GROWING! The pace keeps increasing!",
                    "THE PACE KEEPS INCREASING! Building something special here!",
                    "THEY ARE BUILDING MOMENTUM! Ramping up the velocity and passing cars!",
                    "MOMENTUM IS ON THE RISE! The hum of the engine is intensifying!"
                ],
                "Traffic Weaving": [
                    "THEY'RE WEAVING BEAUTIFULLY THROUGH TRAFFIC!",
                    "WEAVING THROUGH THE FIELD! Left, right, left slaloms!",
                    "A SPECTACULAR SLALOM SEQUENCE! Agility of the car is outstanding!",
                    "WEAVING LEFT, WEAVING RIGHT! Car control is absolutely spellbinding!"
                ],
                "Perfect Rhythm": [
                    "IN PERFECT RHYTHM! Every lane shift and pass working beautifully!",
                    "THE DRIVER HAS FOUND THE RHYTHM! Hum of the tires, zoom of the passes!",
                    "A PERFECT CONCERT OF PASSING AND WEAVING! Completely in rhythm!",
                    "RHYTHM AND SPEED WORKING IN HARMONY! Effortless progress!"
                ],
                "Recovery Phase": [
                    "WHAT A SAVE! Composure restored after a near-disaster!",
                    "DISASTER AVERTED! Composure regained and control re-established!",
                    "EXCELLENT COMPOUND REFLEXES! What a save to get out of that jam!",
                    "REGAINED CONTROL! The driver resets their focus and stabilizes!"
                ],
                "High Score": [
                    "NEW HIGH SCORE! The driver is rewriting the history books!",
                    "HISTORY IS MADE! A new benchmark has been set!",
                    "UNPRECEDENTED HEIGHTS! They've just beaten the record!"
                ],
                "Elite Reactions": [
                    "WHAT SPECTACULAR REACTIONS! Squeezing through with lightning-fast speed!",
                    "THE REFLEXES ON THIS DRIVER! Absolutely cat-like reactions!",
                    "INHERENT REFLEXES! He reacted in a fraction of a second!",
                    "AN EXHIBITION OF INSTINCT! Superb reaction time from the driver!",
                    "ELITE LEVEL REFLEXES! That was pure muscle memory in action!",
                    "OH! DANCING ON A RAZOR BLADE! A combo of {combo} and reflexes from another planet!",
                    "INCREDIBLE! HE DODGES AGAIN! The synapses are firing at warp speed!"
                ],
                "Total Control": [
                    "THIS IS A DEMONSTRATION OF TOTAL CONTROL! Absolutely flawless driving!",
                    "THE DRIVER IS DICTATING THE TERMS! Total control of the vehicle!",
                    "Flawless execution! They have complete command of this highway!",
                    "No mistakes, no panic. Just absolute, total control at {speed} km/h!",
                    "A MASTERCLASS IN MOTION! Total control for {clean_driving_seconds} seconds!",
                    "THE CAR IS AN EXTENSION OF HIS BODY! Spellbinding highway control!"
                ],
                "Building Momentum->Traffic Surgeon": [
                    "The confidence is growing now! Threading through lanes like a pro!",
                    "Excellent transition! Building momentum has led to clinical traffic surgery!"
                ],
                "Traffic Surgeon->Highway Wizard": [
                    "They are finding gaps that barely exist! Total highway wizardry!",
                    "Surgical precision has turned into complete wizardry on the asphalt!"
                ],
                "Highway Wizard->Clutch Survival": [
                    "They are taking bigger and bigger risks! Inches from disaster!",
                    "Agility turns to extreme danger! They are walking a tightrope now!"
                ],
                "Clutch Survival->Recovery Phase": [
                    "What a save! The run survives!",
                    "HE SURVIVED! disaster averted, the driver resets their focus!"
                ],
                "*->Recovery Phase": [
                    "Crisis resolved! Composure regained after a highly intense sequence!",
                    "What a spectacular recovery to stay alive! Splendid driving!"
                ],
                "*->Total Control": [
                    "Total control established! After {state_duration} seconds of volatility, they have completely stabilized!",
                    "A return to complete control! The driver is looking absolutely locked in!"
                ],
                "*->Clutch Survival": [
                    "Danger levels spiking! They are dodging multiple close calls in a row!",
                    "High pressure evasion! How on earth are they squeezing through?!"
                ]
            },
            "narrator": {
                "game_start": [
                    "A lone driver starts the ignition. The asphalt awaits.",
                    "Into the neon-lit abyss we go.",
                    "Under the shadow of the day, the journey begins."
                ],
                "Crash": [
                    "The highway always wins. In the end.",
                    "A flash of chrome, a screech of tires, and then... silence.",
                    "The run ends as all fast runs must: in spectacular ruin."
                ],
                "Extreme Near Miss": [
                    "Death whispered, but the driver didn't listen.",
                    "A close encounter with fate, resolved in milliseconds.",
                    "The gap was narrow. The survival, narrower."
                ],
                "Clutch Survival": [
                    "Defying the odds, one close call at a time.",
                    "A streak of {combo}. Evasion has become second nature.",
                    "A testament to absolute focus."
                ],
                "Panic Driving": [
                    "The road closes in. Erratic movements in congested space.",
                    "Loss of space, loss of speed, the driver struggles."
                ],
                "Traffic Chaos": [
                    "A storm of steel and exhaust. A test of pure instinct.",
                    "Surrounded by moving walls. Every direction is a hazard."
                ],
                "High Risk Driving": [
                    "At this speed, every decision is life or death.",
                    "Brushing past disaster at {speed} km/h.",
                    "The speed dials up, and with it, the risk."
                ],
                "High Combo": [
                    "Evasion has become second nature. {combo} close calls.",
                    "A sequence of escapes, woven into the run."
                ],
                "Untouchable": [
                    "They move through traffic like a ghost.",
                    "Unmatched speed. Unbroken focus. The road belongs to them."
                ],
                "Dominant Run": [
                    "A display of speed. Just leaving everyone behind.",
                    "They dominate every lane of this highway."
                ],
                "Highway Wizard": [
                    "Slalom sequences. A kinetic spell cast on the road.",
                    "Agility and speed working in unison."
                ],
                "Traffic Surgeon": [
                    "Clinical precision. Cutting through the field.",
                    "Finding gaps that barely exist."
                ],
                "Precision Driving": [
                    "A clean line. A silent masterclass in precision.",
                    "Total control. The car is an extension of the mind."
                ],
                "Flow State": [
                    "Everything is clicking right now.",
                    "Operating on instinct. Effortless flow."
                ],
                "Masterclass": [
                    "This has been a masterclass in control.",
                    "Every decision is the right one."
                ],
                "Controlled Aggression": [
                    "Aggressive passes, but keeping it clean.",
                    "Bold swerves, precise execution."
                ],
                "Record Pace": [
                    "Blistering speed at {speed} km/h.",
                    "Speeding down the highway, pushing limits."
                ],
                "Building Momentum": [
                    "The pace quickens. Momentum builds.",
                    "Confidence grows with every stretch."
                ],
                "Traffic Weaving": [
                    "Rapid lane shifts. Weaving through the pack."
                ],
                "Perfect Rhythm": [
                    "Hum of the engine, zoom of the passes. Perfect rhythm."
                ],
                "Recovery Phase": [
                    "A critical escape. The heartbeat slows.",
                    "Order returns in the aftermath of chaos."
                ],
                "High Score": [
                    "A new record. Pushed past the known limits."
                ],
                "Elite Reactions": [
                    "Reflexes tested, and proven. A fraction of a second separates them from ruin.",
                    "No thinking. Only pure reaction.",
                    "The synapses fire instantly. A clean escape.",
                    "A combo of {combo}. Pure instinct overriding fear."
                ],
                "Total Control": [
                    "Flawless execution. They have complete command of this machine.",
                    "A silent exhibition of total control.",
                    "No mistakes, no doubts. The driver is in complete command.",
                    "For {clean_driving_seconds} seconds, the highway has submitted to their will."
                ],
                "Building Momentum->Traffic Surgeon": [
                    "Confidence rises. The driver begins to slice through traffic with clinical focus."
                ],
                "Traffic Surgeon->Highway Wizard": [
                    "They find gaps that barely exist. Surgery yields to wizardry."
                ],
                "Highway Wizard->Clutch Survival": [
                    "The risks escalate. Every move is a flirtation with ruin."
                ],
                "Clutch Survival->Recovery Phase": [
                    "Composure restored. The heartbeat slows in the wake of danger."
                ],
                "*->Recovery Phase": [
                    "Order returns. The crisis has passed."
                ],
                "*->Total Control": [
                    "Complete stabilization. The vehicle is once again an extension of their mind."
                ]
            },
            "savage": {
                "game_start": [
                    "Oh good, another driver who thinks they're in a movie.",
                    "Let's see how long it takes to turn this car into scrap metal.",
                    "We are live. Place your bets on when the crash happens."
                ],
                "Crash": [
                    "Well, physics wins again. Who saw that coming? Everyone.",
                    "And that, ladies and gentlemen, is why we have seatbelts.",
                    "Beautifully done. The car is now a modern art installation."
                ],
                "Extreme Near Miss": [
                    "Nice dodge. Don't get cocky, it was 90% luck.",
                    "That was close enough to smell the other driver's cologne."
                ],
                "Clutch Survival": [
                    "A combo of {combo}. You're really stretching your guardian angel's patience.",
                    "Double digit combo. The collision is going to be hilarious when it happens."
                ],
                "Panic Driving": [
                    "Are we driving or trying to test the airbag system?",
                    "Trapped in traffic and slowing down. Hilarious."
                ],
                "Traffic Chaos": [
                    "Look at this mess. You're basically playing pinball with real cars.",
                    "Absolute disaster area. Traffic chaos."
                ],
                "High Risk Driving": [
                    "Doing {speed} km/h? Your parents must be so proud.",
                    "If you wanted to die, there are less expensive ways."
                ],
                "High Combo": [
                    "Combo of {combo}? Your guardian angel deserves a raise.",
                    "You dodged {combo} cars. Don't get cocky."
                ],
                "Untouchable": [
                    "Traffic can't slow you down? Let's wait for a truck.",
                    "Untouchable? I'm almost disappointed."
                ],
                "Dominant Run": [
                    "Dominating slower pack. Groundbreaking.",
                    "Wow, you overtook traffic. Incredible."
                ],
                "Highway Wizard": [
                    "Slalom wizard. Calm down, Vin Diesel.",
                    "Weaving like a drunk driver at a slalom event."
                ],
                "Traffic Surgeon": [
                    "Clinical surgery. Cute.",
                    "Threading through gaps. Don't scratch the paint."
                ],
                "Precision Driving": [
                    "Precision driving. Boring! Bring back the crashes!",
                    "Very clean. Very slow. Excellent."
                ],
                "Flow State": [
                    "Everything is clicking. Let's see how fast you mess it up.",
                    "Operating on instinct? That's a dangerous idea."
                ],
                "Masterclass": [
                    "Masterclass control. Boring!",
                    "No mistakes. I'm falling asleep here."
                ],
                "Controlled Aggression": [
                    "Aggressive passes. Trying to look cool, huh?"
                ],
                "Record Pace": [
                    "At {speed} km/h, your insurance premium just reached escape velocity.",
                    "Trying to write your own obituary?"
                ],
                "Building Momentum": [
                    "Oh look, we're actually making progress. Don't ruin it.",
                    "Wow, you overtook a car. Give yourself a medal."
                ],
                "Traffic Weaving": [
                    "Weaving through traffic. Slalom champion."
                ],
                "Perfect Rhythm": [
                    "Rhythm is good. Hope you don't hit a wall."
                ],
                "Recovery Phase": [
                    "Wow, you actually saved it. I'm almost disappointed.",
                    "Disaster averted, unfortunately for the viewers."
                ],
                "High Score": [
                    "New high score. Great, now you'll never stop playing."
                ],
                "Elite Reactions": [
                    "Your reflexes aren't terrible today. I'm almost impressed.",
                    "Flashed some decent reactions there. Don't let it go to your head.",
                    "Look at those twitchy fingers. Pure panic, but it worked.",
                    "Wow, you actually dodged that. A miracle, really."
                ],
                "Total Control": [
                    "Total control? Sure, it's easy when you're playing it this safe.",
                    "Very clean, very controlled. Also very boring.",
                    "Still in control. I'm still waiting for the crash.",
                    "You've survived {clean_driving_seconds} seconds without hitting anything. Impressive for a toddler."
                ],
                "Building Momentum->Traffic Surgeon": [
                    "Confidence is growing. Great, more fast swerves to worry about."
                ],
                "Traffic Surgeon->Highway Wizard": [
                    "Finding gaps that barely exist. Let's see how long this luck holds out."
                ],
                "Highway Wizard->Clutch Survival": [
                    "Taking bigger and bigger risks. I'll get my popcorn ready."
                ],
                "Clutch Survival->Recovery Phase": [
                    "You actually saved it. Mildly disappointing for the ratings."
                ],
                "*->Recovery Phase": [
                    "Somehow, you didn't crash. Good job staying lucky."
                ],
                "*->Total Control": [
                    "Back to driving safely. Yawns all around."
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
