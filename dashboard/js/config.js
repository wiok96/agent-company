/**
 * AACS Dashboard Configuration
 * Contains all configuration constants and settings
 */

const CONFIG = {
    // API Configuration
    API: {
        GITHUB_REPO: 'wiok96/agent-company',
        BASE_URL: 'https://api.github.com/repos/wiok96/agent-company',
        ENDPOINTS: {
            MEETINGS_INDEX: '/contents/meetings/index.json',
            MEETINGS_DIR: '/contents/meetings',
            MEETING_TRANSCRIPT: (sessionId) => `/contents/meetings/${sessionId}/transcript.jsonl`,
            MEETING_DECISIONS: (sessionId) => `/contents/meetings/${sessionId}/decisions.json`,
            MEETING_MINUTES: (sessionId) => `/contents/meetings/${sessionId}/minutes.md`
        }
    },

    // UI Configuration
    UI: {
        REFRESH_INTERVAL: 60000, // 60 seconds
        NOTIFICATION_DURATION: 4000, // 4 seconds
        ANIMATION_DURATION: 1000, // 1 second
        LOAD_TIMEOUT: 10000 // 10 seconds
    },

    // GitHub Actions
    ACTIONS: {
        MEETING_WORKFLOW: 'https://github.com/wiok96/agent-company/actions/workflows/meeting.yml'
    },

    // Default Values
    DEFAULTS: {
        AGENTS_COUNT: 10,
        FALLBACK_MEETINGS: 2,
        FALLBACK_DECISIONS: 2,
        FALLBACK_TASKS: 6
    },

    // Messages
    MESSAGES: {
        AR: {
            LOADING: 'جاري التحميل...',
            ERROR_LOADING: 'خطأ في تحميل البيانات',
            SUCCESS_UPDATE: 'تم تحديث البيانات بنجاح',
            WELCOME: 'مرحباً بك في لوحة تحكم AACS مع البيانات الحقيقية! 🎉',
            MEETING_CONFIRM: 'هل تريد تشغيل اجتماع AACS جديد؟\n\nسيتم فتح GitHub Actions لتشغيل الاجتماع.',
            MEETING_PREPARING: 'جاري تحضير الاجتماع... 🚀',
            MEETING_SUCCESS: 'تم فتح صفحة GitHub Actions. انقر على "Run workflow" لبدء الاجتماع'
        }
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}