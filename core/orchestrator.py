"""
منسق الاجتماعات الأساسي لـ AACS V0
"""
import json
import jsonlines
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from .config import Config, AGENT_ROLES
from .logger import setup_logger, SecureLogger
from .memory import MemorySystem
from .artifact_validator import ArtifactValidator
from agents.agent_manager import AgentManager
from agents.base_agent import Message


@dataclass
class MeetingResult:
    """نتيجة الاجتماع"""
    success: bool
    session_id: str
    artifacts: List[str]
    decisions: List[Dict[str, Any]]
    action_items: List[str]
    error: Optional[str] = None


@dataclass
class Decision:
    """قرار من الاجتماع"""
    id: str
    title: str
    description: str
    votes: Dict[str, str]
    outcome: str
    roi: Dict[str, Any]
    action_items: List[str]


class MeetingOrchestrator:
    """منسق الاجتماعات الأساسي"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = SecureLogger(setup_logger("orchestrator"))
        
        # إنشاء مدير الوكلاء ونظام الذاكرة ومدقق المخرجات
        self.agent_manager = AgentManager(config)
        self.memory_system = MemorySystem(config)
        self.artifact_validator = ArtifactValidator(config)
        
        # إنشاء المجلدات المطلوبة
        self._ensure_directories()
    
    def _ensure_directories(self):
        """إنشاء المجلدات المطلوبة"""
        dirs = [
            Path(self.config.MEETINGS_DIR),
            Path(self.config.BOARD_DIR),
            Path("logs")
        ]
        
        for dir_path in dirs:
            dir_path.mkdir(exist_ok=True)
            self.logger.debug(f"تم إنشاء المجلد: {dir_path}")
    
    def run_meeting(self, session_id: str, agenda: str, debug_mode: bool = False) -> MeetingResult:
        """تشغيل اجتماع كامل"""
        self.logger.info(f"🚀 بدء الاجتماع: {session_id}")
        
        try:
            # إنشاء مجلد الجلسة
            session_dir = Path(self.config.MEETINGS_DIR) / session_id
            session_dir.mkdir(exist_ok=True)
            
            # بيانات الاجتماع الأساسية
            meeting_data = {
                "session_id": session_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agenda": agenda,
                "participants": AGENT_ROLES,
                "debug_mode": debug_mode
            }
            
            # محاكاة الاجتماع (V0 - نسخة بسيطة)
            transcript_data = self._simulate_meeting(meeting_data)
            decisions = self._extract_decisions(transcript_data)
            action_items = self._extract_action_items(decisions)
            
            # إنتاج المخرجات الإلزامية
            artifacts = self._generate_artifacts(
                session_dir, meeting_data, transcript_data, decisions, action_items
            )
            
            # التحقق من اكتمال المخرجات
            validation_result = self.artifact_validator.validate_meeting_artifacts(session_id)
            
            if not validation_result.is_valid:
                self.logger.warning(f"⚠️ مشاكل في المخرجات: {len(validation_result.missing_files)} مفقود، {len(validation_result.invalid_files)} غير صحيح")
                
                # محاولة إعادة التوليد مرة واحدة
                if validation_result.missing_files:
                    self.logger.info("🔄 محاولة إعادة توليد الملفات المفقودة...")
                    retry_success = self.artifact_validator.retry_failed_generation(session_id, validation_result.missing_files)
                    
                    if retry_success:
                        # إعادة التحقق
                        validation_result = self.artifact_validator.validate_meeting_artifacts(session_id)
                        if validation_result.is_valid:
                            self.logger.info("✅ تم إصلاح المخرجات بنجاح")
                        else:
                            self.logger.warning("⚠️ لا تزال هناك مشاكل في المخرجات")
            else:
                self.logger.info("✅ جميع المخرجات الإلزامية صحيحة ومكتملة")
            
            # تحديث الفهارس
            self._update_indexes(session_id, meeting_data, decisions, action_items)
            
            # حفظ في نظام الذاكرة الدائم
            reflections = self.agent_manager.generate_all_self_reflections(meeting_summary)
            memory_success = self.memory_system.store_meeting_data(
                session_id, meeting_data, transcript_data, decisions, reflections
            )
            
            if memory_success:
                self.logger.info("💾 تم حفظ البيانات في نظام الذاكرة الدائم")
            else:
                self.logger.warning("⚠️ فشل في حفظ البيانات في نظام الذاكرة")
            
            self.logger.info(f"✅ تم إنهاء الاجتماع بنجاح: {session_id}")
            
            return MeetingResult(
                success=True,
                session_id=session_id,
                artifacts=artifacts,
                decisions=decisions,
                action_items=action_items
            )
            
        except Exception as e:
            self.logger.error(f"❌ فشل الاجتماع {session_id}: {e}")
            self.logger.exception("تفاصيل الخطأ:")
            
            return MeetingResult(
                success=False,
                session_id=session_id,
                artifacts=[],
                decisions=[],
                action_items=[],
                error=str(e)
            )
    
    def _simulate_meeting(self, meeting_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """إجراء اجتماع حقيقي مع الوكلاء"""
        self.logger.info("🎭 بدء الاجتماع مع الوكلاء...")
        
        # إعادة تعيين الوكلاء للاجتماع الجديد
        self.agent_manager.reset_all_agents()
        
        transcript = []
        
        # 1. رسالة الافتتاح من رئيس الاجتماع
        opening_context = {
            "meeting_data": meeting_data,
            "expected_response_type": "opening"
        }
        
        opening_msg = self._create_agent_message(
            "chair", 
            opening_context, 
            f"أهلاً وسهلاً بالجميع في اجتماع AACS. الأجندة اليوم: {meeting_data['agenda']}"
        )
        transcript.append(opening_msg)
        
        # 2. مناقشة الموضوع الرئيسي
        discussion_topic = f"مناقشة: {meeting_data['agenda']}"
        discussion_messages = self.agent_manager.conduct_discussion(
            discussion_topic, 
            {"meeting_type": "regular", "agenda": meeting_data['agenda']}
        )
        
        # تحويل رسائل المناقشة إلى تنسيق المحضر
        for msg in discussion_messages:
            transcript.append({
                "timestamp": msg.timestamp,
                "agent": msg.agent_id,
                "message": msg.content,
                "type": msg.message_type
            })
        
        # 3. اقتراح مشروع جديد
        proposal = self._generate_project_proposal(meeting_data)
        
        proposal_msg = self._create_agent_message(
            "chair",
            {"expected_response_type": "proposal"},
            f"أقترح أن نصوت على: {proposal['title']}"
        )
        transcript.append(proposal_msg)
        
        # 4. التصويت على الاقتراح
        votes = self.agent_manager.conduct_voting(proposal)
        
        for agent_id, vote in votes.items():
            vote_msg = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent": agent_id,
                "message": f"صوتي: {vote}",
                "type": "vote"
            }
            transcript.append(vote_msg)
        
        # 5. إعلان النتيجة
        voting_result = self.agent_manager.calculate_voting_result(votes)
        
        result_msg = self._create_agent_message(
            "chair",
            {"expected_response_type": "closing"},
            f"نتيجة التصويت: {voting_result['outcome']} بنسبة {voting_result['approval_percentage']:.1f}%"
        )
        transcript.append(result_msg)
        
        # 6. الخاتمة
        closing_msg = self._create_agent_message(
            "chair",
            {"expected_response_type": "closing"},
            "شكراً للجميع على المشاركة الفعالة. تم إنهاء الاجتماع."
        )
        transcript.append(closing_msg)
        
        return transcript
    
    def _create_agent_message(self, agent_id: str, context: Dict[str, Any], default_content: str) -> Dict[str, Any]:
        """إنشاء رسالة من وكيل محدد"""
        agent = self.agent_manager.get_agent(agent_id)
        
        if agent:
            try:
                content = agent.generate_response(context, default_content)
            except Exception as e:
                self.logger.warning(f"فشل في توليد رد من {agent_id}: {e}")
                content = default_content
        else:
            content = default_content
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": agent_id,
            "message": content,
            "type": context.get("expected_response_type", "contribution")
        }
    
    def _generate_project_proposal(self, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        """توليد اقتراح مشروع بناءً على الأجندة"""
        
        # قوالب مشاريع بسيطة للنسخة V0
        project_templates = [
            {
                "title": "تطوير أداة إدارة المهام البسيطة",
                "description": "بناء تطبيق ويب بسيط لإدارة المهام والمشاريع الصغيرة",
                "type": "web_app"
            },
            {
                "title": "إنشاء مكتبة Python مفيدة",
                "description": "تطوير مكتبة Python تحل مشكلة شائعة في التطوير",
                "type": "library"
            },
            {
                "title": "بناء أداة سطر أوامر",
                "description": "تطوير أداة CLI تساعد المطورين في المهام اليومية",
                "type": "cli_tool"
            },
            {
                "title": "تطوير إضافة متصفح بسيطة",
                "description": "إنشاء إضافة متصفح تحسن تجربة المستخدم",
                "type": "browser_extension"
            }
        ]
        
        # اختيار مشروع بناءً على الأجندة أو عشوائياً
        import random
        selected_template = random.choice(project_templates)
        
        return {
            "id": f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "title": selected_template["title"],
            "description": selected_template["description"],
            "type": selected_template["type"],
            "proposed_by": "chair",
            "meeting_session": meeting_data.get("session_id", "unknown")
        }
    
    def _extract_decisions(self, transcript: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """استخراج القرارات من المحضر"""
        decisions = []
        
        # البحث عن الاقتراحات والتصويت
        proposals = [entry for entry in transcript if entry.get("type") == "proposal"]
        votes = {}
        
        # جمع الأصوات
        for entry in transcript:
            if entry.get("type") == "vote":
                agent_id = entry["agent"]
                vote_text = entry["message"].replace("صوتي: ", "")
                votes[agent_id] = vote_text
        
        # إنشاء قرار لكل اقتراح
        for i, proposal_entry in enumerate(proposals):
            # استخراج عنوان الاقتراح
            proposal_text = proposal_entry["message"]
            if "أقترح أن نصوت على:" in proposal_text:
                title = proposal_text.split("أقترح أن نصوت على:")[-1].strip()
            else:
                title = f"اقتراح {i+1}"
            
            # حساب نتيجة التصويت
            voting_result = self.agent_manager.calculate_voting_result(votes)
            
            # تحليل ROI بسيط
            roi_analysis = self._calculate_simple_roi(title)
            
            decision = {
                "id": f"decision_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i+1:03d}",
                "title": title,
                "description": f"قرار بشأن: {title}",
                "votes": votes,
                "outcome": voting_result["outcome"],
                "voting_details": voting_result,
                "roi": roi_analysis,
                "action_items": self._generate_action_items(title, voting_result["outcome"])
            }
            decisions.append(decision)
        
        return decisions
    
    def _calculate_simple_roi(self, project_title: str) -> Dict[str, Any]:
        """حساب ROI بسيط للمشروع"""
        
        # تقديرات بسيطة بناءً على نوع المشروع
        roi_templates = {
            "أداة إدارة المهام": {
                "estimated_cost": 2000,
                "projected_revenue": 8000,
                "development_time_weeks": 4,
                "market_size": "متوسط"
            },
            "مكتبة": {
                "estimated_cost": 1000,
                "projected_revenue": 3000,
                "development_time_weeks": 2,
                "market_size": "صغير"
            },
            "أداة سطر أوامر": {
                "estimated_cost": 800,
                "projected_revenue": 2000,
                "development_time_weeks": 2,
                "market_size": "صغير"
            },
            "إضافة متصفح": {
                "estimated_cost": 1500,
                "projected_revenue": 5000,
                "development_time_weeks": 3,
                "market_size": "متوسط"
            }
        }
        
        # اختيار القالب المناسب
        selected_template = None
        for key, template in roi_templates.items():
            if key in project_title:
                selected_template = template
                break
        
        if not selected_template:
            # قالب افتراضي
            selected_template = roi_templates["أداة إدارة المهام"]
        
        # حساب ROI
        cost = selected_template["estimated_cost"]
        revenue = selected_template["projected_revenue"]
        roi_percentage = ((revenue - cost) / cost) * 100 if cost > 0 else 0
        
        return {
            "estimated_cost": cost,
            "projected_revenue": revenue,
            "roi_percentage": round(roi_percentage, 1),
            "development_time_weeks": selected_template["development_time_weeks"],
            "market_size": selected_template["market_size"],
            "assumptions": [
                "تقديرات أولية بناءً على مشاريع مماثلة",
                "لا تشمل تكاليف التسويق والدعم",
                "تفترض نجاح المشروع في السوق"
            ]
        }
    
    def _generate_action_items(self, project_title: str, outcome: str) -> List[str]:
        """توليد عناصر العمل بناءً على القرار"""
        
        if outcome == "approved":
            return [
                f"إنشاء مواصفات تفصيلية لـ {project_title}",
                "تحديد الفريق المسؤول عن التنفيذ",
                "وضع جدول زمني للتطوير",
                "إعداد بيئة التطوير والأدوات",
                "بدء مرحلة التصميم والتخطيط"
            ]
        elif outcome == "rejected":
            return [
                f"مراجعة أسباب رفض {project_title}",
                "البحث عن بدائل أو تحسينات",
                "إعادة تقييم الجدوى الاقتصادية",
                "جمع المزيد من المعلومات"
            ]
        else:
            return [
                f"مراجعة إضافية لـ {project_title}",
                "جمع المزيد من الآراء والمعلومات",
                "إعادة طرح الموضوع في الاجتماع القادم"
            ]
    
    def _extract_action_items(self, decisions: List[Dict[str, Any]]) -> List[str]:
        """استخراج عناصر العمل من القرارات"""
        action_items = []
        
        for decision in decisions:
            action_items.extend(decision.get("action_items", []))
        
        return action_items
    
    def _generate_artifacts(self, session_dir: Path, meeting_data: Dict[str, Any], 
                          transcript: List[Dict[str, Any]], decisions: List[Dict[str, Any]], 
                          action_items: List[str]) -> List[str]:
        """إنتاج جميع المخرجات الإلزامية"""
        artifacts = []
        
        # 1. transcript.jsonl
        transcript_file = session_dir / "transcript.jsonl"
        with jsonlines.open(transcript_file, mode='w') as writer:
            for entry in transcript:
                writer.write(entry)
        artifacts.append(str(transcript_file))
        
        # 2. minutes.md
        minutes_file = session_dir / "minutes.md"
        minutes_content = self._generate_minutes(meeting_data, transcript, decisions)
        minutes_file.write_text(minutes_content, encoding='utf-8')
        artifacts.append(str(minutes_file))
        
        # 3. decisions.json
        decisions_file = session_dir / "decisions.json"
        decisions_data = {"decisions": decisions}
        decisions_file.write_text(json.dumps(decisions_data, ensure_ascii=False, indent=2), encoding='utf-8')
        artifacts.append(str(decisions_file))
        
        # 4. self_reflections/
        reflections_dir = session_dir / "self_reflections"
        reflections_dir.mkdir(exist_ok=True)
        
        # توليد تقارير المراجعة الذاتية من مدير الوكلاء
        meeting_summary = {
            "session_id": meeting_data["session_id"],
            "timestamp": meeting_data["timestamp"],
            "agenda": meeting_data["agenda"],
            "decisions_count": len(decisions)
        }
        
        reflections = self.agent_manager.generate_all_self_reflections(meeting_summary)
        
        for agent_id, reflection_content in reflections.items():
            reflection_file = reflections_dir / f"{agent_id}.md"
            reflection_file.write_text(reflection_content, encoding='utf-8')
            artifacts.append(str(reflection_file))
        
        return artifacts
    
    def _generate_minutes(self, meeting_data: Dict[str, Any], transcript: List[Dict[str, Any]], 
                         decisions: List[Dict[str, Any]]) -> str:
        """إنتاج محضر الاجتماع"""
        content = f"""# محضر اجتماع AACS

## معلومات الاجتماع
- **معرف الجلسة**: {meeting_data['session_id']}
- **التاريخ والوقت**: {meeting_data['timestamp']}
- **الأجندة**: {meeting_data['agenda']}
- **المشاركون**: {', '.join(meeting_data['participants'])}

## ملخص المناقشات

"""
        
        # إضافة المساهمات الرئيسية
        for entry in transcript:
            if entry.get("type") in ["contribution", "proposal"]:
                content += f"- **{entry['agent']}**: {entry['message']}\n"
        
        content += "\n## القرارات المتخذة\n\n"
        
        for i, decision in enumerate(decisions, 1):
            content += f"### {i}. {decision['title']}\n"
            content += f"**الوصف**: {decision['description']}\n\n"
            content += f"**النتيجة**: {decision['outcome']}\n\n"
            
            content += "**التصويت**:\n"
            for agent, vote in decision['votes'].items():
                content += f"- {agent}: {vote}\n"
            
            content += f"\n**تحليل ROI**:\n"
            roi = decision['roi']
            content += f"- التكلفة المقدرة: ${roi['estimated_cost']}\n"
            content += f"- الإيرادات المتوقعة: ${roi['projected_revenue']}\n"
            content += f"- نسبة العائد: {roi['roi_percentage']}%\n"
            
            content += f"\n**عناصر العمل**:\n"
            for item in decision['action_items']:
                content += f"- {item}\n"
            
            content += "\n"
        
        content += f"\n---\n*تم إنتاج هذا المحضر تلقائياً بواسطة AACS V0*"
        
        return content
    
    def _update_indexes(self, session_id: str, meeting_data: Dict[str, Any], 
                       decisions: List[Dict[str, Any]], action_items: List[str]):
        """تحديث الفهارس والمؤشرات"""
        
        # تحديث meetings/index.json
        self._update_meetings_index(session_id, meeting_data, decisions)
        
        # تحديث board/tasks.json
        self._update_board_tasks(decisions, action_items)
    
    def _update_meetings_index(self, session_id: str, meeting_data: Dict[str, Any], 
                              decisions: List[Dict[str, Any]]):
        """تحديث فهرس الاجتماعات"""
        index_file = Path(self.config.MEETINGS_DIR) / "index.json"
        
        # قراءة الفهرس الحالي أو إنشاء جديد
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
        else:
            index_data = {"meetings": []}
        
        # إضافة الاجتماع الجديد
        meeting_entry = {
            "session_id": session_id,
            "timestamp": meeting_data["timestamp"],
            "agenda": meeting_data["agenda"],
            "participants": meeting_data["participants"],
            "decisions_count": len(decisions),
            "status": "completed"
        }
        
        index_data["meetings"].append(meeting_entry)
        
        # حفظ الفهرس المحدث
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"✅ تم تحديث فهرس الاجتماعات: {index_file}")
    
    def _update_board_tasks(self, decisions: List[Dict[str, Any]], action_items: List[str]):
        """تحديث لوحة المهام"""
        board_file = Path(self.config.BOARD_DIR) / "tasks.json"
        
        # قراءة اللوحة الحالية أو إنشاء جديدة
        if board_file.exists():
            with open(board_file, 'r', encoding='utf-8') as f:
                board_data = json.load(f)
        else:
            board_data = {
                "todo": [],
                "in_progress": [],
                "done": []
            }
        
        # إضافة المهام الجديدة
        for decision in decisions:
            for item in decision.get("action_items", []):
                task = {
                    "id": f"task_{len(board_data['todo']) + 1:03d}",
                    "title": item,
                    "description": f"مهمة من قرار: {decision['title']}",
                    "decision_id": decision["id"],
                    "assigned_to": "developer",  # افتراضي في V0
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "priority": "medium",
                    "status": "todo"
                }
                board_data["todo"].append(task)
        
        # حفظ اللوحة المحدثة
        with open(board_file, 'w', encoding='utf-8') as f:
            json.dump(board_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"✅ تم تحديث لوحة المهام: {board_file}")