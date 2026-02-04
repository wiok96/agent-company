# دليل إعداد الأمان لنظام AACS V0

## نظرة عامة

يتضمن نظام AACS V0 مدير أمان شامل يوفر:
- إدارة آمنة للأسرار والمفاتيح
- تنقية السجلات من البيانات الحساسة
- التحكم في الوصول القائم على الأدوار
- فحص المستودع للأسرار المكشوفة

## إعداد GitHub Secrets

### الأسرار المطلوبة

#### 1. GROQ_API_KEY (مطلوب)
- **الوصف**: مفتاح API لخدمة Groq للذكاء الاصطناعي
- **التنسيق**: `gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- **كيفية الحصول عليه**:
  1. اذهب إلى [Groq Console](https://console.groq.com/)
  2. أنشئ حساب أو سجل دخول
  3. اذهب إلى API Keys
  4. أنشئ مفتاح جديد
  5. انسخ المفتاح (يبدأ بـ `gsk_`)

#### 2. TELEGRAM_BOT_TOKEN (اختياري)
- **الوصف**: رمز بوت Telegram للإشعارات
- **التنسيق**: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`
- **كيفية الحصول عليه**:
  1. ابحث عن @BotFather في Telegram
  2. أرسل `/newbot`
  3. اتبع التعليمات لإنشاء البوت
  4. احفظ الرمز المرسل

#### 3. TELEGRAM_CHAT_ID (اختياري)
- **الوصف**: معرف المحادثة لإرسال الإشعارات
- **التنسيق**: رقم (مثل `-1001234567890`)
- **كيفية الحصول عليه**:
  1. أضف البوت إلى المجموعة أو المحادثة
  2. أرسل رسالة للبوت
  3. اذهب إلى `https://api.telegram.org/bot<TOKEN>/getUpdates`
  4. ابحث عن `chat.id` في الاستجابة

#### 4. GITHUB_TOKEN (اختياري)
- **الوصف**: رمز GitHub للوصول للمستودع
- **التنسيق**: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- **كيفية الحصول عليه**:
  1. اذهب إلى GitHub Settings > Developer settings > Personal access tokens
  2. أنشئ رمز جديد مع الصلاحيات المطلوبة
  3. انسخ الرمز

### إضافة الأسرار إلى GitHub

1. اذهب إلى مستودع GitHub
2. اذهب إلى Settings > Secrets and variables > Actions
3. اضغط على "New repository secret"
4. أدخل اسم السر والقيمة
5. اضغط "Add secret"

### أسماء الأسرار في GitHub

```
GROQ_API_KEY=gsk_your_groq_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
GITHUB_TOKEN=ghp_your_github_token_here
```

## التحكم في الوصول

### أدوار الوكلاء وصلاحياتهم

| الوكيل | الموارد المسموحة | مستوى الوصول |
|--------|------------------|---------------|
| Chair | meetings, decisions, voting, board | ADMIN |
| CEO | meetings, decisions, ideas, board | WRITE/ADMIN |
| CTO | meetings, technical_decisions, security | ADMIN |
| Developer | meetings, technical_tasks, board | WRITE/ADMIN |
| PM | meetings, tasks, board | ADMIN |
| Finance | meetings, financial_data, roi_analysis | ADMIN |
| Marketing | meetings, market_analysis, board | WRITE/READ_ONLY |
| QA | meetings, testing, quality_reports | ADMIN |
| Critic | meetings, evaluations, all_proposals | WRITE/READ_ONLY |
| Memory | all_data, memory_system, backups | READ_ONLY/ADMIN |

### مستويات الوصول

- **READ_ONLY**: قراءة فقط
- **WRITE**: قراءة وكتابة
- **ADMIN**: تحكم كامل
- **SYSTEM**: وصول النظام (أعلى مستوى)

## تنقية السجلات

### البيانات المنقاة تلقائياً

- مفاتيح API
- كلمات المرور
- الرموز المميزة (Tokens)
- المفاتيح الخاصة
- عناوين URL مع بيانات اعتماد
- عناوين البريد الإلكتروني
- أرقام الهواتف

### مثال على التنقية

```
الأصلي: "API Key: gsk_1234567890abcdef, Password: mypassword123"
المنقى: "API Key: [API_KEY_REDACTED], Password: [PASSWORD_REDACTED]"
```

## فحص الأسرار المكشوفة

### الفحص التلقائي

يقوم النظام بفحص المستودع تلقائياً للبحث عن:
- مفاتيح API مكشوفة
- كلمات مرور في الكود
- رموز GitHub
- بيانات اعتماد في URLs
- مفاتيح خاصة

### تشغيل الفحص يدوياً

```python
from core.security_manager import SecurityManager
from core.config import Config

config = Config()
security_manager = SecurityManager(config)

# فحص المستودع
scan_result = security_manager.scan_repository()
print(f"الأسرار المكتشفة: {scan_result['total_findings']}")

# توليد تقرير أمني
report = security_manager.generate_security_report()
```

## أفضل الممارسات الأمنية

### 1. إدارة الأسرار
- ✅ استخدم GitHub Secrets دائماً
- ❌ لا تضع أسرار في الكود مباشرة
- ✅ استخدم متغيرات البيئة
- ❌ لا تكتب أسرار في ملفات التكوين

### 2. السجلات
- ✅ استخدم SecureLogger دائماً
- ✅ راجع السجلات دورياً للتأكد من التنقية
- ❌ لا تسجل بيانات حساسة مباشرة

### 3. التحكم في الوصول
- ✅ امنح أقل صلاحيات مطلوبة
- ✅ راجع صلاحيات الوكلاء دورياً
- ✅ استخدم انتهاء صلاحية للوصول المؤقت

### 4. الفحص الدوري
- ✅ اجري فحص أمني أسبوعياً
- ✅ راجع تقارير الأمان
- ✅ اتبع التوصيات الأمنية

## استكشاف الأخطاء

### مشاكل شائعة

#### 1. "أسرار مطلوبة مفقودة"
- تأكد من إضافة GROQ_API_KEY في GitHub Secrets
- تحقق من صحة تنسيق المفتاح

#### 2. "رفض الوصول"
- تحقق من صلاحيات الوكيل
- راجع قواعد الوصول في SecurityManager

#### 3. "أسرار مكشوفة في الكود"
- احذف الأسرار من الملفات
- أضفها إلى .gitignore
- استخدم GitHub Secrets بدلاً منها

### الحصول على المساعدة

إذا واجهت مشاكل أمنية:
1. راجع السجلات للتفاصيل
2. اجري فحص أمني شامل
3. اتبع التوصيات المقترحة
4. تأكد من تحديث جميع الأسرار

## التحديثات الأمنية

### إضافة أسرار جديدة

1. أضف السر إلى `required_secrets` في SecurityManager
2. حدث وثائق الأمان
3. أضف السر إلى GitHub Secrets
4. اختبر النظام

### تحديث قواعد الوصول

1. عدل `_load_access_rules()` في SecurityManager
2. اختبر الصلاحيات الجديدة
3. وثق التغييرات

### إضافة أنماط تنقية جديدة

1. أضف النمط إلى `sensitive_patterns`
2. اختبر التنقية
3. تحقق من السجلات