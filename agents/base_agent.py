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
        """توليد تقرير المراجعة الذاتية باستخدام النظام المحسن"""
        
        # محاولة استخدام النظام المحسن إذا كان متوفراً
        try:
            from core.self_reflection_system import SelfReflectionSystem
            from core.memory import MemorySystem
            from core.config import Config
            
            config = Config()
            memory_system = MemorySystem(config)
            reflection_system = SelfReflectionSystem(config, memory_system)
            
            return reflection_system.generate_enhanced_reflection(
                self.profile.id, 
                self.profile, 
                meeting_summary, 
                self.conversation_history
            )
            
        except Exception as e:
            # في حالة فشل النظام المحسن، استخدم النظام الأساسي
            return self._generate_basic_reflection(meeting_summary)
    
    def _generate_basic_reflection(self, meeting_summary: Dict[str, Any]) -> str:
        """توليد مراجعة ذاتية أساسية (نسخة احتياطية)"""
        
        # حساب المساهمات الصحيح
        my_contributions = len([m for m in self.conversation_history if m.agent_id == self.profile.id])
        
        # محاولة استخدام الذكاء الاصطناعي أولاً
        try:
            context = {
                "meeting_phase": "self_reflection",
                "meeting_summary": meeting_summary,
                "my_contributions": my_contributions
            }
            
            prompt = f"""اكتب تقرير مراجعة ذاتية مفصل لأدائك في الاجتماع.
            
معلومات الاجتماع:
- معرف الجلسة: {meeting_summary.get('session_id', 'غير محدد')}
- الأجندة: {meeting_summary.get('agenda', 'غير محدد')}
- عدد مساهماتك: {my_contributions}

اكتب التقرير بصيغة markdown مع الأقسام التالية:
- ما نجح ✅
- ما فشل ❌  
- خطة التحسين 🔄
- ملاحظات إضافية

كن صادقاً وبناءً في تقييمك."""

            ai_reflection = self._generate_ai_response(context, prompt)
            
            # تنسيق التقرير النهائي
            return f"""# تقرير المراجعة الذاتية - {self.profile.name}

## معلومات الاجتماع
- **معرف الجلسة**: {meeting_summary.get('session_id', 'غير محدد')}
- **التاريخ**: {meeting_summary.get('timestamp', 'غير محدد')}
- **دوري**: {self.profile.role}

## التقييم الذاتي

{ai_reflection}

## إحصائيات الأداء
- **عدد المساهمات**: {my_contributions}
- **درجة السمعة الحالية**: {self.profile.reputation_score:.2f}
- **وزن التصويت**: {self.get_voting_weight():.2f}

---
*تم إنتاج هذا التقرير في {datetime.now(timezone.utc).isoformat()}*
"""
            
        except Exception as e:
            # في حالة فشل الـ AI، استخدم القالب الافتراضي
            return f"""# تقرير المراجعة الذاتية - {self.profile.name}

## معلومات الاجتماع
- **معرف الجلسة**: {meeting_summary.get('session_id', 'غير محدد')}
- **التاريخ**: {meeting_summary.get('timestamp', 'غير محدد')}
- **دوري**: {self.profile.role}

## التقييم الذاتي

### ما نجح ✅
شاركت في الاجتماع وقدمت مساهمات في مجال تخصصي ({', '.join(self.profile.expertise_areas)}).

### ما فشل ❌
يمكنني تحسين جودة مساهماتي وتقديم المزيد من التفاصيل التقنية.

### خطة التحسين 🔄
سأركز على تطوير خبرتي في {', '.join(self.profile.expertise_areas)} وتحسين التواصل مع الفريق.

## إحصائيات الأداء
- **عدد المساهمات**: {my_contributions}
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
        self.idea_generator = None  # سيتم تعيينه من المدير
    
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
        """توليد رد ذكي باستخدام الذكاء الاصطناعي"""
        try:
            # استخدام الذكاء الاصطناعي لتوليد رد طبيعي ومتنوع
            return self._generate_ai_response(context, prompt)
        except Exception as e:
            # في حالة فشل الـ AI، استخدم القوالب كبديل
            import random
            response_type = context.get('expected_response_type', 'contribution')
            
            if response_type in self.response_templates:
                templates = self.response_templates[response_type]
                return random.choice(templates)
            
            return f"كـ{self.profile.role}، أقدر هذه المناقشة وأدعم القرارات المدروسة."
    
    def _generate_ai_response(self, context: Dict[str, Any], prompt: str) -> str:
        """توليد رد باستخدام الذكاء الاصطناعي"""
        import os
        import requests
        import json
        
        # الحصول على مفتاح API
        api_key = os.getenv('AI_API_KEY')
        if not api_key or api_key == 'dummy_token_for_local_testing':
            raise Exception("No valid AI API key")
        
        # بناء السياق للوكيل
        agent_context = self._build_agent_context(context, prompt)
        
        try:
            # استدعاء Groq API
            response = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'llama-3.1-8b-instant',
                    'messages': [
                        {
                            'role': 'system',
                            'content': agent_context
                        },
                        {
                            'role': 'user', 
                            'content': prompt
                        }
                    ],
                    'max_tokens': 300,
                    'temperature': 0.9,
                    'top_p': 0.9,
                    'frequency_penalty': 0.5,
                    'presence_penalty': 0.3
                },
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content'].strip()
                
                # تنظيف الرد وإزالة التكرار
                ai_response = self._clean_ai_response(ai_response, context)
                return ai_response
            else:
                error_msg = f"API call failed: {response.status_code}"
                if response.text:
                    error_msg += f" - {response.text}"
                
                # محاولة إرسال إشعار فشل API (إذا كان متوفراً)
                self._notify_ai_api_failure(error_msg, context)
                
                raise Exception(error_msg)
                
        except requests.exceptions.Timeout:
            error_msg = "API request timeout"
            self._notify_ai_api_failure(error_msg, context)
            raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {str(e)}"
            self._notify_ai_api_failure(error_msg, context)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"AI response generation failed: {str(e)}"
            self._notify_ai_api_failure(error_msg, context)
            raise Exception(error_msg)
    
    def _notify_ai_api_failure(self, error_msg: str, context: Dict[str, Any]):
        """إشعار فشل API الذكاء الاصطناعي (إذا كان متوفراً)"""
        try:
            # محاولة الحصول على مدير الإشعارات من السياق العام
            session_id = context.get('session_id', 'unknown')
            
            # هذا سيعمل فقط إذا كان مدير الإشعارات متوفراً في النظام
            from core.config import Config
            from core.notification_manager import NotificationManager
            
            config = Config()
            notification_manager = NotificationManager(config)
            notification_manager.notify_ai_api_failure(session_id, error_msg)
            
        except Exception:
            # تجاهل أخطاء الإشعارات لتجنب تعطيل النظام
            pass
    
    def _clean_ai_response(self, response: str, context: Dict[str, Any]) -> str:
        """تنظيف وتحسين رد الذكاء الاصطناعي"""
        # إزالة الأسطر الفارغة الزائدة
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        
        # إزالة التكرار في بداية الرد
        common_prefixes = [
            f"كـ{self.profile.role}",
            f"من منظور {self.profile.role}",
            f"بصفتي {self.profile.role}",
            "أعتقد أن",
            "أرى أن",
            "من وجهة نظري"
        ]
        
        cleaned_lines = []
        for line in lines:
            # تجنب التكرار المفرط للبادئات
            if len(cleaned_lines) == 0 or not any(line.startswith(prefix) for prefix in common_prefixes if any(prev_line.startswith(prefix) for prev_line in cleaned_lines)):
                cleaned_lines.append(line)
        
        # دمج الأسطر وتحديد الطول
        result = ' '.join(cleaned_lines)
        
        # تحديد الطول الأقصى حسب نوع المساهمة
        meeting_phase = context.get('meeting_phase', 'general')
        if meeting_phase in ['project_proposal', 'proposal_defense']:
            max_length = 400
        elif meeting_phase in ['project_evaluation', 'vote_justification']:
            max_length = 250
        else:
            max_length = 150
        
        if len(result) > max_length:
            # قطع النص عند آخر جملة كاملة
            sentences = result.split('.')
            truncated = ""
            for sentence in sentences:
                if len(truncated + sentence + '.') <= max_length:
                    truncated += sentence + '.'
                else:
                    break
            result = truncated.strip()
        
        return result if result else "أشارك في هذه المناقشة المهمة."
    
    def _build_agent_context(self, context: Dict[str, Any], prompt: str) -> str:
        """بناء السياق للوكيل للحصول على ردود طبيعية ومتنوعة"""
        
        # معلومات الوكيل الأساسية
        agent_info = f"""أنت {self.profile.name} في شركة هايتك للحلول التقنية المبتكرة.
دورك: {self.profile.role}
مجالات خبرتك: {', '.join(self.profile.expertise_areas)}
صفاتك الشخصية: {', '.join(self.profile.personality_traits)}

شركة هايتك متخصصة في تطوير حلول تقنية مبتكرة تحل مشاكل حقيقية في السوق.

"""
        
        # سياق الاجتماع والمرحلة
        meeting_phase = context.get('meeting_phase', 'general_discussion')
        
        # إضافة سياق المحادثة السابقة لتجنب التكرار
        recent_messages = self.get_recent_context(3)
        if recent_messages:
            agent_info += "رسائلك الأخيرة في هذا الاجتماع:\n"
            for msg in recent_messages[-2:]:  # آخر رسالتين فقط
                agent_info += f"- {msg.content[:100]}...\n"
            agent_info += "\nتجنب تكرار نفس الأفكار أو العبارات.\n\n"
        
        if meeting_phase == 'project_proposal':
            agent_info += """🎯 مرحلة العصف الذهني - اقترح مشروع تقني مبتكر:

المطلوب منك:
- اقترح مشروع تقني حقيقي وقابل للتنفيذ من منظور دورك
- يجب أن يحل مشكلة فعلية في السوق
- اشرح المشكلة والحل والسوق المستهدف بوضوح
- كن مبدعاً ومقنعاً في عرضك
- اجعل اقتراحك مختلف عن الاقتراحات السابقة

أسلوب الكتابة:
- ابدأ بتقديم نفسك وخبرتك
- اعرض المشروع بحماس وثقة
- استخدم أمثلة واقعية
- اختتم بتأكيد الفائدة للعملاء"""

        elif meeting_phase == 'project_evaluation':
            current_suggestion = context.get('current_suggestion', {})
            evaluation_focus = context.get('evaluation_focus', 'التقييم العام')
            
            agent_info += f"""🔍 مرحلة تقييم المشروع - ركز على: {evaluation_focus}

المشروع المطروح: {current_suggestion.get('suggestion', '')[:200]}...

المطلوب منك:
- قدم تقييم صادق ومفصل من منظور دورك
- اذكر النقاط الإيجابية والسلبية
- حدد التحديات المحتملة في مجال خبرتك
- اقترح تحسينات أو حلول للمشاكل
- كن موضوعياً وبناءً في نقدك

أسلوب الكتابة:
- ابدأ برأيك العام في المشروع
- اذكر نقاط محددة من خبرتك
- استخدم أمثلة من تجاربك السابقة
- اختتم بتوصية واضحة"""

        elif meeting_phase == 'proposal_defense':
            agent_info += """🛡️ مرحلة الدفاع عن الاقتراح:

زملاؤك علقوا على اقتراحك. المطلوب:
- رد على التعليقات والمخاوف بطريقة مهنية
- وضح النقاط الغامضة أو المبهمة
- أضف تفاصيل تقنية أو تجارية مهمة فاتتك
- أظهر ثقتك بالمشروع مع الاعتراف بالتحديات
- اقترح حلول للمشاكل المطروحة

أسلوب الكتابة:
- اشكر الزملاء على تعليقاتهم
- رد على كل نقطة بوضوح
- أضف معلومات جديدة مفيدة
- أظهر مرونة واستعداد للتحسين"""

        elif meeting_phase == 'open_debate':
            all_suggestions = context.get('all_suggestions', [])
            
            agent_info += f"""💬 مرحلة المناقشة المفتوحة:

تم طرح {len(all_suggestions)} اقتراحات مختلفة. المطلوب:
- شارك برأيك الصريح والمفصل
- قارن بين الاقتراحات المختلفة
- اطرح أسئلة مهمة لم تُطرح بعد
- شارك خبرتك السابقة ذات الصلة
- اقترح تحسينات أو بدائل

أسلوب الكتابة:
- كن صريحاً ومباشراً
- استخدم أمثلة من الواقع
- اطرح أسئلة استفزازية مفيدة
- أظهر تفكيراً نقدياً عميقاً"""

        elif meeting_phase == 'vote_justification':
            my_vote = context.get('my_vote', 'محايد')
            proposal = context.get('proposal', {})
            
            agent_info += f"""🗳️ مرحلة تبرير التصويت:

صوتك: {my_vote}
المشروع: {proposal.get('title', 'غير محدد')}

المطلوب:
- اشرح بوضوح ومنطق لماذا صوت بهذا الشكل
- اربط قرارك بخبرتك ومجال تخصصك
- اذكر العوامل المحددة التي أثرت على قرارك
- كن صادقاً في تقييمك حتى لو كان سلبياً

أسلوب الكتابة:
- ابدأ بإعلان صوتك بوضوح
- اذكر 2-3 أسباب محددة
- استخدم أمثلة من خبرتك
- اختتم بنصيحة أو توصية"""

        elif meeting_phase == 'implementation_planning':
            approved_project = context.get('approved_project', {})
            
            agent_info += f"""⚙️ مرحلة التخطيط للتنفيذ:

المشروع المعتمد: {approved_project.get('title', 'غير محدد')}

المطلوب من منظور دورك:
- حدد ما تحتاجه لتنفيذ هذا المشروع
- اذكر الموارد والأدوات المطلوبة
- حدد التحديات المتوقعة في مجالك
- اقترح جدول زمني واقعي
- حدد معايير النجاح في تخصصك

أسلوب الكتابة:
- كن عملياً ومحدداً
- اذكر خطوات واضحة قابلة للتنفيذ
- حدد المسؤوليات والأدوار
- اقترح مؤشرات قياس الأداء"""

        elif meeting_phase == 'self_reflection':
            meeting_summary = context.get('meeting_summary', {})
            my_contributions = context.get('my_contributions', 0)
            
            agent_info += f"""📝 مرحلة المراجعة الذاتية:

الاجتماع انتهى. المطلوب:
- قيم أداءك في الاجتماع بصدق
- اذكر ما نجح وما فشل
- حدد خطة للتحسين
- كن بناءً ومفيداً في تقييمك

معلومات أدائك:
- عدد مساهماتك: {my_contributions}
- دورك في الاجتماع: {self.profile.role}
- مجالات خبرتك: {', '.join(self.profile.expertise_areas)}

أسلوب الكتابة:
- كن صادقاً وموضوعياً
- اذكر أمثلة محددة من الاجتماع
- اقترح تحسينات عملية
- استخدم نبرة مهنية ومتفائلة"""

        else:
            # مناقشة عامة
            agent_info += """💭 مناقشة عامة:

أنت في اجتماع عمل مهني. المطلوب:
- شارك برأيك بطريقة طبيعية ومفيدة
- اعكس شخصيتك المهنية ودورك
- أضف قيمة حقيقية للنقاش
- كن مختصراً ومركزاً
- تجنب التكرار والعموميات

أسلوب الكتابة:
- كن طبيعياً وتلقائياً
- استخدم خبرتك العملية
- اطرح أفكار جديدة ومفيدة
- كن إيجابياً وبناءً"""

        # إضافة تعليمات عامة مهمة
        agent_info += f"""

🎯 تعليمات مهمة:
- تحدث بالعربية فقط
- كن طبيعي ومتنوع - تجنب التكرار تماماً
- اجعل ردك مختلف عن ردودك السابقة
- لا تتجاوز 4 جمل (إلا في مرحلة اقتراح المشاريع)
- اعكس شخصيتك: {', '.join(self.profile.personality_traits)}
- استخدم خبرتك في: {', '.join(self.profile.expertise_areas)}
- كن مهنياً لكن ودوداً
- تجنب العبارات المكررة مثل "من وجهة نظري" أو "أعتقد أن"
- استخدم أمثلة واقعية عندما أمكن
- كن حاسماً في آرائك ومقترحاتك

🚫 تجنب هذه العبارات المكررة:
- "من وجهة نظر..."
- "أعتقد أن..."
- "يجب أن نضمن..."
- "من ناحية..."
- "أقترح أن..."

✅ استخدم بدائل متنوعة:
- "خبرتي تقول..."
- "الواقع يؤكد..."
- "لاحظت في مشاريع سابقة..."
- "التجربة علمتني..."
- "الأرقام تشير إلى..."
"""

        return agent_info
    
    def generate_project_idea(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """توليد فكرة مشروع جديدة (للـ CEO Agent فقط)"""
        if self.profile.id != "ceo":
            raise ValueError("توليد الأفكار متاح فقط للرئيس التنفيذي")
        
        if not self.idea_generator:
            raise ValueError("مولد الأفكار غير مُهيأ")
        
        # إضافة سياق الوكيل للمولد
        agent_context = context or {}
        agent_context.update({
            "agent_expertise": self.profile.expertise_areas,
            "agent_personality": self.profile.personality_traits,
            "preferred_category": self._determine_preferred_category(),
            "max_budget": 30000  # ميزانية افتراضية
        })
        
        return self.idea_generator.generate_project_idea(agent_context)
    
    def _determine_preferred_category(self) -> str:
        """تحديد الفئة المفضلة بناءً على شخصية الوكيل"""
        if self.profile.id == "ceo":
            # الرئيس التنفيذي يفضل المشاريع الاستراتيجية
            import random
            return random.choice(["saas", "tool", "bot"])
        return "tool"  # افتراضي
    
    def vote_on_proposal(self, proposal: Dict[str, Any]) -> str:
        """التصويت على اقتراح بناءً على دور الوكيل وتحليل المشروع"""
        
        # تحليل المشروع من منظور الوكيل
        project_title = proposal.get('title', '').lower()
        project_description = proposal.get('description', '').lower()
        
        # منطق تصويت ذكي بناءً على دور الوكيل
        if self.profile.id == "critic":
            # الناقد يركز على المخاطر والتحديات
            high_risk_keywords = ['ذكاء اصطناعي', 'بلوك تشين', 'جديد تماماً', 'ثوري', 'لم يُجرب']
            if any(keyword in project_description for keyword in high_risk_keywords):
                return "محايد - أحتاج المزيد من المعلومات"
            elif 'منافسة عالية' in project_description or 'تحديات كبيرة' in project_description:
                return "موافق بشروط"
            else:
                return "موافق"
                
        elif self.profile.id == "finance":
            # المحلل المالي يركز على الربحية والتكاليف
            if 'مكلف' in project_description or 'استثمار كبير' in project_description:
                return "موافق بشروط"
            elif any(keyword in project_title for keyword in ['مجاني', 'مفتوح المصدر']):
                return "محايد"
            else:
                return "موافق"
                
        elif self.profile.id == "qa":
            # ضمان الجودة يركز على قابلية الاختبار والموثوقية
            complex_keywords = ['معقد', 'متقدم جداً', 'تقنيات حديثة']
            if any(keyword in project_description for keyword in complex_keywords):
                return "موافق بشروط"
            else:
                return "موافق"
                
        elif self.profile.id == "cto":
            # المدير التقني يركز على الجانب التقني والقابلية للتطوير
            tech_keywords = ['تقني', 'برمجة', 'نظام', 'منصة', 'أداة']
            if any(keyword in project_title for keyword in tech_keywords):
                return "موافق"
            else:
                return "محايد"
                
        elif self.profile.id == "developer":
            # المطور يركز على قابلية التنفيذ
            dev_friendly = ['مكتبة', 'أداة', 'إطار عمل', 'API']
            if any(keyword in project_title for keyword in dev_friendly):
                return "موافق"
            elif 'معقد جداً' in project_description:
                return "موافق بشروط"
            else:
                return "موافق"
                
        elif self.profile.id == "marketing":
            # التسويق يركز على السوق والعملاء
            market_keywords = ['عملاء', 'سوق', 'تسويق', 'مبيعات']
            if any(keyword in project_description for keyword in market_keywords):
                return "موافق"
            else:
                return "محايد"
                
        elif self.profile.id == "pm":
            # مدير المشاريع يركز على القابلية للإدارة
            manageable_keywords = ['مراحل', 'تدريجي', 'منظم']
            if any(keyword in project_description for keyword in manageable_keywords):
                return "موافق"
            elif 'معقد' in project_description:
                return "موافق بشروط"
            else:
                return "موافق"
                
        elif self.profile.id == "ceo":
            # الرئيس التنفيذي يركز على الاستراتيجية والربحية
            strategic_keywords = ['مبتكر', 'استراتيجي', 'مربح', 'نمو']
            if any(keyword in project_description for keyword in strategic_keywords):
                return "موافق"
            else:
                return "موافق"
                
        else:
            # باقي الوكلاء - تصويت متوازن
            import random
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