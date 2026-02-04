"""
مولد الأفكار مع القوالب المحددة لنظام AACS V0
"""
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .config import Config
from .logger import setup_logger, SecureLogger
from .memory import MemorySystem


@dataclass
class ProjectTemplate:
    """قالب مشروع"""
    id: str
    name: str
    category: str
    description: str
    problem_statement: str
    target_market: str
    tech_stack: List[str]
    estimated_cost: int
    estimated_revenue: int
    development_time_weeks: int
    difficulty_level: str  # easy, medium, hard
    market_size: str  # small, medium, large
    competition_level: str  # low, medium, high


class IdeaGenerator:
    """مولد الأفكار مع القوالب المحددة"""
    
    def __init__(self, config: Config, memory_system: MemorySystem):
        self.config = config
        self.memory_system = memory_system
        self.logger = SecureLogger(setup_logger("idea_generator"))
        
        # تحميل قوالب المشاريع
        self.templates = self._load_project_templates()
        
        # تحميل الأفكار المرفوضة من الذاكرة
        self.rejected_ideas = self._load_rejected_ideas()
        
        self.logger.info(f"🧠 تم تهيئة مولد الأفكار مع {len(self.templates)} قالب")
    
    def _load_project_templates(self) -> Dict[str, ProjectTemplate]:
        """تحميل قوالب المشاريع المحددة"""
        templates = {}
        
        # قوالب البوتات والأدوات
        bot_templates = [
            ProjectTemplate(
                id="chatbot_customer_service",
                name="بوت خدمة العملاء الذكي",
                category="bot",
                description="بوت محادثة ذكي يستخدم الذكاء الاصطناعي لخدمة العملاء على مدار الساعة",
                problem_statement="الشركات تحتاج لخدمة عملاء متاحة 24/7 بتكلفة معقولة",
                target_market="الشركات الصغيرة والمتوسطة",
                tech_stack=["Python", "FastAPI", "OpenAI API", "PostgreSQL", "Docker"],
                estimated_cost=15000,
                estimated_revenue=45000,
                development_time_weeks=8,
                difficulty_level="medium",
                market_size="large",
                competition_level="high"
            ),
            ProjectTemplate(
                id="social_media_bot",
                name="بوت إدارة وسائل التواصل الاجتماعي",
                category="bot",
                description="بوت يدير المحتوى والتفاعل على منصات التواصل الاجتماعي تلقائياً",
                problem_statement="إدارة وسائل التواصل الاجتماعي تستغرق وقت كبير",
                target_market="المؤثرين والشركات الصغيرة",
                tech_stack=["Python", "Twitter API", "Instagram API", "MongoDB", "Celery"],
                estimated_cost=12000,
                estimated_revenue=36000,
                development_time_weeks=6,
                difficulty_level="medium",
                market_size="medium",
                competition_level="medium"
            )
        ]
        
        # قوالب الإضافات والامتدادات
        extension_templates = [
            ProjectTemplate(
                id="vscode_ai_assistant",
                name="مساعد الذكاء الاصطناعي لـ VS Code",
                category="extension",
                description="إضافة VS Code تستخدم الذكاء الاصطناعي لمساعدة المطورين في كتابة الكود",
                problem_statement="المطورون يحتاجون لمساعدة ذكية أثناء البرمجة",
                target_market="المطورين والمبرمجين",
                tech_stack=["TypeScript", "VS Code API", "OpenAI API", "Node.js"],
                estimated_cost=10000,
                estimated_revenue=30000,
                development_time_weeks=5,
                difficulty_level="medium",
                market_size="large",
                competition_level="high"
            ),
            ProjectTemplate(
                id="browser_productivity_extension",
                name="إضافة متصفح لتحسين الإنتاجية",
                category="extension",
                description="إضافة متصفح تساعد في إدارة الوقت وحجب المشتتات وتنظيم التبويبات",
                problem_statement="المستخدمون يفقدون التركيز بسبب المشتتات على الإنترنت",
                target_market="العاملين والطلاب",
                tech_stack=["JavaScript", "Chrome Extension API", "React", "IndexedDB"],
                estimated_cost=8000,
                estimated_revenue=24000,
                development_time_weeks=4,
                difficulty_level="easy",
                market_size="large",
                competition_level="medium"
            )
        ]
        
        # قوالب الأدوات
        tool_templates = [
            ProjectTemplate(
                id="api_testing_tool",
                name="أداة اختبار APIs المتقدمة",
                category="tool",
                description="أداة سطر أوامر لاختبار وتوثيق APIs بطريقة ذكية ومؤتمتة",
                problem_statement="اختبار APIs يدوياً عملية مملة ومعرضة للأخطاء",
                target_market="المطورين وفرق QA",
                tech_stack=["Go", "CLI", "HTTP Client", "JSON Schema", "YAML"],
                estimated_cost=12000,
                estimated_revenue=36000,
                development_time_weeks=6,
                difficulty_level="medium",
                market_size="medium",
                competition_level="medium"
            ),
            ProjectTemplate(
                id="database_migration_tool",
                name="أداة ترحيل قواعد البيانات الذكية",
                category="tool",
                description="أداة تسهل ترحيل البيانات بين قواعد بيانات مختلفة مع ضمان سلامة البيانات",
                problem_statement="ترحيل قواعد البيانات عملية معقدة ومحفوفة بالمخاطر",
                target_market="فرق DevOps ومديري قواعد البيانات",
                tech_stack=["Python", "SQLAlchemy", "Docker", "PostgreSQL", "MySQL"],
                estimated_cost=18000,
                estimated_revenue=54000,
                development_time_weeks=10,
                difficulty_level="hard",
                market_size="medium",
                competition_level="low"
            )
        ]
        
        # قوالب SaaS
        saas_templates = [
            ProjectTemplate(
                id="project_management_saas",
                name="منصة إدارة المشاريع للفرق الصغيرة",
                category="saas",
                description="منصة سحابية بسيطة وفعالة لإدارة المشاريع والمهام للفرق الصغيرة",
                problem_statement="أدوات إدارة المشاريع الحالية معقدة ومكلفة للفرق الصغيرة",
                target_market="الفرق الصغيرة والشركات الناشئة",
                tech_stack=["React", "Node.js", "PostgreSQL", "Redis", "AWS"],
                estimated_cost=25000,
                estimated_revenue=75000,
                development_time_weeks=12,
                difficulty_level="hard",
                market_size="large",
                competition_level="high"
            ),
            ProjectTemplate(
                id="invoice_automation_saas",
                name="منصة أتمتة الفواتير للشركات الصغيرة",
                category="saas",
                description="منصة تؤتمت إنشاء وإرسال ومتابعة الفواتير للشركات الصغيرة",
                problem_statement="إدارة الفواتير يدوياً تستغرق وقت كبير وعرضة للأخطاء",
                target_market="الشركات الصغيرة والمستقلين",
                tech_stack=["Vue.js", "Laravel", "MySQL", "Stripe API", "PDF Generator"],
                estimated_cost=20000,
                estimated_revenue=60000,
                development_time_weeks=10,
                difficulty_level="medium",
                market_size="large",
                competition_level="medium"
            )
        ]
        
        # قوالب GitHub Automation
        github_templates = [
            ProjectTemplate(
                id="pr_review_automation",
                name="أتمتة مراجعة Pull Requests",
                category="github_automation",
                description="GitHub Action يراجع Pull Requests تلقائياً ويقدم اقتراحات للتحسين",
                problem_statement="مراجعة الكود يدوياً تستغرق وقت كبير من المطورين",
                target_market="فرق التطوير والمشاريع مفتوحة المصدر",
                tech_stack=["JavaScript", "GitHub API", "OpenAI API", "Docker", "YAML"],
                estimated_cost=8000,
                estimated_revenue=24000,
                development_time_weeks=4,
                difficulty_level="medium",
                market_size="large",
                competition_level="low"
            ),
            ProjectTemplate(
                id="dependency_security_scanner",
                name="ماسح أمان التبعيات التلقائي",
                category="github_automation",
                description="GitHub Action يفحص التبعيات للثغرات الأمنية ويقترح التحديثات",
                problem_statement="تتبع الثغرات الأمنية في التبعيات عملية معقدة",
                target_market="فرق DevOps والأمان",
                tech_stack=["Python", "GitHub API", "Security APIs", "Docker", "YAML"],
                estimated_cost=10000,
                estimated_revenue=30000,
                development_time_weeks=5,
                difficulty_level="medium",
                market_size="medium",
                competition_level="medium"
            )
        ]
        
        # دمج جميع القوالب
        all_templates = (bot_templates + extension_templates + 
                        tool_templates + saas_templates + github_templates)
        
        for template in all_templates:
            templates[template.id] = template
        
        return templates
    
    def _load_rejected_ideas(self) -> List[str]:
        """تحميل الأفكار المرفوضة من نظام الذاكرة"""
        try:
            # البحث في قرارات الاجتماعات السابقة عن المشاريع المرفوضة
            rejected_ideas = []
            
            # استرجاع تاريخ التصويت من الذاكرة
            voting_history = self.memory_system.get_voting_history()
            
            for vote_record in voting_history:
                if vote_record.get('outcome') == 'rejected':
                    proposal_title = vote_record.get('proposal', {}).get('title', '')
                    if proposal_title:
                        rejected_ideas.append(proposal_title.lower())
            
            self.logger.info(f"📝 تم تحميل {len(rejected_ideas)} فكرة مرفوضة من الذاكرة")
            return rejected_ideas
            
        except Exception as e:
            self.logger.warning(f"فشل في تحميل الأفكار المرفوضة: {e}")
            return []
    
    def generate_project_idea(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """توليد فكرة مشروع جديدة بناءً على القوالب"""
        
        # تصفية القوالب المتاحة (تجنب المرفوضة سابقاً)
        available_templates = self._filter_available_templates()
        
        if not available_templates:
            self.logger.warning("⚠️ لا توجد قوالب متاحة - جميع الأفكار تم رفضها سابقاً")
            return self._generate_fallback_idea()
        
        # اختيار قالب بناءً على السياق أو عشوائياً
        selected_template = self._select_template(available_templates, context)
        
        # تخصيص القالب وإضافة تفاصيل إضافية
        customized_idea = self._customize_template(selected_template, context)
        
        self.logger.info(f"💡 تم توليد فكرة جديدة: {customized_idea['title']}")
        
        return customized_idea
    
    def _filter_available_templates(self) -> List[ProjectTemplate]:
        """تصفية القوالب المتاحة (تجنب المرفوضة)"""
        available = []
        
        for template in self.templates.values():
            # فحص إذا كانت الفكرة مشابهة للمرفوضة سابقاً
            is_rejected = any(
                rejected_title in template.name.lower() or 
                template.name.lower() in rejected_title
                for rejected_title in self.rejected_ideas
            )
            
            if not is_rejected:
                available.append(template)
        
        return available
    
    def _select_template(self, available_templates: List[ProjectTemplate], 
                        context: Dict[str, Any] = None) -> ProjectTemplate:
        """اختيار قالب بناءً على السياق"""
        
        if not context:
            # اختيار عشوائي
            return random.choice(available_templates)
        
        # اختيار ذكي بناءً على السياق
        preferred_category = context.get('preferred_category')
        preferred_difficulty = context.get('preferred_difficulty')
        max_budget = context.get('max_budget')
        
        # تصفية بناءً على المعايير
        filtered = available_templates
        
        if preferred_category:
            filtered = [t for t in filtered if t.category == preferred_category]
        
        if preferred_difficulty:
            filtered = [t for t in filtered if t.difficulty_level == preferred_difficulty]
        
        if max_budget:
            filtered = [t for t in filtered if t.estimated_cost <= max_budget]
        
        # إذا لم تبق قوالب بعد التصفية، استخدم الأصلية
        if not filtered:
            filtered = available_templates
        
        return random.choice(filtered)
    
    def _customize_template(self, template: ProjectTemplate, 
                           context: Dict[str, Any] = None) -> Dict[str, Any]:
        """تخصيص القالب وإضافة تفاصيل"""
        
        # إضافة تنويعات للاسم والوصف
        variations = self._generate_name_variations(template)
        
        # حساب ROI
        roi_percentage = ((template.estimated_revenue - template.estimated_cost) / 
                         template.estimated_cost) * 100
        
        # إنشاء الفكرة المخصصة
        customized_idea = {
            "id": f"idea_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "title": variations["name"],
            "description": variations["description"],
            "category": template.category,
            "template_id": template.id,
            "problem_statement": template.problem_statement,
            "target_market": template.target_market,
            "tech_stack": template.tech_stack,
            "business_model": self._generate_business_model(template),
            "financial_projection": {
                "estimated_cost": template.estimated_cost,
                "estimated_revenue": template.estimated_revenue,
                "roi_percentage": roi_percentage,
                "development_time_weeks": template.development_time_weeks,
                "break_even_months": max(1, template.development_time_weeks // 2)
            },
            "market_analysis": {
                "market_size": template.market_size,
                "competition_level": template.competition_level,
                "difficulty_level": template.difficulty_level
            },
            "implementation_plan": self._generate_implementation_plan(template),
            "success_metrics": self._generate_success_metrics(template),
            "risks_and_mitigation": self._generate_risks(template),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated_by": "idea_generator_v1"
        }
        
        return customized_idea
    
    def _generate_name_variations(self, template: ProjectTemplate) -> Dict[str, str]:
        """توليد تنويعات للاسم والوصف"""
        
        # تنويعات بسيطة للأسماء
        name_prefixes = ["", "منصة ", "نظام ", "أداة ", "حل "]
        name_suffixes = ["", " المتقدم", " الذكي", " المبتكر", " السحابي"]
        
        base_name = template.name
        # إزالة البادئات الموجودة
        for prefix in name_prefixes:
            if base_name.startswith(prefix):
                base_name = base_name[len(prefix):]
                break
        
        # إضافة تنويع جديد
        new_prefix = random.choice(name_prefixes)
        new_suffix = random.choice(name_suffixes)
        varied_name = f"{new_prefix}{base_name}{new_suffix}".strip()
        
        # تنويع الوصف
        description_starters = [
            "تطوير ",
            "بناء ",
            "إنشاء ",
            "تصميم وتطوير "
        ]
        
        starter = random.choice(description_starters)
        varied_description = f"{starter}{template.description}"
        
        return {
            "name": varied_name,
            "description": varied_description
        }
    
    def _generate_business_model(self, template: ProjectTemplate) -> Dict[str, Any]:
        """توليد نموذج عمل للمشروع"""
        
        if template.category == "saas":
            return {
                "type": "subscription",
                "pricing_model": "monthly_subscription",
                "target_price_per_month": template.estimated_revenue // 12 // 10,  # تقدير 10 عملاء
                "revenue_streams": ["اشتراكات شهرية", "خطط مميزة", "دعم فني"]
            }
        elif template.category == "tool":
            return {
                "type": "one_time_purchase",
                "pricing_model": "license",
                "target_price": template.estimated_revenue // 20,  # تقدير 20 عميل
                "revenue_streams": ["بيع التراخيص", "دعم فني", "تدريب"]
            }
        elif template.category in ["bot", "extension"]:
            return {
                "type": "freemium",
                "pricing_model": "freemium_with_premium",
                "target_price_per_month": template.estimated_revenue // 12 // 15,
                "revenue_streams": ["اشتراكات مميزة", "إعلانات", "عمولات"]
            }
        else:  # github_automation
            return {
                "type": "marketplace",
                "pricing_model": "pay_per_use",
                "target_price_per_use": 5,
                "revenue_streams": ["رسوم الاستخدام", "خطط مؤسسية", "استشارات"]
            }
    
    def _generate_implementation_plan(self, template: ProjectTemplate) -> List[Dict[str, Any]]:
        """توليد خطة تنفيذ للمشروع"""
        
        total_weeks = template.development_time_weeks
        
        phases = [
            {
                "phase": "التخطيط والتصميم",
                "duration_weeks": max(1, total_weeks // 4),
                "tasks": [
                    "تحليل المتطلبات التفصيلي",
                    "تصميم واجهة المستخدم",
                    "تصميم قاعدة البيانات",
                    "اختيار التقنيات والأدوات"
                ]
            },
            {
                "phase": "التطوير الأساسي",
                "duration_weeks": max(2, total_weeks // 2),
                "tasks": [
                    "إعداد البنية التحتية",
                    "تطوير الوظائف الأساسية",
                    "تطوير واجهة المستخدم",
                    "تكامل قاعدة البيانات"
                ]
            },
            {
                "phase": "الاختبار والتحسين",
                "duration_weeks": max(1, total_weeks // 5),
                "tasks": [
                    "اختبار الوحدة",
                    "اختبار التكامل",
                    "اختبار الأداء",
                    "إصلاح الأخطاء"
                ]
            },
            {
                "phase": "النشر والإطلاق",
                "duration_weeks": max(1, total_weeks - (total_weeks // 4) - (total_weeks // 2) - (total_weeks // 5)),
                "tasks": [
                    "إعداد بيئة الإنتاج",
                    "نشر التطبيق",
                    "اختبار الإنتاج",
                    "إطلاق رسمي"
                ]
            }
        ]
        
        return phases
    
    def _generate_success_metrics(self, template: ProjectTemplate) -> List[str]:
        """توليد مؤشرات النجاح للمشروع"""
        
        base_metrics = [
            f"تحقيق {template.estimated_revenue:,} ريال عائد في السنة الأولى",
            f"اكتساب 100+ مستخدم نشط في أول 3 أشهر",
            "تحقيق معدل رضا عملاء 85%+",
            "وقت استجابة أقل من 2 ثانية"
        ]
        
        # مؤشرات خاصة بالفئة
        if template.category == "saas":
            base_metrics.extend([
                "معدل الاحتفاظ بالعملاء 80%+",
                "نمو شهري 10%+ في المستخدمين"
            ])
        elif template.category == "tool":
            base_metrics.extend([
                "تحميل 1000+ في أول شهر",
                "تقييم 4.5+ نجوم في المتاجر"
            ])
        elif template.category in ["bot", "extension"]:
            base_metrics.extend([
                "معدل استخدام يومي 70%+",
                "مشاركة المستخدمين 50%+"
            ])
        
        return base_metrics
    
    def _generate_risks(self, template: ProjectTemplate) -> List[Dict[str, str]]:
        """توليد المخاطر وخطط التخفيف"""
        
        risks = [
            {
                "risk": "تأخير في التطوير",
                "probability": "متوسط",
                "impact": "متوسط",
                "mitigation": "تقسيم المشروع لمراحل صغيرة ومراجعة دورية"
            },
            {
                "risk": "منافسة قوية في السوق",
                "probability": template.competition_level,
                "impact": "عالي",
                "mitigation": "التركيز على ميزة تنافسية فريدة وخدمة عملاء ممتازة"
            },
            {
                "risk": "تجاوز الميزانية",
                "probability": "متوسط",
                "impact": "متوسط",
                "mitigation": "مراقبة دقيقة للمصروفات ووضع احتياطي 20%"
            }
        ]
        
        # مخاطر خاصة بالفئة
        if template.category == "saas":
            risks.append({
                "risk": "صعوبة في اكتساب العملاء",
                "probability": "متوسط",
                "impact": "عالي",
                "mitigation": "استراتيجية تسويق رقمي قوية وعروض تجريبية مجانية"
            })
        elif template.difficulty_level == "hard":
            risks.append({
                "risk": "تعقيد تقني غير متوقع",
                "probability": "متوسط",
                "impact": "عالي",
                "mitigation": "إجراء دراسة جدوى تقنية مفصلة وتطوير نموذج أولي"
            })
        
        return risks
    
    def _generate_fallback_idea(self) -> Dict[str, Any]:
        """توليد فكرة احتياطية عندما تكون جميع القوالب مرفوضة"""
        
        fallback_ideas = [
            {
                "title": "أداة تحسين الإنتاجية الشخصية",
                "description": "تطوير أداة بسيطة تساعد الأفراد في تنظيم مهامهم اليومية وتحسين إنتاجيتهم",
                "category": "tool"
            },
            {
                "title": "منصة تعلم البرمجة التفاعلية",
                "description": "إنشاء منصة تعليمية تفاعلية لتعلم أساسيات البرمجة للمبتدئين",
                "category": "saas"
            },
            {
                "title": "بوت مساعد للمطورين",
                "description": "تطوير بوت يساعد المطورين في العثور على حلول للمشاكل البرمجية الشائعة",
                "category": "bot"
            }
        ]
        
        selected = random.choice(fallback_ideas)
        
        return {
            "id": f"fallback_idea_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "title": selected["title"],
            "description": selected["description"],
            "category": selected["category"],
            "template_id": "fallback",
            "problem_statement": "حاجة عامة لحلول تقنية بسيطة ومفيدة",
            "target_market": "المستخدمين العامين",
            "tech_stack": ["Python", "FastAPI", "SQLite", "HTML/CSS/JS"],
            "financial_projection": {
                "estimated_cost": 5000,
                "estimated_revenue": 15000,
                "roi_percentage": 200,
                "development_time_weeks": 4
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated_by": "fallback_generator",
            "note": "فكرة احتياطية - جميع القوالب الأخرى مرفوضة سابقاً"
        }
    
    def get_template_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات القوالب"""
        
        stats = {
            "total_templates": len(self.templates),
            "templates_by_category": {},
            "templates_by_difficulty": {},
            "average_cost": 0,
            "average_revenue": 0,
            "average_roi": 0,
            "rejected_ideas_count": len(self.rejected_ideas)
        }
        
        total_cost = 0
        total_revenue = 0
        
        for template in self.templates.values():
            # إحصائيات الفئات
            category = template.category
            stats["templates_by_category"][category] = stats["templates_by_category"].get(category, 0) + 1
            
            # إحصائيات الصعوبة
            difficulty = template.difficulty_level
            stats["templates_by_difficulty"][difficulty] = stats["templates_by_difficulty"].get(difficulty, 0) + 1
            
            # إحصائيات مالية
            total_cost += template.estimated_cost
            total_revenue += template.estimated_revenue
        
        if len(self.templates) > 0:
            stats["average_cost"] = total_cost // len(self.templates)
            stats["average_revenue"] = total_revenue // len(self.templates)
            stats["average_roi"] = ((total_revenue - total_cost) / total_cost) * 100
        
        return stats