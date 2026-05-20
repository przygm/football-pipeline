import os
from flask import Flask
from scripts.run_pipeline import main  

app = Flask(__name__)

@app.route("/")
def run_pipeline():
    try:
        main() 
        return "PIPELINE SUCCESS - Check logs in GCP console.", 200
    except Exception as e:
        return f"PIPELINE FAILED: {str(e)}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
