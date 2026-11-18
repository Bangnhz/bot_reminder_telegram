# Hướng dẫn cài đặt nhanh

## 1. Cài đặt Python và Dependencies

```bash
# Kiểm tra Python đã cài (cần >= 3.8)
python --version

# Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```

## 2. Lấy Telegram Bot Token

1. Mở Telegram và tìm **@BotFather**
2. Gửi lệnh `/newbot`
3. Đặt tên cho bot (VD: `My Reminder Bot`)
4. Đặt username cho bot (phải kết thúc bằng `bot`, VD: `my_reminder_bot`)
5. Copy **token** nhận được (dạng: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

## 3. Lấy Google Gemini API Key (Tuỳ chọn)

1. Truy cập: https://makersuite.google.com/app/apikey
2. Đăng nhập bằng tài khoản Google
3. Click nút **"Create API Key"**
4. Chọn project hoặc tạo mới
5. Copy **API Key** nhận được

> **Lưu ý:** Nếu không cần tính năng AI, có thể bỏ qua bước này. Bot vẫn hoạt động với lệnh `/remind`.

## 4. Cấu hình file .env

```bash
# Copy file mẫu
cp .env.example .env

# Hoặc trên Windows
copy .env.example .env
```

Mở file `.env` và điền thông tin:

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

## 5. Chạy Bot

```bash
python app.py
```

Khi thấy dòng này nghĩa là bot đã chạy thành công:
```
✓ Database đã được khởi tạo
✓ Bot đang chạy... (Nhấn Ctrl + C để dừng)
✓ AI (Gemini) đã được kích hoạt
```

## 6. Test Bot

1. Mở Telegram và tìm bot của bạn (theo username đã đặt)
2. Gửi lệnh `/start`
3. Thử các lệnh:
   - `/remind 60 Test` - Nhắc sau 60 giây
   - `/list` - Xem danh sách
   - Hoặc nhắn tự nhiên: "5 phút nữa nhắc tôi uống nước"

## Troubleshooting

### Bot không phản hồi
- Kiểm tra token đã đúng chưa
- Đảm bảo bot đang chạy
- Kiểm tra kết nối internet

### AI không hoạt động
- Kiểm tra Gemini API key
- Xem log có lỗi gì không
- Bot vẫn dùng được với lệnh `/remind`

### Lỗi "Module not found"
```bash
pip install -r requirements.txt --upgrade
```

## Chạy Bot 24/7

### Trên VPS/Server Linux:
```bash
# Cài tmux
sudo apt install tmux

# Chạy trong tmux session
tmux new -s reminder_bot
python app.py

# Detach: Ctrl+B rồi D
# Attach lại: tmux attach -t reminder_bot
```

### Trên Windows:
- Tạo file `run_bot.bat`:
```batch
@echo off
cd /d "%~dp0"
python app.py
pause
```
- Chạy file bat này khi cần

### Dùng systemd (Linux):
Tạo file `/etc/systemd/system/reminder-bot.service`:
```ini
[Unit]
Description=Telegram Reminder Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/telegram-ai-reminder
ExecStart=/usr/bin/python3 /path/to/telegram-ai-reminder/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Kích hoạt:
```bash
sudo systemctl enable reminder-bot
sudo systemctl start reminder-bot
sudo systemctl status reminder-bot
```
