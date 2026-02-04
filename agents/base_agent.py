"""
الوكيل الأساسي لنظام AACS V0
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone


@dataclass
class AgentProfile:
    """ملف الوكيل الشخصي"""
    id: str
    name: str
    role: str
    expertise_areas: List[str]
    personality_traits: List[str]
    voting_weight: float
    reputation_score: float = 1.0


@dataclass
class Message:
    """رسالة في الاجتماع"""
    timestamp: str
    agent_id: str
    content: str
    message_type: str  # contribution, proposal, vote, question, etc.
    metadata: Dict[str, Any] = None


class BaseAgent(ABC):
    """الفئة الأساسية لجميع الوكلاء"""
    
    def __init__(self, profile: AgentProfile):
        self.profile = profile
        self.conversation_history: List[Message] = []
        self.current_meeting_context: Dict[str, Any] = {}
    
    @abstractmethod
    def generate_response(self, context: Dict[str, Any], prompt: str) -> str:
        """توليد رد على السياق والمطالبة المعطاة"""
        pass
    
    @abstractmethod
    def vote_on_proposal(self, proposal: Dict[str, Any]) -> str:
        """التصويت على اقتراح معين"""
        pass
    
    def add_message(self, message: Message):
        """إضافة رسالة لتاريخ المحادثة"""
        self.conversation_history.append(message)
    
    def get_recent_context(self, limit: int = 10) -> List[Message]:
        """الحصول على السياق الأخير من المحادثة"""
        return self.conversation_history[-limit:]
    
    def reset_conversation(self):
        """إعادة تعيين تاريخ المحادثة"""
        self.conversation_history = []
        self.current_meeting_context = {}
    
    def update_reputation(self, score_change: float):
        """تحديث درجة السمعة"""
        self.profile.reputation_score = max(0.1, self.profile.reputation_score + score_change)
    
    def get_voting_weight(self) -> float:
        """الحصول على وزن التصويت الحالي"""
        # الوزن الأساسي مضروب في درجة السمعة
        return self.profile.voting_weight * self.profile.reputation_score
    
    def generate_self_reflection(self, meeting_summary: Dict[str, Any]) -> str:
        """توليد تقرير المراجعة الذاتية"""
        # تنفيذ أساسي - يمكن تخصيصه في الفئات المشتقة
        return f"""# تقرير المراجعة الذاتية - {self.profile.name}

## معلومات الاجتماع
- **معرف الجلسة**: {meeting_summary.get('session_id', 'غير محدد')}
- **التاريخ**: {meeting_summary.get('timestamp', 'غير محدد')}
- **دوري**: {self.profile.role}

## التقييم الذاتي

### ما نجح ✅
شاركت في الاجتماع وقدمت مساهمات في مجال تخصصي.

### ما فشل ❌
يمكنني تحسين جودة مساهماتي وتقديم المزيد من التفاصيل.

### خطة التحسين 🔄
سأركز على تطوير خبرتي في {', '.join(self.profile.expertise_areas)}.

## إحصائيات الأداء
- **عدد المساهمات**: {len([m for m in self.conversation_history if m.agent_id == self.profile.id])}
- **درجة السمعة الحالية**: {self.profile.reputation_score:.2f}
- **وزن التصويت**: {self.get_voting_weight():.2f}

---
*تم إنتاج هذا التقرير في {datetime.now(timezone.utc).isoformat()}*
"""


class SimpleAgent(BaseAgent):
    """وكيل بسيط للنسخة V0"""
    
    def __init__(self, profile: AgentProfile, response_templates: Dict[str, List[str]] = None):
        super().__init__(profile)
        self.response_templates = response_templates or self._get_default_templates()
    
    def _get_default_templates(self) -> Dict[str, List[str]]:
        """قوالب الردود الافتراضية"""
        return {
            "contribution": [
                f"من وجهة نظر {self.profile.role}، أعتقد أن هذا الموضوع مهم.",
                f"بناءً على خبرتي في {', '.join(self.profile.expertise_areas)}، أقترح التركيز على الجودة.",
                f"كـ{self.profile.role}، أرى أن هناك فرصة جيدة هنا."
            ],
            "proposal": [
                f"أقترح أن نبدأ بمشروع بسيط في مجال {self.profile.expertise_areas[0] if self.profile.expertise_areas else 'التطوير'}.",
                "أعتقد أننا يجب أن نركز على المشاريع ذات العائد السريع.",
                "أقترح تقسيم هذا المشروع إلى مراحل أصغر."
            ],
            "vote": [
                "موافق",
                "موافق بشروط", 
                "محايد",
                "غير موافق",
                "أحتاج المزيد من المعلومات"
            ]
        }
    
    def generate_response(self, context: Dict[str, Any], prompt: str) -> str:
        """توليد رد بسيط بناءً على القوالب"""
        import random
        
        # تحديد نوع الرد بناءً على السياق
        response_type = context.get('expected_response_type', 'contribution')
        
        if response_type in self.response_templates:
            templates = self.response_templates[response_type]
            return random.choice(templates)
        
        # رد افتراضي
        return f"كـ{self.profile.role}، أقدر هذه المناقشة وأدعم القرارات المدروسة."
    
    def vote_on_proposal(self, proposal: Dict[str, Any]) -> str:
        """التصويت على اقتراح"""
        import random
        
        # منطق تصويت بسيط بناءً على دور الوكيل
        if self.profile.id == "critic":
            # الناقد أكثر حذراً
            return random.choice(["محايد", "موافق بشروط", "أحتاج المزيد من المعلومات"])
        elif self.profile.id in ["ceo", "pm"]:
            # القيادة أكثر حسماً
            return random.choice(["موافق", "موافق بشروط", "موافق"])
        else:
            # باقي الوكلاء
            return random.choice(["موافق", "موافق", "محايد", "موافق بشروط"])


# تعريف ملفات الوكلاء العشرة
AGENT_PROFILES = {
    "ceo": AgentProfile(
        id="ceo",
        name="الرئيس التنفيذي",
        role="CEO",
        expertise_areas=["الاستراتيجية", "القيادة", "الرؤية"],
        personality_traits=["حاسم", "استراتيجي", "ملهم"],
        voting_weight=1.5
    ),
    "pm": AgentProfile(
        id="pm",
        name="مدير المشاريع",
        role="Project Manager",
        expertise_areas=["إدارة المشاريع", "التخطيط", "التنسيق"],
        personality_traits=["منظم", "عملي", "متواصل"],
        voting_weight=1.3
    ),
    "cto": AgentProfile(
        id="cto",
        name="المدير التقني",
        role="CTO",
        expertise_areas=["التكنولوجيا", "الهندسة", "الأمان"],
        personality_traits=["تقني", "مبتكر", "حذر"],
        voting_weight=1.3
    ),
    "developer": AgentProfile(
        id="developer",
        name="المطور",
        role="Developer",
        expertise_areas=["البرمجة", "التطوير", "التنفيذ"],
        personality_traits=["عملي", "مبدع", "مفصل"],
        voting_weight=1.2
    ),
    "qa": AgentProfile(
        id="qa",
        name="ضمان الجودة",
        role="QA Engineer",
        expertise_areas=["الاختبار", "الجودة", "التحقق"],
        personality_traits=["دقيق", "منهجي", "صبور"],
        voting_weight=1.1
    ),
    "marketing": AgentProfile(
        id="marketing",
        name="مختص التسويق",
        role="Marketing Specialist",
        expertise_areas=["التسويق", "السوق", "العملاء"],
        personality_traits=["إبداعي", "تحليلي", "متفائل"],
        voting_weight=1.0
    ),
    "finance": AgentProfile(
        id="finance",
        name="المحلل المالي",
        role="Financial Analyst",
        expertise_areas=["المالية", "ROI", "التكاليف"],
        personality_traits=["تحليلي", "حذر", "دقيق"],
        voting_weight=1.2
    ),
    "critic": AgentProfile(
        id="critic",
        name="الناقد",
        role="Critic",
        expertise_areas=["التحليل النقدي", "تقييم المخاطر", "المراجعة"],
        personality_traits=["نقدي", "موضوعي", "صريح"],
        voting_weight=1.1
    ),
    "chair": AgentProfile(
        id="chair",
        name="رئيس الاجتماع",
        role="Meeting Chair",
        expertise_areas=["إدارة الاجتماعات", "التنسيق", "اتخاذ القرارات"],
        personality_traits=["منظم", "عادل", "حاسم"],
        voting_weight=1.0
    ),
    "memory": AgentProfile(
        id="memory",
        name="مدير الذاكرة",
        role="Memory Manager",
        expertise_areas=["إدارة المعرفة", "الأرشفة", "الاسترجاع"],
        personality_traits=["منظم", "شامل", "موثوق"],
        voting_weight=0.0  # لا يصوت - استشاري فقط
    )
}