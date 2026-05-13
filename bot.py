import requests
import json
import time
from datetime import datetime
import os
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# ================= CONFIGURATION =================
# ⚠️ TOKEN REVOKE KARKE NAYA LAGANA (IMPORTANT!)
BOT_TOKEN = "8797483939:AAGigJaKMxNAwtItpDPxYo7OOuIztGDJujU"  # Naya token daalo
ADMIN_PASSWORD = "#shashikumar"
DEVELOPER_USERNAME = "@KINGITACHI18"

# APIs
NUMBER_API = "https://email-info-rajan-mauve.vercel.app/api?num="
UNIVERSAL_API = "https://all-sigma-pad-api-damo-5-day.vercel.app/api"
API_KEY = "RAJAN123"
# =================================================

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
OFFSET = 0

user_data = {}
admin_session = {}
trending_numbers = {}
waiting_for_input = {}

# ============ KEYBOARDS ============
USER_KEYBOARD = {
    "keyboard": [
        [{"text": "📞 Number Lookup"}, {"text": "🆔 Aadhaar Lookup"}],
        [{"text": "📧 Email Lookup"}, {"text": "🚗 Vehicle Lookup"}],
        [{"text": "📱 TG to Number"}],
        [{"text": "ℹ️ Help"}]
    ],
    "resize_keyboard": True
}

ADMIN_KEYBOARD = {
    "keyboard": [
        [{"text": "📊 Dashboard"}, {"text": "👥 Users"}],
        [{"text": "📜 All History"}, {"text": "🔥 Trending"}],
        [{"text": "🗑️ Remove User"}, {"text": "📢 Broadcast"}],
        [{"text": "🚪 Exit Admin"}]
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

# ============ SEND MESSAGE ============
def send_msg(chat_id, text, reply_markup=None, parse_mode="HTML"):
    url = f"{BASE_URL}/sendMessage"
    try:
        chat_id = int(chat_id)
    except:
        pass
    
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            print(f"✅ Message sent")
            return response.json()
        else:
            print(f"❌ Failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# ============ DATA MANAGEMENT ============
def save_data():
    try:
        with open("user_data.json", "w") as f:
            json.dump(user_data, f, indent=2)
        with open("trending.json", "w") as f:
            json.dump(trending_numbers, f, indent=2)
    except:
        pass

def load_data():
    global user_data, trending_numbers
    try:
        with open("user_data.json", "r") as f:
            user_data = json.load(f)
    except:
        user_data = {}
    try:
        with open("trending.json", "r") as f:
            trending_numbers = json.load(f)
    except:
        trending_numbers = {}

def is_admin(chat_id):
    return str(chat_id) in admin_session

def get_display_name(user_info):
    first_name = user_info.get("first_name", "")
    last_name = user_info.get("last_name", "")
    username = user_info.get("username", "")
    
    if first_name and last_name:
        full_name = f"{first_name} {last_name}"
    elif first_name:
        full_name = first_name
    elif username:
        full_name = username
    else:
        full_name = "User"
    
    if username and username != full_name and username not in full_name:
        return f"{full_name} (@{username})"
    return full_name

def update_stats(chat_id, user_info, search_type=None, search_term=None):
    cid = str(chat_id)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    first_name = user_info.get("first_name", "")
    last_name = user_info.get("last_name", "")
    username = user_info.get("username", "")
    display_name = get_display_name(user_info)
    
    if cid not in user_data:
        user_data[cid] = {
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "display_name": display_name,
            "searches": [],
            "joined": now,
            "last_active": now
        }
        print(f"✅ New user: {display_name}")
    else:
        if not user_data[cid].get("display_name") or user_data[cid].get("display_name") == "Unknown":
            user_data[cid]["first_name"] = first_name
            user_data[cid]["last_name"] = last_name
            user_data[cid]["username"] = username
            user_data[cid]["display_name"] = display_name
        user_data[cid]["last_active"] = now
    
    if search_term:
        user_data[cid]["searches"].append({
            "type": search_type,
            "term": search_term,
            "time": now
        })
        if search_type == "NUMBER":
            trending_numbers[search_term] = trending_numbers.get(search_term, 0) + 1
    
    save_data()

# ============ API CALLS ============
def call_number_api(number):
    try:
        clean = ''.join(filter(str.isdigit, number))
        if len(clean) == 10:
            url = f"{NUMBER_API}{clean}"
            print(f"📡 Number API: {url}")
            resp = requests.get(url, timeout=20)
            if resp.status_code == 200:
                return resp.json()
            return {"error": f"HTTP {resp.status_code}"}
        return {"error": "Send 10-digit number"}
    except Exception as e:
        return {"error": str(e)[:50]}

def call_universal_api(api_type, term):
    try:
        url = f"{UNIVERSAL_API}?key={API_KEY}&type={api_type}&term={term}"
        print(f"📡 Universal API: {url}")
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)[:50]}

# ============ FORMATTERS ============
def format_number_result(data, number):
    if data.get("error"):
        return f"❌ Error: {data['error']}"
    
    records = data.get("data", [])
    if not records:
        return f"❌ No information found for {number}"
    
    first = records[0]
    
    result = f"[ 📱 NUMBER INFO   ]  (⁠•⁠‿⁠•⁠)\n\n"
    result += f"|  🎯 Number: {number}\n\n"
    result += f"|  👤 Name: {first.get('name', 'N/A')}\n\n"
    result += f"|  👨 Father: {first.get('fname', 'N/A')}\n\n"
    result += f"|  🆔 Aadhaar: {first.get('id', 'N/A')}\n\n"
    result += f"|  📞 Alternate: {first.get('alt', 'N/A')}\n\n"
    result += f"|  📡 Carrier: {first.get('circle', 'N/A')}\n\n"
    result += f"|  📧 Email: {first.get('email', 'N/A') or 'N/A'}\n\n"
    
    address = first.get('address', 'N/A') or 'N/A'
    if len(address) > 80:
        address = address[:77] + '...'
    result += f"|  📍 Address: {address}\n\n"
    
    total = data.get('count', len(records))
    if total > 1:
        result += f"|    📚 Total Records: {total}\n"
        result += f"|💡 Use /full {number} to see all\n\n"
    
    result += f"[  POWERED BY MOD  X  PATEL  ]"
    return result

def format_full_number_result(data, number):
    if data.get("error"):
        return f"❌ Error: {data['error']}"
    
    records = data.get("data", [])
    if not records:
        return f"❌ No records found for {number}"
    
    total = len(records)
    result = f"[ 📱 FULL DETAILS - {number} ]\n\n"
    result += f"|  📊 Total Records: {total}\n"
    result += f"|  ⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    show_count = min(20, total)
    for i in range(show_count):
        rec = records[i]
        result += f"|  ▶ Record {i+1}\n"
        result += f"|     👤 Name: {rec.get('name', 'N/A')}\n"
        result += f"|     👨 Father: {rec.get('fname', 'N/A')}\n"
        result += f"|     🆔 Aadhaar: {rec.get('id', 'N/A')}\n"
        result += f"|     📞 Alternate: {rec.get('alt', 'N/A')}\n"
        result += f"|     📡 Carrier: {rec.get('circle', 'N/A')}\n"
        result += f"|     📧 Email: {rec.get('email', 'N/A') or 'N/A'}\n"
        
        address = rec.get('address', 'N/A') or 'N/A'
        if len(address) > 60:
            address = address[:57] + '...'
        result += f"|     📍 Address: {address}\n\n"
    
    if total > 20:
        result += f"|  ⚠️ Showing first 20 of {total} records\n"
    
    result += f"[  POWERED BY MOD  X  PATEL  ]"
    return result

def format_aadhaar_result(data, term):
    if data.get("error"):
        return f"❌ Error: {data['error']}"
    
    records = data.get("data", {}).get("data", [])
    if not records:
        return f"❌ No information found for Aadhaar: {term}"
    
    total = len(records)
    result = f"[ 🆔 AADHAAR INFO ]\n\n"
    result += f"|  🎯 Aadhaar: {term}\n"
    result += f"|  📊 Total Records: {total}\n\n"
    
    show_count = min(5, total)
    for i in range(show_count):
        rec = records[i]
        result += f"|  ▶ Record {i+1}\n"
        result += f"|     👤 Name: {rec.get('name', 'N/A')}\n"
        result += f"|     📞 Mobile: {rec.get('mobile', 'N/A')}\n"
        result += f"|     📞 Alt: {rec.get('alt', 'N/A')}\n"
        result += f"|     📧 Email: {rec.get('email', 'N/A') or 'N/A'}\n"
        result += f"|     📡 Carrier: {rec.get('circle', 'N/A')}\n"
        address = rec.get('address', 'N/A') or 'N/A'
        if len(address) > 60:
            address = address[:57] + '...'
        result += f"|     📍 Address: {address}\n\n"
    
    if total > 5:
        result += f"|  ⚠️ Showing first 5 of {total} records\n"
        result += f"|💡 Use /full {term} to see all records\n\n"
    
    result += f"[  POWERED BY MOD  X  PATEL  ]"
    return result

def format_full_aadhaar_result(data, term):
    if data.get("error"):
        return f"❌ Error: {data['error']}"
    
    records = data.get("data", {}).get("data", [])
    if not records:
        return f"❌ No records found for Aadhaar: {term}"
    
    total = len(records)
    result = f"[ 🆔 FULL AADHAAR DETAILS ]\n\n"
    result += f"|  🎯 Aadhaar: {term}\n"
    result += f"|  📊 Total Records: {total}\n"
    result += f"|  ⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    show_count = min(20, total)
    for i in range(show_count):
        rec = records[i]
        result += f"|  ▶ Record {i+1}\n"
        result += f"|     👤 Name: {rec.get('name', 'N/A')}\n"
        result += f"|     📞 Mobile: {rec.get('mobile', 'N/A')}\n"
        result += f"|     📞 Alt: {rec.get('alt', 'N/A')}\n"
        result += f"|     📧 Email: {rec.get('email', 'N/A') or 'N/A'}\n"
        result += f"|     📡 Carrier: {rec.get('circle', 'N/A')}\n"
        address = rec.get('address', 'N/A') or 'N/A'
        if len(address) > 60:
            address = address[:57] + '...'
        result += f"|     📍 Address: {address}\n\n"
    
    if total > 20:
        result += f"|  ⚠️ Showing first 20 of {total} records\n"
    
    result += f"[  POWERED BY MOD  X  PATEL  ]"
    return result

def format_email_result(data, term):
    if data.get("error"):
        return f"❌ Error: {data['error']}"
    
    records = data.get("data", {}).get("data", [])
    if not records:
        return f"❌ No information found for Email: {term}"
    
    total = len(records)
    result = f"[ 📧 EMAIL INFO ]\n\n"
    result += f"|  🎯 Email: {term}\n"
    result += f"|  📊 Total Records: {total}\n\n"
    
    show_count = min(5, total)
    for i in range(show_count):
        rec = records[i]
        result += f"|  ▶ Record {i+1}\n"
        result += f"|     👤 Name: {rec.get('name', 'N/A')}\n"
        result += f"|     📞 Mobile: {rec.get('mobile', 'N/A')}\n"
        result += f"|     📧 Email: {rec.get('email', 'N/A') or 'N/A'}\n"
        result += f"|     📡 Carrier: {rec.get('circle', 'N/A')}\n"
        address = rec.get('address', 'N/A') or 'N/A'
        if len(address) > 60:
            address = address[:57] + '...'
        result += f"|     📍 Address: {address}\n\n"
    
    if total > 5:
        result += f"|  ⚠️ Showing first 5 of {total} records\n"
        result += f"|💡 Use /full {term} to see all records\n\n"
    
    result += f"[  POWERED BY MOD  X  PATEL  ]"
    return result

def format_full_email_result(data, term):
    if data.get("error"):
        return f"❌ Error: {data['error']}"
    
    records = data.get("data", {}).get("data", [])
    if not records:
        return f"❌ No records found for Email: {term}"
    
    total = len(records)
    result = f"[ 📧 FULL EMAIL DETAILS ]\n\n"
    result += f"|  🎯 Email: {term}\n"
    result += f"|  📊 Total Records: {total}\n"
    result += f"|  ⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    show_count = min(20, total)
    for i in range(show_count):
        rec = records[i]
        result += f"|  ▶ Record {i+1}\n"
        result += f"|     👤 Name: {rec.get('name', 'N/A')}\n"
        result += f"|     📞 Mobile: {rec.get('mobile', 'N/A')}\n"
        result += f"|     📧 Email: {rec.get('email', 'N/A') or 'N/A'}\n"
        result += f"|     📡 Carrier: {rec.get('circle', 'N/A')}\n"
        address = rec.get('address', 'N/A') or 'N/A'
        if len(address) > 60:
            address = address[:57] + '...'
        result += f"|     📍 Address: {address}\n\n"
    
    if total > 20:
        result += f"|  ⚠️ Showing first 20 of {total} records\n"
    
    result += f"[  POWERED BY MOD  X  PATEL  ]"
    return result

def format_vehicle_result(data, term):
    if data.get("error"):
        return f"❌ Error: {data['error']}"
    
    if not data.get("success"):
        return f"❌ No information found for vehicle: {term.upper()}"
    
    vehicle_data = data.get("data", {})
    
    if not vehicle_data:
        return f"❌ No data found for vehicle: {term.upper()}"
    
    result = f"[ 🚗 VEHICLE INFORMATION ]\n\n"
    result += f"|  🎯 Vehicle No: {term.upper()}\n\n"
    result += f"|  👤 Owner: {vehicle_data.get('Owner Name', 'N/A')}\n\n"
    result += f"|  🏭 Model: {vehicle_data.get('Model Name', 'N/A')}\n\n"
    result += f"|  📝 Maker: {vehicle_data.get('Maker Model', 'N/A')}\n\n"
    result += f"|  🚦 Class: {vehicle_data.get('Vehicle Class', 'N/A')}\n\n"
    result += f"|  ⛽ Fuel: {vehicle_data.get('Fuel Type', 'N/A')}\n\n"
    result += f"|  📅 Reg Date: {vehicle_data.get('Registration Date', 'N/A')}\n\n"
    result += f"|  🏢 RTO: {vehicle_data.get('Registered RTO', 'N/A')}\n\n"
    result += f"|  📍 City: {vehicle_data.get('City Name', 'N/A')}\n\n"
    result += f"|  📞 Phone: {vehicle_data.get('Phone', 'N/A')}\n\n"
    result += f"|  🏥 Insurance: {vehicle_data.get('Insurance Company', 'N/A')}\n\n"
    result += f"|  📅 Insurance Upto: {vehicle_data.get('Insurance Upto', 'N/A')}\n\n"
    result += f"|  🔧 PUC Upto: {vehicle_data.get('PUC Upto', 'N/A')}\n\n"
    result += f"|  ✅ Fitness Upto: {vehicle_data.get('Fitness Upto', 'N/A')}\n\n"
    result += f"[  POWERED BY MOD  X  PATEL  ]"
    return result

def format_tg_result(data, term):
    if data.get("error"):
        return f"❌ Error: {data['error']}"
    
    result_data = data.get("data", {})
    tg_result = result_data.get("result", {})
    
    if not tg_result.get("success"):
        return f"❌ No information found for Telegram ID: {term}"
    
    result = f"[ 📱 TELEGRAM TO NUMBER ]\n\n"
    result += f"|  🎯 Telegram ID: {term}\n"
    result += f"|  📞 Mobile: {tg_result.get('number', 'N/A')}\n"
    result += f"|  🌍 Country: {tg_result.get('country', 'N/A')}\n"
    result += f"|  📡 Code: {tg_result.get('country_code', 'N/A')}\n"
    
    result += f"\n[  POWERED BY MOD  X  PATEL  ]"
    return result

# ============ ADMIN FUNCTIONS ============
def show_dashboard(chat_id):
    total_users = len(user_data)
    total_searches = 0
    for cid in user_data:
        total_searches += len(user_data[cid].get("searches", []))
    
    msg = f"📊 ADMIN DASHBOARD\n\n👥 Users: {total_users}\n🔍 Searches: {total_searches}\n📊 Trending: {len(trending_numbers)}"
    send_msg(chat_id, msg, ADMIN_KEYBOARD)

def show_users(chat_id):
    if not user_data:
        send_msg(chat_id, "❌ No users found!")
        return
    
    msg = "👥 USERS\n\n"
    for i, (cid, data) in enumerate(list(user_data.items())[:20], 1):
        name = data.get("display_name")
        if not name or name == "Unknown":
            name = data.get("first_name")
            if not name:
                name = data.get("username")
            if not name:
                name = f"User_{cid[-6:]}"
        
        searches = len(data.get("searches", []))
        msg += f"{i}. {name}\n   🔍 {searches}\n   🆔 <code>{cid}</code>\n\n"
    send_msg(chat_id, msg)

def show_all_history(chat_id):
    all_searches = []
    for cid, data in user_data.items():
        for s in data.get("searches", []):
            name = data.get("display_name", data.get("first_name", "Unknown"))
            all_searches.append(f"{name}: [{s.get('type', 'Unknown')}] {s.get('term', 'N/A')} - {s.get('time', 'N/A')}")
    
    if all_searches:
        msg = "📜 LAST 30 SEARCHES\n\n" + "\n".join(all_searches[-30:])
        send_msg(chat_id, msg)
    else:
        send_msg(chat_id, "No history found!")

def get_trending():
    if not trending_numbers:
        return "📊 No trending data yet!"
    
    sorted_trend = sorted(trending_numbers.items(), key=lambda x: x[1], reverse=True)[:10]
    msg = "🔥 TRENDING NUMBERS\n\n"
    for i, (num, count) in enumerate(sorted_trend, 1):
        msg += f"{i}. <code>{num}</code> - {count} searches\n"
    return msg

def remove_user(chat_id, target_id):
    target = str(target_id).strip()
    if target in user_data:
        name = user_data[target].get("display_name", "Unknown")
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
            if send_msg(int(cid), f"📢 BROADCAST\n\n{msg_text}"):
                sent += 1
            time.sleep(0.05)
        except:
            pass
    
    send_msg(chat_id, f"✅ Sent to {sent}/{len(user_data)} users", ADMIN_KEYBOARD)

# ============ MAIN HANDLER ============
def handle_update(update):
    global OFFSET
    
    if not isinstance(update, dict) or "message" not in update:
        return
    
    msg = update["message"]
    if not isinstance(msg, dict):
        return
    
    chat_id = msg.get("chat", {}).get("id", 0)
    
    if chat_id < 0:
        return
    
    text = msg.get("text", "")
    user_info = msg.get("chat", {})
    
    print(f"📨 {user_info.get('first_name', 'User')} | {text[:50]}")
    
    update_stats(chat_id, user_info)
    admin = is_admin(chat_id)
    
    # /full command
    if text and text.startswith("/full "):
        query = text.replace("/full ", "").strip()
        
        if query.isdigit() and len(query) == 10:
            update_stats(chat_id, user_info, "FULL_NUMBER", query)
            send_msg(chat_id, f"🔍 Fetching all records for number: {query}...")
            result = call_number_api(query)
            send_msg(chat_id, format_full_number_result(result, query))
            return
        
        elif query.isdigit() and len(query) == 12:
            update_stats(chat_id, user_info, "FULL_AADHAAR", query)
            send_msg(chat_id, f"🔍 Fetching all records for Aadhaar: {query}...")
            result = call_universal_api("AADHAAR", query)
            send_msg(chat_id, format_full_aadhaar_result(result, query))
            return
        
        elif '@' in query and '.' in query:
            update_stats(chat_id, user_info, "FULL_EMAIL", query)
            send_msg(chat_id, f"🔍 Fetching all records for Email: {query}...")
            result = call_universal_api("EMAIL", query)
            send_msg(chat_id, format_full_email_result(result, query))
            return
        
        elif any(c.isalpha() for c in query) and any(c.isdigit() for c in query):
            update_stats(chat_id, user_info, "VEHICLE", query)
            send_msg(chat_id, f"🔍 Fetching vehicle details for: {query.upper()}...")
            result = call_universal_api("VEHICLE", query)
            send_msg(chat_id, format_vehicle_result(result, query))
            return
        
        else:
            send_msg(chat_id, "❌ Invalid!\n\nUse:\n/full 9876543210\n/full 123412341234\n/full test@gmail.com\n/full GJ08CJ7132")
            return
    
    # Waiting for input
    if str(chat_id) in waiting_for_input:
        stype = waiting_for_input[str(chat_id)]
        del waiting_for_input[str(chat_id)]
        
        if text and text not in ["❌ Cancel", "/cancel"]:
            update_stats(chat_id, user_info, stype, text)
            send_msg(chat_id, f"🔍 Searching {stype}: {text}...")
            
            if stype == "NUMBER":
                result = call_number_api(text)
                send_msg(chat_id, format_number_result(result, text))
            elif stype == "AADHAAR":
                result = call_universal_api("AADHAAR", text)
                send_msg(chat_id, format_aadhaar_result(result, text))
            elif stype == "EMAIL":
                result = call_universal_api("EMAIL", text)
                send_msg(chat_id, format_email_result(result, text))
            elif stype == "VEHICLE":
                result = call_universal_api("VEHICLE", text)
                send_msg(chat_id, format_vehicle_result(result, text))
            elif stype == "TGNUMBER":
                result = call_universal_api("TGNUMBER", text)
                send_msg(chat_id, format_tg_result(result, text))
        else:
            keyboard = ADMIN_KEYBOARD if admin else USER_KEYBOARD
            send_msg(chat_id, "❌ Cancelled!", keyboard)
        return
    
    # Admin remove mode
    if admin and admin_session.get(str(chat_id), {}).get("remove_mode"):
        if text == "/cancel":
            admin_session[str(chat_id)]["remove_mode"] = False
            send_msg(chat_id, "❌ Cancelled!", ADMIN_KEYBOARD)
        elif text and text.isdigit():
            remove_user(chat_id, text)
            admin_session[str(chat_id)]["remove_mode"] = False
        return
    
    # Admin broadcast mode
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
        elif text == "🔥 Trending":
            send_msg(chat_id, get_trending())
        elif text == "🗑️ Remove User":
            send_msg(chat_id, "🗑️ Send user ID to remove:\nType /cancel")
            admin_session[str(chat_id)] = {"remove_mode": True}
        elif text == "📢 Broadcast":
            send_msg(chat_id, "📢 Send message to broadcast:\nType /cancel")
            admin_session[str(chat_id)] = {"broadcast_mode": True}
        elif text == "🚪 Exit Admin":
            if str(chat_id) in admin_session:
                del admin_session[str(chat_id)]
            send_msg(chat_id, "👋 Logged out!", USER_KEYBOARD)
        return
    
    # Admin login
    if text == "/admin":
        send_msg(chat_id, "🔐 Enter admin password:")
        return
    if text == ADMIN_PASSWORD:
        admin_session[str(chat_id)] = {}
        send_msg(chat_id, "✅ Admin access granted!", ADMIN_KEYBOARD)
        return
    
    # ============ /start COMMAND (EXACTLY AS YOU WANTED) ============
    if text == "/start":
        welcome = f"🎉 WELCOME! 🎉\n\n"
        welcome += f"📱 <b>MULTI INFO BOT</b>\n\n"
        welcome += f"✨ <b>Features:</b>\n"
        welcome += f"• 📞 Number Lookup - Get mobile details\n"
        welcome += f"• 🆔 Aadhaar Lookup - Get Aadhaar info\n"
        welcome += f"• 📧 Email Lookup - Get email details\n"
        welcome += f"• 🚗 Vehicle Lookup - Get vehicle information\n"
        welcome += f"• 📱 TG to Number - Get mobile from Telegram ID\n\n"
        welcome += f"Send any 10-digit number directly!"
        send_msg(chat_id, welcome, USER_KEYBOARD)
        return
    
    if text == "📞 Number Lookup":
        send_msg(chat_id, "📞 Send 10-digit number:\nExample: 9876543210\n\nType /cancel")
        waiting_for_input[str(chat_id)] = "NUMBER"
        return
    
    if text == "🆔 Aadhaar Lookup":
        send_msg(chat_id, "🆔 Send 12-digit Aadhaar:\nExample: 123412341234\n\nType /cancel")
        waiting_for_input[str(chat_id)] = "AADHAAR"
        return
    
    if text == "📧 Email Lookup":
        send_msg(chat_id, "📧 Send email:\nExample: test@gmail.com\n\nType /cancel")
        waiting_for_input[str(chat_id)] = "EMAIL"
        return
    
    if text == "🚗 Vehicle Lookup":
        send_msg(chat_id, "🚗 Send vehicle number:\nExample: GJ08CJ7132\n\nType /cancel")
        waiting_for_input[str(chat_id)] = "VEHICLE"
        return
    
    if text == "📱 TG to Number":
        send_msg(chat_id, "📱 Send Telegram ID:\nExample: 8490678882\n\nType /cancel")
        waiting_for_input[str(chat_id)] = "TGNUMBER"
        return
    
    if text == "ℹ️ Help":
        help_msg = f"📚 HELP & COMMANDS\n\n"
        help_msg += f"🔍 <b>Available Lookups:</b>\n\n"
        help_msg += f"📞 <b>Number Lookup</b>\n"
        help_msg += f"   Send 10-digit number\n"
        help_msg += f"   Use /full 9876543210 for all records\n\n"
        help_msg += f"🆔 <b>Aadhaar Lookup</b>\n"
        help_msg += f"   Send 12-digit Aadhaar\n"
        help_msg += f"   Use /full 123412341234 for all records\n\n"
        help_msg += f"📧 <b>Email Lookup</b>\n"
        help_msg += f"   Send email address\n"
        help_msg += f"   Use /full test@gmail.com for all records\n\n"
        help_msg += f"🚗 <b>Vehicle Lookup</b>\n"
        help_msg += f"   Send vehicle number\n\n"
        help_msg += f"📱 <b>TG to Number</b>\n"
        help_msg += f"   Send Telegram ID\n\n"
        help_msg += f"📋 <b>Commands:</b>\n"
        help_msg += f"   /start - Restart bot\n"
        help_msg += f"   /help - Show this help\n"
        help_msg += f"   /full [query] - Show all records\n\n"
        help_msg += f"👨‍💻 <b>Developer:</b> {DEVELOPER_USERNAME}"
        send_msg(chat_id, help_msg, USER_KEYBOARD)
        return
    
    # Direct number (10 digits)
    if text and text.isdigit() and len(text) == 10:
        waiting_for_input[str(chat_id)] = "NUMBER"
        handle_update(update)
        return
    
    if text == "/cancel":
        send_msg(chat_id, "❌ Nothing to cancel!", USER_KEYBOARD)
        return
    
    if text:
        send_msg(chat_id, "❌ Invalid! Use buttons or send 10-digit number", USER_KEYBOARD)

# ============ MAIN ============
def main():
    load_data()
    Thread(target=run_health_server, daemon=True).start()
    
    print("=" * 50)
    print("🤖 MULTI INFO BOT STARTED")
    print(f"👥 Loaded users: {len(user_data)}")
    print(f"👨‍💻 Developer: {DEVELOPER_USERNAME}")
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
                        if isinstance(update, dict):
                            handle_update(update)
                            OFFSET = update.get("update_id", OFFSET) + 1
            time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n👋 Bot stopped!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
