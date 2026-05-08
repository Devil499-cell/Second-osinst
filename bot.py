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
DEVELOPER_USERNAME = "@KINGITACHI18"  # Your username in help
# =================================================

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
OFFSET = 0

user_data = {}
admin_session = {}
trending_numbers = {}

# ============ KEYBOARDS ============
USER_KEYBOARD = {
    "keyboard": [
        [{"text": "📱 Phone Lookup"}],
        [{"text": "📜 My History"}, {"text": "📊 Trending"}],
        [{"text": "ℹ️ Help"}]
    ],
    "resize_keyboard": True
}

ADMIN_KEYBOARD = {
    "keyboard": [
        [{"text": "📊 Dashboard"}, {"text": "👥 Users"}],
        [{"text": "📜 All History"}, {"text": "🏆 Top Users"}],
        [{"text": "🔥 Trending Numbers"}, {"text": "🗑️ Remove User"}],
        [{"text": "📢 Broadcast"}, {"text": "🚪 Exit Admin"}]
    ],
    "resize_keyboard": True
}

# ============ HEALTH SERVER ============
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Running")
    def log_message(self, *args): pass

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), HealthHandler).serve_forever()

# ============ DATA MANAGEMENT ============
def save_data():
    try:
        with open("user_data.json", "w") as f:
            json.dump(user_data, f, indent=2)
        with open("trending.json", "w") as f:
            json.dump(trending_numbers, f, indent=2)
    except: pass

def load_data():
    global user_data, trending_numbers
    try:
        with open("user_data.json", "r") as f:
            user_data = json.load(f)
    except: user_data = {}
    try:
        with open("trending.json", "r") as f:
            trending_numbers = json.load(f)
    except: trending_numbers = {}

def send_msg(chat_id, text, reply_markup=None, parse_mode="HTML"):
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        return requests.post(url, json=payload, timeout=15).json()
    except: return None

def is_admin(chat_id):
    return str(chat_id) in admin_session

# ============ API CALL ============
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

# ============ TRENDING NUMBERS ============
def update_trending(number):
    if number in trending_numbers:
        trending_numbers[number] += 1
    else:
        trending_numbers[number] = 1
    save_data()

def get_trending():
    sorted_trending = sorted(trending_numbers.items(), key=lambda x: x[1], reverse=True)[:10]
    if not sorted_trending:
        return "📊 No trending data yet!"
    
    msg = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "         🔥 TRENDING NUMBERS\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, (num, count) in enumerate(sorted_trending, 1):
        msg += f"{i}. <code>{num}</code>\n"
        msg += f"   🔍 Searched: {count} times\n\n"
    return msg

# ============ USER FUNCTIONS ============
def update_stats(chat_id, name, number=None):
    cid = str(chat_id)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if cid not in user_data:
        user_data[cid] = {
            "name": name,
            "searches": [],
            "joined": now
        }
    
    if number:
        user_data[cid]["searches"].append({
            "number": number,
            "time": now
        })
        update_trending(number)
    
    user_data[cid]["last_active"] = now
    save_data()

def get_user_history(chat_id):
    cid = str(chat_id)
    if cid not in user_data or not user_data[cid].get("searches"):
        return "📜 No search history yet!\n\nPress 📱 Phone Lookup to start."
    
    msg = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "         📜 YOUR SEARCH HISTORY\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for i, search in enumerate(user_data[cid]["searches"][-20:][::-1], 1):
        msg += f"{i}. <code>{search['number']}</code>\n"
        msg += f"   🕐 {search['time']}\n\n"
    
    return msg

def export_history(chat_id):
    cid = str(chat_id)
    if cid not in user_data or not user_data[cid].get("searches"):
        return "❌ No history to export!"
    
    export_data = {
        "user": user_data[cid]["name"],
        "user_id": chat_id,
        "export_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_searches": len(user_data[cid]["searches"]),
        "search_history": user_data[cid]["searches"]
    }
    
    json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
    
    if len(json_str) > 4000:
        return "📤 History too long! Use /export_small for last 10 searches"
    
    return f"<pre>{json_str}</pre>"

# ============ ADMIN FUNCTIONS ============
def show_dashboard(chat_id):
    total_users = len(user_data)
    total_searches = sum(len(u.get("searches", [])) for u in user_data.values())
    
    msg = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "         📊 ADMIN DASHBOARD\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += f"👥 Total Users: {total_users}\n"
    msg += f"🔍 Total Searches: {total_searches}\n"
    msg += f"📊 Trending Numbers: {len(trending_numbers)}\n"
    msg += f"\n🕐 {datetime.now().strftime('%d %B %Y, %I:%M %p')}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    send_msg(chat_id, msg, ADMIN_KEYBOARD)

def show_users(chat_id):
    if not user_data:
        send_msg(chat_id, "❌ No users found!")
        return
    
    msg = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "         👥 USER LIST\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for i, (cid, data) in enumerate(user_data.items(), 1):
        searches = len(data.get("searches", []))
        msg += f"{i}. {data.get('name', 'Unknown')[:20]}\n"
        msg += f"   🆔 <code>{cid}</code>\n"
        msg += f"   🔍 {searches} searches\n"
        msg += f"   🕐 Last: {data.get('last_active', 'Unknown')[:16]}\n\n"
        if i >= 15:
            msg += "Showing first 15 users\n"
            break
    
    send_msg(chat_id, msg)

def show_all_history(chat_id):
    all_searches = []
    for cid, data in user_data.items():
        for s in data.get("searches", []):
            all_searches.append({
                "user": data.get("name", "Unknown"),
                "user_id": cid,
                "number": s.get("number"),
                "time": s.get("time", "")[:16]
            })
    
    if not all_searches:
        send_msg(chat_id, "❌ No search logs!")
        return
    
    msg = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "         📜 ALL SEARCH HISTORY\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for i, s in enumerate(all_searches[-30:][::-1], 1):
        msg += f"{i}. {s['user']}\n"
        msg += f"   📞 {s['number']}\n"
        msg += f"   🕐 {s['time']}\n\n"
    
    send_msg(chat_id, msg)

def show_top_users(chat_id):
    if not user_data:
        send_msg(chat_id, "❌ No data!")
        return
    
    user_stats = []
    for cid, data in user_data.items():
        user_stats.append({
            "name": data.get("name", "Unknown"),
            "searches": len(data.get("searches", []))
        })
    
    user_stats.sort(key=lambda x: x["searches"], reverse=True)
    
    msg = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "         🏆 TOP USERS\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for i, u in enumerate(user_stats[:10], 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📌"
        msg += f"{medal} {i}. {u['name'][:20]}\n"
        msg += f"   🔍 {u['searches']} searches\n\n"
    
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
        send_msg(chat_id, f"✅ Removed user '{name}'!", ADMIN_KEYBOARD)
    else:
        send_msg(chat_id, f"❌ User {target} not found!")

def broadcast_msg(chat_id, msg_text):
    if not user_data:
        send_msg(chat_id, "❌ No users found!")
        return
    
    send_msg(chat_id, f"⏳ Sending to {len(user_data)} users...")
    sent = 0
    
    for cid in user_data.keys():
        try:
            if send_msg(int(cid), f"📢 ADMIN BROADCAST\n\n{msg_text}"):
                sent += 1
            time.sleep(0.05)
        except: pass
    
    send_msg(chat_id, f"✅ Sent to {sent}/{len(user_data)} users", ADMIN_KEYBOARD)

# ============ MAIN HANDLER ============
def handle_update(update):
    global OFFSET
    if "message" not in update: return
    
    msg = update["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")
    name = msg["chat"].get("first_name", "User")
    
    print(f"📨 {name}: {text[:50]}")
    update_stats(chat_id, name)
    
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
        elif text == "📜 All History":
            show_all_history(chat_id)
        elif text == "🏆 Top Users":
            show_top_users(chat_id)
        elif text == "🔥 Trending Numbers":
            send_msg(chat_id, get_trending())
        elif text == "🗑️ Remove User":
            send_msg(chat_id, "🗑️ Send user ID to remove:\nExample: 6323367629\n\nType /cancel")
            admin_session[str(chat_id)] = {"remove_mode": True}
        elif text == "📢 Broadcast":
            send_msg(chat_id, "📢 Send message to broadcast:\nType /cancel")
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
        welcome += f"📱 <b>NUMBER INFO BOT</b>\n\n"
        welcome += f"✨ <b>Features:</b>\n"
        welcome += f"• 🔍 Lookup any 10-digit number\n"
        welcome += f"• 📜 View your search history\n"
        welcome += f"• 📊 See trending numbers\n\n"
        welcome += f"Press buttons below to get started!\n"
        welcome += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        send_msg(chat_id, welcome, USER_KEYBOARD)
        return
    
    if text == "📱 Phone Lookup":
        send_msg(chat_id, "📞 Send 10-digit mobile number:\n\nExample: 9876543210")
        return
    
    if text == "📜 My History":
        send_msg(chat_id, get_user_history(chat_id))
        return
    
    if text == "📊 Trending":
        send_msg(chat_id, get_trending())
        return
    
    if text == "ℹ️ Help":
        help_msg = f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        help_msg += f"         📚 HELP & COMMANDS\n"
        help_msg += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        help_msg += f"🔍 <b>Basic Commands:</b>\n"
        help_msg += f"• Send any 10-digit number - Lookup info\n"
        help_msg += f"• /start - Restart bot\n\n"
        help_msg += f"📜 <b>History:</b>\n"
        help_msg += f"• 📜 My History - View your searches\n"
        help_msg += f"• /export - Export your history as JSON\n\n"
        help_msg += f"📊 <b>Other:</b>\n"
        help_msg += f"• 📊 Trending - Most searched numbers\n\n"
        help_msg += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        help_msg += f"👨‍💻 Developer: {DEVELOPER_USERNAME}\n"
        help_msg += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        send_msg(chat_id, help_msg)
        return
    
    if text == "/export":
        result = export_history(chat_id)
        send_msg(chat_id, result)
        return
    
    # Phone number lookup
    if text.isdigit() and len(text) == 10:
        send_msg(chat_id, f"🔍 Searching for {text}...")
        api_data = call_api(text)
        json_response = json.dumps(api_data, indent=2, ensure_ascii=False)
        
        if len(json_response) > 4000:
            parts = [json_response[i:i+4000] for i in range(0, len(json_response), 4000)]
            for part in parts:
                send_msg(chat_id, f"<pre>{part}</pre>")
        else:
            send_msg(chat_id, f"<pre>{json_response}</pre>")
        
        update_stats(chat_id, name, text)
        return
    
    # Invalid
    if text and text not in ["/start", "/admin", ADMIN_PASSWORD]:
        send_msg(chat_id, "❌ Invalid! Send 10-digit number or use buttons\n\nType /help for commands")

# ============ MAIN ============
def main():
    load_data()
    Thread(target=run_health_server, daemon=True).start()
    
    print("=" * 60)
    print("🤖 NUMBER INFO BOT STARTED")
    print("=" * 60)
    print(f"🔐 Admin Password: {ADMIN_PASSWORD}")
    print(f"🌐 API: {EXTERNAL_API_URL}")
    print(f"👥 Loaded users: {len(user_data)}")
    print("=" * 60)
    
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
