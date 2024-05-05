import telebot
import requests
from urllib.parse import urlparse, parse_qs
import sys

# Khởi tạo bot với token của bạn
bot_token = '7193015461:AAGlO0bUEFB17GqqSlsNCj4DfAIHvPx0qGM'
bot = telebot.TeleBot(bot_token)

def get_facebook_id_from_url(url):
    # Trích xuất phần path của URL
    path = urlparse(url).path
    
    # Kiểm tra nếu URL không chứa dấu ? (không có query parameters)
    if '?' not in path:
        # Trích xuất ID từ phần path bằng cách loại bỏ dấu / ở đầu và cuối
        return path.strip('/')
    else:
        # Trích xuất query parameters từ URL
        query_params = parse_qs(urlparse(url).query)
        
        # Kiểm tra nếu query parameters có chứa 'id'
        if 'id' in query_params:
            return query_params['id'][0]
        else:
            return None

def main():
    # Nhận link Facebook từ dòng lệnh
    url_input = sys.argv[1]

    # Trích xuất ID từ link Facebook
    facebook_id = get_facebook_id_from_url(url_input)

    if facebook_id:
        # Tạo URL để gửi yêu cầu API
        url = "https://wusteam.com/api/find-info-facebook"
        params = {
            "FindInfoFacebook": "true",
            "input": facebook_id
        }

        try:
            # Gửi yêu cầu GET tới API
            response = requests.get(url, params=params)

            # Kiểm tra nếu yêu cầu thành công (status code 200)
            if response.status_code == 200:
                # Lấy dữ liệu từ response.json()
                data = response.json()["data"]
                
                # Tạo thông điệp
                info = f'''
    
ID: {data["idtk"]}
Họ Tên: {data["name"]}
Ngày Tạo: {data["datecreate"]}
Có: {data["follow"]} người theo dõi
Tình Trạng: {data["relationship"]}
Sinh Nhật: {data["birthday"]}
Giới Tính: {data["gender"]}
Username: {data["user"]}
Url: {data["link"]}
Quốc Gia: {data["locale"]}
Nơi Sống: {data["location"]}
Website: {data["website"]}
                '''

                # Gửi tin nhắn cho người dùng
                bot.send_message(-1002103359217, info)
            else:
                print("Yêu cầu không thành công, mã lỗi:", response.status_code)
        except Exception as e:
            print("Đã xảy ra lỗi:", e)
    else:
        print("Không thể trích xuất ID từ link Facebook !")

if __name__ == "__main__":
    main()