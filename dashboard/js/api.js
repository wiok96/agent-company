/**
 * AACS API Handler
 * Handles all API calls to GitHub and data processing
 */

class AacsApi {
    constructor() {
        this.baseUrl = CONFIG.API.BASE_URL;
        this.cache = new Map();
        this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
    }

    /**
     * Fetch data from GitHub API with caching
     */
    async fetchWithCache(url, cacheKey) {
        const cached = this.cache.get(cacheKey);
        if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
            return cached.data;
        }

        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            this.cache.set(cacheKey, {
                data,
                timestamp: Date.now()
            });

            return data;
        } catch (error) {
            console.error(`API Error for ${url}:`, error);
            throw error;
        }
    }

    /**
     * Get meetings data from GitHub
     */
    async getMeetingsData() {
        try {
            // Try to get meetings index first
            const indexUrl = this.baseUrl + CONFIG.API.ENDPOINTS.MEETINGS_INDEX;
            const indexData = await this.fetchWithCache(indexUrl, 'meetings-index');
            
            if (indexData && indexData.content) {
                const content = JSON.parse(atob(indexData.content));
                return this.processMeetingsData(content.meetings);
            }

            // Fallback to directory listing
            const dirUrl = this.baseUrl + CONFIG.API.ENDPOINTS.MEETINGS_DIR;
            const dirData = await this.fetchWithCache(dirUrl, 'meetings-dir');
            
            const meetingDirs = dirData.filter(item => 
                item.type === 'dir' && item.name.startsWith('meeting_')
            );

            return {
                meetings: meetingDirs.length,
                decisions: meetingDirs.length * 2, // Estimate
                tasks: meetingDirs.length * 3, // Estimate
                meetingsData: []
            };

        } catch (error) {
            console.error('Error fetching meetings data:', error);
            return null;
        }
    }

    /**
     * Process raw meetings data
     */
    processMeetingsData(meetings) {
        const totalDecisions = meetings.reduce((sum, m) => sum + (m.decisions_count || 0), 0);
        
        return {
            meetings: meetings.length,
            decisions: totalDecisions,
            tasks: Math.floor(totalDecisions * 1.5), // Estimate tasks based on decisions
            meetingsData: meetings
        };
    }

    /**
     * Get meeting transcript
     */
    async getMeetingTranscript(sessionId) {
        try {
            const url = this.baseUrl + CONFIG.API.ENDPOINTS.MEETING_TRANSCRIPT(sessionId);
            const data = await this.fetchWithCache(url, `transcript-${sessionId}`);
            
            if (data && data.content) {
                const content = atob(data.content);
                const lines = content.split('\n').filter(line => line.trim());
                return lines.map(line => JSON.parse(line));
            }
            
            return [];
        } catch (error) {
            console.error(`Error fetching transcript for ${sessionId}:`, error);
            throw error;
        }
    }

    /**
     * Get meeting decisions
     */
    async getMeetingDecisions(sessionId) {
        try {
            const url = this.baseUrl + CONFIG.API.ENDPOINTS.MEETING_DECISIONS(sessionId);
            const data = await this.fetchWithCache(url, `decisions-${sessionId}`);
            
            if (data && data.content) {
                const content = JSON.parse(atob(data.content));
                return content.decisions || [];
            }
            
            return [];
        } catch (error) {
            console.error(`Error fetching decisions for ${sessionId}:`, error);
            throw error;
        }
    }

    /**
     * Get meeting minutes
     */
    async getMeetingMinutes(sessionId) {
        try {
            const url = this.baseUrl + CONFIG.API.ENDPOINTS.MEETING_MINUTES(sessionId);
            const data = await this.fetchWithCache(url, `minutes-${sessionId}`);
            
            if (data && data.content) {
                return atob(data.content);
            }
            
            return '';
        } catch (error) {
            console.error(`Error fetching minutes for ${sessionId}:`, error);
            throw error;
        }
    }

    /**
     * Clear cache
     */
    clearCache() {
        this.cache.clear();
    }

    /**
     * Get cache stats
     */
    getCacheStats() {
        return {
            size: this.cache.size,
            keys: Array.from(this.cache.keys())
        };
    }
}