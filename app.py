import os
from dotenv import load_dotenv 
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest
from datetime import datetime, timedelta
import db
from openai import OpenAI
import re
import asyncio
import json
from aiohttp import web

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PORT = int(os.getenv("PORT", 8080))  # Render cần port

# Cấu hình OpenAI với custom base URL
if OPENAI_API_KEY:
    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url="https://api.xingchiapi.com/v1"
    )
    # Danh sách models để fallback
    MODELS = ["gpt-5.4", "gpt-6.1-terra", "gpt-6-sol"]
else:
    client = None
    MODELS = []

def normalize_time(time_input: str) -> str:
    """Chuẩn hóa giờ về định dạng HH:MM
    Chấp nhận: 8, 08, 8:00, 08:00, 8:0, etc.
    """
    time_input = time_input.strip()
    
    # Nếu chỉ có số (VD: 8, 08, 14)
    if ':' not in time_input:
        hour = int(time_input)
        return f"{hour:02d}:00"
    
    # Nếu có dấu : (VD: 8:00, 8:0, 08:30)
    parts = time_input.split(':')
    if len(parts) == 2:
        hour = int(parts[0])
        minute = int(parts[1])
        return f"{hour:02d}:{minute:02d}"
    
    raise ValueError(f"Định dạng giờ không hợp lệ: {time_input}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Xin chào! Tôi là AI Reminder Bot.\n"
        "Tôi sẵn sàng giúp bạn quản lý lịch nhắc nhở."
    )
async def post_init(application):
    # 1. Định nghĩa danh sách các lệnh sẽ hiện lên khi gõ /
    commands = [
        BotCommand("start", "Khởi động bot và xem giới thiệu"),
        BotCommand("once", "Thêm lịch hẹn 1 lần: /once <ngày> <giờ:phút> <nội dung>"),
        BotCommand("schedule", "Thêm lịch hẹn hàng tuần: /schedule <thứ> <giờ:phút> <nội dung>"),
        BotCommand("schedules", "Xem tất cả lịch hẹn tuần"),
        BotCommand("editschedule", "Sửa lịch hẹn tuần: /editschedule <id>"),
        BotCommand("delschedule", "Xóa lịch tuần: /delschedule <thứ> <giờ:phút>"),
        BotCommand("list", "Xem danh sách lịch hẹn 1 lần"),
        BotCommand("cancel", "Hủy lịch 1 lần: /cancel <ngày> <giờ:phút>"),
        BotCommand("setreminder", "Thiết lập thời gian nhắc trước (phút)"),
        BotCommand("help", "Xem hướng dẫn chi tiết cách dùng"),
    ]
    # 2. Gửi danh sách này lên server Telegram
    try:
        await application.bot.set_my_commands(commands)
    except Exception as e:
        print(f"-> Lỗi khi cài đặt menu lệnh trên Telegram: {e}", flush=True)
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /help: Hướng dẫn chi tiết"""
    user_id = update.effective_user.id
    reminder_min = db.get_reminder_minutes(user_id)
    
    help_text = (
        "🤖 **HƯỚNG DẪN SỬ DỤNG REMINDER BOT**\n\n"
        "**1. Lịch hẹn 1 lần:**\n"
        "• `/once <ngày> <giờ> <nội dung>`\n"
        "  VD: `/once 20/11 08:00 Họp khách hàng`\n"
        "  VD: `/once hom_nay 14:30 Gọi điện`\n"
        "  VD: `/once mai 09:00 Nộp báo cáo`\n\n"
        "**2. Lịch hẹn hàng tuần:**\n"
        "• `/schedule <thứ> <giờ:phút> <nội dung>`\n"
        "  VD: `/schedule 2 08:00 Họp sáng`\n"
        "• `/schedules` - Xem lịch hẹn tuần\n"
        "• `/editschedule <id>` - Sửa lịch tuần\n"
        "• `/delschedule <id>` - Xóa lịch tuần\n\n"
        "**3. Quản lý:**\n"
        "• `/list` - Xem lịch hẹn 1 lần đang chờ\n"
        "• `/cancel <ngày> <giờ>` - Hủy lịch 1 lần\n"
        "  VD: `/cancel 25/12 08:00`\n\n"
        "**4. Thiết lập:**\n"
        f"• `/setreminder <phút>` - Nhắc trước bao lâu\n"
        f"  _(Hiện tại: {reminder_min} phút)_\n\n"
        "**Thứ:** 2-7, cn | **Ngày:** dd/mm, hom_nay, mai"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def setreminder_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /setreminder: Thiết lập thời gian nhắc trước"""
    if len(context.args) != 1:
        user_id = update.effective_user.id
        current_min = db.get_reminder_minutes(user_id)
        await update.message.reply_text(
            f"⚙️ **CÀI ĐẶT THỜI GIAN NHẮC TRƯỚC**\n\n"
            f"Hiện tại: **{current_min} phút** trước lịch hẹn\n\n"
            f"**Cách dùng:**\n"
            f"`/setreminder <số_phút>`\n\n"
            f"**Ví dụ:**\n"
            f"• `/setreminder 10` - Nhắc trước 10 phút\n"
            f"• `/setreminder 30` - Nhắc trước 30 phút\n"
            f"• `/setreminder 60` - Nhắc trước 1 giờ",
            parse_mode="Markdown"
        )
        return
    
    try:
        minutes = int(context.args[0])
        
        if minutes < 0:
            await update.message.reply_text("⚠️ Số phút phải lớn hơn hoặc bằng 0!")
            return
        
        if minutes > 1440:  # 24 giờ
            await update.message.reply_text("⚠️ Số phút không được vượt quá 1440 (24 giờ)!")
            return
        
        user_id = update.effective_user.id
        db.set_reminder_minutes(user_id, minutes)
        
        if minutes == 0:
            await update.message.reply_text(
                "✅ Đã cập nhật!\n"
                "⏰ Nhắc **đúng giờ** lịch hẹn (không nhắc trước)"
            )
        else:
            await update.message.reply_text(
                f"✅ Đã cập nhật!\n"
                f"⏰ Sẽ nhắc **{minutes} phút** trước mỗi lịch hẹn"
            )
        
    except ValueError:
        await update.message.reply_text("⚠️ Số phút phải là số nguyên!")
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {str(e)}")

async def once_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /once: Thêm lịch hẹn 1 lần"""
    if len(context.args) < 3:
        help_text = (
            "📅 **THÊM LỊCH HẸN 1 LẦN**\n\n"
            "**Cách dùng:**\n"
            "`/once <ngày> <giờ:phút> <nội dung>`\n\n"
            "**Định dạng ngày:**\n"
            "• `dd/mm` - Ngày cụ thể (VD: 25/12, 01/01)\n"
            "• `hom_nay` hoặc `hn` - Hôm nay\n"
            "• `mai` - Ngày mai\n\n"
            "**Ví dụ:**\n"
            "• `/once 25/12 08:00 Họp cuối năm`\n"
            "• `/once hom_nay 14:30 Gọi điện khách`\n"
            "• `/once mai 09:00 Nộp báo cáo`\n"
            "• `/once hn 16:00 Đón con`"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")
        return
    
    try:
        # Parse ngày
        date_str = context.args[0].lower()
        now = datetime.now()
        
        if date_str in ['hom_nay', 'hn', 'homnay']:
            target_date = now.date()
        elif date_str == 'mai':
            target_date = (now + timedelta(days=1)).date()
        elif '/' in date_str:
            parts = date_str.split('/')
            if len(parts) != 2:
                await update.message.reply_text("⚠️ Ngày phải theo định dạng dd/mm (VD: 25/12)")
                return
            day, month = map(int, parts)
            year = now.year
            # Nếu ngày đã qua trong năm nay, lấy năm sau
            try:
                target_date = datetime(year, month, day).date()
                if target_date < now.date():
                    target_date = datetime(year + 1, month, day).date()
            except ValueError:
                await update.message.reply_text("⚠️ Ngày không hợp lệ!")
                return
        else:
            await update.message.reply_text(
                "⚠️ Định dạng ngày không đúng!\n"
                "Dùng: dd/mm, hom_nay, hoặc mai"
            )
            return
        
        # Parse giờ
        time_str = context.args[1]
        try:
            time_str = normalize_time(time_str)
        except ValueError:
            await update.message.reply_text(
                "⚠️ Giờ không hợp lệ!\n"
                "Dùng: 8, 08, 8:00, 08:00, 14:30, etc."
            )
            return
        
        hour, minute = map(int, time_str.split(':'))
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            await update.message.reply_text("⚠️ Giờ không hợp lệ! (HH: 00-23, MM: 00-59)")
            return
        
        # Tạo datetime đầy đủ
        target_datetime = datetime.combine(target_date, datetime.strptime(time_str, '%H:%M').time())
        
        # Lấy thời gian nhắc trước của user
        reminder_minutes = db.get_reminder_minutes(update.effective_user.id)
        remind_datetime = target_datetime - timedelta(minutes=reminder_minutes)
        
        # Kiểm tra xem thời gian nhắc đã qua chưa
        if remind_datetime <= now:
            await update.message.reply_text(
                "⚠️ Thời gian đã qua rồi!\n"
                "Vui lòng chọn thời gian trong tương lai."
            )
            return
        
        # Parse nội dung
        content = " ".join(context.args[2:])
        
        # Lưu vào database
        reminder_id = db.add_reminder(
            user_id=update.effective_user.id,
            chat_id=update.effective_chat.id,
            message=content,
            remind_at=remind_datetime.isoformat()
        )
        
        # Tạo job để gửi nhắc nhở
        seconds_until = (remind_datetime - now).total_seconds()
        context.job_queue.run_once(
            send_reminder,
            when=seconds_until,
            data={
                'reminder_id': reminder_id,
                'chat_id': update.effective_chat.id,
                'message': f"{content} (lúc {time_str})"
            },
            name=f"reminder_{reminder_id}"
        )
        
        if reminder_minutes == 0:
            reminder_text = "đúng lúc"
        else:
            reminder_text = f"trước {reminder_minutes} phút"
        
        await update.message.reply_text(
            f"✅ Đã đặt lịch hẹn #{reminder_id}\n"
            f"📅 Ngày: {target_date.strftime('%d/%m/%Y')} lúc {time_str}\n"
            f"📝 Nội dung: {content}\n\n"
            f"🔔 Bot sẽ nhắc {reminder_text} ({remind_datetime.strftime('%d/%m/%Y %H:%M')})"
        )
        
    except ValueError as e:
        await update.message.reply_text(f"⚠️ Lỗi định dạng: {str(e)}")
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {str(e)}")

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /list: Xem danh sách lịch nhắc"""
    user_id = update.effective_user.id
    reminders = db.get_user_reminders(user_id)
    
    if not reminders:
        await update.message.reply_text("📭 Bạn chưa có lịch nhắc nào!")
        return
    
    text = "📋 **DANH SÁCH LỊCH NHẮC CỦA BẠN:**\n\n"
    for r in reminders:
        remind_time = datetime.fromisoformat(r['remind_at'])
        text += (
            f"🔔 **#{r['id']}** - {r['message']}\n"
            f"⏰ {remind_time.strftime('%d/%m/%Y %H:%M:%S')}\n\n"
        )
    
    text += "\n💡 Dùng `/cancel <id>` để huỷ lịch hẹn"
    await update.message.reply_text(text, parse_mode="Markdown")

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /cancel: Hủy lịch hẹn 1 lần theo ngày và giờ"""
    if len(context.args) != 2:
        await update.message.reply_text(
            "⚠️ **HỦY LỊCH HẸN 1 LẦN**\n\n"
            "**Cách dùng:**\n"
            "`/cancel <ngày> <giờ:phút>`\n\n"
            "**Ví dụ:**\n"
            "• `/cancel 25/12 08:00` - Hủy lịch ngày 25/12 lúc 8h\n"
            "• `/cancel 01/01 14:30` - Hủy lịch ngày 1/1 lúc 2h30 chiều\n\n"
            "💡 Xem danh sách với `/list`",
            parse_mode="Markdown"
        )
        return
    
    try:
        date_str = context.args[0]  # dd/mm
        time_str = context.args[1]  # HH:MM
        user_id = update.effective_user.id
        
        # Validate định dạng
        if '/' not in date_str or len(date_str.split('/')) != 2:
            await update.message.reply_text("⚠️ Ngày phải theo định dạng dd/mm (VD: 25/12)")
            return
        
        try:
            time_str = normalize_time(time_str)
        except ValueError:
            await update.message.reply_text(
                "⚠️ Giờ không hợp lệ!\n"
                "Dùng: 8, 08, 8:00, 08:00, 14:30, etc."
            )
            return
        
        # Hủy trong database
        cancelled = db.cancel_reminder_by_time(user_id, date_str, time_str)
        
        if cancelled:
            # Hủy job nếu có
            for item in cancelled:
                current_jobs = context.job_queue.get_jobs_by_name(f"reminder_{item['id']}")
                for job in current_jobs:
                    job.schedule_removal()
            
            if len(cancelled) == 1:
                await update.message.reply_text(
                    f"✅ Đã hủy lịch hẹn:\n"
                    f"📅 {date_str} lúc {time_str}\n"
                    f"📝 {cancelled[0]['message']}"
                )
            else:
                text = f"✅ Đã hủy {len(cancelled)} lịch hẹn vào {date_str} lúc {time_str}:\n\n"
                for item in cancelled:
                    text += f"• {item['message']}\n"
                await update.message.reply_text(text)
        else:
            await update.message.reply_text(
                f"❌ Không tìm thấy lịch hẹn nào vào {date_str} lúc {time_str}!"
            )
    
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {str(e)}")


async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    """Callback để gửi nhắc nhở"""
    job_data = context.job.data
    reminder_id = job_data['reminder_id']
    chat_id = job_data['chat_id']
    message = job_data['message']
    
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🔔 **NHẮC NHỞ!**\n\n📝 {message}",
            parse_mode="Markdown"
        )
        
        # Đánh dấu đã hoàn thành
        db.mark_completed(reminder_id)
        
    except Exception as e:
        print(f"Lỗi khi gửi nhắc nhở #{reminder_id}: {e}")

def parse_time_with_ai(text: str) -> dict:
    """Dùng AI để phân tích thời gian từ câu nói tự nhiên"""
    if not client:
        return None
    
    prompt = f"""Bạn là trợ lý phân tích thời gian. Hãy phân tích câu sau và trả về thông tin thời gian:

Câu: "{text}"
Thời gian hiện tại: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Hãy trả về ĐÚNG định dạng JSON sau (không thêm bất kỳ text nào khác):
{{
    "has_reminder": true/false,
    "seconds_from_now": <số giây từ bây giờ>,
    "message": "<nội dung cần nhắc>"
}}

Ví dụ:
- "15 phút nữa nhắc tôi lấy đồ" -> {{"has_reminder": true, "seconds_from_now": 900, "message": "lấy đồ"}}
- "8h tối nay nhắc tôi uống thuốc" -> {{"has_reminder": true, "seconds_from_now": <tính từ bây giờ đến 8h tối>, "message": "uống thuốc"}}
- "Chào bạn" -> {{"has_reminder": false}}
"""
    
    # Thử từng model theo thứ tự
    for model_name in MODELS:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "Bạn là trợ lý phân tích thời gian chuyên nghiệp. Luôn trả về JSON hợp lệ."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Trích xuất JSON từ response (có thể có markdown code block)
            json_match = re.search(r'\{[^{}]*\}', result_text)
            if json_match:
                result = json.loads(json_match.group())
                print(f"✓ AI parse thành công với model: {model_name}", flush=True)
                return result
            
        except Exception as e:
            print(f"⚠ Model {model_name} lỗi: {e}", flush=True)
            continue  # Thử model tiếp theo
    
    print("❌ Tất cả models đều lỗi", flush=True)
    return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý tin nhắn tự nhiên bằng AI"""
    text = update.message.text
    
    if not client:
        await update.message.reply_text(
            "⚠️ Chức năng AI chưa được cấu hình!\n"
            "Vui lòng thêm OPENAI_API_KEY vào .env"
        )
        return
    
    # Gửi typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Phân tích bằng AI
    result = parse_time_with_ai(text)
    
    if not result or not result.get('has_reminder'):
        await update.message.reply_text(
            "🤔 Tôi không thấy yêu cầu nhắc nhở trong tin nhắn của bạn.\n"
            "Hãy thử nói rõ hơn, ví dụ: '30 phút nữa nhắc tôi uống nước'"
        )
        return
    
    seconds = result.get('seconds_from_now', 0)
    message = result.get('message', text)
    
    if seconds <= 0:
        await update.message.reply_text(
            "⚠️ Thời gian không hợp lệ hoặc đã qua rồi!"
        )
        return
    
    # Tính thời gian nhắc nhở
    remind_time = datetime.now() + timedelta(seconds=seconds)
    
    # Lưu vào database
    reminder_id = db.add_reminder(
        user_id=update.effective_user.id,
        chat_id=update.effective_chat.id,
        message=message,
        remind_at=remind_time.isoformat()
    )
    
    # Tạo job để gửi nhắc nhở
    context.job_queue.run_once(
        send_reminder,
        when=seconds,
        data={'reminder_id': reminder_id, 'chat_id': update.effective_chat.id, 'message': message},
        name=f"reminder_{reminder_id}"
    )
    
    await update.message.reply_text(
        f"✅ Đã đặt lịch nhắc #{reminder_id}\n"
        f"⏰ Thời gian: {remind_time.strftime('%d/%m/%Y %H:%M:%S')}\n"
        f"📝 Nội dung: {message}"
    )

# ===== RECURRING SCHEDULES =====

DAY_NAMES = {
    0: "Thứ 2", 1: "Thứ 3", 2: "Thứ 4", 3: "Thứ 5",
    4: "Thứ 6", 5: "Thứ 7", 6: "Chủ nhật"
}

async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /schedule: Thêm lịch hẹn hàng tuần"""
    if len(context.args) < 3:
        help_text = (
            "📅 **THÊM LỊCH HẸN HÀNG TUẦN**\n\n"
            "**Cách dùng:**\n"
            "`/schedule <thứ> <giờ:phút> <nội dung>`\n\n"
            "**Thứ trong tuần:**\n"
            "• `2` = Thứ 2\n"
            "• `3` = Thứ 3\n"
            "• `4` = Thứ 4\n"
            "• `5` = Thứ 5\n"
            "• `6` = Thứ 6\n"
            "• `7` = Thứ 7\n"
            "• `cn` = Chủ nhật\n\n"
            "**Ví dụ:**\n"
            "• `/schedule 2 08:00 Họp team sáng`\n"
            "• `/schedule 3 14:30 Gặp khách hàng`\n"
            "• `/schedule 5 09:15 Kiểm tra email quan trọng`\n"
            "• `/schedule cn 10:00 Đi chợ`"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")
        return
    
    try:
        # Parse thứ
        day_str = context.args[0].lower()
        if day_str == 'cn':
            day_of_week = 6  # Chủ nhật
        else:
            day_num = int(day_str)
            if day_num < 2 or day_num > 7:
                await update.message.reply_text("⚠️ Thứ phải từ 2 đến 7, hoặc 'cn' cho Chủ nhật!")
                return
            day_of_week = day_num - 2  # Convert: Thứ 2=0, Thứ 3=1, ...
        
        # Parse giờ
        time_str = context.args[1]
        try:
            time_str = normalize_time(time_str)
        except ValueError:
            await update.message.reply_text(
                "⚠️ Giờ không hợp lệ!\n"
                "Dùng: 8, 08, 8:00, 08:00, 14:30, etc."
            )
            return
        
        hour, minute = map(int, time_str.split(':'))
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            await update.message.reply_text("⚠️ Giờ không hợp lệ! (HH: 00-23, MM: 00-59)")
            return
        
        # Parse nội dung
        content = " ".join(context.args[2:])
        
        # Lưu vào database
        schedule_id = db.add_schedule(
            user_id=update.effective_user.id,
            chat_id=update.effective_chat.id,
            day_of_week=day_of_week,
            time=time_str,
            message=content
        )
        
        # Lấy thời gian nhắc của user
        reminder_min = db.get_reminder_minutes(update.effective_user.id)
        
        if reminder_min == 0:
            reminder_text = "đúng giờ"
        else:
            reminder_text = f"trước {reminder_min} phút"
        
        await update.message.reply_text(
            f"✅ Đã thêm lịch hẹn #{schedule_id}\n"
            f"📅 {DAY_NAMES[day_of_week]} lúc {time_str}\n"
            f"📝 Nội dung: {content}\n\n"
            f"🔔 Bot sẽ nhắc {reminder_text}!"
        )
        
    except ValueError:
        await update.message.reply_text("⚠️ Định dạng không đúng! Xem hướng dẫn với `/schedule`")
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {str(e)}")

async def schedules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /schedules: Xem tất cả lịch hẹn"""
    user_id = update.effective_user.id
    schedules = db.get_user_schedules(user_id)
    
    if not schedules:
        await update.message.reply_text(
            "📭 Bạn chưa có lịch hẹn nào!\n\n"
            "💡 Dùng `/schedule` để thêm lịch hẹn hàng tuần"
        )
        return
    
    text = "📅 **LỊCH HẸN HÀNG TUẦN CỦA BẠN:**\n\n"
    
    # Nhóm theo thứ
    by_day = {}
    for s in schedules:
        day = s['day_of_week']
        if day not in by_day:
            by_day[day] = []
        by_day[day].append(s)
    
    for day in sorted(by_day.keys()):
        text += f"**{DAY_NAMES[day]}:**\n"
        for s in sorted(by_day[day], key=lambda x: x['time']):
            text += f"  🕐 {s['time']} - {s['message']} (ID: #{s['id']})\n"
        text += "\n"
    
    text += "\n💡 Dùng `/delschedule <id>` để xóa lịch hẹn"
    await update.message.reply_text(text, parse_mode="Markdown")


async def delschedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /delschedule: Xóa lịch hẹn tuần theo thứ và giờ"""
    if len(context.args) != 2:
        await update.message.reply_text(
            "⚠️ **XÓA LỊCH HẸN TUẦN**\n\n"
            "**Cách dùng:**\n"
            "`/delschedule <thứ> <giờ:phút>`\n\n"
            "**Ví dụ:**\n"
            "• `/delschedule 2 08:00` - Xóa lịch Thứ 2 lúc 8h\n"
            "• `/delschedule 5 14:30` - Xóa lịch Thứ 6 lúc 2h30 chiều\n"
            "• `/delschedule cn 10:00` - Xóa lịch Chủ nhật lúc 10h\n\n"
            "💡 Xem danh sách với `/schedules`",
            parse_mode="Markdown"
        )
        return
    
    try:
        # Parse thứ
        day_str = context.args[0].lower()
        if day_str == 'cn':
            day_of_week = 6
        else:
            day_num = int(day_str)
            if day_num < 2 or day_num > 7:
                await update.message.reply_text("⚠️ Thứ phải từ 2 đến 7, hoặc 'cn' cho Chủ nhật!")
                return
            day_of_week = day_num - 2
        
        time_str = context.args[1]
        try:
            time_str = normalize_time(time_str)
        except ValueError:
            await update.message.reply_text(
                "⚠️ Giờ không hợp lệ!\n"
                "Dùng: 8, 08, 8:00, 08:00, 14:30, etc."
            )
            return
        
        user_id = update.effective_user.id
        deleted = db.delete_schedule_by_time(user_id, day_of_week, time_str)
        
        if deleted:
            if len(deleted) == 1:
                await update.message.reply_text(
                    f"✅ Đã xóa lịch hẹn:\n"
                    f"📅 {DAY_NAMES[day_of_week]} lúc {time_str}\n"
                    f"📝 {deleted[0]['message']}"
                )
            else:
                text = f"✅ Đã xóa {len(deleted)} lịch hẹn vào {DAY_NAMES[day_of_week]} lúc {time_str}:\n\n"
                for item in deleted:
                    text += f"• {item['message']}\n"
                await update.message.reply_text(text)
        else:
            await update.message.reply_text(
                f"❌ Không tìm thấy lịch hẹn nào vào {DAY_NAMES[day_of_week]} lúc {time_str}!"
            )
    
    except ValueError as e:
        await update.message.reply_text(f"⚠️ Lỗi định dạng: {str(e)}")
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {str(e)}")


async def editschedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /editschedule: Sửa lịch hẹn tuần"""
    if len(context.args) == 0:
        await update.message.reply_text(
            "✏️ **SỬA LỊCH HẸN TUẦN**\n\n"
            "**Cách dùng:**\n"
            "`/editschedule <id> [thứ] [giờ:phút] [nội dung]`\n\n"
            "**Lưu ý:** Chỉ cần nhập phần muốn sửa\n\n"
            "**Ví dụ:**\n"
            "• `/editschedule 5 3` - Đổi sang Thứ 3\n"
            "• `/editschedule 5 _ 09:00` - Đổi giờ (giữ nguyên thứ)\n"
            "• `/editschedule 5 _ _ Họp mới` - Đổi nội dung\n"
            "• `/editschedule 5 4 10:30 Họp team` - Đổi hết\n\n"
            "💡 Dùng `_` để giữ nguyên giá trị cũ\n"
            "💡 Xem ID với `/schedules`",
            parse_mode="Markdown"
        )
        return
    
    try:
        schedule_id = int(context.args[0])
        user_id = update.effective_user.id
        
        # Lấy thông tin lịch hẹn hiện tại
        current = db.get_schedule_by_id(schedule_id, user_id)
        if not current:
            await update.message.reply_text(
                f"❌ Không tìm thấy lịch hẹn #{schedule_id} hoặc bạn không có quyền sửa!"
            )
            return
        
        # Parse các tham số
        new_day = None
        new_time = None
        new_message = None
        
        if len(context.args) > 1 and context.args[1] != '_':
            day_str = context.args[1].lower()
            if day_str == 'cn':
                new_day = 6
            else:
                day_num = int(day_str)
                if day_num < 2 or day_num > 7:
                    await update.message.reply_text("⚠️ Thứ phải từ 2 đến 7, hoặc 'cn'!")
                    return
                new_day = day_num - 2
        
        if len(context.args) > 2 and context.args[2] != '_':
            time_str = context.args[2]
            try:
                time_str = normalize_time(time_str)
            except ValueError:
                await update.message.reply_text(
                    "⚠️ Giờ không hợp lệ!\n"
                    "Dùng: 8, 08, 8:00, 08:00, 14:30, etc."
                )
                return
            hour, minute = map(int, time_str.split(':'))
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                await update.message.reply_text("⚠️ Giờ không hợp lệ!")
                return
            new_time = time_str
        
        if len(context.args) > 3:
            # Nếu có nội dung mới
            if context.args[3] != '_':
                new_message = " ".join(context.args[3:])
        
        # Cập nhật
        success = db.update_schedule(schedule_id, user_id, new_day, new_time, new_message)
        
        if success:
            # Lấy thông tin sau khi cập nhật
            updated = db.get_schedule_by_id(schedule_id, user_id)
            await update.message.reply_text(
                f"✅ Đã cập nhật lịch hẹn #{schedule_id}\n"
                f"📅 {DAY_NAMES[updated['day_of_week']]} lúc {updated['time']}\n"
                f"📝 Nội dung: {updated['message']}"
            )
        else:
            await update.message.reply_text("❌ Không thể cập nhật lịch hẹn!")
        
    except ValueError as e:
        await update.message.reply_text(f"⚠️ Lỗi định dạng: {str(e)}")
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {str(e)}")

async def check_schedules(context: ContextTypes.DEFAULT_TYPE):
    """Job định kỳ kiểm tra lịch hẹn và tạo nhắc nhở"""
    schedules = db.get_all_active_schedules()
    now = datetime.now()
    current_day = now.weekday()  # 0=Monday, 6=Sunday
    
    for schedule in schedules:
        # Lấy thời gian nhắc trước của user
        reminder_minutes = db.get_reminder_minutes(schedule['user_id'])
        
        # Tính thời gian nhắc nhở
        schedule_time = datetime.strptime(schedule['time'], '%H:%M').time()
        schedule_datetime = datetime.combine(now.date(), schedule_time)
        remind_datetime = schedule_datetime - timedelta(minutes=reminder_minutes)
        
        # Kiểm tra xem đã đến giờ nhắc chưa
        if (current_day == schedule['day_of_week'] and 
            now.time() >= remind_datetime.time() and 
            now.time() < schedule_time):
            
            # Kiểm tra xem đã tạo reminder cho hôm nay chưa
            existing_reminders = db.get_pending_reminders()
            already_created = False
            for r in existing_reminders:
                if (r['user_id'] == schedule['user_id'] and 
                    r['message'].startswith(f"Lịch hẹn: {schedule['message']}") and
                    datetime.fromisoformat(r['remind_at']).date() == now.date()):
                    already_created = True
                    break
            
            if not already_created:
                # Tạo reminder
                seconds_until = (remind_datetime - now).total_seconds()
                if seconds_until > 0:
                    message = f"Lịch hẹn: {schedule['message']} (lúc {schedule['time']})"
                    reminder_id = db.add_reminder(
                        user_id=schedule['user_id'],
                        chat_id=schedule['chat_id'],
                        message=message,
                        remind_at=remind_datetime.isoformat()
                    )
                    
                    # Tạo job
                    context.job_queue.run_once(
                        send_reminder,
                        when=seconds_until,
                        data={
                            'reminder_id': reminder_id,
                            'chat_id': schedule['chat_id'],
                            'message': message
                        },
                        name=f"reminder_{reminder_id}"
                    )

async def check_pending_reminders(context: ContextTypes.DEFAULT_TYPE):
    """Kiểm tra và gửi các nhắc nhở đang chờ khi bot khởi động lại"""
    reminders = db.get_pending_reminders()
    now = datetime.now()
    
    for reminder in reminders:
        remind_time = datetime.fromisoformat(reminder['remind_at'])
        
        # Nếu đã quá giờ, gửi luôn
        if remind_time <= now:
            try:
                await context.bot.send_message(
                    chat_id=reminder['chat_id'],
                    text=f"🔔 **NHẮC NHỞ (Bị trễ)!**\n\n📝 {reminder['message']}",
                    parse_mode="Markdown"
                )
                db.mark_completed(reminder['id'])
            except Exception as e:
                print(f"Lỗi khi gửi nhắc nhở #{reminder['id']}: {e}")
        else:
            # Tạo job cho tương lai
            seconds = (remind_time - now).total_seconds()
            context.job_queue.run_once(
                send_reminder,
                when=seconds,
                data={
                    'reminder_id': reminder['id'],
                    'chat_id': reminder['chat_id'],
                    'message': reminder['message']
                },
                name=f"reminder_{reminder['id']}"
            )

def main():
    if not TOKEN:
        print("Lỗi: Chưa cấu hình TELEGRAM_BOT_TOKEN trong file .env")
        return

    # Khởi tạo database
    db.init_db()
    db.init_schedules_table()
    db.init_user_settings_table()
    print("✓ Database đã được khởi tạo", flush=True)

    # Tăng timeout do mạng quốc tế tới Telegram có thể mất 15-30s
    request_handler = HTTPXRequest(
        connect_timeout=60.0,
        read_timeout=60.0,
        write_timeout=60.0,
        pool_timeout=60.0,
    )

    app = ApplicationBuilder().token(TOKEN).post_init(post_init).request(request_handler).build()
    
    # Thêm các handler
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("setreminder", setreminder_command))
    app.add_handler(CommandHandler("once", once_command))
    app.add_handler(CommandHandler("schedule", schedule_command))
    app.add_handler(CommandHandler("schedules", schedules_command))
    app.add_handler(CommandHandler("editschedule", editschedule_command))
    app.add_handler(CommandHandler("delschedule", delschedule_command))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    
    # Handler cho tin nhắn thông thường (AI)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Kiểm tra các reminder đang chờ khi khởi động
    app.job_queue.run_once(check_pending_reminders, when=1)
    
    # Kiểm tra lịch hẹn mỗi 5 phút
    app.job_queue.run_repeating(check_schedules, interval=300, first=10)
    
    print("✓ Bot đang chạy... (Nhấn Ctrl + C để dừng)", flush=True)
    if client:
        print(f"✓ AI đã được kích hoạt với models: {', '.join(MODELS)}", flush=True)
    else:
        print("⚠ AI chưa được cấu hình", flush=True)
    print("✓ Lịch hẹn tự động đã được kích hoạt", flush=True)
    
    # Chạy bot với webhook cho Render
    if os.getenv("RENDER"):
        # Trên Render: dùng webhook
        print(f"✓ Chạy trên Render với webhook, port {PORT}", flush=True)
        
        # Health check endpoint cho Render
        async def health(request):
            return web.Response(text="Bot is running!")
        
        webapp = web.Application()
        webapp.router.add_get("/", health)
        webapp.router.add_get("/health", health)
        
        # Start web server cho health check
        runner = web.AppRunner(webapp)
        
        async def start_bot():
            await runner.setup()
            site = web.TCPSite(runner, '0.0.0.0', PORT)
            await site.start()
            print(f"✓ Health check server running on port {PORT}", flush=True)
            
            # Start bot polling
            await app.initialize()
            await app.start()
            await app.updater.start_polling()
            
            # Keep running
            while True:
                await asyncio.sleep(1)
        
        asyncio.run(start_bot())
    else:
        # Local: chạy bình thường
        app.run_polling(bootstrap_retries=5)

if __name__ == "__main__":
    main()
