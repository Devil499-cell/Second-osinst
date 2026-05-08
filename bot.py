import requests
import json
import time
from datetime import datetime
import os
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# ================= CONFIGURATION =================
BOT_TOKEN = "8797483939:AAE2LJ1sy1k1_4BOhelrcOcMaJtiR_o0xXY"
EXTERNAL_API_URL = "https://all-number-info-rajan-eta.vercel.app/api"
ADMIN_PASSWORD = "#shashikumar"
# =================================================

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
OFFSET = 0

user_data = {}
admin_session = {}

USER_KEYBOARD = {
    "keyboard": [[{"text": "📱 Phone Lookup"}]],
    "resize_keyboard": True
}

ADMIN_KEYBOARD = {
    "keyboard": [
        [{"text": "📊 Dashboard"}, {"text": "👥 Users"}],
        [{"text": "🗑️ Remove User"}, {"text": "📢 Broadcast"}],
        [{"text": "🚪 Exit Admin"}]
    ],
    "resize_keyboard": True
}

# Health server
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Running")
    def log_message(self, *args): pass

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), HealthHandler).serve_forever()

def save_data():
    try:
        with open("user_data.json", "w") as f:
            json.dump(user_data, f)
    except: pass

def load_data():
    global user_data
    try:
        with open("user_data.json", "r") as f:
            user_data = json.load(f)
    except: user_data = {}

def send_msg(chat_id, text, reply_markup=None):
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        return requests.post(url, json=payload, timeout=15).json()
    except: return None

def is_admin(chat_id):
    return str(chat_id) in admin_session

def call_api(mobile_number):
    """Call API and return RAW response as JSON"""
    try:
        url = f"{EXTERNAL_API_URL}?number={mobile_number}"
        print(f"📡 API Call: {url}")
        resp = requests.get(url, timeout=30)
        
        if resp.status_code == 200:
            # Return RAW JSON response
            return resp.json()
        else:
            return {"error": f"HTTP {resp.status_code}", "raw": resp.text}
    except Exception as e:
        return {"error": str(e)}

def update_stats(chat_id, name, number=None):
    cid = str(chat_id)
    if cid not in user_data:
        user_data[cid] = {"name": name, "searches": 0}
    user_data[cid]["searches"] += 1
    save_data()

# Admin functions
def show_dashboard(chat_id):
    total = len(user_data)
    searches = sum(u.get("searches", 0) for u in user_data.values())
    msg = f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📊 DASHBOARD\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n👥 Users: {total}\n🔍 Searches: {searches}\n🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    send_msg(chat_id, msg, ADMIN_KEYBOARD)

def show_users(chat_id):
    if not user_data:
        send_msg(chat_id, "❌ No users")
        return
    msg = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n👥 USERS\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, (cid, data) in enumerate(user_data.items(), 1):
        msg += f"{i}. {data.get('name', 'Unknown')}\n   ID: <code>{cid}</code>\n   Searches: {data.get('searches', 0)}\n\n"
        if i >= 15: break
    send_msg(chat_id, msg)

def remove_user(chat_id, target_id):
    target = str(target_id).strip()
    if str(chat_id) == target:
        send_msg(chat_id, "❌ Cannot remove self")
        return
    if target in user_data:
        name = user_data[target].get("name", "Unknown")
        del user_data[target]
        save_data()
        send_msg(chat_id, f"✅ Removed {name}", ADMIN_KEYBOARD)
    else:
        send_msg(chat_id, f"❌ User {target} not found")

def start_remove(chat_id):
    send_msg(chat_id, "🗑️ Send user ID to remove:\nExample: 6323367629\n\nType /cancel")

def broadcast_msg(chat_id, msg_text):
    if not user_data:
        send_msg(chat_id, "❌ No users")
        return
    sent = 0
    for cid in user_data.keys():
        try:
            if send_msg(int(cid), f"📢 BROADCAST\n\n{msg_text}"):
                sent += 1
            time.sleep(0.05)
        except: pass
    send_msg(chat_id, f"✅ Sent to {sent}/{len(user_data)} users", ADMIN_KEYBOARD)

def start_broadcast(chat_id):
    send_msg(chat_id, "📢 Send message to broadcast:\nType /cancel")

def handle_update(update):
    global OFFSET
    if "message" not in update: return
    
    msg = update["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")
    name = msg["chat"].get("first_name", "User")
    
    print(f"📨 {name}: {text}")
    update_stats(chat_id, name)
    
    admin = is_admin(chat_id)
    
    # Remove mode
    if admin and admin_session.get(str(chat_id), {}).get("remove_mode"):
        if text == "/cancel":
            admin_session[str(chat_id)]["remove_mode"] = False
            send_msg(chat_id, "❌ Cancelled", ADMIN_KEYBOARD)
        elif text.isdigit():
            remove_user(chat_id, text)
            admin_session[str(chat_id)]["remove_mode"] = False
        return
    
    # Broadcast mode
    if admin and admin_session.get(str(chat_id), {}).get("broadcast_mode"):
        if text == "/cancel":
            admin_session[str(chat_id)]["broadcast_mode"] = False
            send_msg(chat_id, "❌ Cancelled", ADMIN_KEYBOARD)
        else:
            broadcast_msg(chat_id, text)
            admin_session[str(chat_id)]["broadcast_mode"] = False
        return
    
    # Admin commands
    if admin:
        if text == "📊 Dashboard":
            show_dashboard(chat_id)
        elif text == "👥 Users":
            show_users(chat_id)
        elif text == "🗑️ Remove User":
            start_remove(chat_id)
            admin_session[str(chat_id)] = {"remove_mode": True}
        elif text == "📢 Broadcast":
            start_broadcast(chat_id)
            admin_session[str(chat_id)] = {"broadcast_mode": True}
        elif text == "🚪 Exit Admin":
            del admin_session[str(chat_id)]
            send_msg(chat_id, "👋 Logged out", USER_KEYBOARD)
        return
    
    # Admin login
    if text.lower() == "/admin":
        send_msg(chat_id, "🔐 Send password:")
        return
    if text == ADMIN_PASSWORD:
        admin_session[str(chat_id)] = {}
        send_msg(chat_id, "✅ Admin login!", ADMIN_KEYBOARD)
        return
    
    # User commands
    if text == "/start":
        welcome = f"🎉 Welcome {name}!\n\n📱 Send any 10-digit number to get info"
        send_msg(chat_id, welcome, USER_KEYBOARD)
        return
    
    if text == "📱 Phone Lookup":
        send_msg(chat_id, "📞 Send 10-digit number:\nExample: 9876543210")
        return
    
    # Phone lookup - Send RAW API response as JSON
    if text.isdigit() and len(text) == 10:
        send_msg(chat_id, f"🔍 Fetching info for {text}...")
        
        api_response = call_api(text)
        
        # Convert to formatted JSON string
        json_response = json.dumps(api_response, indent=2, ensure_ascii=False)
        
        # If too long, split
        if len(json_response) > 4000:
            parts = [json_response[i:i+4000] for i in range(0, len(json_response), 4000)]
            for part in parts:
                send_msg(chat_id, f"<pre>{part}</pre>")
        else:
            send_msg(chat_id, f"<pre>{json_response}</pre>")
        
        update_stats(chat_id, name, text)
        return
    
    if text and text not in ["/start", "/admin", ADMIN_PASSWORD]:
        send_msg(chat_id, "❌ Send 10-digit number or press button")

def main():
    load_data()
    Thread(target=run_health_server, daemon=True).start()
    
    print("=" * 50)
    print("🤖 BOT STARTED - RAW API RESPONSE MODE")
    print("=" * 50)
    print(f"🔐 Admin: {ADMIN_PASSWORD}")
    print(f"🌐 API: {EXTERNAL_API_URL}")
    print("=" * 50)
    
    global OFFSET
    while True:
        try:
            resp = requests.get(f"{BASE_URL}/getUpdates", 
                               params={"offset": OFFSET, "timeout": 30}, timeout=35)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    for update in data.get("result", []):
                        handle_update(update)
                        OFFSET = update["update_id"] + 1
            time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n👋 Stopped")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
