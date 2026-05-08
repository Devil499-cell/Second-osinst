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

# Keyboards
USER_KEYBOARD = {
    "keyboard": [[{"text": "📱 Phone Lookup"}]],
    "resize_keyboard": True
}

ADMIN_KEYBOARD = {
    "keyboard": [
        [{"text": "📊 Dashboard"}, {"text": "👥 Users"}],
        [{"text": "📝 Logs"}, {"text": "📈 Stats"}],
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
    try:
        url = f"{EXTERNAL_API_URL}?number={mobile_number}"
        print(f"📡 API: {url}")
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)[:50]}

def format_output(data, number):
    """Clean formatted output - exactly like screenshot style"""
    
    output = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    output += "         📱 NUMBER INFO BOT\n"
    output += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    output += f"📞 Number: <code>{number}</code>\n\n"
    
    if "error" in data:
        output += f"❌ {data['error']}\n"
        return output
    
    output += "📊 EXTRACTED SUMMARY:\n"
    output += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    found = False
    
    # Parse all sources
    if "results" in data:
        results = data["results"]
        
        # Source 1 - Database
        if "source_1" in results and results["source_1"].get("status") == "success":
            src = results["source_1"].get("data", {})
            records = src.get("data", [])
            if records:
                found = True
                output += "📌 <b>From DATABASE:</b>\n"
                for i, rec in enumerate(records[:3], 1):
                    name = rec.get('name', 'N/A')
                    mob = rec.get('mobile', number)
                    addr = rec.get('address', '')[:60]
                    output += f"{i}. {name} - {mob}\n"
                    if addr:
                        output += f"   📍 {addr}...\n"
                output += "\n"
        
        # Source 3 - Tracking
        if "source_3" in results and results["source_3"].get("status") == "success":
            src = results["source_3"].get("data", {})
            if src.get("SIM card") or src.get("Owner Name"):
                found = True
                output += "📌 <b>From TRACKING:</b>\n"
                if src.get("Owner Name"):
                    output += f"   👤 Owner: {src.get('Owner Name')}\n"
                if src.get("SIM card"):
                    output += f"   📡 SIM: {src.get('SIM card')}\n"
                if src.get("Mobile Locations"):
                    loc = src.get('Mobile Locations', '')[:50]
                    output += f"   📍 Location: {loc}...\n"
                output += "\n"
        
        # Source 8 - Truecaller
        if "source_8" in results and results["source_8"].get("status") == "success":
            src = results["source_8"].get("data", {})
            inner = src.get("data", {})
            tc_data = inner.get("results", {})
            if tc_data.get("name"):
                found = True
                output += "📌 <b>From TRUECALLER:</b>\n"
                output += f"   👤 Name: {tc_data.get('name')}\n"
                if tc_data.get("carrier"):
                    output += f"   📡 Carrier: {tc_data.get('carrier')}\n"
                if tc_data.get("location"):
                    output += f"   📍 Location: {tc_data.get('location')}\n"
                output += "\n"
        
        # Source 9
        if "source_9" in results and results["source_9"].get("status") == "success":
            src = results["source_9"].get("data", {})
            records = src.get("result", {}).get("results", [])
            if records:
                found = True
                output += "📌 <b>From OTHER SOURCE:</b>\n"
                for i, rec in enumerate(records[:3], 1):
                    name = rec.get('NAME', 'N/A')
                    mob = rec.get('MOBILE', number)
                    output += f"{i}. {name} - {mob}\n"
                output += "\n"
    
    if not found:
        output += "⚠️ No information found for this number\n\n"
    
    time_str = datetime.now().strftime("%d %B %Y, %I:%M %p")
    output += f"🕐 Fetched: {time_str}\n"
    output += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    return output

def update_stats(chat_id, name, number=None):
    cid = str(chat_id)
    if cid not in user_data:
        user_data[cid] = {"name": name, "searches": 0, "numbers": []}
    user_data[cid]["searches"] += 1
    if number:
        user_data[cid]["numbers"].append({"num": number, "time": str(datetime.now())})
    save_data()

# Admin Functions
def show_dashboard(chat_id):
    total = len(user_data)
    searches = sum(u.get("searches", 0) for u in user_data.values())
    msg = f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"         📊 ADMIN DASHBOARD\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += f"👥 Total Users: {total}\n"
    msg += f"🔍 Total Searches: {searches}\n"
    msg += f"🕐 {datetime.now().strftime('%d %B %Y, %I:%M %p')}\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    send_msg(chat_id, msg, ADMIN_KEYBOARD)

def show_users(chat_id):
    if not user_data:
        send_msg(chat_id, "❌ No users found!")
        return
    msg = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "         👥 USER LIST\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, (cid, data) in enumerate(user_data.items(), 1):
        msg += f"{i}. {data.get('name', 'Unknown')[:20]}\n"
        msg += f"   🆔 <code>{cid}</code>\n"
        msg += f"   🔍 {data.get('searches', 0)} searches\n\n"
        if i >= 15:
            msg += "Showing first 15 users\n"
            break
    send_msg(chat_id, msg)

def show_logs(chat_id):
    all_searches = []
    for cid, data in user_data.items():
        for s in data.get("numbers", []):
            all_searches.append({
                "user": data.get("name", "Unknown"),
                "num": s.get("num"),
                "time": s.get("time", "")[:16]
            })
    if not all_searches:
        send_msg(chat_id, "❌ No search logs!")
        return
    msg = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "         📝 SEARCH LOGS\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, s in enumerate(all_searches[-20:][::-1], 1):
        msg += f"{i}. {s['user']} - {s['num']}\n"
        msg += f"   🕐 {s['time']}\n\n"
    send_msg(chat_id, msg)

def show_stats(chat_id):
    total = len(user_data)
    searches = sum(u.get("searches", 0) for u in user_data.values())
    avg = searches / total if total > 0 else 0
    top = sorted(user_data.values(), key=lambda x: x.get("searches", 0), reverse=True)[:5]
    msg = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "         📈 DETAILED STATS\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += f"👥 Users: {total}\n"
    msg += f"🔍 Searches: {searches}\n"
    msg += f"📊 Avg: {avg:.1f}\n\n"
    msg += "🏆 Top 5 Users:\n"
    for i, u in enumerate(top, 1):
        msg += f"{i}. {u.get('name', 'Unknown')[:15]} - {u.get('searches', 0)} searches\n"
    send_msg(chat_id, msg)

def remove_user(chat_id, target_id):
    target = str(target_id).strip()
    if str(chat_id) == target:
        send_msg(chat_id, "❌ Cannot remove yourself!")
        return
    if target in user_data:
        name = user_data[target].get("name", "Unknown")
        del user_data[target]
        save_data()
        send_msg(chat_id, f"✅ User '{name}' removed!", ADMIN_KEYBOARD)
    else:
        send_msg(chat_id, f"❌ User ID {target} not found!")

def start_remove(chat_id):
    send_msg(chat_id, "🗑️ Send user ID to remove:\n\nExample: 6323367629\n\nType /cancel to cancel")

def broadcast_msg(chat_id, msg_text):
    if not user_data:
        send_msg(chat_id, "❌ No users found!")
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
    send_msg(chat_id, "📢 Send message to broadcast:\n\nType /cancel to cancel")

# Main handler
def handle_update(update):
    global OFFSET
    if "message" not in update: return
    
    msg = update["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")
    name = msg["chat"].get("first_name", "User")
    
    print(f"📨 {name}: {text[:40]}")
    update_stats(chat_id, name)
    
    # Admin session check
    admin = is_admin(chat_id)
    
    # Handle remove mode
    if admin and admin_session.get(str(chat_id), {}).get("remove_mode"):
        if text == "/cancel":
            admin_session[str(chat_id)]["remove_mode"] = False
            send_msg(chat_id, "❌ Cancelled!", ADMIN_KEYBOARD)
        elif text.isdigit():
            remove_user(chat_id, text)
            admin_session[str(chat_id)]["remove_mode"] = False
        return
    
    # Handle broadcast mode
    if admin and admin_session.get(str(chat_id), {}).get("broadcast_mode"):
        if text == "/cancel":
            admin_session[str(chat_id)]["broadcast_mode"] = False
            send_msg(chat_id, "❌ Cancelled!", ADMIN_KEYBOARD)
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
        elif text == "📝 Logs":
            show_logs(chat_id)
        elif text == "📈 Stats":
            show_stats(chat_id)
        elif text == "🗑️ Remove User":
            start_remove(chat_id)
            admin_session[str(chat_id)] = {"remove_mode": True}
        elif text == "📢 Broadcast":
            start_broadcast(chat_id)
            admin_session[str(chat_id)] = {"broadcast_mode": True}
        elif text == "🚪 Exit Admin":
            del admin_session[str(chat_id)]
            send_msg(chat_id, "👋 Logged out!", USER_KEYBOARD)
        return
    
    # Admin login
    if text.lower() == "/admin":
        send_msg(chat_id, "🔐 Send admin password:")
        return
    if text == ADMIN_PASSWORD:
        admin_session[str(chat_id)] = {}
        send_msg(chat_id, "✅ Admin login successful!", ADMIN_KEYBOARD)
        return
    
    # User commands
    if text == "/start":
        welcome = f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        welcome += f"     🎉 WELCOME {name.upper()}! 🎉\n"
        welcome += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        welcome += f"🚀 NUMBER INFO BOT\n\n"
        welcome += f"📱 Send any 10-digit mobile number\n"
        welcome += f"📊 Get instant details\n\n"
        welcome += f"Press button below to start\n"
        welcome += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        send_msg(chat_id, welcome, USER_KEYBOARD)
        return
    
    if text == "📱 Phone Lookup":
        send_msg(chat_id, "📞 Send 10-digit mobile number:\n\nExample: 9876543210")
        return
    
    # Phone number lookup
    if text.isdigit() and len(text) == 10:
        send_msg(chat_id, f"🔍 Searching for {text}...")
        api_data = call_api(text)
        output = format_output(api_data, text)
        if len(output) > 4000:
            for i in range(0, len(output), 4000):
                send_msg(chat_id, output[i:i+4000])
        else:
            send_msg(chat_id, output)
        update_stats(chat_id, name, text)
        return
    
    # Invalid
    if text and text not in ["/start", "/admin", ADMIN_PASSWORD]:
        send_msg(chat_id, "❌ Send 10-digit number or press '📱 Phone Lookup'")

def main():
    load_data()
    Thread(target=run_health_server, daemon=True).start()
    
    print("=" * 50)
    print("🤖 NUMBER INFO BOT STARTED!")
    print("=" * 50)
    print(f"🔐 Admin Password: {ADMIN_PASSWORD}")
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
            print("\n👋 Bot stopped!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
