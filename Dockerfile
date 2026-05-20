# Używamy oficjalnego obrazu Pythona
FROM python:3.10-slim

# Kopiujemy pliki projektu do kontenera
WORKDIR /app
COPY . .

# Instalujemy biblioteki z Twojego pliku requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install flask gunicorn

# Uruchamiamy serwer pośredniczący
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
