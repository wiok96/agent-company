"""
مدير الوكلاء لنظام AACS V0
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from .base_agent import BaseAgent, SimpleAgent, AGENT_PROFILES, Message
from core.config import Config, AGENT_ROLES, VOTING_WEIGHTS
from core.logger import setup_logger, SecureLogger
from core.idea_generator import IdeaGenerator
from core.failure_library import FailureLibrary


class AgentManager:
    """مدير الوكلاء الأساسي"""
    
    def __init__(self, config: Config, memory_system=None, failure_library: FailureLibrary = None):
        self.config = config
        self.logger = SecureLogger(setup_logger("agent_manager"))
        self.agents: Dict[str, BaseAgent] = {}
        
        # تهيئة مولد الأفكار إذا كان نظام الذاكرة متوفر
        self.idea_generator = None
        if memory_system:
            self.idea_generator = IdeaGenerator(config, memory_system, failure_library)
        
        # تهيئة الوكلاء
        self._initialize_agents()
        
        # التحقق من صحة التهيئة
        self._validate_initialization()
    
    def _initialize_agents(self):
        """تهيئة جميع الوكلاء العشرة"""
        self.logger.info("🤖 بدء تهيئة الوكلاء...")
        
        for agent_id in AGENT_ROLES:
            if agent_id not in AGENT_PROFILES:
                raise ValueError(f"ملف الوكيل غير موجود: {agent_id}")
            
            profile = AGENT_PROFILES[agent_id]
            
            # تحديث وزن التصويت من التكوين
            if agent_id in VOTING_WEIGHTS:
                profile.voting_weight = VOTING_WEIGHTS[agent_id]
            
            # إنشاء الوكيل
            agent = SimpleAgent(profile, self._get_agent_templates(agent_id))
            
            # تعيين مولد الأفكار للرئيس التنفيذي
            if agent_id == "ceo" and self.idea_generator:
                agent.idea_generator = self.idea_generator
            
            self.agents[agent_id] = agent
            
            self.logger.info(f"✅ تم تهيئة الوكيل: {profile.name} ({agent_id})")
        
        self.logger.info(f"🎉 تم تهيئة {len(self.agents)} وكيل بنجاح")
    
    def _get_agent_templates(self, agent_id: str) -> Dict[str, List[str]]:
        """الحصول على قوالب الردود المخصصة لكل وكيل"""
        
        templates = {
            "ceo": {
                "project_proposal": [
                    "أقترح تطوير منصة ذكية لإدارة المشاريع التقنية باستخدام الذكاء الاصطناعي",
                    "أقترح إنشاء نظام تحليل البيانات الضخمة للشركات الناشئة",
                    "أقترح تطوير حل أمني متقدم للحماية من التهديدات السيبرانية",
                    "أقترح بناء منصة تعليمية تفاعلية للبرمجة والتقنية"
                ],
                "project_suggestion": [
                    "كرئيس تنفيذي، أرى فرصة كبيرة في تطوير حلول الذكاء الاصطناعي للشركات الصغيرة",
                    "أقترح التركيز على تقنيات البلوك تشين لحلول الأعمال",
                    "نحتاج لمشروع يجمع بين إنترنت الأشياء والتحليلات الذكية"
                ],
                "contribution": [
                    "من منظور استراتيجي، أرى أن هذا المشروع يتماشى مع رؤيتنا طويلة المدى",
                    "كرئيس تنفيذي، أؤكد على أهمية التركيز على القيمة المضافة للعملاء",
                    "يجب أن نضمن أن هذا القرار يخدم أهدافنا الاستراتيجية"
                ]
            },
            "cto": {
                "project_proposal": [
                    "أقترح تطوير إطار عمل مفتوح المصدر لتطبيقات الويب السريعة",
                    "أقترح بناء نظام إدارة قواعد البيانات الموزعة",
                    "أقترح إنشاء أداة تطوير متقدمة للتطبيقات السحابية",
                    "أقترح تطوير منصة DevOps متكاملة للفرق التقنية"
                ],
                "project_suggestion": [
                    "من الناحية التقنية، أرى حاجة ملحة لأدوات تطوير أكثر ذكاءً",
                    "أقترح التركيز على تقنيات الحوسبة السحابية المتقدمة",
                    "نحتاج لحلول تقنية تسهل عملية التطوير والنشر"
                ],
                "contribution": [
                    "من الناحية التقنية، يجب أن نضمن قابلية التوسع والأمان",
                    "أقترح استخدام تقنيات حديثة وموثوقة لضمان الاستقرار",
                    "يجب أن نخطط للبنية التحتية والأمان من البداية"
                ]
            },
            "developer": {
                "project_proposal": [
                    "أقترح تطوير مكتبة برمجية تبسط التعامل مع APIs المعقدة",
                    "أقترح بناء أداة تصحيح أخطاء متقدمة للتطبيقات الحديثة",
                    "أقترح إنشاء منصة لمشاركة وإعادة استخدام الكود البرمجي",
                    "أقترح تطوير IDE ذكي يستخدم الذكاء الاصطناعي"
                ],
                "project_suggestion": [
                    "كمطور، أرى حاجة لأدوات تسرع عملية التطوير وتقلل الأخطاء",
                    "أقترح التركيز على حلول تحسن تجربة المطورين",
                    "نحتاج لأدوات تساعد في كتابة كود أكثر جودة وأماناً"
                ],
                "contribution": [
                    "من ناحية التطوير، يمكنني البدء فوراً في بناء النموذج الأولي",
                    "أقترح استخدام تقنيات بسيطة وموثوقة لضمان سرعة التطوير",
                    "يجب أن نركز على كتابة كود نظيف وقابل للصيانة"
                ]
            },
            "pm": {
                "project_proposal": [
                    "أقترح تطوير منصة إدارة المشاريع التقنية مع تتبع ذكي للتقدم",
                    "أقترح بناء نظام إدارة الموارد والفرق التقنية",
                    "أقترح إنشاء أداة تخطيط وتقدير المشاريع البرمجية",
                    "أقترح تطوير منصة تعاون للفرق الموزعة"
                ],
                "project_suggestion": [
                    "كمدير مشاريع، أرى حاجة لأدوات تحسن التعاون والتنسيق",
                    "أقترح التركيز على حلول تسهل إدارة المشاريع المعقدة",
                    "نحتاج لأدوات تساعد في التخطيط والمتابعة الفعالة"
                ],
                "contribution": [
                    "من ناحية إدارة المشاريع، نحتاج لتحديد الجدول الزمني والموارد المطلوبة",
                    "يجب أن نقسم هذا المشروع إلى مراحل قابلة للإدارة والتتبع",
                    "أقترح وضع معايير واضحة لقياس نجاح المشروع"
                ]
            },
            "marketing": {
                "project_proposal": [
                    "أقترح تطوير منصة تسويق رقمي ذكية للشركات الصغيرة",
                    "أقترح بناء أداة تحليل وسائل التواصل الاجتماعي",
                    "أقترح إنشاء نظام إدارة علاقات العملاء المتقدم",
                    "أقترح تطوير منصة التجارة الإلكترونية الذكية"
                ],
                "project_suggestion": [
                    "من ناحية التسويق، أرى فرصة في حلول التسويق الرقمي المبتكرة",
                    "أقترح التركيز على أدوات تحليل سلوك العملاء",
                    "نحتاج لحلول تساعد الشركات في الوصول لعملائها بفعالية"
                ],
                "contribution": [
                    "من ناحية التسويق، يجب أن نفهم احتياجات السوق والعملاء المستهدفين",
                    "أقترح دراسة المنافسين وتحديد نقاط التميز لدينا",
                    "يجب أن نخطط لاستراتيجية تسويق فعالة منذ البداية"
                ]
            },
            "qa": {
                "evaluation": [
                    "من ناحية الجودة، هذا المشروع يحتاج لخطة اختبار شاملة ومعايير جودة صارمة",
                    "أرى أن المشروع قابل للتنفيذ لكن يحتاج لاستراتيجية اختبار متقدمة",
                    "من منظور ضمان الجودة، يجب التأكد من قابلية الاختبار والموثوقية"
                ],
                "contribution": [
                    "من ناحية الجودة، يجب أن نضع خطة اختبار شاملة من البداية",
                    "أقترح تطبيق معايير جودة صارمة لضمان موثوقية المنتج",
                    "يجب أن نختبر جميع السيناريوهات المحتملة قبل الإطلاق"
                ]
            },
            "finance": {
                "evaluation": [
                    "من الناحية المالية، هذا المشروع يحتاج لتحليل دقيق للتكاليف والعائد المتوقع",
                    "أرى إمكانية ربحية جيدة لكن يجب وضع ميزانية واضحة ومراقبة الإنفاق",
                    "من منظور مالي، المشروع واعد لكن يحتاج لدراسة جدوى مفصلة"
                ],
                "contribution": [
                    "من الناحية المالية، يجب أن نحسب التكاليف والعائد المتوقع بدقة",
                    "أقترح وضع ميزانية واضحة ومراقبة الإنفاق بانتظام",
                    "يجب أن نضمن أن المشروع مربح ومستدام مالياً"
                ]
            },
            "critic": {
                "evaluation": [
                    "يجب أن نكون حذرين من المخاطر المحتملة - هل درسنا المنافسة والتحديات التقنية؟",
                    "أرى مخاطر في التنفيذ والسوق - نحتاج لخطة للتعامل مع السيناريوهات السلبية",
                    "المشروع طموح لكن هل لدينا الخبرة والموارد الكافية لتنفيذه بنجاح؟"
                ],
                "contribution": [
                    "يجب أن نكون حذرين من المخاطر المحتملة وننظر في السيناريوهات السلبية",
                    "أقترح مراجعة دقيقة لجميع الافتراضات قبل اتخاذ القرار",
                    "يجب أن نسأل الأسئلة الصعبة ونتحدى الافتراضات"
                ],
                "vote": [
                    "محايد - أحتاج المزيد من المعلومات",
                    "موافق بشروط - مع وضع خطة للمخاطر",
                    "غير موافق - المخاطر عالية جداً",
                    "أحتاج المزيد من المعلومات حول التكاليف"
                ]
            },
            "memory": {
                "evaluation": [
                    "بناءً على تجاربنا السابقة، مشاريع مماثلة واجهت تحديات في التسويق والتبني",
                    "أذكركم بأن المشروع السابق المشابه نجح بسبب التركيز على البساطة",
                    "من خبرتنا السابقة، هذا النوع من المشاريع يحتاج لصبر ومثابرة في التطوير"
                ],
                "contribution": [
                    "بناءً على تجاربنا السابقة، هذا النوع من المشاريع كان ناجحاً",
                    "أذكركم بأننا واجهنا تحديات مماثلة في المشروع السابق",
                    "لدينا خبرة جيدة في هذا المجال من المشاريع السابقة"
                ]
            },
            "chair": {
                "contribution": [
                    "دعونا نركز على النقاط الأساسية ونتخذ قرارات واضحة",
                    "أقترح أن نستمع لجميع وجهات النظر قبل التصويت",
                    "يجب أن نضمن أن جميع الأعضاء لديهم فرصة للمساهمة"
                ]
            }
        }
        
        # إرجاع القوالب المخصصة أو الافتراضية
        return templates.get(agent_id, {})
    
    def _validate_initialization(self):
        """التحقق من صحة تهيئة الوكلاء"""
        # التحقق من العدد الصحيح
        if len(self.agents) != 10:
            raise ValueError(f"يجب أن يكون عدد الوكلاء 10 بالضبط، الحالي: {len(self.agents)}")
        
        # التحقق من وجود جميع الأدوار المطلوبة
        missing_roles = set(AGENT_ROLES) - set(self.agents.keys())
        if missing_roles:
            raise ValueError(f"أدوار مفقودة: {missing_roles}")
        
        # التحقق من أوزان التصويت
        voting_agents = [agent_id for agent_id in self.agents.keys() if VOTING_WEIGHTS[agent_id] > 0]
        if len(voting_agents) < self.config.MIN_VOTING_PARTICIPANTS:
            raise ValueError(f"عدد الوكلاء المصوتين أقل من الحد الأدنى: {len(voting_agents)} < {self.config.MIN_VOTING_PARTICIPANTS}")
        
        self.logger.info("✅ تم التحقق من صحة تهيئة الوكلاء")
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """الحصول على وكيل محدد"""
        return self.agents.get(agent_id)
    
    def get_all_agents(self) -> Dict[str, BaseAgent]:
        """الحصول على جميع الوكلاء"""
        return self.agents.copy()
    
    def get_voting_agents(self) -> Dict[str, BaseAgent]:
        """الحصول على الوكلاء المصوتين فقط"""
        return {
            agent_id: agent for agent_id, agent in self.agents.items()
            if VOTING_WEIGHTS[agent_id] > 0
        }
    
    def conduct_discussion(self, topic: str, context: Dict[str, Any]) -> List[Message]:
        """إجراء مناقشة حول موضوع معين"""
        messages = []
        
        # رسالة الافتتاح من رئيس الاجتماع
        chair_message = self._generate_agent_message("chair", context, f"نبدأ مناقشة: {topic}")
        messages.append(chair_message)
        
        # مساهمات من الوكلاء الآخرين
        for agent_id in AGENT_ROLES:
            if agent_id == "chair":  # تم بالفعل
                continue
            
            agent_context = context.copy()
            agent_context["topic"] = topic
            agent_context["previous_messages"] = messages
            agent_context["expected_response_type"] = "contribution"
            
            message = self._generate_agent_message(agent_id, agent_context, f"ما رأيك في: {topic}")
            messages.append(message)
        
        return messages
    
    def conduct_voting(self, proposal: Dict[str, Any]) -> Dict[str, str]:
        """إجراء تصويت على اقتراح"""
        votes = {}
        voting_agents = self.get_voting_agents()
        
        self.logger.info(f"🗳️ بدء التصويت على: {proposal.get('title', 'اقتراح')}")
        
        for agent_id, agent in voting_agents.items():
            vote = agent.vote_on_proposal(proposal)
            votes[agent_id] = vote
            self.logger.info(f"  {agent.profile.name}: {vote}")
        
        return votes
    
    def calculate_voting_result(self, votes: Dict[str, str]) -> Dict[str, Any]:
        """حساب نتيجة التصويت مع إنفاذ النصاب القانوني"""
        
        # التحقق من النصاب القانوني أولاً (7/10 وكلاء كحد أدنى)
        voting_agents_count = len([agent_id for agent_id in votes.keys() if VOTING_WEIGHTS[agent_id] > 0])
        
        if voting_agents_count < self.config.MIN_VOTING_PARTICIPANTS:
            return {
                "outcome": "failed_quorum",
                "failure_reason": f"عدد المصوتين ({voting_agents_count}) أقل من النصاب القانوني المطلوب ({self.config.MIN_VOTING_PARTICIPANTS})",
                "total_votes": len(votes),
                "voting_agents_count": voting_agents_count,
                "required_quorum": self.config.MIN_VOTING_PARTICIPANTS,
                "vote_breakdown": {},
                "approval_percentage": 0,
                "total_weight": 0,
                "positive_weight": 0
            }
        
        # حساب الأوزان (فقط بعد اجتياز النصاب القانوني)
        total_weight = 0
        positive_weight = 0
        
        vote_counts = {}
        
        for agent_id, vote in votes.items():
            weight = VOTING_WEIGHTS[agent_id]
            total_weight += weight
            
            # تصنيف الأصوات
            if vote in ["موافق", "موافق بشروط"]:
                positive_weight += weight
            
            vote_counts[vote] = vote_counts.get(vote, 0) + 1
        
        # تحديد النتيجة
        approval_percentage = (positive_weight / total_weight) * 100 if total_weight > 0 else 0
        
        # يحتاج 60% للموافقة
        outcome = "approved" if approval_percentage >= 60 else "rejected"
        
        return {
            "outcome": outcome,
            "approval_percentage": approval_percentage,
            "total_votes": len(votes),
            "voting_agents_count": voting_agents_count,
            "required_quorum": self.config.MIN_VOTING_PARTICIPANTS,
            "vote_breakdown": vote_counts,
            "total_weight": total_weight,
            "positive_weight": positive_weight
        }
    
    def _generate_agent_message(self, agent_id: str, context: Dict[str, Any], prompt: str) -> Message:
        """توليد رسالة من وكيل محدد"""
        agent = self.agents[agent_id]
        content = agent.generate_response(context, prompt)
        
        message = Message(
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_id=agent_id,
            content=content,
            message_type=context.get("expected_response_type", "contribution"),
            metadata={"agent_name": agent.profile.name}
        )
        
        # إضافة الرسالة لتاريخ الوكيل
        agent.add_message(message)
        
        return message
    
    def reset_all_agents(self):
        """إعادة تعيين جميع الوكلاء للاجتماع الجديد"""
        for agent in self.agents.values():
            agent.reset_conversation()
        
        self.logger.info("🔄 تم إعادة تعيين جميع الوكلاء")
    
    def generate_all_self_reflections(self, meeting_summary: Dict[str, Any]) -> Dict[str, str]:
        """توليد تقارير المراجعة الذاتية لجميع الوكلاء"""
        reflections = {}
        
        for agent_id, agent in self.agents.items():
            reflection = agent.generate_self_reflection(meeting_summary)
            reflections[agent_id] = reflection
        
        self.logger.info(f"📝 تم توليد {len(reflections)} تقرير مراجعة ذاتية")
        
        return reflections
    
    def get_agent_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات الوكلاء"""
        stats = {
            "total_agents": len(self.agents),
            "voting_agents": len(self.get_voting_agents()),
            "agent_details": {}
        }
        
        for agent_id, agent in self.agents.items():
            stats["agent_details"][agent_id] = {
                "name": agent.profile.name,
                "role": agent.profile.role,
                "voting_weight": agent.get_voting_weight(),
                "reputation_score": agent.profile.reputation_score,
                "expertise_areas": agent.profile.expertise_areas
            }
        
        return stats
    
    def generate_project_idea(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """توليد فكرة مشروع جديدة من الرئيس التنفيذي"""
        ceo_agent = self.get_agent("ceo")
        
        if not ceo_agent:
            raise ValueError("الرئيس التنفيذي غير موجود")
        
        if not hasattr(ceo_agent, 'generate_project_idea'):
            raise ValueError("مولد الأفكار غير متوفر للرئيس التنفيذي")
        
        return ceo_agent.generate_project_idea(context)
    
    def get_idea_generator_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات مولد الأفكار"""
        if not self.idea_generator:
            return {"error": "مولد الأفكار غير مُهيأ"}
        
        return self.idea_generator.get_template_statistics()