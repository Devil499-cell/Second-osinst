import requests
import json
import time
from datetime import datetime
import os
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# ================= CONFIGURATION =================
BOT_TOKEN = "8797483939:AAGigJaKMxNAwtItpDPxYo7OOuIztGDJujU"
ADMIN_PASSWORD = "#shashikumar"
DEVELOPER_USERNAME = "@KINGITACHI18"

# APIs
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
        [{"text": "📞 Number Lookup"}, {"text": "🪪 Ration Card"}],
        [{"text": "📧 Email Lookup"}, {"text": "🚗 Vehicle Lookup"}],
        [{"text": "🌐 IP Lookup"}, {"text": "🏦 IFSC Lookup"}],
        [{"text": "📦 GST Lookup"}, {"text": "📱 TG to Number"}],
        [{"text": "ℹ️ Help"}]
    ],
    "resize_keyboard": True,
    "is_persistent": True
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
        "parse_mode": parse_mode,
        "allow_sending_without_reply": True
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

# ============ UNIVERSAL API CALL ============
def call_universal_api(api_type, term):
    try:
        url = f"{UNIVERSAL_API}?key={API_KEY}&type={api_type}&term={term}"
        print(f"📡 API Call: {url}")
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
    
    results = []
    if data.get("data", {}).get("success"):
        results = data["data"].get("result", {}).get("results", [])
    elif isinstance(data.get("data"), list):
        results = data["data"]
    
    if not results:
        return f"❌ No information found for {number}"
    
    first = results[0]
    
    result = f"📞 NUMBER INFO\n━━━━━━━━━━━━━━━━━━\n\n"
    result += f"🎯 Number: {number}\n\n"
    result += f"👤 Name: {first.get('NAME', first.get('name', 'N/A'))}\n\n"
    result += f"👨 Father: {first.get('fname', 'N/A')}\n\n"
    result += f"🆔 Aadhaar: {first.get('id', 'N/A')}\n\n"
    result += f"📞 Alternate: {first.get('alt', 'N/A')}\n\n"
    result += f"📡 Carrier: {first.get('circle', 'N/A')}\n\n"
    result += f"📧 Email: {first.get('email', 'N/A') or 'N/A'}\n\n"
    
    address = first.get('ADDRESS', first.get('address', 'N/A')) or 'N/A'
    if len(address) > 80:
        address = address[:77] + '...'
    result += f"📍 Address: {address}\n\n"
    
    total = len(results)
    if total > 1:
        result += f"📚 Total Records: {total}\n"
        result += f"💡 Use /full {number} to see all\n\n"
    
    result += f"⚡ POWERED BY MOD X PATEL"
    return result

def format_ration_result(data, term):
    if data.get("error"):
        return f"❌ Error: {data['error']}"
    
    ration_data = data.get("data", {})
    if not ration_data.get("success"):
        return f"❌ No information found for Aadhaar: {term}"
    
    details = ration_data.get("details", {})
    card_info = details.get("card_info", {})
    members = details.get("members", [])
    
    result = f"🪪 RATION CARD INFO\n━━━━━━━━━━━━━━━━━━\n\n"
    result += f"🎯 Aadhaar: {term}\n\n"
    result += f"📇 Card ID: {ration_data.get('ration_card_id', 'N/A')}\n\n"
    result += f"📋 Card Type: {card_info.get('Card Type', 'N/A')}\n\n"
    result += f"📍 Address: {card_info.get('Address', 'N/A')}\n\n"
    result += f"🏠 District: {card_info.get('District', 'N/A')}\n\n"
    result += f"🗺️ State: {card_info.get('State', 'N/A')}\n\n"
    result += f"📅 Issue Date: {card_info.get('Issue Date', 'N/A')}\n\n"
    result += f"🏪 FPS: {card_info.get('Home FPS', 'N/A')}\n\n"
    result += f"📊 Scheme: {card_info.get('Scheme', 'N/A')}\n\n"
    
    if members:
        result += f"👥 FAMILY MEMBERS ({len(members)})\n"
        result += f"━━━━━━━━━━━━━━━━━━\n"
        for i, member in enumerate(members[:5], 1):
            result += f"\n{i}. 👤 {member.get('member_name', 'N/A').upper()}\n"
            result += f"   👨‍👧 Relation: {member.get('relationship', 'N/A')}\n"
            result += f"   🔞 Gender: {member.get('gender', 'N/A')}\n"
            result += f"   🆔 UID: {member.get('uid_masked', 'N/A')}\n"
    
    result += f"\n⚡ POWERED BY MOD X PATEL"
    return result

def format_ip_result(data, term):
    if data.get("error"):
        return f"❌ Error: {data['error']}"
    
    ip_data = data.get("data", {}).get("result", {})
    if not ip_data:
        return f"❌ No information found for IP: {term}"
    
    result = f"🌐 IP INFORMATION\n━━━━━━━━━━━━━━━━━━\n\n"
    result += f"🎯 IP: {ip_data.get('IP', term)}\n\n"
    result += f"📍 Location: {ip_data.get('City', 'N/A')}, {ip_data.get('Region', 'N/A')}\n"
    result += f"🌍 Country: {ip_data.get('Country', 'N/A')} {ip_data.get('Flag_Emoji', '')}\n"
    result += f"📮 Postal: {ip_data.get('Postal', 'N/A')}\n\n"
    result += f"🏢 ISP: {ip_data.get('ISP', 'N/A')}\n"
    result += f"🏢 Organization: {ip_data.get('ORG', 'N/A')}\n"
    result += f"🆔 ASN: {ip_data.get('ASN', 'N/A')}\n\n"
    result += f"🌐 Domain: {ip_data.get('Domain', 'N/A')}\n"
    result += f"📡 Type: {ip_data.get('Type', 'N/A')}\n\n"
    result += f"🗺️ Coordinates: {ip_data.get('Location', 'N/A')}\n"
    result += f"⏰ Timezone: {ip_data.get('Timezone', 'N/A')} (UTC{ip_data.get('Timezone_Offset', 'N/A')})\n"
    
    result += f"\n⚡ POWERED BY MOD X PATEL"
    return result

def format_ifsc_result(data, term):
    if data.get("error"):
        return f"❌ Error: {data['error']}"
    
    bank_data = data.get("data", {}).get("result", {})
    if not bank_data:
        return f"❌ No information found for IFSC: {term}"
    
    result = f"🏦 BANK IFSC INFORMATION\n━━━━━━━━━━━━━━━━━━\n\n"
    result += f"🎯 IFSC: {bank_data.get('IFSC', term)}\n\n"
    result += f"🏛️ Bank: {bank_data.get('BANK', 'N/A')}\n"
    result += f"🏢 Branch: {bank_data.get('BRANCH', 'N/A')}\n"
    result += f"🏙️ City: {bank_data.get('CITY', 'N/A')}\n"
    result += f"📍 District: {bank_data.get('DISTRICT', 'N/A')}\n"
    result += f"🗺️ State: {bank_data.get('STATE', 'N/A')}\n\n"
    result += f"📬 Address: {bank_data.get('ADDRESS', 'N/A')}\n\n"
    result += f"📞 Contact: {bank_data.get('CONTACT', 'N/A')}\n\n"
    result += f"💳 Services:\n"
    result += f"   • NEFT: {'✅' if bank_data.get('NEFT') else '❌'}\n"
    result += f"   • RTGS: {'✅' if bank_data.get('RTGS') else '❌'}\n"
    result += f"   • IMPS: {'✅' if bank_data.get('IMPS') else '❌'}\n"
    result += f"   • UPI: {'✅' if bank_data.get('UPI') else '❌'}\n\n"
    result += f"🔢 MICR: {bank_data.get('MICR', 'N/A')}\n"
    result += f"🔑 Bank Code: {bank_data.get('BANKCODE', 'N/A')}\n"
    
    result += f"\n⚡ POWERED BY MOD X PATEL"
    return result

def format_gst_result(data, term):
    if data.get("error"):
        return f"❌ Error: {data['error']}"
    
    gst_data = data.get("data", {}).get("result", {}).get("data", {})
    if not gst_data:
        return f"❌ No information found for GST: {term}"
    
    result = f"📦 GST INFORMATION\n━━━━━━━━━━━━━━━━━━\n\n"
    result += f"🎯 GSTIN: {gst_data.get('Gstin', term)}\n\n"
    result += f"👤 Legal Name: {gst_data.get('LegalName', 'N/A')}\n"
    result += f"🏪 Trade Name: {gst_data.get('TradeName', 'N/A')}\n\n"
    result += f"📅 Registration Date: {gst_data.get('DtReg', 'N/A')}\n"
    result += f"📊 Status: {gst_data.get('Status', 'N/A')}\n"
    result += f"🔄 Block Status: {gst_data.get('BlkStatus', 'N/A')}\n"
    result += f"💰 Taxpayer Type: {gst_data.get('TxpType', 'N/A')}\n\n"
    result += f"📍 Address: {gst_data.get('AddrLoc', 'N/A')}, {gst_data.get('AddrSt', 'N/A')}\n"
    result += f"📮 PIN Code: {gst_data.get('AddrPncd', 'N/A')}\n"
    result += f"🏢 State Code: {gst_data.get('StateCode', 'N/A')}\n"
    
    result += f"\n⚡ POWERED BY MOD X PATEL"
    return result

def format_email_result(data, term):
    if data.get("error"):
        return f"❌ Error: {data['error']}"
    
    results = []
    if data.get("data", {}).get("success"):
        results = data["data"].get("result", {}).get("results", [])
    elif isinstance(data.get("data"), list):
        results = data["data"]
    
    if not results:
        return f"❌ No information found for Email: {term}"
    
    total = len(results)
    result = f"📧 EMAIL INFO\n━━━━━━━━━━━━━━━━━━\n\n"
    result += f"🎯 Email: {term}\n"
    result += f"📊 Total Records: {total}\n\n"
    
    for i, rec in enumerate(results[:3], 1):
        result += f"▶ Record {i}\n"
        result += f"   👤 Name: {rec.get('NAME', rec.get('name', 'N/A'))}\n"
        result += f"   📞 Mobile: {rec.get('MOBILE', rec.get('mobile', 'N/A'))}\n"
        result += f"   📞 Alt: {rec.get('alt', 'N/A')}\n"
        address = rec.get('ADDRESS', rec.get('address', 'N/A')) or 'N/A'
        if len(address) > 60:
            address = address[:57] + '...'
        result += f"   📍 Address: {address}\n\n"
    
    if total > 3:
        result += f"⚠️ Showing first 3 of {total} records\n"
    
    result += f"⚡ POWERED BY MOD X PATEL"
    return result

def format_vehicle_result(data, term):
    if data.get("error"):
        return f"❌ Error: {data['error']}"
    
    vehicle_data = data.get("data", {})
    if not vehicle_data:
        return f"❌ No information found for vehicle: {term.upper()}"
    
    result = f"🚗 VEHICLE INFO\n━━━━━━━━━━━━━━━━━━\n\n"
    result += f"🎯 Vehicle: {term.upper()}\n\n"
    result += f"👤 Owner: {vehicle_data.get('Owner Name', 'N/A')}\n"
    result += f"🏭 Model: {vehicle_data.get('Model Name', 'N/A')}\n"
    result += f"📝 Maker: {vehicle_data.get('Maker Model', 'N/A')}\n"
    result += f"🚦 Class: {vehicle_data.get('Vehicle Class', 'N/A')}\n"
    result += f"⛽ Fuel: {vehicle_data.get('Fuel Type', 'N/A')}\n"
    result += f"📅 Reg Date: {vehicle_data.get('Registration Date', 'N/A')}\n"
    result += f"🏢 RTO: {vehicle_data.get('Registered RTO', 'N/A')}\n"
    result += f"📍 City: {vehicle_data.get('City Name', 'N/A')}\n"
    result += f"📞 Phone: {vehicle_data.get('Phone', 'N/A')}\n"
    result += f"🏥 Insurance: {vehicle_data.get('Insurance Company', 'N/A')}\n"
    result += f"📅 Insurance Upto: {vehicle_data.get('Insurance Upto', 'N/A')}\n"
    
    result += f"\n⚡ POWERED BY MOD X PATEL"
    return result

def format_tg_result(data, term):
    if data.get("error"):
        return f"❌ Error: {data['error']}"
    
    tg_result = data.get("data", {}).get("result", {})
    if not tg_result.get("success"):
        return f"❌ No information found for Telegram ID: {term}"
    
    result = f"📱 TG TO NUMBER\n━━━━━━━━━━━━━━━━━━\n\n"
    result += f"🎯 Telegram ID: {term}\n"
    result += f"📞 Mobile: {tg_result.get('number', 'N/A')}\n"
    result += f"🌍 Country: {tg_result.get('country', 'N/A')}\n"
    result += f"📡 Code: {tg_result.get('country_code', 'N/A')}\n"
    
    result += f"\n⚡ POWERED BY MOD X PATEL"
    return result

# ============ FULL FORMATTERS ============
def format_full_number_result(data, number):
    if data.get("error"):
        return f"❌ Error: {data['error']}"
    
    results = []
    if data.get("data", {}).get("success"):
        results = data["data"].get("result", {}).get("results", [])
    
    if not results:
        return f"❌ No records found for {number}"
    
    total = len(results)
    result = f"📞 FULL NUMBER DETAILS\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    result += f"🎯 Number: {number}\n"
    result += f"📊 Total Records: {total}\n"
    result += f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    for i, rec in enumerate(results[:15], 1):
        result += f"▶ Record {i}\n"
        result += f"   👤 Name: {rec.get('NAME', rec.get('name', 'N/A'))}\n"
        result += f"   👨 Father: {rec.get('fname', 'N/A')}\n"
        result += f"   🆔 Aadhaar: {rec.get('id', 'N/A')}\n"
        result += f"   📞 Alt: {rec.get('alt', 'N/A')}\n"
        result += f"   📡 Carrier: {rec.get('circle', 'N/A')}\n"
        address = rec.get('ADDRESS', rec.get('address', 'N/A')) or 'N/A'
        if len(address) > 60:
            address = address[:57] + '...'
        result += f"   📍 Address: {address}\n\n"
    
    if total > 15:
        result += f"⚠️ Showing first 15 of {total} records\n"
    
    result += f"⚡ POWERED BY MOD X PATEL"
    return result

def format_full_ration_result(data, term):
    if data.get("error"):
        return f"❌ Error: {data['error']}"
    
    ration_data = data.get("data", {})
    if not ration_data.get("success"):
        return f"❌ No records found for Aadhaar: {term}"
    
    details = ration_data.get("details", {})
    card_info = details.get("card_info", {})
    members = details.get("members", [])
    monthly_summary = details.get("monthly_summary", [])
    
    result = f"🪪 FULL RATION CARD DETAILS\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    result += f"🎯 Aadhaar: {term}\n"
    result += f"📇 Card ID: {ration_data.get('ration_card_id', 'N/A')}\n"
    result += f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    result += f"📋 CARD INFO\n"
    result += f"━━━━━━━━━━━━━━━━━━\n"
    result += f"Type: {card_info.get('Card Type', 'N/A')}\n"
    result += f"Scheme: {card_info.get('Scheme', 'N/A')}\n"
    result += f"Issue Date: {card_info.get('Issue Date', 'N/A')}\n"
    result += f"District: {card_info.get('District', 'N/A')}\n"
    result += f"State: {card_info.get('State', 'N/A')}\n"
    result += f"FPS: {card_info.get('Home FPS', 'N/A')}\n"
    result += f"Address: {card_info.get('Address', 'N/A')}\n\n"
    
    if members:
        result += f"👥 ALL MEMBERS ({len(members)})\n"
        result += f"━━━━━━━━━━━━━━━━━━\n"
        for i, member in enumerate(members, 1):
            result += f"\n{i}. 👤 {member.get('member_name', 'N/A').upper()}\n"
            result += f"   Relation: {member.get('relationship', 'N/A')}\n"
            result += f"   Gender: {member.get('gender', 'N/A')}\n"
            result += f"   UID: {member.get('uid_masked', 'N/A')}\n"
            result += f"   Updated: {member.get('cr_last_updated', 'N/A')}\n"
    
    if monthly_summary:
        result += f"\n📆 MONTHLY SUMMARY\n"
        result += f"━━━━━━━━━━━━━━━━━━\n"
        for summary in monthly_summary:
            result += f"• {summary.get('month', 'N/A')}: {summary.get('member_count', 'N/A')} members\n"
    
    result += f"\n⚡ POWERED BY MOD X PATEL"
    return result

def format_full_email_result(data, term):
    if data.get("error"):
        return f"❌ Error: {data['error']}"
    
    results = []
    if data.get("data", {}).get("success"):
        results = data["data"].get("result", {}).get("results", [])
    
    if not results:
        return f"❌ No records found for Email: {term}"
    
    total = len(results)
    result = f"📧 FULL EMAIL DETAILS\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    result += f"🎯 Email: {term}\n"
    result += f"📊 Total Records: {total}\n"
    result += f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    for i, rec in enumerate(results[:15], 1):
        result += f"▶ Record {i}\n"
        result += f"   👤 Name: {rec.get('NAME', rec.get('name', 'N/A'))}\n"
        result += f"   📞 Mobile: {rec.get('MOBILE', rec.get('mobile', 'N/A'))}\n"
        result += f"   📞 Alt: {rec.get('alt', 'N/A')}\n"
        result += f"   📡 Carrier: {rec.get('circle', 'N/A')}\n"
        address = rec.get('ADDRESS', rec.get('address', 'N/A')) or 'N/A'
        if len(address) > 60:
            address = address[:57] + '...'
        result += f"   📍 Address: {address}\n\n"
    
    if total > 15:
        result += f"⚠️ Showing first 15 of {total} records\n"
    
    result += f"⚡ POWERED BY MOD X PATEL"
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
        name = data.get("display_name", "Unknown")
        searches = len(data.get("searches", []))
        msg += f"{i}. {name}\n   🔍 {searches}\n   🆔 <code>{cid}</code>\n\n"
    send_msg(chat_id, msg)

def show_all_history(chat_id):
    all_searches = []
    for cid, data in user_data.items():
        for s in data.get("searches", []):
            name = data.get("display_name", "Unknown")
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
    text = msg.get("text", "")
    user_info = msg.get("chat", {})
    
    print(f"📨 {user_info.get('first_name', 'User')} | {text[:50]}")
    
    update_stats(chat_id, user_info)
    admin = is_admin(chat_id)
    
    # ============ FULL COMMANDS ============
    if text and text.startswith("/full "):
        query = text.replace("/full ", "").strip()
        
        if query.isdigit() and len(query) == 10:
            update_stats(chat_id, user_info, "FULL_NUMBER", query)
            send_msg(chat_id, f"🔍 Fetching all records for number: {query}...")
            result = call_universal_api("NUMBER", query)
            send_msg(chat_id, format_full_number_result(result, query))
            return
        
        elif query.isdigit() and len(query) == 12:
            update_stats(chat_id, user_info, "FULL_RATION", query)
            send_msg(chat_id, f"🔍 Fetching full ration card details for: {query}...")
            result = call_universal_api("AADHAAR", query)
            send_msg(chat_id, format_full_ration_result(result, query))
            return
        
        elif '@' in query and '.' in query:
            update_stats(chat_id, user_info, "FULL_EMAIL", query)
            send_msg(chat_id, f"🔍 Fetching all records for Email: {query}...")
            result = call_universal_api("EMAIL", query)
            send_msg(chat_id, format_full_email_result(result, query))
            return
        
        else:
            send_msg(chat_id, "❌ Invalid!\n\nUse:\n/full 9876543210\n/full 123412341234\n/full test@gmail.com")
            return
    
    # ============ WAITING FOR INPUT ============
    if str(chat_id) in waiting_for_input:
        stype = waiting_for_input[str(chat_id)]
        del waiting_for_input[str(chat_id)]
        
        if text and text not in ["❌ Cancel", "/cancel"]:
            update_stats(chat_id, user_info, stype, text)
            send_msg(chat_id, f"🔍 Searching {stype}: {text}...")
            
            if stype == "NUMBER":
                result = call_universal_api("NUMBER", text)
                send_msg(chat_id, format_number_result(result, text))
            elif stype == "RATION":
                result = call_universal_api("AADHAAR", text)
                send_msg(chat_id, format_ration_result(result, text))
            elif stype == "IP":
                result = call_universal_api("IP", text)
                send_msg(chat_id, format_ip_result(result, text))
            elif stype == "IFSC":
                result = call_universal_api("IFSC", text)
                send_msg(chat_id, format_ifsc_result(result, text))
            elif stype == "GST":
                result = call_universal_api("GST", text)
                send_msg(chat_id, format_gst_result(result, text))
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
    
    # ============ ADMIN MODES ============
    if admin and admin_session.get(str(chat_id), {}).get("remove_mode"):
        if text == "/cancel":
            admin_session[str(chat_id)]["remove_mode"] = False
            send_msg(chat_id, "❌ Cancelled!", ADMIN_KEYBOARD)
        elif text and text.isdigit():
            remove_user(chat_id, text)
            admin_session[str(chat_id)]["remove_mode"] = False
        return
    
    if admin and admin_session.get(str(chat_id), {}).get("broadcast_mode"):
        if text == "/cancel":
            admin_session[str(chat_id)]["broadcast_mode"] = False
            send_msg(chat_id, "❌ Cancelled!", ADMIN_KEYBOARD)
        else:
            broadcast_msg(chat_id, text)
            admin_session[str(chat_id)]["broadcast_mode"] = False
        return
    
    # ============ ADMIN COMMANDS ============
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
    
    # ============ ADMIN LOGIN ============
    if text == "/admin":
        send_msg(chat_id, "🔐 Enter admin password:")
        return
    if text == ADMIN_PASSWORD:
        admin_session[str(chat_id)] = {}
        send_msg(chat_id, "✅ Admin access granted!", ADMIN_KEYBOARD)
        return
    
    # ============ /start COMMAND ============
    if text == "/start":
        welcome = f"🎉 WELCOME! 🎉\n\n"
        welcome += f"📱 <b>MULTI INFO BOT</b>\n\n"
        welcome += f"✨ <b>Features:</b>\n"
        welcome += f"• 📞 Number Lookup - Get mobile details\n"
        welcome += f"• 🪪 Ration Card - Get ration card info from Aadhaar\n"
        welcome += f"• 📧 Email Lookup - Get email details\n"
        welcome += f"• 🚗 Vehicle Lookup - Get vehicle information\n"
        welcome += f"• 🌐 IP Lookup - Get IP geolocation\n"
        welcome += f"• 🏦 IFSC Lookup - Get bank branch details\n"
        welcome += f"• 📦 GST Lookup - Get GST information\n"
        welcome += f"• 📱 TG to Number - Get mobile from Telegram ID\n\n"
        welcome += f"Send any 10-digit number directly!"
        send_msg(chat_id, welcome, USER_KEYBOARD)
        return
    
    # ============ BUTTON HANDLERS ============
    if text == "📞 Number Lookup":
        send_msg(chat_id, "📞 Send 10-digit number:\nExample: 9876543210\n\nType /cancel")
        waiting_for_input[str(chat_id)] = "NUMBER"
        return
    
    if text == "🪪 Ration Card":
        send_msg(chat_id, "🪪 Send 12-digit Aadhaar number:\nExample: 123412341234\n\nThis will fetch Ration Card details\n\nType /cancel")
        waiting_for_input[str(chat_id)] = "RATION"
        return
    
    if text == "📧 Email Lookup":
        send_msg(chat_id, "📧 Send email address:\nExample: test@gmail.com\n\nType /cancel")
        waiting_for_input[str(chat_id)] = "EMAIL"
        return
    
    if text == "🚗 Vehicle Lookup":
        send_msg(chat_id, "🚗 Send vehicle number:\nExample: GJ08CJ7132\n\nType /cancel")
        waiting_for_input[str(chat_id)] = "VEHICLE"
        return
    
    if text == "🌐 IP Lookup":
        send_msg(chat_id, "🌐 Send IP address:\nExample: 8.8.8.8\n\nType /cancel")
        waiting_for_input[str(chat_id)] = "IP"
        return
    
    if text == "🏦 IFSC Lookup":
        send_msg(chat_id, "🏦 Send IFSC code:\nExample: SBIN0000001\n\nType /cancel")
        waiting_for_input[str(chat_id)] = "IFSC"
        return
    
    if text == "📦 GST Lookup":
        send_msg(chat_id, "📦 Send GST number:\nExample: 10DJCPK4351Q1Z5\n\nType /cancel")
        waiting_for_input[str(chat_id)] = "GST"
        return
    
    if text == "📱 TG to Number":
        send_msg(chat_id, "📱 Send Telegram ID (number):\nExample: 8490678882\n\nType /cancel")
        waiting_for_input[str(chat_id)] = "TGNUMBER"
        return
    
    if text == "ℹ️ Help":
        help_msg = f"📚 HELP & COMMANDS\n\n"
        help_msg += f"🔍 <b>Available Lookups:</b>\n\n"
        help_msg += f"📞 <b>Number Lookup</b>\n   Send 10-digit number\n   /full 9876543210\n\n"
        help_msg += f"🪪 <b>Ration Card</b>\n   Send 12-digit Aadhaar\n   /full 123412341234\n\n"
        help_msg += f"📧 <b>Email Lookup</b>\n   Send email address\n   /full test@gmail.com\n\n"
        help_msg += f"🚗 <b>Vehicle Lookup</b>\n   Send vehicle number\n\n"
        help_msg += f"🌐 <b>IP Lookup</b>\n   Send IP address\n\n"
        help_msg += f"🏦 <b>IFSC Lookup</b>\n   Send IFSC code\n\n"
        help_msg += f"📦 <b>GST Lookup</b>\n   Send GST number\n\n"
        help_msg += f"📱 <b>TG to Number</b>\n   Send Telegram ID\n\n"
        help_msg += f"📋 <b>Commands:</b>\n   /start - Restart bot\n   /help - Show help\n   /full [query] - All records\n\n"
        help_msg += f"👨‍💻 <b>Developer:</b> {DEVELOPER_USERNAME}"
        send_msg(chat_id, help_msg, USER_KEYBOARD)
        return
    
    # ============ DIRECT 10-DIGIT NUMBER ============
    if text and text.isdigit() and len(text) == 10:
        waiting_for_input[str(chat_id)] = "NUMBER"
        handle_update(update)
        return
    
    if text == "/cancel":
        send_msg(chat_id, "❌ Nothing to cancel!", USER_KEYBOARD)
        return
    
    if text and not text.startswith("/"):
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
