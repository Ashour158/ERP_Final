/**
 * Complete ERP System V2.0 - Main UI Application
 * Handles all frontend interactions, API calls, and user interface logic
 */

class ERPApp {
    constructor() {
        this.API_BASE = window.location.origin;
        this.authToken = localStorage.getItem('erp_auth_token');
        this.currentUser = JSON.parse(localStorage.getItem('erp_current_user') || '{}');
        this.currentModule = 'dashboard';
        this.searchTimeout = null;
        
        this.init();
    }

    init() {
        // Check authentication status
        if (this.authToken && this.currentUser.id) {
            this.showMainApp();
            this.setupEventListeners();
            this.loadDashboard();
        } else {
            this.showLoginScreen();
        }
    }

    setupEventListeners() {
        // Login form
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }

        // Mobile menu toggle
        const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
        const sidebar = document.getElementById('sidebar');
        const sidebarOverlay = document.getElementById('sidebar-overlay');
        
        if (mobileMenuToggle) {
            mobileMenuToggle.addEventListener('click', () => {
                sidebar.classList.toggle('-translate-x-full');
                sidebarOverlay.classList.toggle('hidden');
            });
        }

        if (sidebarOverlay) {
            sidebarOverlay.addEventListener('click', () => {
                sidebar.classList.add('-translate-x-full');
                sidebarOverlay.classList.add('hidden');
            });
        }

        // Global search
        const globalSearch = document.getElementById('global-search');
        if (globalSearch) {
            globalSearch.addEventListener('input', (e) => this.handleGlobalSearch(e));
            globalSearch.addEventListener('focus', () => {
                document.getElementById('search-results').classList.remove('hidden');
            });
            
            // Close search results when clicking outside
            document.addEventListener('click', (e) => {
                if (!e.target.closest('#global-search') && !e.target.closest('#search-results')) {
                    document.getElementById('search-results').classList.add('hidden');
                }
            });
        }

        // User menu toggle
        const userMenuToggle = document.getElementById('user-menu-toggle');
        const userMenu = document.getElementById('user-menu');
        if (userMenuToggle && userMenu) {
            userMenuToggle.addEventListener('click', (e) => {
                e.stopPropagation();
                userMenu.classList.toggle('hidden');
            });

            // Close user menu when clicking outside
            document.addEventListener('click', (e) => {
                if (!e.target.closest('#user-menu-toggle') && !e.target.closest('#user-menu')) {
                    userMenu.classList.add('hidden');
                }
            });
        }

        // Quick create menu
        const quickCreateToggle = document.getElementById('quick-create-toggle');
        const quickCreateMenu = document.getElementById('quick-create-menu');
        if (quickCreateToggle && quickCreateMenu) {
            quickCreateToggle.addEventListener('click', (e) => {
                e.stopPropagation();
                quickCreateMenu.classList.toggle('hidden');
            });

            document.addEventListener('click', (e) => {
                if (!e.target.closest('#quick-create-toggle') && !e.target.closest('#quick-create-menu')) {
                    quickCreateMenu.classList.add('hidden');
                }
            });
        }

        // Navigation items
        document.querySelectorAll('.nav-item, .nav-subitem').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const module = item.getAttribute('data-module');
                if (module) {
                    this.loadModule(module);
                }
            });
        });

        // Navigation group toggles
        document.querySelectorAll('.nav-group-toggle').forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                e.preventDefault();
                const group = toggle.getAttribute('data-group');
                const submenu = document.querySelector(`[data-submenu="${group}"]`);
                if (submenu) {
                    submenu.classList.toggle('show');
                    toggle.classList.toggle('expanded');
                }
            });
        });

        // User menu actions
        document.querySelectorAll('[data-action]').forEach(action => {
            action.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleAction(action.getAttribute('data-action'));
            });
        });

        // GPS modal handlers
        const gpsAllow = document.getElementById('gps-allow');
        const gpsCancel = document.getElementById('gps-cancel');
        const gpsModal = document.getElementById('gps-modal');

        if (gpsAllow) {
            gpsAllow.addEventListener('click', () => {
                this.requestLocation().then(() => {
                    gpsModal.classList.add('hidden');
                });
            });
        }

        if (gpsCancel) {
            gpsCancel.addEventListener('click', () => {
                gpsModal.classList.add('hidden');
            });
        }

        // File upload handlers
        const fileSelect = document.getElementById('file-select');
        const fileInput = document.getElementById('file-input');
        const uploadConfirm = document.getElementById('upload-confirm');
        const uploadCancel = document.getElementById('upload-cancel');
        const uploadModal = document.getElementById('upload-modal');

        if (fileSelect && fileInput) {
            fileSelect.addEventListener('click', () => fileInput.click());
            fileInput.addEventListener('change', (e) => this.handleFileSelection(e));
        }

        if (uploadConfirm) {
            uploadConfirm.addEventListener('click', () => this.uploadFiles());
        }

        if (uploadCancel) {
            uploadCancel.addEventListener('click', () => {
                uploadModal.classList.add('hidden');
            });
        }
    }

    async handleLogin(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const credentials = {
            username: formData.get('username'),
            password: formData.get('password')
        };

        // Clear any previous errors
        const errorElement = document.getElementById('login-error');
        if (errorElement) {
            errorElement.classList.add('hidden');
        }

        try {
            this.showLoading();
            
            const response = await this.apiCall('/api/auth/login', {
                method: 'POST',
                body: JSON.stringify(credentials)
            });

            if (response.access_token) {
                this.authToken = response.access_token;
                this.currentUser = response.user;
                
                localStorage.setItem('erp_auth_token', this.authToken);
                localStorage.setItem('erp_current_user', JSON.stringify(this.currentUser));
                
                console.log('Login successful, showing main app');
                this.showMainApp();
                this.setupEventListeners();
                this.loadDashboard();
                this.showToast('Welcome back!', 'success');
            } else {
                console.error('Login response missing access_token:', response);
                this.showLoginError('Invalid credentials');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showLoginError(error.message || 'Login failed. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    async handleGlobalSearch(e) {
        const query = e.target.value.trim();
        const resultsContainer = document.getElementById('search-results');
        
        if (query.length < 2) {
            resultsContainer.classList.add('hidden');
            return;
        }

        // Debounce search
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(async () => {
            try {
                const response = await this.apiCall(`/api/search?q=${encodeURIComponent(query)}`);
                this.displaySearchResults(response);
                resultsContainer.classList.remove('hidden');
            } catch (error) {
                console.error('Search error:', error);
            }
        }, 300);
    }

    displaySearchResults(data) {
        const resultsContainer = document.getElementById('search-results');
        
        if (data.total_results === 0) {
            resultsContainer.innerHTML = `
                <div class="p-4 text-center text-gray-500">
                    <i class="fas fa-search text-2xl mb-2"></i>
                    <p>No results found for "${data.query}"</p>
                </div>
            `;
            return;
        }

        let html = `
            <div class="p-3 border-b border-gray-200 bg-gray-50">
                <span class="text-sm font-medium text-gray-700">${data.total_results} results for "${data.query}"</span>
            </div>
        `;

        Object.entries(data.results).forEach(([category, items]) => {
            if (items.length > 0) {
                html += `
                    <div class="p-2">
                        <h4 class="text-xs font-semibold text-gray-500 uppercase mb-2">${category}</h4>
                        ${items.map(item => `
                            <a href="${item.url}" class="block p-2 hover:bg-gray-50 rounded">
                                <div class="flex items-center">
                                    <div class="flex-1">
                                        <p class="text-sm font-medium text-gray-900">${item.name}</p>
                                        <p class="text-xs text-gray-500">${item.type}</p>
                                    </div>
                                    ${item.status ? `<span class="badge badge-gray">${item.status}</span>` : ''}
                                </div>
                            </a>
                        `).join('')}
                    </div>
                `;
            }
        });

        resultsContainer.innerHTML = html;
    }

    handleAction(action) {
        switch (action) {
            case 'logout':
                this.logout();
                break;
            case 'profile':
                this.loadModule('profile');
                break;
            case 'settings':
                this.loadModule('settings');
                break;
            case 'dark-mode-toggle':
                this.toggleDarkMode();
                break;
            case 'create-customer':
                this.showCreateModal('customer');
                break;
            case 'create-deal':
                this.showCreateModal('deal');
                break;
            case 'create-ticket':
                this.showCreateModal('ticket');
                break;
            case 'create-vendor':
                this.showCreateModal('vendor');
                break;
            default:
                console.log('Unknown action:', action);
        }
    }

    logout() {
        localStorage.removeItem('erp_auth_token');
        localStorage.removeItem('erp_current_user');
        this.authToken = null;
        this.currentUser = {};
        this.showLoginScreen();
        this.showToast('Logged out successfully', 'success');
    }

    toggleDarkMode() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('erp_theme', newTheme);
        
        this.showToast(`Switched to ${newTheme} mode`, 'success');
    }

    async loadModule(module) {
        if (this.currentModule === module) return;
        
        this.currentModule = module;
        this.updateActiveNavigation(module);
        
        try {
            this.showLoading();
            
            const contentArea = document.getElementById('content-area');
            
            switch (module) {
                case 'dashboard':
                    await this.loadDashboard();
                    break;
                case 'crm-customers':
                    await this.loadCustomers();
                    break;
                case 'crm-deals':
                    await this.loadDeals();
                    break;
                case 'crm-quotes':
                    await this.loadQuotes();
                    break;
                case 'finance-invoices':
                    await this.loadInvoices();
                    break;
                case 'hr-employees':
                    await this.loadEmployees();
                    break;
                case 'hr-attendance':
                    await this.loadAttendance();
                    break;
                case 'supply-inventory':
                    await this.loadInventory();
                    break;
                case 'desk-tickets':
                    await this.loadTickets();
                    break;
                case 'vendors':
                    await this.loadVendors();
                    break;
                case 'kpis':
                    await this.loadKPIs();
                    break;
                case 'vigilance':
                    await this.loadVigilanceAlerts();
                    break;
                default:
                    contentArea.innerHTML = `
                        <div class="card">
                            <div class="card-body text-center py-12">
                                <i class="fas fa-tools text-4xl text-gray-400 mb-4"></i>
                                <h3 class="text-lg font-semibold text-gray-900 mb-2">${module.replace('-', ' ').toUpperCase()}</h3>
                                <p class="text-gray-600">This module is under development.</p>
                            </div>
                        </div>
                    `;
            }
        } catch (error) {
            console.error('Error loading module:', error);
            this.showToast('Failed to load module', 'error');
        } finally {
            this.hideLoading();
        }
    }

    updateActiveNavigation(module) {
        // Remove active class from all nav items
        document.querySelectorAll('.nav-item, .nav-subitem').forEach(item => {
            item.classList.remove('active');
        });
        
        // Add active class to current module
        const activeItem = document.querySelector(`[data-module="${module}"]`);
        if (activeItem) {
            activeItem.classList.add('active');
            
            // If it's a submenu item, expand the parent group
            const parentGroup = activeItem.closest('.nav-submenu');
            if (parentGroup) {
                parentGroup.classList.add('show');
                const toggle = document.querySelector(`[data-group="${parentGroup.getAttribute('data-submenu')}"]`);
                if (toggle) {
                    toggle.classList.add('expanded');
                }
            }
        }
    }

    async loadDashboard() {
        const contentArea = document.getElementById('content-area');
        
        try {
            // Load dashboard data
            const kpisResponse = await this.apiCall('/api/kpis');
            const alertsResponse = await this.apiCall('/api/vigilance/alerts?per_page=5');
            
            contentArea.innerHTML = `
                <div class="mb-6">
                    <h1 class="text-2xl font-bold text-gray-900">Dashboard</h1>
                    <p class="text-gray-600">Welcome back, ${this.currentUser.first_name}!</p>
                </div>
                
                <!-- KPI Cards -->
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    ${this.renderKPICards(kpisResponse)}
                </div>
                
                <!-- Charts and Alerts -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div class="card">
                        <div class="card-header">
                            <h3 class="text-lg font-semibold">Recent Activity</h3>
                        </div>
                        <div class="card-body">
                            <div class="space-y-4">
                                <div class="flex items-center space-x-3">
                                    <div class="w-2 h-2 bg-blue-600 rounded-full"></div>
                                    <span class="text-sm text-gray-600">New customer added</span>
                                    <span class="text-xs text-gray-400 ml-auto">2 min ago</span>
                                </div>
                                <div class="flex items-center space-x-3">
                                    <div class="w-2 h-2 bg-green-600 rounded-full"></div>
                                    <span class="text-sm text-gray-600">Invoice paid</span>
                                    <span class="text-xs text-gray-400 ml-auto">1 hour ago</span>
                                </div>
                                <div class="flex items-center space-x-3">
                                    <div class="w-2 h-2 bg-yellow-600 rounded-full"></div>
                                    <span class="text-sm text-gray-600">Support ticket created</span>
                                    <span class="text-xs text-gray-400 ml-auto">3 hours ago</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <div class="card-header">
                            <h3 class="text-lg font-semibold">Vigilance Alerts</h3>
                        </div>
                        <div class="card-body">
                            ${this.renderVigilanceAlerts(alertsResponse.alerts || [])}
                        </div>
                    </div>
                </div>
            `;
            
            this.updateUserProfile();
        } catch (error) {
            console.error('Dashboard error:', error);
            contentArea.innerHTML = `
                <div class="card">
                    <div class="card-body text-center py-12">
                        <i class="fas fa-exclamation-triangle text-4xl text-red-400 mb-4"></i>
                        <h3 class="text-lg font-semibold text-gray-900 mb-2">Error Loading Dashboard</h3>
                        <p class="text-gray-600">Please try refreshing the page.</p>
                    </div>
                </div>
            `;
        }
    }

    renderKPICards(kpisData) {
        if (!kpisData.kpis_by_module || Object.keys(kpisData.kpis_by_module).length === 0) {
            return `
                <div class="col-span-full">
                    <div class="card">
                        <div class="card-body text-center py-8">
                            <i class="fas fa-chart-line text-4xl text-gray-400 mb-4"></i>
                            <p class="text-gray-600">No KPI data available yet. Start using the system to see your metrics.</p>
                        </div>
                    </div>
                </div>
            `;
        }

        let cards = '';
        let count = 0;
        
        Object.entries(kpisData.kpis_by_module).forEach(([module, kpis]) => {
            if (count >= 4) return; // Show only 4 cards
            
            kpis.forEach(kpi => {
                if (count >= 4) return;
                
                const achievementColor = kpi.achievement_percentage >= 100 ? 'text-green-600' : 
                                       kpi.achievement_percentage >= 70 ? 'text-yellow-600' : 'text-red-600';
                
                cards += `
                    <div class="card">
                        <div class="card-body">
                            <div class="flex items-center justify-between">
                                <div>
                                    <p class="text-sm font-medium text-gray-600">${kpi.kpi_name}</p>
                                    <p class="text-2xl font-bold text-gray-900">${kpi.current_value}${kpi.unit === 'percentage' ? '%' : ''}</p>
                                </div>
                                <div class="text-right">
                                    <p class="text-xs text-gray-500">${module.toUpperCase()}</p>
                                    <p class="text-sm font-medium ${achievementColor}">${kpi.achievement_percentage.toFixed(0)}%</p>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                count++;
            });
        });
        
        return cards;
    }

    renderVigilanceAlerts(alerts) {
        if (!alerts || alerts.length === 0) {
            return `
                <div class="text-center py-8">
                    <i class="fas fa-shield-alt text-4xl text-green-400 mb-4"></i>
                    <p class="text-gray-600">All systems are running smoothly!</p>
                </div>
            `;
        }

        return `
            <div class="space-y-3">
                ${alerts.map(alert => `
                    <div class="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                        <div class="w-2 h-2 ${this.getSeverityColor(alert.severity)} rounded-full"></div>
                        <div class="flex-1">
                            <p class="text-sm font-medium text-gray-900">${alert.title}</p>
                            <p class="text-xs text-gray-600">${alert.module} • ${alert.severity}</p>
                        </div>
                        <button class="text-xs text-blue-600 hover:text-blue-800" onclick="app.acknowledgeAlert(${alert.id})">
                            Acknowledge
                        </button>
                    </div>
                `).join('')}
            </div>
        `;
    }

    getSeverityColor(severity) {
        switch (severity) {
            case 'critical': return 'bg-red-600';
            case 'high': return 'bg-orange-600';
            case 'medium': return 'bg-yellow-600';
            case 'low': return 'bg-blue-600';
            default: return 'bg-gray-600';
        }
    }

    async acknowledgeAlert(alertId) {
        try {
            await this.apiCall(`/api/vigilance/alerts/${alertId}/acknowledge`, {
                method: 'POST'
            });
            this.showToast('Alert acknowledged', 'success');
            this.loadDashboard(); // Refresh dashboard
        } catch (error) {
            console.error('Error acknowledging alert:', error);
            this.showToast('Failed to acknowledge alert', 'error');
        }
    }

    async loadCustomers() {
        const contentArea = document.getElementById('content-area');
        
        try {
            const response = await this.apiCall('/api/crm/customers');
            
            contentArea.innerHTML = `
                <div class="mb-6 flex items-center justify-between">
                    <div>
                        <h1 class="text-2xl font-bold text-gray-900">Customers</h1>
                        <p class="text-gray-600">Manage your customer relationships</p>
                    </div>
                    <button class="btn btn-primary" onclick="app.showCreateModal('customer')">
                        <i class="fas fa-plus mr-2"></i>Add Customer
                    </button>
                </div>
                
                <div class="card">
                    <div class="card-body">
                        ${this.renderDataTable(response, [
                            { key: 'name', label: 'Name' },
                            { key: 'email', label: 'Email' },
                            { key: 'phone', label: 'Phone' },
                            { key: 'customer_type', label: 'Type' },
                            { key: 'status', label: 'Status', type: 'badge' },
                            { key: 'created_at', label: 'Created', type: 'date' }
                        ])}
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('Error loading customers:', error);
            this.showErrorPage('Failed to load customers');
        }
    }

    renderDataTable(data, columns) {
        if (!data || data.length === 0) {
            return `
                <div class="text-center py-12">
                    <i class="fas fa-inbox text-4xl text-gray-400 mb-4"></i>
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">No data found</h3>
                    <p class="text-gray-600">Start by adding some records.</p>
                </div>
            `;
        }

        return `
            <div class="overflow-x-auto">
                <table class="table">
                    <thead>
                        <tr>
                            ${columns.map(col => `<th>${col.label}</th>`).join('')}
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.map(row => `
                            <tr>
                                ${columns.map(col => `
                                    <td>
                                        ${this.formatTableCell(row[col.key], col.type)}
                                    </td>
                                `).join('')}
                                <td>
                                    <div class="flex space-x-2">
                                        <button class="btn btn-sm btn-secondary" onclick="app.viewRecord('${row.id}')">
                                            <i class="fas fa-eye"></i>
                                        </button>
                                        <button class="btn btn-sm btn-secondary" onclick="app.editRecord('${row.id}')">
                                            <i class="fas fa-edit"></i>
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    formatTableCell(value, type) {
        if (!value) return '-';
        
        switch (type) {
            case 'badge':
                return `<span class="badge badge-${this.getBadgeColor(value)}">${value}</span>`;
            case 'date':
                return new Date(value).toLocaleDateString();
            case 'currency':
                return `$${Number(value).toFixed(2)}`;
            default:
                return value;
        }
    }

    getBadgeColor(status) {
        const statusColors = {
            'active': 'success',
            'inactive': 'gray',
            'pending': 'warning',
            'completed': 'success',
            'cancelled': 'error',
            'open': 'primary',
            'closed': 'gray'
        };
        return statusColors[status.toLowerCase()] || 'gray';
    }

    updateUserProfile() {
        if (this.currentUser) {
            const userName = document.getElementById('user-name');
            const userRole = document.getElementById('user-role');
            const userInitials = document.getElementById('user-initials');
            
            if (userName) userName.textContent = `${this.currentUser.first_name} ${this.currentUser.last_name}`;
            if (userRole) userRole.textContent = this.currentUser.role || 'User';
            if (userInitials) {
                const initials = `${this.currentUser.first_name?.[0] || ''}${this.currentUser.last_name?.[0] || ''}`;
                userInitials.textContent = initials.toUpperCase();
            }
        }
    }

    async requestLocation() {
        return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject(new Error('Geolocation is not supported'));
                return;
            }

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const location = {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude,
                        accuracy: position.coords.accuracy
                    };
                    localStorage.setItem('last_location', JSON.stringify(location));
                    resolve(location);
                },
                (error) => {
                    reject(error);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 300000 // 5 minutes
                }
            );
        });
    }

    handleFileSelection(e) {
        const files = Array.from(e.target.files);
        const fileList = document.createElement('div');
        fileList.className = 'mt-4 space-y-2';
        
        files.forEach(file => {
            const fileItem = document.createElement('div');
            fileItem.className = 'flex items-center justify-between p-2 bg-gray-50 rounded';
            fileItem.innerHTML = `
                <span class="text-sm text-gray-700">${file.name}</span>
                <span class="text-xs text-gray-500">${this.formatFileSize(file.size)}</span>
            `;
            fileList.appendChild(fileItem);
        });
        
        const existingList = document.querySelector('#upload-modal .file-list');
        if (existingList) {
            existingList.remove();
        }
        
        fileList.className += ' file-list';
        document.querySelector('#upload-modal .modal-body').appendChild(fileList);
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async uploadFiles() {
        const fileInput = document.getElementById('file-input');
        const files = fileInput.files;
        
        if (files.length === 0) {
            this.showToast('Please select files to upload', 'warning');
            return;
        }

        const progressContainer = document.getElementById('upload-progress');
        const progressBar = document.getElementById('upload-progress-bar');
        const statusText = document.getElementById('upload-status');
        
        progressContainer.classList.remove('hidden');
        
        try {
            const uploadPromises = Array.from(files).map(async (file, index) => {
                const formData = new FormData();
                formData.append('file', file);
                
                const response = await fetch(`${this.API_BASE}/upload`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.authToken}`
                    },
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error(`Failed to upload ${file.name}`);
                }
                
                const result = await response.json();
                
                // Update progress
                const progress = ((index + 1) / files.length) * 100;
                progressBar.style.width = `${progress}%`;
                statusText.textContent = `Uploading ${index + 1} of ${files.length}...`;
                
                return result;
            });
            
            const results = await Promise.all(uploadPromises);
            
            this.showToast(`Successfully uploaded ${results.length} files`, 'success');
            document.getElementById('upload-modal').classList.add('hidden');
            
            // Reset form
            fileInput.value = '';
            progressContainer.classList.add('hidden');
            progressBar.style.width = '0%';
            
        } catch (error) {
            console.error('Upload error:', error);
            this.showToast('Upload failed', 'error');
            progressContainer.classList.add('hidden');
        }
    }

    showCreateModal(type) {
        // This would show a modal for creating new records
        this.showToast(`Create ${type} modal would open here`, 'info');
    }

    viewRecord(id) {
        this.showToast(`View record ${id}`, 'info');
    }

    editRecord(id) {
        this.showToast(`Edit record ${id}`, 'info');
    }

    showLoginScreen() {
        document.getElementById('login-screen').classList.remove('hidden');
        document.getElementById('main-app').classList.add('hidden');
    }

    showMainApp() {
        document.getElementById('login-screen').classList.add('hidden');
        document.getElementById('main-app').classList.remove('hidden');
    }

    showLoginError(message) {
        const errorElement = document.getElementById('login-error');
        errorElement.textContent = message;
        errorElement.classList.remove('hidden');
    }

    showLoading() {
        document.getElementById('loading-overlay').classList.remove('hidden');
    }

    hideLoading() {
        document.getElementById('loading-overlay').classList.add('hidden');
    }

    showErrorPage(message) {
        const contentArea = document.getElementById('content-area');
        contentArea.innerHTML = `
            <div class="card">
                <div class="card-body text-center py-12">
                    <i class="fas fa-exclamation-triangle text-4xl text-red-400 mb-4"></i>
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">Error</h3>
                    <p class="text-gray-600">${message}</p>
                    <button class="btn btn-primary mt-4" onclick="location.reload()">
                        Refresh Page
                    </button>
                </div>
            </div>
        `;
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-${this.getToastIcon(type)} mr-3"></i>
                <span class="flex-1">${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-3 text-gray-400 hover:text-gray-600">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        container.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }

    getToastIcon(type) {
        switch (type) {
            case 'success': return 'check-circle';
            case 'error': return 'exclamation-circle';
            case 'warning': return 'exclamation-triangle';
            default: return 'info-circle';
        }
    }

    async apiCall(endpoint, options = {}) {
        const config = {
            headers: {
                'Content-Type': 'application/json'
            },
            ...options
        };

        // Add auth header if token exists
        if (this.authToken) {
            config.headers['Authorization'] = `Bearer ${this.authToken}`;
        }

        try {
            const response = await fetch(`${this.API_BASE}${endpoint}`, config);
            
            if (!response.ok) {
                if (response.status === 401) {
                    // Token expired, redirect to login
                    console.log('Authentication expired, redirecting to login');
                    this.logout();
                    throw new Error('Authentication expired');
                }
                
                // Try to get error message from response
                let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                try {
                    const errorData = await response.json();
                    if (errorData.error || errorData.message) {
                        errorMessage = errorData.error || errorData.message;
                    }
                } catch (e) {
                    // Ignore JSON parse errors
                }
                
                throw new Error(errorMessage);
            }

            return response.json();
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    }
}

// Initialize the application when DOM is loaded
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new ERPApp();
    
    // Load saved theme
    const savedTheme = localStorage.getItem('erp_theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
    }
});

// Global functions for inline event handlers
window.app = app;