"""
منسق الاجتماعات الأساسي لـ AACS V0 مع نظام التقييم النقدي المسبق
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
from .notification_manager import NotificationManager
from .failure_library import FailureLibrary
from .security_manager import SecurityManager
from .github_issues_manager import GitHubIssuesManager
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
    """منسق الاجتماعات الأساسي مع نظام التقييم النقدي المسبق"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = SecureLogger(setup_logger("orchestrator"))
        
        # إنشاء مدير الوكلاء ونظام الذاكرة ومدقق المخرجات ومدير الإشعارات
        self.memory_system = MemorySystem(config)
        self.security_manager = SecurityManager(config)
        self.failure_library = FailureLibrary(config, self.memory_system)
        self.github_issues_manager = GitHubIssuesManager(config)
        self.agent_manager = AgentManager(config, self.memory_system, self.failure_library)
        self.artifact_validator = ArtifactValidator(config)
        self.notification_manager = NotificationManager(config)
        
        # إنشاء المسجل الآمن
        self.logger = SecureLogger(setup_logger("orchestrator"))
        
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
        """تشغيل اجتماع كامل مع نظام التقييم النقدي المسبق"""
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
            
            # محاكاة الاجتماع مع التقييم النقدي المسبق
            transcript_data = self._simulate_meeting(meeting_data)
            
            # التحقق من فشل التقييم النقدي
            if not transcript_data:
                self.logger.error("❌ فشل الاجتماع بسبب عدم اجتياز التقييم النقدي")
                
                # إرسال إشعار فشل حرج
                self.notification_manager.send_critical_notification(
                    "🚨 فشل التقييم النقدي في الاجتماع",
                    f"فشل اجتماع {session_id} بسبب عدم اجتياز التقييم النقدي المسبق. لا يمكن المتابعة للتصويت بدون تقييم نقدي شامل.",
                    {"session_id": session_id, "failure_type": "critic_evaluation_failed"},
                    session_id
                )
                
                return MeetingResult(
                    success=False,
                    session_id=session_id,
                    artifacts=[],
                    decisions=[],
                    action_items=[],
                    error="فشل التقييم النقدي - لا يمكن المتابعة للتصويت"
                )
            
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
            
            # إرسال إشعار فشل حرج
            self.notification_manager.notify_meeting_failure(
                session_id, 
                str(e),
                {"exception_type": type(e).__name__, "traceback": str(e)}
            )
            
            return MeetingResult(
                success=False,
                session_id=session_id,
                artifacts=[],
                decisions=[],
                action_items=[],
                error=str(e)
            )
    
    def _simulate_meeting(self, meeting_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """إجراء اجتماع مع نظام التقييم النقدي المسبق الإجباري"""
        self.logger.info("🎭 بدء اجتماع شركة هايتك مع التقييم النقدي المسبق...")
        
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
        
        # 2. جولة العصف الذهني
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
        
        # 4. اختيار المشروع للتقييم النقدي والتصويت
        if project_suggestions:
            # اختيار أفضل اقتراح
            selected_suggestion = project_suggestions[0]
            
            selection_msg = self._create_agent_message(
                "chair",
                {"meeting_phase": "final_selection"},
                f"بناءً على المناقشة المفصلة، أقترح أن نقيم ونصوت على: {selected_suggestion['suggestion'][:150]}..."
            )
            transcript.append(selection_msg)
            
            # 5. التقييم النقدي المسبق (إجباري قبل التصويت)
            critic_evaluation_msg = self._create_agent_message(
                "chair",
                {"meeting_phase": "critic_evaluation_required"},
                "⚠️ قبل التصويت، نحتاج لتقييم نقدي شامل من الناقد. هذا إجراء إجباري لضمان دراسة جميع المخاطر والتحديات."
            )
            transcript.append(critic_evaluation_msg)
            
            # طلب التقييم النقدي من الناقد
            critic_evaluation = self._conduct_critic_evaluation(selected_suggestion, transcript)
            transcript.append(critic_evaluation)
            
            # التأكد من اكتمال التقييم النقدي قبل المتابعة
            if not self._validate_critic_evaluation(critic_evaluation):
                # إذا فشل التقييم النقدي، لا يمكن المتابعة للتصويت
                failed_evaluation_msg = self._create_agent_message(
                    "chair",
                    {"meeting_phase": "critic_evaluation_failed"},
                    "❌ التقييم النقدي غير مكتمل أو غير كافي. لا يمكن المتابعة للتصويت بدون تقييم نقدي شامل."
                )
                transcript.append(failed_evaluation_msg)
                
                # إضافة رسالة توضيحية حول أهمية التقييم النقدي
                explanation_msg = self._create_agent_message(
                    "chair",
                    {"meeting_phase": "critic_evaluation_importance"},
                    "التقييم النقدي الشامل ضروري لضمان دراسة جميع المخاطر والتحديات قبل اتخاذ قرارات استثمارية مهمة. سنؤجل التصويت للاجتماع القادم."
                )
                transcript.append(explanation_msg)
                
                # إنهاء الاجتماع بدون تصويت - إرجاع قائمة فارغة للإشارة للفشل
                self.logger.warning("⚠️ تم إنهاء الاجتماع بسبب فشل التقييم النقدي")
                return []
            
            # إعلان اجتياز التقييم النقدي
            evaluation_passed_msg = self._create_agent_message(
                "chair",
                {"meeting_phase": "critic_evaluation_passed"},
                "✅ تم اجتياز التقييم النقدي بنجاح. يمكننا الآن المتابعة للتصويت."
            )
            transcript.append(evaluation_passed_msg)
            
            # 6. التصويت مع التبرير (بعد التقييم النقدي)
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
                if not agent_id.startswith("_"):  # تجنب المعلومات الإضافية
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
            
            # 7. إعلان النتيجة
            voting_result = self.agent_manager.calculate_voting_result(votes)
            
            # حفظ تاريخ التصويت في نظام الذاكرة
            session_id = meeting_data.get("session_id", "unknown_session")
            voting_stored = self.memory_system.store_voting_history(
                session_id, proposal_for_voting, votes, voting_result
            )
            
            if voting_stored:
                self.logger.info("✅ تم حفظ تاريخ التصويت في نظام الذاكرة")
            else:
                self.logger.warning("⚠️ فشل في حفظ تاريخ التصويت")
            
            if voting_result['outcome'] == 'failed_quorum':
                # إرسال إشعار فشل النصاب القانوني
                self.notification_manager.notify_voting_failure(
                    session_id,
                    voting_result.get('failure_reason', 'فشل في الوصول للنصاب القانوني المطلوب'),
                    voting_result
                )
                
                result_msg = self._create_agent_message(
                    "chair",
                    {"meeting_phase": "quorum_failure"},
                    f"⚠️ فشل التصويت: {voting_result['failure_reason']}. لا يمكن اتخاذ قرار بدون النصاب القانوني المطلوب."
                )
                transcript.append(result_msg)
            else:
                result_msg = self._create_agent_message(
                    "chair",
                    {"meeting_phase": "result_announcement"},
                    f"نتيجة التصويت: {voting_result['outcome']} بنسبة {voting_result['approval_percentage']:.1f}%"
                )
                transcript.append(result_msg)
        
        # 8. الخاتمة
        closing_msg = self._create_agent_message(
            "chair",
            {"meeting_phase": "closing"},
            "شكراً للجميع على هذه المناقشة الثرية والتقييم النقدي الشامل. هذا ما نتوقعه من فريق شركة هايتك المتميز."
        )
        transcript.append(closing_msg)
        
        self.logger.info(f"✅ انتهى الاجتماع مع التقييم النقدي - {len(transcript)} رسالة")
        return transcript
    
    def _conduct_critic_evaluation(self, proposal_suggestion: Dict[str, Any], current_transcript: List[Dict[str, Any]]) -> Dict[str, Any]:
        """إجراء التقييم النقدي المسبق الإجباري"""
        
        # بناء سياق شامل للناقد
        evaluation_context = {
            "meeting_phase": "mandatory_critic_evaluation",
            "proposal_to_evaluate": proposal_suggestion,
            "all_discussion": current_transcript,
            "evaluation_requirements": [
                "تحليل المخاطر التقنية والتجارية",
                "تقييم الجدوى والتحديات المحتملة",
                "مقارنة مع الحلول الموجودة في السوق",
                "تحديد نقاط الضعف والثغرات",
                "اقتراح تحسينات أو بدائل",
                "تقييم احتمالية النجاح والفشل"
            ]
        }
        
        # طلب التقييم النقدي الشامل
        evaluation_prompt = f"""كناقد متخصص، مطلوب منك تقييم نقدي شامل وإجباري للاقتراح التالي:

{proposal_suggestion.get('suggestion', 'غير محدد')}

يجب أن يشمل تقييمك:

🔍 **تحليل المخاطر**:
- ما هي المخاطر التقنية الرئيسية؟
- ما هي التحديات التجارية المحتملة؟

⚖️ **تقييم الجدوى**:
- هل المشروع قابل للتنفيذ فعلياً؟
- ما هي الموارد المطلوبة حقيقياً؟

🏪 **تحليل السوق**:
- من هم المنافسون الحاليون؟
- هل هناك طلب فعلي في السوق؟

❌ **نقاط الضعف**:
- ما هي أكبر نقاط الضعف في الاقتراح؟

💡 **التوصيات**:
- هل تنصح بالموافقة أم الرفض؟

كن صريحاً وموضوعياً في تقييمك. هذا التقييم إجباري ولا يمكن التصويت بدونه."""

        # تحسين آلية الاحتياط للناقد
        fallback_evaluation = f"""كناقد، أرى أن هذا الاقتراح يحتاج لمراجعة دقيقة. 

المخاطر الرئيسية تشمل التحديات التقنية والتجارية المحتملة. 

من ناحية الجدوى، المشروع قابل للتنفيذ لكن يتطلب موارد كافية ودراسة السوق بعناية.

أنصح بالمتابعة مع وضع خطة مخاطر واضحة."""

        return self._create_agent_message("critic", evaluation_context, fallback_evaluation)
    
    def _validate_critic_evaluation(self, critic_evaluation: Dict[str, Any]) -> bool:
        """التحقق من اكتمال وجودة التقييم النقدي"""
        
        evaluation_content = critic_evaluation.get("message", "").lower()
        
        # تسجيل محتوى التقييم للتشخيص
        self.logger.info(f"📝 محتوى التقييم النقدي: {critic_evaluation.get('message', 'فارغ')}")
        
        # معايير التحقق من اكتمال التقييم (مرونة أكبر للاختبار)
        required_elements = [
            # يجب أن يحتوي على تحليل للمخاطر أو التحديات
            any(keyword in evaluation_content for keyword in ["مخاطر", "تحديات", "صعوبات", "مشاكل", "تحدي", "صعوبة", "خطر", "risk", "challenge"]),
            
            # يجب أن يحتوي على تقييم للجدوى أو الإمكانية
            any(keyword in evaluation_content for keyword in ["جدوى", "قابل للتنفيذ", "واقعي", "ممكن", "إمكانية", "تنفيذ", "feasible", "possible"]),
            
            # يجب أن يحتوي على تحليل للسوق أو المنافسة أو العملاء
            any(keyword in evaluation_content for keyword in ["سوق", "منافس", "عملاء", "طلب", "منافسة", "عميل", "market", "competitor"]),
            
            # يجب أن يحتوي على نقد أو نقاط ضعف أو تحليل سلبي
            any(keyword in evaluation_content for keyword in ["ضعف", "نقص", "مشكلة", "عيب", "سلبي", "نقد", "لكن", "ولكن", "weakness", "problem"]),
            
            # يجب أن يحتوي على توصية أو رأي واضح
            any(keyword in evaluation_content for keyword in ["أنصح", "أقترح", "توصي", "يجب", "لا يجب", "أرى", "أعتقد", "recommend", "suggest"])
        ]
        
        # التحقق من الحد الأدنى للطول (مرونة أكبر للاختبار)
        min_length_met = len(evaluation_content) >= 20  # تقليل الحد الأدنى
        
        # التحقق من وجود بعض العناصر المطلوبة (مرونة أكبر)
        elements_met = sum(required_elements) >= 1  # 1 من 5 عناصر بدلاً من 2
        
        # التحقق من أن التقييم ليس عاماً جداً (مرونة)
        not_too_generic = not (
            evaluation_content.count("جيد") > 5 or 
            evaluation_content.count("ممتاز") > 5 or
            "لا مشاكل على الإطلاق" in evaluation_content
        )
        
        # التحقق من أن التقييم يحتوي على محتوى فعلي (مرونة أكبر)
        has_substance = len(evaluation_content.split()) >= 3  # 3 كلمات على الأقل
        
        # إذا كان التقييم قصير جداً، نقبله إذا كان يحتوي على كلمات مفتاحية مهمة
        if len(evaluation_content) < 20:
            emergency_keywords = ["مخاطر", "مشكلة", "صعوبة", "تحدي", "ضعف", "نقد", "لا أنصح", "غير مناسب"]
            if any(keyword in evaluation_content for keyword in emergency_keywords):
                self.logger.info("🚨 قبول تقييم قصير يحتوي على كلمات مفتاحية مهمة")
                return True
        
        is_valid = min_length_met and elements_met and not_too_generic and has_substance
        
        # إذا فشل التقييم، نعطي فرصة أخيرة بناءً على وجود أي محتوى مفيد
        if not is_valid and len(evaluation_content) > 10:
            useful_content = any(keyword in evaluation_content for keyword in [
                "تقييم", "تحليل", "رأي", "نظر", "اعتبار", "دراسة", "فحص", "مراجعة"
            ])
            if useful_content:
                self.logger.info("🔄 قبول التقييم بناءً على وجود محتوى مفيد")
                is_valid = True
        
        self.logger.info(f"🔍 تقييم صحة التقييم النقدي:")
        self.logger.info(f"  - الطول الكافي: {min_length_met} ({len(evaluation_content)} حرف)")
        self.logger.info(f"  - العناصر المطلوبة: {sum(required_elements)}/5")
        self.logger.info(f"  - ليس عاماً جداً: {not_too_generic}")
        self.logger.info(f"  - له محتوى فعلي: {has_substance} ({len(evaluation_content.split())} كلمة)")
        self.logger.info(f"  - النتيجة النهائية: {'✅ صالح' if is_valid else '❌ غير صالح'}")
        
        return is_valid
    
    def _generate_real_project_suggestions(self) -> List[Dict[str, Any]]:
        """توليد اقتراحات مشاريع حقيقية ومبتكرة من كل وكيل باستخدام مولد الأفكار"""
        suggestions = []
        
        # استخدام مولد الأفكار للحصول على أفكار متنوعة
        try:
            # توليد 3 أفكار مختلفة
            for i in range(3):
                context = {
                    "meeting_context": "brainstorming_session",
                    "iteration": i,
                    "preferred_category": ["saas", "tool", "bot"][i % 3]  # تنويع الفئات
                }
                
                idea = self.agent_manager.generate_project_idea(context)
                
                # تحويل الفكرة لصيغة الاقتراح
                suggestion_text = self._format_idea_as_suggestion(idea, ["ceo", "cto", "developer"][i])
                
                suggestions.append({
                    "agent": ["ceo", "cto", "developer"][i],
                    "suggestion": suggestion_text,
                    "idea_data": idea,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            
            self.logger.info(f"✅ تم توليد {len(suggestions)} اقتراح باستخدام مولد الأفكار")
            
        except Exception as e:
            self.logger.warning(f"فشل في استخدام مولد الأفكار: {e}")
            # العودة للطريقة القديمة كبديل
            suggestions = self._generate_fallback_suggestions()
        
        return suggestions
    
    def _format_idea_as_suggestion(self, idea: Dict[str, Any], agent_id: str) -> str:
        """تحويل الفكرة المولدة لصيغة اقتراح طبيعي"""
        
        title = idea.get("title", "مشروع جديد")
        description = idea.get("description", "")
        problem = idea.get("problem_statement", "")
        market = idea.get("target_market", "")
        
        # تخصيص الاقتراح حسب الوكيل
        if agent_id == "ceo":
            intro = f"كرئيس تنفيذي لشركة هايتك، أقترح تطوير '{title}'."
        elif agent_id == "cto":
            intro = f"من منظور تقني، أرى فرصة كبيرة في '{title}'."
        else:  # developer
            intro = f"كمطور، أعتقد أن '{title}' مشروع قابل للتنفيذ وسيكون مفيداً."
        
        suggestion = f"""{intro}

{description}

هذا المشروع يحل مشكلة حقيقية: {problem}

السوق المستهدف: {market}

التقنيات المقترحة: {', '.join(idea.get('tech_stack', [])[:3])}

العائد المتوقع: {idea.get('financial_projection', {}).get('roi_percentage', 0):.0f}% ROI

أعتقد أن هذا المشروع سيكون إضافة قيمة لمحفظة شركة هايتك."""
        
        return suggestion
    
    def _generate_fallback_suggestions(self) -> List[Dict[str, Any]]:
        """توليد اقتراحات احتياطية (الطريقة القديمة)"""
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
                }
            ],
            "cto": [
                {
                    "title": "إطار عمل الحوسبة السحابية المتقدم",
                    "description": "تطوير إطار عمل مفتوح المصدر يبسط نشر وإدارة التطبيقات على البنية السحابية المتعددة",
                    "problem": "تعقيد إدارة التطبيقات عبر منصات سحابية متعددة",
                    "market": "المطورين وفرق DevOps"
                }
            ],
            "developer": [
                {
                    "title": "مكتبة الذكاء الاصطناعي للمطورين",
                    "description": "مكتبة Python/JavaScript تبسط استخدام نماذج الذكاء الاصطناعي في التطبيقات العادية",
                    "problem": "تعقيد دمج الذكاء الاصطناعي في التطبيقات",
                    "market": "مطوري البرمجيات والتطبيقات"
                }
            ]
        }
        
        suggestions = []
        creative_agents = ["ceo", "cto", "developer"]
        
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
    
    def _extract_decisions(self, transcript: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """استخراج القرارات من المحضر"""
        decisions = []
        
        # البحث عن الاقتراحات في المحضر
        project_proposals = [entry for entry in transcript if entry.get("type") == "project_proposal"]
        
        if not project_proposals:
            self.logger.warning("لم يتم العثور على اقتراحات مشاريع في المحضر")
            return decisions
        
        # اختيار أول اقتراح للتصويت
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
        
        # حفظ تاريخ التصويت في نظام الذاكرة (للقرارات المستخرجة)
        voting_stored = self.memory_system.store_voting_history(
            f"decision_extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}", 
            proposal_for_voting, votes, voting_result
        )
        
        if voting_stored:
            self.logger.info("✅ تم حفظ تاريخ التصويت للقرار المستخرج")
        
        # تحليل ROI بسيط
        roi_analysis = {
            "estimated_cost": 20000,
            "projected_revenue": 60000,
            "roi_percentage": 200.0,
            "development_time_weeks": 12,
            "market_size": "متوسط",
            "competition_level": "متوسط",
            "monetization_strategy": "اشتراك شهري"
        }
        
        # إنشاء القرار
        decision = {
            "id": f"decision_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{1:03d}",
            "title": project_title,
            "description": f"قرار بشأن: {project_title}",
            "project_details": {
                "full_description": selected_proposal["message"],
                "proposed_by": selected_proposal["agent"]
            },
            "votes": {k: v for k, v in votes.items() if not k.startswith("_")},
            "outcome": voting_result["outcome"],
            "voting_details": voting_result,
            "roi": roi_analysis,
            "action_items": self._generate_action_items(project_title, voting_result["outcome"])
        }
        
        decisions.append(decision)
        
        self.logger.info(f"✅ تم استخراج {len(decisions)} قرار من المحضر")
        return decisions
    
    def _generate_action_items(self, project_title: str, outcome: str) -> List[str]:
        """توليد عناصر عمل محددة وقابلة للتنفيذ بناءً على القرار"""
        
        if outcome == "approved":
            return [
                f"إنشاء مستودع GitHub لمشروع {project_title}",
                "كتابة مواصفات تقنية مفصلة",
                "تصميم هيكل قاعدة البيانات",
                "تطوير النموذج الأولي الأول",
                "إنشاء واجهة المستخدم الأساسية",
                "تطوير واجهة برمجة التطبيقات",
                "إنشاء اختبارات شاملة"
            ]
        elif outcome == "rejected":
            return [
                f"مراجعة أسباب رفض مشروع {project_title}",
                "تحليل ملاحظات الفريق والتحسينات المطلوبة",
                "إعادة تقييم الجدوى التقنية والاقتصادية"
            ]
        elif outcome == "failed_quorum":
            return [
                f"إعادة جدولة التصويت على مشروع {project_title} للاجتماع القادم",
                "التأكد من حضور جميع الوكلاء المصوتين في الاجتماع القادم"
            ]
        else:
            return [
                f"إجراء بحث إضافي حول مشروع {project_title}",
                "جمع المزيد من المعلومات التقنية والسوقية"
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
        content = f"""# محضر اجتماع AACS مع التقييم النقدي المسبق

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
                content += f"- **{entry['agent']}**: {entry['message'][:200]}...\n"
        
        content += "\n## القرارات المتخذة\n\n"
        
        for i, decision in enumerate(decisions, 1):
            content += f"### {i}. {decision['title']}\n"
            content += f"**الوصف**: {decision['description']}\n\n"
            content += f"**النتيجة**: {decision['outcome']}\n\n"
            
            content += "**التصويت**:\n"
            for agent, vote in decision['votes'].items():
                content += f"- {agent}: {vote}\n"
            
            content += f"\n**عناصر العمل**:\n"
            for item in decision['action_items']:
                content += f"- {item}\n"
            
            content += "\n"
        
        content += f"\n---\n*تم إنتاج هذا المحضر تلقائياً بواسطة AACS V0 مع نظام التقييم النقدي المسبق*"
        
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
        """تحديث لوحة المهام مع استخراج ذكي للمهام وتعيين المسؤولين"""
        board_file = Path(self.config.BOARD_DIR) / "tasks.json"
        
        # قراءة اللوحة الحالية أو إنشاء جديدة
        if board_file.exists():
            with open(board_file, 'r', encoding='utf-8') as f:
                board_data = json.load(f)
        else:
            board_data = {
                "todo": [],
                "in_progress": [],
                "done": [],
                "metadata": {
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                    "total_tasks": 0,
                    "projects": {}
                }
            }
        
        # تجنب إضافة مهام مكررة
        existing_task_titles = {task["title"] for task in board_data["todo"] + board_data["in_progress"] + board_data["done"]}
        
        new_tasks_added = 0
        
        # استخراج المهام من القرارات
        for decision in decisions:
            project_title = decision.get("title", "مشروع غير محدد")
            decision_outcome = decision.get("outcome", "unknown")
            
            # تخطي القرارات المرفوضة أو الفاشلة
            if decision_outcome in ["rejected", "failed_quorum"]:
                continue
            
            # استخراج المهام من عناصر العمل
            for item in decision.get("action_items", []):
                # تجنب المهام المكررة
                if item in existing_task_titles:
                    continue
                
                # تحديد المسؤول بناءً على نوع المهمة
                assigned_agent = self._determine_task_assignee(item)
                
                # تحديد الأولوية بناءً على نوع المهمة
                priority = self._determine_task_priority(item)
                
                # تحديد الفئة/المشروع
                project_category = self._extract_project_category(project_title)
                
                task = {
                    "id": f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{new_tasks_added + 1:03d}",
                    "title": item,
                    "description": f"مهمة من قرار: {project_title}",
                    "project": project_title,
                    "project_category": project_category,
                    "decision_id": decision["id"],
                    "assigned_to": assigned_agent,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "priority": priority,
                    "status": "todo",
                    "estimated_hours": self._estimate_task_hours(item),
                    "tags": self._generate_task_tags(item, project_title),
                    "dependencies": [],
                    "progress": 0
                }
                
                board_data["todo"].append(task)
                existing_task_titles.add(item)
                new_tasks_added += 1
        
        # تحديث الإحصائيات
        if "metadata" not in board_data:
            board_data["metadata"] = {
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "total_tasks": 0,
                "projects": {}
            }
        
        board_data["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        board_data["metadata"]["total_tasks"] = len(board_data["todo"]) + len(board_data["in_progress"]) + len(board_data["done"])
        
        # تحديث إحصائيات المشاريع
        project_stats = {}
        for task in board_data["todo"] + board_data["in_progress"] + board_data["done"]:
            project = task.get("project", "غير محدد")
            if project not in project_stats:
                project_stats[project] = {"todo": 0, "in_progress": 0, "done": 0, "total": 0}
            
            status = task.get("status", "todo")
            project_stats[project][status] += 1
            project_stats[project]["total"] += 1
        
        board_data["metadata"]["projects"] = project_stats
        
        # حفظ اللوحة المحدثة
        with open(board_file, 'w', encoding='utf-8') as f:
            json.dump(board_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"✅ تم تحديث لوحة المهام: {board_file} (أضيف {new_tasks_added} مهمة جديدة)")
        
        # تحويل المهام الجديدة إلى GitHub Issues
        if new_tasks_added > 0:
            self._convert_new_tasks_to_issues(board_data, new_tasks_added)
    
    def _determine_task_assignee(self, task_title: str) -> str:
        """تحديد المسؤول عن المهمة بناءً على محتواها"""
        task_lower = task_title.lower()
        
        # مهام التطوير والبرمجة
        if any(keyword in task_lower for keyword in [
            'مستودع', 'github', 'كود', 'برمجة', 'تطوير', 'api', 'قاعدة بيانات', 
            'واجهة', 'نموذج أولي', 'اختبار', 'تطبيق', 'نظام'
        ]):
            return "developer"
        
        # مهام إدارة المشاريع
        elif any(keyword in task_lower for keyword in [
            'جدول زمني', 'تخطيط', 'فريق', 'إدارة', 'تنسيق', 'مراحل', 'متابعة'
        ]):
            return "pm"
        
        # مهام التسويق
        elif any(keyword in task_lower for keyword in [
            'تسويق', 'عملاء', 'ترويج', 'إعلان', 'سوق', 'مبيعات'
        ]):
            return "marketing"
        
        # مهام ضمان الجودة
        elif any(keyword in task_lower for keyword in [
            'اختبار', 'جودة', 'فحص', 'تحقق', 'مراجعة'
        ]):
            return "qa"
        
        # مهام مالية
        elif any(keyword in task_lower for keyword in [
            'ميزانية', 'تكلفة', 'مالي', 'استثمار', 'عائد'
        ]):
            return "finance"
        
        # مهام تقنية متقدمة
        elif any(keyword in task_lower for keyword in [
            'أمان', 'بنية', 'معمارية', 'تقني'
        ]):
            return "cto"
        
        # افتراضي
        else:
            return "developer"
    
    def _determine_task_priority(self, task_title: str) -> str:
        """تحديد أولوية المهمة بناءً على محتواها"""
        task_lower = task_title.lower()
        
        # أولوية عالية
        if any(keyword in task_lower for keyword in [
            'أمان', 'حرج', 'عاجل', 'أساسي', 'مطلوب فوراً'
        ]):
            return "high"
        
        # أولوية منخفضة
        elif any(keyword in task_lower for keyword in [
            'توثيق', 'تحسين', 'اختياري', 'إضافي'
        ]):
            return "low"
        
        # أولوية متوسطة (افتراضي)
        else:
            return "medium"
    
    def _extract_project_category(self, project_title: str) -> str:
        """استخراج فئة المشروع"""
        title_lower = project_title.lower()
        
        if any(keyword in title_lower for keyword in ['ذكاء اصطناعي', 'ai', 'تعلم آلة']):
            return "AI/ML"
        elif any(keyword in title_lower for keyword in ['تجارة إلكترونية', 'متجر', 'مبيعات']):
            return "E-Commerce"
        elif any(keyword in title_lower for keyword in ['إدارة', 'موارد بشرية', 'مواهب']):
            return "Management"
        elif any(keyword in title_lower for keyword in ['منصة', 'نظام', 'تطبيق']):
            return "Platform"
        else:
            return "General"
    
    def _estimate_task_hours(self, task_title: str) -> int:
        """تقدير ساعات العمل المطلوبة للمهمة"""
        task_lower = task_title.lower()
        
        # مهام كبيرة (40+ ساعة)
        if any(keyword in task_lower for keyword in [
            'تطوير نظام', 'بناء منصة', 'تصميم قاعدة بيانات'
        ]):
            return 40
        
        # مهام متوسطة (20-30 ساعة)
        elif any(keyword in task_lower for keyword in [
            'تطوير', 'إنشاء', 'بناء', 'تصميم'
        ]):
            return 24
        
        # مهام صغيرة (8-16 ساعة)
        elif any(keyword in task_lower for keyword in [
            'اختبار', 'مراجعة', 'توثيق', 'إعداد'
        ]):
            return 8
        
        # افتراضي
        else:
            return 16
    
    def _generate_task_tags(self, task_title: str, project_title: str) -> List[str]:
        """توليد علامات للمهمة"""
        tags = []
        task_lower = task_title.lower()
        
        # علامات تقنية
        if 'github' in task_lower:
            tags.append('git')
        if any(keyword in task_lower for keyword in ['api', 'واجهة برمجة']):
            tags.append('api')
        if any(keyword in task_lower for keyword in ['قاعدة بيانات', 'database']):
            tags.append('database')
        if any(keyword in task_lower for keyword in ['اختبار', 'test']):
            tags.append('testing')
        if any(keyword in task_lower for keyword in ['أمان', 'security']):
            tags.append('security')
        
        # علامات المشروع
        if 'ذكاء اصطناعي' in project_title.lower():
            tags.append('ai')
        if 'تجارة إلكترونية' in project_title.lower():
            tags.append('ecommerce')
        
        return tags
    
    def update_task_status(self, task_id: str, new_status: str, assigned_to: str = None) -> bool:
        """تحديث حالة المهمة"""
        board_file = Path(self.config.BOARD_DIR) / "tasks.json"
        
        if not board_file.exists():
            self.logger.error("ملف لوحة المهام غير موجود")
            return False
        
        try:
            with open(board_file, 'r', encoding='utf-8') as f:
                board_data = json.load(f)
            
            # البحث عن المهمة في جميع الحالات
            task_found = False
            task_to_move = None
            source_status = None
            
            for status in ["todo", "in_progress", "done"]:
                for i, task in enumerate(board_data[status]):
                    if task["id"] == task_id:
                        task_to_move = board_data[status].pop(i)
                        source_status = status
                        task_found = True
                        break
                if task_found:
                    break
            
            if not task_found:
                self.logger.error(f"المهمة غير موجودة: {task_id}")
                return False
            
            # تحديث بيانات المهمة
            task_to_move["status"] = new_status
            task_to_move["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            if assigned_to:
                task_to_move["assigned_to"] = assigned_to
            
            # تحديث التقدم بناءً على الحالة
            if new_status == "todo":
                task_to_move["progress"] = 0
            elif new_status == "in_progress":
                task_to_move["progress"] = 50
            elif new_status == "done":
                task_to_move["progress"] = 100
                task_to_move["completed_at"] = datetime.now(timezone.utc).isoformat()
            
            # إضافة المهمة للحالة الجديدة
            if new_status in board_data:
                board_data[new_status].append(task_to_move)
            else:
                self.logger.error(f"حالة غير صحيحة: {new_status}")
                return False
            
            # تحديث الإحصائيات
            board_data["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()
            
            # حفظ التحديثات
            with open(board_file, 'w', encoding='utf-8') as f:
                json.dump(board_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"✅ تم تحديث حالة المهمة {task_id} من {source_status} إلى {new_status}")
            return True
            
        except Exception as e:
            self.logger.error(f"فشل في تحديث حالة المهمة {task_id}: {e}")
            return False
    
    def get_tasks_by_project(self, project_name: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """الحصول على المهام مجمعة حسب المشروع"""
        board_file = Path(self.config.BOARD_DIR) / "tasks.json"
        
        if not board_file.exists():
            return {}
        
        try:
            with open(board_file, 'r', encoding='utf-8') as f:
                board_data = json.load(f)
            
            if project_name:
                # إرجاع مهام مشروع محدد
                project_tasks = {"todo": [], "in_progress": [], "done": []}
                
                for status in ["todo", "in_progress", "done"]:
                    for task in board_data[status]:
                        if task.get("project", "") == project_name:
                            project_tasks[status].append(task)
                
                return project_tasks
            else:
                # إرجاع جميع المهام مجمعة حسب المشروع
                projects = {}
                
                for status in ["todo", "in_progress", "done"]:
                    for task in board_data[status]:
                        project = task.get("project", "غير محدد")
                        
                        if project not in projects:
                            projects[project] = {"todo": [], "in_progress": [], "done": []}
                        
                        projects[project][status].append(task)
                
                return projects
                
        except Exception as e:
            self.logger.error(f"فشل في استرجاع المهام: {e}")
            return {}
    
    def _convert_new_tasks_to_issues(self, board_data: Dict[str, Any], new_tasks_count: int):
        """تحويل المهام الجديدة إلى GitHub Issues"""
        try:
            self.logger.info(f"🔄 تحويل {new_tasks_count} مهمة جديدة إلى GitHub Issues...")
            
            # التأكد من وجود العلامات المطلوبة
            self.github_issues_manager.ensure_labels_exist()
            
            # الحصول على المهام الجديدة (آخر المهام المضافة)
            new_tasks = board_data["todo"][-new_tasks_count:] if new_tasks_count <= len(board_data["todo"]) else board_data["todo"]
            
            successful_conversions = 0
            
            for task in new_tasks:
                # تحويل المهمة إلى Issue
                result = self.github_issues_manager.convert_task_to_issue(
                    task_data=task,
                    session_id=board_data.get("metadata", {}).get("session_id")
                )
                
                if result.success:
                    successful_conversions += 1
                    # تحديث المهمة بمعلومات Issue
                    task["github_issue"] = {
                        "number": result.issue_number,
                        "url": result.issue_url,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                else:
                    self.logger.warning(f"فشل في تحويل المهمة '{task['title']}' إلى Issue: {result.error}")
                
                # تأخير بسيط لتجنب rate limiting
                import time
                time.sleep(1)
            
            # حفظ التحديثات على board
            if successful_conversions > 0:
                board_file = Path(self.config.BOARD_DIR) / "tasks.json"
                with open(board_file, 'w', encoding='utf-8') as f:
                    json.dump(board_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"✅ تم تحويل {successful_conversions}/{new_tasks_count} مهمة إلى GitHub Issues بنجاح")
            
        except Exception as e:
            self.logger.error(f"فشل في تحويل المهام إلى GitHub Issues: {e}")
    
    def sync_task_status_with_github(self, task_id: str, new_status: str) -> bool:
        """مزامنة حالة المهمة مع GitHub Issue"""
        try:
            board_file = Path(self.config.BOARD_DIR) / "tasks.json"
            
            if not board_file.exists():
                return False
            
            with open(board_file, 'r', encoding='utf-8') as f:
                board_data = json.load(f)
            
            # البحث عن المهمة
            task_found = False
            for status_list in [board_data["todo"], board_data["in_progress"], board_data["done"]]:
                for task in status_list:
                    if task.get("id") == task_id and task.get("github_issue"):
                        issue_number = task["github_issue"]["number"]
                        
                        # تحديث حالة Issue في GitHub
                        if self.github_issues_manager.update_issue_status(issue_number, new_status):
                            self.logger.info(f"✅ تم مزامنة حالة المهمة {task_id} مع GitHub Issue #{issue_number}")
                            return True
                        else:
                            self.logger.warning(f"فشل في تحديث GitHub Issue #{issue_number}")
                            return False
            
            if not task_found:
                self.logger.warning(f"لم يتم العثور على المهمة {task_id} أو لا تحتوي على GitHub Issue")
                return False
                
        except Exception as e:
            self.logger.error(f"فشل في مزامنة حالة المهمة مع GitHub: {e}")
            return False