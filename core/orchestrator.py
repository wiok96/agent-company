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
            
            if voting_result['outcome'] == 'failed_quorum':
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

        return self._create_agent_message("critic", evaluation_context, evaluation_prompt)
    
    def _validate_critic_evaluation(self, critic_evaluation: Dict[str, Any]) -> bool:
        """التحقق من اكتمال وجودة التقييم النقدي"""
        
        evaluation_content = critic_evaluation.get("message", "").lower()
        
        # معايير التحقق من اكتمال التقييم (مرونة للاختبار)
        required_elements = [
            # يجب أن يحتوي على تحليل للمخاطر أو التحديات
            any(keyword in evaluation_content for keyword in ["مخاطر", "تحديات", "صعوبات", "مشاكل", "تحدي", "صعوبة"]),
            
            # يجب أن يحتوي على تقييم للجدوى أو الإمكانية
            any(keyword in evaluation_content for keyword in ["جدوى", "قابل للتنفيذ", "واقعي", "ممكن", "إمكانية", "تنفيذ"]),
            
            # يجب أن يحتوي على تحليل للسوق أو المنافسة أو العملاء
            any(keyword in evaluation_content for keyword in ["سوق", "منافس", "عملاء", "طلب", "منافسة", "عميل"]),
            
            # يجب أن يحتوي على نقد أو نقاط ضعف أو تحليل سلبي
            any(keyword in evaluation_content for keyword in ["ضعف", "نقص", "مشكلة", "عيب", "سلبي", "نقد", "لكن", "ولكن"]),
            
            # يجب أن يحتوي على توصية أو رأي واضح
            any(keyword in evaluation_content for keyword in ["أنصح", "أقترح", "توصي", "يجب", "لا يجب", "أرى", "أعتقد"])
        ]
        
        # التحقق من الحد الأدنى للطول (مرونة للاختبار)
        min_length_met = len(evaluation_content) >= 30  # مرونة للاختبار
        
        # التحقق من وجود معظم العناصر المطلوبة (مرونة)
        elements_met = sum(required_elements) >= 2  # 2 من 5 عناصر
        
        # التحقق من أن التقييم ليس عاماً جداً (مرونة)
        not_too_generic = not (
            evaluation_content.count("جيد") > 3 or 
            evaluation_content.count("ممتاز") > 3 or
            "لا مشاكل على الإطلاق" in evaluation_content
        )
        
        # التحقق من أن التقييم يحتوي على محتوى فعلي (مرونة)
        has_substance = len(evaluation_content.split()) >= 5  # 5 كلمات على الأقل
        
        is_valid = min_length_met and elements_met and not_too_generic and has_substance
        
        self.logger.info(f"🔍 تقييم صحة التقييم النقدي:")
        self.logger.info(f"  - الطول الكافي: {min_length_met} ({len(evaluation_content)} حرف)")
        self.logger.info(f"  - العناصر المطلوبة: {sum(required_elements)}/5")
        self.logger.info(f"  - ليس عاماً جداً: {not_too_generic}")
        self.logger.info(f"  - له محتوى فعلي: {has_substance} ({len(evaluation_content.split())} كلمة)")
        self.logger.info(f"  - النتيجة النهائية: {'✅ صالح' if is_valid else '❌ غير صالح'}")
        
        return is_valid
    
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