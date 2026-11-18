"""
Script test đơn giản để kiểm tra database
Chạy: python test_db.py
"""

import db
from datetime import datetime, timedelta

def test_database():
    print("=== KIỂM TRA DATABASE ===\n")
    
    # 1. Khởi tạo database
    print("1. Khởi tạo database...")
    db.init_db()
    print("   ✓ Database đã khởi tạo\n")
    
    # 2. Thêm reminder test
    print("2. Thêm reminder test...")
    test_time = datetime.now() + timedelta(minutes=5)
    reminder_id = db.add_reminder(
        user_id=12345,
        chat_id=12345,
        message="Test reminder",
        remind_at=test_time.isoformat()
    )
    print(f"   ✓ Đã thêm reminder #{reminder_id}\n")
    
    # 3. Lấy danh sách reminders
    print("3. Lấy danh sách reminders...")
    reminders = db.get_user_reminders(12345)
    print(f"   ✓ Tìm thấy {len(reminders)} reminder(s)")
    for r in reminders:
        print(f"     - ID: {r['id']}, Message: {r['message']}, Status: {r['status']}\n")
    
    # 4. Test cancel reminder
    print("4. Test huỷ reminder...")
    success = db.cancel_reminder(reminder_id, 12345)
    if success:
        print(f"   ✓ Đã huỷ reminder #{reminder_id}\n")
    else:
        print(f"   ✗ Không thể huỷ reminder #{reminder_id}\n")
    
    # 5. Kiểm tra lại
    print("5. Kiểm tra lại sau khi huỷ...")
    reminders = db.get_user_reminders(12345)
    print(f"   ✓ Còn lại {len(reminders)} reminder(s) đang pending\n")
    
    # 6. Thêm và đánh dấu hoàn thành
    print("6. Test đánh dấu hoàn thành...")
    test_time2 = datetime.now() + timedelta(seconds=30)
    reminder_id2 = db.add_reminder(
        user_id=12345,
        chat_id=12345,
        message="Test completed reminder",
        remind_at=test_time2.isoformat()
    )
    print(f"   ✓ Đã thêm reminder #{reminder_id2}")
    
    db.mark_completed(reminder_id2)
    print(f"   ✓ Đã đánh dấu hoàn thành #{reminder_id2}\n")
    
    # 7. Lấy tất cả pending reminders
    print("7. Lấy tất cả pending reminders...")
    all_pending = db.get_pending_reminders()
    print(f"   ✓ Tổng cộng {len(all_pending)} reminder(s) đang pending trong hệ thống\n")
    
    print("=== TẤT CẢ TESTS ĐÃ HOÀN THÀNH ===")

if __name__ == "__main__":
    try:
        test_database()
    except Exception as e:
        print(f"\n❌ LỖI: {e}")
        import traceback
        traceback.print_exc()
