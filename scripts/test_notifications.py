#!/usr/bin/env python3
"""
اختبار نظام الإشعارات لـ AACS V0
"""
import sys
import os
from pathlib import Path

# إضافة المجلد الجذر للمسار
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import Config
from core.notification_manager import NotificationManager


def main():
    """اختبار نظام الإشعارات"""
    print("🔔 اختبار نظام الإشعارات لـ AACS V0")
    print("=" * 50)
    
    try:
        # تهيئة النظام
        config = Config()
        notification_manager = NotificationManager(config)
        
        print(f"📱 القنوات المفعلة: {[channel.value for channel in notification_manager.enabled_channels]}")
        
        if not notification_manager.enabled_channels:
            print("⚠️ لا توجد قنوات إشعارات مفعلة!")
            print("💡 لتفعيل إشعارات Telegram:")
            print("   1. احصل على bot token من @BotFather")
            print("   2. احصل على chat ID من @userinfobot")
            print("   3. اضبط متغيرات البيئة:")
            print("      export TELEGRAM_BOT_TOKEN='your_bot_token'")
            print("      export TELEGRAM_CHAT_ID='your_chat_id'")
            return
        
        # اختبار الإشعارات المختلفة
        print("\n🧪 اختبار أنواع الإشعارات المختلفة...")
        
        # 1. اختبار إشعار تحذير
        print("1️⃣ اختبار إشعار التحذير...")
        success1 = notification_manager.test_notification_system()
        print(f"   النتيجة: {'✅ نجح' if success1 else '❌ فشل'}")
        
        # 2. اختبار إشعار خطأ
        print("2️⃣ اختبار إشعار الخطأ...")
        success2 = notification_manager.send_error_notification(
            "🧪 اختبار إشعار خطأ",
            "هذا اختبار لإشعار الأخطاء في النظام.",
            {"test_type": "error_test", "component": "notification_system"}
        )
        print(f"   النتيجة: {'✅ نجح' if success2 else '❌ فشل'}")
        
        # 3. اختبار إشعار حرج
        print("3️⃣ اختبار إشعار حرج...")
        success3 = notification_manager.send_critical_notification(
            "🧪 اختبار إشعار حرج",
            "هذا اختبار للإشعارات الحرجة في النظام.",
            {"test_type": "critical_test", "severity": "high"}
        )
        print(f"   النتيجة: {'✅ نجح' if success3 else '❌ فشل'}")
        
        # 4. اختبار إشعار فشل الاجتماع
        print("4️⃣ اختبار إشعار فشل الاجتماع...")
        success4 = notification_manager.notify_meeting_failure(
            "test_session_001",
            "خطأ في محاكاة الاجتماع - اختبار",
            {"error_type": "simulation_error", "test": True}
        )
        print(f"   النتيجة: {'✅ نجح' if success4 else '❌ فشل'}")
        
        # 5. اختبار إشعار فشل التصويت
        print("5️⃣ اختبار إشعار فشل التصويت...")
        success5 = notification_manager.notify_voting_failure(
            "test_session_001",
            "عدم وجود النصاب القانوني المطلوب - اختبار",
            {"voting_agents": 6, "required_quorum": 7, "test": True}
        )
        print(f"   النتيجة: {'✅ نجح' if success5 else '❌ فشل'}")
        
        # النتيجة النهائية
        all_success = all([success1, success2, success3, success4, success5])
        
        print("\n" + "=" * 50)
        print(f"🎯 النتيجة النهائية: {'✅ جميع الاختبارات نجحت' if all_success else '❌ بعض الاختبارات فشلت'}")
        
        if all_success:
            print("🎉 نظام الإشعارات يعمل بشكل صحيح!")
        else:
            print("⚠️ يرجى مراجعة إعدادات الإشعارات")
        
    except Exception as e:
        print(f"❌ خطأ في اختبار نظام الإشعارات: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()