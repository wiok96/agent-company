"""
مدير الإشعارات للأخطاء الحرجة في AACS V0
"""
import json
import requests
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass

from .config import Config
from .logger import setup_logger, SecureLogger


class NotificationLevel(Enum):
    """مستويات الإشعارات"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationChannel(Enum):
    """قنوات الإشعارات"""
    TELEGRAM = "telegram"
    EMAIL = "email"
    WEBHOOK = "webhook"


@dataclass
class NotificationEvent:
    """حدث إشعار"""
    id: str
    timestamp: str
    level: NotificationLevel
    title: str
    message: str
    details: Dict[str, Any]
    session_id: Optional[str] = None
    error_type: Optional[str] = None


class NotificationManager:
    """مدير الإشعارات للأخطاء الحرجة"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = SecureLogger(setup_logger("notification_manager"))
        
        # سياسات الإشعارات
        self.notification_policies = self._load_notification_policies()
        
        # قنوات الإشعارات المفعلة
        self.enabled_channels = self._get_enabled_channels()
        
        self.logger.info("🔔 تم تهيئة مدير الإشعارات")
    
    def _load_notification_policies(self) -> Dict[str, Any]:
        """تحميل سياسات الإشعارات"""
        return {
            "critical_events": [
                "meeting_orchestrator_failure",
                "agent_manager_failure", 
                "memory_system_failure",
                "voting_system_failure",
                "artifact_generation_failure",
                "github_workflow_failure"
            ],
            "error_events": [
                "ai_api_failure",
                "file_system_error",
                "network_timeout",
                "data_corruption"
            ],
            "warning_events": [
                "quorum_failure",
                "partial_artifact_generation",
                "agent_response_timeout"
            ],
            "notification_rules": {
                "critical": {
                    "channels": ["telegram"],
                    "immediate": True,
                    "retry_count": 3
                },
                "error": {
                    "channels": ["telegram"],
                    "immediate": True,
                    "retry_count": 2
                },
                "warning": {
                    "channels": ["telegram"],
                    "immediate": False,
                    "retry_count": 1
                }
            }
        }
    
    def _get_enabled_channels(self) -> List[NotificationChannel]:
        """الحصول على قنوات الإشعارات المفعلة"""
        channels = []
        
        # فحص Telegram
        if (self.config.TELEGRAM_BOT_TOKEN and 
            self.config.TELEGRAM_CHAT_ID and
            self.config.TELEGRAM_BOT_TOKEN != "your_telegram_bot_token"):
            channels.append(NotificationChannel.TELEGRAM)
            self.logger.info("✅ تم تفعيل إشعارات Telegram")
        else:
            self.logger.warning("⚠️ إشعارات Telegram غير مفعلة - تحقق من TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID")
        
        return channels
    
    def send_critical_notification(self, title: str, message: str, 
                                 details: Dict[str, Any] = None, 
                                 session_id: str = None) -> bool:
        """إرسال إشعار حرج"""
        event = NotificationEvent(
            id=f"critical_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=NotificationLevel.CRITICAL,
            title=title,
            message=message,
            details=details or {},
            session_id=session_id,
            error_type="critical_system_failure"
        )
        
        return self._send_notification(event)
    
    def send_error_notification(self, title: str, message: str, 
                              details: Dict[str, Any] = None, 
                              session_id: str = None) -> bool:
        """إرسال إشعار خطأ"""
        event = NotificationEvent(
            id=f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=NotificationLevel.ERROR,
            title=title,
            message=message,
            details=details or {},
            session_id=session_id,
            error_type="system_error"
        )
        
        return self._send_notification(event)
    
    def send_warning_notification(self, title: str, message: str, 
                                details: Dict[str, Any] = None, 
                                session_id: str = None) -> bool:
        """إرسال إشعار تحذير"""
        event = NotificationEvent(
            id=f"warning_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=NotificationLevel.WARNING,
            title=title,
            message=message,
            details=details or {},
            session_id=session_id,
            error_type="system_warning"
        )
        
        return self._send_notification(event)
    
    def notify_meeting_failure(self, session_id: str, error: str, 
                             error_details: Dict[str, Any] = None) -> bool:
        """إشعار فشل الاجتماع"""
        title = "🚨 فشل في تشغيل الاجتماع"
        message = f"""
فشل اجتماع AACS V0

📅 معرف الجلسة: {session_id}
⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
❌ سبب الفشل: {error}

يرجى مراجعة السجلات للحصول على تفاصيل أكثر.
        """.strip()
        
        details = {
            "session_id": session_id,
            "error": error,
            "error_details": error_details or {},
            "github_actions_url": f"https://github.com/{self._get_repo_name()}/actions"
        }
        
        return self.send_critical_notification(title, message, details, session_id)
    
    def notify_voting_failure(self, session_id: str, reason: str, 
                            voting_details: Dict[str, Any] = None) -> bool:
        """إشعار فشل التصويت"""
        title = "⚠️ فشل في عملية التصويت"
        message = f"""
فشل التصويت في اجتماع AACS V0

📅 معرف الجلسة: {session_id}
⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🗳️ سبب الفشل: {reason}

قد يكون السبب عدم وجود النصاب القانوني المطلوب.
        """.strip()
        
        details = {
            "session_id": session_id,
            "failure_reason": reason,
            "voting_details": voting_details or {}
        }
        
        return self.send_warning_notification(title, message, details, session_id)
    
    def notify_ai_api_failure(self, session_id: str, api_error: str, 
                            retry_count: int = 0) -> bool:
        """إشعار فشل API الذكاء الاصطناعي"""
        title = "🤖 فشل في API الذكاء الاصطناعي"
        message = f"""
فشل في الاتصال بـ API الذكاء الاصطناعي

📅 معرف الجلسة: {session_id}
⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔄 عدد المحاولات: {retry_count + 1}
❌ خطأ API: {api_error}

يرجى التحقق من مفتاح API والاتصال بالإنترنت.
        """.strip()
        
        details = {
            "session_id": session_id,
            "api_error": api_error,
            "retry_count": retry_count,
            "api_provider": self.config.AI_PROVIDER
        }
        
        return self.send_error_notification(title, message, details, session_id)
    
    def _send_notification(self, event: NotificationEvent) -> bool:
        """إرسال الإشعار عبر القنوات المفعلة"""
        success = True
        
        for channel in self.enabled_channels:
            try:
                if channel == NotificationChannel.TELEGRAM:
                    channel_success = self._send_telegram_notification(event)
                    success = success and channel_success
                else:
                    self.logger.warning(f"قناة إشعارات غير مدعومة: {channel}")
                    
            except Exception as e:
                self.logger.error(f"فشل في إرسال الإشعار عبر {channel}: {e}")
                success = False
        
        if success:
            self.logger.info(f"✅ تم إرسال الإشعار: {event.title}")
        else:
            self.logger.error(f"❌ فشل في إرسال الإشعار: {event.title}")
        
        return success
    
    def _send_telegram_notification(self, event: NotificationEvent) -> bool:
        """إرسال إشعار عبر Telegram"""
        try:
            # تنسيق الرسالة
            formatted_message = self._format_telegram_message(event)
            
            # إرسال الرسالة
            url = f"https://api.telegram.org/bot{self.config.TELEGRAM_BOT_TOKEN}/sendMessage"
            
            payload = {
                "chat_id": self.config.TELEGRAM_CHAT_ID,
                "text": formatted_message,
                "parse_mode": "HTML",
                "disable_web_page_preview": False
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                self.logger.info("✅ تم إرسال إشعار Telegram بنجاح")
                return True
            else:
                self.logger.error(f"فشل إرسال إشعار Telegram: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"خطأ في إرسال إشعار Telegram: {e}")
            return False
    
    def _format_telegram_message(self, event: NotificationEvent) -> str:
        """تنسيق رسالة Telegram"""
        # رموز المستويات
        level_icons = {
            NotificationLevel.CRITICAL: "🚨",
            NotificationLevel.ERROR: "❌", 
            NotificationLevel.WARNING: "⚠️",
            NotificationLevel.INFO: "ℹ️"
        }
        
        icon = level_icons.get(event.level, "📢")
        
        # تنسيق الرسالة الأساسية
        message = f"""<b>{icon} {event.title}</b>

{event.message}

<b>📊 تفاصيل إضافية:</b>
• <b>المستوى:</b> {event.level.value.upper()}
• <b>الوقت:</b> {datetime.fromisoformat(event.timestamp.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S UTC')}
• <b>معرف الحدث:</b> <code>{event.id}</code>"""
        
        # إضافة معرف الجلسة إذا كان متوفراً
        if event.session_id:
            message += f"\n• <b>معرف الجلسة:</b> <code>{event.session_id}</code>"
        
        # إضافة روابط مفيدة
        repo_name = self._get_repo_name()
        if repo_name:
            message += f"\n\n<b>🔗 روابط مفيدة:</b>"
            message += f"\n• <a href='https://github.com/{repo_name}/actions'>GitHub Actions</a>"
            message += f"\n• <a href='https://{repo_name.split('/')[0]}.github.io/{repo_name.split('/')[1]}'>لوحة التحكم</a>"
            
            if event.session_id:
                message += f"\n• <a href='https://github.com/{repo_name}/tree/main/meetings/{event.session_id}'>ملفات الجلسة</a>"
        
        # إضافة تفاصيل إضافية إذا كانت متوفرة
        if event.details:
            important_details = []
            
            if "error" in event.details:
                important_details.append(f"• <b>الخطأ:</b> <code>{event.details['error']}</code>")
            
            if "failure_reason" in event.details:
                important_details.append(f"• <b>سبب الفشل:</b> {event.details['failure_reason']}")
            
            if "api_provider" in event.details:
                important_details.append(f"• <b>مزود API:</b> {event.details['api_provider']}")
            
            if important_details:
                message += f"\n\n<b>📋 تفاصيل تقنية:</b>\n" + "\n".join(important_details)
        
        return message
    
    def _get_repo_name(self) -> Optional[str]:
        """الحصول على اسم المستودع من متغيرات البيئة أو Git"""
        import os
        
        # محاولة الحصول من متغيرات البيئة
        github_repo = os.getenv('GITHUB_REPOSITORY')
        if github_repo:
            return github_repo
        
        # محاولة الحصول من Git
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'config', '--get', 'remote.origin.url'],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                url = result.stdout.strip()
                # استخراج اسم المستودع من URL
                if 'github.com' in url:
                    if url.endswith('.git'):
                        url = url[:-4]
                    
                    if url.startswith('https://github.com/'):
                        return url.replace('https://github.com/', '')
                    elif url.startswith('git@github.com:'):
                        return url.replace('git@github.com:', '')
        
        except Exception:
            pass
        
        return None
    
    def test_notification_system(self) -> bool:
        """اختبار نظام الإشعارات"""
        self.logger.info("🧪 اختبار نظام الإشعارات...")
        
        test_title = "🧪 اختبار نظام الإشعارات"
        test_message = f"""
هذه رسالة اختبار لنظام الإشعارات في AACS V0.

⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
✅ النظام يعمل بشكل صحيح!

إذا وصلتك هذه الرسالة، فإن نظام الإشعارات مُعد بشكل صحيح.
        """.strip()
        
        test_details = {
            "test_type": "system_test",
            "channels_enabled": [channel.value for channel in self.enabled_channels],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return self.send_warning_notification(test_title, test_message, test_details)