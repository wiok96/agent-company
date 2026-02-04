"""
مدير الأمان العملي لـ AACS V0
نظام شامل لإدارة الأسرار وتنقية السجلات والتحكم في الوصول
"""
import os
import re
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Union
from dataclasses import dataclass
from enum import Enum

from .config import Config
from .logger import setup_logger, SecureLogger


class AccessLevel(Enum):
    """مستويات الوصول"""
    READ_ONLY = "read_only"
    WRITE = "write"
    ADMIN = "admin"
    SYSTEM = "system"


class SecretType(Enum):
    """أنواع الأسرار"""
    API_KEY = "api_key"
    TOKEN = "token"
    PASSWORD = "password"
    DATABASE_URL = "database_url"
    WEBHOOK_URL = "webhook_url"
    PRIVATE_KEY = "private_key"
    CERTIFICATE = "certificate"


@dataclass
class AccessRule:
    """قاعدة الوصول"""
    agent_id: str
    resource: str
    access_level: AccessLevel
    conditions: Dict[str, Any] = None
    expires_at: Optional[str] = None


@dataclass
class SecretInfo:
    """معلومات السر"""
    name: str
    secret_type: SecretType
    description: str
    required: bool
    env_var_name: str
    github_secret_name: str
    validation_pattern: Optional[str] = None


class SecurityManager:
    """مدير الأمان العملي"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = SecureLogger(setup_logger("security"))
        
        # قواعد الوصول
        self.access_rules = self._load_access_rules()
        
        # أنماط البيانات الحساسة للتنقية
        self.sensitive_patterns = self._initialize_sensitive_patterns()
        
        # معلومات الأسرار المطلوبة
        self.required_secrets = self._define_required_secrets()
        
        # تحقق من الأسرار المطلوبة
        self._validate_secrets()
        
        self.logger.info("🔒 تم تهيئة مدير الأمان العملي")
    
    def _load_access_rules(self) -> Dict[str, List[AccessRule]]:
        """تحميل قواعد الوصول"""
        # قواعد الوصول الافتراضية بناءً على أدوار الوكلاء
        default_rules = {
            "chair": [
                AccessRule("chair", "meetings", AccessLevel.ADMIN),
                AccessRule("chair", "decisions", AccessLevel.ADMIN),
                AccessRule("chair", "voting", AccessLevel.ADMIN),
                AccessRule("chair", "board", AccessLevel.WRITE)
            ],
            "ceo": [
                AccessRule("ceo", "meetings", AccessLevel.WRITE),
                AccessRule("ceo", "decisions", AccessLevel.WRITE),
                AccessRule("ceo", "ideas", AccessLevel.ADMIN),
                AccessRule("ceo", "board", AccessLevel.WRITE)
            ],
            "cto": [
                AccessRule("cto", "meetings", AccessLevel.WRITE),
                AccessRule("cto", "technical_decisions", AccessLevel.ADMIN),
                AccessRule("cto", "security", AccessLevel.ADMIN),
                AccessRule("cto", "board", AccessLevel.WRITE)
            ],
            "developer": [
                AccessRule("developer", "meetings", AccessLevel.WRITE),
                AccessRule("developer", "technical_tasks", AccessLevel.ADMIN),
                AccessRule("developer", "board", AccessLevel.WRITE)
            ],
            "pm": [
                AccessRule("pm", "meetings", AccessLevel.WRITE),
                AccessRule("pm", "tasks", AccessLevel.ADMIN),
                AccessRule("pm", "board", AccessLevel.ADMIN)
            ],
            "finance": [
                AccessRule("finance", "meetings", AccessLevel.WRITE),
                AccessRule("finance", "financial_data", AccessLevel.ADMIN),
                AccessRule("finance", "roi_analysis", AccessLevel.ADMIN)
            ],
            "marketing": [
                AccessRule("marketing", "meetings", AccessLevel.WRITE),
                AccessRule("marketing", "market_analysis", AccessLevel.ADMIN),
                AccessRule("marketing", "board", AccessLevel.READ_ONLY)
            ],
            "qa": [
                AccessRule("qa", "meetings", AccessLevel.WRITE),
                AccessRule("qa", "testing", AccessLevel.ADMIN),
                AccessRule("qa", "quality_reports", AccessLevel.ADMIN)
            ],
            "critic": [
                AccessRule("critic", "meetings", AccessLevel.WRITE),
                AccessRule("critic", "evaluations", AccessLevel.ADMIN),
                AccessRule("critic", "all_proposals", AccessLevel.READ_ONLY)
            ],
            "memory": [
                AccessRule("memory", "all_data", AccessLevel.READ_ONLY),
                AccessRule("memory", "memory_system", AccessLevel.ADMIN),
                AccessRule("memory", "backups", AccessLevel.ADMIN)
            ]
        }
        
        return default_rules
    
    def _initialize_sensitive_patterns(self) -> Dict[str, List[str]]:
        """تهيئة أنماط البيانات الحساسة"""
        return {
            "api_keys": [
                r"(?i)(api[_-]?key|apikey)[\"'\s]*[:=][\"'\s]*([a-zA-Z0-9_-]{20,})",
                r"(?i)(secret[_-]?key|secretkey)[\"'\s]*[:=][\"'\s]*([a-zA-Z0-9_-]{20,})",
                r"(?i)(access[_-]?token|accesstoken)[\"'\s]*[:=][\"'\s]*([a-zA-Z0-9_-]{20,})"
            ],
            "passwords": [
                r"(?i)(password|passwd|pwd)[\"'\s]*[:=][\"'\s]*([^\s\"']{8,})",
                r"(?i)(pass)[\"'\s]*[:=][\"'\s]*([^\s\"']{8,})"
            ],
            "urls_with_credentials": [
                r"(?i)(https?://[^:\s]+:[^@\s]+@[^\s]+)",
                r"(?i)(mongodb://[^:\s]+:[^@\s]+@[^\s]+)",
                r"(?i)(postgres://[^:\s]+:[^@\s]+@[^\s]+)"
            ],
            "private_keys": [
                r"-----BEGIN [A-Z ]+PRIVATE KEY-----[^-]+-----END [A-Z ]+PRIVATE KEY-----",
                r"(?i)(private[_-]?key)[\"'\s]*[:=][\"'\s]*([a-zA-Z0-9+/=]{100,})"
            ],
            "tokens": [
                r"(?i)(bearer[_-]?token|bearertoken)[\"'\s]*[:=][\"'\s]*([a-zA-Z0-9_-]{20,})",
                r"(?i)(auth[_-]?token|authtoken)[\"'\s]*[:=][\"'\s]*([a-zA-Z0-9_-]{20,})",
                r"(?i)(jwt[_-]?token|jwttoken)[\"'\s]*[:=][\"'\s]*([a-zA-Z0-9_.-]{20,})"
            ],
            "github_tokens": [
                r"ghp_[a-zA-Z0-9]{36}",
                r"gho_[a-zA-Z0-9]{36}",
                r"ghu_[a-zA-Z0-9]{36}",
                r"ghs_[a-zA-Z0-9]{36}",
                r"ghr_[a-zA-Z0-9]{36}"
            ],
            "email_addresses": [
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
            ],
            "phone_numbers": [
                r"(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}",
                r"(?:\+?966[-.\s]?)?[0-9]{9}"
            ]
        }
    
    def _define_required_secrets(self) -> Dict[str, SecretInfo]:
        """تعريف الأسرار المطلوبة"""
        return {
            "groq_api_key": SecretInfo(
                name="Groq API Key",
                secret_type=SecretType.API_KEY,
                description="مفتاح API لخدمة Groq للذكاء الاصطناعي",
                required=True,
                env_var_name="GROQ_API_KEY",
                github_secret_name="GROQ_API_KEY",
                validation_pattern=r"gsk_[a-zA-Z0-9]{48}"
            ),
            "telegram_bot_token": SecretInfo(
                name="Telegram Bot Token",
                secret_type=SecretType.TOKEN,
                description="رمز بوت Telegram للإشعارات",
                required=False,
                env_var_name="TELEGRAM_BOT_TOKEN",
                github_secret_name="TELEGRAM_BOT_TOKEN",
                validation_pattern=r"[0-9]{8,10}:[a-zA-Z0-9_-]{35}"
            ),
            "telegram_chat_id": SecretInfo(
                name="Telegram Chat ID",
                secret_type=SecretType.TOKEN,
                description="معرف المحادثة لإرسال الإشعارات",
                required=False,
                env_var_name="TELEGRAM_CHAT_ID",
                github_secret_name="TELEGRAM_CHAT_ID",
                validation_pattern=r"-?[0-9]+"
            ),
            "github_token": SecretInfo(
                name="GitHub Token",
                secret_type=SecretType.TOKEN,
                description="رمز GitHub للوصول للمستودع",
                required=False,
                env_var_name="GITHUB_TOKEN",
                github_secret_name="GITHUB_TOKEN",
                validation_pattern=r"gh[ps]_[a-zA-Z0-9]{36}"
            )
        }
    
    def _validate_secrets(self):
        """التحقق من وجود الأسرار المطلوبة"""
        missing_secrets = []
        invalid_secrets = []
        
        for secret_name, secret_info in self.required_secrets.items():
            env_value = os.getenv(secret_info.env_var_name)
            
            if secret_info.required and not env_value:
                missing_secrets.append(secret_name)
            elif env_value and secret_info.validation_pattern:
                if not re.match(secret_info.validation_pattern, env_value):
                    invalid_secrets.append(secret_name)
        
        if missing_secrets:
            self.logger.error(f"❌ أسرار مطلوبة مفقودة: {missing_secrets}")
        
        if invalid_secrets:
            self.logger.warning(f"⚠️ أسرار بتنسيق غير صحيح: {invalid_secrets}")
        
        if not missing_secrets and not invalid_secrets:
            self.logger.info("✅ جميع الأسرار المطلوبة متوفرة وصحيحة")
    
    def sanitize_log_message(self, message: str) -> str:
        """تنقية رسالة السجل من البيانات الحساسة"""
        sanitized = message
        
        for category, patterns in self.sensitive_patterns.items():
            for pattern in patterns:
                # استبدال البيانات الحساسة بنص آمن
                if category == "api_keys":
                    sanitized = re.sub(pattern, r"\1: [API_KEY_REDACTED]", sanitized)
                elif category == "passwords":
                    sanitized = re.sub(pattern, r"\1: [PASSWORD_REDACTED]", sanitized)
                elif category == "urls_with_credentials":
                    sanitized = re.sub(pattern, "[URL_WITH_CREDENTIALS_REDACTED]", sanitized)
                elif category == "private_keys":
                    sanitized = re.sub(pattern, "[PRIVATE_KEY_REDACTED]", sanitized)
                elif category == "tokens":
                    sanitized = re.sub(pattern, r"\1: [TOKEN_REDACTED]", sanitized)
                elif category == "github_tokens":
                    sanitized = re.sub(pattern, "[GITHUB_TOKEN_REDACTED]", sanitized)
                elif category == "email_addresses":
                    sanitized = re.sub(pattern, "[EMAIL_REDACTED]", sanitized)
                elif category == "phone_numbers":
                    sanitized = re.sub(pattern, "[PHONE_REDACTED]", sanitized)
        
        return sanitized
    
    def sanitize_data_structure(self, data: Union[Dict, List, str, Any]) -> Union[Dict, List, str, Any]:
        """تنقية هيكل البيانات من المعلومات الحساسة"""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                # فحص المفاتيح الحساسة
                if self._is_sensitive_key(key):
                    sanitized[key] = "[REDACTED]"
                else:
                    sanitized[key] = self.sanitize_data_structure(value)
            return sanitized
        
        elif isinstance(data, list):
            return [self.sanitize_data_structure(item) for item in data]
        
        elif isinstance(data, str):
            return self.sanitize_log_message(data)
        
        else:
            return data
    
    def _is_sensitive_key(self, key: str) -> bool:
        """فحص إذا كان المفتاح حساساً"""
        sensitive_keys = [
            "password", "passwd", "pwd", "pass",
            "api_key", "apikey", "secret_key", "secretkey",
            "token", "access_token", "auth_token", "bearer_token",
            "private_key", "privatekey", "certificate", "cert",
            "webhook_url", "database_url", "connection_string",
            "email", "phone", "mobile", "address"
        ]
        
        key_lower = key.lower()
        return any(sensitive in key_lower for sensitive in sensitive_keys)
    
    def check_access(self, agent_id: str, resource: str, access_level: AccessLevel) -> bool:
        """فحص صلاحية الوصول"""
        try:
            agent_rules = self.access_rules.get(agent_id, [])
            
            for rule in agent_rules:
                if rule.resource == resource or rule.resource == "all_data":
                    # فحص انتهاء الصلاحية
                    if rule.expires_at:
                        expiry_time = datetime.fromisoformat(rule.expires_at)
                        if datetime.now(timezone.utc) > expiry_time:
                            continue
                    
                    # فحص مستوى الوصول
                    if self._access_level_sufficient(rule.access_level, access_level):
                        return True
            
            self.logger.warning(f"🚫 رفض الوصول: {agent_id} -> {resource} ({access_level.value})")
            return False
            
        except Exception as e:
            self.logger.error(f"خطأ في فحص الوصول: {e}")
            return False
    
    def _access_level_sufficient(self, granted: AccessLevel, required: AccessLevel) -> bool:
        """فحص إذا كان مستوى الوصول الممنوح كافياً"""
        level_hierarchy = {
            AccessLevel.READ_ONLY: 1,
            AccessLevel.WRITE: 2,
            AccessLevel.ADMIN: 3,
            AccessLevel.SYSTEM: 4
        }
        
        return level_hierarchy.get(granted, 0) >= level_hierarchy.get(required, 0)
    
    def create_secure_log_entry(self, level: str, message: str, 
                              agent_id: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """إنشاء إدخال سجل آمن"""
        # تنقية الرسالة والسياق
        sanitized_message = self.sanitize_log_message(message)
        sanitized_context = self.sanitize_data_structure(context) if context else {}
        
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": sanitized_message,
            "agent_id": agent_id,
            "context": sanitized_context,
            "security_hash": self._generate_security_hash(sanitized_message, agent_id)
        }
        
        return log_entry
    
    def _generate_security_hash(self, message: str, agent_id: str = None) -> str:
        """توليد hash أمني للسجل"""
        content = f"{message}:{agent_id}:{datetime.now().strftime('%Y%m%d')}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def scan_file_for_secrets(self, file_path: str) -> List[Dict[str, Any]]:
        """فحص ملف للبحث عن أسرار مكشوفة"""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            for category, patterns in self.sensitive_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.MULTILINE)
                    
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        
                        findings.append({
                            "file": file_path,
                            "line": line_num,
                            "category": category,
                            "pattern": pattern,
                            "severity": self._get_severity(category),
                            "context": content[max(0, match.start()-50):match.end()+50]
                        })
            
        except Exception as e:
            self.logger.error(f"فشل في فحص الملف {file_path}: {e}")
        
        return findings
    
    def _get_severity(self, category: str) -> str:
        """تحديد خطورة نوع السر المكشوف"""
        high_severity = ["api_keys", "private_keys", "passwords", "github_tokens"]
        medium_severity = ["tokens", "urls_with_credentials"]
        
        if category in high_severity:
            return "high"
        elif category in medium_severity:
            return "medium"
        else:
            return "low"
    
    def scan_repository(self, repo_path: str = ".") -> Dict[str, Any]:
        """فحص المستودع بالكامل للبحث عن أسرار مكشوفة"""
        self.logger.info("🔍 بدء فحص المستودع للأسرار المكشوفة...")
        
        all_findings = []
        scanned_files = 0
        
        # أنواع الملفات المراد فحصها
        file_extensions = ['.py', '.js', '.json', '.yaml', '.yml', '.env', '.txt', '.md', '.sh']
        
        # مجلدات يجب تجاهلها
        ignore_dirs = {'.git', '__pycache__', 'node_modules', '.pytest_cache', 'venv', 'env'}
        
        repo_path = Path(repo_path)
        
        for file_path in repo_path.rglob('*'):
            # تجاهل المجلدات المحددة
            if any(ignore_dir in file_path.parts for ignore_dir in ignore_dirs):
                continue
            
            # فحص الملفات ذات الامتدادات المحددة فقط
            if file_path.is_file() and file_path.suffix in file_extensions:
                findings = self.scan_file_for_secrets(str(file_path))
                all_findings.extend(findings)
                scanned_files += 1
        
        # تجميع النتائج
        summary = {
            "scan_timestamp": datetime.now(timezone.utc).isoformat(),
            "scanned_files": scanned_files,
            "total_findings": len(all_findings),
            "findings_by_severity": {
                "high": len([f for f in all_findings if f["severity"] == "high"]),
                "medium": len([f for f in all_findings if f["severity"] == "medium"]),
                "low": len([f for f in all_findings if f["severity"] == "low"])
            },
            "findings_by_category": {},
            "detailed_findings": all_findings
        }
        
        # إحصائيات الفئات
        for finding in all_findings:
            category = finding["category"]
            summary["findings_by_category"][category] = summary["findings_by_category"].get(category, 0) + 1
        
        # تسجيل النتائج
        if all_findings:
            self.logger.warning(f"⚠️ تم العثور على {len(all_findings)} سر مكشوف محتمل")
            for finding in all_findings:
                if finding["severity"] == "high":
                    self.logger.error(f"🚨 سر عالي الخطورة في {finding['file']}:{finding['line']}")
        else:
            self.logger.info("✅ لم يتم العثور على أسرار مكشوفة")
        
        return summary
    
    def generate_security_report(self) -> Dict[str, Any]:
        """توليد تقرير أمني شامل"""
        self.logger.info("📊 توليد التقرير الأمني...")
        
        # فحص الأسرار المكشوفة
        secrets_scan = self.scan_repository()
        
        # فحص الأسرار المطلوبة
        secrets_status = {}
        for secret_name, secret_info in self.required_secrets.items():
            env_value = os.getenv(secret_info.env_var_name)
            secrets_status[secret_name] = {
                "required": secret_info.required,
                "present": bool(env_value),
                "valid": bool(env_value and secret_info.validation_pattern and 
                            re.match(secret_info.validation_pattern, env_value))
            }
        
        # إحصائيات قواعد الوصول
        access_stats = {
            "total_agents": len(self.access_rules),
            "total_rules": sum(len(rules) for rules in self.access_rules.values()),
            "agents_with_admin_access": len([
                agent for agent, rules in self.access_rules.items()
                if any(rule.access_level == AccessLevel.ADMIN for rule in rules)
            ])
        }
        
        report = {
            "report_timestamp": datetime.now(timezone.utc).isoformat(),
            "security_version": "1.0",
            "secrets_scan": secrets_scan,
            "secrets_configuration": secrets_status,
            "access_control": access_stats,
            "security_recommendations": self._generate_security_recommendations(secrets_scan, secrets_status)
        }
        
        return report
    
    def _generate_security_recommendations(self, secrets_scan: Dict[str, Any], 
                                         secrets_status: Dict[str, Any]) -> List[str]:
        """توليد توصيات أمنية"""
        recommendations = []
        
        # توصيات بناءً على فحص الأسرار
        if secrets_scan["total_findings"] > 0:
            recommendations.append("إزالة جميع الأسرار المكشوفة من الملفات")
            recommendations.append("استخدام GitHub Secrets لتخزين البيانات الحساسة")
            
            if secrets_scan["findings_by_severity"]["high"] > 0:
                recommendations.append("🚨 أولوية عالية: إزالة الأسرار عالية الخطورة فوراً")
        
        # توصيات بناءً على حالة الأسرار
        missing_required = [name for name, status in secrets_status.items() 
                          if status["required"] and not status["present"]]
        
        if missing_required:
            recommendations.append(f"إضافة الأسرار المطلوبة المفقودة: {', '.join(missing_required)}")
        
        invalid_secrets = [name for name, status in secrets_status.items() 
                         if status["present"] and not status["valid"]]
        
        if invalid_secrets:
            recommendations.append(f"تصحيح تنسيق الأسرار: {', '.join(invalid_secrets)}")
        
        # توصيات عامة
        recommendations.extend([
            "مراجعة قواعد الوصول دورياً",
            "تفعيل تنقية السجلات في جميع المكونات",
            "إجراء فحص أمني دوري للمستودع",
            "استخدام أدوات CI/CD لفحص الأسرار تلقائياً"
        ])
        
        return recommendations
    
    def export_security_config(self, output_path: str = "security_config.json") -> str:
        """تصدير تكوين الأمان"""
        try:
            config_data = {
                "required_secrets": {
                    name: {
                        "description": info.description,
                        "required": info.required,
                        "env_var_name": info.env_var_name,
                        "github_secret_name": info.github_secret_name,
                        "type": info.secret_type.value
                    }
                    for name, info in self.required_secrets.items()
                },
                "access_rules": {
                    agent: [
                        {
                            "resource": rule.resource,
                            "access_level": rule.access_level.value,
                            "conditions": rule.conditions,
                            "expires_at": rule.expires_at
                        }
                        for rule in rules
                    ]
                    for agent, rules in self.access_rules.items()
                },
                "sensitive_patterns_count": {
                    category: len(patterns) 
                    for category, patterns in self.sensitive_patterns.items()
                }
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"📄 تم تصدير تكوين الأمان: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"فشل في تصدير تكوين الأمان: {e}")
            return ""