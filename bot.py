import requests
import json
import time
from datetime import datetime
import os
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# ================= CONFIGURATION =================
BOT_TOKEN = "8797483939:AAE2LJ1sy1k1_4BOhelrcOcMaJtiR_o0xXY"
EXTERNAL_API_URL = "https://email-info-rajan-mauve.vercel.app/api?num="
ADMIN_PASSWORD = "#shashikumar"
DEVELOPER_USERNAME = "@KINGITACHI18"
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
        url = f"{EXTERNAL_API_URL}{mobile_number}"
        print(f"📡 API: {url}")
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)[:50]}

# ============ BOX STYLE FORMAT RESULT ============
def format_result(data, number):
    if data.get("error"):
        return f"❌ Error: {data['error']}"
    
    records = data.get("data", [])
    if not records:
        return f"❌ No information found for +91 {number}"
    
    first = records[0]
    
    name = first.get('name', 'N/A') or 'N/A'
    fname = first.get('fname', 'N/A') or 'N/A'
    aadhaar = first.get('id', 'N/A') or 'N/A'
    alternate = first.get('alt', 'N/A') or 'N/A'
    circle = first.get('circle', 'N/A') or 'N/A'
    email = first.get('email', 'N/A') or 'N/A'
    if email == '':
        email = 'N/A'
    address = first.get('address', 'N/A') or 'N/A'
    
    if len(address) > 80:
        address = address[:77] + '...'
    
    result = f"[ 📱 NUMBER INFO   ]  (⁠•⁠‿⁠•⁠)\n\n"
    result += f"|  🎯 Number: +91 {number}\n\n"
    result += f"|  👤 Name: {name}\n\n"
    result += f"|  👨 Father: {fname}\n\n"
    result += f"|  🆔 Aadhaar: {aadhaar}\n\n"
    result += f"|  📞 Alternate: {alternate}\n\n"
    result += f"|  📡 Carrier: {circle}\n\n"
    result += f"|  📧 Email: {email}\n\n"
    result += f"|  📍 Address: {address}\n\n"
    
    total_records = data.get('count', len(records))
    if total_records > 1:
        result += f"|    📚 Total Records: {total_records}\n"
        result += f"|💡 Use /full {number} to see all\n\n"
    
    result += f"[  POWERED BY MOD  X  PATEL  ]"
    return result

def format_full_result(data, number):
    if data.get("error"):
        return f"❌ Error: {data['error']}"
    
    records = data.get("data", [])
    if not records:
        return f"❌ No records found"
    
    result = f"[ 📱 FULL DETAILS - +91 {number} ]\n\n"
    result += f"|  ⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    for i, rec in enumerate(records[:15], 1):
        name = rec.get('name', 'N/A') or 'N/A'
        fname = rec.get('fname', 'N/A') or 'N/A'
        aadhaar = rec.get('id', 'N/A') or 'N/A'
        alternate = rec.get('alt', 'N/A') or 'N/A'
        circle = rec.get('circle', 'N/A') or 'N/A'
        email = rec.get('email', 'N/A') or 'N/A'
        if email == '':
            email = 'N/A'
        address = rec.get('address', 'N/A') or 'N/A'
        
        if len(address) > 70:
            address = address[:67] + '...'
        
        result += f"|  ▶ Record {i}\n"
        result += f"|     👤 Name: {name}\n"
        result += f"|     👨 Father: {fname}\n"
        result += f"|     🆔 Aadhaar: {aadhaar}\n"
        result += f"|     📞 Alternate: {alternate}\n"
        result += f"|     📡 Carrier: {circle}\n"
        result += f"|     📧 Email: {email}\n"
        result += f"|     📍 Address: {address}\n\n"
    
    result += f"[  POWERED BY MOD  X  PATEL  ]"
    return result

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
    
    msg = "🔥 TRENDING NUMBERS\n\n"
    for i, (num, count) in enumerate(sorted_trending, 1):
        msg += f"{i}. <code>{num}</code> - {count} searches\n"
    return msg

# ============ USER FUNCTIONS - FIXED FOR ANY SITUATION ============
def get_display_name(user_info):
    """Smart display name - works with or without username"""
    first_name = user_info.get("first_name", "")
    last_name = user_info.get("last_name", "")
    username = user_info.get("username", "")
    
    # Build full name
    if first_name and last_name:
        full_name = f"{first_name} {last_name}"
    elif first_name:
        full_name = first_name
    elif username:
        full_name = username  # Use username as name if no name set
    else:
        full_name = f"User_{user_info.get('id', 'unknown')[:6]}"
    
    # Add username prefix if username exists and is different from name
    if username and username not in full_name:
        return f"{full_name} (@{username})"
    return full_name

def update_stats(chat_id, user_info, number=None):
    cid = str(chat_id)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Extract user details
    first_name = user_info.get("first_name", "")
    last_name = user_info.get("last_name", "")
    username = user_info.get("username", "")
    
    # Debug print
    print(f"📝 User: {first_name} (@{username if username else 'no_username'}) - ID: {cid}")
    
    if cid not in user_data:
        user_data[cid] = {
            "first_name": first_name,
            "last_name": last_name,
            "username": username if username else "",
            "display_name": get_display_name(user_info),
            "searches": [],
            "joined": now
        }
        print(f"✅ New user registered: {user_data[cid]['display_name']}")
    
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
    
    msg = "📜 YOUR SEARCH HISTORY\n\n"
    for i, search in enumerate(user_data[cid]["searches"][-20:][::-1], 1):
        msg += f"{i}. <code>{search['number']}</code> - {search['time']}\n"
    return msg

def export_history(chat_id):
    cid = str(chat_id)
    if cid not in user_data or not user_data[cid].get("searches"):
        return "❌ No history to export!"
    
    export_data = {
        "user": user_data[cid].get("display_name", "Unknown"),
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
    
    msg = f"📊 ADMIN DASHBOARD\n\n"
    msg += f"👥 Total Users: {total_users}\n"
    msg += f"🔍 Total Searches: {total_searches}\n"
    msg += f"📊 Trending Numbers: {len(trending_numbers)}\n"
    msg += f"\n🕐 {datetime.now().strftime('%d %B %Y, %I:%M %p')}"
    send_msg(chat_id, msg, ADMIN_KEYBOARD)

def show_users(chat_id):
    if not user_data:
        send_msg(chat_id, "❌ No users found!")
        return
    
    msg = "👥 USER LIST\n\n"
    for i, (cid, data) in enumerate(user_data.items(), 1):
        searches = len(data.get("searches", []))
        
        # Get best display name
        if data.get('display_name'):
            display = data['display_name']
        elif data.get('username'):
            display = f"User (@{data['username']})"
        elif data.get('first_name'):
            display = data['first_name']
        else:
            display = f"User_{cid[:6]}"
        
        msg += f"{i}. {display}\n"
        msg += f"   🆔 ID: <code>{cid}</code>\n"
        msg += f"   🔍 Searches: {searches}\n"
        msg += f"   🕐 Last: {data.get('last_active', 'Unknown')[:16]}\n\n"
        if i >= 15:
            msg += "📌 Showing first 15 users\n"
            break
    
    send_msg(chat_id, msg)

def show_all_history(chat_id):
    all_searches = []
    for cid, data in user_data.items():
        for s in data.get("searches", []):
            # Get best display name
            if data.get('display_name'):
                user_display = data['display_name']
            elif data.get('username'):
                user_display = data['username']
            else:
                user_display = data.get('first_name', f"User_{cid[:6]}")
            
            all_searches.append({
                "user": user_display,
                "user_id": cid,
                "number": s.get("number"),
                "time": s.get("time", "")[:16]
            })
    
    if not all_searches:
        send_msg(chat_id, "❌ No search logs!")
        return
    
    msg = "📜 ALL SEARCH HISTORY\n\n"
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
        if data.get('display_name'):
            name = data['display_name']
        elif data.get('username'):
            name = data['username']
        else:
            name = data.get('first_name', f"User_{cid[:6]}")
        
        user_stats.append({
            "name": name,
            "searches": len(data.get("searches", []))
        })
    
    user_stats.sort(key=lambda x: x["searches"], reverse=True)
    
    msg = "🏆 TOP USERS\n\n"
    for i, u in enumerate(user_stats[:10], 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📌"
        msg += f"{medal} {i}. {u['name'][:30]}\n"
        msg += f"   🔍 {u['searches']} searches\n\n"
    
    send_msg(chat_id, msg)

def remove_user(chat_id, target_id):
    target = str(target_id).strip()
    if str(chat_id) == target:
        send_msg(chat_id, "❌ Cannot remove yourself!")
        return
    
    if target in user_data:
        name = user_data[target].get("display_name", user_data[target].get("first_name", "Unknown"))
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
    user_info = msg["chat"]
    
    # Debug print
    print(f"📨 {user_info.get('first_name', 'Unknown')} | Username: @{user_info.get('username', 'NOT_SET')} | ID: {chat_id}")
    
    # Update stats with full user info
    update_stats(chat_id, user_info)
    
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
        send_msg(chat_id, "🔐 Enter admin password:")
        return
    if text == ADMIN_PASSWORD:
        admin_session[str(chat_id)] = {}
        send_msg(chat_id, "✅ Admin access granted!", ADMIN_KEYBOARD)
        return
    
    # User commands
    if text == "/start":
        display = get_display_name(user_info)
        welcome = f"🎉 WELCOME {display}! 🎉\n\n"
        welcome += f"📱 <b>NUMBER INFO BOT</b>\n\n"
        welcome += f"✨ <b>Features:</b>\n"
        welcome += f"• 🔍 Lookup any 10-digit number\n"
        welcome += f"• 📜 View your search history\n"
        welcome += f"• 📊 See trending numbers\n\n"
        welcome += f"Press buttons below to get started!"
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
        help_msg = f"📚 HELP & COMMANDS\n\n"
        help_msg += f"🔍 Send any 10-digit number\n"
        help_msg += f"   Example: 9876543210\n\n"
        help_msg += f"📋 Commands:\n"
        help_msg += f"   /start - Restart bot\n"
        help_msg += f"   /help - Show this help\n"
        help_msg += f"   /stats - Your usage stats\n"
        help_msg += f"   /full [number] - All records\n\n"
        help_msg += f"👨‍💻 Developer: {DEVELOPER_USERNAME}"
        send_msg(chat_id, help_msg)
        return
    
    if text == "/export":
        result = export_history(chat_id)
        send_msg(chat_id, result)
        return
    
    # Phone number lookup
    if text.isdigit() and len(text) == 10:
        update_stats(chat_id, user_info, text)
        send_msg(chat_id, f"🔍 Searching for {text}...")
        api_data = call_api(text)
        send_msg(chat_id, format_result(api_data, text))
        return
    
    if text.startswith("/full "):
        num = text.replace("/full ", "").strip()
        if num.isdigit() and len(num) == 10:
            api_data = call_api(num)
            send_msg(chat_id, format_full_result(api_data, num))
        else:
            send_msg(chat_id, "❌ Invalid! Use: /full 1234567890")
        return
    
    # Invalid
    if text and text not in ["/start", "/admin", ADMIN_PASSWORD]:
        send_msg(chat_id, "❌ Invalid! Send 10-digit number or use buttons")

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
    print("\n💡 NOTE: Username tabhi show hoga jab user ne Telegram mein username set kiya ho!")
    print("💡 Agar username nahi set hai toh sirf name dikhega.")
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
