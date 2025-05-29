import requests, time, csv
from datetime import datetime
from math import radians, cos, sin, asin, sqrt
import os
import telebot

# --- Config ---
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
USER_CHAT_ID = os.getenv("CHAT_ID")  # Use numeric Telegram ID, not @handle
CHECK_INTERVAL = 60  # seconds
CSV_LOG = "quake_log.csv"
LOCATION = (49.429, -123.632)  # Roberts Creek

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# --- Utility ---
def haversine(lat1, lon1, lat2, lon2):
    # Calculate distance between two lat/lons in km
    R = 6371
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * asin(sqrt(a))

def log_quake(data):
    with open(CSV_LOG, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(data)

def fetch_nrcan():
    try:
        r = requests.get("https://earthquakescanada.nrcan.gc.ca/api/earthquakes/latest?format=geojson")
        quakes = r.json()["features"]
        return [{
            "time": q["properties"]["time"],
            "mag": q["properties"]["mag"],
            "lat": q["geometry"]["coordinates"][1],
            "lon": q["geometry"]["coordinates"][0],
            "place": q["properties"]["place"]
        } for q in quakes]
    except:
        return []

def fetch_pnsn():
    try:
        r = requests.get("https://pnsn.org/earthquakes/feed/v1.0/summary/all_hour.geojson")
        quakes = r.json()["features"]
        return [{
            "time": q["properties"]["time"],
            "mag": q["properties"]["mag"],
            "lat": q["geometry"]["coordinates"][1],
            "lon": q["geometry"]["coordinates"][0],
            "place": q["properties"]["place"]
        } for q in quakes]
    except:
        return []

# --- Main ---
seen = set()

def monitor():
    while True:
        for source in [fetch_nrcan, fetch_pnsn]:
            for quake in source():
                quake_id = f"{quake['time']}-{quake['lat']}-{quake['lon']}"
                if quake_id in seen:
                    continue
                seen.add(quake_id)
                dist = haversine(LOCATION[0], LOCATION[1], quake["lat"], quake["lon"])
                if dist <= 200:
                    msg = f"🌍 Quake detected!\n🗺 {quake['place']}\n💥 M{quake['mag']}\n📍 {dist:.1f} km from Roberts Creek\n⏰ {quake['time']}"
                    bot.send_message(USER_CHAT_ID, msg)
                    log_quake([datetime.utcnow().isoformat(), quake['place'], quake['mag'], dist, quake['time']])
        time.sleep(CHECK_INTERVAL)

monitor()
