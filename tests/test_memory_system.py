"""
اختبارات نظام الذاكرة
"""
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone

from core.memory import MemorySystem, MemoryEntry
from core.config import Config


def test_memory_system_initialization():
    """اختبار تهيئة نظام الذاكرة"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # تغيير مسار الذاكرة للاختبار
        config = Config()
        
        # إنشاء نظام الذاكرة
        memory = MemorySystem(config)
        
        # التحقق من إنشاء المجلدات
        assert memory.base_path.exists()
        assert (memory.base_path / "meetings").exists()
        assert (memory.base_path / "decisions").exists()
        assert (memory.base_path / "reflections").exists()
        assert (memory.base_path / "failures").exists()
        
        # التحقق من الفهرس
        assert memory.memory_index is not None
        assert "version" in memory.memory_index
        assert "entries_count" in memory.memory_index


def test_store_meeting_data():
    """اختبار حفظ بيانات الاجتماع"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = Config()
        memory = MemorySystem(config)
        
        # بيانات اجتماع تجريبية
        session_id = "test_meeting_001"
        meeting_data = {
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agenda": "اجتماع تجريبي",
            "participants": ["ceo", "pm", "developer"]
        }
        
        transcript = [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent": "chair",
                "message": "بدء الاجتماع",
                "type": "opening"
            },
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent": "ceo",
                "message": "أقترح مشروع جديد",
                "type": "contribution"
            }
        ]
        
        decisions = [
            {
                "id": "decision_001",
                "title": "مشروع تجريبي",
                "description": "وصف المشروع",
                "outcome": "approved",
                "votes": {"ceo": "موافق", "pm": "موافق"}
            }
        ]
        
        reflections = {
            "ceo": "تقرير المراجعة الذاتية للرئيس التنفيذي",
            "pm": "تقرير المراجعة الذاتية لمدير المشاريع"
        }
        
        # حفظ البيانات
        result = memory.store_meeting_data(session_id, meeting_data, transcript, decisions, reflections)
        
        # التحقق من النجاح
        assert result == True
        
        # التحقق من حفظ الملفات
        meeting_file = memory.base_path / "meetings" / f"meeting_{session_id}.json"
        assert meeting_file.exists()
        
        decision_file = memory.base_path / "decisions" / "decision_decision_001.json"
        assert decision_file.exists()
        
        # التحقق من تحديث الإحصائيات
        assert memory.memory_index["categories"]["meetings"] >= 1
        assert memory.memory_index["categories"]["decisions"] >= 1
        assert memory.memory_index["categories"]["reflections"] >= 2


def test_retrieve_context():
    """اختبار استرجاع السياق"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = Config()
        memory = MemorySystem(config)
        
        # إضافة بعض البيانات للاختبار
        test_entry = MemoryEntry(
            id="test_entry_001",
            timestamp=datetime.now(timezone.utc).isoformat(),
            type="meeting",
            content={"title": "اجتماع تطوير المشروع", "description": "مناقشة التطوير"},
            tags=["meeting", "development", "project"]
        )
        
        memory._store_entry(test_entry, "meetings")
        
        # البحث عن البيانات
        result = memory.retrieve_context("تطوير", limit=5)
        
        # التحقق من النتائج
        assert result.total_count >= 1
        assert len(result.entries) >= 1
        assert result.query_time_ms >= 0
        
        # التحقق من مطابقة النتيجة
        found_entry = result.entries[0]
        assert "تطوير" in json.dumps(found_entry.content, ensure_ascii=False)


def test_failure_storage():
    """اختبار حفظ بيانات الإخفاقات"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = Config()
        memory = MemorySystem(config)
        
        # بيانات إخفاق تجريبية
        failure_data = {
            "title": "فشل في تطوير المشروع",
            "description": "المشروع فشل بسبب نقص الموارد",
            "category": "resource_shortage",
            "severity": "high",
            "lessons_learned": ["تخطيط أفضل للموارد", "تقدير أكثر دقة للوقت"]
        }
        
        # حفظ بيانات الإخفاق
        result = memory.store_failure(failure_data)
        
        # التحقق من النجاح
        assert result == True
        
        # التحقق من تحديث الإحصائيات
        assert memory.memory_index["categories"]["failures"] >= 1
        
        # استرجاع أنماط الإخفاقات
        patterns = memory.get_failure_patterns()
        assert len(patterns) >= 1
        assert patterns[0]["category"] == "resource_shortage"


def test_backup_and_restore():
    """اختبار النسخ الاحتياطي والاستعادة"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = Config()
        memory = MemorySystem(config)
        
        # إضافة بعض البيانات
        test_entry = MemoryEntry(
            id="backup_test_001",
            timestamp=datetime.now(timezone.utc).isoformat(),
            type="test",
            content={"test": "backup data"}
        )
        
        memory._store_entry(test_entry, "meetings")
        
        # إنشاء نسخة احتياطية
        backup_result = memory.create_backup()
        assert backup_result == True
        
        # التحقق من وجود النسخة الاحتياطية
        backups_dir = memory.base_path / "backups"
        assert backups_dir.exists()
        
        backup_dirs = list(backups_dir.glob("backup_*"))
        assert len(backup_dirs) >= 1


def test_memory_statistics():
    """اختبار إحصائيات الذاكرة"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = Config()
        memory = MemorySystem(config)
        
        # الحصول على الإحصائيات
        stats = memory.get_memory_statistics()
        
        # التحقق من وجود الحقول المطلوبة
        assert "version" in stats
        assert "entries_count" in stats
        assert "categories" in stats
        assert "storage_size_mb" in stats
        assert "backup_count" in stats
        
        # التحقق من أن الإحصائيات منطقية
        assert stats["entries_count"] >= 0
        assert stats["storage_size_mb"] >= 0
        assert stats["backup_count"] >= 0


def test_query_matching():
    """اختبار مطابقة الاستعلامات"""
    config = Config()
    memory = MemorySystem(config)
    
    # إنشاء إدخال للاختبار
    entry = MemoryEntry(
        id="query_test_001",
        timestamp=datetime.now(timezone.utc).isoformat(),
        type="meeting",
        content={"title": "اجتماع تطوير النظام", "topic": "مناقشة التقنيات الجديدة"},
        tags=["meeting", "development", "technology"]
    )
    
    # اختبار المطابقة
    assert memory._matches_query(entry, "تطوير") == True
    assert memory._matches_query(entry, "النظام") == True
    assert memory._matches_query(entry, "meeting") == True
    assert memory._matches_query(entry, "development") == True
    assert memory._matches_query(entry, "غير موجود") == False


if __name__ == "__main__":
    # تشغيل الاختبارات
    test_memory_system_initialization()
    test_store_meeting_data()
    test_retrieve_context()
    test_failure_storage()
    test_backup_and_restore()
    test_memory_statistics()
    test_query_matching()
    
    print("✅ جميع اختبارات نظام الذاكرة نجحت!")