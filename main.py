import network
import time
import urequests
from machine import Pin
from cred import WIFI_SSID, WIFI_PASS, BLYNK_AUTH

# ---------------- CONFIG ----------------
RELAY_PIN = 25          # change as needed
LIGHT_PIN = 2
RELAY_ACTIVE_LOW = False
BLYNK_VPIN = "V0"
POLL_INTERVAL = 30    # seconds
# ----------------------------------------

# Relay setup
relay = Pin(RELAY_PIN, Pin.OUT)
light = Pin(LIGHT_PIN, Pin.OUT)

def relay_on():
    relay.value(0 if RELAY_ACTIVE_LOW else 1)
    light.value(1)
    print("Relay ON")

def relay_off():
    relay.value(1 if RELAY_ACTIVE_LOW else 0)
    light.value(0)
    print("Relay OFF")

# WiFi connect
def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASS)
        while not wlan.isconnected():
            time.sleep(0.5)

    print("WiFi connected:", wlan.ifconfig())

def sync_time():
    try:
        import ntptime
        ntptime.host = "time.google.com"
        ntptime.settime()
        print("Time synced via NTP")
    except Exception as e:
        print("NTP sync failed:", e)

# Get current seconds from midnight
def now_seconds():
    t = time.localtime()
    return t[3]*3600 + t[4]*60 + t[5] + 19800

def seconds_to_hhmmss(seconds):
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours}:{minutes}:{secs}"

# Read Time Input from Blynk (Time Range mode)
def read_time_input():
    url = "https://blynk.cloud/external/api/get?token={}&{}".format(
        BLYNK_AUTH, BLYNK_VPIN
    )
    r = urequests.get(url)
    raw = r.text
    r.close()

    # Split NULL-separated response
    parts = [p for p in raw.split('\x00') if p]

    start_sec = int(parts[0])
    stop_sec  = int(parts[1])
    timezone  = parts[2]
    offset    = int(parts[3])

    return start_sec, stop_sec

# Time window logic (handles overnight)
def in_time_window(now, start, stop):
    print("\nSchedule time:", seconds_to_hhmmss(start), seconds_to_hhmmss(stop))
    print("Current time:", seconds_to_hhmmss(now))
    if start <= stop:
        return start <= now < stop
    else:
        # Overnight (e.g. 22:00 → 06:00)
        return now >= start or now < stop

# ---------------- MAIN ----------------

relay_off()
wifi_connect()
time.sleep(2)
sync_time()

print("Scheduler running...")

while True:
    try:
        start_sec, stop_sec = read_time_input()
        now = now_seconds()

        if in_time_window(now, start_sec, stop_sec):
            relay_on()
        else:
            relay_off()

    except Exception as e:
        print("Error:", e)
        relay_off()   # fail-safe

    time.sleep(POLL_INTERVAL)

