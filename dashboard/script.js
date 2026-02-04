// AACS V0 Dashboard JavaScript

// Configuration
const CONFIG = {
    GITHUB_REPO: window.location.hostname.includes('github.io') 
        ? window.location.pathname.split('/')[1] 
        : 'aacs-v0',
    GITHUB_USER: window.location.hostname.includes('github.io')
        ? window.location.hostname.split('.')[0]
        : 'user',
    REFRESH_INTERVAL: 30000, // 30 seconds
    MAX_MEETINGS_DISPLAY: 5
};

// Global state
let lastRefresh = null;
let refreshTimer = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 AACS Dashboard V0 تم التحميل');
    initializeDashboard();
    startAutoRefresh();
});

function initializeDashboard() {
    updateLastRefreshTime();
    loadSystemStatus();
    loadRecentMeetings();
    loadTaskBoard();
    loadAgentsStatus();
    
    // Set up event listeners
    setupEventListeners();
}

function setupEventListeners() {
    // Close modal when clicking outside
    window.onclick = function(event) {
        const modal = document.getElementById('meetingModal');
        if (event.target === modal) {
            closeMeetingModal();
        }
    };
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            closeMeetingModal();
        }
        if (event.ctrlKey && event.key === 'r') {
            event.preventDefault();
            refreshData();
        }
    });
}

function startAutoRefresh() {
    refreshTimer = setInterval(() => {
        refreshData();
    }, CONFIG.REFRESH_INTERVAL);
}

function stopAutoRefresh() {
    if (refreshTimer) {
        clearInterval(refreshTimer);
        refreshTimer = null;
    }
}

// Manual meeting functions
function runManualMeeting() {
    document.getElementById('meetingModal').style.display = 'block';
}

function closeMeetingModal() {
    document.getElementById('meetingModal').style.display = 'none';
}

function confirmRunMeeting() {
    const agenda = document.getElementById('meetingAgenda').value || 'اجتماع يدوي من لوحة التحكم';
    const debug = document.getElementById('debugMode').checked;
    
    // Build GitHub Actions URL
    const baseUrl = `https://github.com/${CONFIG.GITHUB_USER}/${CONFIG.GITHUB_REPO}/actions/workflows/manual-meeting.yml`;
    const params = new URLSearchParams({
        'agenda': agenda,
        'debug': debug.toString(),
        'priority': 'normal',
        'notify_telegram': 'true'
    });
    
    const url = `${baseUrl}?${params.toString()}`;
    
    // Open GitHub Actions in new tab
    window.open(url, '_blank');
    
    // Close modal
    closeMeetingModal();
    
    // Show success message
    showNotification('تم توجيهك إلى GitHub Actions لتشغيل الاجتماع', 'success');
    
    // Refresh data after a delay
    setTimeout(() => {
        refreshData();
    }, 2000);
}

// Data loading functions
async function loadSystemStatus() {
    try {
        updateSystemStatus('نشط', 'success');
        
        // Try to load meetings index
        const meetings = await loadMeetingsIndex();
        if (meetings && meetings.length > 0) {
            const lastMeeting = meetings[meetings.length - 1];
            updateLastMeetingInfo(lastMeeting);
        }
        
        // Calculate next meeting time (every 6 hours)
        updateNextMeetingTime();
        
    } catch (error) {
        console.error('خطأ في تحميل حالة النظام:', error);
        updateSystemStatus('خطأ في التحميل', 'error');
    }
}

async function loadRecentMeetings() {
    try {
        const meetings = await loadMeetingsIndex();
        displayMeetings(meetings);
    } catch (error) {
        console.error('خطأ في تحميل الاجتماعات:', error);
        document.getElementById('meetingsList').innerHTML = 
            '<div class="error">خطأ في تحميل الاجتماعات</div>';
    }
}

async function loadTaskBoard() {
    try {
        const tasks = await loadTasksData();
        displayTasks(tasks);
    } catch (error) {
        console.error('خطأ في تحميل المهام:', error);
        displayTasksError();
    }
}

function loadAgentsStatus() {
    const agents = [
        { id: 'ceo', name: 'الرئيس التنفيذي', icon: '👔', status: 'نشط' },
        { id: 'pm', name: 'مدير المشاريع', icon: '📊', status: 'نشط' },
        { id: 'cto', name: 'المدير التقني', icon: '💻', status: 'نشط' },
        { id: 'developer', name: 'المطور', icon: '⚡', status: 'نشط' },
        { id: 'qa', name: 'ضمان الجودة', icon: '🔍', status: 'نشط' },
        { id: 'marketing', name: 'التسويق', icon: '📈', status: 'نشط' },
        { id: 'finance', name: 'المالية', icon: '💰', status: 'نشط' },
        { id: 'critic', name: 'الناقد', icon: '🤔', status: 'نشط' },
        { id: 'chair', name: 'رئيس الاجتماع', icon: '🎯', status: 'نشط' },
        { id: 'memory', name: 'إدارة الذاكرة', icon: '🧠', status: 'نشط' }
    ];
    
    displayAgents(agents);
}

// Data fetching functions
async function loadMeetingsIndex() {
    try {
        const response = await fetch('./meetings/index.json');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        return data.meetings || [];
    } catch (error) {
        console.warn('لم يتم العثور على فهرس الاجتماعات:', error);
        return [];
    }
}

async function loadTasksData() {
    try {
        const response = await fetch('./board/tasks.json');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.warn('لم يتم العثور على بيانات المهام:', error);
        return { todo: [], in_progress: [], done: [] };
    }
}

// Display functions
function updateSystemStatus(status, type) {
    const statusElement = document.getElementById('systemStatus');
    const statusText = statusElement.querySelector('.status-text');
    const statusDot = statusElement.querySelector('.status-dot');
    
    statusText.textContent = status;
    
    // Update dot color based on status type
    statusDot.style.background = type === 'success' ? '#48bb78' : 
                                 type === 'warning' ? '#ed8936' : '#e53e3e';
}

function updateLastMeetingInfo(meeting) {
    const lastMeetingElement = document.getElementById('lastMeeting');
    if (meeting) {
        const date = new Date(meeting.timestamp);
        lastMeetingElement.textContent = `${formatDate(date)} - ${meeting.agenda}`;
    } else {
        lastMeetingElement.textContent = 'لا توجد اجتماعات سابقة';
    }
}

function updateNextMeetingTime() {
    const nextMeetingElement = document.getElementById('nextMeeting');
    
    // Calculate next meeting (every 6 hours from midnight UTC)
    const now = new Date();
    const utcHours = now.getUTCHours();
    const nextMeetingHour = Math.ceil(utcHours / 6) * 6;
    
    const nextMeeting = new Date(now);
    nextMeeting.setUTCHours(nextMeetingHour, 0, 0, 0);
    
    if (nextMeeting <= now) {
        nextMeeting.setUTCDate(nextMeeting.getUTCDate() + 1);
        nextMeeting.setUTCHours(0, 0, 0, 0);
    }
    
    nextMeetingElement.textContent = formatDate(nextMeeting);
}

function displayMeetings(meetings) {
    const meetingsList = document.getElementById('meetingsList');
    
    if (!meetings || meetings.length === 0) {
        meetingsList.innerHTML = '<div class="loading">لا توجد اجتماعات حتى الآن</div>';
        return;
    }
    
    const recentMeetings = meetings.slice(-CONFIG.MAX_MEETINGS_DISPLAY).reverse();
    
    meetingsList.innerHTML = recentMeetings.map(meeting => `
        <div class="meeting-item">
            <div class="meeting-title">${meeting.agenda}</div>
            <div class="meeting-meta">
                <span>📅 ${formatDate(new Date(meeting.timestamp))}</span>
                <span>🗳️ ${meeting.decisions_count || 0} قرارات</span>
            </div>
        </div>
    `).join('');
}

function displayTasks(tasks) {
    displayTaskColumn('todoTasks', tasks.todo || [], 'لا توجد مهام في الانتظار');
    displayTaskColumn('inProgressTasks', tasks.in_progress || [], 'لا توجد مهام قيد التنفيذ');
    displayTaskColumn('doneTasks', tasks.done || [], 'لا توجد مهام مكتملة');
}

function displayTaskColumn(elementId, tasks, emptyMessage) {
    const element = document.getElementById(elementId);
    
    if (tasks.length === 0) {
        element.innerHTML = `<div class="loading">${emptyMessage}</div>`;
        return;
    }
    
    element.innerHTML = tasks.map(task => `
        <div class="task-item">
            <div class="task-title">${task.title}</div>
            <div class="task-meta">
                👤 ${task.assigned_to || 'غير محدد'} | 
                ⏰ ${formatDate(new Date(task.created_at))}
            </div>
        </div>
    `).join('');
}

function displayTasksError() {
    ['todoTasks', 'inProgressTasks', 'doneTasks'].forEach(id => {
        document.getElementById(id).innerHTML = '<div class="error">خطأ في التحميل</div>';
    });
}

function displayAgents(agents) {
    const agentsGrid = document.getElementById('agentsGrid');
    
    agentsGrid.innerHTML = agents.map(agent => `
        <div class="agent-item">
            <div class="agent-icon">${agent.icon}</div>
            <div class="agent-name">${agent.name}</div>
            <div class="agent-status">${agent.status}</div>
        </div>
    `).join('');
}

// Utility functions
function formatDate(date) {
    return date.toLocaleString('ar-SA', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'UTC'
    });
}

function updateLastRefreshTime() {
    lastRefresh = new Date();
    document.getElementById('lastUpdate').textContent = formatDate(lastRefresh);
}

function showNotification(message, type = 'info') {
    // Simple notification - could be enhanced with a proper notification system
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#48bb78' : type === 'error' ? '#e53e3e' : '#4299e1'};
        color: white;
        border-radius: 8px;
        z-index: 1001;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        font-weight: 500;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Public functions for buttons
function refreshData() {
    console.log('🔄 تحديث البيانات...');
    showNotification('جاري تحديث البيانات...', 'info');
    
    updateLastRefreshTime();
    loadSystemStatus();
    loadRecentMeetings();
    loadTaskBoard();
    
    setTimeout(() => {
        showNotification('تم تحديث البيانات بنجاح', 'success');
    }, 1000);
}

function viewLogs() {
    const logsUrl = `https://github.com/${CONFIG.GITHUB_USER}/${CONFIG.GITHUB_REPO}/actions`;
    window.open(logsUrl, '_blank');
    showNotification('تم فتح صفحة السجلات', 'info');
}

// Error handling
window.addEventListener('error', function(event) {
    console.error('خطأ في لوحة التحكم:', event.error);
    showNotification('حدث خطأ في لوحة التحكم', 'error');
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    stopAutoRefresh();
});