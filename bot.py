import requests
import json
import time
from datetime import datetime
import os
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
import sys

# ================= CONFIGURATION =================
# ✅ Updated Bot Token
BOT_TOKEN = "8797483939:AAE2LJ1sy1k1_4BOhelrcOcMaJtiR_o0xXY"

# ✅ API (same as before)
EXTERNAL_API_URL = "https://mean-folders-athletic-divide.trycloudflare.com/search/number"
API_KEY = "Mauryaji12"

# 🔐 Admin Password (changed as per your request)
ADMIN_PASSWORD = "#shashikumar"

# 👑 Admin User ID (same as before)
ADMIN_USER_ID = 6323367629
# =================================================

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
OFFSET = 0

# Data storage
user_data = {}
admin_session = {}
broadcast_state = {}

# Keyboards
USER_KEYBOARD = {
    "keyboard": [[{"text": "📱 Phone Lookup"}]],
    "resize_keyboard": True,
    "one_time_keyboard": False
}

ADMIN_KEYBOARD = {
    "keyboard": [
        [{"text": "📊 Dashboard"}, {"text": "👥 User List"}],
        [{"text": "📝 Search Logs"}, {"text": "📈 Statistics"}],
        [{"text": "📢 Broadcast"}, {"text": "🔙 Exit Admin"}]
    ],
    "resize_keyboard": True,
    "one_time_keyboard": False
}

# ============ HEALTH SERVER ============
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        status = f"""
        <html>
        <body>
        <h1>🤖 OSIANT BOT IS RUNNING!</h1>
        <p>Status: Active</p>
        <p>Users: {len(user_data)}</p>
        <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </body>
        </html>
        """
        self.wfile.write(status.encode())
    
    def log_message(self, format, *args):
        pass

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    server.serve_forever()
# =================================================

def save_user_data():
    try:
        with open("user_data.json", "w") as f:
            json.dump(user_data, f, indent=2)
    except:
        pass

def load_user_data():
    global user_data
    try:
        with open("user_data.json", "r") as f:
            user_data = json.load(f)
    except:
        user_data = {}

def save_admin_session():
    try:
        with open("admin_session.json", "w") as f:
            json.dump(admin_session, f, indent=2)
    except:
        pass

def load_admin_session():
    global admin_session
    try:
        with open("admin_session.json", "r") as f:
            admin_session = json.load(f)
    except:
        admin_session = {}

def send_message(chat_id, text, reply_markup=None, parse_mode="HTML"):
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        response = requests.post(url, json=payload, timeout=15)
        return response.json() if response.status_code == 200 else None
    except:
        return None

def send_typing_action(chat_id):
    url = f"{BASE_URL}/sendChatAction"
    try:
        requests.post(url, json={"chat_id": chat_id, "action": "typing"}, timeout=5)
    except:
        pass

def is_valid_10_digit_number(text):
    return text.isdigit() and len(text) == 10

def call_api(mobile_number):
    """✅ API call with your endpoint"""
    try:
        full_url = f"{EXTERNAL_API_URL}?key={API_KEY}&number={mobile_number}"
        print(f"📡 Calling API: {full_url}")
        
        response = requests.get(full_url, timeout=30)
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ API Response received")
                return data
            except:
                return {"error": "Invalid JSON response", "raw": response.text[:200]}
        else:
            return {"error": f"API returned {response.status_code}"}
            
    except requests.exceptions.Timeout:
        return {"error": "⏰ API Timeout! Try again"}
    except Exception as e:
        return {"error": f"❌ Error: {str(e)[:50]}"}

def format_response(api_data, mobile_number):
    """✅ Format API response nicely"""
    result = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    result += "              📱 PHONE NUMBER DETAILS 🔍\n"
    result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    result += f"🆔 Mobile: <code>{mobile_number}</code>\n\n"
    
    if "error" in api_data:
        result += f"⚠️ {api_data['error']}\n"
    elif api_data.get("status") == "success":
        results = api_data.get("result", [])
        
        if results:
            for i, record in enumerate(results, 1):
                result += f"📌 <b>Record #{i}</b>\n"
                result += "─────────────────────────────────────\n"
                result += f"👤 Name: {record.get('name', 'N/A')}\n"
                result += f"👨 Father: {record.get('fname', 'N/A')}\n"
                result += f"📞 Mobile: {record.get('num', mobile_number)}\n"
                if record.get('alt'):
                    result += f"🔄 Alternate: {record.get('alt')}\n"
                result += f"📡 Circle: {record.get('circle', 'N/A')}\n"
                result += f"📍 Address: {record.get('address', 'N/A')}\n"
                if record.get('aadhar'):
                    result += f"🆔 Aadhar: {record.get('aadhar')}\n"
                result += "─────────────────────────────────────\n\n"
        else:
            result += "⚠️ No information found for this number\n"
    else:
        result += f"⚠️ Unexpected response format\n"
        result += f"<code>{json.dumps(api_data, indent=2)[:300]}</code>\n"
    
    timestamp = datetime.now().strftime("%d %B %Y, %I:%M %p")
    result += f"\n🕐 Fetched: {timestamp}\n"
    result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    result += "              🔥 OSIANT BOT 🔥\n"
    result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    return result

def update_user_stats(chat_id, username, first_name, mobile_number=None):
    global user_data
    chat_id_str = str(chat_id)
    
    if chat_id_str not in user_data:
        user_data[chat_id_str] = {
            "chat_id": chat_id,
            "username": username or "No username",
            "first_name": first_name or "User",
            "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_searches": 0,
            "searches": []
        }
    else:
        user_data[chat_id_str]["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if mobile_number:
        user_data[chat_id_str]["total_searches"] += 1
        user_data[chat_id_str]["searches"].append({
            "number": mobile_number,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    save_user_data()

def is_admin(chat_id):
    return str(chat_id) in admin_session and admin_session[str(chat_id)].get("logged_in", False)

def show_admin_dashboard(chat_id):
    total_users = len(user_data)
    total_searches = sum(u.get("total_searches", 0) for u in user_data.values())
    today = datetime.now().strftime("%Y-%m-%d")
    active_today = sum(1 for u in user_data.values() 
                      if u.get("last_seen", "").startswith(today))
    
    dashboard = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         📊 ADMIN DASHBOARD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👥 Total Users: {total_users}
🔍 Total Searches: {total_searches}
📱 Active Today: {active_today}

🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    send_message(chat_id, dashboard, reply_markup=ADMIN_KEYBOARD)

def show_user_list(chat_id):
    if not user_data:
        send_message(chat_id, "❌ No users found!")
        return
    
    user_list = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    user_list += "           👥 USER LIST\n"
    user_list += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for idx, (chat_id_str, data) in enumerate(user_data.items(), 1):
        user_list += f"{idx}. {data.get('first_name', 'Unknown')}\n"
        user_list += f"   ID: <code>{chat_id_str}</code>\n"
        if data.get('username') and data['username'] != "No username":
            user_list += f"   @{data['username']}\n"
        user_list += f"   Searches: {data.get('total_searches', 0)}\n\n"
        if idx >= 20:
            user_list += "... (showing first 20)"
            break
    
    send_message(chat_id, user_list)

def show_search_logs(chat_id):
    if not user_data:
        send_message(chat_id, "❌ No search logs!")
        return
    
    logs = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    logs += "           📝 SEARCH LOGS\n"
    logs += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    all_searches = []
    for data in user_data.values():
        for search in data.get("searches", []):
            all_searches.append({
                "user": data.get("first_name", "Unknown"),
                "number": search.get("number"),
                "time": search.get("time")
            })
    
    all_searches.reverse()
    for idx, search in enumerate(all_searches[:30], 1):
        logs += f"{idx}. {search['user']} - {search['number']}\n"
        logs += f"   🕐 {search['time']}\n\n"
    
    if not all_searches:
        logs += "No searches yet!"
    
    send_message(chat_id, logs)

def show_statistics(chat_id):
    total_users = len(user_data)
    total_searches = sum(u.get("total_searches", 0) for u in user_data.values())
    avg_searches = total_searches / total_users if total_users > 0 else 0
    
    top_users = sorted(user_data.values(), key=lambda x: x.get("total_searches", 0), reverse=True)[:5]
    
    stats = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          📈 DETAILED STATS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Overview:
👥 Users: {total_users}
🔍 Searches: {total_searches}
📊 Avg per user: {avg_searches:.1f}

🏆 Top 5 Active Users:
"""
    for idx, user in enumerate(top_users, 1):
        stats += f"{idx}. {user.get('first_name', 'Unknown')} - {user.get('total_searches', 0)} searches\n"
    
    stats += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    send_message(chat_id, stats)

def start_broadcast(chat_id):
    broadcast_state[str(chat_id)] = {"active": True}
    msg = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
           📢 BROADCAST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Send me the message to broadcast to ALL users.

Type /cancel to cancel
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    send_message(chat_id, msg)

def send_broadcast(admin_chat_id, message):
    if not user_data:
        send_message(admin_chat_id, "❌ No users found!")
        return
    
    send_message(admin_chat_id, f"⏳ Sending to {len(user_data)} users...")
    
    success = 0
    fail = 0
    
    broadcast_msg = f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📢 ADMIN BROADCAST\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n{message}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    for chat_id_str in user_data.keys():
        try:
            result = send_message(int(chat_id_str), broadcast_msg)
            if result and result.get("ok"):
                success += 1
            else:
                fail += 1
            time.sleep(0.05)
        except:
            fail += 1
    
    report = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         📢 BROADCAST DONE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Sent: {success}
❌ Failed: {fail}
👥 Total: {len(user_data)}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    send_message(admin_chat_id, report, reply_markup=ADMIN_KEYBOARD)

def handle_admin_login(chat_id, password):
    if password.strip() == ADMIN_PASSWORD:
        admin_session[str(chat_id)] = {"logged_in": True}
        save_admin_session()
        
        welcome = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         ✅ ADMIN LOGIN SUCCESSFUL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Welcome Admin! 🎉

Use the buttons to manage:
📊 Dashboard | 👥 User List
📝 Search Logs | 📈 Statistics
📢 Broadcast | 🔙 Exit Admin
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        send_message(chat_id, welcome, reply_markup=ADMIN_KEYBOARD)
    else:
        send_message(chat_id, "❌ Invalid Password! Access Denied!")

def handle_update(update):
    global OFFSET
    
    if "message" not in update:
        return
    
    message = update["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    username = message["chat"].get("username", "")
    first_name = message["chat"].get("first_name", "User")
    
    print(f"📨 {first_name}: {text[:50]}")
    update_user_stats(chat_id, username, first_name)
    
    # Broadcast state
    if str(chat_id) in broadcast_state and broadcast_state[str(chat_id)].get("active", False):
        if text == "/cancel":
            broadcast_state[str(chat_id)]["active"] = False
            send_message(chat_id, "❌ Broadcast cancelled!", reply_markup=ADMIN_KEYBOARD)
            return
        else:
            send_broadcast(chat_id, text)
            broadcast_state[str(chat_id)]["active"] = False
            return
    
    # Admin commands
    if is_admin(chat_id):
        if text == "📊 Dashboard":
            show_admin_dashboard(chat_id)
        elif text == "👥 User List":
            show_user_list(chat_id)
        elif text == "📝 Search Logs":
            show_search_logs(chat_id)
        elif text == "📈 Statistics":
            show_statistics(chat_id)
        elif text == "📢 Broadcast":
            start_broadcast(chat_id)
        elif text == "🔙 Exit Admin":
            admin_session[str(chat_id)]["logged_in"] = False
            save_admin_session()
            send_message(chat_id, "👋 Logged out!", reply_markup=USER_KEYBOARD)
        return
    
    # Admin login
    if text.lower() == "/admin":
        send_message(chat_id, "🔐 Send admin password to login:")
        return
    
    if text == ADMIN_PASSWORD:
        handle_admin_login(chat_id, text)
        return
    
    # User commands
    if text == "/start":
        welcome = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     🎉 WELCOME {first_name.upper()}! 🎉
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 OSIANT PHONE LOOKUP BOT

✨ Features:
• ⚡ Instant 10-digit lookup
• 📊 Owner details
• 🎯 100% Free

📱 Press button below to start
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        send_message(chat_id, welcome, reply_markup=USER_KEYBOARD)
        return
    
    if text == "📱 Phone Lookup":
        send_message(chat_id, "📞 Send 10-digit mobile number:\n\nExample: 9876543210")
        return
    
    # Phone lookup
    if is_valid_10_digit_number(text):
        send_typing_action(chat_id)
        
        # Send processing
        processing = send_message(chat_id, f"⏳ Looking up {text}...")
        
        # Call API
        result = call_api(text)
        
        # Delete processing message
        if processing and processing.get('result'):
            try:
                delete_url = f"{BASE_URL}/deleteMessage"
                requests.post(delete_url, json={"chat_id": chat_id, "message_id": processing['result']['message_id']})
            except:
                pass
        
        # Send response
        if "error" in result:
            send_message(chat_id, f"❌ {result['error']}")
        else:
            update_user_stats(chat_id, username, first_name, text)
            response_text = format_response(result, text)
            send_message(chat_id, response_text)
        return
    
    # Invalid input
    if text and text != "/start" and text != ADMIN_PASSWORD:
        send_message(chat_id, "❌ Invalid! Send 10-digit number or press '📱 Phone Lookup'")

def main():
    global OFFSET
    
    load_user_data()
    load_admin_session()
    
    # Start health server
    Thread(target=run_health_server, daemon=True).start()
    
    print("=" * 50)
    print("🤖 OSIANT BOT STARTED!")
    print("=" * 50)
    print(f"🔐 Admin Password: {ADMIN_PASSWORD}")
    print(f"🤖 Bot Token: {BOT_TOKEN[:20]}...")
    print(f"🌐 API URL: {EXTERNAL_API_URL}")
    print("=" * 50)
    
    while True:
        try:
            url = f"{BASE_URL}/getUpdates"
            params = {"offset": OFFSET, "timeout": 30}
            response = requests.get(url, params=params, timeout=35)
            
            if response.status_code != 200:
                time.sleep(5)
                continue
            
            data = response.json()
            
            if not data.get("ok"):
                time.sleep(5)
                continue
            
            for update in data.get("result", []):
                handle_update(update)
                OFFSET = update["update_id"] + 1
                
        except requests.exceptions.Timeout:
            continue
        except KeyboardInterrupt:
            print("\n👋 Bot stopped!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
