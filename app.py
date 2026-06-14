import os
import logging
from flask import Flask, request, jsonify, render_template, Response
from game import validate_event_data
from commentary import CommentaryEngine
from tts_provider import KittenTTSProvider
from narrative import NarrativeEngine

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize singletons
commentary_engine = CommentaryEngine()
tts_provider = KittenTTSProvider()
narrative_engine = NarrativeEngine()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status", methods=["GET"])
def get_status():
    """Returns the status of backend systems, especially the TTS engine."""
    return jsonify({
        "tts_enabled": tts_provider.enabled,
        "tts_model": "KittenML/kitten-tts-nano-0.8"
    })

@app.route("/api/commentary", methods=["POST"])
def get_commentary():
    """Generates context-aware commentary from gameplay event JSON."""
    data = request.json
    if not data:
        return jsonify({"error": "Invalid request body"}), 400
        
    is_valid, err_msg = validate_event_data(data)
    if not is_valid:
        logger.warning(f"Event validation failed: {err_msg}")
        return jsonify({"error": err_msg}), 400
        
    # Reset narrative engine on direct game start events
    if data.get("event") == "game_start":
        logger.info("Direct game_start event. Resetting narrative engine history.")
        narrative_engine.reset()
        
    mode = request.args.get("mode", "sports")
    try:
        commentary_data = commentary_engine.generate(data, mode=mode)
        return jsonify(commentary_data)
    except Exception as e:
        logger.error(f"Error generating commentary: {e}", exc_info=True)
        return jsonify({"error": "Internal error generating commentary"}), 500

@app.route("/api/narrative", methods=["POST"])
def get_narrative():
    """Receives a batch of gameplay events, evaluates narrative state,
    generates commentary, and returns it."""
    data = request.json
    if not data:
        return jsonify({"error": "Invalid request body"}), 400
        
    events = data.get("events", [])
    current_time = data.get("current_time", 0.0)
    current_speed = data.get("current_speed", 0.0)
    current_combo = data.get("current_combo", 0)
    
    # Check for game start to reset the narrative history
    for ev in events:
        if ev.get("event") == "game_start":
            logger.info("Game start event detected in batch. Resetting narrative engine history.")
            narrative_engine.reset()
            
    mode = request.args.get("mode", "sports")
    
    try:
        result = narrative_engine.evaluate(events, current_time, current_speed, current_combo)
        
        if not result["should_speak"]:
            return jsonify({"skip": True})
            
        commentary = commentary_engine.generate(result, mode=mode)
        # Add narrative state and stats for debugging / rendering
        commentary["narrative_state"] = result["state"]
        commentary["stats"] = result["stats"]
        return jsonify(commentary)
    except Exception as e:
        logger.error(f"Error generating narrative commentary: {e}", exc_info=True)
        return jsonify({"error": "Internal error generating narrative commentary"}), 500

@app.route("/api/tts", methods=["POST"])
def get_tts():
    """Generates WAV audio bytes for a given text and voice."""
    if not tts_provider.enabled:
        return jsonify({"error": "KittenTTS provider is disabled/uninitialized"}), 503
        
    data = request.json or {}
    text = data.get("text", "")
    voice = data.get("voice", "Jasper")
    
    if not text:
        return jsonify({"error": "Missing 'text' in request body"}), 400
        
    try:
        # Preprocess text to strip characters that might cause audio artifacts
        clean_text = text.replace("!", ".").replace("?", ".").replace("OH.", "Oh.")
        wav_bytes = tts_provider.generate(clean_text, voice=voice)
        return Response(wav_bytes, mimetype="audio/wav")
    except Exception as e:
        logger.error(f"Error in TTS generation: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting RoadCaster server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
