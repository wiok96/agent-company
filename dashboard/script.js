// AACS Enhanced Dashboard JavaScript

// Configuration
const CONFIG = {
    GITHUB_REPO: window.location.hostname.includes('github.io') 
        ? window.location.pathname.split('/')[1] 
        : 'aacs-v0',
    GITHUB_USER: window.location.hostname.includes('github.io')
        ? window.location.hostname.split('.')[0]
        : 'user',
    REFRESH_INTERVAL: 30000,
    MAX_MEETINGS_DISPLAY: 20
};

// Global state
let currentSection = 'overview';
let allMeetings = [];
let allTasks = { todo: [], in_progress: [], done: [] };
let allDecisions = [];
let allAgents = [];

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 AACS Enhanced Dashboard تم التحميل');
    
    // Add GitHub Pages detection
    if (window.location.hostname.includes('github.io')) {
        const repoName = window.location.pathname.split('/')[1];
        console.log('🌐 GitHub Pages detected:', window.location.hostname.split('.')[0] + '/' + repoName);
    }
    
    // Debug CSS loading
    console.log('📱 Screen size:', window.innerWidth + 'x' + window.innerHeight);
    console.log('🎨 Body computed styles:', {
        background: window.getComputedStyle(document.body).background,
        fontFamily: window.getComputedStyle(document.body).fontFamily,
        direction: window.getComputedStyle(document.body).direction
    });
    
    // Check if critical elements exist
    const criticalElements = ['totalMeetings', 'totalDecisions', 'totalTasks'];
    criticalElements.forEach(id => {
        const element = document.getElementById(id);
        console.log(`Element ${id}:`, element ? 'Found' : 'Missing');
    });
    
    initializeDashboard();
    setupEventListeners();
    startAutoRefresh();
});

function initializeDashboard() {
    // Check if CSS is loaded properly
    const bodyStyles = window.getComputedStyle(document.body);
    const background = bodyStyles.background || bodyStyles.backgroundColor;
    
    if (!background || background === 'rgba(0, 0, 0, 0)' || background === 'transparent') {
        console.warn('⚠️ CSS may not be loading properly');
        showNotification('قد تكون هناك مشكلة في تحميل التصميم', 'warning');
    }
    
    // Show loading state
    const loadingElements = document.querySelectorAll('.loading');
    loadingElements.forEach(el => {
        el.textContent = 'جاري التحميل...';
    });
    
    loadAllData();
}

function setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function() {
            const section = this.dataset.section;
            switchSection(section);
        });
    });

    // Modal close
    window.addEventListener('click', function(event) {
        const modal = document.getElementById('meetingModal');
        if (event.target === modal) {
            closeModal();
        }
    });

    // Search functionality
    const searchInput = document.getElementById('meetingSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            filterMeetings(this.value);
        });
    }

    // Filter functionality
    const filterSelect = document.getElementById('meetingFilter');
    if (filterSelect) {
        filterSelect.addEventListener('change', function() {
            filterMeetingsByType(this.value);
        });
    }
}

function startAutoRefresh() {
    setInterval(() => {
        if (document.visibilityState === 'visible') {
            refreshData();
        }
    }, CONFIG.REFRESH_INTERVAL);
}

// Navigation functions
function switchSection(section) {
    // Update navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-section="${section}"]`).classList.add('active');

    // Update content sections
    document.querySelectorAll('.content-section').forEach(sec => {
        sec.classList.remove('active');
    });
    document.getElementById(`${section}-section`).classList.add('active');

    // Update header
    updateSectionHeader(section);
    
    currentSection = section;
    
    // Load section-specific data
    loadSectionData(section);
}

function updateSectionHeader(section) {
    const titles = {
        'overview': { title: 'نظرة عامة', subtitle: 'حالة النظام والإحصائيات العامة' },
        'meetings': { title: 'الاجتماعات', subtitle: 'سجل الاجتماعات والمحاضر' },
        'agents': { title: 'الوكلاء', subtitle: 'حالة ونشاط الوكلاء الذكيين' },
        'tasks': { title: 'المهام', subtitle: 'إدارة وتتبع المهام' },
        'decisions': { title: 'القرارات', subtitle: 'سجل القرارات والتصويت' },
        'analytics': { title: 'التحليلات', subtitle: 'إحصائيات وتحليلات الأداء' }
    };
    
    const info = titles[section] || titles['overview'];
    document.getElementById('sectionTitle').textContent = info.title;
    document.getElementById('sectionSubtitle').textContent = info.subtitle;
}
// Data loading functions
async function loadAllData() {
    showNotification('جاري تحميل البيانات...', 'info');
    
    try {
        await Promise.all([
            loadMeetingsData(),
            loadTasksData(),
            loadDecisionsData(),
            loadAgentsData()
        ]);
        
        // Ensure DOM elements exist before updating
        setTimeout(() => {
            updateOverviewStats();
        }, 100);
        
        showNotification('تم تحميل البيانات بنجاح', 'success');
    } catch (error) {
        console.error('خطأ في تحميل البيانات:', error);
        showNotification('خطأ في تحميل البيانات', 'error');
        
        // Load demo data as fallback
        allMeetings = getDemoMeetingsData();
        allTasks = getDemoTasksData();
        loadDecisionsData();
        loadAgentsData();
        
        setTimeout(() => {
            updateOverviewStats();
        }, 100);
    }
}

async function loadSectionData(section) {
    switch (section) {
        case 'overview':
            displayOverview();
            break;
        case 'meetings':
            displayMeetings();
            break;
        case 'agents':
            displayAgents();
            break;
        case 'tasks':
            displayTasks();
            break;
        case 'decisions':
            displayDecisions();
            break;
        case 'analytics':
            displayAnalytics();
            break;
    }
}

async function loadMeetingsData() {
    try {
        // Try to load from localStorage first
        const localMeetings = localStorage.getItem('aacs_meetings');
        if (localMeetings) {
            allMeetings = JSON.parse(localMeetings);
        }
        
        // Try to load from server
        const response = await fetch('./meetings/index.json');
        if (response.ok) {
            const data = await response.json();
            const serverMeetings = data.meetings || [];
            
            // Merge and deduplicate
            const combined = [...serverMeetings, ...allMeetings];
            allMeetings = combined.filter((meeting, index, self) => 
                index === self.findIndex(m => m.session_id === meeting.session_id)
            );
            
            // Load detailed meeting data
            await loadMeetingDetails();
        }
        
        if (allMeetings.length === 0) {
            allMeetings = getDemoMeetingsData();
        }
        
    } catch (error) {
        console.warn('لم يتم العثور على بيانات الاجتماعات:', error);
        allMeetings = getDemoMeetingsData();
    }
}

async function loadMeetingDetails() {
    for (let meeting of allMeetings) {
        try {
            // Load transcript
            const transcriptResponse = await fetch(`./meetings/${meeting.session_id}/transcript.jsonl`);
            if (transcriptResponse.ok) {
                const transcriptText = await transcriptResponse.text();
                meeting.transcript = parseTranscript(transcriptText);
            }
            
            // Load decisions
            const decisionsResponse = await fetch(`./meetings/${meeting.session_id}/decisions.json`);
            if (decisionsResponse.ok) {
                const decisionsData = await decisionsResponse.json();
                meeting.decisions = decisionsData.decisions || [];
            }
            
            // Load minutes
            const minutesResponse = await fetch(`./meetings/${meeting.session_id}/minutes.md`);
            if (minutesResponse.ok) {
                const minutesText = await minutesResponse.text();
                meeting.minutes = minutesText;
            }
            
        } catch (error) {
            console.warn(`لم يتم تحميل تفاصيل الاجتماع ${meeting.session_id}:`, error);
        }
    }
}

function parseTranscript(transcriptText) {
    const lines = transcriptText.split('\n').filter(line => line.trim());
    const messages = [];
    
    for (const line of lines) {
        try {
            const message = JSON.parse(line);
            messages.push(message);
        } catch (error) {
            console.warn('خطأ في تحليل سطر المحضر:', line);
        }
    }
    
    return messages;
}

async function loadTasksData() {
    try {
        const localTasks = localStorage.getItem('aacs_tasks');
        if (localTasks) {
            allTasks = JSON.parse(localTasks);
        }
        
        const response = await fetch('./board/tasks.json');
        if (response.ok) {
            const serverTasks = await response.json();
            // Merge with local tasks
            allTasks = {
                todo: [...(serverTasks.todo || []), ...(allTasks.todo || [])],
                in_progress: [...(serverTasks.in_progress || []), ...(allTasks.in_progress || [])],
                done: [...(serverTasks.done || []), ...(allTasks.done || [])]
            };
        }
        
        if (!allTasks.todo && !allTasks.in_progress && !allTasks.done) {
            allTasks = getDemoTasksData();
        }
        
    } catch (error) {
        console.warn('لم يتم العثور على بيانات المهام:', error);
        allTasks = getDemoTasksData();
    }
}

async function loadDecisionsData() {
    allDecisions = [];
    
    // Extract decisions from meetings
    for (const meeting of allMeetings) {
        if (meeting.decisions) {
            meeting.decisions.forEach(decision => {
                allDecisions.push({
                    ...decision,
                    meeting_id: meeting.session_id,
                    meeting_date: meeting.timestamp,
                    meeting_agenda: meeting.agenda
                });
            });
        }
    }
}

function loadAgentsData() {
    allAgents = [
        { 
            id: 'ceo', 
            name: 'الرئيس التنفيذي', 
            icon: '👔', 
            role: 'القيادة الاستراتيجية',
            status: 'نشط',
            contributions: getAgentContributions('ceo'),
            decisions_made: getAgentDecisions('ceo')
        },
        { 
            id: 'pm', 
            name: 'مدير المشاريع', 
            icon: '📊', 
            role: 'إدارة المشاريع',
            status: 'نشط',
            contributions: getAgentContributions('pm'),
            decisions_made: getAgentDecisions('pm')
        },
        { 
            id: 'cto', 
            name: 'المدير التقني', 
            icon: '💻', 
            role: 'القيادة التقنية',
            status: 'نشط',
            contributions: getAgentContributions('cto'),
            decisions_made: getAgentDecisions('cto')
        },
        { 
            id: 'developer', 
            name: 'المطور', 
            icon: '⚡', 
            role: 'التطوير والبرمجة',
            status: 'نشط',
            contributions: getAgentContributions('developer'),
            decisions_made: getAgentDecisions('developer')
        },
        { 
            id: 'qa', 
            name: 'ضمان الجودة', 
            icon: '🔍', 
            role: 'اختبار الجودة',
            status: 'نشط',
            contributions: getAgentContributions('qa'),
            decisions_made: getAgentDecisions('qa')
        },
        { 
            id: 'marketing', 
            name: 'التسويق', 
            icon: '📈', 
            role: 'التسويق والمبيعات',
            status: 'نشط',
            contributions: getAgentContributions('marketing'),
            decisions_made: getAgentDecisions('marketing')
        },
        { 
            id: 'finance', 
            name: 'المالية', 
            icon: '💰', 
            role: 'التحليل المالي',
            status: 'نشط',
            contributions: getAgentContributions('finance'),
            decisions_made: getAgentDecisions('finance')
        },
        { 
            id: 'critic', 
            name: 'الناقد', 
            icon: '🤔', 
            role: 'التقييم النقدي',
            status: 'نشط',
            contributions: getAgentContributions('critic'),
            decisions_made: getAgentDecisions('critic')
        },
        { 
            id: 'chair', 
            name: 'رئيس الاجتماع', 
            icon: '🎯', 
            role: 'إدارة الاجتماعات',
            status: 'نشط',
            contributions: getAgentContributions('chair'),
            decisions_made: getAgentDecisions('chair')
        },
        { 
            id: 'memory', 
            name: 'إدارة الذاكرة', 
            icon: '🧠', 
            role: 'إدارة المعلومات',
            status: 'نشط',
            contributions: getAgentContributions('memory'),
            decisions_made: 0 // Memory agent doesn't vote
        }
    ];
}

function getAgentContributions(agentId) {
    let count = 0;
    allMeetings.forEach(meeting => {
        if (meeting.transcript) {
            count += meeting.transcript.filter(msg => msg.agent === agentId).length;
        }
    });
    return count;
}

function getAgentDecisions(agentId) {
    let count = 0;
    allDecisions.forEach(decision => {
        if (decision.votes && decision.votes[agentId]) {
            count++;
        }
    });
    return count;
}
// Display functions
function displayOverview() {
    // Update last meeting overview
    if (allMeetings.length > 0) {
        const lastMeeting = allMeetings[allMeetings.length - 1];
        document.getElementById('lastMeetingOverview').innerHTML = `
            <div class="meeting-summary">
                <h4>${extractMeetingTitle(lastMeeting)}</h4>
                <p><strong>التاريخ:</strong> ${formatDate(new Date(lastMeeting.timestamp))}</p>
                <p><strong>القرارات:</strong> ${lastMeeting.decisions_count || 0}</p>
                <p><strong>المشاركون:</strong> ${lastMeeting.participants ? lastMeeting.participants.length : 10} وكيل</p>
                <button class="action-btn" onclick="showMeetingDetails('${lastMeeting.session_id}')">
                    عرض التفاصيل
                </button>
            </div>
        `;
    }
    
    // Update active tasks
    const activeTasks = [...(allTasks.todo || []), ...(allTasks.in_progress || [])];
    document.getElementById('activeTasks').innerHTML = `
        <div class="tasks-summary">
            <div class="task-count">
                <span class="count">${allTasks.todo ? allTasks.todo.length : 0}</span>
                <span class="label">في الانتظار</span>
            </div>
            <div class="task-count">
                <span class="count">${allTasks.in_progress ? allTasks.in_progress.length : 0}</span>
                <span class="label">قيد التنفيذ</span>
            </div>
            <div class="task-count">
                <span class="count">${allTasks.done ? allTasks.done.length : 0}</span>
                <span class="label">مكتملة</span>
            </div>
        </div>
    `;
}

function displayMeetings() {
    const container = document.getElementById('meetingsContainer');
    
    if (allMeetings.length === 0) {
        container.innerHTML = '<div class="loading">لا توجد اجتماعات حتى الآن</div>';
        return;
    }
    
    const sortedMeetings = [...allMeetings].sort((a, b) => 
        new Date(b.timestamp) - new Date(a.timestamp)
    );
    
    container.innerHTML = sortedMeetings.map(meeting => `
        <div class="meeting-card enhanced-card" onclick="showMeetingDetails('${meeting.session_id}')">
            <div class="meeting-header">
                <div class="meeting-title-section">
                    <div class="meeting-main-title">${extractMeetingTitle(meeting)}</div>
                    <div class="meeting-subtitle">
                        <span class="session-id">جلسة: ${formatSessionId(meeting.session_id)}</span>
                        <span class="meeting-date">${formatDate(new Date(meeting.timestamp))}</span>
                    </div>
                </div>
                <div class="meeting-status-section">
                    <div class="meeting-status ${meeting.status === 'completed' ? 'completed' : 'in-progress'}">
                        ${meeting.status === 'completed' ? '✅ مكتمل' : '⏳ قيد التنفيذ'}
                    </div>
                    <div class="meeting-actions">
                        <button class="quick-action-btn" onclick="event.stopPropagation(); viewMeetingTranscript('${meeting.session_id}')" title="عرض المحضر">
                            📄
                        </button>
                        <button class="quick-action-btn" onclick="event.stopPropagation(); viewMeetingDecisions('${meeting.session_id}')" title="عرض القرارات">
                            🗳️
                        </button>
                        <button class="quick-action-btn" onclick="event.stopPropagation(); exportMeetingReport('${meeting.session_id}')" title="تصدير تقرير">
                            📊
                        </button>
                    </div>
                </div>
            </div>
            <div class="meeting-stats">
                <div class="stat-item">
                    <span class="stat-icon">🗳️</span>
                    <span class="stat-value">${meeting.decisions_count || 0}</span>
                    <span class="stat-label">قرارات</span>
                </div>
                <div class="stat-item">
                    <span class="stat-icon">👥</span>
                    <span class="stat-value">${meeting.participants ? meeting.participants.length : 10}</span>
                    <span class="stat-label">مشارك</span>
                </div>
                <div class="stat-item">
                    <span class="stat-icon">💬</span>
                    <span class="stat-value">${meeting.transcript ? meeting.transcript.length : 0}</span>
                    <span class="stat-label">رسالة</span>
                </div>
                <div class="stat-item">
                    <span class="stat-icon">⏱️</span>
                    <span class="stat-value">${calculateMeetingDuration(meeting)}</span>
                    <span class="stat-label">دقيقة</span>
                </div>
            </div>
            <div class="meeting-preview-enhanced">
                <div class="preview-content">
                    ${getMeetingPreviewEnhanced(meeting)}
                </div>
                <div class="preview-actions">
                    <span class="view-details-btn">انقر لعرض التفاصيل الكاملة ←</span>
                </div>
            </div>
        </div>
    `).join('');
}

function displayAgents() {
    const container = document.getElementById('agentsContainer');
    
    container.innerHTML = allAgents.map(agent => `
        <div class="agent-card" onclick="showAgentDetails('${agent.id}')">
            <div class="agent-header">
                <div class="agent-avatar">${agent.icon}</div>
                <div class="agent-info">
                    <h3>${agent.name}</h3>
                    <div class="agent-role">${agent.role}</div>
                </div>
            </div>
            <div class="agent-stats">
                <div class="agent-stat">
                    <div class="agent-stat-value">${agent.contributions}</div>
                    <div class="agent-stat-label">مساهمات</div>
                </div>
                <div class="agent-stat">
                    <div class="agent-stat-value">${agent.decisions_made}</div>
                    <div class="agent-stat-label">قرارات</div>
                </div>
            </div>
        </div>
    `).join('');
}

function displayTasks() {
    displayTaskColumn('todoTasksList', allTasks.todo || [], 'لا توجد مهام في الانتظار');
    displayTaskColumn('inProgressTasksList', allTasks.in_progress || [], 'لا توجد مهام قيد التنفيذ');
    displayTaskColumn('doneTasksList', allTasks.done || [], 'لا توجد مهام مكتملة');
}

function displayTaskColumn(elementId, tasks, emptyMessage) {
    const element = document.getElementById(elementId);
    
    if (!element) return;
    
    if (tasks.length === 0) {
        element.innerHTML = `<div class="loading">${emptyMessage}</div>`;
        return;
    }
    
    element.innerHTML = tasks.map(task => `
        <div class="task-card" onclick="showTaskDetails('${task.id}')">
            <div class="task-title">${task.title}</div>
            <div class="task-meta">
                <span>👤 ${task.assigned_to || 'غير محدد'}</span>
                <span class="task-priority ${task.priority || 'medium'}">
                    ${getPriorityIcon(task.priority)} ${getPriorityLabel(task.priority)}
                </span>
            </div>
        </div>
    `).join('');
}

function displayDecisions() {
    const container = document.getElementById('decisionsContainer');
    
    if (allDecisions.length === 0) {
        container.innerHTML = '<div class="loading">لا توجد قرارات حتى الآن</div>';
        return;
    }
    
    const sortedDecisions = [...allDecisions].sort((a, b) => 
        new Date(b.meeting_date) - new Date(a.meeting_date)
    );
    
    container.innerHTML = sortedDecisions.map(decision => `
        <div class="decision-card">
            <div class="decision-header">
                <div class="decision-title">${decision.title || decision.proposal || 'قرار'}</div>
                <div class="decision-result ${decision.result === 'approved' ? 'approved' : 'rejected'}">
                    ${decision.result === 'approved' ? 'موافق عليه' : 'مرفوض'}
                </div>
            </div>
            <div class="decision-content">
                ${decision.description || decision.summary || 'لا يوجد وصف متاح'}
            </div>
            <div class="decision-votes">
                <div class="votes-summary">
                    <span>الأصوات: ${getVotesSummary(decision.votes)}</span>
                    <span>من اجتماع: ${decision.meeting_agenda}</span>
                </div>
            </div>
        </div>
    `).join('');
}

function displayAnalytics() {
    // Simple analytics display
    document.getElementById('agentActivityChart').innerHTML = `
        <div style="text-align: center; color: #718096;">
            <p>📊 رسم بياني لنشاط الوكلاء</p>
            <p>سيتم تطويره في النسخة القادمة</p>
        </div>
    `;
    
    document.getElementById('taskProgressChart').innerHTML = `
        <div style="text-align: center; color: #718096;">
            <p>📈 رسم بياني لتقدم المهام</p>
            <p>سيتم تطويره في النسخة القادمة</p>
        </div>
    `;
}
// Modal functions
function showMeetingDetails(meetingId) {
    const meeting = allMeetings.find(m => m.session_id === meetingId);
    if (!meeting) {
        showNotification('لم يتم العثور على تفاصيل الاجتماع', 'error');
        return;
    }
    
    document.getElementById('modalTitle').textContent = `تفاصيل الاجتماع - ${extractMeetingTitle(meeting)}`;
    
    let modalContent = `
        <div class="meeting-details-full">
            <div class="detail-section">
                <h4>معلومات الاجتماع</h4>
                <div class="detail-grid">
                    <div><strong>معرف الجلسة:</strong> ${meeting.session_id}</div>
                    <div><strong>التاريخ:</strong> ${formatDate(new Date(meeting.timestamp))}</div>
                    <div><strong>الأجندة:</strong> ${meeting.agenda}</div>
                    <div><strong>الحالة:</strong> ${meeting.status === 'completed' ? 'مكتمل' : 'قيد التنفيذ'}</div>
                </div>
            </div>
    `;
    
    // Add transcript if available
    if (meeting.transcript && meeting.transcript.length > 0) {
        modalContent += `
            <div class="detail-section">
                <h4>محضر الاجتماع</h4>
                <div class="transcript-container">
                    ${meeting.transcript.map(msg => `
                        <div class="transcript-message">
                            <div class="message-header">
                                <strong>${getAgentName(msg.agent)}</strong>
                                <span class="message-time">${formatTime(msg.timestamp)}</span>
                            </div>
                            <div class="message-content">${msg.message}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    // Add decisions if available
    if (meeting.decisions && meeting.decisions.length > 0) {
        modalContent += `
            <div class="detail-section">
                <h4>القرارات المتخذة</h4>
                <div class="decisions-container">
                    ${meeting.decisions.map(decision => `
                        <div class="decision-item">
                            <div class="decision-title">${decision.title || decision.proposal}</div>
                            <div class="decision-result ${decision.result === 'approved' ? 'approved' : 'rejected'}">
                                ${decision.result === 'approved' ? 'موافق عليه' : 'مرفوض'}
                            </div>
                            <div class="decision-votes">الأصوات: ${getVotesSummary(decision.votes)}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    modalContent += '</div>';
    
    document.getElementById('modalBody').innerHTML = modalContent;
    document.getElementById('meetingModal').style.display = 'block';
}

function showAgentDetails(agentId) {
    const agent = allAgents.find(a => a.id === agentId);
    if (!agent) return;
    
    document.getElementById('modalTitle').textContent = `تفاصيل الوكيل - ${agent.name}`;
    
    // Get agent's recent contributions
    const recentContributions = [];
    allMeetings.forEach(meeting => {
        if (meeting.transcript) {
            const agentMessages = meeting.transcript.filter(msg => msg.agent === agentId);
            agentMessages.forEach(msg => {
                recentContributions.push({
                    ...msg,
                    meeting_agenda: meeting.agenda,
                    meeting_date: meeting.timestamp
                });
            });
        }
    });
    
    const modalContent = `
        <div class="agent-details-full">
            <div class="agent-overview">
                <div class="agent-avatar-large">${agent.icon}</div>
                <div class="agent-info-full">
                    <h3>${agent.name}</h3>
                    <p>${agent.role}</p>
                    <div class="agent-stats-full">
                        <div class="stat">
                            <span class="stat-value">${agent.contributions}</span>
                            <span class="stat-label">مساهمات</span>
                        </div>
                        <div class="stat">
                            <span class="stat-value">${agent.decisions_made}</span>
                            <span class="stat-label">قرارات</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="recent-contributions">
                <h4>المساهمات الأخيرة</h4>
                <div class="contributions-list">
                    ${recentContributions.slice(-10).reverse().map(contrib => `
                        <div class="contribution-item">
                            <div class="contribution-header">
                                <span class="meeting-ref">${contrib.meeting_agenda}</span>
                                <span class="contribution-time">${formatDate(new Date(contrib.meeting_date))}</span>
                            </div>
                            <div class="contribution-content">${contrib.message}</div>
                        </div>
                    `).join('') || '<p>لا توجد مساهمات حديثة</p>'}
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('modalBody').innerHTML = modalContent;
    document.getElementById('meetingModal').style.display = 'block';
}

function closeModal() {
    document.getElementById('meetingModal').style.display = 'none';
}

// Utility functions
function updateOverviewStats() {
    const totalMeetingsEl = document.getElementById('totalMeetings');
    const totalDecisionsEl = document.getElementById('totalDecisions');
    const totalTasksEl = document.getElementById('totalTasks');
    
    if (totalMeetingsEl) {
        totalMeetingsEl.textContent = allMeetings.length;
    }
    if (totalDecisionsEl) {
        totalDecisionsEl.textContent = allDecisions.length;
    }
    if (totalTasksEl) {
        const totalTasks = (allTasks.todo?.length || 0) + 
                          (allTasks.in_progress?.length || 0) + 
                          (allTasks.done?.length || 0);
        totalTasksEl.textContent = totalTasks;
    }
}

function getAgentName(agentId) {
    const agent = allAgents.find(a => a.id === agentId);
    return agent ? agent.name : agentId;
}

function getVotesSummary(votes) {
    if (!votes) return 'لا توجد أصوات';
    
    const voteCount = Object.keys(votes).length;
    const approvedCount = Object.values(votes).filter(vote => 
        vote === 'موافق' || vote === 'approved' || vote === 'yes'
    ).length;
    
    return `${approvedCount}/${voteCount} موافق`;
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
function extractMeetingTitle(meeting) {
    // Extract meaningful title from meeting data
    if (meeting.agenda && meeting.agenda !== 'اجتماع دوري') {
        return meeting.agenda;
    }
    
    // Try to extract from transcript
    if (meeting.transcript && meeting.transcript.length > 0) {
        const chairMessages = meeting.transcript.filter(msg => 
            msg.agent === 'chair' && msg.message.length > 20
        );
        
        if (chairMessages.length > 0) {
            const firstMessage = chairMessages[0].message;
            // Extract topic from chair's opening message
            const topicMatch = firstMessage.match(/نناقش|سنتحدث عن|موضوع|مشروع|فكرة|اقتراح\s+([^.،]+)/);
            if (topicMatch) {
                return topicMatch[1].trim();
            }
        }
    }
    
    // Try to extract from decisions
    if (meeting.decisions && meeting.decisions.length > 0) {
        const firstDecision = meeting.decisions[0];
        if (firstDecision.title) {
            return `قرار: ${firstDecision.title}`;
        }
    }
    
    // Fallback to formatted session ID
    return formatSessionId(meeting.session_id);
}

function formatSessionId(sessionId) {
    // Convert technical session ID to readable format
    if (sessionId.startsWith('meeting_')) {
        const datePart = sessionId.replace('meeting_', '').substring(0, 8);
        const timePart = sessionId.replace('meeting_', '').substring(9);
        
        if (datePart.length === 8) {
            const year = datePart.substring(0, 4);
            const month = datePart.substring(4, 6);
            const day = datePart.substring(6, 8);
            
            const monthNames = {
                '01': 'يناير', '02': 'فبراير', '03': 'مارس', '04': 'أبريل',
                '05': 'مايو', '06': 'يونيو', '07': 'يوليو', '08': 'أغسطس',
                '09': 'سبتمبر', '10': 'أكتوبر', '11': 'نوفمبر', '12': 'ديسمبر'
            };
            
            return `اجتماع ${day} ${monthNames[month]} ${year}`;
        }
    }
    
    return sessionId;
}

function getMeetingPreviewEnhanced(meeting) {
    let preview = '';
    
    // Try to get meaningful preview from different sources
    if (meeting.decisions && meeting.decisions.length > 0) {
        const decision = meeting.decisions[0];
        preview = `📋 تم اتخاذ ${meeting.decisions.length} قرار: ${decision.title || decision.proposal || 'قرار مهم'}`;
    } else if (meeting.transcript && meeting.transcript.length > 0) {
        // Find the most meaningful message
        const meaningfulMessages = meeting.transcript.filter(msg => 
            msg.type === 'contribution' && 
            msg.message.length > 30 &&
            !msg.message.includes('أهلاً وسهلاً') &&
            !msg.message.includes('شكراً للجميع')
        );
        
        if (meaningfulMessages.length > 0) {
            const message = meaningfulMessages[0];
            preview = `💬 ${getAgentName(message.agent)}: ${message.message.substring(0, 120)}...`;
        }
    } else if (meeting.minutes) {
        // Extract from minutes
        const lines = meeting.minutes.split('\n').filter(line => 
            line.trim() && 
            !line.startsWith('#') && 
            !line.startsWith('**') && 
            line.length > 30
        );
        
        if (lines.length > 0) {
            preview = `📄 ${lines[0].substring(0, 120)}...`;
        }
    }
    
    // Fallback
    if (!preview) {
        preview = `🏢 اجتماع شركة AACS - ${meeting.participants ? meeting.participants.length : 10} مشارك`;
    }
    
    return preview;
}

function calculateMeetingDuration(meeting) {
    // Calculate meeting duration in minutes
    if (meeting.transcript && meeting.transcript.length > 1) {
        const firstMessage = meeting.transcript[0];
        const lastMessage = meeting.transcript[meeting.transcript.length - 1];
        
        if (firstMessage.timestamp && lastMessage.timestamp) {
            const start = new Date(firstMessage.timestamp);
            const end = new Date(lastMessage.timestamp);
            const durationMs = end - start;
            const durationMinutes = Math.round(durationMs / (1000 * 60));
            
            return durationMinutes > 0 ? durationMinutes : 15; // Default 15 minutes
        }
    }
    
    // Estimate based on transcript length
    if (meeting.transcript) {
        return Math.max(5, Math.round(meeting.transcript.length * 0.5));
    }
    
    return 10; // Default duration
}

// Quick action functions for meeting cards
function viewMeetingTranscript(meetingId) {
    const meeting = allMeetings.find(m => m.session_id === meetingId);
    if (!meeting || !meeting.transcript) {
        showNotification('المحضر غير متوفر', 'warning');
        return;
    }
    
    document.getElementById('modalTitle').textContent = `محضر الاجتماع - ${extractMeetingTitle(meeting)}`;
    
    const transcriptHtml = meeting.transcript.map(msg => `
        <div class="transcript-message">
            <div class="message-header">
                <span class="agent-name">${getAgentName(msg.agent)}</span>
                <span class="message-time">${formatTime(msg.timestamp)}</span>
            </div>
            <div class="message-content">${msg.message}</div>
        </div>
    `).join('');
    
    document.getElementById('modalBody').innerHTML = `
        <div class="transcript-full">
            ${transcriptHtml}
        </div>
    `;
    
    document.getElementById('meetingModal').style.display = 'block';
}

function viewMeetingDecisions(meetingId) {
    const meeting = allMeetings.find(m => m.session_id === meetingId);
    if (!meeting || !meeting.decisions || meeting.decisions.length === 0) {
        showNotification('لا توجد قرارات في هذا الاجتماع', 'warning');
        return;
    }
    
    document.getElementById('modalTitle').textContent = `قرارات الاجتماع - ${extractMeetingTitle(meeting)}`;
    
    const decisionsHtml = meeting.decisions.map(decision => `
        <div class="decision-detail">
            <div class="decision-header">
                <h4>${decision.title || decision.proposal}</h4>
                <span class="decision-result ${decision.result === 'approved' ? 'approved' : 'rejected'}">
                    ${decision.result === 'approved' ? '✅ موافق عليه' : '❌ مرفوض'}
                </span>
            </div>
            <div class="decision-content">
                <p>${decision.description || decision.summary || 'لا يوجد وصف'}</p>
            </div>
            <div class="decision-votes">
                <h5>تفاصيل التصويت:</h5>
                <div class="votes-grid">
                    ${Object.entries(decision.votes || {}).map(([agent, vote]) => `
                        <div class="vote-item">
                            <span class="voter">${getAgentName(agent)}</span>
                            <span class="vote ${vote === 'موافق' || vote === 'approved' ? 'approve' : 'reject'}">
                                ${vote}
                            </span>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `).join('');
    
    document.getElementById('modalBody').innerHTML = `
        <div class="decisions-full">
            ${decisionsHtml}
        </div>
    `;
    
    document.getElementById('meetingModal').style.display = 'block';
}

function exportMeetingReport(meetingId) {
    const meeting = allMeetings.find(m => m.session_id === meetingId);
    if (!meeting) {
        showNotification('الاجتماع غير موجود', 'error');
        return;
    }
    
    // Create comprehensive report
    const report = {
        meeting_info: {
            title: extractMeetingTitle(meeting),
            session_id: meeting.session_id,
            date: formatDate(new Date(meeting.timestamp)),
            duration: calculateMeetingDuration(meeting),
            participants: meeting.participants || ['ceo', 'cto', 'pm', 'developer', 'qa', 'marketing', 'finance', 'critic', 'chair', 'memory']
        },
        transcript: meeting.transcript || [],
        decisions: meeting.decisions || [],
        minutes: meeting.minutes || '',
        statistics: {
            total_messages: meeting.transcript ? meeting.transcript.length : 0,
            decisions_count: meeting.decisions ? meeting.decisions.length : 0,
            participants_count: meeting.participants ? meeting.participants.length : 10
        }
    };
    
    // Download as JSON
    const dataStr = JSON.stringify(report, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `meeting_report_${meeting.session_id}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    showNotification('تم تصدير تقرير الاجتماع', 'success');
}

// Enhanced run meeting function
function runManualMeeting() {
    // Show confirmation dialog
    if (!confirm('هل تريد تشغيل اجتماع AACS جديد؟ سيتم تشغيله في GitHub Actions.')) {
        return;
    }
    
    showNotification('جاري تشغيل الاجتماع...', 'info');
    
    // Try to trigger GitHub Actions workflow
    const repoUrl = `https://github.com/${CONFIG.GITHUB_USER}/${CONFIG.GITHUB_REPO}`;
    const actionsUrl = `${repoUrl}/actions/workflows/meeting.yml`;
    
    // Open GitHub Actions page for manual trigger
    window.open(actionsUrl, '_blank');
    
    showNotification('تم فتح صفحة GitHub Actions. يرجى النقر على "Run workflow" لتشغيل الاجتماع.', 'info');
    
    // Optionally refresh data after a delay
    setTimeout(() => {
        refreshData();
    }, 5000);
}
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

function formatTime(timestamp) {
    return new Date(timestamp).toLocaleTimeString('ar-SA', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

function showNotification(message, type = 'info') {
    // Ensure DOM is ready
    if (!document.body) {
        console.log(`Notification (${type}): ${message}`);
        return;
    }
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 3000);
}

// Filter functions
function filterMeetings(searchTerm) {
    const filteredMeetings = allMeetings.filter(meeting => 
        meeting.agenda.toLowerCase().includes(searchTerm.toLowerCase()) ||
        meeting.session_id.toLowerCase().includes(searchTerm.toLowerCase())
    );
    
    displayFilteredMeetings(filteredMeetings);
}

function filterMeetingsByType(type) {
    let filteredMeetings = allMeetings;
    
    switch (type) {
        case 'recent':
            filteredMeetings = allMeetings.slice(-5);
            break;
        case 'completed':
            filteredMeetings = allMeetings.filter(m => m.status === 'completed');
            break;
        default:
            filteredMeetings = allMeetings;
    }
    
    displayFilteredMeetings(filteredMeetings);
}

function displayFilteredMeetings(meetings) {
    const container = document.getElementById('meetingsContainer');
    
    if (meetings.length === 0) {
        container.innerHTML = '<div class="loading">لا توجد نتائج</div>';
        return;
    }
    
    const sortedMeetings = [...meetings].sort((a, b) => 
        new Date(b.timestamp) - new Date(a.timestamp)
    );
    
    container.innerHTML = sortedMeetings.map(meeting => `
        <div class="meeting-card" onclick="showMeetingDetails('${meeting.session_id}')">
            <div class="meeting-header">
                <div>
                    <div class="meeting-title">${meeting.agenda}</div>
                    <div class="meeting-date">${formatDate(new Date(meeting.timestamp))}</div>
                </div>
                <div class="meeting-status">${meeting.status === 'completed' ? 'مكتمل' : 'قيد التنفيذ'}</div>
            </div>
            <div class="meeting-meta">
                <span>🗳️ ${meeting.decisions_count || 0} قرارات</span>
                <span>👥 ${meeting.participants ? meeting.participants.length : 10} مشارك</span>
                <span>💬 ${meeting.transcript ? meeting.transcript.length : 0} رسالة</span>
            </div>
            <div class="meeting-preview">
                ${getMeetingPreviewEnhanced(meeting)}
            </div>
        </div>
    `).join('');
}

// Demo data functions
function getDemoMeetingsData() {
    return [
        {
            session_id: 'demo_meeting_1',
            agenda: 'مناقشة مشاريع جديدة للشركة',
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            decisions_count: 3,
            status: 'completed',
            participants: ['ceo', 'cto', 'pm', 'developer', 'qa', 'marketing', 'finance', 'critic', 'chair', 'memory'],
            transcript: [
                {
                    timestamp: new Date().toISOString(),
                    agent: 'chair',
                    message: 'أهلاً وسهلاً بالجميع في اجتماع اليوم. سنناقش المشاريع الجديدة المقترحة.',
                    type: 'contribution'
                },
                {
                    timestamp: new Date().toISOString(),
                    agent: 'ceo',
                    message: 'أقترح التركيز على مشاريع الذكاء الاصطناعي والتقنيات الناشئة.',
                    type: 'contribution'
                }
            ],
            decisions: [
                {
                    title: 'الموافقة على مشروع منصة الذكاء الاصطناعي',
                    result: 'approved',
                    votes: { ceo: 'موافق', cto: 'موافق', pm: 'موافق' }
                }
            ]
        }
    ];
}

function getDemoTasksData() {
    return {
        todo: [
            {
                id: 'demo_task_1',
                title: 'تطوير نموذج أولي لمنصة الذكاء الاصطناعي',
                description: 'مهمة من قرار: منصة الذكاء الاصطناعي للشركات الناشئة',
                assigned_to: 'developer',
                created_at: new Date().toISOString(),
                priority: 'high',
                status: 'todo'
            }
        ],
        in_progress: [
            {
                id: 'demo_task_2',
                title: 'تصميم قاعدة البيانات للنظام',
                description: 'مهمة من قرار: نظام إدارة المواهب الذكي',
                assigned_to: 'cto',
                created_at: new Date(Date.now() - 86400000).toISOString(),
                priority: 'high',
                status: 'in_progress'
            }
        ],
        done: [
            {
                id: 'demo_task_3',
                title: 'إعداد بيئة التطوير الأساسية',
                description: 'مهمة من قرار: إعداد البنية التحتية',
                assigned_to: 'developer',
                created_at: new Date(Date.now() - 172800000).toISOString(),
                priority: 'medium',
                status: 'done'
            }
        ]
    };
}

// Public functions
function refreshData() {
    showNotification('جاري تحديث البيانات...', 'info');
    loadAllData();
}

// Debug function for testing
window.debugDashboard = function() {
    console.log('=== AACS Dashboard Debug Info ===');
    console.log('Current section:', currentSection);
    console.log('All meetings:', allMeetings.length);
    console.log('All tasks:', {
        todo: allTasks.todo?.length || 0,
        in_progress: allTasks.in_progress?.length || 0,
        done: allTasks.done?.length || 0
    });
    console.log('All decisions:', allDecisions.length);
    console.log('All agents:', allAgents.length);
    
    // Test critical elements
    const elements = ['totalMeetings', 'totalDecisions', 'totalTasks'];
    elements.forEach(id => {
        const el = document.getElementById(id);
        console.log(`${id}:`, el ? `Found (${el.textContent})` : 'Missing');
    });
    
    return {
        meetings: allMeetings.length,
        tasks: allTasks,
        decisions: allDecisions.length,
        agents: allAgents.length
    };
};

// Error handling
window.addEventListener('error', function(event) {
    console.error('خطأ في لوحة التحكم المحسنة:', event.error);
    console.error('Stack trace:', event.error?.stack);
    showNotification('حدث خطأ في لوحة التحكم', 'error');
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', function(event) {
    console.error('خطأ في Promise:', event.reason);
    showNotification('حدث خطأ في تحميل البيانات', 'error');
});

// Initialize on load
console.log('✅ AACS Enhanced Dashboard JavaScript تم تحميله بنجاح');