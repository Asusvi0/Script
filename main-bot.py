import json
import os
import requests
import telebot
from telebot import types
import concurrent.futures


# Your bot token
API_TOKEN = '7586163097:AAFW-1cPYSRPGOdq9zJr0kOJh--gknZjyUU'
bot = telebot.TeleBot(API_TOKEN)

ADMIN_ID = 5492311099  # Change this to the admin's Telegram user ID
# โหลดแอดมินจากไฟล์

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def load_admins():
    if os.path.exists('admins.json'):
        with open('admins.json', 'r') as f:
            return json.load(f)
    return [ADMIN_ID]

def save_admins(admins):
    with open('admins.json', 'w') as f:
        json.dump(admins, f, indent=4)

ADMINS = load_admins()

def is_admin(user_id):
    return user_id in ADMINS

@bot.message_handler(commands=['adminmenu'])
def admin_menu(message: types.Message):
    if not is_admin(message.from_user.id):
        return bot.reply_to(message, "❌ คุณไม่ใช่แอดมิน ไม่สามารถใช้คำสั่งนี้ได้")

    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton("➕ เพิ่มแอดมิน", callback_data="add_admin"),
        types.InlineKeyboardButton("➖ ลบแอดมิน", callback_data="remove_admin"),
        types.InlineKeyboardButton("📜 รายชื่อแอดมิน", callback_data="list_admins"),
        types.InlineKeyboardButton("🔑 สร้างคีย์", callback_data="create_key"),
        types.InlineKeyboardButton("📢 ส่งข้อความ", callback_data="broadcast"),
    ]
    markup.add(*buttons)
    bot.send_message(message.chat.id, "📌 **เมนูแอดมิน** 📌\nเลือกคำสั่งที่ต้องการ", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=['addadmin'])
def add_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "❌ คุณไม่ใช่แอดมินหลัก ไม่สามารถเพิ่มแอดมินได้")

    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        return bot.reply_to(message, "❌ คำสั่งไม่ถูกต้อง! ใช้ /addadmin <user_id>")

    new_admin_id = int(args[1])
    if new_admin_id in ADMINS:
        return bot.reply_to(message, "⚠️ ผู้ใช้นี้เป็นแอดมินอยู่แล้ว")

    ADMINS.append(new_admin_id)
    save_admins(ADMINS)
    bot.reply_to(message, f"✅ เพิ่มแอดมินสำเร็จ! ID: {new_admin_id}")

@bot.message_handler(commands=['removeadmin'])
def remove_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "❌ คุณไม่ใช่แอดมินหลัก ไม่สามารถลบแอดมินได้")

    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        return bot.reply_to(message, "❌ คำสั่งไม่ถูกต้อง! ใช้ /removeadmin <user_id>")

    admin_id = int(args[1])
    if admin_id == ADMIN_ID:
        return bot.reply_to(message, "⚠️ ไม่สามารถลบแอดมินหลักได้!")

    if admin_id not in ADMINS:
        return bot.reply_to(message, "⚠️ ผู้ใช้คนนี้ไม่ใช่แอดมิน")

    ADMINS.remove(admin_id)
    save_admins(ADMINS)
    bot.reply_to(message, f"✅ ลบแอดมินสำเร็จ! ID: {admin_id}")
    
    
# ฟังก์ชัน redeem
@bot.message_handler(commands=['redeem'])
def redeem(message: types.Message):
    args = message.text.split()
    if len(args) != 2:
        return bot.reply_to(message, "คำสั่งไม่ถูกต้อง. ใช้ /redeem <key>")

    key = args[1]
    
    if not os.path.exists('key.json'):
        return bot.reply_to(message, "ไม่มีข้อมูลคีย์")
    
    with open('key.json', 'r') as f:
        keys = json.load(f)

    if key not in keys:
        return bot.reply_to(message, "คีย์ไม่ถูกต้อง")
    
    user_id = str(message.from_user.id)
    
    if not os.path.exists('user.json'):
        users = {}
    else:
        with open('user.json', 'r') as f:
            users = json.load(f)
    
    users.setdefault(user_id, {"used_keys": {}, "remaining_keys": {}})
    users[user_id]["remaining_keys"][key] = users[user_id]["remaining_keys"].get(key, 0) + keys[key]
    users[user_id]["used_keys"].setdefault(key, 0)
    
    with open('user.json', 'w') as f:
        json.dump(users, f, indent=4)

    del keys[key]
    with open('key.json', 'w') as f:
        json.dump(keys, f, indent=4)

    bot.reply_to(message, f"คีย์ {key} ถูก redeem และเพิ่มจำนวนการใช้งานเรียบร้อยแล้ว")

    # แจ้งเตือนแอดมิน
    bot.send_message(
        ADMIN_ID, 
        f"🔔 มีการใช้คีย์ 🔔\n"
      #  f"👤 ผู้ใช้: {username} ({user_id})\n"
        f"🔑 คีย์ที่ใช้: {key}"
    )
# ฟังก์ชัน info
@bot.message_handler(commands=['info'])
def info(message: types.Message):
    user_id = str(message.from_user.id)
    
    if not os.path.exists('user.json'):
        return bot.reply_to(message, "คุณยังไม่มีข้อมูลคีย์")

    with open('user.json', 'r') as f:
        users = json.load(f)

    if user_id not in users or not users[user_id]["remaining_keys"]:
        return bot.reply_to(message, "คุณไม่มีคีย์ที่ใช้งานอยู่")

    response = "สถานะการใช้งานคีย์ของคุณ:\n"
    for key, remaining_usage in users[user_id]["remaining_keys"].items():
        used_usage = users[user_id]["used_keys"].get(key, 0)
        response += (f"ข้อมูลการใช้งาน 🔋\n"
                     f"จำนวนการใช้งานที่เหลือ: {remaining_usage} ครั้ง📱\n"
                     f"จำนวนที่ใช้ไปแล้ว: {used_usage} ครั้ง❗\n\n")
    
    bot.reply_to(message, response)

@bot.message_handler(commands=['activeusers'])
def active_user_count(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "คุณไม่ใช่แอดมิน ไม่สามารถใช้คำสั่งนี้ได้.")

    if not os.path.exists('user.json'):
        return bot.reply_to(message, "ยังไม่มีผู้ใช้ที่ใช้คีย์")

    with open('user.json', 'r') as f:
        users = json.load(f)

    active_users = sum(1 for user in users.values() if user["remaining_keys"])
    bot.reply_to(message, f"📊 จำนวนผู้ใช้ที่มีคีย์เหลืออยู่: {active_users} คน")


@bot.message_handler(commands=['help'])
def help_command(message: types.Message):
    help_text = (
        "คำสั่งที่ใช้ได้ 🌐:\n"
        "/start - เริ่มต้นการใช้งานบอท🟢\n"
        "/help - แสดงข้อความช่วยเหลือ🔋\n"
        "/search <URL> - ค้นหา URL ในไฟล์ log📄\n"
        "/redeem <key> - ใช้คีย์เพื่อเพิ่มจำนวนการใช้งาน 🔑\n"
        "/info - แสดงข้อมูลสถานะการใช้งานคีย์ของคุณ👤"
    )
    bot.reply_to(message, help_text)


# ตัวแปร URL และการใช้งานที่จำเป็น
url = ''  # URL ที่ค้นหา
directory_path = '/storage/emulated/0/bot/dataleak/'
output_file_path = ''

@bot.message_handler(commands=['search'])
def search_url(message: types.Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "ไม่มีชื่อผู้ใช้"

    # เช็คว่าไฟล์ user.json มีหรือไม่
    if not os.path.exists('user.json'):
        return bot.reply_to(message, "กรุณาเช่าคีย์ ผ่านแอดมิน❗❗")

    with open('user.json', 'r') as f:
        users = json.load(f)

    # ตรวจสอบคีย์ของผู้ใช้
    if user_id not in users or not users[user_id]["remaining_keys"]:
        return bot.reply_to(message, "คุณยังไม่มีคีย์ใช้งาน\nกรุณาเช่าคีย์ ผ่านแอดมิน❗❗")

    user_keys = users[user_id]["remaining_keys"]
    if not user_keys:
        return bot.reply_to(message, "คุณไม่มีคีย์ที่สามารถใช้งานได้ ❌")

    key_to_use = next(iter(user_keys))

    if users[user_id]["remaining_keys"][key_to_use] <= 0:
        return bot.reply_to(message, "❌ คีย์ของคุณหมดจำนวนการใช้งานแล้ว ❌")

    args = message.text.split()
    if len(args) != 2:
        return bot.reply_to(message, "คำสั่งไม่ถูกต้อง. ใช้ /search <URL>")

    url = args[1]
    output_file_path = f"{url}.txt"

    searching_msg = bot.reply_to(message, "🔍 กำลังค้นหา URL ของคุณ โปรดรอสักครู่...")

    # ฟังก์ชันค้นหา URL ในไฟล์
   # searching_msg = bot.reply_to(message, "🔍 กำลังค้นหา URL ของคุณ โปรดรอสักครู่...")

    def check_log_files(directory, output_file_path):
        found_lines = set()
        try:
            with open(output_file_path, 'w', encoding='utf-8') as output_file:
                for file_name in os.listdir(directory):
                    file_path = os.path.join(directory, file_name)
                    if os.path.isfile(file_path):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as file:
                                for line in file:
                                    if url in line and line not in found_lines:
                                        output_file.write(line)
                                        found_lines.add(line)
                        except UnicodeDecodeError:
                            with open(file_path, 'rb') as file:
                                for line in file:
                                    try:
                                        decoded_line = line.decode('utf-8')
                                        if url in decoded_line and decoded_line not in found_lines:
                                            output_file.write(decoded_line)
                                            found_lines.add(decoded_line)
                                    except UnicodeDecodeError:
                                        continue

        except FileNotFoundError:
            bot.edit_message_text("❌ ไม่พบไดเรกทอรีที่เก็บไฟล์ log", message.chat.id, searching_msg.message_id)
            return
        except PermissionError:
            bot.edit_message_text("❌ ไม่มีสิทธิ์เข้าถึงไฟล์ log", message.chat.id, searching_msg.message_id)
            return

    check_log_files(directory_path, output_file_path)

    bot.delete_message(message.chat.id, searching_msg.message_id)
    # หากพบผลลัพธ์ ส่งไฟล์ให้ผู้ใช้
    if os.path.exists(output_file_path) and os.path.getsize(output_file_path) > 0:
        with open(output_file_path, 'rb') as file:
            bot.send_document(message.chat.id, file, caption="✅ ค้นหาสำเร็จ ✅")

        # ลดจำนวนคีย์ที่ใช้ไป
        users[user_id]["remaining_keys"][key_to_use] -= 1
        users[user_id]["used_keys"][key_to_use] += 1

        if users[user_id]["remaining_keys"][key_to_use] <= 0:
            del users[user_id]["remaining_keys"][key_to_use]

        # บันทึกข้อมูลผู้ใช้ใหม่
        with open('user.json', 'w') as f:
            json.dump(users, f, indent=4)

        # แจ้งแอดมิน
        bot.send_message(
            ADMIN_ID,
            f"🔍 มีการค้นหา URL 🔍\n"
            f"👤 ผู้ใช้: {username} ({user_id})\n"
            f"🔗 ค้นหา URL: {url}\n"
            f"🔑 ใช้คีย์: {key_to_use}\n"
            f"📉 คงเหลือ: {users[user_id]['remaining_keys'].get(key_to_use, 0)} ครั้ง"
        )
    else:
        bot.reply_to(message, "❌ ไม่พบข้อมูลที่ตรงกับ URL ที่คุณค้นหา ❌")

    # ลบข้อความค้นหา
    #bot.delete_message(message.chat.id, searching_msg.message_id)

bot.polling(none_stop=True)

