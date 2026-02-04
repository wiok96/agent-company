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
            meeting_summary = {
                "session_id": session_id,
                "timestamp": meeting_data["timestamp"],
                "agenda": meeting_data["agenda"],
                "decisions_count": len(decisions)
            }
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
        """إجراء اجتماع حقيقي طويل مع مناقشة مفصلة"""
        self.logger.info("🎭 بدء اجتماع شركة هايتك - مناقشة مفصلة...")
        
        # إعادة تعيين الوكلاء للاجتماع الجديد
        self.agent_manager.reset_all_agents()
        
        transcript = []
        
        # 1. افتتاح الاجتماع
        opening_msg = self._create_agent_message(
            "chair", 
            {"company_context": "شركة هايتك رائدة في الحلول التقنية"},
            f"مرحباً بالجميع في اجتماع شركة هايتك. اليوم سنناقش: {meeting_data['agenda']}. كشركة تقنية رائدة، نحتاج لأفكار مبتكرة تحل مشاكل حقيقية."
        )
        transcript.append(opening_msg)
        
        # 2. جولة العصف الذهني - كل وكيل يقترح مشروع حقيقي
        brainstorm_msg = self._create_agent_message(
            "chair",
            {"meeting_phase": "brainstorming"},
            "نبدأ بجولة العصف الذهني. أريد من كل وكيل أن يقترح مشروع تقني مبتكر يحل مشكلة حقيقية في السوق."
        )
        transcript.append(brainstorm_msg)
        
        # توليد مشاريع حقيقية ومبتكرة من كل وكيل
        project_suggestions = self._generate_real_project_suggestions()
        
        # إضافة اقتراحات المشاريع للمحضر
        for suggestion in project_suggestions:
            project_msg = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent": suggestion["agent"],
                "message": suggestion["suggestion"],
                "type": "project_proposal"
            }
            transcript.append(project_msg)
        
        # 3. مناقشة مفصلة لكل اقتراح
        discussion_msg = self._create_agent_message(
            "chair",
            {"meeting_phase": "detailed_discussion"},
            "ممتاز! الآن سنناقش كل اقتراح بالتفصيل. كل وكيل يعطي رأيه التقني والتجاري."
        )
        transcript.append(discussion_msg)
        
        # مناقشة كل اقتراح على حدة
        for i, suggestion in enumerate(project_suggestions):
            # عرض الاقتراح
            presentation_msg = self._create_agent_message(
                "chair",
                {"meeting_phase": "project_presentation"},
                f"الاقتراح {i+1}: {suggestion['suggestion'][:100]}... دعونا نناقش هذا بالتفصيل."
            )
            transcript.append(presentation_msg)
            
            # كل وكيل يعلق على الاقتراح
            evaluation_agents = ["qa", "finance", "critic", "memory", "cto", "pm"]
            for evaluator in evaluation_agents:
                if evaluator != suggestion["agent"]:  # لا يعلق على اقتراحه
                    evaluation = self._create_agent_message(
                        evaluator,
                        {
                            "meeting_phase": "project_evaluation",
                            "current_suggestion": suggestion,
                            "evaluation_focus": self._get_evaluation_focus(evaluator)
                        },
                        f"ما رأيك في هذا الاقتراح من منظور {evaluator}؟"
                    )
                    transcript.append(evaluation)
            
            # صاحب الاقتراح يرد على التعليقات
            response = self._create_agent_message(
                suggestion["agent"],
                {
                    "meeting_phase": "proposal_defense",
                    "defending_proposal": True
                },
                "أشكركم على التعليقات. دعوني أوضح بعض النقاط..."
            )
            transcript.append(response)
        
        # 4. مناقشة مفتوحة وجدال
        open_discussion_msg = self._create_agent_message(
            "chair",
            {"meeting_phase": "open_discussion"},
            "الآن مناقشة مفتوحة. أي وكيل يريد التعليق أو طرح أسئلة إضافية؟"
        )
        transcript.append(open_discussion_msg)
        
        # جولة مناقشة مفتوحة
        discussion_agents = ["critic", "finance", "ceo", "qa", "memory"]
        for agent in discussion_agents:
            open_comment = self._create_agent_message(
                agent,
                {
                    "meeting_phase": "open_debate",
                    "all_suggestions": project_suggestions
                },
                "أريد أن أضيف نقطة مهمة..."
            )
            transcript.append(open_comment)
        
        # 5. تضييق الخيارات
        narrowing_msg = self._create_agent_message(
            "chair",
            {"meeting_phase": "narrowing_options"},
            "بناءً على المناقشة، دعونا نضيق الخيارات. أي الاقتراحات الأكثر جدوى؟"
        )
        transcript.append(narrowing_msg)
        
        # 6. اختيار المشروع للتصويت
        if project_suggestions:
            # اختيار أفضل اقتراح (يمكن تحسينه بخوارزمية ذكية)
            selected_suggestion = project_suggestions[0]
            
            selection_msg = self._create_agent_message(
                "chair",
                {"meeting_phase": "final_selection"},
                f"بناءً على المناقشة المفصلة، أقترح أن نصوت على: {selected_suggestion['suggestion'][:150]}..."
            )
            transcript.append(selection_msg)
            
            # 7. التصويت مع التبرير
            voting_msg = self._create_agent_message(
                "chair",
                {"meeting_phase": "voting_phase"},
                "الآن التصويت. كل وكيل يعطي صوته مع التبرير."
            )
            transcript.append(voting_msg)
            
            proposal_for_voting = {
                "title": self._extract_project_title(selected_suggestion['suggestion']),
                "description": selected_suggestion['suggestion'],
                "proposed_by": selected_suggestion['agent'],
                "full_context": selected_suggestion
            }
            
            votes = self.agent_manager.conduct_voting(proposal_for_voting)
            
            # كل وكيل يبرر صوته
            for agent_id, vote in votes.items():
                vote_justification = self._create_agent_message(
                    agent_id,
                    {
                        "meeting_phase": "vote_justification",
                        "my_vote": vote,
                        "proposal": proposal_for_voting
                    },
                    f"صوتي: {vote}. السبب: ..."
                )
                transcript.append(vote_justification)
            
            # 8. إعلان النتيجة ومناقشة التنفيذ
            voting_result = self.agent_manager.calculate_voting_result(votes)
            
            result_msg = self._create_agent_message(
                "chair",
                {"meeting_phase": "result_announcement"},
                f"نتيجة التصويت: {voting_result['outcome']} بنسبة {voting_result['approval_percentage']:.1f}%"
            )
            transcript.append(result_msg)
            
            # 9. مناقشة خطة التنفيذ (إذا تمت الموافقة)
            if voting_result['outcome'] == 'approved':
                implementation_msg = self._create_agent_message(
                    "chair",
                    {"meeting_phase": "implementation_planning"},
                    "ممتاز! المشروع معتمد. الآن دعونا نناقش خطة التنفيذ العملية."
                )
                transcript.append(implementation_msg)
                
                # كل وكيل يساهم في خطة التنفيذ
                implementation_agents = ["pm", "cto", "developer", "qa", "finance"]
                for agent in implementation_agents:
                    implementation_input = self._create_agent_message(
                        agent,
                        {
                            "meeting_phase": "implementation_contribution",
                            "approved_project": proposal_for_voting
                        },
                        f"من ناحية {agent}، هذا ما نحتاجه للتنفيذ..."
                    )
                    transcript.append(implementation_input)
        
        # 10. الخاتمة والخطوات التالية
        closing_msg = self._create_agent_message(
            "chair",
            {"meeting_phase": "closing"},
            "شكراً للجميع على هذه المناقشة الثرية والمفصلة. هذا ما نتوقعه من فريق شركة هايتك المتميز."
        )
        transcript.append(closing_msg)
        
        self.logger.info(f"✅ انتهى الاجتماع المفصل - {len(transcript)} رسالة")
        return transcript
    
    def _get_evaluation_focus(self, agent_id: str) -> str:
        """تحديد تركيز التقييم لكل وكيل"""
        focus_map = {
            "qa": "الجودة والاختبار والموثوقية",
            "finance": "التكاليف والربحية والجدوى المالية", 
            "critic": "المخاطر والتحديات والنقاط السلبية",
            "memory": "التجارب السابقة والدروس المستفادة",
            "cto": "الجانب التقني والبنية التحتية",
            "pm": "إدارة المشروع والجدول الزمني"
        }
        return focus_map.get(agent_id, "التقييم العام")
    
    def _generate_real_project_suggestions(self) -> List[Dict[str, Any]]:
        """توليد اقتراحات مشاريع حقيقية ومبتكرة من كل وكيل"""
        import random
        
        # مشاريع حقيقية ومفيدة مقسمة حسب دور كل وكيل
        project_pools = {
            "ceo": [
                {
                    "title": "منصة الذكاء الاصطناعي للشركات الناشئة",
                    "description": "تطوير منصة SaaS تستخدم الذكاء الاصطناعي لمساعدة الشركات الناشئة في اتخاذ القرارات الاستراتيجية وتحليل السوق",
                    "problem": "الشركات الناشئة تفتقر للخبرة في التحليل الاستراتيجي",
                    "market": "الشركات الناشئة والمؤسسات الصغيرة"
                },
                {
                    "title": "نظام إدارة المواهب الذكي",
                    "description": "منصة تجمع بين الذكاء الاصطناعي وتحليل البيانات لمساعدة الشركات في اكتشاف وتطوير المواهب",
                    "problem": "صعوبة العثور على المواهب المناسبة وتطويرها",
                    "market": "أقسام الموارد البشرية في الشركات"
                },
                {
                    "title": "منصة التجارة الإلكترونية الذكية",
                    "description": "حل متكامل للتجارة الإلكترونية يستخدم الذكاء الاصطناعي لتحسين تجربة العملاء والمبيعات",
                    "problem": "تعقيد إدارة المتاجر الإلكترونية وضعف التخصيص",
                    "market": "التجار وأصحاب المتاجر الإلكترونية"
                }
            ],
            "cto": [
                {
                    "title": "إطار عمل الحوسبة السحابية المتقدم",
                    "description": "تطوير إطار عمل مفتوح المصدر يبسط نشر وإدارة التطبيقات على البنية السحابية المتعددة",
                    "problem": "تعقيد إدارة التطبيقات عبر منصات سحابية متعددة",
                    "market": "المطورين وفرق DevOps"
                },
                {
                    "title": "نظام مراقبة الأمان السيبراني الذكي",
                    "description": "حل أمني متقدم يستخدم التعلم الآلي لاكتشاف التهديدات السيبرانية والاستجابة لها تلقائياً",
                    "problem": "زيادة التهديدات السيبرانية وبطء الاستجابة التقليدية",
                    "market": "الشركات والمؤسسات الحكومية"
                },
                {
                    "title": "منصة تطوير التطبيقات بدون كود",
                    "description": "أداة تمكن المستخدمين من بناء تطبيقات معقدة بدون كتابة كود برمجي",
                    "problem": "نقص المطورين وبطء عملية التطوير التقليدية",
                    "market": "الشركات الصغيرة ورجال الأعمال"
                }
            ],
            "developer": [
                {
                    "title": "مكتبة الذكاء الاصطناعي للمطورين",
                    "description": "مكتبة Python/JavaScript تبسط استخدام نماذج الذكاء الاصطناعي في التطبيقات العادية",
                    "problem": "تعقيد دمج الذكاء الاصطناعي في التطبيقات",
                    "market": "مطوري البرمجيات والتطبيقات"
                },
                {
                    "title": "أداة تصحيح الأخطاء الذكية",
                    "description": "IDE plugin يستخدم الذكاء الاصطناعي لاكتشاف وإصلاح الأخطاء البرمجية تلقائياً",
                    "problem": "وقت طويل في تصحيح الأخطاء البرمجية",
                    "market": "المطورين وفرق التطوير"
                },
                {
                    "title": "منصة مشاركة الكود الذكية",
                    "description": "موقع يسمح للمطورين بمشاركة أجزاء الكود مع تحليل ذكي وتحسينات مقترحة",
                    "problem": "صعوبة العثور على حلول برمجية جاهزة وموثوقة",
                    "market": "مجتمع المطورين والطلاب"
                }
            ],
            "pm": [
                {
                    "title": "منصة إدارة المشاريع التقنية الذكية",
                    "description": "أداة إدارة مشاريع تستخدم الذكاء الاصطناعي للتنبؤ بالمخاطر وتحسين الجداول الزمنية",
                    "problem": "فشل المشاريع بسبب سوء التخطيط والمتابعة",
                    "market": "مديري المشاريع والفرق التقنية"
                },
                {
                    "title": "نظام تتبع الإنتاجية للفرق الموزعة",
                    "description": "منصة تساعد في إدارة ومراقبة إنتاجية الفرق التي تعمل عن بُعد",
                    "problem": "صعوبة إدارة الفرق الموزعة وقياس الإنتاجية",
                    "market": "الشركات التي تعتمد على العمل عن بُعد"
                },
                {
                    "title": "أداة تحليل متطلبات المشاريع",
                    "description": "نظام يحلل متطلبات المشاريع ويقترح أفضل الحلول التقنية والفرق المناسبة",
                    "problem": "سوء فهم المتطلبات يؤدي لفشل المشاريع",
                    "market": "مديري المنتجات والمشاريع"
                }
            ],
            "marketing": [
                {
                    "title": "منصة التسويق الرقمي الذكية",
                    "description": "حل متكامل للتسويق الرقمي يستخدم الذكاء الاصطناعي لتحسين الحملات وتحليل العملاء",
                    "problem": "صعوبة إدارة حملات التسويق الرقمي وقياس فعاليتها",
                    "market": "الشركات الصغيرة ووكالات التسويق"
                },
                {
                    "title": "أداة تحليل وسائل التواصل الاجتماعي",
                    "description": "منصة تحلل أداء المحتوى على وسائل التواصل وتقترح استراتيجيات تحسين",
                    "problem": "صعوبة فهم أداء المحتوى على وسائل التواصل",
                    "market": "المؤثرين والعلامات التجارية"
                },
                {
                    "title": "نظام إدارة علاقات العملاء الذكي",
                    "description": "CRM متقدم يستخدم الذكاء الاصطناعي لتحليل سلوك العملاء وتحسين التفاعل",
                    "problem": "فقدان العملاء بسبب ضعف المتابعة والتفاعل",
                    "market": "فرق المبيعات وخدمة العملاء"
                }
            ]
        }
        
        suggestions = []
        creative_agents = ["ceo", "cto", "developer", "pm", "marketing"]
        
        for agent_id in creative_agents:
            if agent_id in project_pools:
                # اختيار مشروع عشوائي من مجموعة المشاريع الخاصة بالوكيل
                project = random.choice(project_pools[agent_id])
                
                # تكوين الاقتراح بطريقة طبيعية
                suggestion_text = f"""كـ{agent_id} في شركة هايتك، أقترح تطوير "{project['title']}".

{project['description']}

هذا المشروع يحل مشكلة حقيقية: {project['problem']}

السوق المستهدف: {project['market']}

أعتقد أن هذا المشروع سيكون مربحاً ومفيداً لعملائنا."""
                
                suggestions.append({
                    "agent": agent_id,
                    "suggestion": suggestion_text,
                    "project_data": project,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
        
        return suggestions
    
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
        
        # إنشاء كائن الرسالة
        from agents.base_agent import Message
        message = Message(
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_id=agent_id,
            content=content,
            message_type=context.get("expected_response_type", "contribution"),
            metadata={"agent_name": agent.profile.name if agent else agent_id}
        )
        
        # إضافة الرسالة لتاريخ الوكيل
        if agent:
            agent.add_message(message)
        
        return {
            "timestamp": message.timestamp,
            "agent": agent_id,
            "message": content,
            "type": message.message_type
        }
    
    def _generate_project_proposal(self, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        """توليد اقتراح مشروع حقيقي ومفيد بناءً على الأجندة"""
        
        # مشاريع حقيقية ومفيدة للنسخة V0
        real_projects = [
            {
                "title": "تطوير أداة مراقبة الخوادم البسيطة",
                "description": "بناء أداة CLI تراقب حالة الخوادم وترسل تنبيهات عند المشاكل",
                "type": "monitoring_tool",
                "tech_stack": "Python + FastAPI + SQLite",
                "target_users": "مطوري DevOps والشركات الصغيرة",
                "problem_solved": "مراقبة الخوادم بدون أدوات معقدة ومكلفة"
            },
            {
                "title": "مكتبة Python لإدارة ملفات التكوين",
                "description": "مكتبة تبسط قراءة وكتابة ملفات JSON/YAML/TOML مع التحقق من الصحة",
                "type": "python_library",
                "tech_stack": "Python + Pydantic + pytest",
                "target_users": "مطوري Python",
                "problem_solved": "تعقيد إدارة ملفات التكوين في المشاريع"
            },
            {
                "title": "أداة تحليل استهلاك API البسيطة",
                "description": "تطبيق ويب يحلل استهلاك APIs ويعرض إحصائيات مفيدة",
                "type": "web_analytics",
                "tech_stack": "Python + Flask + Chart.js",
                "target_users": "مطوري APIs والشركات",
                "problem_solved": "فهم أنماط استخدام APIs وتحسين الأداء"
            },
            {
                "title": "إضافة متصفح لحفظ المقالات التقنية",
                "description": "إضافة تحفظ المقالات التقنية مع تصنيف تلقائي وبحث ذكي",
                "type": "browser_extension",
                "tech_stack": "JavaScript + Chrome Extension API + IndexedDB",
                "target_users": "المطورين والتقنيين",
                "problem_solved": "تنظيم وإدارة المقالات التقنية المحفوظة"
            },
            {
                "title": "أداة تحويل قواعد البيانات البسيطة",
                "description": "أداة CLI تحول البيانات بين قواعد بيانات مختلفة (MySQL, PostgreSQL, SQLite)",
                "type": "database_tool",
                "tech_stack": "Python + SQLAlchemy + Click",
                "target_users": "مطوري قواعد البيانات",
                "problem_solved": "تعقيد نقل البيانات بين قواعد بيانات مختلفة"
            },
            {
                "title": "منصة مشاركة الكود المؤقت",
                "description": "موقع بسيط لمشاركة أجزاء الكود مع انتهاء صلاحية تلقائي",
                "type": "web_platform",
                "tech_stack": "Python + FastAPI + Redis + Vue.js",
                "target_users": "المطورين والطلاب",
                "problem_solved": "مشاركة الكود بسرعة وأمان بدون حسابات معقدة"
            }
        ]
        
        # اختيار مشروع عشوائي
        import random
        selected_project = random.choice(real_projects)
        
        return {
            "id": f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "title": selected_project["title"],
            "description": selected_project["description"],
            "type": selected_project["type"],
            "tech_stack": selected_project["tech_stack"],
            "target_users": selected_project["target_users"],
            "problem_solved": selected_project["problem_solved"],
            "proposed_by": "chair",
            "meeting_session": meeting_data.get("session_id", "unknown")
        }
    
    def _extract_decisions(self, transcript: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """استخراج القرارات من المحضر"""
        decisions = []
        
        # البحث عن الاقتراحات في المحضر
        project_proposals = [entry for entry in transcript if entry.get("type") == "project_proposal"]
        
        if not project_proposals:
            self.logger.warning("لم يتم العثور على اقتراحات مشاريع في المحضر")
            return decisions
        
        # اختيار أول اقتراح للتصويت (يمكن تحسينه لاحقاً)
        selected_proposal = project_proposals[0]
        
        # استخراج عنوان المشروع
        project_title = self._extract_project_title(selected_proposal["message"])
        
        # إجراء التصويت على المشروع المختار
        proposal_for_voting = {
            "title": project_title,
            "description": selected_proposal["message"],
            "proposed_by": selected_proposal["agent"],
            "full_context": selected_proposal
        }
        
        votes = self.agent_manager.conduct_voting(proposal_for_voting)
        voting_result = self.agent_manager.calculate_voting_result(votes)
        
        # تحليل ROI
        roi_analysis = self._calculate_simple_roi(project_title)
        
        # إنشاء القرار
        decision = {
            "id": f"decision_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{1:03d}",
            "title": project_title,
            "description": f"قرار بشأن: {project_title}",
            "project_details": {
                "full_description": selected_proposal["message"],
                "proposed_by": selected_proposal["agent"],
                "all_proposals": [
                    {
                        "agent": p["agent"],
                        "title": self._extract_project_title(p["message"]),
                        "description": p["message"]
                    } for p in project_proposals
                ]
            },
            "votes": votes,
            "outcome": voting_result["outcome"],
            "voting_details": voting_result,
            "roi": roi_analysis,
            "action_items": self._generate_action_items(project_title, voting_result["outcome"])
        }
        
        decisions.append(decision)
        
        self.logger.info(f"✅ تم استخراج {len(decisions)} قرار من المحضر")
        return decisions
    
    def _extract_project_title(self, suggestion: str) -> str:
        """استخراج عنوان المشروع من الاقتراح"""
        # البحث عن العنوان بين علامات الاقتباس
        import re
        
        # البحث عن النص بين علامات الاقتباس
        quote_match = re.search(r'"([^"]+)"', suggestion)
        if quote_match:
            return quote_match.group(1)
        
        # البحث عن كلمات مفتاحية للمشاريع
        lines = suggestion.split('\n')
        for line in lines:
            line = line.strip()
            if any(keyword in line for keyword in ['منصة', 'نظام', 'أداة', 'مكتبة', 'إطار عمل']):
                # إزالة البادئات الشائعة
                for prefix in ['كـ', 'أقترح تطوير', 'أقترح', 'تطوير', 'بناء', 'إنشاء']:
                    if line.startswith(prefix):
                        line = line[len(prefix):].strip()
                
                # إزالة علامات الترقيم من النهاية
                line = line.rstrip('.,!?:')
                
                if line:
                    return line[:100]  # أول 100 حرف
        
        # إذا لم نجد عنوان واضح، نستخدم أول جملة
        first_sentence = suggestion.split('.')[0].strip()
        return first_sentence[:100] if first_sentence else "مشروع جديد"
    
    def _calculate_simple_roi(self, project_title: str) -> Dict[str, Any]:
        """حساب ROI واقعي للمشروع بناءً على نوعه"""
        
        # تقديرات واقعية بناءً على نوع المشروع الفعلي
        if "منصة الذكاء الاصطناعي" in project_title or "الذكاء الاصطناعي" in project_title:
            roi_data = {
                "estimated_cost": 25000,
                "projected_revenue": 80000,
                "development_time_weeks": 12,
                "market_size": "كبير - الشركات الناشئة",
                "competition": "متوسط - سوق نامي",
                "monetization": "اشتراك شهري $200-500"
            }
        elif "نظام إدارة المواهب" in project_title or "المواهب" in project_title:
            roi_data = {
                "estimated_cost": 20000,
                "projected_revenue": 60000,
                "development_time_weeks": 10,
                "market_size": "متوسط - أقسام الموارد البشرية",
                "competition": "عالي - حلول موجودة",
                "monetization": "اشتراك شهري $100-300"
            }
        elif "التجارة الإلكترونية" in project_title or "متجر" in project_title:
            roi_data = {
                "estimated_cost": 18000,
                "projected_revenue": 70000,
                "development_time_weeks": 8,
                "market_size": "كبير جداً - التجارة الإلكترونية",
                "competition": "عالي جداً - Shopify, WooCommerce",
                "monetization": "عمولة 2-3% + اشتراك شهري"
            }
        elif "الحوسبة السحابية" in project_title or "سحابية" in project_title:
            roi_data = {
                "estimated_cost": 30000,
                "projected_revenue": 100000,
                "development_time_weeks": 16,
                "market_size": "كبير - المطورين وDevOps",
                "competition": "عالي - AWS, Azure, GCP",
                "monetization": "مفتوح المصدر + خدمات مدفوعة"
            }
        elif "الأمان السيبراني" in project_title or "أمني" in project_title:
            roi_data = {
                "estimated_cost": 35000,
                "projected_revenue": 120000,
                "development_time_weeks": 18,
                "market_size": "كبير - الشركات والحكومات",
                "competition": "متوسط - سوق متخصص",
                "monetization": "ترخيص سنوي $5000-20000"
            }
        elif "بدون كود" in project_title or "no-code" in project_title:
            roi_data = {
                "estimated_cost": 22000,
                "projected_revenue": 85000,
                "development_time_weeks": 14,
                "market_size": "كبير - الشركات الصغيرة",
                "competition": "عالي - Bubble, Webflow",
                "monetization": "اشتراك شهري $50-200"
            }
        elif "مكتبة" in project_title and "مطورين" in project_title:
            roi_data = {
                "estimated_cost": 8000,
                "projected_revenue": 25000,
                "development_time_weeks": 6,
                "market_size": "كبير - مطوري البرمجيات",
                "competition": "متوسط - مكتبات متخصصة",
                "monetization": "مفتوح المصدر + دعم تجاري"
            }
        elif "تصحيح الأخطاء" in project_title or "IDE" in project_title:
            roi_data = {
                "estimated_cost": 15000,
                "projected_revenue": 45000,
                "development_time_weeks": 8,
                "market_size": "متوسط - المطورين",
                "competition": "عالي - أدوات IDE موجودة",
                "monetization": "اشتراك شهري $20-50"
            }
        elif "مشاركة الكود" in project_title:
            roi_data = {
                "estimated_cost": 12000,
                "projected_revenue": 35000,
                "development_time_weeks": 6,
                "market_size": "كبير - مجتمع المطورين",
                "competition": "عالي - GitHub Gist, CodePen",
                "monetization": "إعلانات + حسابات premium"
            }
        elif "إدارة المشاريع" in project_title:
            roi_data = {
                "estimated_cost": 20000,
                "projected_revenue": 65000,
                "development_time_weeks": 10,
                "market_size": "كبير - مديري المشاريع",
                "competition": "عالي جداً - Jira, Asana",
                "monetization": "اشتراك شهري $30-100 لكل مستخدم"
            }
        elif "الإنتاجية" in project_title and "موزعة" in project_title:
            roi_data = {
                "estimated_cost": 18000,
                "projected_revenue": 55000,
                "development_time_weeks": 9,
                "market_size": "متوسط - الشركات الموزعة",
                "competition": "متوسط - أدوات جديدة",
                "monetization": "اشتراك شهري $15-40 لكل مستخدم"
            }
        elif "التسويق الرقمي" in project_title:
            roi_data = {
                "estimated_cost": 25000,
                "projected_revenue": 75000,
                "development_time_weeks": 12,
                "market_size": "كبير - الشركات ووكالات التسويق",
                "competition": "عالي - HubSpot, Mailchimp",
                "monetization": "اشتراك شهري $100-500"
            }
        elif "وسائل التواصل" in project_title:
            roi_data = {
                "estimated_cost": 15000,
                "projected_revenue": 50000,
                "development_time_weeks": 8,
                "market_size": "كبير - المؤثرين والعلامات التجارية",
                "competition": "عالي - Hootsuite, Buffer",
                "monetization": "اشتراك شهري $30-150"
            }
        elif "CRM" in project_title or "علاقات العملاء" in project_title:
            roi_data = {
                "estimated_cost": 22000,
                "projected_revenue": 70000,
                "development_time_weeks": 11,
                "market_size": "كبير - فرق المبيعات",
                "competition": "عالي جداً - Salesforce, HubSpot",
                "monetization": "اشتراك شهري $50-200 لكل مستخدم"
            }
        else:
            # قالب افتراضي للمشاريع غير المحددة
            roi_data = {
                "estimated_cost": 15000,
                "projected_revenue": 50000,
                "development_time_weeks": 8,
                "market_size": "متوسط",
                "competition": "متوسط",
                "monetization": "اشتراك شهري"
            }
        
        # حساب ROI
        cost = roi_data["estimated_cost"]
        revenue = roi_data["projected_revenue"]
        roi_percentage = ((revenue - cost) / cost) * 100 if cost > 0 else 0
        
        return {
            "estimated_cost": cost,
            "projected_revenue": revenue,
            "roi_percentage": round(roi_percentage, 1),
            "development_time_weeks": roi_data["development_time_weeks"],
            "market_size": roi_data["market_size"],
            "competition_level": roi_data["competition"],
            "monetization_strategy": roi_data["monetization"],
            "assumptions": [
                "تقديرات بناءً على مشاريع مماثلة في السوق",
                "تشمل تكاليف التطوير والتسويق الأساسية",
                "تفترض فريق من 3-5 مطورين",
                "العائد متوقع خلال 12-18 شهر"
            ]
        }
    
    def _generate_action_items(self, project_title: str, outcome: str) -> List[str]:
        """توليد عناصر عمل محددة وقابلة للتنفيذ بناءً على القرار"""
        
        if outcome == "approved":
            # تحديد نوع المشروع من العنوان وتوليد مهام محددة
            if "منصة الذكاء الاصطناعي" in project_title:
                return [
                    f"إنشاء مستودع GitHub لمشروع {project_title}",
                    "تصميم قاعدة بيانات للشركات الناشئة والتحليلات",
                    "تطوير نماذج الذكاء الاصطناعي للتحليل الاستراتيجي",
                    "بناء واجهة API لخدمات التحليل",
                    "إنشاء لوحة تحكم تفاعلية للعملاء",
                    "تطوير نظام اشتراكات ومدفوعات",
                    "إجراء اختبارات شاملة مع شركات ناشئة تجريبية"
                ]
            elif "نظام إدارة المواهب" in project_title:
                return [
                    f"إنشاء مستودع GitHub لمشروع {project_title}",
                    "تصميم قاعدة بيانات للموظفين والمهارات",
                    "تطوير خوارزميات تحليل الأداء والمواهب",
                    "بناء نظام تقييم الموظفين الذكي",
                    "إنشاء واجهة إدارة الموارد البشرية",
                    "تطوير تقارير تحليلية للمديرين",
                    "اختبار النظام مع أقسام الموارد البشرية"
                ]
            elif "التجارة الإلكترونية" in project_title:
                return [
                    f"إنشاء مستودع GitHub لمشروع {project_title}",
                    "تصميم قاعدة بيانات للمنتجات والعملاء",
                    "تطوير نظام إدارة المخزون الذكي",
                    "بناء واجهة متجر إلكتروني متجاوبة",
                    "تطوير نظام دفع آمن ومتعدد الطرق",
                    "إنشاء نظام توصيات ذكي للمنتجات",
                    "تطوير لوحة تحكم للتجار",
                    "اختبار الأمان والأداء"
                ]
            elif "الحوسبة السحابية" in project_title:
                return [
                    f"إنشاء مستودع GitHub لمشروع {project_title}",
                    "تصميم هيكل إطار العمل والمكونات الأساسية",
                    "تطوير أدوات نشر التطبيقات السحابية",
                    "بناء واجهة سطر الأوامر (CLI)",
                    "إنشاء دعم للمنصات السحابية الرئيسية",
                    "تطوير نظام مراقبة ومتابعة التطبيقات",
                    "كتابة وثائق شاملة للمطورين",
                    "إنشاء أمثلة ودروس تعليمية"
                ]
            elif "الأمان السيبراني" in project_title:
                return [
                    f"إنشاء مستودع GitHub لمشروع {project_title}",
                    "تطوير خوارزميات كشف التهديدات بالذكاء الاصطناعي",
                    "بناء نظام مراقبة الشبكة في الوقت الفعلي",
                    "إنشاء قاعدة بيانات التهديدات والأنماط",
                    "تطوير نظام الاستجابة التلقائية للتهديدات",
                    "بناء لوحة تحكم أمنية شاملة",
                    "إجراء اختبارات اختراق وأمان",
                    "الحصول على شهادات الأمان المطلوبة"
                ]
            elif "بدون كود" in project_title:
                return [
                    f"إنشاء مستودع GitHub لمشروع {project_title}",
                    "تصميم محرر السحب والإفلات التفاعلي",
                    "تطوير مكتبة المكونات الجاهزة",
                    "بناء نظام توليد الكود التلقائي",
                    "إنشاء نظام إدارة قواعد البيانات المرئي",
                    "تطوير أدوات النشر والاستضافة",
                    "بناء متجر القوالب والإضافات",
                    "اختبار سهولة الاستخدام مع المستخدمين"
                ]
            elif "مكتبة" in project_title and "مطورين" in project_title:
                return [
                    f"إنشاء مستودع GitHub لمشروع {project_title}",
                    "تصميم واجهة برمجة التطبيقات (API)",
                    "تطوير الوحدات الأساسية للمكتبة",
                    "كتابة اختبارات وحدة شاملة",
                    "إنشاء وثائق تقنية مفصلة",
                    "تطوير أمثلة وحالات استخدام",
                    "نشر المكتبة على PyPI/npm",
                    "إنشاء موقع ويب للمكتبة"
                ]
            elif "تصحيح الأخطاء" in project_title:
                return [
                    f"إنشاء مستودع GitHub لمشروع {project_title}",
                    "تطوير خوارزميات تحليل الكود بالذكاء الاصطناعي",
                    "بناء إضافات لبيئات التطوير الشائعة",
                    "إنشاء قاعدة بيانات الأخطاء الشائعة",
                    "تطوير نظام اقتراح الإصلاحات",
                    "بناء واجهة مستخدم بديهية",
                    "اختبار الأداء مع مشاريع كبيرة",
                    "إنشاء نظام تعلم من أخطاء المستخدمين"
                ]
            elif "إدارة المشاريع" in project_title:
                return [
                    f"إنشاء مستودع GitHub لمشروع {project_title}",
                    "تصميم قاعدة بيانات المشاريع والمهام",
                    "تطوير خوارزميات التنبؤ بالمخاطر",
                    "بناء نظام إدارة الفرق والموارد",
                    "إنشاء لوحة تحكم تفاعلية للمديرين",
                    "تطوير تقارير تقدم المشاريع",
                    "بناء نظام إشعارات ذكي",
                    "اختبار التكامل مع أدوات أخرى"
                ]
            elif "التسويق الرقمي" in project_title:
                return [
                    f"إنشاء مستودع GitHub لمشروع {project_title}",
                    "تطوير نظام إدارة الحملات الإعلانية",
                    "بناء أدوات تحليل أداء المحتوى",
                    "إنشاء نظام إدارة وسائل التواصل",
                    "تطوير خوارزميات تحسين الحملات",
                    "بناء لوحة تحكم تحليلية شاملة",
                    "إنشاء نظام تقارير مخصصة",
                    "اختبار التكامل مع منصات الإعلان"
                ]
            else:
                # مهام عامة للمشاريع غير المحددة
                return [
                    f"إنشاء مستودع GitHub لمشروع {project_title}",
                    "كتابة مواصفات تقنية مفصلة",
                    "تصميم هيكل قاعدة البيانات",
                    "تطوير النموذج الأولي الأول",
                    "إنشاء واجهة المستخدم الأساسية",
                    "تطوير واجهة برمجة التطبيقات",
                    "إنشاء اختبارات شاملة",
                    "توثيق طريقة الاستخدام والنشر"
                ]
        elif outcome == "rejected":
            return [
                f"مراجعة أسباب رفض مشروع {project_title}",
                "تحليل ملاحظات الفريق والتحسينات المطلوبة",
                "إعادة تقييم الجدوى التقنية والاقتصادية",
                "البحث عن حلول بديلة أو تعديلات على المشروع",
                "جمع المزيد من آراء المستخدمين المحتملين",
                "دراسة المنافسين والحلول الموجودة بتفصيل أكبر"
            ]
        else:
            return [
                f"إجراء بحث إضافي حول مشروع {project_title}",
                "جمع المزيد من المعلومات التقنية والسوقية",
                "تحليل المنافسين والحلول الموجودة",
                "إعداد دراسة جدوى مفصلة",
                "استشارة خبراء في المجال",
                "إعادة طرح الموضوع في الاجتماع القادم مع معلومات إضافية"
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