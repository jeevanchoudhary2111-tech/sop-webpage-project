// frontend/js/api.js
class ApiClient {
    constructor() {

        this.baseURL = `/api/v1`;
        this.token = localStorage.getItem('access_token');
    }

    setToken(token) {
        this.token = token;
        if (token) {
            localStorage.setItem('access_token', token);
        } else {
            localStorage.removeItem('access_token');
        }
    }

    getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        return headers;
    }

     // NEW: User-accessible SOP Definition Management
    async getAccessibleSOPDefinitions() {
        return await this.request('/sop-definitions');
    }  
     
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: this.getHeaders(),
            ...options,
        };

        console.log('Making API request to:', url);

        try {
            const response = await fetch(url, config);

            if (response.status === 401) {
                this.setToken(null);
                window.location.href = '/index.html';
                return;
            }

            const data = await response.json();

            if (!response.ok) {
                console.error('API request failed:', response.status, data);
                throw new Error(data.detail || 'Request failed');
            }

            return data;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // Auth methods
    async login(username, password) {
        const response = await this.request('/login', {
            method: 'POST',
            headers: { // Explicitly set headers here
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });

        if (response.access_token) {
            this.setToken(response.access_token);
            localStorage.setItem('user', JSON.stringify(response.user));
        }

        return response;
    }

    // Marked dates methods
    async markDate(date, description = null) {
        return await this.request('/marked-dates', {
            method: 'POST',
            body: JSON.stringify({
                marked_date: date,
                description: description
            }),
        });
    }

    async getMarkedDates() {
        return await this.request('/marked-dates');
    }

    async unmarkDate(date) {
        return await this.request(`/marked-dates/${date}`, {
            method: 'DELETE',
        });
    }

    async register(formData) {
        return await this.request('/register', {
            method: 'POST',
            headers: {}, // Let browser set content-type for FormData
            body: formData,
        });
    }

    async getProfile() {
        return await this.request('/profile');
    }

    async updateProfile(formData) {
        return await this.request('/profile', {
            method: 'PUT',
            headers: {}, // Let browser set content-type for FormData
            body: formData,
        });
    }

    // Admin methods
    async getUsers() {
        return await this.request('/admin/users');
    }

    async createUser(userData) {
        return await this.request('/admin/users', {
            method: 'POST',
            body: JSON.stringify(userData),
        });
    }

    async updateUser(userId, userData) {
        return await this.request(`/admin/users/${userId}`, {
            method: 'PUT',
            body: JSON.stringify(userData),
        });
    }

    async deleteUser(userId) {
        return await this.request(`/admin/users/${userId}`, {
            method: 'DELETE',
        });
    }

    async resetPassword(oldPassword, newPassword) {
        const formData = new FormData();
        formData.append('old_password', oldPassword);
        formData.append('new_password', newPassword);
        
        return await this.request('/reset-password', {
            method: 'POST',
            headers: {}, // Let browser set content-type for FormData
            body: formData,
        });
    }

    async getUserById(userId) {
        return await this.request(`/admin/users/${userId}`);
    }

    logout() {
        this.setToken(null);
        localStorage.removeItem('user');
        window.location.href = '/index.html';
    }

    isAuthenticated() {
        return !!this.token;
    }

    getCurrentUser() {
        const user = localStorage.getItem('user');
        return user ? JSON.parse(user) : null;
    }

    // SOP Activity methods
    async logSOPActivity(sopType, taskId, taskDescription) {
        try {
            return await this.request('/sop/activity', {
                method: 'POST',
                body: JSON.stringify({
                    sop_type: sopType,
                    task_id: taskId,
                    task_description: taskDescription
                }),
            });
        } catch (error) {
            if (error.message.includes('already completed')) {
                throw new Error(`Task locked: ${error.message}`);
            }
            throw error;
        }
    }

    async getUserSOPActivities(sopType = null) {
        const endpoint = sopType ? `/sop/activities?sop_type=${sopType}` : '/sop/activities';
        return await this.request(endpoint);
    }

    async getTodaySOPActivities(sopType = null) {
        const endpoint = sopType ? `/sop/activities/today?sop_type=${sopType}` : '/sop/activities/today';
        return await this.request(endpoint);
    }

    // Admin SOP methods
    async getAllSOPActivities(sopType = null, userId = null, days = 30) {
        let endpoint = `/admin/sop/activities?days=${days}`;
        if (sopType) endpoint += `&sop_type=${sopType}`;
        if (userId) endpoint += `&user_id=${userId}`;
        return await this.request(endpoint);
    }

    async downloadSOPReport(sopType = null, userId = null, days = 30, format = 'html') {
        let endpoint = `/admin/sop/report?format=${format}&days=${days}`;
        if (sopType) endpoint += `&sop_type=${sopType}`;
        if (userId) endpoint += `&user_id=${userId}`;

        const url = `${this.baseURL}${endpoint}`;
        const response = await fetch(url, {
            headers: this.getHeaders(),
        });

        if (!response.ok) {
            throw new Error('Failed to download report');
        }

        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        const extension = format === 'sop_styled' ? 'html' : (format === 'html' ? 'html' : 'csv');
        const sopTypeName = sopType ? `_${sopType}` : '';
        a.download = `sop_report${sopTypeName}_${new Date().toISOString().slice(0, 10)}.${extension}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(downloadUrl);
    }

    async getSOPSummary(sopType = null, days = 30) {
    }
    async getSOPSummary(sopType = null, days = 30, userId = null) {
        let endpoint = `/admin/sop/summary?days=${days}`;
        if (sopType) endpoint += `&sop_type=${sopType}`;
        if (userId) endpoint += `&user_id=${userId}`;
        return await this.request(endpoint);
    }

    // SOP Progress methods
    async getSOPProgress(sopType) {
        return await this.request(`/sop/progress?sop_type=${sopType}`);
    }

    async saveSOPProgress(sopType, completedTasks) {
        return await this.request('/sop/progress', {
            method: 'POST',
            body: JSON.stringify({
                sop_type: sopType,
                completed_tasks: completedTasks
            }),
        });
    }

    // Daily report methods
    async checkDailyReportAvailability() {
        return await this.request('/admin/daily-report/check');
    }

    async downloadDailyReport(sopType = null) {
        let url = `${this.baseURL}/admin/daily-report/download`;
        if (sopType) {
            url += `?sop_type=${sopType}`;
        }

        const response = await fetch(url, {
            headers: this.getHeaders(),
        });

        if (!response.ok) {
            throw new Error('Failed to download daily report');
        }

        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        const today = new Date().toISOString().slice(0, 10);
        const sopTypeName = sopType ? `_${sopType}` : '';
        a.download = `daily_sop_report${sopTypeName}_${today}.html`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(downloadUrl);
    }

    

    // Advanced admin functions
    async assignUserShift(userId, shift, exchanges) {
        return await this.request(`/admin/users/${userId}/shift`, {
            method: 'POST',
            body: JSON.stringify({ shift, exchanges })
        });
    }

    async getUsersByShift() {
        return await this.request('/admin/users/by-shift');
    }

    async generateAdvancedReport(filters) {
        const params = new URLSearchParams(filters);
        return await this.request(`/admin/reports/advanced?${params.toString()}`);
    }

    async listBackups() {
        return await this.request('/admin/backup/list');
    }

    async restoreBackup(backupDate, backupTime) {
        return await this.request('/admin/backup/restore', {
            method: 'POST',
            body: JSON.stringify({ 
                backup_date: backupDate, 
                backup_time: backupTime 
            })
        });
    }
    
    async createManualBackup() {
        return await this.request('/admin/backup/manual', {
            method: 'POST'
        });
    }
    
    async getArchivedCollections() {
        return await this.request('/admin/archived-collections');
    }

    async getArchivedData(collectionName) {
        return await this.request(`/admin/archived-data/${collectionName}`);
    }

    // SOP Type Management
    async getSOPTypesWithActivity() {
        return await this.request('/admin/sop-types');
    }

    async resetSOPTypeWithBackup(sopType) {
        const url = `${this.baseURL}/admin/reset-sop-type/${sopType}`;
        const response = await fetch(url, {
            method: 'POST',
            headers: this.getHeaders(),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to reset SOP type');
        }

        // Handle file download
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        
        // Extract filename from Content-Disposition header
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = `sop_backup_${sopType}_${new Date().toISOString().slice(0, 10)}.html`;
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="(.+)"/);
            if (filenameMatch) {
                filename = filenameMatch[1];
            }
        }
        
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(downloadUrl);
        
        return { message: 'SOP reset completed and backup downloaded' };
    }

  // Get today's SOP activities for a specific SOP type (for showing completion info)
  async getTodaySOPActivities(sopType) {
    const response = await this.request(`/sop/today-activities/${sopType}`);
    return response;
  }

  // Save US Position form data
  async saveUSPositionData(formData) {
    const response = await this.request('/sop/us-position-data', {
      method: 'POST',
      body: JSON.stringify({
        form_data: formData,
        date: new Date().toISOString().split('T')[0]
      })
    });
    return response;
  }
  
    // New method for US Position Report
    async downloadUSPositionReport(date = null) { 
        let endpoint = '/admin/us-position-report';
        if (date) { 
            endpoint += `?report_date=${date}`;
        }

        const url = `${this.baseURL}${endpoint}`;
        const response = await fetch(url, {
            headers: this.getHeaders(),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to download US Position report');
        }

        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        
        // Extract filename from Content-Disposition header
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = `us_position_report_${new Date().toISOString().slice(0, 10)}.html`; 
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="(.+)"/);
            if (filenameMatch && filenameMatch[1]) {
                filename = filenameMatch[1];
            }
        }
        
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(downloadUrl);
        
        return { message: 'US Position report downloaded successfully' };
    }

  // Get US Position form data
  async getUSPositionData() {
    const response = await this.request('/sop/us-position-data');
    return response;
  }

    async getAdminUSPositionActivities(days = 30) {
        let endpoint = `/admin/us-position-activities?days=${days}`;
        return await this.request(endpoint);
    }

    // This is where the resetAllSOPs method should be:
    async resetAllSOPs() {
        return await this.request('/admin/reset-all-sops', { method: 'POST' });
    }

    // NEW: SOP Definition Management
    async createSOPDefinition(sopData) {
        return await this.request('/admin/sop-definitions', {
            method: 'POST',
            body: JSON.stringify(sopData),
        });
    }

    async updateSOPDefinition(sopId, sopData) {
        return await this.request(`/admin/sop-definitions/${sopId}`, {
            method: 'PUT',
            body: JSON.stringify(sopData),
        });
    }

    async deleteSOPDefinition(sopId) {
        return await this.request(`/admin/sop-definitions/${sopId}`, {
            method: 'DELETE',
        });
    }
}

// Global API client instance
const api = new ApiClient();