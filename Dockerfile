# Use official lightweight Python image as the base runtime
FROM python:3.10-slim

# Install git (required by dbt to fetch packages and internal dependencies)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy application source code into the container image
COPY . .

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install web server and framework used to run the app
RUN pip install flask gunicorn

# Start the Gunicorn server and bind to the port provided by Cloud Run
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app