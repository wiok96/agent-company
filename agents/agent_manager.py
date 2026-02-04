"""
مدير الوكلاء لنظام AACS V0
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from .base_agent import BaseAgent, SimpleAgent, AGENT_PROFILES, Message
from core.config import Config, AGENT_ROLES, VOTING_WEIGHTS
from core.logger import setup_logger, SecureLogger


class AgentManager:
    """مدير الوكلاء الأساسي"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = SecureLogger(setup_logger("agent_manager"))
        self.agents: Dict[str, BaseAgent] = {}
        
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
            self.agents[agent_id] = agent
            
            self.logger.info(f"✅ تم تهيئة الوكيل: {profile.name} ({agent_id})")
        
        self.logger.info(f"🎉 تم تهيئة {len(self.agents)} وكيل بنجاح")
    
    def _get_agent_templates(self, agent_id: str) -> Dict[str, List[str]]:
        """الحصول على قوالب الردود المخصصة لكل وكيل"""
        
        templates = {
            "ceo": {
                "contribution": [
                    "من منظور استراتيجي، أرى أن هذا المشروع يتماشى مع رؤيتنا طويلة المدى",
                    "كرئيس تنفيذي، أؤكد على أهمية التركيز على القيمة المضافة للعملاء",
                    "يجب أن نضمن أن هذا القرار يخدم أهدافنا الاستراتيجية"
                ],
                "proposal": [
                    "أقترح أن نبدأ بمشروع يحقق عائد استثمار سريع ويعزز موقعنا في السوق",
                    "أعتقد أننا بحاجة لمشروع يظهر قدراتنا التقنية والإبداعية",
                    "أقترح التركيز على مشروع يحل مشكلة حقيقية في السوق"
                ]
            },
            "pm": {
                "contribution": [
                    "من ناحية إدارة المشاريع، نحتاج لتحديد الجدول الزمني والموارد المطلوبة",
                    "يجب أن نقسم هذا المشروع إلى مراحل قابلة للإدارة والتتبع",
                    "أقترح وضع معايير واضحة لقياس نجاح المشروع"
                ],
                "proposal": [
                    "أقترح إنشاء أداة بسيطة لإدارة المهام تساعد الفرق الصغيرة",
                    "يمكننا تطوير تطبيق ويب بسيط لتتبع المشاريع",
                    "أقترح بناء نظام إشعارات ذكي للمهام المهمة"
                ]
            },
            "cto": {
                "contribution": [
                    "من الناحية التقنية، يجب أن نضمن قابلية التوسع والأمان",
                    "أقترح استخدام تقنيات حديثة وموثوقة لضمان الاستقرار",
                    "يجب أن نخطط للبنية التحتية والأمان من البداية"
                ],
                "proposal": [
                    "أقترح تطوير API بسيط يمكن للمطورين الآخرين استخدامه",
                    "يمكننا بناء أداة تطوير تساعد في أتمتة المهام المتكررة",
                    "أقترح إنشاء مكتبة مفتوحة المصدر تحل مشكلة شائعة"
                ]
            },
            "developer": {
                "contribution": [
                    "من ناحية التطوير، يمكنني البدء فوراً في بناء النموذج الأولي",
                    "أقترح استخدام تقنيات بسيطة وموثوقة لضمان سرعة التطوير",
                    "يجب أن نركز على كتابة كود نظيف وقابل للصيانة"
                ],
                "proposal": [
                    "أقترح بناء تطبيق ويب بسيط باستخدام Python و HTML",
                    "يمكننا تطوير أداة سطر أوامر مفيدة للمطورين",
                    "أقترح إنشاء إضافة بسيطة للمتصفح تحل مشكلة يومية"
                ]
            },
            "qa": {
                "contribution": [
                    "من ناحية الجودة، يجب أن نضع خطة اختبار شاملة من البداية",
                    "أقترح تطبيق معايير جودة صارمة لضمان موثوقية المنتج",
                    "يجب أن نختبر جميع السيناريوهات المحتملة قبل الإطلاق"
                ],
                "proposal": [
                    "أقترح بناء أداة اختبار تلقائي تساعد المطورين",
                    "يمكننا تطوير نظام مراقبة جودة للتطبيقات",
                    "أقترح إنشاء مكتبة اختبار تبسط عملية كتابة الاختبارات"
                ]
            },
            "marketing": {
                "contribution": [
                    "من ناحية التسويق، يجب أن نفهم احتياجات السوق والعملاء المستهدفين",
                    "أقترح دراسة المنافسين وتحديد نقاط التميز لدينا",
                    "يجب أن نخطط لاستراتيجية تسويق فعالة منذ البداية"
                ],
                "proposal": [
                    "أقترح تطوير أداة تساعد في إدارة وسائل التواصل الاجتماعي",
                    "يمكننا بناء منصة بسيطة لإنشاء المحتوى التسويقي",
                    "أقترح إنشاء أداة تحليل بسيطة لمواقع الويب"
                ]
            },
            "finance": {
                "contribution": [
                    "من الناحية المالية، يجب أن نحسب التكاليف والعائد المتوقع بدقة",
                    "أقترح وضع ميزانية واضحة ومراقبة الإنفاق بانتظام",
                    "يجب أن نضمن أن المشروع مربح ومستدام مالياً"
                ],
                "proposal": [
                    "أقترح تطوير أداة بسيطة لإدارة الميزانيات الشخصية",
                    "يمكننا بناء حاسبة ROI تساعد في تقييم المشاريع",
                    "أقترح إنشاء أداة تتبع المصروفات للشركات الصغيرة"
                ]
            },
            "critic": {
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
            "chair": {
                "contribution": [
                    "دعونا نركز على النقاط الأساسية ونتخذ قرارات واضحة",
                    "أقترح أن نستمع لجميع وجهات النظر قبل التصويت",
                    "يجب أن نضمن أن جميع الأعضاء لديهم فرصة للمساهمة"
                ],
                "proposal": [
                    "أقترح أن نصوت على هذا الاقتراح بعد مناقشة شاملة",
                    "دعونا نحدد الخطوات التالية بوضوح",
                    "أقترح تشكيل فريق عمل لتنفيذ هذا المشروع"
                ]
            },
            "memory": {
                "contribution": [
                    "بناءً على تجاربنا السابقة، هذا النوع من المشاريع كان ناجحاً",
                    "أذكركم بأننا واجهنا تحديات مماثلة في المشروع السابق",
                    "لدينا خبرة جيدة في هذا المجال من المشاريع السابقة"
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
        """حساب نتيجة التصويت"""
        # حساب الأوزان
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