# Telegram AI Reminder Bot

Bot Telegram thông minh giúp bạn đặt lịch nhắc nhở bằng ngôn ngữ tự nhiên, sử dụng Google Gemini AI.

## ✨ Tính năng

- 🤖 **Nhắc nhở thông minh với AI**: Chỉ cần nhắn tin tự nhiên như "30 phút nữa nhắc tôi uống nước"
- ⚡ **Lệnh nhanh**: Dùng `/remind` để đặt lịch nhanh chóng
- 📋 **Quản lý lịch hẹn**: Xem danh sách và huỷ lịch hẹn dễ dàng
- 💾 **Lưu trữ bền vững**: Dữ liệu được lưu trong SQLite database
- 🔄 **Khôi phục tự động**: Bot tự động gửi các nhắc nhở đã đặt sau khi khởi động lại

## 📋 Yêu cầu

- Python 3.8+
- Telegram Bot Token (từ [@BotFather](https://t.me/botfather))
- Google Gemini API Key (tuỳ chọn, để dùng AI)

## 🚀 Cài đặt

1. **Clone hoặc tải project về**

2. **Cài đặt dependencies:**
```bash
pip install -r requirements.txt
```

3. **Cấu hình môi trường:**
   - Sao chép file `.env.example` thành `.env`
   - Điền thông tin vào file `.env`:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
```

   **Lấy Telegram Bot Token:**
   - Nhắn tin cho [@BotFather](https://t.me/botfather)
   - Gửi lệnh `/newbot` và làm theo hướng dẫn
   - Copy token nhận được

   **Lấy Gemini API Key (tuỳ chọn):**
   - Truy cập [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Tạo API key mới
   - Copy key vào file `.env`

4. **Chạy bot:**
```bash
python app.py
```

## 📖 Hướng dẫn sử dụng

### Lệnh cơ bản:

- `/start` - Khởi động bot
- `/help` - Xem hướng dẫn chi tiết
- `/remind <giây> <nội dung>` - Đặt lịch nhanh
- `/list` - Xem danh sách lịch hẹn
- `/cancel <id>` - Huỷ lịch hẹn

### Ví dụ sử dụng:

**1. Đặt lịch bằng lệnh nhanh:**
```
/remind 3600 Họp team
```
(Nhắc sau 1 giờ = 3600 giây)

**2. Đặt lịch bằng AI (nếu đã cấu hình Gemini):**
```
15 phút nữa nhắc tôi lấy đồ phơi
```
```
8h tối nay nhắc tôi uống thuốc
```
```
Sáng mai 9h họp dự án
```

**3. Xem danh sách:**
```
/list
```

**4. Huỷ lịch hẹn:**
```
/cancel 3
```
(Huỷ lịch nhắc có ID = 3)

## 🗂️ Cấu trúc project

```
telegram-ai-reminder/
├── app.py              # File chính chạy bot
├── db.py               # Quản lý database SQLite
├── requirements.txt    # Các thư viện cần thiết
├── .env               # Cấu hình môi trường (không commit)
├── .env.example       # Mẫu file cấu hình
├── reminders.db       # Database SQLite (tự động tạo)
└── README.md          # File này
```

## ⚙️ Chi tiết kỹ thuật

### Database Schema:
```sql
CREATE TABLE reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    chat_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    remind_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL
)
```

### Trạng thái reminder:
- `pending` - Đang chờ gửi
- `completed` - Đã gửi thành công
- `cancelled` - Đã bị huỷ

## 🔧 Troubleshooting

**Lỗi: "Chưa cấu hình TELEGRAM_BOT_TOKEN"**
- Kiểm tra file `.env` có tồn tại không
- Đảm bảo đã điền đúng token vào file `.env`

**Lỗi kết nối Telegram:**
- Bot sử dụng timeout 60s để xử lý kết nối chậm
- Kiểm tra kết nối internet
- Thử chạy lại bot

**AI không hoạt động:**
- Đảm bảo đã cấu hình `GEMINI_API_KEY` trong file `.env`
- Kiểm tra API key còn hiệu lực
- Bot vẫn hoạt động bình thường với lệnh `/remind` nếu không có AI

## 📝 License

MIT License - Tự do sử dụng và chỉnh sửa

## 🤝 Đóng góp

Mọi đóng góp đều được hoan nghênh! Hãy tạo issue hoặc pull request.

## 📧 Liên hệ

Nếu có câu hỏi hoặc góp ý, vui lòng tạo issue trên GitHub.
