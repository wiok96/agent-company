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
        """إجراء اجتماع حقيقي مع الوكلاء - يقترحون مشاريع بأنفسهم"""
        self.logger.info("🎭 بدء الاجتماع مع الوكلاء...")
        
        # إعادة تعيين الوكلاء للاجتماع الجديد
        self.agent_manager.reset_all_agents()
        
        transcript = []
        
        # 1. رسالة الافتتاح من رئيس الاجتماع
        opening_context = {
            "meeting_data": meeting_data,
            "expected_response_type": "opening",
            "company_context": "نحن شركة هايتك متخصصة في الحلول التقنية المبتكرة"
        }
        
        opening_msg = self._create_agent_message(
            "chair", 
            opening_context, 
            f"أهلاً وسهلاً بالجميع في اجتماع شركة هايتك. الأجندة اليوم: {meeting_data['agenda']}. كشركة تقنية رائدة، نحتاج لمناقشة مشاريع جديدة ومبتكرة."
        )
        transcript.append(opening_msg)
        
        # 2. طلب اقتراحات من الوكلاء
        brainstorm_context = {
            "meeting_type": "brainstorming", 
            "agenda": meeting_data['agenda'],
            "company_type": "هايتك - حلول تقنية مبتكرة",
            "expected_response_type": "project_suggestion"
        }
        
        suggestion_msg = self._create_agent_message(
            "chair",
            brainstorm_context,
            "أريد من كل وكيل أن يقترح مشروع تقني مبتكر يناسب شركة هايتك. فكروا في مشاكل حقيقية يمكننا حلها."
        )
        transcript.append(suggestion_msg)
        
        # 3. جمع اقتراحات من جميع الوكلاء
        project_suggestions = []
        for agent_id in ["ceo", "cto", "developer", "pm", "marketing"]:  # الوكلاء الأكثر إبداعاً
            suggestion_context = {
                "meeting_type": "project_brainstorming",
                "company_focus": "هايتك - تقنية مبتكرة",
                "expected_response_type": "project_proposal",
                "role_perspective": True
            }
            
            suggestion = self._create_agent_message(
                agent_id,
                suggestion_context,
                f"كـ{AGENT_ROLES[AGENT_ROLES.index(agent_id)]} في شركة هايتك، ما هو المشروع التقني المبتكر الذي تقترحه؟"
            )
            transcript.append(suggestion)
            
            # استخراج الاقتراح
            if "أقترح" in suggestion["message"] or "مشروع" in suggestion["message"]:
                project_suggestions.append({
                    "agent": agent_id,
                    "suggestion": suggestion["message"],
                    "timestamp": suggestion["timestamp"]
                })
        
        # 4. مناقشة الاقتراحات
        discussion_context = {
            "meeting_type": "project_discussion",
            "suggestions": project_suggestions,
            "expected_response_type": "discussion"
        }
        
        discussion_msg = self._create_agent_message(
            "chair",
            discussion_context,
            "الآن دعونا نناقش هذه الاقتراحات. كل وكيل يعطي رأيه في الاقتراحات المطروحة."
        )
        transcript.append(discussion_msg)
        
        # 5. مناقشة من باقي الوكلاء
        for agent_id in ["qa", "finance", "critic", "memory"]:
            discussion_context_agent = {
                "meeting_type": "project_evaluation",
                "suggestions": project_suggestions,
                "expected_response_type": "evaluation",
                "role_perspective": True
            }
            
            evaluation = self._create_agent_message(
                agent_id,
                discussion_context_agent,
                f"ما رأيك في الاقتراحات المطروحة من منظور {agent_id}؟"
            )
            transcript.append(evaluation)
        
        # 6. اختيار أفضل اقتراح للتصويت
        if project_suggestions:
            # اختيار الاقتراح الأول للتصويت (يمكن تحسينه لاحقاً)
            selected_suggestion = project_suggestions[0]
            
            voting_msg = self._create_agent_message(
                "chair",
                {"expected_response_type": "voting_call"},
                f"بناءً على المناقشة، أقترح أن نصوت على: {selected_suggestion['suggestion'][:100]}..."
            )
            transcript.append(voting_msg)
            
            # 7. التصويت
            proposal_for_voting = {
                "title": self._extract_project_title(selected_suggestion['suggestion']),
                "description": selected_suggestion['suggestion'],
                "proposed_by": selected_suggestion['agent']
            }
            
            votes = self.agent_manager.conduct_voting(proposal_for_voting)
            
            for agent_id, vote in votes.items():
                vote_msg = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "agent": agent_id,
                    "message": f"صوتي: {vote}",
                    "type": "vote",
                    "proposal_context": proposal_for_voting
                }
                transcript.append(vote_msg)
            
            # 8. إعلان النتيجة
            voting_result = self.agent_manager.calculate_voting_result(votes)
            
            result_msg = self._create_agent_message(
                "chair",
                {"expected_response_type": "result"},
                f"نتيجة التصويت: {voting_result['outcome']} بنسبة {voting_result['approval_percentage']:.1f}%"
            )
            transcript.append(result_msg)
        
        # 9. الخاتمة
        closing_msg = self._create_agent_message(
            "chair",
            {"expected_response_type": "closing"},
            "شكراً للجميع على الأفكار المبتكرة والمناقشة البناءة. هذا ما نتوقعه من شركة هايتك الرائدة."
        )
        transcript.append(closing_msg)
        
        return transcript
    
    def _extract_project_title(self, suggestion_text: str) -> str:
        """استخراج عنوان المشروع من اقتراح الوكيل"""
        # البحث عن أنماط شائعة
        if "أقترح" in suggestion_text:
            parts = suggestion_text.split("أقترح")
            if len(parts) > 1:
                title_part = parts[1].strip()
                # أخذ أول جملة
                title = title_part.split('.')[0].split('،')[0]
                return title[:80]  # تحديد الطول
        
        # إذا لم نجد نمط واضح، نأخذ أول 50 حرف
        return suggestion_text[:50] + "..." if len(suggestion_text) > 50 else suggestion_text
    
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
        
        # البحث عن الاقتراحات والتصويت
        proposals = [entry for entry in transcript if entry.get("type") == "proposal"]
        votes = {}
        proposal_context = None
        
        # جمع الأصوات وسياق المشروع
        for entry in transcript:
            if entry.get("type") == "vote":
                agent_id = entry["agent"]
                vote_text = entry["message"].replace("صوتي: ", "")
                votes[agent_id] = vote_text
                
                # الحصول على سياق المشروع من أول صوت
                if proposal_context is None and "proposal_context" in entry:
                    proposal_context = entry["proposal_context"]
        
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
                "project_details": proposal_context if proposal_context else {},
                "votes": votes,
                "outcome": voting_result["outcome"],
                "voting_details": voting_result,
                "roi": roi_analysis,
                "action_items": self._generate_action_items(title, voting_result["outcome"])
            }
            decisions.append(decision)
        
        return decisions
    
    def _calculate_simple_roi(self, project_title: str) -> Dict[str, Any]:
        """حساب ROI واقعي للمشروع بناءً على نوعه"""
        
        # تقديرات واقعية بناءً على نوع المشروع الفعلي
        if "مراقبة الخوادم" in project_title:
            roi_data = {
                "estimated_cost": 1500,
                "projected_revenue": 5000,
                "development_time_weeks": 3,
                "market_size": "متوسط - شركات DevOps",
                "competition": "منخفض - أدوات بسيطة قليلة",
                "monetization": "اشتراك شهري $10-20"
            }
        elif "مكتبة Python" in project_title:
            roi_data = {
                "estimated_cost": 800,
                "projected_revenue": 2000,
                "development_time_weeks": 2,
                "market_size": "كبير - مطوري Python",
                "competition": "عالي - مكتبات كثيرة",
                "monetization": "مفتوح المصدر + دعم مدفوع"
            }
        elif "تحليل استهلاك API" in project_title:
            roi_data = {
                "estimated_cost": 2000,
                "projected_revenue": 8000,
                "development_time_weeks": 4,
                "market_size": "متوسط - شركات APIs",
                "competition": "متوسط - أدوات معقدة موجودة",
                "monetization": "اشتراك $50-100 شهرياً"
            }
        elif "إضافة متصفح" in project_title:
            roi_data = {
                "estimated_cost": 1200,
                "projected_revenue": 3000,
                "development_time_weeks": 3,
                "market_size": "كبير - المطورين والتقنيين",
                "competition": "متوسط - إضافات مماثلة موجودة",
                "monetization": "نسخة مجانية + premium $5/شهر"
            }
        elif "تحويل قواعد البيانات" in project_title:
            roi_data = {
                "estimated_cost": 1800,
                "projected_revenue": 6000,
                "development_time_weeks": 4,
                "market_size": "صغير - مطوري قواعد البيانات",
                "competition": "منخفض - أدوات معقدة فقط",
                "monetization": "ترخيص تجاري + استشارات"
            }
        elif "مشاركة الكود" in project_title:
            roi_data = {
                "estimated_cost": 1000,
                "projected_revenue": 4000,
                "development_time_weeks": 2,
                "market_size": "كبير - المطورين والطلاب",
                "competition": "عالي - GitHub Gist وغيرها",
                "monetization": "إعلانات + حسابات premium"
            }
        else:
            # قالب افتراضي
            roi_data = {
                "estimated_cost": 1500,
                "projected_revenue": 5000,
                "development_time_weeks": 3,
                "market_size": "متوسط",
                "competition": "متوسط",
                "monetization": "غير محدد"
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
                "تشمل تكاليف التطوير الأساسية فقط",
                "تفترض تسويق بسيط وعضوي",
                "العائد متوقع خلال 6-12 شهر"
            ]
        }
    
    def _generate_action_items(self, project_title: str, outcome: str) -> List[str]:
        """توليد عناصر عمل محددة وقابلة للتنفيذ بناءً على القرار"""
        
        if outcome == "approved":
            # تحديد نوع المشروع من العنوان
            if "مراقبة الخوادم" in project_title:
                return [
                    "إنشاء مستودع GitHub جديد للمشروع",
                    "كتابة مواصفات API لمراقبة الخوادم",
                    "تطوير نموذج أولي لمراقبة خادم واحد",
                    "إنشاء قاعدة بيانات SQLite لحفظ البيانات",
                    "تطوير واجهة CLI أساسية للتحكم"
                ]
            elif "مكتبة Python" in project_title:
                return [
                    "إنشاء هيكل مكتبة Python معياري",
                    "كتابة وثائق API الأساسية",
                    "تطوير وحدة قراءة ملفات JSON/YAML",
                    "إنشاء اختبارات وحدة شاملة",
                    "نشر النسخة الأولى على PyPI"
                ]
            elif "تحليل استهلاك API" in project_title:
                return [
                    "تصميم قاعدة بيانات لتخزين بيانات API",
                    "تطوير نظام جمع البيانات من APIs",
                    "إنشاء واجهة ويب بسيطة للعرض",
                    "تطوير مخططات بيانية للإحصائيات",
                    "إضافة نظام تنبيهات للاستهلاك العالي"
                ]
            elif "إضافة متصفح" in project_title:
                return [
                    "إنشاء manifest.json للإضافة",
                    "تطوير واجهة popup للحفظ السريع",
                    "إنشاء نظام تصنيف تلقائي للمقالات",
                    "تطوير محرك بحث داخلي",
                    "اختبار الإضافة على Chrome و Firefox"
                ]
            elif "تحويل قواعد البيانات" in project_title:
                return [
                    "تطوير محلل مخططات قواعد البيانات",
                    "إنشاء نظام تحويل البيانات",
                    "تطوير واجهة CLI مع معاملات",
                    "إضافة دعم للجداول الكبيرة",
                    "كتابة دليل استخدام مفصل"
                ]
            elif "مشاركة الكود" in project_title:
                return [
                    "تصميم قاعدة بيانات للكود المؤقت",
                    "تطوير API لحفظ واسترجاع الكود",
                    "إنشاء واجهة ويب بسيطة وسريعة",
                    "تطوير نظام انتهاء الصلاحية التلقائي",
                    "إضافة دعم لغات البرمجة المختلفة"
                ]
            else:
                # مهام عامة للمشاريع غير المحددة
                return [
                    f"إنشاء مستودع GitHub لمشروع {project_title}",
                    "كتابة مواصفات تقنية مفصلة",
                    "تطوير النموذج الأولي الأول",
                    "إنشاء اختبارات أساسية",
                    "توثيق طريقة الاستخدام"
                ]
        elif outcome == "rejected":
            return [
                f"مراجعة أسباب رفض مشروع {project_title}",
                "البحث عن حلول بديلة أو تحسينات",
                "إعادة تقييم الجدوى التقنية والاقتصادية",
                "جمع المزيد من آراء المستخدمين المحتملين"
            ]
        else:
            return [
                f"إجراء بحث إضافي حول مشروع {project_title}",
                "جمع المزيد من المعلومات التقنية",
                "تحليل المنافسين والحلول الموجودة",
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