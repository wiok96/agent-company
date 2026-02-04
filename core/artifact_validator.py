"""
مدقق المخرجات الإلزامية لـ AACS V0
"""
import json
import jsonlines
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from .config import Config, MEETING_ARTIFACTS, AGENT_ROLES
from .logger import setup_logger, SecureLogger


@dataclass
class ValidationResult:
    """نتيجة التحقق من المخرجات"""
    is_valid: bool
    missing_files: List[str]
    invalid_files: List[str]
    warnings: List[str]
    details: Dict[str, Any]


class ArtifactValidator:
    """مدقق المخرجات الإلزامية"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = SecureLogger(setup_logger("artifact_validator"))
    
    def validate_meeting_artifacts(self, session_id: str) -> ValidationResult:
        """التحقق من جميع مخرجات الاجتماع الإلزامية"""
        self.logger.info(f"🔍 التحقق من مخرجات الاجتماع: {session_id}")
        
        session_dir = Path(self.config.MEETINGS_DIR) / session_id
        
        missing_files = []
        invalid_files = []
        warnings = []
        details = {}
        
        # 1. التحقق من وجود مجلد الجلسة
        if not session_dir.exists():
            return ValidationResult(
                is_valid=False,
                missing_files=[str(session_dir)],
                invalid_files=[],
                warnings=[],
                details={"error": "مجلد الجلسة غير موجود"}
            )
        
        # 2. التحقق من transcript.jsonl
        transcript_result = self._validate_transcript(session_dir)
        if not transcript_result[0]:
            if transcript_result[1] == "missing":
                missing_files.append("transcript.jsonl")
            else:
                invalid_files.append("transcript.jsonl")
        details["transcript"] = transcript_result[2]
        
        # 3. التحقق من minutes.md
        minutes_result = self._validate_minutes(session_dir)
        if not minutes_result[0]:
            if minutes_result[1] == "missing":
                missing_files.append("minutes.md")
            else:
                invalid_files.append("minutes.md")
        details["minutes"] = minutes_result[2]
        
        # 4. التحقق من decisions.json
        decisions_result = self._validate_decisions(session_dir)
        if not decisions_result[0]:
            if decisions_result[1] == "missing":
                missing_files.append("decisions.json")
            else:
                invalid_files.append("decisions.json")
        details["decisions"] = decisions_result[2]
        
        # 5. التحقق من self_reflections/
        reflections_result = self._validate_reflections(session_dir)
        if not reflections_result[0]:
            missing_files.extend(reflections_result[1])
            invalid_files.extend(reflections_result[2])
        details["reflections"] = reflections_result[3]
        
        # 6. التحقق من تحديث meetings/index.json
        index_result = self._validate_meetings_index(session_id)
        if not index_result[0]:
            warnings.append("فهرس الاجتماعات لم يتم تحديثه")
        details["index"] = index_result[1]
        
        # 7. التحقق من تحديث board/tasks.json
        board_result = self._validate_board_update()
        if not board_result[0]:
            warnings.append("لوحة المهام لم يتم تحديثها")
        details["board"] = board_result[1]
        
        # تحديد النتيجة النهائية
        is_valid = len(missing_files) == 0 and len(invalid_files) == 0
        
        result = ValidationResult(
            is_valid=is_valid,
            missing_files=missing_files,
            invalid_files=invalid_files,
            warnings=warnings,
            details=details
        )
        
        if is_valid:
            self.logger.info(f"✅ جميع مخرجات الاجتماع {session_id} صحيحة")
        else:
            self.logger.warning(f"⚠️ مشاكل في مخرجات الاجتماع {session_id}: {len(missing_files)} مفقود، {len(invalid_files)} غير صحيح")
        
        return result
    
    def _validate_transcript(self, session_dir: Path) -> Tuple[bool, str, Dict[str, Any]]:
        """التحقق من ملف transcript.jsonl"""
        transcript_file = session_dir / "transcript.jsonl"
        
        if not transcript_file.exists():
            return False, "missing", {"error": "الملف غير موجود"}
        
        try:
            entries = []
            with jsonlines.open(transcript_file) as reader:
                for entry in reader:
                    entries.append(entry)
            
            # التحقق من المحتوى
            if len(entries) == 0:
                return False, "invalid", {"error": "الملف فارغ"}
            
            # التحقق من الحقول المطلوبة
            required_fields = ["timestamp", "agent", "message", "type"]
            for i, entry in enumerate(entries):
                for field in required_fields:
                    if field not in entry:
                        return False, "invalid", {"error": f"الحقل {field} مفقود في الإدخال {i}"}
            
            # إحصائيات
            agent_counts = {}
            message_types = {}
            
            for entry in entries:
                agent = entry.get("agent", "unknown")
                msg_type = entry.get("type", "unknown")
                
                agent_counts[agent] = agent_counts.get(agent, 0) + 1
                message_types[msg_type] = message_types.get(msg_type, 0) + 1
            
            return True, "valid", {
                "entries_count": len(entries),
                "agent_participation": agent_counts,
                "message_types": message_types
            }
            
        except Exception as e:
            return False, "invalid", {"error": f"خطأ في قراءة الملف: {str(e)}"}
    
    def _validate_minutes(self, session_dir: Path) -> Tuple[bool, str, Dict[str, Any]]:
        """التحقق من ملف minutes.md"""
        minutes_file = session_dir / "minutes.md"
        
        if not minutes_file.exists():
            return False, "missing", {"error": "الملف غير موجود"}
        
        try:
            content = minutes_file.read_text(encoding='utf-8')
            
            if len(content.strip()) == 0:
                return False, "invalid", {"error": "الملف فارغ"}
            
            # التحقق من وجود الأقسام المطلوبة
            required_sections = ["معلومات الاجتماع", "ملخص المناقشات", "القرارات المتخذة"]
            missing_sections = []
            
            for section in required_sections:
                if section not in content:
                    missing_sections.append(section)
            
            if missing_sections:
                return False, "invalid", {"error": f"أقسام مفقودة: {missing_sections}"}
            
            return True, "valid", {
                "content_length": len(content),
                "sections_found": len(required_sections) - len(missing_sections)
            }
            
        except Exception as e:
            return False, "invalid", {"error": f"خطأ في قراءة الملف: {str(e)}"}
    
    def _validate_decisions(self, session_dir: Path) -> Tuple[bool, str, Dict[str, Any]]:
        """التحقق من ملف decisions.json"""
        decisions_file = session_dir / "decisions.json"
        
        if not decisions_file.exists():
            return False, "missing", {"error": "الملف غير موجود"}
        
        try:
            with open(decisions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # التحقق من البنية الأساسية
            if "decisions" not in data:
                return False, "invalid", {"error": "مفتاح 'decisions' مفقود"}
            
            decisions = data["decisions"]
            if not isinstance(decisions, list):
                return False, "invalid", {"error": "decisions يجب أن يكون قائمة"}
            
            # التحقق من كل قرار
            required_decision_fields = ["id", "title", "description", "votes", "outcome"]
            
            for i, decision in enumerate(decisions):
                for field in required_decision_fields:
                    if field not in decision:
                        return False, "invalid", {"error": f"الحقل {field} مفقود في القرار {i}"}
                
                # التحقق من صحة التصويت
                votes = decision.get("votes", {})
                if not isinstance(votes, dict):
                    return False, "invalid", {"error": f"votes يجب أن يكون كائن في القرار {i}"}
                
                # التحقق من صحة النتيجة
                outcome = decision.get("outcome", "")
                valid_outcomes = ["approved", "rejected", "deferred"]
                if outcome not in valid_outcomes:
                    return False, "invalid", {"error": f"نتيجة غير صحيحة في القرار {i}: {outcome}"}
            
            return True, "valid", {
                "decisions_count": len(decisions),
                "total_votes": sum(len(d.get("votes", {})) for d in decisions)
            }
            
        except Exception as e:
            return False, "invalid", {"error": f"خطأ في قراءة الملف: {str(e)}"}
    
    def _validate_reflections(self, session_dir: Path) -> Tuple[bool, List[str], List[str], Dict[str, Any]]:
        """التحقق من مجلد self_reflections/"""
        reflections_dir = session_dir / "self_reflections"
        
        missing_files = []
        invalid_files = []
        details = {}
        
        if not reflections_dir.exists():
            return False, [str(reflections_dir)], [], {"error": "مجلد التأملات غير موجود"}
        
        # التحقق من وجود ملف لكل وكيل
        for agent_id in AGENT_ROLES:
            reflection_file = reflections_dir / f"{agent_id}.md"
            
            if not reflection_file.exists():
                missing_files.append(f"self_reflections/{agent_id}.md")
                continue
            
            try:
                content = reflection_file.read_text(encoding='utf-8')
                
                if len(content.strip()) == 0:
                    invalid_files.append(f"self_reflections/{agent_id}.md")
                    continue
                
                # التحقق من وجود الأقسام المطلوبة
                required_sections = ["تقرير المراجعة الذاتية", "معلومات الاجتماع", "التقييم الذاتي"]
                missing_sections = []
                
                for section in required_sections:
                    if section not in content:
                        missing_sections.append(section)
                
                details[agent_id] = {
                    "content_length": len(content),
                    "missing_sections": missing_sections
                }
                
                if missing_sections:
                    invalid_files.append(f"self_reflections/{agent_id}.md")
                
            except Exception as e:
                invalid_files.append(f"self_reflections/{agent_id}.md")
                details[agent_id] = {"error": str(e)}
        
        is_valid = len(missing_files) == 0 and len(invalid_files) == 0
        return is_valid, missing_files, invalid_files, details
    
    def _validate_meetings_index(self, session_id: str) -> Tuple[bool, Dict[str, Any]]:
        """التحقق من تحديث فهرس الاجتماعات"""
        index_file = Path(self.config.MEETINGS_DIR) / "index.json"
        
        if not index_file.exists():
            return False, {"error": "فهرس الاجتماعات غير موجود"}
        
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if "meetings" not in data:
                return False, {"error": "مفتاح 'meetings' مفقود"}
            
            meetings = data["meetings"]
            
            # البحث عن الجلسة الحالية
            session_found = False
            for meeting in meetings:
                if meeting.get("session_id") == session_id:
                    session_found = True
                    break
            
            if not session_found:
                return False, {"error": f"الجلسة {session_id} غير موجودة في الفهرس"}
            
            return True, {
                "total_meetings": len(meetings),
                "session_found": True
            }
            
        except Exception as e:
            return False, {"error": f"خطأ في قراءة الفهرس: {str(e)}"}
    
    def _validate_board_update(self) -> Tuple[bool, Dict[str, Any]]:
        """التحقق من تحديث لوحة المهام"""
        board_file = Path(self.config.BOARD_DIR) / "tasks.json"
        
        if not board_file.exists():
            return False, {"error": "لوحة المهام غير موجودة"}
        
        try:
            with open(board_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # التحقق من البنية الأساسية
            required_columns = ["todo", "in_progress", "done"]
            for column in required_columns:
                if column not in data:
                    return False, {"error": f"عمود {column} مفقود"}
            
            # حساب إجمالي المهام
            total_tasks = sum(len(data[column]) for column in required_columns)
            
            return True, {
                "total_tasks": total_tasks,
                "todo_count": len(data.get("todo", [])),
                "in_progress_count": len(data.get("in_progress", [])),
                "done_count": len(data.get("done", []))
            }
            
        except Exception as e:
            return False, {"error": f"خطأ في قراءة لوحة المهام: {str(e)}"}
    
    def retry_failed_generation(self, session_id: str, missing_files: List[str]) -> bool:
        """إعادة محاولة توليد الملفات المفقودة"""
        self.logger.info(f"🔄 إعادة محاولة توليد الملفات المفقودة للجلسة {session_id}")
        
        try:
            # هذه الوظيفة ستحتاج للتكامل مع المنسق
            # في الوقت الحالي، نسجل فقط المحاولة
            self.logger.warning(f"إعادة التوليد غير مُنفذة حالياً. ملفات مفقودة: {missing_files}")
            return False
            
        except Exception as e:
            self.logger.error(f"فشل في إعادة التوليد: {e}")
            return False
    
    def generate_validation_report(self, validation_result: ValidationResult, session_id: str) -> str:
        """توليد تقرير التحقق"""
        report = f"""# تقرير التحقق من مخرجات الاجتماع

## معلومات الجلسة
- **معرف الجلسة**: {session_id}
- **وقت التحقق**: {Path().cwd()}
- **النتيجة العامة**: {'✅ صحيح' if validation_result.is_valid else '❌ غير صحيح'}

## الملفات المفقودة ({len(validation_result.missing_files)})
"""
        
        if validation_result.missing_files:
            for file in validation_result.missing_files:
                report += f"- ❌ {file}\n"
        else:
            report += "- لا توجد ملفات مفقودة\n"
        
        report += f"\n## الملفات غير الصحيحة ({len(validation_result.invalid_files)})\n"
        
        if validation_result.invalid_files:
            for file in validation_result.invalid_files:
                report += f"- ⚠️ {file}\n"
        else:
            report += "- لا توجد ملفات غير صحيحة\n"
        
        report += f"\n## التحذيرات ({len(validation_result.warnings)})\n"
        
        if validation_result.warnings:
            for warning in validation_result.warnings:
                report += f"- ⚠️ {warning}\n"
        else:
            report += "- لا توجد تحذيرات\n"
        
        report += "\n## التفاصيل\n"
        for key, details in validation_result.details.items():
            report += f"### {key}\n"
            if isinstance(details, dict):
                for detail_key, detail_value in details.items():
                    report += f"- **{detail_key}**: {detail_value}\n"
            else:
                report += f"- {details}\n"
            report += "\n"
        
        return report