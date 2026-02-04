#!/usr/bin/env python3
"""
سكريبت تشغيل اجتماع AACS
"""
import os
import sys
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

# إضافة المسار الجذر للمشروع
sys.path.insert(0, str(Path(__file__).parent.parent))

# تحميل متغيرات البيئة من ملف .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # إذا لم تكن مكتبة python-dotenv مثبتة، تجاهل
    pass

from core.config import Config
from core.orchestrator import MeetingOrchestrator
from core.logger import setup_logger


def main():
    """تشغيل اجتماع AACS"""
    try:
        # إعداد التسجيل
        logger = setup_logger()
        logger.info("🚀 بدء تشغيل اجتماع AACS V0")
        
        # التحقق من التكوين
        config = Config.get_instance()
        logger.info(f"✅ تم التحقق من التكوين - المزود: {config.AI_PROVIDER}")
        
        # الحصول على الأجندة
        agenda = os.getenv('MEETING_AGENDA', 'اجتماع دوري مجدول')
        debug_mode = config.DEBUG_MODE
        
        logger.info(f"📋 الأجندة: {agenda}")
        logger.info(f"🔧 وضع التصحيح: {debug_mode}")
        
        # إنشاء منسق الاجتماع
        orchestrator = MeetingOrchestrator(config)
        
        # تشغيل الاجتماع
        session_id = f"meeting_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"🆔 معرف الجلسة: {session_id}")
        
        result = orchestrator.run_meeting(
            session_id=session_id,
            agenda=agenda,
            debug_mode=debug_mode
        )
        
        if result.success:
            logger.info("✅ تم إنهاء الاجتماع بنجاح")
            logger.info(f"📁 الملفات المنتجة: {len(result.artifacts)}")
            
            # طباعة ملخص النتائج
            if result.decisions:
                logger.info(f"🗳️ القرارات المتخذة: {len(result.decisions)}")
            
            if result.action_items:
                logger.info(f"📝 عناصر العمل: {len(result.action_items)}")
            
        else:
            logger.error("❌ فشل الاجتماع")
            logger.error(f"السبب: {result.error}")
            sys.exit(1)
            
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"💥 خطأ غير متوقع: {e}")
        logger.exception("تفاصيل الخطأ:")
        sys.exit(1)


if __name__ == "__main__":
    main()