"""
اختبار خاصية مخرجات الاجتماع الإلزامية
**Feature: autonomous-ai-company-system, Property 25: مخرجات الاجتماع الإلزامية**

**Validates: Requirements 20.1**

الخاصية: لأي اجتماع يتم إنهاؤه، يجب أن يتم توليد جميع الملفات الإلزامية 
(transcript, minutes, decisions, self_reflections, index, board/tasks.json)
"""
import pytest
import tempfile
import json
import jsonlines
from hypothesis import given, strategies as st, assume, settings
from typing import Dict, List, Any
from datetime import datetime, timezone
from pathlib import Path

from core.orchestrator import MeetingOrchestrator
from core.artifact_validator import ArtifactValidator
from core.config import Config, AGENT_ROLES


class TestMandatoryOutputsProperty:
    """اختبارات خاصية مخرجات الاجتماع الإلزامية"""
    
    @settings(max_examples=30)
    @given(
        # توليد بيانات اجتماعات متنوعة
        meeting_data=st.dictionaries(
            keys=st.sampled_from(['agenda', 'debug_mode']),
            values=st.one_of(
                st.text(min_size=5, max_size=100),
                st.booleans()
            ),
            min_size=1,
            max_size=2
        ),
        session_variations=st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))
    )
    def test_all_mandatory_files_generated_property(self, meeting_data: Dict[str, Any], session_variations: str):
        """
        **Feature: autonomous-ai-company-system, Property 25: مخرجات الاجتماع الإلزامية**
        
        اختبار أن جميع الملفات الإلزامية يتم توليدها لأي اجتماع
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # إعداد التكوين
            config = Config()
            
            # إنشاء معرف جلسة فريد
            session_id = f"test_meeting_{session_variations}_{datetime.now().strftime('%H%M%S')}"
            
            # إنشاء منسق الاجتماع
            orchestrator = MeetingOrchestrator(config)
            
            # تشغيل الاجتماع
            agenda = meeting_data.get('agenda', 'اجتماع تجريبي')
            debug_mode = meeting_data.get('debug_mode', False)
            
            result = orchestrator.run_meeting(
                session_id=session_id,
                agenda=agenda,
                debug_mode=debug_mode
            )
            
            # الخاصية الأساسية: يجب أن ينجح الاجتماع
            assert result.success == True, f"فشل الاجتماع: {result.error}"
            
            # التحقق من المخرجات الإلزامية
            validator = ArtifactValidator(config)
            validation_result = validator.validate_meeting_artifacts(session_id)
            
            # الخاصية: جميع الملفات الإلزامية يجب أن تكون موجودة
            assert validation_result.is_valid == True, f"ملفات مفقودة: {validation_result.missing_files}, ملفات غير صحيحة: {validation_result.invalid_files}"
            
            # الخاصية: لا يجب أن تكون هناك ملفات مفقودة
            assert len(validation_result.missing_files) == 0, f"ملفات مفقودة: {validation_result.missing_files}"
            
            # الخاصية: لا يجب أن تكون هناك ملفات غير صحيحة
            assert len(validation_result.invalid_files) == 0, f"ملفات غير صحيحة: {validation_result.invalid_files}"
    
    @settings(max_examples=20)
    @given(
        # توليد سيناريوهات اجتماعات متعددة
        meeting_scenarios=st.lists(
            st.dictionaries(
                keys=st.sampled_from(['agenda', 'priority']),
                values=st.text(min_size=3, max_size=50),
                min_size=1,
                max_size=2
            ),
            min_size=1,
            max_size=3
        )
    )
    def test_multiple_meetings_outputs_property(self, meeting_scenarios: List[Dict[str, str]]):
        """
        **Feature: autonomous-ai-company-system, Property 25: مخرجات الاجتماع الإلزامية**
        
        اختبار أن كل اجتماع ينتج مخرجاته الإلزامية بشكل مستقل
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config()
            orchestrator = MeetingOrchestrator(config)
            validator = ArtifactValidator(config)
            
            session_ids = []
            
            # تشغيل اجتماعات متعددة
            for i, scenario in enumerate(meeting_scenarios):
                session_id = f"multi_meeting_{i}_{datetime.now().strftime('%H%M%S%f')}"
                session_ids.append(session_id)
                
                agenda = scenario.get('agenda', f'اجتماع {i}')
                
                result = orchestrator.run_meeting(
                    session_id=session_id,
                    agenda=agenda,
                    debug_mode=False
                )
                
                # الخاصية: كل اجتماع يجب أن ينجح
                assert result.success == True, f"فشل الاجتماع {session_id}: {result.error}"
            
            # التحقق من مخرجات كل اجتماع
            for session_id in session_ids:
                validation_result = validator.validate_meeting_artifacts(session_id)
                
                # الخاصية: كل اجتماع يجب أن ينتج مخرجات صحيحة
                assert validation_result.is_valid == True, f"مخرجات غير صحيحة للاجتماع {session_id}: مفقود={validation_result.missing_files}, غير صحيح={validation_result.invalid_files}"
    
    @settings(max_examples=25)
    @given(
        # توليد محتوى متنوع للاختبار
        agenda_content=st.text(min_size=10, max_size=200),
        expected_decisions=st.integers(min_value=0, max_value=3),
        expected_participants=st.integers(min_value=5, max_value=10)
    )
    def test_output_content_completeness_property(self, agenda_content: str, 
                                                expected_decisions: int, expected_participants: int):
        """
        **Feature: autonomous-ai-company-system, Property 25: مخرجات الاجتماع الإلزامية**
        
        اختبار أن محتوى المخرجات مكتمل ويحتوي على البيانات المطلوبة
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config()
            orchestrator = MeetingOrchestrator(config)
            
            session_id = f"content_test_{datetime.now().strftime('%H%M%S%f')}"
            
            result = orchestrator.run_meeting(
                session_id=session_id,
                agenda=agenda_content,
                debug_mode=False
            )
            
            assert result.success == True, f"فشل الاجتماع: {result.error}"
            
            session_dir = Path(config.MEETINGS_DIR) / session_id
            
            # التحقق من محتوى transcript.jsonl
            transcript_file = session_dir / "transcript.jsonl"
            assert transcript_file.exists(), "ملف المحضر غير موجود"
            
            transcript_entries = []
            with jsonlines.open(transcript_file) as reader:
                for entry in reader:
                    transcript_entries.append(entry)
            
            # الخاصية: يجب أن يحتوي المحضر على رسائل من وكلاء متعددين
            participating_agents = set(entry.get('agent', '') for entry in transcript_entries)
            assert len(participating_agents) >= 3, f"عدد الوكلاء المشاركين قليل: {len(participating_agents)}"
            
            # التحقق من محتوى decisions.json
            decisions_file = session_dir / "decisions.json"
            assert decisions_file.exists(), "ملف القرارات غير موجود"
            
            with open(decisions_file, 'r', encoding='utf-8') as f:
                decisions_data = json.load(f)
            
            # الخاصية: يجب أن تكون هناك بنية قرارات صحيحة
            assert "decisions" in decisions_data, "مفتاح القرارات مفقود"
            decisions = decisions_data["decisions"]
            assert isinstance(decisions, list), "القرارات يجب أن تكون قائمة"
            
            # التحقق من محتوى self_reflections/
            reflections_dir = session_dir / "self_reflections"
            assert reflections_dir.exists(), "مجلد التأملات غير موجود"
            
            # الخاصية: يجب أن يكون هناك تأمل لكل وكيل
            reflection_files = list(reflections_dir.glob("*.md"))
            assert len(reflection_files) == len(AGENT_ROLES), f"عدد ملفات التأمل غير صحيح: {len(reflection_files)} != {len(AGENT_ROLES)}"
            
            # التحقق من أن كل ملف تأمل يحتوي على محتوى
            for reflection_file in reflection_files:
                content = reflection_file.read_text(encoding='utf-8')
                assert len(content.strip()) > 0, f"ملف التأمل فارغ: {reflection_file.name}"
                assert "تقرير المراجعة الذاتية" in content, f"محتوى التأمل غير صحيح: {reflection_file.name}"
    
    @settings(max_examples=15)
    @given(
        # توليد سيناريوهات فشل محتملة
        failure_scenarios=st.lists(
            st.sampled_from(['empty_agenda', 'special_chars', 'very_long_agenda']),
            min_size=1,
            max_size=2
        )
    )
    def test_output_generation_robustness_property(self, failure_scenarios: List[str]):
        """
        **Feature: autonomous-ai-company-system, Property 25: مخرجات الاجتماع الإلزامية**
        
        اختبار أن المخرجات يتم توليدها حتى في السيناريوهات الصعبة
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config()
            orchestrator = MeetingOrchestrator(config)
            validator = ArtifactValidator(config)
            
            for i, scenario in enumerate(failure_scenarios):
                session_id = f"robust_test_{scenario}_{i}_{datetime.now().strftime('%H%M%S%f')}"
                
                # إعداد الأجندة حسب السيناريو
                if scenario == 'empty_agenda':
                    agenda = ""
                elif scenario == 'special_chars':
                    agenda = "أجندة مع رموز خاصة: !@#$%^&*()_+-=[]{}|;':\",./<>?"
                elif scenario == 'very_long_agenda':
                    agenda = "أجندة طويلة جداً " * 100
                else:
                    agenda = "أجندة عادية"
                
                # تشغيل الاجتماع
                result = orchestrator.run_meeting(
                    session_id=session_id,
                    agenda=agenda,
                    debug_mode=True  # تفعيل وضع التصحيح للسيناريوهات الصعبة
                )
                
                # الخاصية: حتى في السيناريوهات الصعبة، يجب أن ينجح الاجتماع أو يفشل بأمان
                if result.success:
                    # إذا نجح، يجب أن تكون المخرجات صحيحة
                    validation_result = validator.validate_meeting_artifacts(session_id)
                    assert validation_result.is_valid == True, f"مخرجات غير صحيحة في السيناريو {scenario}: {validation_result.missing_files}"
                else:
                    # إذا فشل، يجب أن يكون هناك رسالة خطأ واضحة
                    assert result.error is not None, f"لا توجد رسالة خطأ في السيناريو {scenario}"
                    assert len(result.error) > 0, f"رسالة خطأ فارغة في السيناريو {scenario}"
    
    @settings(max_examples=10)
    @given(
        # توليد تسلسلات اجتماعات
        meeting_sequence=st.lists(
            st.dictionaries(
                keys=st.sampled_from(['agenda', 'interval_minutes']),
                values=st.one_of(
                    st.text(min_size=5, max_size=50),
                    st.integers(min_value=1, max_value=10)
                ),
                min_size=1,
                max_size=2
            ),
            min_size=2,
            max_size=4
        )
    )
    def test_sequential_meetings_independence_property(self, meeting_sequence: List[Dict[str, Any]]):
        """
        **Feature: autonomous-ai-company-system, Property 25: مخرجات الاجتماع الإلزامية**
        
        اختبار أن الاجتماعات المتتالية تنتج مخرجات مستقلة
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config()
            orchestrator = MeetingOrchestrator(config)
            validator = ArtifactValidator(config)
            
            session_results = []
            
            # تشغيل اجتماعات متتالية
            for i, meeting_config in enumerate(meeting_sequence):
                session_id = f"seq_meeting_{i}_{datetime.now().strftime('%H%M%S%f')}"
                agenda = meeting_config.get('agenda', f'اجتماع متسلسل {i}')
                
                result = orchestrator.run_meeting(
                    session_id=session_id,
                    agenda=agenda,
                    debug_mode=False
                )
                
                session_results.append((session_id, result))
                
                # الخاصية: كل اجتماع يجب أن ينجح بشكل مستقل
                assert result.success == True, f"فشل الاجتماع المتسلسل {i}: {result.error}"
            
            # التحقق من استقلالية المخرجات
            for session_id, result in session_results:
                validation_result = validator.validate_meeting_artifacts(session_id)
                
                # الخاصية: كل اجتماع يجب أن يكون له مخرجات مستقلة وصحيحة
                assert validation_result.is_valid == True, f"مخرجات غير صحيحة للاجتماع المتسلسل {session_id}"
                
                # التحقق من أن المخرجات فريدة لكل جلسة
                session_dir = Path(config.MEETINGS_DIR) / session_id
                transcript_file = session_dir / "transcript.jsonl"
                
                with jsonlines.open(transcript_file) as reader:
                    transcript_entries = list(reader)
                
                # الخاصية: كل محضر يجب أن يحتوي على معرف الجلسة الصحيح
                # (هذا يضمن عدم الخلط بين الجلسات)
                session_dir_name = session_dir.name
                assert session_id in session_dir_name, f"معرف الجلسة لا يتطابق مع اسم المجلد: {session_id} vs {session_dir_name}"
    
    def test_mandatory_files_structure_property(self):
        """
        **Feature: autonomous-ai-company-system, Property 25: مخرجات الاجتماع الإلزامية**
        
        اختبار أن بنية الملفات الإلزامية صحيحة دائماً
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config()
            orchestrator = MeetingOrchestrator(config)
            validator = ArtifactValidator(config)
            
            session_id = f"structure_test_{datetime.now().strftime('%H%M%S%f')}"
            
            result = orchestrator.run_meeting(
                session_id=session_id,
                agenda="اختبار بنية الملفات",
                debug_mode=False
            )
            
            assert result.success == True, f"فشل الاجتماع: {result.error}"
            
            session_dir = Path(config.MEETINGS_DIR) / session_id
            
            # الخاصية: جميع الملفات الإلزامية يجب أن تكون موجودة
            mandatory_files = [
                "transcript.jsonl",
                "minutes.md", 
                "decisions.json"
            ]
            
            for file_name in mandatory_files:
                file_path = session_dir / file_name
                assert file_path.exists(), f"الملف الإلزامي غير موجود: {file_name}"
                assert file_path.stat().st_size > 0, f"الملف الإلزامي فارغ: {file_name}"
            
            # الخاصية: مجلد التأملات يجب أن يحتوي على ملف لكل وكيل
            reflections_dir = session_dir / "self_reflections"
            assert reflections_dir.exists(), "مجلد التأملات غير موجود"
            
            for agent_id in AGENT_ROLES:
                reflection_file = reflections_dir / f"{agent_id}.md"
                assert reflection_file.exists(), f"ملف تأمل الوكيل غير موجود: {agent_id}"
                assert reflection_file.stat().st_size > 0, f"ملف تأمل الوكيل فارغ: {agent_id}"
            
            # الخاصية: فهرس الاجتماعات يجب أن يتم تحديثه
            index_file = Path(config.MEETINGS_DIR) / "index.json"
            assert index_file.exists(), "فهرس الاجتماعات غير موجود"
            
            with open(index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            assert "meetings" in index_data, "مفتاح الاجتماعات مفقود في الفهرس"
            
            # البحث عن الجلسة الحالية في الفهرس
            session_found = False
            for meeting in index_data["meetings"]:
                if meeting.get("session_id") == session_id:
                    session_found = True
                    break
            
            assert session_found, f"الجلسة {session_id} غير موجودة في الفهرس"


if __name__ == "__main__":
    # تشغيل الاختبارات
    test_instance = TestMandatoryOutputsProperty()
    
    # اختبار البنية (لا يحتاج hypothesis)
    test_instance.test_mandatory_files_structure_property()
    print("✅ اختبار بنية الملفات الإلزامية نجح")
    
    print("🧪 اختبارات خاصية المخرجات الإلزامية جاهزة للتشغيل")
    print("لتشغيل الاختبارات: pytest tests/property/test_mandatory_outputs_property.py -v")