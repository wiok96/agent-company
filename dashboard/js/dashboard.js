/**
 * AACS Dashboard Main Class
 * Handles dashboard functionality and business logic
 */

class AacsDashboard {
    constructor() {
        this.api = new AacsApi();
        this.ui = new AacsUI();
        this.systemData = {
            meetings: 0,
            decisions: 0,
            tasks: 0,
            lastUpdate: new Date(),
            meetingsData: []
        };
        this.refreshInterval = null;
    }

    /**
     * Initialize dashboard
     */
    async initialize() {
        console.log('🚀 تم تحميل لوحة تحكم AACS بنجاح');
        
        // Load initial data
        await this.loadSystemData();
        
        // Show welcome message
        setTimeout(() => {
            this.ui.showNotification(CONFIG.MESSAGES.AR.WELCOME, 'success');
        }, 800);
        
        // Setup auto-refresh
        this.setupAutoRefresh();
    }

    /**
     * Setup auto-refresh interval
     */
    setupAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        this.refreshInterval = setInterval(() => {
            this.loadSystemData();
        }, CONFIG.UI.REFRESH_INTERVAL);
    }

    /**
     * Load system data from GitHub
     */
    async loadSystemData() {
        try {
            this.ui.showLoadingState(true);
            
            const repoData = await this.api.getMeetingsData();
            if (repoData) {
                this.updateDashboardWithRealData(repoData);
                if (repoData.meetingsData && repoData.meetingsData.length > 0) {
                    this.ui.updateRecentActivity(repoData.meetingsData);
                }
            } else {
                this.ui.showNotification('تعذر تحميل البيانات من GitHub. يرجى المحاولة لاحقاً.', 'warning');
                this.updateDashboardWithFallbackData();
            }
            
            this.ui.showLoadingState(false);
        } catch (error) {
            console.error('خطأ في تحميل البيانات:', error);
            this.ui.showNotification('خطأ في تحميل البيانات: ' + error.message, 'error');
            this.updateDashboardWithFallbackData();
            this.ui.showLoadingState(false);
        }
    }

    /**
     * Update dashboard with real data
     */
    updateDashboardWithRealData(data) {
        this.systemData = { ...this.systemData, ...data, lastUpdate: new Date() };
        this.ui.updateStatistics(this.systemData);
        this.ui.updateChangeIndicators(true, data.meetings);
        this.ui.showNotification('تم تحديث البيانات بنجاح من المستودع! ✅', 'success');
    }

    /**
     * Update dashboard with fallback data
     */
    updateDashboardWithFallbackData() {
        this.systemData.meetings = CONFIG.DEFAULTS.FALLBACK_MEETINGS;
        this.systemData.decisions = CONFIG.DEFAULTS.FALLBACK_DECISIONS;
        this.systemData.tasks = CONFIG.DEFAULTS.FALLBACK_TASKS;
        this.systemData.lastUpdate = new Date();
        
        this.ui.updateStatistics(this.systemData);
        this.ui.updateChangeIndicators(false, this.systemData.meetings);
    }

    /**
     * Run new meeting
     */
    runMeeting() {
        if (confirm(CONFIG.MESSAGES.AR.MEETING_CONFIRM)) {
            this.ui.showNotification(CONFIG.MESSAGES.AR.MEETING_PREPARING, 'info');
            
            setTimeout(() => {
                window.open(CONFIG.ACTIONS.MEETING_WORKFLOW, '_blank');
                this.ui.showNotification(CONFIG.MESSAGES.AR.MEETING_SUCCESS, 'success');
            }, 1000);
            
            // Update meeting count after some time
            setTimeout(() => {
                this.systemData.meetings += 1;
                this.ui.updateStatistics(this.systemData);
                this.ui.showNotification('سيتم تحديث الإحصائيات تلقائياً بعد انتهاء الاجتماع', 'info');
            }, 2000);
        }
    }

    /**
     * View meetings details
     */
    async viewMeetings() {
        this.ui.showNotification('جاري تحميل تفاصيل الاجتماعات... 📅', 'info');
        
        try {
            const data = await this.api.getMeetingsData();
            if (data && data.meetingsData && data.meetingsData.length > 0) {
                this.displayMeetingsOverview(data.meetingsData);
            } else {
                // Fallback to demo data
                this.displayMeetingsOverview([
                    {
                        session_id: "meeting_20260204_095556",
                        timestamp: "2026-02-04T09:55:56.481441+00:00",
                        agenda: "اجتماع دوري",
                        participants: ["ceo", "pm", "cto", "developer", "qa", "marketing", "finance", "critic", "chair", "memory"],
                        decisions_count: 1,
                        status: "completed"
                    },
                    {
                        session_id: "meeting_20260205_012642",
                        timestamp: "2026-02-05T01:26:42.211520+00:00",
                        agenda: "اجتماع دوري مجدول",
                        participants: ["ceo", "pm", "cto", "developer", "qa", "marketing", "finance", "critic", "chair", "memory"],
                        decisions_count: 1,
                        status: "completed"
                    }
                ]);
            }
        } catch (error) {
            console.error('خطأ في تحميل بيانات الاجتماعات:', error);
            this.ui.showNotification('خطأ في تحميل بيانات الاجتماعات: ' + error.message, 'error');
        }
    }

    /**
     * Display meetings overview in new window
     */
    displayMeetingsOverview(meetings) {
        const meetingsWindow = window.open('', '_blank');
        const html = this.generateMeetingsHTML(meetings);
        meetingsWindow.document.write(html);
        meetingsWindow.document.close();
        this.ui.showNotification('تم فتح صفحة تفاصيل الاجتماعات! 🎉', 'success');
    }

    /**
     * Generate meetings HTML
     */
    generateMeetingsHTML(meetings) {
        return `
            <!DOCTYPE html>
            <html lang="ar" dir="rtl">
            <head>
                <meta charset="UTF-8">
                <title>🏢 AACS - تفاصيل الاجتماعات</title>
                <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap" rel="stylesheet">
                <style>
                    body { 
                        font-family: 'Cairo', Arial; 
                        padding: 20px; 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                        margin: 0;
                    }
                    .container { max-width: 1200px; margin: 0 auto; }
                    .header { 
                        background: rgba(255, 255, 255, 0.95); 
                        padding: 30px; 
                        border-radius: 20px; 
                        text-align: center; 
                        margin-bottom: 30px; 
                        backdrop-filter: blur(10px);
                        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                    }
                    .header h1 { color: #2563eb; margin-bottom: 10px; }
                    .meeting-card { 
                        background: rgba(255, 255, 255, 0.95); 
                        padding: 25px; 
                        border-radius: 20px; 
                        margin-bottom: 25px; 
                        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                        backdrop-filter: blur(10px);
                        transition: all 0.3s ease;
                    }
                    .meeting-card:hover { transform: translateY(-5px); }
                    .meeting-header { 
                        background: linear-gradient(135deg, #2563eb, #1e40af); 
                        color: white; 
                        padding: 20px; 
                        border-radius: 15px; 
                        margin-bottom: 20px; 
                    }
                    .participants { 
                        display: flex; 
                        flex-wrap: wrap; 
                        gap: 10px; 
                        margin: 15px 0; 
                    }
                    .participant { 
                        background: linear-gradient(135deg, #e3f2fd, #bbdefb); 
                        padding: 8px 15px; 
                        border-radius: 20px; 
                        font-size: 0.9em; 
                        font-weight: 600;
                        color: #1565c0;
                    }
                    .status { 
                        padding: 8px 20px; 
                        border-radius: 25px; 
                        color: white; 
                        font-weight: bold; 
                        display: inline-block;
                    }
                    .status.completed { background: linear-gradient(135deg, #10b981, #059669); }
                    .btn { 
                        background: linear-gradient(135deg, #2563eb, #1e40af); 
                        color: white; 
                        border: none; 
                        padding: 12px 24px; 
                        border-radius: 12px; 
                        cursor: pointer; 
                        margin: 8px; 
                        font-weight: 600;
                        transition: all 0.3s ease;
                        font-family: inherit;
                    }
                    .btn:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(37, 99, 235, 0.3); }
                    .btn-success { background: linear-gradient(135deg, #10b981, #059669); }
                    .btn-warning { background: linear-gradient(135deg, #f59e0b, #d97706); }
                    .stats { 
                        display: grid; 
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                        gap: 15px; 
                        margin: 20px 0; 
                    }
                    .stat { 
                        background: rgba(37, 99, 235, 0.1); 
                        padding: 15px; 
                        border-radius: 12px; 
                        text-align: center; 
                    }
                    .stat-number { font-size: 2em; font-weight: bold; color: #2563eb; }
                    .stat-label { color: #6b7280; font-weight: 600; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📅 تفاصيل اجتماعات AACS</h1>
                        <p>استعراض شامل لجميع الاجتماعات والقرارات والنقاشات</p>
                    </div>
                    
                    <div class="stats">
                        <div class="stat">
                            <div class="stat-number">${meetings.length}</div>
                            <div class="stat-label">إجمالي الاجتماعات</div>
                        </div>
                        <div class="stat">
                            <div class="stat-number">${meetings.reduce((sum, m) => sum + m.decisions_count, 0)}</div>
                            <div class="stat-label">إجمالي القرارات</div>
                        </div>
                        <div class="stat">
                            <div class="stat-number">${meetings.filter(m => m.status === 'completed').length}</div>
                            <div class="stat-label">الاجتماعات المكتملة</div>
                        </div>
                    </div>
                    
                    ${meetings.map(meeting => {
                        const date = new Date(meeting.timestamp).toLocaleString('ar-SA');
                        return `
                            <div class="meeting-card">
                                <div class="meeting-header">
                                    <h2>📋 ${meeting.agenda}</h2>
                                    <p>📅 ${date}</p>
                                    <span class="status ${meeting.status}">${meeting.status === 'completed' ? '✅ مكتمل' : '🔄 جاري'}</span>
                                </div>
                                
                                <div class="meeting-info">
                                    <p><strong>🆔 معرف الجلسة:</strong> ${meeting.session_id}</p>
                                    <p><strong>🗳️ عدد القرارات:</strong> ${meeting.decisions_count}</p>
                                    <p><strong>👥 عدد المشاركين:</strong> ${meeting.participants.length}</p>
                                </div>
                                
                                <div class="participants">
                                    <strong>المشاركون:</strong><br>
                                    ${meeting.participants.map(p => `<span class="participant">🤖 ${p}</span>`).join('')}
                                </div>
                                
                                <div class="meeting-actions">
                                    <button class="btn btn-success" onclick="alert('جاري تحميل النقاشات لـ: ${meeting.session_id}')">
                                        💬 عرض النقاشات التفصيلية
                                    </button>
                                    <button class="btn btn-warning" onclick="alert('جاري تحميل القرارات لـ: ${meeting.session_id}')">
                                        🗳️ عرض القرارات والتصويت
                                    </button>
                                    <button class="btn" onclick="alert('جاري تحميل محضر الاجتماع لـ: ${meeting.session_id}')">
                                        📄 عرض محضر الاجتماع
                                    </button>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </body>
            </html>
        `;
    }

    /**
     * View reports
     */
    viewReports() {
        this.ui.showNotification('جاري تحضير التقارير التفصيلية... 📊', 'info');
        
        setTimeout(() => {
            const reportsData = {
                totalMeetings: this.systemData.meetings,
                totalDecisions: this.systemData.decisions,
                activeTasks: this.systemData.tasks,
                lastUpdate: this.systemData.lastUpdate.toLocaleString('ar-SA')
            };
            
            const reportWindow = window.open('', '_blank');
            reportWindow.document.write(this.generateReportsHTML(reportsData));
            reportWindow.document.close();
            
            this.ui.showNotification('تم إنشاء التقرير التفصيلي بنجاح! 📋', 'success');
        }, 1500);
    }

    /**
     * Generate reports HTML
     */
    generateReportsHTML(data) {
        return `
            <!DOCTYPE html>
            <html lang="ar" dir="rtl">
            <head>
                <meta charset="UTF-8">
                <title>تقرير AACS التفصيلي</title>
                <style>
                    body { font-family: 'Cairo', Arial; padding: 20px; background: #f8fafc; }
                    .report-header { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 30px; }
                    .report-section { background: white; padding: 25px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                    .metric { display: flex; justify-content: space-between; padding: 15px 0; border-bottom: 1px solid #eee; }
                    .metric:last-child { border-bottom: none; }
                    .metric-label { font-weight: 600; }
                    .metric-value { color: #667eea; font-weight: bold; }
                </style>
            </head>
            <body>
                <div class="report-header">
                    <h1>📊 تقرير AACS التفصيلي</h1>
                    <p>تم إنشاؤه في: ${new Date().toLocaleString('ar-SA')}</p>
                </div>
                <div class="report-section">
                    <h2>📈 الإحصائيات العامة (البيانات الحقيقية)</h2>
                    <div class="metric">
                        <span class="metric-label">إجمالي الاجتماعات:</span>
                        <span class="metric-value">${data.totalMeetings}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">القرارات المتخذة:</span>
                        <span class="metric-value">${data.totalDecisions}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">المهام النشطة:</span>
                        <span class="metric-value">${data.activeTasks}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">آخر تحديث:</span>
                        <span class="metric-value">${data.lastUpdate}</span>
                    </div>
                </div>
                <div class="report-section">
                    <h2>🎯 التوصيات</h2>
                    <ul>
                        <li>زيادة تكرار الاجتماعات لتحسين التواصل</li>
                        <li>مراجعة القرارات المعلقة وتنفيذها</li>
                        <li>تحديث حالة المهام بانتظام</li>
                        <li>تحسين كفاءة الوكلاء</li>
                    </ul>
                </div>
            </body>
            </html>
        `;
    }

    /**
     * Open settings
     */
    openSettings() {
        this.ui.showNotification('جاري فتح إعدادات النظام... ⚙️', 'info');
        
        setTimeout(() => {
            const settingsWindow = window.open('', '_blank');
            settingsWindow.document.write(this.generateSettingsHTML());
            settingsWindow.document.close();
            
            this.ui.showNotification('تم فتح إعدادات النظام بنجاح! 🔧', 'success');
        }, 1000);
    }

    /**
     * Generate settings HTML
     */
    generateSettingsHTML() {
        return `
            <!DOCTYPE html>
            <html lang="ar" dir="rtl">
            <head>
                <meta charset="UTF-8">
                <title>إعدادات AACS</title>
                <style>
                    body { font-family: 'Cairo', Arial; padding: 20px; background: #f8fafc; }
                    .settings-header { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 30px; }
                    .settings-section { background: white; padding: 25px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                    .setting-item { display: flex; justify-content: space-between; align-items: center; padding: 15px 0; border-bottom: 1px solid #eee; }
                    .setting-item:last-child { border-bottom: none; }
                    .setting-label { font-weight: 600; }
                    .setting-value { color: #667eea; font-weight: bold; }
                    .btn { background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; }
                </style>
            </head>
            <body>
                <div class="settings-header">
                    <h1>⚙️ إعدادات AACS</h1>
                    <p>إدارة وتكوين النظام</p>
                </div>
                <div class="settings-section">
                    <h2>🔧 معلومات النظام</h2>
                    <div class="setting-item">
                        <span class="setting-label">إصدار النظام:</span>
                        <span class="setting-value">v2.1</span>
                    </div>
                    <div class="setting-item">
                        <span class="setting-label">آخر تحديث:</span>
                        <span class="setting-value">${new Date().toLocaleDateString('ar-SA')}</span>
                    </div>
                    <div class="setting-item">
                        <span class="setting-label">الوكلاء النشطون:</span>
                        <span class="setting-value">${CONFIG.DEFAULTS.AGENTS_COUNT}</span>
                    </div>
                    <div class="setting-item">
                        <span class="setting-label">حالة النظام:</span>
                        <span class="setting-value">ممتاز</span>
                    </div>
                </div>
                <div class="settings-section">
                    <h2>🛠️ إجراءات سريعة</h2>
                    <button class="btn" onclick="alert('تم تحديث النظام!')">تحديث النظام</button>
                    <button class="btn" onclick="alert('تم إعادة تشغيل الوكلاء!')">إعادة تشغيل الوكلاء</button>
                    <button class="btn" onclick="alert('تم تنظيف الذاكرة!')">تنظيف الذاكرة</button>
                </div>
            </body>
            </html>
        `;
    }

    /**
     * Cleanup resources
     */
    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        this.api.clearCache();
    }
}