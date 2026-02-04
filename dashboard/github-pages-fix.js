// GitHub Pages Configuration Fix
// This script detects GitHub Pages environment and adjusts paths accordingly

(function() {
    // Detect if running on GitHub Pages
    const isGitHubPages = window.location.hostname.includes('github.io');
    const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    
    if (isGitHubPages) {
        console.log('🌐 Running on GitHub Pages');
        
        // Override fetch function to handle GitHub Pages paths
        const originalFetch = window.fetch;
        window.fetch = function(url, options) {
            if (typeof url === 'string' && url.startsWith('./')) {
                // Convert relative paths for GitHub Pages
                const repoName = window.location.pathname.split('/')[1];
                url = `/${repoName}/${url.substring(2)}`;
                console.log('📁 Adjusted path for GitHub Pages:', url);
            }
            return originalFetch(url, options);
        };
        
        // Add GitHub Pages indicator
        document.addEventListener('DOMContentLoaded', function() {
            const subtitle = document.querySelector('.subtitle');
            if (subtitle) {
                subtitle.textContent += ' (GitHub Pages)';
            }
            
            // Show GitHub Pages notice
            setTimeout(() => {
                showNotification('🌐 تعمل على GitHub Pages - قد تحتاج لمسح ذاكرة المتصفح لرؤية التحديثات', 'info');
            }, 2000);
        });
    }
    
    // Add cache busting for GitHub Pages
    if (isGitHubPages) {
        const originalFetch = window.fetch;
        window.fetch = function(url, options) {
            if (typeof url === 'string' && (url.includes('.json') || url.includes('.md'))) {
                const separator = url.includes('?') ? '&' : '?';
                url += `${separator}v=${Date.now()}`;
            }
            return originalFetch(url, options);
        };
    }
})();