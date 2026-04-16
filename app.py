"""
Flask Application — MediSense AI
Serves the web interface and prediction API.
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import traceback
import logging

from predictor import predict_diseases

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)


@app.route("/")
def index():
    """Serve the main web interface."""
    return render_template("index.html")


@app.route("/api/predict", methods=["POST"])
def predict():
    """
    POST /api/predict
    Body: { "query": "<user symptom description>" }
    Returns prediction JSON.
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        query = (data.get("query") or "").strip()

        if not query:
            return jsonify({"success": False, "error": "Please provide a symptom description."}), 400

        if len(query) < 5:
            return jsonify({"success": False, "error": "Please describe your symptoms in more detail."}), 400

        logger.info(f"Prediction request: {query[:80]}...")
        result = predict_diseases(query, top_n=2)
        return jsonify({"success": True, **result})

    except Exception as e:
        logger.error(f"Prediction error: {traceback.format_exc()}")
        return jsonify({"success": False, "error": "An internal error occurred. Please try again."}), 500


@app.route("/api/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "service": "MediSense AI"})


@app.route("/api/examples")
def examples():
    """Return example queries for the UI."""
    return jsonify({
        "examples": [
            "I have high fever, severe headache, body aches and fatigue since yesterday",
            "My chest feels tight, I have shortness of breath and I'm wheezing",
            "I feel extremely tired, urinate frequently and I'm always thirsty",
            "I have a runny nose, sneezing, mild sore throat and low fever",
            "My joints are very swollen and stiff, especially bad in the morning",
            "I have severe abdominal pain that started around my belly button and moved to the lower right",
            "I feel persistent sadness, loss of interest and difficulty sleeping for weeks",
            "I have a butterfly shaped rash on my face, joint pain and fatigue",
            "Sudden numbness on the left side of my face and trouble speaking clearly",
            "Burning sensation when I urinate, cloudy urine and lower abdominal pain",
        ]
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
