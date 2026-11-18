# Changelog

Tất cả các thay đổi đáng chú ý của project sẽ được ghi lại trong file này.

## [1.0.0] - 2024-12-XX

### ✨ Tính năng mới
- ✅ Đặt lịch nhắc nhở bằng lệnh `/remind <giây> <nội dung>`
- ✅ Đặt lịch thông minh bằng ngôn ngữ tự nhiên với Google Gemini AI
- ✅ Xem danh sách lịch hẹn với lệnh `/list`
- ✅ Huỷ lịch hẹn với lệnh `/cancel <id>`
- ✅ Hướng dẫn chi tiết với lệnh `/help`
- ✅ Menu lệnh tự động hiển thị khi gõ `/`

### 🗄️ Database
- SQLite database để lưu trữ reminders
- Theo dõi trạng thái: pending, completed, cancelled
- Tự động khởi tạo database khi chạy bot

### 🤖 AI Integration
- Tích hợp Google Gemini Pro để phân tích ngôn ngữ tự nhiên
- Phân tích thời gian từ câu nói: "15 phút nữa", "8h tối nay", "sáng mai 9h"
- Hoạt động tốt cả khi không có AI (fallback to `/remind`)

### ⚡ Job Queue
- Tự động gửi nhắc nhở đúng thời gian
- Khôi phục reminders sau khi bot restart
- Gửi ngay các reminder bị trễ

### 🛠️ Developer Experience
- File `.env.example` để hướng dẫn cấu hình
- Script test database (`test_db.py`)
- File batch để chạy bot trên Windows (`run_bot.bat`)
- README.md và SETUP.md chi tiết
- .gitignore hoàn chỉnh

### 📝 Documentation
- README.md: Tổng quan và hướng dẫn đầy đủ
- SETUP.md: Hướng dẫn cài đặt từng bước
- CHANGELOG.md: Theo dõi các phiên bản
- Comments trong code rõ ràng

### 🔒 Security
- Token và API keys lưu trong file .env
- .env được ignore trong git
- Timeout 60s cho requests tới Telegram

### 🌐 Localization
- Giao diện tiếng Việt
- Định dạng ngày giờ theo VN (dd/mm/yyyy HH:MM:SS)
- Emoji cho UI thân thiện

---

## Kế hoạch tương lai

### [1.1.0] - Sắp tới
- [ ] Hỗ trợ timezone tự động
- [ ] Lặp lại reminder (daily, weekly, monthly)
- [ ] Nhóm reminders thành categories
- [ ] Export/Import reminders
- [ ] Thống kê sử dụng

### [1.2.0] - Tương lai
- [ ] Nhắc nhở theo vị trí (location-based)
- [ ] Chia sẻ reminder với người khác
- [ ] Voice message support
- [ ] Multi-language support
- [ ] Web dashboard

### [2.0.0] - Dài hạn
- [ ] Tích hợp lịch (Google Calendar, Outlook)
- [ ] Smart suggestions dựa trên lịch sử
- [ ] Mobile app companion
- [ ] Premium features
