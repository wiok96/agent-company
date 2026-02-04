// AACS V0 Dashboard JavaScript - Enhanced Version

// Configuration
const CONFIG = {
    GITHUB_REPO: window.location.hostname.includes('github.io') 
        ? window.location.pathname.split('/')[1] 
        : 'aacs-v0',
    GITHUB_USER: window.location.hostname.includes('github.io')
        ? window.location.hostname.split('.')[0]
        : 'user',
    REFRESH_INTERVAL: 30000, // 30 seconds
    MAX_MEETINGS_DISPLAY: 10
};

// Global state
let lastRefresh = null;
let refreshTimer = null;
let allTasks = { todo: [], in_progress: [], done: [] };
let allMeetings = [];
let groupedTasks = {};

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
    
    // Task filter buttons
    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('filter-btn')) {
            const filter = event.target.dataset.filter;
            filterTasks(filter);
            
            // Update active button
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
        }
        
        // Meeting details
        if (event.target.classList.contains('meeting-details-btn')) {
            const meetingId = event.target.dataset.meetingId;
            showMeetingDetails(meetingId);
        }
    });
    
    // Task status change via select dropdown
    document.addEventListener('change', function(event) {
        if (event.target.classList.contains('task-status-select')) {
            const taskId = event.target.dataset.taskId;
            const newStatus = event.target.value;
            changeTaskStatus(taskId, newStatus);
        }
    });
    
    // Check if running from file:// protocol and show warning
    if (window.location.protocol === 'file:') {
        setTimeout(() => {
            showNotification('⚠️ يرجى استخدام الخادم المحلي للحصول على أفضل تجربة. شغل start-dashboard.bat', 'error');
        }, 2000);
    }
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
    
    // Show loading state
    showNotification('جاري تشغيل الاجتماع...', 'info');
    
    // Close modal
    closeMeetingModal();
    
    // Simulate meeting execution locally
    // In a real implementation, this would call a local API or Python script
    simulateLocalMeeting(agenda, debug);
}

function simulateLocalMeeting(agenda, debug) {
    // Create a simulated meeting
    const meetingId = `meeting_${new Date().toISOString().replace(/[:.]/g, '').slice(0, 15)}`;
    const newMeeting = {
        session_id: meetingId,
        agenda: agenda,
        timestamp: new Date().toISOString(),
        decisions_count: Math.floor(Math.random() * 3) + 1,
        status: 'in_progress',
        participants: ['ceo', 'cto', 'pm', 'developer', 'qa', 'marketing', 'finance', 'critic', 'chair', 'memory']
    };
    
    // Add to meetings list
    allMeetings.push(newMeeting);
    
    // Simulate meeting progress
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += 10;
        
        if (progress <= 100) {
            showNotification(`تقدم الاجتماع: ${progress}%`, 'info');
        }
        
        if (progress >= 100) {
            clearInterval(progressInterval);
            
            // Mark meeting as completed
            newMeeting.status = 'completed';
            
            // Generate some mock tasks
            generateMockTasks(newMeeting);
            
            showNotification('تم إكمال الاجتماع بنجاح! تم إنشاء مهام جديدة.', 'success');
            
            // Refresh data
            setTimeout(() => {
                refreshData();
            }, 1000);
        }
    }, 2000);
}

function generateMockTasks(meeting) {
    // Generate 2-3 mock tasks from the meeting
    const taskTemplates = [
        'تطوير نموذج أولي لـ',
        'إجراء بحث السوق لـ',
        'إنشاء خطة تسويقية لـ',
        'تحليل المتطلبات التقنية لـ',
        'إعداد دراسة جدوى لـ'
    ];
    
    const numTasks = Math.floor(Math.random() * 3) + 2;
    
    for (let i = 0; i < numTasks; i++) {
        const template = taskTemplates[Math.floor(Math.random() * taskTemplates.length)];
        const taskId = `task_${Date.now()}_${i}`;
        
        const newTask = {
            id: taskId,
            title: `${template} ${meeting.agenda}`,
            description: `مهمة من قرار: ${meeting.agenda}`,
            decision_id: meeting.session_id,
            assigned_to: ['developer', 'pm', 'cto'][Math.floor(Math.random() * 3)],
            created_at: new Date().toISOString(),
            priority: ['high', 'medium', 'low'][Math.floor(Math.random() * 3)],
            status: 'todo'
        };
        
        allTasks.todo.push(newTask);
    }
    
    // Save to localStorage
    localStorage.setItem('aacs_tasks', JSON.stringify(allTasks));
    localStorage.setItem('aacs_meetings', JSON.stringify(allMeetings));
}

// Task management functions
function changeTaskStatus(taskId, newStatus) {
    // Find the task
    let task = null;
    let oldStatus = null;
    
    for (const status in allTasks) {
        const taskIndex = allTasks[status].findIndex(t => t.id === taskId);
        if (taskIndex !== -1) {
            task = allTasks[status][taskIndex];
            oldStatus = status;
            allTasks[status].splice(taskIndex, 1);
            break;
        }
    }
    
    if (task) {
        // Update task status
        task.status = newStatus;
        task.updated_at = new Date().toISOString();
        
        // Add to new status column
        allTasks[newStatus].push(task);
        
        // Update display
        displayTasks(allTasks);
        
        // Show notification
        const statusNames = {
            'todo': 'قيد الانتظار',
            'in_progress': 'قيد التنفيذ', 
            'done': 'مكتملة'
        };
        
        showNotification(`تم نقل المهمة إلى: ${statusNames[newStatus]}`, 'success');
        
        // Save to localStorage (in real implementation, this would save to backend)
        localStorage.setItem('aacs_tasks', JSON.stringify(allTasks));
    }
}

function filterTasks(filter) {
    if (filter === 'all') {
        displayTasks(allTasks);
    } else if (filter === 'project') {
        displayTasksByProject();
    } else {
        // Filter by specific status
        const filteredTasks = {
            todo: filter === 'todo' ? allTasks.todo : [],
            in_progress: filter === 'in_progress' ? allTasks.in_progress : [],
            done: filter === 'done' ? allTasks.done : []
        };
        displayTasks(filteredTasks);
    }
}

function displayTasksByProject() {
    // Group tasks by project/decision
    const grouped = {};
    
    for (const status in allTasks) {
        allTasks[status].forEach(task => {
            const projectName = extractProjectName(task.description);
            if (!grouped[projectName]) {
                grouped[projectName] = { todo: [], in_progress: [], done: [] };
            }
            grouped[projectName][status].push(task);
        });
    }
    
    groupedTasks = grouped;
    displayGroupedTasks(grouped);
}

function extractProjectName(description) {
    // Extract project name from task description
    const match = description.match(/قرار: (.+)/);
    return match ? match[1] : 'مشروع غير محدد';
}

function displayGroupedTasks(grouped) {
    const container = document.querySelector('.board-columns');
    
    container.innerHTML = Object.keys(grouped).map(projectName => `
        <div class="project-group">
            <h3 class="project-title">📁 ${projectName}</h3>
            <div class="project-tasks">
                <div class="task-column">
                    <h4 class="column-title">📝 قيد الانتظار (${grouped[projectName].todo.length})</h4>
                    <div class="tasks-list">
                        ${grouped[projectName].todo.map(task => createTaskHTML(task)).join('')}
                    </div>
                </div>
                <div class="task-column">
                    <h4 class="column-title">⚡ قيد التنفيذ (${grouped[projectName].in_progress.length})</h4>
                    <div class="tasks-list">
                        ${grouped[projectName].in_progress.map(task => createTaskHTML(task)).join('')}
                    </div>
                </div>
                <div class="task-column">
                    <h4 class="column-title">✅ مكتملة (${grouped[projectName].done.length})</h4>
                    <div class="tasks-list">
                        ${grouped[projectName].done.map(task => createTaskHTML(task)).join('')}
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

function createTaskHTML(task) {
    const statusOptions = [
        { value: 'todo', label: 'قيد الانتظار', icon: '📝' },
        { value: 'in_progress', label: 'قيد التنفيذ', icon: '⚡' },
        { value: 'done', label: 'مكتملة', icon: '✅' }
    ];
    
    return `
        <div class="task-item enhanced" data-task-id="${task.id}">
            <div class="task-header">
                <div class="task-title">${task.title}</div>
                <div class="task-actions">
                    <select class="task-status-select" data-task-id="${task.id}">
                        ${statusOptions.map(option => `
                            <option value="${option.value}" ${task.status === option.value ? 'selected' : ''}>
                                ${option.icon} ${option.label}
                            </option>
                        `).join('')}
                    </select>
                </div>
            </div>
            <div class="task-meta">
                <span>👤 ${task.assigned_to || 'غير محدد'}</span>
                <span>⏰ ${formatDate(new Date(task.created_at))}</span>
                <span class="task-priority priority-${task.priority || 'medium'}">
                    ${getPriorityIcon(task.priority)} ${getPriorityLabel(task.priority)}
                </span>
            </div>
        </div>
    `;
}

function getPriorityIcon(priority) {
    const icons = {
        'high': '🔴',
        'medium': '🟡', 
        'low': '🟢'
    };
    return icons[priority] || '🟡';
}

function getPriorityLabel(priority) {
    const labels = {
        'high': 'عالية',
        'medium': 'متوسطة',
        'low': 'منخفضة'
    };
    return labels[priority] || 'متوسطة';
}

// Meeting details function
function showMeetingDetails(meetingId) {
    const meeting = allMeetings.find(m => m.session_id === meetingId);
    if (!meeting) {
        showNotification('لم يتم العثور على تفاصيل الاجتماع', 'error');
        return;
    }
    
    // Create modal for meeting details
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'block';
    modal.innerHTML = `
        <div class="modal-content large">
            <div class="modal-header">
                <h3>📋 تفاصيل الاجتماع</h3>
                <button class="close-btn" onclick="this.closest('.modal').remove()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="meeting-details">
                    <div class="detail-row">
                        <strong>معرف الجلسة:</strong> 
                        <span>${meeting.session_id}</span>
                    </div>
                    <div class="detail-row">
                        <strong>التاريخ:</strong> 
                        <span>${formatDate(new Date(meeting.timestamp))}</span>
                    </div>
                    <div class="detail-row">
                        <strong>الأجندة:</strong> 
                        <span>${meeting.agenda}</span>
                    </div>
                    <div class="detail-row">
                        <strong>عدد القرارات:</strong> 
                        <span>${meeting.decisions_count || 0}</span>
                    </div>
                    <div class="detail-row">
                        <strong>المشاركون:</strong> 
                        <span>${meeting.participants ? meeting.participants.length : 10} وكيل</span>
                    </div>
                    <div class="detail-row">
                        <strong>الحالة:</strong> 
                        <span class="status-badge ${meeting.status || 'completed'}">${meeting.status === 'completed' ? 'مكتمل' : 'قيد التنفيذ'}</span>
                    </div>
                </div>
                <div class="meeting-actions">
                    <button class="btn secondary" onclick="viewMeetingTranscript('${meeting.session_id}')">
                        📄 عرض المحضر
                    </button>
                    <button class="btn secondary" onclick="viewMeetingDecisions('${meeting.session_id}')">
                        🗳️ عرض القرارات
                    </button>
                    <button class="btn secondary" onclick="viewMeetingMinutes('${meeting.session_id}')">
                        📝 عرض المحضر المكتوب
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close modal when clicking outside
    modal.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.remove();
        }
    });
}

function viewMeetingTranscript(meetingId) {
    showNotification('جاري تحميل المحضر...', 'info');
    
    // Try to open transcript file
    const transcriptUrl = `./meetings/${meetingId}/transcript.jsonl`;
    
    fetch(transcriptUrl)
        .then(response => {
            if (response.ok) {
                // Open in new tab/window
                window.open(transcriptUrl, '_blank');
                showNotification('تم فتح المحضر في نافذة جديدة', 'success');
            } else {
                throw new Error('Transcript not found');
            }
        })
        .catch(error => {
            showNotification('لم يتم العثور على المحضر', 'error');
        });
}

function viewMeetingDecisions(meetingId) {
    showNotification('جاري تحميل القرارات...', 'info');
    
    // Try to open decisions file
    const decisionsUrl = `./meetings/${meetingId}/decisions.json`;
    
    fetch(decisionsUrl)
        .then(response => {
            if (response.ok) {
                // Open in new tab/window
                window.open(decisionsUrl, '_blank');
                showNotification('تم فتح القرارات في نافذة جديدة', 'success');
            } else {
                throw new Error('Decisions not found');
            }
        })
        .catch(error => {
            showNotification('لم يتم العثور على القرارات', 'error');
        });
}

function viewMeetingMinutes(meetingId) {
    showNotification('جاري تحميل المحضر المكتوب...', 'info');
    
    // Try to open minutes file
    const minutesUrl = `./meetings/${meetingId}/minutes.md`;
    
    fetch(minutesUrl)
        .then(response => {
            if (response.ok) {
                // Open in new tab/window
                window.open(minutesUrl, '_blank');
                showNotification('تم فتح المحضر المكتوب في نافذة جديدة', 'success');
            } else {
                throw new Error('Minutes not found');
            }
        })
        .catch(error => {
            showNotification('لم يتم العثور على المحضر المكتوب', 'error');
        });
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
        // Check if running from file:// protocol
        if (window.location.protocol === 'file:') {
            // Load from localStorage only when running from file://
            const localMeetings = localStorage.getItem('aacs_meetings');
            if (localMeetings) {
                return JSON.parse(localMeetings);
            }
            
            // Return demo data if no localStorage
            return getDemoMeetingsData();
        }
        
        // Try to load from localStorage first
        const localMeetings = localStorage.getItem('aacs_meetings');
        if (localMeetings) {
            const parsedMeetings = JSON.parse(localMeetings);
            // Also try to load server meetings and merge
            try {
                const response = await fetch('./meetings/index.json');
                if (response.ok) {
                    const data = await response.json();
                    const serverMeetings = data.meetings || [];
                    // Merge and deduplicate
                    const allMeetings = [...serverMeetings, ...parsedMeetings];
                    const uniqueMeetings = allMeetings.filter((meeting, index, self) => 
                        index === self.findIndex(m => m.session_id === meeting.session_id)
                    );
                    return uniqueMeetings;
                }
            } catch (error) {
                console.warn('Could not load server meetings, using local only');
            }
            return parsedMeetings;
        }
        
        // Try to load from meetings/index.json
        const response = await fetch('./meetings/index.json');
        if (response.ok) {
            const data = await response.json();
            const meetings = data.meetings || [];
            localStorage.setItem('aacs_meetings', JSON.stringify(meetings));
            return meetings;
        }
        
        // If index.json doesn't exist, try to build from directory structure
        // This is a fallback - in real implementation, the Python script should create index.json
        const meetings = [];
        
        // Try to load some recent meetings based on known structure
        const meetingDirs = [
            'meeting_20260204_040633',
            'meeting_20260204_040129', 
            'meeting_20260204_035945',
            'meeting_20260204_035753',
            'meeting_20260204_035159'
        ];
        
        for (const dir of meetingDirs) {
            try {
                const minutesResponse = await fetch(`./meetings/${dir}/minutes.md`);
                if (minutesResponse.ok) {
                    const minutesText = await minutesResponse.text();
                    
                    // Extract meeting info from minutes
                    const sessionMatch = minutesText.match(/معرف الجلسة: (.+)/);
                    const agendaMatch = minutesText.match(/الأجندة: (.+)/);
                    const timestampMatch = minutesText.match(/التاريخ والوقت: (.+)/);
                    
                    meetings.push({
                        session_id: sessionMatch ? sessionMatch[1] : dir,
                        agenda: agendaMatch ? agendaMatch[1] : 'اجتماع دوري',
                        timestamp: timestampMatch ? timestampMatch[1] : new Date().toISOString(),
                        decisions_count: 1,
                        status: 'completed',
                        participants: ['ceo', 'cto', 'pm', 'developer', 'qa', 'marketing', 'finance', 'critic', 'chair', 'memory']
                    });
                }
            } catch (error) {
                console.warn(`Could not load meeting ${dir}:`, error);
            }
        }
        
        if (meetings.length > 0) {
            localStorage.setItem('aacs_meetings', JSON.stringify(meetings));
            return meetings;
        }
        
        return getDemoMeetingsData();
        
    } catch (error) {
        console.warn('لم يتم العثور على فهرس الاجتماعات:', error);
        return getDemoMeetingsData();
    }
}

function getDemoMeetingsData() {
    const demoMeetings = [
        {
            session_id: 'demo_meeting_1',
            agenda: 'مناقشة مشاريع جديدة للشركة',
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            decisions_count: 3,
            status: 'completed',
            participants: ['ceo', 'cto', 'pm', 'developer', 'qa', 'marketing', 'finance', 'critic', 'chair', 'memory']
        },
        {
            session_id: 'demo_meeting_2',
            agenda: 'مراجعة الأداء الشهري وتحديد الأولويات',
            timestamp: new Date(Date.now() - 7200000).toISOString(),
            decisions_count: 2,
            status: 'completed',
            participants: ['ceo', 'cto', 'pm', 'developer', 'qa', 'marketing', 'finance', 'critic', 'chair', 'memory']
        },
        {
            session_id: 'demo_meeting_3',
            agenda: 'تطوير استراتيجية التسويق الرقمي',
            timestamp: new Date(Date.now() - 10800000).toISOString(),
            decisions_count: 1,
            status: 'completed',
            participants: ['ceo', 'cto', 'pm', 'developer', 'qa', 'marketing', 'finance', 'critic', 'chair', 'memory']
        }
    ];
    
    localStorage.setItem('aacs_meetings', JSON.stringify(demoMeetings));
    return demoMeetings;
}

async function loadTasksData() {
    try {
        // Check if running from file:// protocol
        if (window.location.protocol === 'file:') {
            // Load from localStorage only when running from file://
            const localTasks = localStorage.getItem('aacs_tasks');
            if (localTasks) {
                return JSON.parse(localTasks);
            }
            
            // Return demo data if no localStorage
            return getDemoTasksData();
        }
        
        // Try to load from localStorage first
        const localTasks = localStorage.getItem('aacs_tasks');
        if (localTasks) {
            const parsedTasks = JSON.parse(localTasks);
            // Merge with server data if available
            try {
                const response = await fetch('./board/tasks.json');
                if (response.ok) {
                    const serverTasks = await response.json();
                    // Merge server tasks with local tasks (local takes precedence)
                    return {
                        todo: [...(serverTasks.todo || []), ...(parsedTasks.todo || [])],
                        in_progress: [...(serverTasks.in_progress || []), ...(parsedTasks.in_progress || [])],
                        done: [...(serverTasks.done || []), ...(parsedTasks.done || [])]
                    };
                }
            } catch (error) {
                console.warn('Could not load server tasks, using local only');
            }
            return parsedTasks;
        }
        
        // Fallback to server data
        const response = await fetch('./board/tasks.json');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        
        // Save to localStorage for future use
        localStorage.setItem('aacs_tasks', JSON.stringify(data));
        
        return data;
    } catch (error) {
        console.warn('لم يتم العثور على بيانات المهام:', error);
        return getDemoTasksData();
    }
}

function getDemoTasksData() {
    return {
        todo: [
            {
                id: 'demo_task_1',
                title: 'تطوير نموذج أولي لمنصة الذكاء الاصطناعي',
                description: 'مهمة من قرار: منصة الذكاء الاصطناعي للشركات الناشئة',
                decision_id: 'demo_decision_1',
                assigned_to: 'developer',
                created_at: new Date().toISOString(),
                priority: 'high',
                status: 'todo'
            },
            {
                id: 'demo_task_2',
                title: 'إجراء بحث السوق للمنتجات الذكية',
                description: 'مهمة من قرار: منصة التجارة الإلكترونية الذكية',
                decision_id: 'demo_decision_2',
                assigned_to: 'marketing',
                created_at: new Date().toISOString(),
                priority: 'medium',
                status: 'todo'
            }
        ],
        in_progress: [
            {
                id: 'demo_task_3',
                title: 'تصميم قاعدة البيانات للنظام',
                description: 'مهمة من قرار: نظام إدارة المواهب الذكي',
                decision_id: 'demo_decision_3',
                assigned_to: 'cto',
                created_at: new Date(Date.now() - 86400000).toISOString(),
                priority: 'high',
                status: 'in_progress'
            }
        ],
        done: [
            {
                id: 'demo_task_4',
                title: 'إعداد بيئة التطوير الأساسية',
                description: 'مهمة من قرار: إعداد البنية التحتية',
                decision_id: 'demo_decision_4',
                assigned_to: 'developer',
                created_at: new Date(Date.now() - 172800000).toISOString(),
                priority: 'medium',
                status: 'done'
            }
        ]
    };
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
    allMeetings = meetings; // Store globally
    
    if (!meetings || meetings.length === 0) {
        meetingsList.innerHTML = '<div class="loading">لا توجد اجتماعات حتى الآن</div>';
        return;
    }
    
    const recentMeetings = meetings.slice(-CONFIG.MAX_MEETINGS_DISPLAY).reverse();
    
    meetingsList.innerHTML = recentMeetings.map(meeting => `
        <div class="meeting-item" onclick="showMeetingDetails('${meeting.session_id}')">
            <div class="meeting-title">${meeting.agenda}</div>
            <div class="meeting-meta">
                <span>📅 ${formatDate(new Date(meeting.timestamp))}</span>
                <span>🗳️ ${meeting.decisions_count || 0} قرارات</span>
                <span>👥 ${meeting.participants ? meeting.participants.length : 10} مشارك</span>
            </div>
            <div class="meeting-actions" onclick="event.stopPropagation()">
                <button class="meeting-details-btn" onclick="showMeetingDetails('${meeting.session_id}')">
                    📋 التفاصيل
                </button>
            </div>
        </div>
    `).join('');
}

function displayTasks(tasks) {
    allTasks = tasks; // Store globally for filtering
    
    // Make sure elements exist before trying to update them
    const todoElement = document.getElementById('todoTasks');
    const inProgressElement = document.getElementById('inProgressTasks');
    const doneElement = document.getElementById('doneTasks');
    
    if (todoElement) {
        displayTaskColumn('todoTasks', tasks.todo || [], 'لا توجد مهام في الانتظار');
    }
    if (inProgressElement) {
        displayTaskColumn('inProgressTasks', tasks.in_progress || [], 'لا توجد مهام قيد التنفيذ');
    }
    if (doneElement) {
        displayTaskColumn('doneTasks', tasks.done || [], 'لا توجد مهام مكتملة');
    }
}

function displayTaskColumn(elementId, tasks, emptyMessage) {
    const element = document.getElementById(elementId);
    
    if (!element) {
        console.warn(`Element ${elementId} not found`);
        return;
    }
    
    if (tasks.length === 0) {
        element.innerHTML = `<div class="loading">${emptyMessage}</div>`;
        return;
    }
    
    element.innerHTML = tasks.map(task => createTaskHTML(task)).join('');
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