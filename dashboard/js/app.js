/**
 * AACS Application Entry Point
 * Initializes the dashboard and handles global events
 */

// Global dashboard instance
let dashboard;

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', async function() {
    try {
        // Create dashboard instance
        dashboard = new AacsDashboard();
        
        // Initialize dashboard
        await dashboard.initialize();
        
        // Add CSS animation for ripple effect
        addRippleAnimation();
        
        console.log('✅ AACS Dashboard initialized successfully');
        
    } catch (error) {
        console.error('❌ Failed to initialize AACS Dashboard:', error);
        
        // Show error notification
        const notification = document.createElement('div');
        notification.className = 'notification error';
        notification.innerHTML = '❌ فشل في تحميل لوحة التحكم: ' + error.message;
        document.body.appendChild(notification);
        
        setTimeout(() => notification.remove(), 5000);
    }
});

// Handle page unload
window.addEventListener('beforeunload', function() {
    if (dashboard) {
        dashboard.destroy();
    }
});

// Handle visibility change (tab switching)
document.addEventListener('visibilitychange', function() {
    if (dashboard) {
        if (document.hidden) {
            // Page is hidden, pause auto-refresh
            console.log('📱 Page hidden, pausing auto-refresh');
        } else {
            // Page is visible, resume auto-refresh and load fresh data
            console.log('📱 Page visible, resuming auto-refresh');
            dashboard.loadSystemData();
        }
    }
});

// Add ripple animation CSS
function addRippleAnimation() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes ripple {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}

// Global error handler
window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
    
    if (dashboard && dashboard.ui) {
        dashboard.ui.showNotification('حدث خطأ غير متوقع في النظام', 'error');
    }
});

// Global unhandled promise rejection handler
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    
    if (dashboard && dashboard.ui) {
        dashboard.ui.showNotification('خطأ في معالجة البيانات', 'warning');
    }
    
    // Prevent the default behavior (logging to console)
    event.preventDefault();
});

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + R: Refresh data
    if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
        event.preventDefault();
        if (dashboard) {
            dashboard.loadSystemData();
            dashboard.ui.showNotification('تم تحديث البيانات يدوياً', 'info');
        }
    }
    
    // Ctrl/Cmd + M: Run meeting
    if ((event.ctrlKey || event.metaKey) && event.key === 'm') {
        event.preventDefault();
        if (dashboard) {
            dashboard.runMeeting();
        }
    }
    
    // Ctrl/Cmd + D: View meetings
    if ((event.ctrlKey || event.metaKey) && event.key === 'd') {
        event.preventDefault();
        if (dashboard) {
            dashboard.viewMeetings();
        }
    }
});

// Export dashboard for global access (for onclick handlers)
window.dashboard = dashboard;