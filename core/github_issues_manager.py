"""
مدير GitHub Issues لنظام AACS V0
تحويل المهام إلى GitHub Issues تلقائياً مع العلامات والتصنيف
"""
import os
import json
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from .config import Config
from .logger import setup_logger, SecureLogger


class IssuePriority(Enum):
    """أولوية المهمة"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueType(Enum):
    """نوع المهمة"""
    FEATURE = "feature"
    BUG = "bug"
    ENHANCEMENT = "enhancement"
    DOCUMENTATION = "documentation"
    TASK = "task"
    RESEARCH = "research"


@dataclass
class GitHubIssue:
    """معلومات GitHub Issue"""
    title: str
    body: str
    labels: List[str]
    assignees: List[str] = None
    milestone: Optional[str] = None
    priority: IssuePriority = IssuePriority.MEDIUM
    issue_type: IssueType = IssueType.TASK
    session_id: Optional[str] = None
    task_id: Optional[str] = None


@dataclass
class IssueCreationResult:
    """نتيجة إنشاء Issue"""
    success: bool
    issue_number: Optional[int] = None
    issue_url: Optional[str] = None
    error: Optional[str] = None


class GitHubIssuesManager:
    """مدير GitHub Issues"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = SecureLogger(setup_logger("github_issues"))
        
        # إعدادات GitHub
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repo_owner = os.getenv('GITHUB_REPOSITORY_OWNER', 'your-username')
        self.repo_name = os.getenv('GITHUB_REPOSITORY_NAME', 'agent-company')
        
        # إعداد headers للطلبات
        self.headers = {
            'Authorization': f'token {self.github_token}' if self.github_token else '',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
        
        # تحقق من التكوين
        self._validate_configuration()
        
        # تحميل قوالب العلامات
        self.label_templates = self._initialize_label_templates()
        
        self.logger.info("📋 تم تهيئة مدير GitHub Issues")
    
    def _validate_configuration(self):
        """التحقق من صحة التكوين"""
        if not self.github_token:
            self.logger.warning("⚠️ GITHUB_TOKEN غير متوفر - سيتم تعطيل إنشاء Issues")
            return
        
        # اختبار الاتصال بـ GitHub API
        try:
            response = requests.get(
                f'https://api.github.com/repos/{self.repo_owner}/{self.repo_name}',
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("✅ تم التحقق من الاتصال بـ GitHub API")
            else:
                self.logger.error(f"❌ فشل في الاتصال بـ GitHub API: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"❌ خطأ في الاتصال بـ GitHub API: {e}")
    
    def _initialize_label_templates(self) -> Dict[str, Dict[str, str]]:
        """تهيئة قوالب العلامات"""
        return {
            # علامات الأولوية
            "priority:critical": {
                "name": "priority:critical",
                "color": "d73a49",
                "description": "أولوية حرجة - يتطلب اهتمام فوري"
            },
            "priority:high": {
                "name": "priority:high", 
                "color": "e36209",
                "description": "أولوية عالية"
            },
            "priority:medium": {
                "name": "priority:medium",
                "color": "fbca04",
                "description": "أولوية متوسطة"
            },
            "priority:low": {
                "name": "priority:low",
                "color": "0e8a16",
                "description": "أولوية منخفضة"
            },
            
            # علامات النوع
            "type:feature": {
                "name": "type:feature",
                "color": "a2eeef",
                "description": "ميزة جديدة"
            },
            "type:bug": {
                "name": "type:bug",
                "color": "d73a49",
                "description": "خطأ في النظام"
            },
            "type:enhancement": {
                "name": "type:enhancement",
                "color": "84b6eb",
                "description": "تحسين على ميزة موجودة"
            },
            "type:documentation": {
                "name": "type:documentation",
                "color": "0075ca",
                "description": "تحديث الوثائق"
            },
            "type:task": {
                "name": "type:task",
                "color": "7057ff",
                "description": "مهمة عامة"
            },
            "type:research": {
                "name": "type:research",
                "color": "d4c5f9",
                "description": "بحث وتحليل"
            },
            
            # علامات الوكلاء
            "agent:ceo": {
                "name": "agent:ceo",
                "color": "ff6b6b",
                "description": "مهمة CEO"
            },
            "agent:cto": {
                "name": "agent:cto",
                "color": "4ecdc4",
                "description": "مهمة CTO"
            },
            "agent:developer": {
                "name": "agent:developer",
                "color": "45b7d1",
                "description": "مهمة Developer"
            },
            "agent:pm": {
                "name": "agent:pm",
                "color": "96ceb4",
                "description": "مهمة PM"
            },
            "agent:finance": {
                "name": "agent:finance",
                "color": "feca57",
                "description": "مهمة Finance"
            },
            "agent:marketing": {
                "name": "agent:marketing",
                "color": "ff9ff3",
                "description": "مهمة Marketing"
            },
            "agent:qa": {
                "name": "agent:qa",
                "color": "54a0ff",
                "description": "مهمة QA"
            },
            
            # علامات الحالة
            "status:todo": {
                "name": "status:todo",
                "color": "ededed",
                "description": "لم تبدأ بعد"
            },
            "status:in-progress": {
                "name": "status:in-progress",
                "color": "fbca04",
                "description": "قيد التنفيذ"
            },
            "status:review": {
                "name": "status:review",
                "color": "0052cc",
                "description": "قيد المراجعة"
            },
            "status:done": {
                "name": "status:done",
                "color": "0e8a16",
                "description": "مكتملة"
            },
            
            # علامات خاصة
            "aacs:meeting": {
                "name": "aacs:meeting",
                "color": "b60205",
                "description": "مهمة من اجتماع AACS"
            },
            "aacs:automated": {
                "name": "aacs:automated",
                "color": "5319e7",
                "description": "تم إنشاؤها تلقائياً"
            }
        }
    
    def ensure_labels_exist(self) -> bool:
        """التأكد من وجود العلامات المطلوبة في المستودع"""
        if not self.github_token:
            return False
        
        try:
            # الحصول على العلامات الموجودة
            response = requests.get(
                f'https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/labels',
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code != 200:
                self.logger.error(f"فشل في الحصول على العلامات: {response.status_code}")
                return False
            
            existing_labels = {label['name'] for label in response.json()}
            
            # إنشاء العلامات المفقودة
            created_count = 0
            for label_name, label_info in self.label_templates.items():
                if label_name not in existing_labels:
                    if self._create_label(label_info):
                        created_count += 1
            
            if created_count > 0:
                self.logger.info(f"✅ تم إنشاء {created_count} علامة جديدة")
            
            return True
            
        except Exception as e:
            self.logger.error(f"خطأ في إنشاء العلامات: {e}")
            return False
    
    def _create_label(self, label_info: Dict[str, str]) -> bool:
        """إنشاء علامة جديدة"""
        try:
            response = requests.post(
                f'https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/labels',
                headers=self.headers,
                json=label_info,
                timeout=10
            )
            
            if response.status_code == 201:
                return True
            else:
                self.logger.warning(f"فشل في إنشاء العلامة {label_info['name']}: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"خطأ في إنشاء العلامة {label_info['name']}: {e}")
            return False
    
    def convert_task_to_issue(self, task_data: Dict[str, Any], 
                            session_id: str = None) -> IssueCreationResult:
        """تحويل مهمة إلى GitHub Issue"""
        try:
            # استخراج معلومات المهمة
            issue = self._parse_task_data(task_data, session_id)
            
            # إنشاء Issue
            return self._create_github_issue(issue)
            
        except Exception as e:
            self.logger.error(f"فشل في تحويل المهمة إلى Issue: {e}")
            return IssueCreationResult(success=False, error=str(e))
    
    def _parse_task_data(self, task_data: Dict[str, Any], session_id: str = None) -> GitHubIssue:
        """تحليل بيانات المهمة وتحويلها إلى GitHubIssue"""
        
        # استخراج العنوان والوصف
        title = task_data.get('title', task_data.get('description', 'مهمة جديدة'))[:100]
        description = task_data.get('description', '')
        
        # تحديد النوع والأولوية
        issue_type = self._determine_issue_type(task_data)
        priority = self._determine_priority(task_data)
        
        # إنشاء محتوى Issue
        body = self._generate_issue_body(task_data, session_id)
        
        # تحديد العلامات
        labels = self._generate_labels(task_data, issue_type, priority, session_id)
        
        # تحديد المسؤولين
        assignees = self._determine_assignees(task_data)
        
        return GitHubIssue(
            title=title,
            body=body,
            labels=labels,
            assignees=assignees,
            priority=priority,
            issue_type=issue_type,
            session_id=session_id,
            task_id=task_data.get('id')
        )
    
    def _determine_issue_type(self, task_data: Dict[str, Any]) -> IssueType:
        """تحديد نوع المهمة"""
        description = task_data.get('description', '').lower()
        title = task_data.get('title', '').lower()
        
        # كلمات مفتاحية لتحديد النوع
        type_keywords = {
            IssueType.BUG: ['خطأ', 'باغ', 'مشكلة', 'عطل', 'فشل'],
            IssueType.FEATURE: ['ميزة', 'إضافة', 'تطوير', 'إنشاء', 'بناء'],
            IssueType.ENHANCEMENT: ['تحسين', 'تطوير', 'تحديث', 'تعديل'],
            IssueType.DOCUMENTATION: ['وثائق', 'توثيق', 'شرح', 'دليل'],
            IssueType.RESEARCH: ['بحث', 'دراسة', 'تحليل', 'استكشاف']
        }
        
        text = f"{title} {description}"
        
        for issue_type, keywords in type_keywords.items():
            if any(keyword in text for keyword in keywords):
                return issue_type
        
        return IssueType.TASK  # افتراضي
    
    def _determine_priority(self, task_data: Dict[str, Any]) -> IssuePriority:
        """تحديد أولوية المهمة"""
        description = task_data.get('description', '').lower()
        title = task_data.get('title', '').lower()
        
        # كلمات مفتاحية للأولوية
        priority_keywords = {
            IssuePriority.CRITICAL: ['حرج', 'عاجل', 'فوري', 'حرجة'],
            IssuePriority.HIGH: ['عالي', 'مهم', 'أولوية عالية'],
            IssuePriority.LOW: ['منخفض', 'بسيط', 'أولوية منخفضة']
        }
        
        text = f"{title} {description}"
        
        for priority, keywords in priority_keywords.items():
            if any(keyword in text for keyword in keywords):
                return priority
        
        return IssuePriority.MEDIUM  # افتراضي
    
    def _generate_issue_body(self, task_data: Dict[str, Any], session_id: str = None) -> str:
        """توليد محتوى Issue"""
        body_parts = []
        
        # الوصف الأساسي
        description = task_data.get('description', '')
        if description:
            body_parts.append(f"## الوصف\n{description}")
        
        # معلومات الجلسة
        if session_id:
            body_parts.append(f"## معلومات الجلسة\n- **معرف الجلسة**: `{session_id}`")
            body_parts.append(f"- **تاريخ الإنشاء**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # المسؤول
        assignee = task_data.get('assignee', task_data.get('responsible_agent'))
        if assignee:
            body_parts.append(f"## المسؤول\n- **الوكيل المسؤول**: {assignee}")
        
        # معايير الإنجاز
        completion_criteria = task_data.get('completion_criteria', task_data.get('acceptance_criteria'))
        if completion_criteria:
            if isinstance(completion_criteria, list):
                criteria_text = '\n'.join([f"- {criterion}" for criterion in completion_criteria])
            else:
                criteria_text = str(completion_criteria)
            body_parts.append(f"## معايير الإنجاز\n{criteria_text}")
        
        # تفاصيل إضافية
        if task_data.get('estimated_hours'):
            body_parts.append(f"## التقدير\n- **الساعات المقدرة**: {task_data['estimated_hours']}")
        
        if task_data.get('dependencies'):
            deps = ', '.join(task_data['dependencies'])
            body_parts.append(f"## التبعيات\n- {deps}")
        
        # معلومات النظام
        body_parts.append("---")
        body_parts.append("*تم إنشاء هذا Issue تلقائياً بواسطة نظام AACS V0*")
        
        return '\n\n'.join(body_parts)
    
    def _generate_labels(self, task_data: Dict[str, Any], issue_type: IssueType, 
                        priority: IssuePriority, session_id: str = None) -> List[str]:
        """توليد العلامات للمهمة"""
        labels = []
        
        # علامة النوع
        labels.append(f"type:{issue_type.value}")
        
        # علامة الأولوية
        labels.append(f"priority:{priority.value}")
        
        # علامة الوكيل المسؤول
        assignee = task_data.get('assignee', task_data.get('responsible_agent', '')).lower()
        if assignee in ['ceo', 'cto', 'developer', 'pm', 'finance', 'marketing', 'qa']:
            labels.append(f"agent:{assignee}")
        
        # علامة الحالة
        status = task_data.get('status', 'todo').lower()
        if status in ['todo', 'in-progress', 'review', 'done']:
            labels.append(f"status:{status}")
        
        # علامات خاصة بـ AACS
        labels.append("aacs:automated")
        if session_id:
            labels.append("aacs:meeting")
        
        # علامات إضافية بناءً على المحتوى
        description = task_data.get('description', '').lower()
        if 'api' in description:
            labels.append("component:api")
        if 'ui' in description or 'واجهة' in description:
            labels.append("component:ui")
        if 'database' in description or 'قاعدة بيانات' in description:
            labels.append("component:database")
        
        return labels
    
    def _determine_assignees(self, task_data: Dict[str, Any]) -> List[str]:
        """تحديد المسؤولين عن المهمة"""
        assignees = []
        
        # الوكيل المسؤول الأساسي
        assignee = task_data.get('assignee', task_data.get('responsible_agent'))
        if assignee:
            # تحويل أسماء الوكلاء إلى أسماء مستخدمين GitHub (إذا كانت متوفرة)
            github_usernames = {
                'ceo': os.getenv('GITHUB_USERNAME_CEO'),
                'cto': os.getenv('GITHUB_USERNAME_CTO'),
                'developer': os.getenv('GITHUB_USERNAME_DEVELOPER'),
                'pm': os.getenv('GITHUB_USERNAME_PM')
            }
            
            github_username = github_usernames.get(assignee.lower())
            if github_username:
                assignees.append(github_username)
        
        return assignees
    
    def _create_github_issue(self, issue: GitHubIssue) -> IssueCreationResult:
        """إنشاء GitHub Issue"""
        if not self.github_token:
            return IssueCreationResult(
                success=False, 
                error="GitHub token غير متوفر"
            )
        
        try:
            # إعداد بيانات Issue
            issue_data = {
                'title': issue.title,
                'body': issue.body,
                'labels': issue.labels
            }
            
            if issue.assignees:
                issue_data['assignees'] = issue.assignees
            
            # إرسال الطلب
            response = requests.post(
                f'https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/issues',
                headers=self.headers,
                json=issue_data,
                timeout=30
            )
            
            if response.status_code == 201:
                issue_info = response.json()
                self.logger.info(f"✅ تم إنشاء Issue #{issue_info['number']}: {issue.title}")
                
                return IssueCreationResult(
                    success=True,
                    issue_number=issue_info['number'],
                    issue_url=issue_info['html_url']
                )
            else:
                error_msg = f"فشل في إنشاء Issue: {response.status_code}"
                if response.text:
                    try:
                        error_data = response.json()
                        error_msg += f" - {error_data.get('message', '')}"
                    except:
                        pass
                
                self.logger.error(error_msg)
                return IssueCreationResult(success=False, error=error_msg)
                
        except Exception as e:
            error_msg = f"خطأ في إنشاء Issue: {e}"
            self.logger.error(error_msg)
            return IssueCreationResult(success=False, error=error_msg)
    
    def convert_tasks_from_board(self, board_file: str = "board/tasks.json") -> List[IssueCreationResult]:
        """تحويل المهام من ملف board إلى GitHub Issues"""
        results = []
        
        try:
            board_path = Path(board_file)
            if not board_path.exists():
                self.logger.warning(f"ملف board غير موجود: {board_file}")
                return results
            
            with open(board_path, 'r', encoding='utf-8') as f:
                board_data = json.load(f)
            
            # التأكد من وجود العلامات
            self.ensure_labels_exist()
            
            # تحويل المهام
            tasks = board_data.get('tasks', [])
            for task in tasks:
                # تجاهل المهام المكتملة
                if task.get('status', '').lower() == 'done':
                    continue
                
                result = self.convert_task_to_issue(task, board_data.get('session_id'))
                results.append(result)
                
                # تأخير بسيط لتجنب rate limiting
                import time
                time.sleep(1)
            
            successful_count = sum(1 for r in results if r.success)
            self.logger.info(f"✅ تم تحويل {successful_count}/{len(results)} مهمة إلى GitHub Issues")
            
        except Exception as e:
            self.logger.error(f"فشل في تحويل المهام من board: {e}")
        
        return results
    
    def update_issue_status(self, issue_number: int, new_status: str) -> bool:
        """تحديث حالة Issue"""
        if not self.github_token:
            return False
        
        try:
            # تحديد العلامات الجديدة
            status_label = f"status:{new_status.lower()}"
            
            # الحصول على Issue الحالي
            response = requests.get(
                f'https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/issues/{issue_number}',
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code != 200:
                return False
            
            issue_data = response.json()
            current_labels = [label['name'] for label in issue_data['labels']]
            
            # إزالة علامات الحالة القديمة وإضافة الجديدة
            new_labels = [label for label in current_labels if not label.startswith('status:')]
            new_labels.append(status_label)
            
            # تحديث Issue
            update_response = requests.patch(
                f'https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/issues/{issue_number}',
                headers=self.headers,
                json={'labels': new_labels},
                timeout=10
            )
            
            if update_response.status_code == 200:
                self.logger.info(f"✅ تم تحديث حالة Issue #{issue_number} إلى {new_status}")
                return True
            
        except Exception as e:
            self.logger.error(f"فشل في تحديث حالة Issue #{issue_number}: {e}")
        
        return False
    
    def get_repository_issues(self, state: str = "open") -> List[Dict[str, Any]]:
        """الحصول على Issues من المستودع"""
        if not self.github_token:
            return []
        
        try:
            response = requests.get(
                f'https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/issues',
                headers=self.headers,
                params={'state': state, 'per_page': 100},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            
        except Exception as e:
            self.logger.error(f"فشل في الحصول على Issues: {e}")
        
        return []
    
    def generate_issues_report(self) -> Dict[str, Any]:
        """توليد تقرير عن Issues"""
        try:
            open_issues = self.get_repository_issues("open")
            closed_issues = self.get_repository_issues("closed")
            
            # تحليل العلامات
            all_issues = open_issues + closed_issues
            label_stats = {}
            agent_stats = {}
            
            for issue in all_issues:
                for label in issue.get('labels', []):
                    label_name = label['name']
                    label_stats[label_name] = label_stats.get(label_name, 0) + 1
                    
                    if label_name.startswith('agent:'):
                        agent = label_name.replace('agent:', '')
                        agent_stats[agent] = agent_stats.get(agent, 0) + 1
            
            return {
                "report_timestamp": datetime.now(timezone.utc).isoformat(),
                "total_issues": len(all_issues),
                "open_issues": len(open_issues),
                "closed_issues": len(closed_issues),
                "label_statistics": label_stats,
                "agent_statistics": agent_stats,
                "aacs_issues": len([i for i in all_issues if any(l['name'] == 'aacs:automated' for l in i.get('labels', []))])
            }
            
        except Exception as e:
            self.logger.error(f"فشل في توليد تقرير Issues: {e}")
            return {"error": str(e)}