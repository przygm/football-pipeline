import logging
import os
import subprocess
from flask import Flask
from scripts.run_pipeline import main  

#---------------------------------------------------------------------------------------------------
def run_command(cmd, cwd):
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    for line in process.stdout:
        logging.info(line.rstrip())

    process.wait()

    if process.returncode != 0:
        raise Exception(f"Command failed: {' '.join(cmd)}")

#---------------------------------------------------------------------------------------------------

app = Flask(__name__)

@app.route("/")
def run_pipeline():
    try:
        main() 
        run_command(["dbt", "debug", "--profiles-dir", ".", "--target", "prod"], "dbt_project")
        run_command(["dbt", "run",   "--profiles-dir", ".", "--target", "prod"], "dbt_project")
        run_command(["dbt", "test",  "--profiles-dir", ".", "--target", "prod"], "dbt_project")
        logging.info("PIPELINE SUCCESS") 
        return "PIPELINE SUCCESS - Check logs in GCP console.", 200
    except Exception as e:
        logging.error(f"PIPELINE FAILED: {str(e)}")
        return f"PIPELINE FAILED: {str(e)}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
