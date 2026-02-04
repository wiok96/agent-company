"""
اختبار خاصية استمرارية الذاكرة
**Feature: autonomous-ai-company-system, Property 2: استمرارية الذاكرة**

**Validates: Requirements 2.1, 2.2, 2.4**

الخاصية: لأي بيانات يتم حفظها في النظام، يجب أن تكون قابلة للاسترجاع بعد إعادة تشغيل النظام مع جميع البيانات الوصفية
"""
import pytest
import tempfile
import shutil
from hypothesis import given, strategies as st, assume, settings
from typing import Dict, List, Any
from datetime import datetime, timezone
from pathlib import Path

from core.memory import MemorySystem, MemoryEntry
from core.config import Config


class TestMemoryPersistenceProperty:
    """اختبارات خاصية استمرارية الذاكرة"""
    
    @settings(max_examples=50)
    @given(
        # توليد بيانات اجتماعات متنوعة
        meeting_data=st.dictionaries(
            keys=st.sampled_from(['session_id', 'agenda', 'timestamp']),
            values=st.text(min_size=1, max_size=100),
            min_size=2,
            max_size=3
        ),
        transcript_size=st.integers(min_value=1, max_value=20),
        decisions_count=st.integers(min_value=0, max_value=5),
        reflections_count=st.integers(min_value=1, max_value=10)
    )
    def test_meeting_data_persistence_property(self, meeting_data: Dict[str, str], 
                                             transcript_size: int, decisions_count: int, 
                                             reflections_count: int):
        """
        **Feature: autonomous-ai-company-system, Property 2: استمرارية الذاكرة**
        
        اختبار أن بيانات الاجتماعات تبقى محفوظة بعد إعادة تشغيل النظام
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # إعداد مسار مؤقت للاختبار
            original_cwd = Path.cwd()
            temp_path = Path(temp_dir)
            
            try:
                # النظام الأول - حفظ البيانات
                config1 = Config()
                memory1 = MemorySystem(config1)
                
                # إنشاء بيانات اجتماع
                session_id = meeting_data.get('session_id', 'test_session')
                
                # توليد محضر
                transcript = []
                for i in range(transcript_size):
                    transcript.append({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "agent": f"agent_{i % 5}",
                        "message": f"رسالة {i}",
                        "type": "contribution"
                    })
                
                # توليد قرارات
                decisions = []
                for i in range(decisions_count):
                    decisions.append({
                        "id": f"decision_{i}",
                        "title": f"قرار {i}",
                        "description": f"وصف القرار {i}",
                        "outcome": "approved" if i % 2 == 0 else "rejected"
                    })
                
                # توليد تأملات
                reflections = {}
                for i in range(reflections_count):
                    reflections[f"agent_{i}"] = f"تأمل الوكيل {i}"
                
                # حفظ البيانات
                save_result = memory1.store_meeting_data(
                    session_id, meeting_data, transcript, decisions, reflections
                )
                
                # الخاصية: يجب أن ينجح الحفظ
                assert save_result == True, "فشل في حفظ بيانات الاجتماع"
                
                # الحصول على إحصائيات النظام الأول
                stats1 = memory1.get_memory_statistics()
                
                # النظام الثاني - إعادة تشغيل واسترجاع
                config2 = Config()
                memory2 = MemorySystem(config2)
                
                # الخاصية: الإحصائيات يجب أن تكون متطابقة
                stats2 = memory2.get_memory_statistics()
                assert stats1["entries_count"] == stats2["entries_count"], "عدد الإدخالات لا يتطابق بعد إعادة التشغيل"
                assert stats1["categories"]["meetings"] == stats2["categories"]["meetings"], "عدد الاجتماعات لا يتطابق"
                assert stats1["categories"]["decisions"] == stats2["categories"]["decisions"], "عدد القرارات لا يتطابق"
                assert stats1["categories"]["reflections"] == stats2["categories"]["reflections"], "عدد التأملات لا يتطابق"
                
                # الخاصية: يجب أن نتمكن من استرجاع البيانات
                retrieved_data = memory2.retrieve_context(session_id, limit=100)
                assert retrieved_data.total_count > 0, "لم يتم العثور على البيانات المحفوظة"
                
                # الخاصية: البيانات المسترجعة يجب أن تحتوي على المعلومات الأصلية
                found_meeting = False
                for entry in retrieved_data.entries:
                    if entry.type == "meeting" and session_id in entry.content.get("session_id", ""):
                        found_meeting = True
                        assert entry.content["meeting_data"]["agenda"] == meeting_data.get("agenda", ""), "الأجندة لا تتطابق"
                        break
                
                assert found_meeting, "لم يتم العثور على بيانات الاجتماع المحفوظة"
                
            finally:
                # تنظيف
                pass
    
    @settings(max_examples=30)
    @given(
        # توليد إدخالات ذاكرة متنوعة
        entries=st.lists(
            st.dictionaries(
                keys=st.sampled_from(['id', 'type', 'content', 'tags']),
                values=st.one_of(
                    st.text(min_size=1, max_size=50),
                    st.dictionaries(
                        keys=st.text(min_size=1, max_size=10),
                        values=st.text(min_size=1, max_size=50),
                        min_size=1,
                        max_size=3
                    ),
                    st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5)
                ),
                min_size=2,
                max_size=4
            ),
            min_size=1,
            max_size=10
        )
    )
    def test_arbitrary_data_persistence_property(self, entries: List[Dict[str, Any]]):
        """
        **Feature: autonomous-ai-company-system, Property 2: استمرارية الذاكرة**
        
        اختبار أن أي بيانات يتم حفظها تبقى قابلة للاسترجاع
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # النظام الأول - حفظ البيانات
            config1 = Config()
            memory1 = MemorySystem(config1)
            
            stored_entries = []
            
            for i, entry_data in enumerate(entries):
                # إنشاء إدخال صالح
                entry = MemoryEntry(
                    id=entry_data.get('id', f'test_entry_{i}'),
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    type=entry_data.get('type', 'test'),
                    content=entry_data.get('content', {'test': f'data_{i}'}),
                    tags=entry_data.get('tags', [f'tag_{i}'])
                )
                
                # حفظ الإدخال
                memory1._store_entry(entry, "meetings")
                stored_entries.append(entry)
            
            # تحديث الإحصائيات
            memory1.memory_index["entries_count"] += len(stored_entries)
            memory1.memory_index["categories"]["meetings"] += len(stored_entries)
            memory1._save_memory_index()
            
            # النظام الثاني - إعادة تشغيل
            config2 = Config()
            memory2 = MemorySystem(config2)
            
            # الخاصية: جميع الإدخالات يجب أن تكون قابلة للاسترجاع
            for original_entry in stored_entries:
                # البحث عن الإدخال
                search_results = memory2.retrieve_context(original_entry.id, limit=10)
                
                # الخاصية: يجب العثور على الإدخال
                found = False
                for retrieved_entry in search_results.entries:
                    if retrieved_entry.id == original_entry.id:
                        found = True
                        
                        # الخاصية: البيانات الوصفية يجب أن تتطابق
                        assert retrieved_entry.type == original_entry.type, f"نوع الإدخال لا يتطابق: {original_entry.id}"
                        assert retrieved_entry.timestamp == original_entry.timestamp, f"الطابع الزمني لا يتطابق: {original_entry.id}"
                        
                        break
                
                assert found, f"لم يتم العثور على الإدخال المحفوظ: {original_entry.id}"
    
    @settings(max_examples=20)
    @given(
        # توليد عمليات متعددة على النظام
        operations=st.lists(
            st.dictionaries(
                keys=st.sampled_from(['action', 'data']),
                values=st.one_of(
                    st.sampled_from(['store_meeting', 'store_failure', 'backup', 'query']),
                    st.dictionaries(
                        keys=st.text(min_size=1, max_size=10),
                        values=st.text(min_size=1, max_size=30),
                        min_size=1,
                        max_size=3
                    )
                ),
                min_size=2,
                max_size=2
            ),
            min_size=1,
            max_size=5
        )
    )
    def test_system_restart_consistency_property(self, operations: List[Dict[str, Any]]):
        """
        **Feature: autonomous-ai-company-system, Property 2: استمرارية الذاكرة**
        
        اختبار أن النظام يحافظ على الاتساق بعد عمليات متعددة وإعادة تشغيل
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # النظام الأول - تنفيذ العمليات
            config1 = Config()
            memory1 = MemorySystem(config1)
            
            operations_count = 0
            
            for i, operation in enumerate(operations):
                action = operation.get('action', 'store_meeting')
                data = operation.get('data', {})
                
                if action == 'store_meeting':
                    # حفظ اجتماع
                    session_id = f"session_{i}"
                    meeting_data = {"session_id": session_id, "agenda": f"أجندة {i}"}
                    transcript = [{"agent": "test", "message": f"رسالة {i}", "type": "test"}]
                    decisions = []
                    reflections = {"test_agent": f"تأمل {i}"}
                    
                    result = memory1.store_meeting_data(session_id, meeting_data, transcript, decisions, reflections)
                    if result:
                        operations_count += 1
                
                elif action == 'store_failure':
                    # حفظ إخفاق
                    failure_data = {
                        "title": f"إخفاق {i}",
                        "category": "test",
                        "severity": "low"
                    }
                    result = memory1.store_failure(failure_data)
                    if result:
                        operations_count += 1
                
                elif action == 'backup':
                    # إنشاء نسخة احتياطية
                    memory1.create_backup()
                
                elif action == 'query':
                    # استعلام
                    memory1.retrieve_context("test", limit=5)
            
            # الحصول على الإحصائيات قبل إعادة التشغيل
            stats_before = memory1.get_memory_statistics()
            
            # النظام الثاني - إعادة تشغيل
            config2 = Config()
            memory2 = MemorySystem(config2)
            
            # الخاصية: الإحصائيات يجب أن تكون متسقة
            stats_after = memory2.get_memory_statistics()
            
            # التحقق من الاتساق الأساسي
            assert stats_after["entries_count"] >= 0, "عدد الإدخالات سالب بعد إعادة التشغيل"
            assert stats_after["categories"]["meetings"] >= 0, "عدد الاجتماعات سالب"
            assert stats_after["categories"]["failures"] >= 0, "عدد الإخفاقات سالب"
            
            # الخاصية: يجب أن نتمكن من الاستعلام بدون أخطاء
            query_result = memory2.retrieve_context("test", limit=10)
            assert query_result is not None, "فشل في الاستعلام بعد إعادة التشغيل"
            assert query_result.query_time_ms >= 0, "وقت الاستعلام سالب"
    
    @settings(max_examples=15)
    @given(
        # توليد بيانات إخفاقات متنوعة
        failures=st.lists(
            st.dictionaries(
                keys=st.sampled_from(['title', 'category', 'severity', 'description']),
                values=st.text(min_size=1, max_size=100),
                min_size=2,
                max_size=4
            ),
            min_size=1,
            max_size=8
        )
    )
    def test_failure_data_persistence_property(self, failures: List[Dict[str, str]]):
        """
        **Feature: autonomous-ai-company-system, Property 2: استمرارية الذاكرة**
        
        اختبار أن بيانات الإخفاقات تبقى محفوظة للتعلم المستقبلي
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # النظام الأول - حفظ الإخفاقات
            config1 = Config()
            memory1 = MemorySystem(config1)
            
            stored_failures = []
            
            for failure_data in failures:
                result = memory1.store_failure(failure_data)
                if result:
                    stored_failures.append(failure_data)
            
            # النظام الثاني - إعادة تشغيل واسترجاع
            config2 = Config()
            memory2 = MemorySystem(config2)
            
            # الخاصية: يجب أن نتمكن من استرجاع أنماط الإخفاقات
            patterns = memory2.get_failure_patterns()
            
            # الخاصية: عدد الأنماط يجب أن يطابق عدد الإخفاقات المحفوظة
            assert len(patterns) == len(stored_failures), f"عدد أنماط الإخفاقات لا يتطابق: {len(patterns)} != {len(stored_failures)}"
            
            # الخاصية: كل إخفاق محفوظ يجب أن يكون موجود في الأنماط
            for original_failure in stored_failures:
                found = False
                for pattern in patterns:
                    if (pattern.get('title') == original_failure.get('title') and 
                        pattern.get('category') == original_failure.get('category')):
                        found = True
                        break
                
                assert found, f"لم يتم العثور على الإخفاق المحفوظ: {original_failure.get('title', 'unknown')}"
    
    def test_backup_restore_consistency_property(self):
        """
        **Feature: autonomous-ai-company-system, Property 2: استمرارية الذاكرة**
        
        اختبار أن النسخ الاحتياطية تحافظ على تكامل البيانات
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config()
            memory = MemorySystem(config)
            
            # إضافة بعض البيانات
            test_data = {
                "title": "بيانات اختبار النسخ الاحتياطي",
                "category": "backup_test",
                "content": "محتوى للاختبار"
            }
            
            memory.store_failure(test_data)
            
            # الحصول على الإحصائيات قبل النسخ الاحتياطي
            stats_before = memory.get_memory_statistics()
            
            # إنشاء نسخة احتياطية
            backup_result = memory.create_backup()
            
            # الخاصية: يجب أن ينجح إنشاء النسخة الاحتياطية
            assert backup_result == True, "فشل في إنشاء النسخة الاحتياطية"
            
            # الخاصية: الإحصائيات يجب أن تبقى كما هي بعد النسخ الاحتياطي
            stats_after = memory.get_memory_statistics()
            assert stats_before["entries_count"] == stats_after["entries_count"], "تغيرت الإحصائيات بعد النسخ الاحتياطي"
            
            # الخاصية: يجب أن تزيد عدد النسخ الاحتياطية
            assert stats_after["backup_count"] > stats_before["backup_count"], "لم تزد عدد النسخ الاحتياطية"


if __name__ == "__main__":
    # تشغيل الاختبارات
    test_instance = TestMemoryPersistenceProperty()
    
    print("🧪 اختبارات خاصية استمرارية الذاكرة جاهزة للتشغيل")
    print("لتشغيل الاختبارات: pytest tests/property/test_memory_persistence_property.py -v")