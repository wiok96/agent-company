#!/usr/bin/env python3
"""
فحص صحة النظام الشامل لـ AACS V0
نقطة تفتيش نهائية للتحقق من اكتمال جميع المكونات
"""
import sys
import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path

# إضافة المسار الجذر للمشروع
sys.path.append(str(Path(__file__).parent.parent))

from core.config import Config
from core.orchestrator import MeetingOrchestrator
from core.memory import MemorySystem
from core.security_manager import SecurityManager
from core.github_issues_manager import GitHubIssuesManager
from core.failure_library import FailureLibrary
from agents.agent_manager import AgentManager


class SystemHealthChecker:
    """فاحص صحة النظام الشامل"""
    
    def __init__(self):
        self.config = Config()
        self.results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": "unknown",
            "components": {},
            "tests": {},
            "recommendations": []
        }
        
        print("🔍 فحص صحة نظام AACS V0")
        print("=" * 60)
    
    def run_full_health_check(self):
        """تشغيل فحص صحة شامل للنظام"""
        
        # 1. فحص المكونات الأساسية
        self._check_core_components()
        
        # 2. فحص التكوين والأسرار
        self._check_configuration()
        
        # 3. فحص الملفات والمجلدات المطلوبة
        self._check_file_structure()
        
        # 4. اختبار الاجتماع التجريبي
        self._test_meeting_workflow()
        
        # 5. فحص لوحة التحكم
        self._check_dashboard()
        
        # 6. فحص الأمان
        self._check_security()
        
        # 7. فحص GitHub Integration
        self._check_github_integration()
        
        # 8. تقييم الحالة العامة
        self._evaluate_overall_status()
        
        # 9. توليد التوصيات
        self._generate_recommendations()
        
        # 10. عرض النتائج
        self._display_results()
        
        return self.results
    
    def _check_core_components(self):
        """فحص المكونات الأساسية"""
        print("\n🧩 فحص المكونات الأساسية...")
        
        components = {
            "config": {"class": Config, "status": "unknown"},
            "memory_system": {"class": MemorySystem, "status": "unknown"},
            "agent_manager": {"class": AgentManager, "status": "unknown"},
            "orchestrator": {"class": MeetingOrchestrator, "status": "unknown"},
            "security_manager": {"class": SecurityManager, "status": "unknown"},
            "failure_library": {"class": FailureLibrary, "status": "unknown"},
            "github_issues_manager": {"class": GitHubIssuesManager, "status": "unknown"}
        }
        
        for component_name, component_info in components.items():
            try:
                if component_name == "config":
                    instance = component_info["class"]()
                elif component_name == "memory_system":
                    instance = component_info["class"](self.config)
                elif component_name == "agent_manager":
                    memory_system = MemorySystem(self.config)
                    instance = component_info["class"](self.config, memory_system)
                elif component_name == "orchestrator":
                    instance = component_info["class"](self.config)
                elif component_name == "security_manager":
                    instance = component_info["class"](self.config)
                elif component_name == "failure_library":
                    memory_system = MemorySystem(self.config)
                    instance = component_info["class"](self.config, memory_system)
                elif component_name == "github_issues_manager":
                    instance = component_info["class"](self.config)
                
                component_info["status"] = "healthy"
                # لا نحفظ instance في النتائج لتجنب مشاكل JSON
                print(f"   ✅ {component_name}: صحي")
                
            except Exception as e:
                component_info["status"] = "error"
                component_info["error"] = str(e)
                print(f"   ❌ {component_name}: خطأ - {e}")
        
        # إزالة المفاتيح غير القابلة للتسلسل
        for component_info in components.values():
            component_info.pop("class", None)
            component_info.pop("instance", None)
        
        self.results["components"] = components
    
    def _check_configuration(self):
        """فحص التكوين والأسرار"""
        print("\n🔧 فحص التكوين والأسرار...")
        
        config_status = {
            "required_secrets": {},
            "optional_secrets": {},
            "environment_vars": {}
        }
        
        # فحص الأسرار المطلوبة
        required_secrets = {
            "GROQ_API_KEY": {"present": bool(os.getenv("GROQ_API_KEY")), "required": True}
        }
        
        optional_secrets = {
            "GITHUB_TOKEN": {"present": bool(os.getenv("GITHUB_TOKEN")), "required": False},
            "TELEGRAM_BOT_TOKEN": {"present": bool(os.getenv("TELEGRAM_BOT_TOKEN")), "required": False},
            "TELEGRAM_CHAT_ID": {"present": bool(os.getenv("TELEGRAM_CHAT_ID")), "required": False}
        }
        
        # فحص الأسرار المطلوبة
        missing_required = []
        for secret, info in required_secrets.items():
            config_status["required_secrets"][secret] = info
            if info["required"] and not info["present"]:
                missing_required.append(secret)
                print(f"   ❌ {secret}: مفقود (مطلوب)")
            else:
                print(f"   ✅ {secret}: متوفر")
        
        # فحص الأسرار الاختيارية
        for secret, info in optional_secrets.items():
            config_status["optional_secrets"][secret] = info
            if info["present"]:
                print(f"   ✅ {secret}: متوفر (اختياري)")
            else:
                print(f"   ⚠️ {secret}: غير متوفر (اختياري)")
        
        config_status["missing_required_secrets"] = missing_required
        self.results["configuration"] = config_status
    
    def _check_file_structure(self):
        """فحص الملفات والمجلدات المطلوبة"""
        print("\n📁 فحص هيكل الملفات...")
        
        required_structure = {
            "directories": [
                "core", "agents", "scripts", "board", "meetings", 
                "memory", "logs", "dashboard", "docs", "tests"
            ],
            "files": [
                "core/config.py", "core/orchestrator.py", "core/memory.py",
                "agents/agent_manager.py", "agents/base_agent.py",
                "dashboard/index.html", "docs/secrets.md",
                "requirements.txt", "README.md"
            ]
        }
        
        structure_status = {"directories": {}, "files": {}}
        
        # فحص المجلدات
        for directory in required_structure["directories"]:
            exists = Path(directory).exists()
            structure_status["directories"][directory] = exists
            status = "✅" if exists else "❌"
            print(f"   {status} {directory}/")
        
        # فحص الملفات
        for file_path in required_structure["files"]:
            exists = Path(file_path).exists()
            structure_status["files"][file_path] = exists
            status = "✅" if exists else "❌"
            print(f"   {status} {file_path}")
        
        self.results["file_structure"] = structure_status
    
    def _test_meeting_workflow(self):
        """اختبار تدفق الاجتماع التجريبي"""
        print("\n🤝 اختبار تدفق الاجتماع التجريبي...")
        
        test_results = {
            "orchestrator_init": False,
            "meeting_execution": False,
            "output_generation": False,
            "error": None
        }
        
        try:
            # إنشاء منسق الاجتماعات
            orchestrator = MeetingOrchestrator(self.config)
            test_results["orchestrator_init"] = True
            print("   ✅ تهيئة منسق الاجتماعات")
            
            # تشغيل اجتماع تجريبي قصير
            session_id = f"health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            agenda = "اختبار صحة النظام - اجتماع تجريبي قصير"
            
            print("   🔄 تشغيل اجتماع تجريبي...")
            result = orchestrator.run_meeting(session_id, agenda, debug_mode=True)
            
            if result.success:
                test_results["meeting_execution"] = True
                print("   ✅ تنفيذ الاجتماع")
                
                # فحص المخرجات
                session_dir = Path("meetings") / session_id
                if session_dir.exists():
                    required_files = ["transcript.jsonl", "minutes.md", "decisions.json"]
                    all_files_exist = all((session_dir / f).exists() for f in required_files)
                    
                    if all_files_exist:
                        test_results["output_generation"] = True
                        print("   ✅ توليد المخرجات")
                    else:
                        print("   ⚠️ بعض ملفات المخرجات مفقودة")
                else:
                    print("   ❌ مجلد الجلسة غير موجود")
            else:
                test_results["error"] = result.error
                print(f"   ❌ فشل تنفيذ الاجتماع: {result.error}")
                
        except Exception as e:
            test_results["error"] = str(e)
            print(f"   ❌ خطأ في اختبار الاجتماع: {e}")
        
        self.results["meeting_test"] = test_results
    
    def _check_dashboard(self):
        """فحص لوحة التحكم"""
        print("\n📊 فحص لوحة التحكم...")
        
        dashboard_status = {
            "html_file": False,
            "css_file": False,
            "js_file": False,
            "data_files": {},
            "accessibility": False
        }
        
        # فحص ملفات لوحة التحكم
        dashboard_files = {
            "index.html": "dashboard/index.html",
            "styles.css": "dashboard/styles.css", 
            "script.js": "dashboard/script.js"
        }
        
        for file_type, file_path in dashboard_files.items():
            exists = Path(file_path).exists()
            dashboard_status[file_type.replace(".", "_")] = exists
            status = "✅" if exists else "❌"
            print(f"   {status} {file_path}")
        
        # فحص ملفات البيانات
        data_files = {
            "board": "board/tasks.json",
            "meetings_index": "meetings/index.json"
        }
        
        for data_type, file_path in data_files.items():
            exists = Path(file_path).exists()
            dashboard_status["data_files"][data_type] = exists
            status = "✅" if exists else "⚠️"
            print(f"   {status} {file_path} (بيانات)")
        
        # فحص إمكانية الوصول (RTL support)
        if Path("dashboard/index.html").exists():
            try:
                with open("dashboard/index.html", 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'dir="rtl"' in content or 'direction: rtl' in content:
                        dashboard_status["accessibility"] = True
                        print("   ✅ دعم اللغة العربية (RTL)")
                    else:
                        print("   ⚠️ دعم اللغة العربية غير مؤكد")
            except Exception as e:
                print(f"   ❌ خطأ في فحص ملف HTML: {e}")
        
        self.results["dashboard"] = dashboard_status
    
    def _check_security(self):
        """فحص الأمان"""
        print("\n🔒 فحص الأمان...")
        
        try:
            security_manager = SecurityManager(self.config)
            
            # فحص الأسرار المكشوفة
            scan_result = security_manager.scan_repository()
            
            security_status = {
                "scan_completed": True,
                "secrets_found": scan_result["total_findings"],
                "high_severity": scan_result["findings_by_severity"]["high"],
                "files_scanned": scan_result["scanned_files"],
                "security_score": "unknown"
            }
            
            # تحديد نقاط الأمان
            if security_status["high_severity"] == 0:
                if security_status["secrets_found"] == 0:
                    security_status["security_score"] = "excellent"
                    print("   ✅ ممتاز: لا توجد أسرار مكشوفة")
                elif security_status["secrets_found"] < 5:
                    security_status["security_score"] = "good"
                    print(f"   ✅ جيد: {security_status['secrets_found']} أسرار منخفضة الخطورة")
                else:
                    security_status["security_score"] = "fair"
                    print(f"   ⚠️ مقبول: {security_status['secrets_found']} أسرار مكشوفة")
            else:
                security_status["security_score"] = "poor"
                print(f"   ❌ ضعيف: {security_status['high_severity']} أسرار عالية الخطورة")
            
            print(f"   📊 تم فحص {security_status['files_scanned']} ملف")
            
        except Exception as e:
            security_status = {
                "scan_completed": False,
                "error": str(e),
                "security_score": "unknown"
            }
            print(f"   ❌ فشل فحص الأمان: {e}")
        
        self.results["security"] = security_status
    
    def _check_github_integration(self):
        """فحص تكامل GitHub"""
        print("\n🐙 فحص تكامل GitHub...")
        
        github_status = {
            "token_available": bool(os.getenv("GITHUB_TOKEN")),
            "manager_init": False,
            "api_connection": False,
            "labels_ready": False
        }
        
        try:
            github_manager = GitHubIssuesManager(self.config)
            github_status["manager_init"] = True
            print("   ✅ تهيئة مدير GitHub Issues")
            
            if github_status["token_available"]:
                # اختبار الاتصال (محاولة بسيطة)
                try:
                    issues = github_manager.get_repository_issues()
                    github_status["api_connection"] = True
                    print(f"   ✅ اتصال API (وجد {len(issues)} issue)")
                    
                    # فحص العلامات
                    if github_manager.ensure_labels_exist():
                        github_status["labels_ready"] = True
                        print("   ✅ العلامات جاهزة")
                    else:
                        print("   ⚠️ مشكلة في العلامات")
                        
                except Exception as e:
                    print(f"   ❌ فشل اتصال API: {e}")
            else:
                print("   ⚠️ GitHub Token غير متوفر")
                
        except Exception as e:
            print(f"   ❌ خطأ في تهيئة GitHub Manager: {e}")
        
        self.results["github_integration"] = github_status
    
    def _evaluate_overall_status(self):
        """تقييم الحالة العامة للنظام"""
        print("\n📈 تقييم الحالة العامة...")
        
        # حساب نقاط الصحة
        health_score = 0
        max_score = 0
        
        # نقاط المكونات الأساسية (40%)
        healthy_components = sum(1 for comp in self.results["components"].values() 
                               if comp["status"] == "healthy")
        total_components = len(self.results["components"])
        component_score = (healthy_components / total_components) * 40
        health_score += component_score
        max_score += 40
        
        # نقاط التكوين (20%)
        missing_required = len(self.results["configuration"]["missing_required_secrets"])
        config_score = (0 if missing_required > 0 else 20)
        health_score += config_score
        max_score += 20
        
        # نقاط اختبار الاجتماع (25%)
        meeting_test = self.results["meeting_test"]
        meeting_score = 0
        if meeting_test["orchestrator_init"]:
            meeting_score += 8
        if meeting_test["meeting_execution"]:
            meeting_score += 10
        if meeting_test["output_generation"]:
            meeting_score += 7
        health_score += meeting_score
        max_score += 25
        
        # نقاط الأمان (15%)
        security = self.results.get("security", {})
        security_score = 0
        if security.get("security_score") == "excellent":
            security_score = 15
        elif security.get("security_score") == "good":
            security_score = 12
        elif security.get("security_score") == "fair":
            security_score = 8
        elif security.get("security_score") == "poor":
            security_score = 3
        health_score += security_score
        max_score += 15
        
        # حساب النسبة المئوية
        health_percentage = (health_score / max_score) * 100 if max_score > 0 else 0
        
        # تحديد الحالة العامة
        if health_percentage >= 90:
            overall_status = "excellent"
            status_icon = "🟢"
            status_text = "ممتاز"
        elif health_percentage >= 75:
            overall_status = "good"
            status_icon = "🟡"
            status_text = "جيد"
        elif health_percentage >= 60:
            overall_status = "fair"
            status_icon = "🟠"
            status_text = "مقبول"
        else:
            overall_status = "poor"
            status_icon = "🔴"
            status_text = "يحتاج تحسين"
        
        self.results["overall_status"] = overall_status
        self.results["health_score"] = health_score
        self.results["max_score"] = max_score
        self.results["health_percentage"] = health_percentage
        
        print(f"   {status_icon} الحالة العامة: {status_text} ({health_percentage:.1f}%)")
        print(f"   📊 النقاط: {health_score:.1f}/{max_score}")
    
    def _generate_recommendations(self):
        """توليد التوصيات لتحسين النظام"""
        recommendations = []
        
        # توصيات المكونات
        for comp_name, comp_info in self.results["components"].items():
            if comp_info["status"] != "healthy":
                recommendations.append(f"إصلاح مشكلة في {comp_name}: {comp_info.get('error', 'خطأ غير محدد')}")
        
        # توصيات التكوين
        missing_secrets = self.results["configuration"]["missing_required_secrets"]
        if missing_secrets:
            recommendations.append(f"إضافة الأسرار المطلوبة: {', '.join(missing_secrets)}")
        
        # توصيات الاجتماع
        meeting_test = self.results["meeting_test"]
        if not meeting_test["meeting_execution"]:
            recommendations.append("إصلاح مشاكل تنفيذ الاجتماعات")
        if not meeting_test["output_generation"]:
            recommendations.append("إصلاح مشاكل توليد مخرجات الاجتماعات")
        
        # توصيات الأمان
        security = self.results.get("security", {})
        if security.get("high_severity", 0) > 0:
            recommendations.append("إزالة الأسرار عالية الخطورة من الملفات")
        
        # توصيات GitHub
        github = self.results.get("github_integration", {})
        if not github.get("token_available"):
            recommendations.append("إضافة GITHUB_TOKEN لتفعيل تكامل GitHub Issues")
        
        # توصيات عامة
        if self.results["health_percentage"] < 90:
            recommendations.append("مراجعة جميع المكونات وإصلاح المشاكل المحددة")
        
        self.results["recommendations"] = recommendations
    
    def _display_results(self):
        """عرض النتائج النهائية"""
        print("\n" + "=" * 60)
        print("📋 تقرير صحة النظام النهائي")
        print("=" * 60)
        
        # الحالة العامة
        status_icons = {
            "excellent": "🟢",
            "good": "🟡", 
            "fair": "🟠",
            "poor": "🔴"
        }
        
        status_texts = {
            "excellent": "ممتاز",
            "good": "جيد",
            "fair": "مقبول", 
            "poor": "يحتاج تحسين"
        }
        
        overall_status = self.results["overall_status"]
        icon = status_icons.get(overall_status, "❓")
        text = status_texts.get(overall_status, "غير محدد")
        
        print(f"\n{icon} الحالة العامة: {text}")
        print(f"📊 نقاط الصحة: {self.results['health_score']:.1f}/{self.results['max_score']} ({self.results['health_percentage']:.1f}%)")
        
        # ملخص المكونات
        print(f"\n🧩 المكونات الأساسية:")
        healthy_count = sum(1 for comp in self.results["components"].values() if comp["status"] == "healthy")
        total_count = len(self.results["components"])
        print(f"   ✅ صحي: {healthy_count}/{total_count}")
        
        # ملخص التكوين
        print(f"\n🔧 التكوين:")
        missing_count = len(self.results["configuration"]["missing_required_secrets"])
        if missing_count == 0:
            print("   ✅ جميع الأسرار المطلوبة متوفرة")
        else:
            print(f"   ❌ {missing_count} أسرار مطلوبة مفقودة")
        
        # ملخص الأمان
        security = self.results.get("security", {})
        if security.get("scan_completed"):
            print(f"\n🔒 الأمان:")
            print(f"   📊 نقاط الأمان: {security.get('security_score', 'غير محدد')}")
            if security.get("high_severity", 0) > 0:
                print(f"   ⚠️ {security['high_severity']} أسرار عالية الخطورة")
        
        # التوصيات
        if self.results["recommendations"]:
            print(f"\n💡 التوصيات ({len(self.results['recommendations'])}):")
            for i, recommendation in enumerate(self.results["recommendations"][:5], 1):
                print(f"   {i}. {recommendation}")
            
            if len(self.results["recommendations"]) > 5:
                print(f"   ... و {len(self.results['recommendations']) - 5} توصيات أخرى")
        
        # خلاصة
        print(f"\n📝 الخلاصة:")
        if overall_status == "excellent":
            print("   🎉 النظام جاهز للإنتاج! جميع المكونات تعمل بشكل ممتاز.")
        elif overall_status == "good":
            print("   👍 النظام يعمل بشكل جيد مع بعض التحسينات البسيطة.")
        elif overall_status == "fair":
            print("   ⚠️ النظام يعمل لكن يحتاج بعض الإصلاحات.")
        else:
            print("   🚨 النظام يحتاج إصلاحات مهمة قبل الاستخدام.")
        
        print("\n" + "=" * 60)
        print(f"✅ اكتمل فحص صحة النظام - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    """الدالة الرئيسية"""
    checker = SystemHealthChecker()
    results = checker.run_full_health_check()
    
    # حفظ النتائج
    results_file = f"system_health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 تم حفظ التقرير المفصل في: {results_file}")
    
    # إرجاع كود الخروج بناءً على الحالة
    if results["overall_status"] in ["excellent", "good"]:
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())