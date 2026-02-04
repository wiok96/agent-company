# دليل الأسرار والتكوين - AACS V0

## نظرة عامة

يتطلب نظام الشركة البرمجية الذاتية (AACS) إعداد عدة أسرار في GitHub Secrets لضمان الأمان والعمل الصحيح. جميع الأسرار يجب أن تُحفظ في GitHub Secrets ولا يُسمح بوجودها في الكود أو الملفات.

## GitHub Secrets المطلوبة

### الأسرار الإجبارية

#### 1. AI_PROVIDER
- **الوصف**: مزود خدمة الذكاء الاصطناعي
- **القيم المدعومة**: `groq`, `openai`, `anthropic`
- **القيمة المقترحة لـ V0**: `groq` (مجاني)
- **مثال**: `groq`

#### 2. AI_API_KEY
- **الوصف**: مفتاح API لمزود الذكاء الاصطناعي
- **التنسيق**: يعتمد على المزود
- **للحصول على مفتاح Groq**: https://console.groq.com/keys
- **مثال**: `gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

#### 3. GITHUB_TOKEN
- **الوصف**: رمز GitHub للوصول إلى Issues API
- **الصلاحيات المطلوبة**: `repo`, `issues:write`
- **كيفية الإنشاء**: Settings → Developer settings → Personal access tokens
- **مثال**: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### الأسرار الاختيارية

#### 4. TELEGRAM_BOT_TOKEN (اختياري)
- **الوصف**: رمز بوت Telegram للإشعارات
- **كيفية الإنشاء**: تحدث مع @BotFather على Telegram
- **مثال**: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

#### 5. TELEGRAM_CHAT_ID (اختياري)
- **الوصف**: معرف المحادثة لإرسال الإشعارات
- **كيفية الحصول عليه**: أرسل رسالة للبوت ثم استخدم API للحصول على chat_id
- **مثال**: `123456789`

## إعداد GitHub Secrets

### الخطوات

1. **انتقل إلى إعدادات المستودع**
   ```
   Repository → Settings → Secrets and variables → Actions
   ```

2. **أضف كل سر على حدة**
   - انقر على "New repository secret"
   - أدخل اسم السر بالضبط كما هو مذكور أعلاه
   - أدخل القيمة
   - انقر على "Add secret"

3. **تحقق من الإعداد**
   - تأكد من وجود جميع الأسرار الإجبارية
   - تحقق من صحة أسماء الأسرار (حساسة للأحرف الكبيرة/الصغيرة)

## متغيرات البيئة المحلية

للتطوير المحلي، يمكنك إنشاء ملف `.env` (لن يتم رفعه للمستودع):

```bash
# ملف .env للتطوير المحلي فقط
AI_PROVIDER=groq
AI_API_KEY=your_groq_api_key_here
GITHUB_TOKEN=your_github_token_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

## قالب التكوين

```python
# config.py - قالب التكوين
import os
from typing import Optional

class Config:
    # الأسرار الإجبارية
    AI_PROVIDER: str = os.getenv('AI_PROVIDER', 'groq')
    AI_API_KEY: str = os.getenv('AI_API_KEY', '')
    GITHUB_TOKEN: str = os.getenv('GITHUB_TOKEN', '')
    
    # الأسرار الاختيارية
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID: Optional[str] = os.getenv('TELEGRAM_CHAT_ID')
    
    # إعدادات النظام
    MEETING_INTERVAL_HOURS: int = 6
    MIN_VOTING_PARTICIPANTS: int = 7
    MAX_AGENTS: int = 10
    
    @classmethod
    def validate(cls) -> bool:
        """التحقق من صحة التكوين الإجباري"""
        required = ['AI_API_KEY', 'GITHUB_TOKEN']
        missing = [key for key in required if not getattr(cls, key)]
        
        if missing:
            raise ValueError(f"Missing required secrets: {missing}")
        
        return True
```

## الأمان والممارسات الجيدة

### ✅ افعل
- احفظ جميع الأسرار في GitHub Secrets فقط
- استخدم أسماء أسرار واضحة ومعيارية
- تحقق من صحة الأسرار قبل الاستخدام
- استخدم متغيرات البيئة في الكود المحلي
- نقّي السجلات من أي بيانات حساسة

### ❌ لا تفعل
- لا تضع أسرار في الكود أو الملفات
- لا ترفع ملف `.env` للمستودع
- لا تطبع الأسرار في السجلات
- لا تشارك الأسرار في التعليقات أو الوثائق
- لا تستخدم أسرار ضعيفة أو قديمة

## استكشاف الأخطاء

### خطأ: "Missing required secrets"
- تحقق من وجود جميع الأسرار الإجبارية في GitHub Secrets
- تأكد من صحة أسماء الأسرار (حساسة للأحرف)

### خطأ: "Invalid API key"
- تحقق من صحة مفتاح API
- تأكد من أن المفتاح لم ينته صلاحيته
- تحقق من أن المزود صحيح

### خطأ: "GitHub API access denied"
- تحقق من صلاحيات GitHub Token
- تأكد من أن الرمز لم ينته صلاحيته

## الدعم

للحصول على المساعدة:
1. راجع سجلات GitHub Actions للأخطاء التفصيلية
2. تحقق من صحة جميع الأسرار المطلوبة
3. تأكد من صحة التكوين باستخدام `Config.validate()`

---

**ملاحظة**: هذا الدليل خاص بالنسخة V0. قد تتغير المتطلبات في النسخ المستقبلية.