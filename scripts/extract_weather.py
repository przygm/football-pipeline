"""
Weather API Extractor
Source: Open-Meteo (free, no API key required)
"""
import os
import requests
import json
from datetime import datetime, timedelta
from snowflake.connector import connect
from dotenv import load_dotenv

load_dotenv()

# Configuration
# Stadium coordinates are now handled in run_weather_etl() function
    # Premier League (PL)
    'Manchester United': {'lat': 53.4631, 'lon': -2.2913},
    'Manchester City': {'lat': 53.4831, 'lon': -2.2006},
    'Liverpool': {'lat': 53.4308, 'lon': -2.9608},
    'Arsenal': {'lat': 51.5549, 'lon': -0.1081},
    'Chelsea': {'lat': 51.4816, 'lon': -0.1910},
    'Tottenham': {'lat': 51.6033, 'lon': -0.0659},
    'Newcastle United': {'lat': 54.9756, 'lon': -1.6217},
    'Aston Villa': {'lat': 52.5093, 'lon': -1.8848},
    'West Ham United': {'lat': 51.5383, 'lon': -0.0166},
    'Crystal Palace': {'lat': 51.3983, 'lon': -0.0855},
    'Brighton & Hove Albion': {'lat': 50.8600, 'lon': -0.0801},
    'Fulham': {'lat': 51.4750, 'lon': -0.2217},
    'Wolverhampton Wanderers': {'lat': 52.5903, 'lon': -2.1303},
    'Southampton': {'lat': 50.9058, 'lon': -1.3911},
    'Nottingham Forest': {'lat': 52.9399, 'lon': -1.1322},
    'Everton': {'lat': 53.4389, 'lon': -2.9663},
    'Leeds United': {'lat': 53.7778, 'lon': -1.5721},
    'Burnley': {'lat': 53.7890, 'lon': -2.2302},
    'Brentford': {'lat': 51.4908, 'lon': -0.2887},
    'Sunderland': {'lat': 54.9146, 'lon': -1.3884},
    
    # Bundesliga (BL1)
    'Bayern Munich': {'lat': 48.2188, 'lon': 11.6247},
    'Borussia Dortmund': {'lat': 51.4925, 'lon': 7.4518},
    'RB Leipzig': {'lat': 51.3458, 'lon': 12.3461},
    'Bayer Leverkusen': {'lat': 50.9333, 'lon': 6.8833},
    'Eintracht Frankfurt': {'lat': 50.0680, 'lon': 8.6458},
    'VfB Stuttgart': {'lat': 48.7923, 'lon': 9.2320},
    'Borussia Mönchengladbach': {'lat': 51.1675, 'lon': 6.4428},
    'VfL Wolfsburg': {'lat': 52.4326, 'lon': 10.8072},
    'FC Union Berlin': {'lat': 52.4572, 'lon': 13.5683},
    'SC Freiburg': {'lat': 47.9889, 'lon': 7.8944},
    'TSG Hoffenheim': {'lat': 49.1222, 'lon': 8.4139},
    '1. FC Köln': {'lat': 50.9333, 'lon': 6.8750},
    '1. FSV Mainz 05': {'lat': 49.9842, 'lon': 8.2797},
    'FC Augsburg': {'lat': 48.3667, 'lon': 10.8833},
    '1. FC Heidenheim': {'lat': 48.6667, 'lon': 10.1333},
    'SV Werder Bremen': {'lat': 53.0667, 'lon': 8.8333},
    'Hamburger SV': {'lat': 53.5872, 'lon': 9.8989},
    'FC St. Pauli': {'lat': 53.5872, 'lon': 9.8989},
    
    # Serie A (SA)
    'Juventus': {'lat': 45.1096, 'lon': 7.6411},
    'Inter Milan': {'lat': 45.4781, 'lon': 9.1211},
    'AC Milan': {'lat': 45.4642, 'lon': 9.1906},
    'Napoli': {'lat': 40.8279, 'lon': 14.1931},
    'Roma': {'lat': 41.9341, 'lon': 12.4547},
    'Lazio': {'lat': 41.9341, 'lon': 12.4547},
    'Atalanta': {'lat': 45.7090, 'lon': 9.6808},
    'Fiorentina': {'lat': 43.7808, 'lon': 11.2827},
    'Bologna': {'lat': 44.4949, 'lon': 11.3426},
    'Torino': {'lat': 45.1017, 'lon': 7.6408},
    'Genoa': {'lat': 44.4142, 'lon': 8.9275},
    'Sassuolo': {'lat': 44.7200, 'lon': 10.6667},
    'Udinese': {'lat': 46.0833, 'lon': 13.2333},
    'Parma': {'lat': 44.8000, 'lon': 10.3333},
    'Como': {'lat': 45.8094, 'lon': 9.0850},
    'Cagliari': {'lat': 39.2000, 'lon': 9.1333},
    'Hellas Verona': {'lat': 45.4386, 'lon': 10.9917},
    'Pisa': {'lat': 43.7167, 'lon': 10.4000},
    'Cremonese': {'lat': 45.1333, 'lon': 10.0333},
    'Lecce': {'lat': 40.3500, 'lon': 18.1667},
    
    # La Liga (PD)
    'Real Madrid': {'lat': 40.4530, 'lon': -3.6883},
    'Barcelona': {'lat': 41.3828, 'lon': 2.1868},
    'Atletico Madrid': {'lat': 40.4362, 'lon': -3.5993},
    'Real Sociedad': {'lat': 43.3014, 'lon': -1.9736},
    'Villarreal': {'lat': 39.9441, 'lon': -0.1036},
    'Real Betis': {'lat': 37.3564, 'lon': -5.9817},
    'Sevilla': {'lat': 37.3833, 'lon': -5.9667},
    'Girona': {'lat': 41.9794, 'lon': 2.8214},
    'Athletic Club': {'lat': 43.2640, 'lon': -2.9494},
    'Valencia': {'lat': 39.4746, 'lon': -0.3582},
    'Mallorca': {'lat': 39.5894, 'lon': 2.6500},
    'Alaves': {'lat': 42.8375, 'lon': -2.6881},
    'Celta Vigo': {'lat': 42.2118, 'lon': -8.7392},
    'Rayo Vallecano': {'lat': 40.3919, 'lon': -3.6589},
    'Getafe': {'lat': 40.3250, 'lon': -3.7167},
    'Osasuna': {'lat': 42.7944, 'lon': -1.2569},
    'Espanyol': {'lat': 41.3479, 'lon': 2.0757},
    'Levante': {'lat': 39.4044, 'lon': -0.3919},
    'Elche': {'lat': 38.2669, 'lon': -0.7017},
    'Oviedo': {'lat': 43.3603, 'lon': -5.8448},
    
    # Champions League teams (CL) - major European teams
    'Paris Saint-Germain': {'lat': 48.8417, 'lon': 2.2520},
    'PSV Eindhoven': {'lat': 51.4416, 'lon': 5.4697},
    'Club Brugge': {'lat': 51.2054, 'lon': 3.1817},
    'Bologna': {'lat': 44.4949, 'lon': 11.3426},  # Already included
    'Slavia Praha': {'lat': 50.0755, 'lon': 14.4378},
    'Liverpool': {'lat': 53.4308, 'lon': -2.9608},  # Already included
    'Sturm Graz': {'lat': 47.0333, 'lon': 15.4167},
    'Sporting CP': {'lat': 38.7223, 'lon': -9.1393},
    'Brest': {'lat': 48.3904, 'lon': -4.4861},
    'Dinamo Zagreb': {'lat': 45.8150, 'lon': 15.9819}
}

SNOWFLAKE_CONFIG = {
    'account': os.getenv('SNOWFLAKE_ACCOUNT'),
    'user': os.getenv('SNOWFLAKE_USER'),
    'password': os.getenv('SNOWFLAKE_PASSWORD'),
    'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH'),
    'database': os.getenv('SNOWFLAKE_DATABASE', 'FOOTBALL_DB'),
    'schema': 'BRONZE'
}


def get_weather_connection():
    """Create Snowflake connection for bronze layer."""
    return connect(**SNOWFLAKE_CONFIG)


def fetch_weather_forecast(lat: float, lon: float, days: int = 7) -> dict:
    """Fetch weather forecast from Open-Meteo API."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        'latitude': lat,
        'longitude': lon,
        'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode',
        'timezone': 'auto',
        'forecast_days': days
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather: {e}")
        return {}


def insert_weather_to_snowflake(team_name: str, lat: float, lon: float, weather_data: dict):
    """Upload weather data to Snowflake stage and copy into table."""
    if not weather_data.get('daily'):
        return
    
    # Save to file first
    os.makedirs("raw", exist_ok=True)
    filename = f"raw/weather_{team_name.replace(' ', '_')}_{datetime.now().isoformat().replace(':', '').replace('-', '').replace('.', '')[:15]}.json"
    
    record = {
        "team_name": team_name,
        "latitude": lat,
        "longitude": lon,
        "ingestion_time": datetime.now().isoformat(),
        "weather_data": weather_data
    }
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False)
    
    print(f"File saved: {filename}")
    
    # Upload to Snowflake
    conn = get_weather_connection()
    cs = conn.cursor()
    
    try:
        # Upload file to stage
        print("Uploading file to Snowflake stage")
        cs.execute(f"PUT file://{os.path.abspath(filename)} @%weather_raw")
        
        # Copy into table
        print("Copying data into weather table")
        cs.execute(f"""
        COPY INTO BRONZE.WEATHER_RAW
        FROM (
            SELECT 
                $1:weather_data,
                $1:ingestion_time::timestamp
            FROM @%weather_raw
        )
        FILE_FORMAT = (TYPE = 'JSON')
        PURGE = TRUE
        ON_ERROR = 'CONTINUE'
        """)
        
        print(f"Data successfully loaded to Snowflake for {team_name}")
        
    except Exception as e:
        print(f"Snowflake error: {e}")
        raise
    finally:
        cs.close()
        conn.close()


def get_team_stadium_coords(team_name: str) -> tuple:
    """Get stadium coordinates for a team. Uses geocoding as fallback."""
    # Clean team name for matching
    clean_name = team_name.replace(' FC', '').replace('Football Club', '').strip()
    
    # Direct mapping for known teams
    stadium_mapping = {
        # Premier League
        'Manchester United': (53.4631, -2.2913),
        'Manchester City': (53.4831, -2.2006),
        'Liverpool': (53.4308, -2.9608),
        'Arsenal': (51.5549, -0.1081),
        'Chelsea': (51.4816, -0.1910),
        'Tottenham Hotspur': (51.6033, -0.0659),
        'Newcastle United': (54.9756, -1.6217),
        'Aston Villa': (52.5093, -1.8848),
        'West Ham United': (51.5383, -0.0166),
        'Crystal Palace': (51.3983, -0.0855),
        'Brighton & Hove Albion': (50.8600, -0.0801),
        'Fulham': (51.4750, -0.2217),
        'Wolverhampton Wanderers': (52.5903, -2.1303),
        'Southampton': (50.9058, -1.3911),
        'Nottingham Forest': (52.9399, -1.1322),
        'Everton': (53.4389, -2.9663),
        'Leeds United': (53.7778, -1.5721),
        'Burnley': (53.7890, -2.2302),
        'Brentford': (51.4908, -0.2887),
        'Sunderland': (54.9146, -1.3884),
        
        # Bundesliga
        'Bayern Munich': (48.2188, 11.6247),
        'Borussia Dortmund': (51.4925, 7.4518),
        'RB Leipzig': (51.3458, 12.3461),
        'Bayer Leverkusen': (50.9333, 6.8833),
        'Eintracht Frankfurt': (50.0680, 8.6458),
        'VfB Stuttgart': (48.7923, 9.2320),
        'Borussia Mönchengladbach': (51.1675, 6.4428),
        'VfL Wolfsburg': (52.4326, 10.8072),
        'Union Berlin': (52.4572, 13.5683),
        'SC Freiburg': (47.9889, 7.8944),
        'TSG Hoffenheim': (49.1222, 8.4139),
        '1. FC Köln': (50.9333, 6.8750),
        '1. FSV Mainz 05': (49.9842, 8.2797),
        'FC Augsburg': (48.3667, 10.8833),
        '1. FC Heidenheim': (48.6667, 10.1333),
        'SV Werder Bremen': (53.0667, 8.8333),
        'Hamburger SV': (53.5872, 9.8989),
        'FC St. Pauli': (53.5872, 9.8989),
        
        # Serie A
        'Juventus': (45.1096, 7.6411),
        'Inter Milan': (45.4781, 9.1211),
        'AC Milan': (45.4642, 9.1906),
        'SSC Napoli': (40.8279, 14.1931),
        'AS Roma': (41.9341, 12.4547),
        'SS Lazio': (41.9341, 12.4547),
        'Atalanta': (45.7090, 9.6808),
        'ACF Fiorentina': (43.7808, 11.2827),
        'Bologna FC': (44.4949, 11.3426),
        'Torino': (45.1017, 7.6408),
        'Genoa': (44.4142, 8.9275),
        'US Sassuolo': (44.7200, 10.6667),
        'Udinese': (46.0833, 13.2333),
        'Parma': (44.8000, 10.3333),
        'Como': (45.8094, 9.0850),
        'Cagliari': (39.2000, 9.1333),
        'Hellas Verona': (45.4386, 10.9917),
        'AC Pisa': (43.7167, 10.4000),
        'US Cremonese': (45.1333, 10.0333),
        'US Lecce': (40.3500, 18.1667),
        
        # La Liga
        'Real Madrid': (40.4530, -3.6883),
        'FC Barcelona': (41.3828, 2.1868),
        'Atlético Madrid': (40.4362, -3.5993),
        'Real Sociedad': (43.3014, -1.9736),
        'Villarreal': (39.9441, -0.1036),
        'Real Betis': (37.3564, -5.9817),
        'Sevilla': (37.3833, -5.9667),
        'Girona': (41.9794, 2.8214),
        'Athletic Club': (43.2640, -2.9494),
        'Valencia': (39.4746, -0.3582),
        'RCD Mallorca': (39.5894, 2.6500),
        'Deportivo Alavés': (42.8375, -2.6881),
        'RC Celta': (42.2118, -8.7392),
        'Rayo Vallecano': (40.3919, -3.6589),
        'Getafe': (40.3250, -3.7167),
        'CA Osasuna': (42.7944, -1.2569),
        'RCD Espanyol': (41.3479, 2.0757),
        'Levante': (39.4044, -0.3919),
        'Elche': (38.2669, -0.7017),
        'Real Oviedo': (43.3603, -5.8448),
    }
    
    # Try exact match first
    if clean_name in stadium_mapping:
        return stadium_mapping[clean_name]
    
    # Try partial match
    for mapped_team, coords in stadium_mapping.items():
        if mapped_team.lower() in clean_name.lower() or clean_name.lower() in mapped_team.lower():
            return coords
    
    # Fallback: return None if no match found
    print(f"No coordinates found for team: {team_name}")
    return None


def run_weather_etl():
    """Main ETL function for weather data."""
    print("Fetching weather data for all teams with known stadiums")
    
    # This should be called after extract_football.py to get all teams
    # For now, we'll use the hardcoded mapping above
    # TODO: Integrate with football API to get all teams dynamically
    
    stadium_mapping = {
        # Premier League
        'Manchester United': (53.4631, -2.2913),
        'Manchester City': (53.4831, -2.2006),
        'Liverpool': (53.4308, -2.9608),
        'Arsenal': (51.5549, -0.1081),
        'Chelsea': (51.4816, -0.1910),
        'Tottenham Hotspur': (51.6033, -0.0659),
        'Newcastle United': (54.9756, -1.6217),
        'Aston Villa': (52.5093, -1.8848),
        'West Ham United': (51.5383, -0.0166),
        'Crystal Palace': (51.3983, -0.0855),
        'Brighton & Hove Albion': (50.8600, -0.0801),
        'Fulham': (51.4750, -0.2217),
        'Wolverhampton Wanderers': (52.5903, -2.1303),
        'Southampton': (50.9058, -1.3911),
        'Nottingham Forest': (52.9399, -1.1322),
        'Everton': (53.4389, -2.9663),
        'Leeds United': (53.7778, -1.5721),
        'Burnley': (53.7890, -2.2302),
        'Brentford': (51.4908, -0.2887),
        'Sunderland': (54.9146, -1.3884),
        
        # Bundesliga
        'Bayern Munich': (48.2188, 11.6247),
        'Borussia Dortmund': (51.4925, 7.4518),
        'RB Leipzig': (51.3458, 12.3461),
        'Bayer Leverkusen': (50.9333, 6.8833),
        'Eintracht Frankfurt': (50.0680, 8.6458),
        'VfB Stuttgart': (48.7923, 9.2320),
        'Borussia Mönchengladbach': (51.1675, 6.4428),
        'VfL Wolfsburg': (52.4326, 10.8072),
        'Union Berlin': (52.4572, 13.5683),
        'SC Freiburg': (47.9889, 7.8944),
        'TSG Hoffenheim': (49.1222, 8.4139),
        '1. FC Köln': (50.9333, 6.8750),
        '1. FSV Mainz 05': (49.9842, 8.2797),
        'FC Augsburg': (48.3667, 10.8833),
        '1. FC Heidenheim': (48.6667, 10.1333),
        'SV Werder Bremen': (53.0667, 8.8333),
        'Hamburger SV': (53.5872, 9.8989),
        'FC St. Pauli': (53.5872, 9.8989),
        
        # Serie A
        'Juventus': (45.1096, 7.6411),
        'Inter Milan': (45.4781, 9.1211),
        'AC Milan': (45.4642, 9.1906),
        'SSC Napoli': (40.8279, 14.1931),
        'AS Roma': (41.9341, 12.4547),
        'SS Lazio': (41.9341, 12.4547),
        'Atalanta': (45.7090, 9.6808),
        'ACF Fiorentina': (43.7808, 11.2827),
        'Bologna FC': (44.4949, 11.3426),
        'Torino': (45.1017, 7.6408),
        'Genoa': (44.4142, 8.9275),
        'US Sassuolo': (44.7200, 10.6667),
        'Udinese': (46.0833, 13.2333),
        'Parma': (44.8000, 10.3333),
        'Como': (45.8094, 9.0850),
        'Cagliari': (39.2000, 9.1333),
        'Hellas Verona': (45.4386, 10.9917),
        'AC Pisa': (43.7167, 10.4000),
        'US Cremonese': (45.1333, 10.0333),
        'US Lecce': (40.3500, 18.1667),
        
        # La Liga
        'Real Madrid': (40.4530, -3.6883),
        'FC Barcelona': (41.3828, 2.1868),
        'Atlético Madrid': (40.4362, -3.5993),
        'Real Sociedad': (43.3014, -1.9736),
        'Villarreal': (39.9441, -0.1036),
        'Real Betis': (37.3564, -5.9817),
        'Sevilla': (37.3833, -5.9667),
        'Girona': (41.9794, 2.8214),
        'Athletic Club': (43.2640, -2.9494),
        'Valencia': (39.4746, -0.3582),
        'RCD Mallorca': (39.5894, 2.6500),
        'Deportivo Alavés': (42.8375, -2.6881),
        'RC Celta': (42.2118, -8.7392),
        'Rayo Vallecano': (40.3919, -3.6589),
        'Getafe': (40.3250, -3.7167),
        'CA Osasuna': (42.7944, -1.2569),
        'RCD Espanyol': (41.3479, 2.0757),
        'Levante': (39.4044, -0.3919),
        'Elche': (38.2669, -0.7017),
        'Real Oviedo': (43.3603, -5.8448),
    }
    
    for team_name, (lat, lon) in stadium_mapping.items():
        weather_data = fetch_weather_forecast(lat, lon)
        if weather_data:
            insert_weather_to_snowflake(team_name, lat, lon, weather_data)
    
    print("Weather ETL completed")


if __name__ == '__main__':
    run_weather_etl()