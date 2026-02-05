/**
 * AACS UI Handler
 * Handles all UI interactions, animations, and notifications
 */

class AacsUI {
    constructor() {
        this.elements = this.initializeElements();
        this.setupEventListeners();
    }

    /**
     * Initialize DOM elements
     */
    initializeElements() {
        return {
            meetingsCount: document.getElementById('meetingsCount'),
            decisionsCount: document.getElementById('decisionsCount'),
            tasksCount: document.getElementById('tasksCount'),
            meetingsChange: document.getElementById('meetingsChange'),
            decisionsChange: document.getElementById('decisionsChange'),
            tasksChange: document.getElementById('tasksChange'),
            recentActivity: document.querySelector('.recent-activity'),
            statCards: document.querySelectorAll('.stat-card')
        };
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Add ripple effect to buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('btn')) {
                this.addRippleEffect(e.target, e);
            }
        });

        // Performance monitoring
        window.addEventListener('load', () => {
            const loadTime = performance.now();
            console.log(`⚡ تم تحميل الصفحة في ${Math.round(loadTime)}ms`);
            
            if (loadTime > 3000) {
                this.showNotification('تم تحميل الصفحة بنجاح ولكن قد تحتاج لتحسين الأداء', 'warning');
            }
        });
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'success') {
        // Remove existing notifications
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(notification => notification.remove());

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        // Add icon based on type
        const icons = {
            success: '✅',
            error: '❌',
            info: 'ℹ️',
            warning: '⚠️'
        };
        
        notification.innerHTML = `${icons[type] || '📢'} ${message}`;
        document.body.appendChild(notification);
        
        // Auto remove after configured duration
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, CONFIG.UI.NOTIFICATION_DURATION);
    }

    /**
     * Add ripple effect to buttons
     */
    addRippleEffect(button, event) {
        const ripple = document.createElement('span');
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            background: rgba(255,255,255,0.3);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple 0.6s linear;
            pointer-events: none;
        `;
        
        button.style.position = 'relative';
        button.style.overflow = 'hidden';
        button.appendChild(ripple);
        
        setTimeout(() => ripple.remove(), 600);
    }

    /**
     * Show loading state
     */
    showLoadingState(isLoading) {
        this.elements.statCards.forEach(card => {
            if (isLoading) {
                card.classList.add('loading');
            } else {
                card.classList.remove('loading');
            }
        });
    }

    /**
     * Animate number counting
     */
    animateNumber(element, targetValue) {
        const currentValue = parseInt(element.textContent) || 0;
        if (isNaN(targetValue)) {
            element.textContent = targetValue;
            return;
        }
        
        const increment = targetValue > currentValue ? 1 : -1;
        const duration = CONFIG.UI.ANIMATION_DURATION;
        const steps = Math.abs(targetValue - currentValue);
        const stepDuration = duration / Math.max(steps, 1);

        let current = currentValue;
        const timer = setInterval(() => {
            current += increment;
            element.textContent = current;
            
            if (current === targetValue) {
                clearInterval(timer);
            }
        }, stepDuration);
    }

    /**
     * Update statistics display
     */
    updateStatistics(data) {
        const elements = {
            meetingsCount: this.elements.meetingsCount,
            decisionsCount: this.elements.decisionsCount,
            tasksCount: this.elements.tasksCount
        };

        // Animate number changes
        Object.keys(elements).forEach(key => {
            const element = elements[key];
            const targetValue = data[key.replace('Count', '')];
            this.animateNumber(element, targetValue);
        });
    }

    /**
     * Update change indicators
     */
    updateChangeIndicators(isRealData, meetingsCount) {
        if (isRealData) {
            this.elements.meetingsChange.textContent = 'بيانات حقيقية من GitHub';
            this.elements.decisionsChange.textContent = `من ${meetingsCount} اجتماع`;
            this.elements.tasksChange.textContent = 'محسوبة تلقائياً';
        } else {
            this.elements.meetingsChange.textContent = 'بيانات تقديرية';
            this.elements.decisionsChange.textContent = 'تقدير أولي';
            this.elements.tasksChange.textContent = 'محسوبة تقديرياً';
        }
    }

    /**
     * Update recent activity
     */
    updateRecentActivity(meetingsData) {
        if (!meetingsData || meetingsData.length === 0) return;
        
        const title = this.elements.recentActivity.querySelector('h3');
        this.elements.recentActivity.innerHTML = '';
        this.elements.recentActivity.appendChild(title);
        
        // Add real meeting activities
        meetingsData.slice(-5).reverse().forEach((meeting) => {
            const date = new Date(meeting.timestamp);
            const timeAgo = this.getTimeAgo(date);
            
            const activityItem = document.createElement('div');
            activityItem.className = 'activity-item';
            activityItem.innerHTML = `
                <div class="activity-icon">📅</div>
                <div class="activity-content">
                    <div class="activity-title">اجتماع: ${meeting.agenda}</div>
                    <div class="activity-description">تم اتخاذ ${meeting.decisions_count} قرار بمشاركة ${meeting.participants.length} وكيل</div>
                    <div class="activity-time">🕐 ${timeAgo}</div>
                </div>
            `;
            this.elements.recentActivity.appendChild(activityItem);
        });
        
        // Add quick access item
        const quickAccessItem = document.createElement('div');
        quickAccessItem.className = 'activity-item';
        quickAccessItem.style.cursor = 'pointer';
        quickAccessItem.innerHTML = `
            <div class="activity-icon">🔍</div>
            <div class="activity-content">
                <div class="activity-title">عرض جميع الاجتماعات</div>
                <div class="activity-description">انقر هنا لاستعراض تفاصيل جميع الاجتماعات والنقاشات</div>
                <div class="activity-time">🚀 وصول سريع</div>
            </div>
        `;
        quickAccessItem.onclick = () => dashboard.viewMeetings();
        this.elements.recentActivity.appendChild(quickAccessItem);
    }

    /**
     * Helper function to calculate time ago
     */
    getTimeAgo(date) {
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);
        
        if (diffInSeconds < 60) return 'منذ لحظات';
        if (diffInSeconds < 3600) return `منذ ${Math.floor(diffInSeconds / 60)} دقيقة`;
        if (diffInSeconds < 86400) return `منذ ${Math.floor(diffInSeconds / 3600)} ساعة`;
        if (diffInSeconds < 2592000) return `منذ ${Math.floor(diffInSeconds / 86400)} يوم`;
        return date.toLocaleDateString('ar-SA');
    }

    /**
     * Create modal window
     */
    createModal(title, content, options = {}) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>${title}</h2>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                ${options.footer ? `<div class="modal-footer">${options.footer}</div>` : ''}
            </div>
        `;

        // Add modal styles
        const style = document.createElement('style');
        style.textContent = `
            .modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10000;
                animation: fadeIn 0.3s ease;
            }
            .modal-content {
                background: white;
                border-radius: 15px;
                max-width: 90vw;
                max-height: 90vh;
                overflow: auto;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            }
            .modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 20px;
                border-bottom: 1px solid #e5e7eb;
            }
            .modal-close {
                background: none;
                border: none;
                font-size: 1.5rem;
                cursor: pointer;
                color: #6b7280;
            }
            .modal-body {
                padding: 20px;
            }
            .modal-footer {
                padding: 20px;
                border-top: 1px solid #e5e7eb;
                text-align: left;
            }
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
        `;
        document.head.appendChild(style);

        // Close modal functionality
        const closeModal = () => {
            modal.remove();
            style.remove();
        };

        modal.querySelector('.modal-close').onclick = closeModal;
        modal.onclick = (e) => {
            if (e.target === modal) closeModal();
        };

        document.body.appendChild(modal);
        return modal;
    }
}