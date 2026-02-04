"""
نظام المراجعة الذاتية المحسن لـ AACS V0
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .config import Config
from .logger import setup_logger, SecureLogger
from .memory import MemorySystem


@dataclass
class ReflectionTemplate:
    """قالب المراجعة الذاتية"""
    id: str
    name: str
    sections: List[str]
    prompts: Dict[str, str]
    evaluation_criteria: List[str]


@dataclass
class ReflectionInsight:
    """رؤية من المراجعة الذاتية"""
    category: str  # success, failure, improvement
    content: str
    confidence: float
    actionable: bool
    priority: str  # high, medium, low


class SelfReflectionSystem:
    """نظام المراجعة الذاتية المحسن"""
    
    def __init__(self, config: Config, memory_system: MemorySystem):
        self.config = config
        self.memory_system = memory_system
        self.logger = SecureLogger(setup_logger("self_reflection"))
        
        # تحميل قوالب التقييم
        self.templates = self._load_reflection_templates()
        
        self.logger.info(f"📝 تم تهيئة نظام المراجعة الذاتية مع {len(self.templates)} قالب")
    
    def _load_reflection_templates(self) -> Dict[str, ReflectionTemplate]:
        """تحميل قوالب المراجعة الذاتية"""
        templates = {}
        
        # قالب المراجعة الأساسي
        basic_template = ReflectionTemplate(
            id="basic_reflection",
            name="المراجعة الذاتية الأساسية",
            sections=["ما نجح", "ما فشل", "خطة التحسين", "ملاحظات إضافية"],
            prompts={
                "ما نجح": "اذكر 2-3 أشياء نجحت فيها خلال هذا الاجتماع من منظور دورك",
                "ما فشل": "اذكر 1-2 أشياء لم تسر كما هو مخطط أو يمكن تحسينها",
                "خطة التحسين": "ضع خطة عملية محددة للتحسين في الاجتماعات القادمة",
                "ملاحظات إضافية": "أي ملاحظات أخرى مهمة حول الاجتماع أو الفريق"
            },
            evaluation_criteria=[
                "جودة المساهمات",
                "التفاعل مع الفريق",
                "تحقيق أهداف الدور",
                "الاستعداد للاجتماع"
            ]
        )
        
        # قالب المراجعة التقنية (للأدوار التقنية)
        technical_template = ReflectionTemplate(
            id="technical_reflection",
            name="المراجعة الذاتية التقنية",
            sections=["الحلول التقنية", "التحديات التقنية", "التعلم والتطوير", "التعاون التقني"],
            prompts={
                "الحلول التقنية": "ما هي الحلول التقنية التي اقترحتها وكيف كانت مفيدة؟",
                "التحديات التقنية": "ما هي التحديات التقنية التي واجهتها أو تم مناقشتها؟",
                "التعلم والتطوير": "ما الذي تعلمته جديد أو تحتاج لتطويره تقنياً؟",
                "التعاون التقني": "كيف كان تعاونك مع الفريق في الجوانب التقنية؟"
            },
            evaluation_criteria=[
                "دقة الحلول التقنية",
                "ابتكار الأفكار",
                "التواصل التقني",
                "حل المشاكل"
            ]
        )
        
        # قالب المراجعة الإدارية (للأدوار الإدارية)
        management_template = ReflectionTemplate(
            id="management_reflection",
            name="المراجعة الذاتية الإدارية",
            sections=["القيادة والتوجيه", "اتخاذ القرارات", "إدارة الفريق", "التخطيط الاستراتيجي"],
            prompts={
                "القيادة والتوجيه": "كيف قدت النقاش ووجهت الفريق نحو الأهداف؟",
                "اتخاذ القرارات": "ما هي القرارات التي ساهمت فيها وكيف كانت فعاليتها؟",
                "إدارة الفريق": "كيف تعاملت مع ديناميكيات الفريق والآراء المختلفة؟",
                "التخطيط الاستراتيجي": "كيف ساهمت في التخطيط طويل المدى للمشاريع؟"
            },
            evaluation_criteria=[
                "فعالية القيادة",
                "جودة القرارات",
                "إدارة الصراعات",
                "الرؤية الاستراتيجية"
            ]
        )
        
        templates["basic"] = basic_template
        templates["technical"] = technical_template
        templates["management"] = management_template
        
        return templates
    
    def generate_enhanced_reflection(self, agent_id: str, agent_profile: Any, 
                                   meeting_summary: Dict[str, Any], 
                                   conversation_history: List[Any]) -> str:
        """توليد مراجعة ذاتية محسنة"""
        
        # اختيار القالب المناسب
        template = self._select_template_for_agent(agent_id, agent_profile)
        
        # حساب الإحصائيات
        stats = self._calculate_agent_stats(agent_id, conversation_history, meeting_summary)
        
        # استرجاع التقييمات السابقة للمقارنة
        previous_reflections = self._get_previous_reflections(agent_id)
        
        # توليد المحتوى
        reflection_content = self._generate_reflection_content(
            agent_profile, template, stats, previous_reflections, meeting_summary
        )
        
        # استخراج الرؤى
        insights = self._extract_structured_insights(reflection_content)
        
        # تنسيق التقرير النهائي
        formatted_report = self._format_reflection_report(
            agent_profile, template, reflection_content, stats, insights, meeting_summary
        )
        
        # حفظ الرؤى في الذاكرة
        self._store_reflection_insights(agent_id, meeting_summary.get('session_id'), insights)
        
        return formatted_report
    
    def _select_template_for_agent(self, agent_id: str, agent_profile: Any) -> ReflectionTemplate:
        """اختيار القالب المناسب للوكيل"""
        
        # الأدوار التقنية
        technical_roles = ["cto", "developer", "qa"]
        # الأدوار الإدارية
        management_roles = ["ceo", "pm", "chair"]
        
        if agent_id in technical_roles:
            return self.templates["technical"]
        elif agent_id in management_roles:
            return self.templates["management"]
        else:
            return self.templates["basic"]
    
    def _calculate_agent_stats(self, agent_id: str, conversation_history: List[Any], 
                              meeting_summary: Dict[str, Any]) -> Dict[str, Any]:
        """حساب إحصائيات أداء الوكيل"""
        
        my_messages = [m for m in conversation_history if m.agent_id == agent_id]
        
        stats = {
            "total_contributions": len(my_messages),
            "average_message_length": 0,
            "participation_rate": 0,
            "message_types": {},
            "engagement_score": 0
        }
        
        if my_messages:
            # متوسط طول الرسائل
            total_length = sum(len(m.content) for m in my_messages)
            stats["average_message_length"] = total_length / len(my_messages)
            
            # معدل المشاركة
            total_messages = len(conversation_history)
            stats["participation_rate"] = (len(my_messages) / total_messages) * 100 if total_messages > 0 else 0
            
            # أنواع الرسائل
            for message in my_messages:
                msg_type = getattr(message, 'message_type', 'contribution')
                stats["message_types"][msg_type] = stats["message_types"].get(msg_type, 0) + 1
            
            # درجة التفاعل (بناءً على التنوع والكمية)
            type_diversity = len(stats["message_types"])
            stats["engagement_score"] = min(100, (len(my_messages) * 10) + (type_diversity * 5))
        
        return stats
    
    def _get_previous_reflections(self, agent_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        """استرجاع التقييمات السابقة للوكيل"""
        try:
            # البحث في نظام الذاكرة عن تقييمات سابقة
            query_result = self.memory_system.retrieve_context(
                f"agent:{agent_id} reflection", 
                limit=limit, 
                entry_types=["reflections"]
            )
            
            previous_reflections = []
            for entry in query_result.entries:
                if entry.content.get("agent_id") == agent_id:
                    previous_reflections.append({
                        "session_id": entry.content.get("session_id"),
                        "insights": entry.content.get("extracted_insights", {}),
                        "timestamp": entry.timestamp
                    })
            
            return previous_reflections
            
        except Exception as e:
            self.logger.warning(f"فشل في استرجاع التقييمات السابقة للوكيل {agent_id}: {e}")
            return []
    
    def _generate_reflection_content(self, agent_profile: Any, template: ReflectionTemplate,
                                   stats: Dict[str, Any], previous_reflections: List[Dict[str, Any]],
                                   meeting_summary: Dict[str, Any]) -> Dict[str, str]:
        """توليد محتوى المراجعة الذاتية"""
        
        content = {}
        
        for section in template.sections:
            prompt = template.prompts.get(section, f"اكتب عن {section}")
            
            # إضافة السياق للمطالبة
            enhanced_prompt = f"""
كـ{agent_profile.name} ({agent_profile.role}):

{prompt}

معلومات مفيدة:
- عدد مساهماتك: {stats['total_contributions']}
- معدل مشاركتك: {stats['participation_rate']:.1f}%
- درجة تفاعلك: {stats['engagement_score']}/100

"""
            
            # إضافة سياق التقييمات السابقة إذا وجدت
            if previous_reflections:
                enhanced_prompt += "\nمن تقييماتك السابقة، ركز على تحسين النقاط التي حددتها سابقاً.\n"
            
            enhanced_prompt += f"\nاكتب 2-3 جمل محددة وعملية عن {section}."
            
            # هنا يمكن استخدام الذكاء الاصطناعي لتوليد المحتوى
            # للآن سنستخدم قوالب بسيطة
            content[section] = self._generate_section_content(section, agent_profile, stats)
        
        return content
    
    def _generate_section_content(self, section: str, agent_profile: Any, 
                                stats: Dict[str, Any]) -> str:
        """توليد محتوى قسم محدد"""
        
        if section == "ما نجح" or section == "الحلول التقنية" or section == "القيادة والتوجيه":
            if stats['total_contributions'] > 3:
                return f"شاركت بفعالية في النقاش مع {stats['total_contributions']} مساهمة، وقدمت رؤى قيمة من منظور {agent_profile.role}."
            else:
                return f"ساهمت في النقاش من منظور {agent_profile.role} وقدمت وجهة نظر متخصصة."
        
        elif section == "ما فشل" or section == "التحديات التقنية":
            if stats['participation_rate'] < 15:
                return "يمكنني زيادة مشاركتي في النقاش وتقديم المزيد من الأفكار والحلول."
            else:
                return "أحتاج لتحسين جودة مساهماتي وجعلها أكثر تفصيلاً وعمقاً."
        
        elif section == "خطة التحسين" or section == "التعلم والتطوير":
            improvements = []
            if stats['participation_rate'] < 20:
                improvements.append("زيادة المشاركة الفعالة في النقاشات")
            if stats['engagement_score'] < 50:
                improvements.append("تنويع أنواع المساهمات (اقتراحات، أسئلة، تحليل)")
            if not improvements:
                improvements.append("تطوير خبرتي في مجالات جديدة ذات صلة بدوري")
            
            return "سأركز على: " + "، ".join(improvements) + "."
        
        else:
            return f"أقدر الفرصة للمساهمة كـ{agent_profile.role} وأتطلع للاجتماعات القادمة."
    
    def _extract_structured_insights(self, reflection_content: Dict[str, str]) -> List[ReflectionInsight]:
        """استخراج رؤى منظمة من المحتوى"""
        insights = []
        
        for section, content in reflection_content.items():
            if "نجح" in section or "حلول" in section or "قيادة" in section:
                category = "success"
                priority = "medium"
                actionable = False
            elif "فشل" in section or "تحديات" in section:
                category = "failure"
                priority = "high"
                actionable = True
            elif "تحسين" in section or "تطوير" in section:
                category = "improvement"
                priority = "high"
                actionable = True
            else:
                category = "general"
                priority = "low"
                actionable = False
            
            insight = ReflectionInsight(
                category=category,
                content=content,
                confidence=0.8,  # ثقة افتراضية
                actionable=actionable,
                priority=priority
            )
            insights.append(insight)
        
        return insights
    
    def _format_reflection_report(self, agent_profile: Any, template: ReflectionTemplate,
                                content: Dict[str, str], stats: Dict[str, Any],
                                insights: List[ReflectionInsight], 
                                meeting_summary: Dict[str, Any]) -> str:
        """تنسيق التقرير النهائي"""
        
        report = f"""# تقرير المراجعة الذاتية المحسن - {agent_profile.name}

## معلومات الاجتماع
- **معرف الجلسة**: {meeting_summary.get('session_id', 'غير محدد')}
- **التاريخ**: {meeting_summary.get('timestamp', 'غير محدد')}
- **الأجندة**: {meeting_summary.get('agenda', 'غير محدد')}
- **دوري**: {agent_profile.role}
- **قالب التقييم**: {template.name}

## التقييم الذاتي المفصل

"""
        
        # إضافة أقسام المحتوى
        for section in template.sections:
            if section in content:
                # تحديد الرمز المناسب للقسم
                if "نجح" in section or "حلول" in section or "قيادة" in section:
                    icon = "✅"
                elif "فشل" in section or "تحديات" in section:
                    icon = "❌"
                elif "تحسين" in section or "تطوير" in section:
                    icon = "🔄"
                else:
                    icon = "📝"
                
                report += f"### {icon} {section}\n\n{content[section]}\n\n"
        
        # إضافة الإحصائيات المفصلة
        report += f"""## إحصائيات الأداء التفصيلية

### مؤشرات المشاركة
- **إجمالي المساهمات**: {stats['total_contributions']}
- **معدل المشاركة**: {stats['participation_rate']:.1f}%
- **متوسط طول المساهمة**: {stats['average_message_length']:.0f} حرف
- **درجة التفاعل**: {stats['engagement_score']}/100

### توزيع أنواع المساهمات
"""
        
        for msg_type, count in stats['message_types'].items():
            report += f"- **{msg_type}**: {count}\n"
        
        # إضافة الرؤى المستخرجة
        report += f"""

## الرؤى المستخرجة

### نقاط القوة 💪
"""
        success_insights = [i for i in insights if i.category == "success"]
        for insight in success_insights:
            report += f"- {insight.content}\n"
        
        report += f"""
### نقاط التحسين 🎯
"""
        improvement_insights = [i for i in insights if i.category in ["failure", "improvement"]]
        for insight in improvement_insights:
            priority_icon = "🔴" if insight.priority == "high" else "🟡" if insight.priority == "medium" else "🟢"
            report += f"- {priority_icon} {insight.content}\n"
        
        # إضافة معايير التقييم
        report += f"""

## معايير التقييم المطبقة
"""
        for criterion in template.evaluation_criteria:
            report += f"- {criterion}\n"
        
        # إضافة الخاتمة
        report += f"""

## الخطوات التالية
بناءً على هذا التقييم، سأركز في الاجتماعات القادمة على تحسين النقاط المحددة أعلاه وتطوير مهاراتي في {', '.join(agent_profile.expertise_areas)}.

---
*تم إنتاج هذا التقرير المحسن في {datetime.now(timezone.utc).isoformat()}*
*نظام المراجعة الذاتية AACS V0*
"""
        
        return report
    
    def _store_reflection_insights(self, agent_id: str, session_id: str, 
                                 insights: List[ReflectionInsight]):
        """حفظ الرؤى في نظام الذاكرة للاستخدام المستقبلي"""
        try:
            insights_data = {
                "agent_id": agent_id,
                "session_id": session_id,
                "insights": [
                    {
                        "category": insight.category,
                        "content": insight.content,
                        "priority": insight.priority,
                        "actionable": insight.actionable
                    }
                    for insight in insights
                ],
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # حفظ في ملف منفصل للرؤى
            insights_dir = Path("memory/insights")
            insights_dir.mkdir(exist_ok=True)
            
            insights_file = insights_dir / f"{agent_id}_{session_id}_insights.json"
            with open(insights_file, 'w', encoding='utf-8') as f:
                json.dump(insights_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"✅ تم حفظ رؤى التقييم للوكيل {agent_id}")
            
        except Exception as e:
            self.logger.warning(f"فشل في حفظ رؤى التقييم: {e}")
    
    def get_agent_improvement_trends(self, agent_id: str) -> Dict[str, Any]:
        """تحليل اتجاهات التحسن للوكيل"""
        try:
            previous_reflections = self._get_previous_reflections(agent_id, limit=5)
            
            if len(previous_reflections) < 2:
                return {"trend": "insufficient_data", "message": "بيانات غير كافية لتحليل الاتجاه"}
            
            # تحليل التحسن عبر الوقت
            improvement_areas = {}
            for reflection in previous_reflections:
                insights = reflection.get("insights", {})
                for category, items in insights.items():
                    if category not in improvement_areas:
                        improvement_areas[category] = []
                    improvement_areas[category].extend(items)
            
            return {
                "trend": "improving" if len(improvement_areas.get("successes", [])) > len(improvement_areas.get("failures", [])) else "needs_attention",
                "improvement_areas": improvement_areas,
                "total_reflections": len(previous_reflections)
            }
            
        except Exception as e:
            self.logger.error(f"فشل في تحليل اتجاهات التحسن: {e}")
            return {"trend": "error", "message": str(e)}