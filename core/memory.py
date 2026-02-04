"""
نظام الذاكرة الدائم لـ AACS V0
"""
import json
import jsonlines
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict

from .config import Config
from .logger import setup_logger, SecureLogger


@dataclass
class MemoryEntry:
    """إدخال في الذاكرة"""
    id: str
    timestamp: str
    type: str  # meeting, decision, reflection, failure, etc.
    content: Dict[str, Any]
    metadata: Dict[str, Any] = None
    tags: List[str] = None


@dataclass
class QueryResult:
    """نتيجة استعلام الذاكرة"""
    entries: List[MemoryEntry]
    total_count: int
    query_time_ms: float


class MemorySystem:
    """نظام الذاكرة الدائم"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = SecureLogger(setup_logger("memory"))
        
        # مسارات التخزين
        self.base_path = Path("memory")
        self.meetings_path = Path(config.MEETINGS_DIR)
        self.board_path = Path(config.BOARD_DIR)
        
        # إنشاء المجلدات
        self._ensure_directories()
        
        # فهارس الذاكرة
        self.memory_index = self._load_memory_index()
        
        self.logger.info("🧠 تم تهيئة نظام الذاكرة")
    
    def _ensure_directories(self):
        """إنشاء المجلدات المطلوبة"""
        directories = [
            self.base_path,
            self.base_path / "meetings",
            self.base_path / "decisions", 
            self.base_path / "reflections",
            self.base_path / "failures",
            self.base_path / "backups",
            self.meetings_path,
            self.board_path
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _load_memory_index(self) -> Dict[str, Any]:
        """تحميل فهرس الذاكرة"""
        index_file = self.base_path / "index.json"
        
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"فشل في تحميل فهرس الذاكرة: {e}")
        
        # فهرس افتراضي
        return {
            "version": "1.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "entries_count": 0,
            "categories": {
                "meetings": 0,
                "decisions": 0,
                "reflections": 0,
                "failures": 0
            }
        }
    
    def _save_memory_index(self):
        """حفظ فهرس الذاكرة"""
        index_file = self.base_path / "index.json"
        
        self.memory_index["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        try:
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"فشل في حفظ فهرس الذاكرة: {e}")
    
    def store_meeting_data(self, session_id: str, meeting_data: Dict[str, Any], 
                          transcript: List[Dict[str, Any]], decisions: List[Dict[str, Any]], 
                          reflections: Dict[str, str]) -> bool:
        """حفظ بيانات الاجتماع في الذاكرة الدائمة"""
        try:
            self.logger.info(f"💾 حفظ بيانات الاجتماع: {session_id}")
            
            # حفظ بيانات الاجتماع الأساسية
            meeting_entry = MemoryEntry(
                id=f"meeting_{session_id}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                type="meeting",
                content={
                    "session_id": session_id,
                    "meeting_data": meeting_data,
                    "transcript_summary": self._summarize_transcript(transcript),
                    "participants": meeting_data.get("participants", []),
                    "agenda": meeting_data.get("agenda", ""),
                    "decisions_count": len(decisions)
                },
                metadata={
                    "source": "meeting_orchestrator",
                    "transcript_length": len(transcript)
                },
                tags=["meeting", "session", session_id]
            )
            
            self._store_entry(meeting_entry, "meetings")
            
            # حفظ القرارات
            for decision in decisions:
                decision_entry = MemoryEntry(
                    id=f"decision_{decision['id']}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    type="decision",
                    content=decision,
                    metadata={
                        "session_id": session_id,
                        "outcome": decision.get("outcome", "unknown")
                    },
                    tags=["decision", session_id, decision.get("outcome", "unknown")]
                )
                
                self._store_entry(decision_entry, "decisions")
            
            # حفظ التأملات الذاتية
            for agent_id, reflection_content in reflections.items():
                reflection_entry = MemoryEntry(
                    id=f"reflection_{session_id}_{agent_id}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    type="reflection",
                    content={
                        "agent_id": agent_id,
                        "session_id": session_id,
                        "reflection_text": reflection_content,
                        "extracted_insights": self._extract_reflection_insights(reflection_content)
                    },
                    metadata={
                        "session_id": session_id,
                        "agent_id": agent_id
                    },
                    tags=["reflection", agent_id, session_id]
                )
                
                self._store_entry(reflection_entry, "reflections")
            
            # تحديث الإحصائيات
            self.memory_index["entries_count"] += 1 + len(decisions) + len(reflections)
            self.memory_index["categories"]["meetings"] += 1
            self.memory_index["categories"]["decisions"] += len(decisions)
            self.memory_index["categories"]["reflections"] += len(reflections)
            
            self._save_memory_index()
            
            self.logger.info(f"✅ تم حفظ بيانات الاجتماع {session_id} بنجاح")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ فشل في حفظ بيانات الاجتماع {session_id}: {e}")
            return False
    
    def _store_entry(self, entry: MemoryEntry, category: str):
        """حفظ إدخال في فئة محددة"""
        category_path = self.base_path / category
        entry_file = category_path / f"{entry.id}.json"
        
        with open(entry_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(entry), f, ensure_ascii=False, indent=2)
    
    def _summarize_transcript(self, transcript: List[Dict[str, Any]]) -> Dict[str, Any]:
        """تلخيص محضر الاجتماع"""
        if not transcript:
            return {"summary": "لا يوجد محضر", "message_count": 0}
        
        # إحصائيات أساسية
        message_types = {}
        agent_participation = {}
        
        for entry in transcript:
            msg_type = entry.get("type", "unknown")
            agent = entry.get("agent", "unknown")
            
            message_types[msg_type] = message_types.get(msg_type, 0) + 1
            agent_participation[agent] = agent_participation.get(agent, 0) + 1
        
        return {
            "message_count": len(transcript),
            "message_types": message_types,
            "agent_participation": agent_participation,
            "duration_estimated": f"{len(transcript) * 2} دقيقة",  # تقدير بسيط
            "key_topics": self._extract_key_topics(transcript)
        }
    
    def _extract_key_topics(self, transcript: List[Dict[str, Any]]) -> List[str]:
        """استخراج المواضيع الرئيسية من المحضر"""
        # استخراج بسيط للكلمات المفتاحية
        key_words = set()
        
        for entry in transcript:
            message = entry.get("message", "").lower()
            
            # كلمات مفتاحية شائعة
            keywords = ["مشروع", "تطوير", "أداة", "تطبيق", "نظام", "موقع", "برنامج", "خدمة"]
            
            for keyword in keywords:
                if keyword in message:
                    key_words.add(keyword)
        
        return list(key_words)
    
    def _extract_reflection_insights(self, reflection_text: str) -> Dict[str, List[str]]:
        """استخراج الرؤى من تقرير التأمل الذاتي"""
        insights = {
            "successes": [],
            "failures": [],
            "improvements": []
        }
        
        lines = reflection_text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if "ما نجح" in line or "نجح" in line:
                current_section = "successes"
            elif "ما فشل" in line or "فشل" in line:
                current_section = "failures"
            elif "خطة التحسين" in line or "تحسين" in line:
                current_section = "improvements"
            elif current_section and line and not line.startswith('#'):
                insights[current_section].append(line)
        
        return insights
    
    def retrieve_context(self, query: str, limit: int = 10, 
                        entry_types: List[str] = None) -> QueryResult:
        """استرجاع السياق بناءً على الاستعلام"""
        start_time = datetime.now()
        
        try:
            entries = []
            
            # البحث في الفئات المحددة أو جميع الفئات
            search_categories = entry_types or ["meetings", "decisions", "reflections"]
            
            for category in search_categories:
                category_path = self.base_path / category
                
                if not category_path.exists():
                    continue
                
                # البحث في ملفات الفئة
                for entry_file in category_path.glob("*.json"):
                    try:
                        with open(entry_file, 'r', encoding='utf-8') as f:
                            entry_data = json.load(f)
                            entry = MemoryEntry(**entry_data)
                            
                            # فحص مطابقة الاستعلام
                            if self._matches_query(entry, query):
                                entries.append(entry)
                    
                    except Exception as e:
                        self.logger.warning(f"فشل في قراءة {entry_file}: {e}")
            
            # ترتيب النتائج حسب التاريخ (الأحدث أولاً)
            entries.sort(key=lambda x: x.timestamp, reverse=True)
            
            # تحديد النتائج
            limited_entries = entries[:limit]
            
            query_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return QueryResult(
                entries=limited_entries,
                total_count=len(entries),
                query_time_ms=query_time
            )
            
        except Exception as e:
            self.logger.error(f"فشل في استرجاع السياق: {e}")
            return QueryResult(entries=[], total_count=0, query_time_ms=0)
    
    def _matches_query(self, entry: MemoryEntry, query: str) -> bool:
        """فحص مطابقة الإدخال للاستعلام"""
        query_lower = query.lower()
        
        # البحث في المحتوى
        content_str = json.dumps(entry.content, ensure_ascii=False).lower()
        if query_lower in content_str:
            return True
        
        # البحث في العلامات
        if entry.tags:
            for tag in entry.tags:
                if query_lower in tag.lower():
                    return True
        
        # البحث في النوع
        if query_lower in entry.type.lower():
            return True
        
        return False
    
    def store_failure(self, failure_data: Dict[str, Any]) -> bool:
        """حفظ بيانات الإخفاق للتعلم"""
        try:
            failure_entry = MemoryEntry(
                id=f"failure_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                type="failure",
                content=failure_data,
                metadata={
                    "severity": failure_data.get("severity", "medium"),
                    "category": failure_data.get("category", "unknown")
                },
                tags=["failure", failure_data.get("category", "unknown")]
            )
            
            self._store_entry(failure_entry, "failures")
            
            # تحديث الإحصائيات
            self.memory_index["entries_count"] += 1
            self.memory_index["categories"]["failures"] += 1
            self._save_memory_index()
            
            self.logger.info(f"💾 تم حفظ بيانات الإخفاق: {failure_entry.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"فشل في حفظ بيانات الإخفاق: {e}")
            return False
    
    def get_failure_patterns(self) -> List[Dict[str, Any]]:
        """الحصول على أنماط الإخفاقات السابقة"""
        try:
            failures_path = self.base_path / "failures"
            patterns = []
            
            if not failures_path.exists():
                return patterns
            
            for failure_file in failures_path.glob("*.json"):
                try:
                    with open(failure_file, 'r', encoding='utf-8') as f:
                        failure_data = json.load(f)
                        patterns.append(failure_data["content"])
                
                except Exception as e:
                    self.logger.warning(f"فشل في قراءة ملف الإخفاق {failure_file}: {e}")
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"فشل في استرجاع أنماط الإخفاقات: {e}")
            return []
    
    def create_backup(self) -> bool:
        """إنشاء نسخة احتياطية من الذاكرة"""
        try:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = self.base_path / "backups" / backup_name
            
            # نسخ جميع بيانات الذاكرة
            shutil.copytree(self.base_path, backup_path, 
                          ignore=shutil.ignore_patterns("backups"))
            
            # نسخ بيانات الاجتماعات واللوحة
            if self.meetings_path.exists():
                shutil.copytree(self.meetings_path, backup_path / "meetings_data")
            
            if self.board_path.exists():
                shutil.copytree(self.board_path, backup_path / "board_data")
            
            self.logger.info(f"✅ تم إنشاء نسخة احتياطية: {backup_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"فشل في إنشاء النسخة الاحتياطية: {e}")
            return False
    
    def restore_from_backup(self, backup_name: str) -> bool:
        """استعادة من نسخة احتياطية"""
        try:
            backup_path = self.base_path / "backups" / backup_name
            
            if not backup_path.exists():
                self.logger.error(f"النسخة الاحتياطية غير موجودة: {backup_name}")
                return False
            
            # إنشاء نسخة احتياطية من الحالة الحالية قبل الاستعادة
            current_backup = f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.create_backup()
            
            # استعادة البيانات
            # (في بيئة الإنتاج، يجب أن تكون هذه العملية أكثر حذراً)
            
            self.logger.info(f"✅ تم استعادة النسخة الاحتياطية: {backup_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"فشل في استعادة النسخة الاحتياطية: {e}")
            return False
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات الذاكرة"""
        try:
            stats = self.memory_index.copy()
            
            # إضافة إحصائيات إضافية
            stats["storage_size_mb"] = self._calculate_storage_size()
            stats["backup_count"] = len(list((self.base_path / "backups").glob("*")))
            
            return stats
            
        except Exception as e:
            self.logger.error(f"فشل في حساب إحصائيات الذاكرة: {e}")
            return {}
    
    def _calculate_storage_size(self) -> float:
        """حساب حجم التخزين بالميجابايت"""
        try:
            total_size = 0
            
            for path in [self.base_path, self.meetings_path, self.board_path]:
                if path.exists():
                    for file_path in path.rglob("*"):
                        if file_path.is_file():
                            total_size += file_path.stat().st_size
            
            return round(total_size / (1024 * 1024), 2)
            
        except Exception as e:
            self.logger.warning(f"فشل في حساب حجم التخزين: {e}")
            return 0.0
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> bool:
        """تنظيف البيانات القديمة"""
        try:
            cutoff_date = datetime.now(timezone.utc).timestamp() - (days_to_keep * 24 * 60 * 60)
            cleaned_count = 0
            
            # تنظيف النسخ الاحتياطية القديمة
            backups_path = self.base_path / "backups"
            if backups_path.exists():
                for backup_dir in backups_path.iterdir():
                    if backup_dir.is_dir():
                        backup_time = backup_dir.stat().st_mtime
                        if backup_time < cutoff_date:
                            shutil.rmtree(backup_dir)
                            cleaned_count += 1
            
            self.logger.info(f"🧹 تم تنظيف {cleaned_count} عنصر قديم")
            return True
            
        except Exception as e:
            self.logger.error(f"فشل في تنظيف البيانات القديمة: {e}")
            return False