// ERP System JavaScript Application
class ERPApp {
    constructor() {
        this.currentUser = null;
        this.authToken = null;
        this.API_BASE = '/api';
        this.currentModule = 'dashboard';
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkAuth();
    }

    bindEvents() {
        // Login form
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', this.handleLogin.bind(this));
        }

        // Module navigation
        document.querySelectorAll('.module-nav').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const module = e.currentTarget.getAttribute('onclick').match(/'([^']+)'/)[1];
                this.switchModule(module);
            });
        });
    }

    checkAuth() {
        const token = localStorage.getItem('auth_token');
        if (token) {
            this.authToken = token;
            this.loadUserProfile();
        } else {
            this.showLogin();
        }
    }

    async handleLogin(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const credentials = {
            username: formData.get('username'),
            password: formData.get('password')
        };

        // Add location if available
        try {
            const position = await this.getCurrentPosition();
            credentials.location = {
                lat: position.coords.latitude,
                lng: position.coords.longitude
            };
        } catch (error) {
            console.warn('Could not get location:', error);
        }

        try {
            const response = await this.apiCall('/auth/login', {
                method: 'POST',
                body: JSON.stringify(credentials)
            });

            this.authToken = response.access_token;
            this.currentUser = response.user;
            localStorage.setItem('auth_token', this.authToken);
            this.showMainApp();
            this.updateUserProfile();
            this.loadDashboard();
        } catch (error) {
            this.showError('login-error', error.message || 'Login failed');
        }
    }

    async loadUserProfile() {
        try {
            const response = await this.apiCall('/auth/profile');
            this.currentUser = response;
            this.showMainApp();
            this.updateUserProfile();
            this.loadDashboard();
        } catch (error) {
            console.error('Failed to load user profile:', error);
            this.logout();
        }
    }

    updateUserProfile() {
        if (this.currentUser) {
            document.getElementById('user-name').textContent = 
                `${this.currentUser.first_name} ${this.currentUser.last_name}`;
            document.getElementById('user-role').textContent = 
                this.currentUser.role.charAt(0).toUpperCase() + this.currentUser.role.slice(1);
            
            if (this.currentUser.profile_picture) {
                document.getElementById('user-avatar').src = this.currentUser.profile_picture;
            }
        }
    }

    logout() {
        localStorage.removeItem('auth_token');
        this.authToken = null;
        this.currentUser = null;
        this.showLogin();
    }

    showLogin() {
        this.hideAllScreens();
        document.getElementById('login-screen').style.display = 'flex';
    }

    showMainApp() {
        this.hideAllScreens();
        document.getElementById('main-app').style.display = 'block';
    }

    hideAllScreens() {
        document.getElementById('loading-screen').style.display = 'none';
        document.getElementById('login-screen').style.display = 'none';
        document.getElementById('main-app').style.display = 'none';
    }

    // API Helper Methods
    async apiCall(endpoint, options = {}) {
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...(this.authToken && { 'Authorization': `Bearer ${this.authToken}` })
            },
            ...options
        };

        try {
            const response = await fetch(`${this.API_BASE}${endpoint}`, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'API call failed');
            }
            
            return data;
        } catch (error) {
            console.error('API call error:', error);
            throw error;
        }
    }

    getCurrentPosition() {
        return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject(new Error('Geolocation not supported'));
                return;
            }
            navigator.geolocation.getCurrentPosition(resolve, reject);
        });
    }

    // Module Management
    switchModule(module) {
        this.currentModule = module;
        
        // Hide all modules
        document.querySelectorAll('.module-content').forEach(content => {
            content.classList.add('hidden');
        });

        // Show selected module
        const moduleElement = document.getElementById(`${module}-module`);
        if (moduleElement) {
            moduleElement.classList.remove('hidden');
        }

        // Update navigation
        document.querySelectorAll('.module-nav').forEach(nav => {
            nav.classList.remove('active');
        });

        const activeNav = document.querySelector(`[onclick*="${module}"]`);
        if (activeNav) {
            activeNav.classList.add('active');
        }

        // Load module data
        this.loadModuleData(module);
    }

    async loadModuleData(module) {
        switch (module) {
            case 'dashboard':
                await this.loadDashboard();
                break;
            case 'crm':
                await this.loadCRM();
                break;
            case 'finance':
                await this.loadFinance();
                break;
            case 'hr':
                await this.loadHR();
                break;
            case 'supply-chain':
                await this.loadSupplyChain();
                break;
            case 'desk':
                await this.loadDesk();
                break;
        }
    }

    // Dashboard Methods
    async loadDashboard() {
        try {
            // Load KPI data
            const [customers, employees, tickets] = await Promise.all([
                this.apiCall('/crm/customers').catch(() => []),
                this.apiCall('/hr/employees').catch(() => []),
                this.apiCall('/desk/tickets').catch(() => [])
            ]);

            document.getElementById('total-customers').textContent = customers.length || 0;
            document.getElementById('total-employees').textContent = employees.length || 0;
            document.getElementById('open-tickets').textContent = 
                tickets.filter(t => t.status === 'open').length || 0;
            document.getElementById('total-revenue').textContent = '$0'; // Placeholder
        } catch (error) {
            console.error('Failed to load dashboard:', error);
        }
    }

    // CRM Module Methods
    async loadCRM() {
        await this.loadCustomers();
    }

    async loadCustomers() {
        try {
            const customers = await this.apiCall('/crm/customers');
            const customersList = document.getElementById('customers-list');
            
            if (customers.length === 0) {
                customersList.innerHTML = '<p class="text-gray-500 text-center py-8">No customers found. Add your first customer!</p>';
                return;
            }

            customersList.innerHTML = customers.map(customer => `
                <div class="list-item">
                    <div class="flex justify-between items-start">
                        <div>
                            <h4 class="text-lg font-medium text-gray-900">${customer.name}</h4>
                            <p class="text-sm text-gray-600">${customer.email}</p>
                            <p class="text-sm text-gray-500">${customer.phone || 'No phone'}</p>
                        </div>
                        <div class="text-right">
                            <span class="status-badge ${customer.status}">${customer.status}</span>
                            <p class="text-sm text-gray-500 mt-1">${customer.customer_type || 'Standard'}</p>
                        </div>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Failed to load customers:', error);
            document.getElementById('customers-list').innerHTML = 
                '<p class="text-red-500 text-center py-8">Failed to load customers</p>';
        }
    }

    async loadDeals() {
        try {
            const deals = await this.apiCall('/crm/deals');
            const dealsList = document.getElementById('deals-list');
            
            if (deals.length === 0) {
                dealsList.innerHTML = '<p class="text-gray-500 text-center py-8">No deals found. Create your first deal!</p>';
                return;
            }

            dealsList.innerHTML = deals.map(deal => `
                <div class="list-item">
                    <div class="flex justify-between items-start">
                        <div>
                            <h4 class="text-lg font-medium text-gray-900">${deal.title}</h4>
                            <p class="text-sm text-gray-600">${deal.customer_name || 'Unknown Customer'}</p>
                            <p class="text-sm text-gray-500">Expected close: ${new Date(deal.expected_close_date).toLocaleDateString()}</p>
                        </div>
                        <div class="text-right">
                            <p class="text-lg font-semibold text-green-600">$${deal.amount}</p>
                            <span class="status-badge ${deal.stage}">${deal.stage}</span>
                        </div>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Failed to load deals:', error);
            document.getElementById('deals-list').innerHTML = 
                '<p class="text-red-500 text-center py-8">Failed to load deals</p>';
        }
    }

    async loadQuotes() {
        try {
            const quotes = await this.apiCall('/crm/quotes');
            const quotesList = document.getElementById('quotes-list');
            
            if (quotes.length === 0) {
                quotesList.innerHTML = '<p class="text-gray-500 text-center py-8">No quotes found. Create your first quote!</p>';
                return;
            }

            quotesList.innerHTML = quotes.map(quote => `
                <div class="list-item">
                    <div class="flex justify-between items-start">
                        <div>
                            <h4 class="text-lg font-medium text-gray-900">Quote #${quote.quote_number}</h4>
                            <p class="text-sm text-gray-600">${quote.customer_name || 'Unknown Customer'}</p>
                            <p class="text-sm text-gray-500">Valid until: ${new Date(quote.valid_until).toLocaleDateString()}</p>
                        </div>
                        <div class="text-right">
                            <p class="text-lg font-semibold text-green-600">$${quote.total_amount}</p>
                            <span class="status-badge ${quote.status}">${quote.status}</span>
                        </div>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Failed to load quotes:', error);
            document.getElementById('quotes-list').innerHTML = 
                '<p class="text-red-500 text-center py-8">Failed to load quotes</p>';
        }
    }

    // Finance Module Methods
    async loadFinance() {
        await this.loadInvoices();
    }

    async loadInvoices() {
        try {
            const invoices = await this.apiCall('/finance/invoices');
            const invoicesList = document.getElementById('invoices-list');
            
            if (invoices.length === 0) {
                invoicesList.innerHTML = '<p class="text-gray-500 text-center py-8">No invoices found. Create your first invoice!</p>';
                return;
            }

            invoicesList.innerHTML = invoices.map(invoice => `
                <div class="list-item">
                    <div class="flex justify-between items-start">
                        <div>
                            <h4 class="text-lg font-medium text-gray-900">Invoice #${invoice.invoice_number}</h4>
                            <p class="text-sm text-gray-600">${invoice.customer_name || 'Unknown Customer'}</p>
                            <p class="text-sm text-gray-500">Due: ${new Date(invoice.due_date).toLocaleDateString()}</p>
                        </div>
                        <div class="text-right">
                            <p class="text-lg font-semibold text-green-600">$${invoice.total_amount}</p>
                            <span class="status-badge ${invoice.status}">${invoice.status}</span>
                        </div>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Failed to load invoices:', error);
            document.getElementById('invoices-list').innerHTML = 
                '<p class="text-red-500 text-center py-8">Failed to load invoices</p>';
        }
    }

    async loadVendorPayments() {
        try {
            const payments = await this.apiCall('/finance/vendor-payments');
            const paymentsList = document.getElementById('vendor-payments-list');
            
            if (payments.length === 0) {
                paymentsList.innerHTML = '<p class="text-gray-500 text-center py-8">No vendor payments found.</p>';
                return;
            }

            paymentsList.innerHTML = payments.map(payment => `
                <div class="list-item">
                    <div class="flex justify-between items-start">
                        <div>
                            <h4 class="text-lg font-medium text-gray-900">Payment #${payment.payment_number}</h4>
                            <p class="text-sm text-gray-600">${payment.vendor_name || 'Unknown Vendor'}</p>
                            <p class="text-sm text-gray-500">Date: ${new Date(payment.payment_date).toLocaleDateString()}</p>
                        </div>
                        <div class="text-right">
                            <p class="text-lg font-semibold text-red-600">$${payment.amount}</p>
                            <span class="status-badge ${payment.status}">${payment.status}</span>
                        </div>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Failed to load vendor payments:', error);
            document.getElementById('vendor-payments-list').innerHTML = 
                '<p class="text-red-500 text-center py-8">Failed to load vendor payments</p>';
        }
    }

    // HR Module Methods
    async loadHR() {
        await this.loadEmployees();
    }

    async loadEmployees() {
        try {
            const employees = await this.apiCall('/hr/employees');
            const employeesList = document.getElementById('employees-list');
            
            if (employees.length === 0) {
                employeesList.innerHTML = '<p class="text-gray-500 text-center py-8">No employees found. Add your first employee!</p>';
                return;
            }

            employeesList.innerHTML = employees.map(employee => `
                <div class="list-item">
                    <div class="flex justify-between items-start">
                        <div>
                            <h4 class="text-lg font-medium text-gray-900">${employee.first_name} ${employee.last_name}</h4>
                            <p class="text-sm text-gray-600">${employee.position || 'No position'}</p>
                            <p class="text-sm text-gray-500">${employee.department || 'No department'}</p>
                        </div>
                        <div class="text-right">
                            <span class="status-badge ${employee.employment_status}">${employee.employment_status}</span>
                            <p class="text-sm text-gray-500 mt-1">ID: ${employee.employee_id}</p>
                        </div>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Failed to load employees:', error);
            document.getElementById('employees-list').innerHTML = 
                '<p class="text-red-500 text-center py-8">Failed to load employees</p>';
        }
    }

    async loadLeaveRequests() {
        try {
            const requests = await this.apiCall('/hr/leave-requests');
            const requestsList = document.getElementById('leave-requests-list');
            
            if (requests.length === 0) {
                requestsList.innerHTML = '<p class="text-gray-500 text-center py-8">No leave requests found.</p>';
                return;
            }

            requestsList.innerHTML = requests.map(request => `
                <div class="list-item">
                    <div class="flex justify-between items-start">
                        <div>
                            <h4 class="text-lg font-medium text-gray-900">${request.leave_type}</h4>
                            <p class="text-sm text-gray-600">${request.employee_name || 'Unknown Employee'}</p>
                            <p class="text-sm text-gray-500">${new Date(request.start_date).toLocaleDateString()} - ${new Date(request.end_date).toLocaleDateString()}</p>
                        </div>
                        <div class="text-right">
                            <span class="status-badge ${request.status}">${request.status}</span>
                            <p class="text-sm text-gray-500 mt-1">${request.days_requested} days</p>
                        </div>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Failed to load leave requests:', error);
            document.getElementById('leave-requests-list').innerHTML = 
                '<p class="text-red-500 text-center py-8">Failed to load leave requests</p>';
        }
    }

    async loadTrainingPrograms() {
        try {
            const programs = await this.apiCall('/hr/training-programs');
            const programsList = document.getElementById('training-list');
            
            if (programs.length === 0) {
                programsList.innerHTML = '<p class="text-gray-500 text-center py-8">No training programs found.</p>';
                return;
            }

            programsList.innerHTML = programs.map(program => `
                <div class="list-item">
                    <div class="flex justify-between items-start">
                        <div>
                            <h4 class="text-lg font-medium text-gray-900">${program.title}</h4>
                            <p class="text-sm text-gray-600">${program.description}</p>
                            <p class="text-sm text-gray-500">Duration: ${program.duration_hours} hours</p>
                        </div>
                        <div class="text-right">
                            <span class="status-badge ${program.status}">${program.status}</span>
                            <p class="text-sm text-gray-500 mt-1">${program.enrolled_count || 0} enrolled</p>
                        </div>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Failed to load training programs:', error);
            document.getElementById('training-list').innerHTML = 
                '<p class="text-red-500 text-center py-8">Failed to load training programs</p>';
        }
    }

    async loadPayroll() {
        try {
            const payroll = await this.apiCall('/hr/payroll');
            const payrollList = document.getElementById('payroll-list');
            
            if (payroll.length === 0) {
                payrollList.innerHTML = '<p class="text-gray-500 text-center py-8">No payroll records found.</p>';
                return;
            }

            payrollList.innerHTML = payroll.map(record => `
                <div class="list-item">
                    <div class="flex justify-between items-start">
                        <div>
                            <h4 class="text-lg font-medium text-gray-900">${record.employee_name}</h4>
                            <p class="text-sm text-gray-600">Pay period: ${new Date(record.pay_period_start).toLocaleDateString()} - ${new Date(record.pay_period_end).toLocaleDateString()}</p>
                            <p class="text-sm text-gray-500">Processed: ${new Date(record.processed_date).toLocaleDateString()}</p>
                        </div>
                        <div class="text-right">
                            <p class="text-lg font-semibold text-green-600">$${record.net_pay}</p>
                            <span class="status-badge ${record.status}">${record.status}</span>
                        </div>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Failed to load payroll:', error);
            document.getElementById('payroll-list').innerHTML = 
                '<p class="text-red-500 text-center py-8">Failed to load payroll</p>';
        }
    }

    // Supply Chain Module Methods
    async loadSupplyChain() {
        await this.loadInventory();
    }

    async loadInventory() {
        try {
            const inventory = await this.apiCall('/supply-chain/inventory');
            const inventoryList = document.getElementById('inventory-list');
            
            if (inventory.length === 0) {
                inventoryList.innerHTML = '<p class="text-gray-500 text-center py-8">No inventory items found. Add your first item!</p>';
                return;
            }

            inventoryList.innerHTML = inventory.map(item => `
                <div class="list-item">
                    <div class="flex justify-between items-start">
                        <div>
                            <h4 class="text-lg font-medium text-gray-900">${item.name}</h4>
                            <p class="text-sm text-gray-600">SKU: ${item.sku}</p>
                            <p class="text-sm text-gray-500">Category: ${item.category || 'Uncategorized'}</p>
                        </div>
                        <div class="text-right">
                            <p class="text-lg font-semibold ${item.current_stock < item.minimum_stock ? 'text-red-600' : 'text-green-600'}">
                                ${item.current_stock} units
                            </p>
                            <p class="text-sm text-gray-500">Min: ${item.minimum_stock}</p>
                        </div>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Failed to load inventory:', error);
            document.getElementById('inventory-list').innerHTML = 
                '<p class="text-red-500 text-center py-8">Failed to load inventory</p>';
        }
    }

    async loadPurchaseOrders() {
        try {
            const orders = await this.apiCall('/supply-chain/purchase-orders');
            const ordersList = document.getElementById('purchase-orders-list');
            
            if (orders.length === 0) {
                ordersList.innerHTML = '<p class="text-gray-500 text-center py-8">No purchase orders found.</p>';
                return;
            }

            ordersList.innerHTML = orders.map(order => `
                <div class="list-item">
                    <div class="flex justify-between items-start">
                        <div>
                            <h4 class="text-lg font-medium text-gray-900">PO #${order.po_number}</h4>
                            <p class="text-sm text-gray-600">${order.vendor_name || 'Unknown Vendor'}</p>
                            <p class="text-sm text-gray-500">Expected: ${new Date(order.expected_delivery_date).toLocaleDateString()}</p>
                        </div>
                        <div class="text-right">
                            <p class="text-lg font-semibold text-green-600">$${order.total_amount}</p>
                            <span class="status-badge ${order.status}">${order.status}</span>
                        </div>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Failed to load purchase orders:', error);
            document.getElementById('purchase-orders-list').innerHTML = 
                '<p class="text-red-500 text-center py-8">Failed to load purchase orders</p>';
        }
    }

    async loadShipments() {
        try {
            const shipments = await this.apiCall('/supply-chain/courier-shipments');
            const shipmentsList = document.getElementById('shipments-list');
            
            if (shipments.length === 0) {
                shipmentsList.innerHTML = '<p class="text-gray-500 text-center py-8">No shipments found.</p>';
                return;
            }

            shipmentsList.innerHTML = shipments.map(shipment => `
                <div class="list-item">
                    <div class="flex justify-between items-start">
                        <div>
                            <h4 class="text-lg font-medium text-gray-900">Shipment #${shipment.tracking_number}</h4>
                            <p class="text-sm text-gray-600">${shipment.courier_service}</p>
                            <p class="text-sm text-gray-500">To: ${shipment.destination_address}</p>
                        </div>
                        <div class="text-right">
                            <span class="status-badge ${shipment.shipment_status}">${shipment.shipment_status}</span>
                            <p class="text-sm text-gray-500 mt-1">Weight: ${shipment.weight} kg</p>
                        </div>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Failed to load shipments:', error);
            document.getElementById('shipments-list').innerHTML = 
                '<p class="text-red-500 text-center py-8">Failed to load shipments</p>';
        }
    }

    // Desk Module Methods
    async loadDesk() {
        await this.loadTickets();
    }

    async loadTickets() {
        try {
            const tickets = await this.apiCall('/desk/tickets');
            const ticketsList = document.getElementById('tickets-list');
            
            if (tickets.length === 0) {
                ticketsList.innerHTML = '<p class="text-gray-500 text-center py-8">No tickets found. Create your first ticket!</p>';
                return;
            }

            ticketsList.innerHTML = tickets.map(ticket => `
                <div class="list-item">
                    <div class="flex justify-between items-start">
                        <div>
                            <h4 class="text-lg font-medium text-gray-900">Ticket #${ticket.ticket_number}</h4>
                            <p class="text-sm text-gray-600">${ticket.subject}</p>
                            <p class="text-sm text-gray-500">From: ${ticket.customer_name || 'Unknown'}</p>
                        </div>
                        <div class="text-right">
                            <span class="status-badge ${ticket.priority}">${ticket.priority}</span>
                            <span class="status-badge ${ticket.status}">${ticket.status}</span>
                        </div>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Failed to load tickets:', error);
            document.getElementById('tickets-list').innerHTML = 
                '<p class="text-red-500 text-center py-8">Failed to load tickets</p>';
        }
    }

    async loadWorkOrders() {
        try {
            const workOrders = await this.apiCall('/desk/work-orders');
            const workOrdersList = document.getElementById('work-orders-list');
            
            if (workOrders.length === 0) {
                workOrdersList.innerHTML = '<p class="text-gray-500 text-center py-8">No work orders found.</p>';
                return;
            }

            workOrdersList.innerHTML = workOrders.map(wo => `
                <div class="list-item">
                    <div class="flex justify-between items-start">
                        <div>
                            <h4 class="text-lg font-medium text-gray-900">WO #${wo.wo_number}</h4>
                            <p class="text-sm text-gray-600">${wo.title}</p>
                            <p class="text-sm text-gray-500">Assigned: ${wo.assigned_to_name || 'Unassigned'}</p>
                        </div>
                        <div class="text-right">
                            <span class="status-badge ${wo.priority}">${wo.priority}</span>
                            <span class="status-badge ${wo.status}">${wo.status}</span>
                        </div>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Failed to load work orders:', error);
            document.getElementById('work-orders-list').innerHTML = 
                '<p class="text-red-500 text-center py-8">Failed to load work orders</p>';
        }
    }

    // Tab Management Methods
    switchCRMTab(tab) {
        this.switchTab('crm', tab);
        if (tab === 'customers') this.loadCustomers();
        else if (tab === 'deals') this.loadDeals();
        else if (tab === 'quotes') this.loadQuotes();
    }

    switchFinanceTab(tab) {
        this.switchTab('finance', tab);
        if (tab === 'invoices') this.loadInvoices();
        else if (tab === 'vendor-payments') this.loadVendorPayments();
    }

    switchHRTab(tab) {
        this.switchTab('hr', tab);
        if (tab === 'employees') this.loadEmployees();
        else if (tab === 'leave-requests') this.loadLeaveRequests();
        else if (tab === 'training') this.loadTrainingPrograms();
        else if (tab === 'payroll') this.loadPayroll();
    }

    switchSupplyChainTab(tab) {
        this.switchTab('supply-chain', tab);
        if (tab === 'inventory') this.loadInventory();
        else if (tab === 'purchase-orders') this.loadPurchaseOrders();
        else if (tab === 'shipments') this.loadShipments();
    }

    switchDeskTab(tab) {
        this.switchTab('desk', tab);
        if (tab === 'tickets') this.loadTickets();
        else if (tab === 'work-orders') this.loadWorkOrders();
    }

    switchTab(module, tab) {
        // Hide all tab contents
        document.querySelectorAll(`.${module}-tab-content`).forEach(content => {
            content.classList.add('hidden');
        });

        // Show selected tab content
        const tabContent = document.getElementById(`${tab}-tab`);
        if (tabContent) {
            tabContent.classList.remove('hidden');
        }

        // Update tab navigation
        document.querySelectorAll(`.${module}-tab`).forEach(tabBtn => {
            tabBtn.classList.remove('active');
        });

        const activeTabBtn = document.querySelector(`[onclick*="${tab}"]`);
        if (activeTabBtn) {
            activeTabBtn.classList.add('active');
        }
    }

    // Attendance Methods
    async checkIn() {
        try {
            const position = await this.getCurrentPosition();
            const response = await this.apiCall('/hr/attendance/checkin', {
                method: 'POST',
                body: JSON.stringify({
                    location: {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude
                    }
                })
            });
            alert('Checked in successfully!');
        } catch (error) {
            alert('Check-in failed: ' + (error.message || 'Unknown error'));
        }
    }

    async checkOut() {
        try {
            const position = await this.getCurrentPosition();
            const response = await this.apiCall('/hr/attendance/checkout', {
                method: 'POST',
                body: JSON.stringify({
                    location: {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude
                    }
                })
            });
            alert('Checked out successfully!');
        } catch (error) {
            alert('Check-out failed: ' + (error.message || 'Unknown error'));
        }
    }

    // Utility Methods
    showError(elementId, message) {
        const errorElement = document.getElementById(elementId);
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.classList.remove('hidden');
        }
    }

    hideError(elementId) {
        const errorElement = document.getElementById(elementId);
        if (errorElement) {
            errorElement.classList.add('hidden');
        }
    }
}

// Global functions for HTML onclick events
function switchModule(module) {
    window.erpApp.switchModule(module);
}

function switchCRMTab(tab) {
    window.erpApp.switchCRMTab(tab);
}

function switchFinanceTab(tab) {
    window.erpApp.switchFinanceTab(tab);
}

function switchHRTab(tab) {
    window.erpApp.switchHRTab(tab);
}

function switchSupplyChainTab(tab) {
    window.erpApp.switchSupplyChainTab(tab);
}

function switchDeskTab(tab) {
    window.erpApp.switchDeskTab(tab);
}

function logout() {
    window.erpApp.logout();
}

function checkIn() {
    window.erpApp.checkIn();
}

function checkOut() {
    window.erpApp.checkOut();
}

// Placeholder functions for modal operations (can be implemented as needed)
function showAddCustomerModal() { alert('Add Customer modal - to be implemented'); }
function showAddDealModal() { alert('Add Deal modal - to be implemented'); }
function showAddQuoteModal() { alert('Add Quote modal - to be implemented'); }
function showAddInvoiceModal() { alert('Add Invoice modal - to be implemented'); }
function showAddVendorPaymentModal() { alert('Add Vendor Payment modal - to be implemented'); }
function showAddEmployeeModal() { alert('Add Employee modal - to be implemented'); }
function showAddLeaveRequestModal() { alert('Add Leave Request modal - to be implemented'); }
function showAddTrainingModal() { alert('Add Training Program modal - to be implemented'); }
function showAddPayrollModal() { alert('Process Payroll modal - to be implemented'); }
function showAddInventoryModal() { alert('Add Inventory Item modal - to be implemented'); }
function showAddPurchaseOrderModal() { alert('Create Purchase Order modal - to be implemented'); }
function showAddShipmentModal() { alert('Create Shipment modal - to be implemented'); }
function showAddTicketModal() { alert('Create Ticket modal - to be implemented'); }
function showAddWorkOrderModal() { alert('Create Work Order modal - to be implemented'); }

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Hide loading screen after a brief delay
    setTimeout(() => {
        document.getElementById('loading-screen').style.display = 'none';
        window.erpApp = new ERPApp();
    }, 1000);
});