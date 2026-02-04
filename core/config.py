"""
تكوين نظام AACS V0
"""
import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class Config:
    """تكوين النظام الأساسي"""
    
    # الأسرار الإجبارية
    AI_PROVIDER: str = os.getenv('AI_PROVIDER', 'groq')
    AI_API_KEY: str = os.getenv('AI_API_KEY', '')
    GITHUB_TOKEN: str = os.getenv('GITHUB_TOKEN', '')
    
    # الأسرار الاختيارية
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID: Optional[str] = os.getenv('TELEGRAM_CHAT_ID')
    
    # إعدادات النظام
    MEETING_INTERVAL_HOURS: int = int(os.getenv('MEETING_INTERVAL_HOURS', '6'))
    MIN_VOTING_PARTICIPANTS: int = int(os.getenv('MIN_VOTING_PARTICIPANTS', '7'))
    MAX_AGENTS: int = int(os.getenv('MAX_AGENTS', '10'))
    
    # إعدادات المسارات
    MEETINGS_DIR: str = 'meetings'
    BOARD_DIR: str = 'board'
    AGENTS_DIR: str = 'agents'
    
    # إعدادات الاختبار
    DEBUG_MODE: bool = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    
    @classmethod
    def validate(cls) -> bool:
        """التحقق من صحة التكوين الإجباري"""
        config = cls()
        
        # التحقق من الأسرار الإجبارية
        required_secrets = {
            'AI_API_KEY': config.AI_API_KEY,
            'GITHUB_TOKEN': config.GITHUB_TOKEN
        }
        
        missing = [key for key, value in required_secrets.items() if not value]
        
        if missing:
            raise ValueError(f"Missing required secrets: {missing}")
        
        # التحقق من صحة AI_PROVIDER
        valid_providers = ['groq', 'openai', 'anthropic']
        if config.AI_PROVIDER not in valid_providers:
            raise ValueError(f"Invalid AI_PROVIDER: {config.AI_PROVIDER}. Must be one of: {valid_providers}")
        
        # التحقق من القيم الرقمية
        if config.MEETING_INTERVAL_HOURS < 1:
            raise ValueError("MEETING_INTERVAL_HOURS must be at least 1")
        
        if config.MIN_VOTING_PARTICIPANTS < 1 or config.MIN_VOTING_PARTICIPANTS > config.MAX_AGENTS:
            raise ValueError(f"MIN_VOTING_PARTICIPANTS must be between 1 and {config.MAX_AGENTS}")
        
        return True
    
    @classmethod
    def get_instance(cls) -> 'Config':
        """الحصول على مثيل التكوين مع التحقق"""
        config = cls()
        config.validate()
        return config


# إعدادات الوكلاء
AGENT_ROLES = [
    'ceo',        # الرئيس التنفيذي
    'pm',         # مدير المشاريع
    'cto',        # المدير التقني
    'developer',  # المطور
    'qa',         # ضمان الجودة
    'marketing',  # التسويق
    'finance',    # المالية
    'critic',     # الناقد
    'chair',      # رئيس الاجتماع
    'memory'      # إدارة الذاكرة
]

# التحقق من عدد الوكلاء
assert len(AGENT_ROLES) == 10, f"يجب أن يكون عدد الوكلاء 10 بالضبط، الحالي: {len(AGENT_ROLES)}"

# إعدادات الاجتماعات
MEETING_ARTIFACTS = [
    'transcript.jsonl',
    'minutes.md',
    'decisions.json',
    'self_reflections',
    'index.json',
    'board/tasks.json'
]

# إعدادات التصويت
VOTING_WEIGHTS = {
    'ceo': 1.5,      # وزن أعلى للرئيس التنفيذي
    'pm': 1.3,       # وزن أعلى لمدير المشاريع
    'cto': 1.3,      # وزن أعلى للمدير التقني
    'developer': 1.2, # وزن أعلى للمطور
    'qa': 1.1,       # وزن أعلى لضمان الجودة
    'marketing': 1.0, # وزن عادي
    'finance': 1.2,   # وزن أعلى للمالية
    'critic': 1.1,    # وزن أعلى للناقد
    'chair': 1.0,     # وزن عادي لرئيس الاجتماع
    'memory': 0.0     # لا يصوت (استشاري فقط)
}

# التحقق من أوزان التصويت
assert set(VOTING_WEIGHTS.keys()) == set(AGENT_ROLES), "أوزان التصويت يجب أن تطابق أدوار الوكلاء"