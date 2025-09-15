/**
 * ERP System Frontend JavaScript
 * Handles authentication, API calls, and UI interactions
 */

// Global variables
let baseURL = '';
let authToken = '';

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Initialize the application
 */
function initializeApp() {
    // Detect base URL
    baseURL = window.location.origin;
    document.getElementById('base-url').textContent = baseURL;
    
    // Check for existing auth token
    authToken = localStorage.getItem('access_token');
    if (authToken) {
        showAuthenticatedState();
    }
    
    // Set up event listeners
    setupEventListeners();
    
    logOutput('Application initialized. Base URL: ' + baseURL);
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    // Health check button
    document.getElementById('health-check-btn').addEventListener('click', performHealthCheck);
    
    // Login form
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    
    // Profile button
    document.getElementById('profile-btn').addEventListener('click', getUserProfile);
    
    // Logout button
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
    
    // Clear output button
    document.getElementById('clear-output-btn').addEventListener('click', clearOutput);
}

/**
 * API Helper Functions
 */

/**
 * Make an authenticated API request
 */
async function apiRequest(endpoint, options = {}) {
    const url = baseURL + endpoint;
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    const requestOptions = {
        headers,
        ...options
    };
    
    try {
        logOutput(`Making ${options.method || 'GET'} request to: ${endpoint}`);
        const response = await fetch(url, requestOptions);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${data.message || 'Request failed'}`);
        }
        
        logOutput(`✅ Success: ${JSON.stringify(data, null, 2)}`);
        return data;
    } catch (error) {
        logOutput(`❌ Error: ${error.message}`, 'error');
        throw error;
    }
}

/**
 * Authentication Functions
 */

async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
        const response = await apiRequest('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
        
        authToken = response.access_token;
        localStorage.setItem('access_token', authToken);
        
        showAuthenticatedState();
        logOutput('✅ Login successful!', 'success');
    } catch (error) {
        logOutput(`❌ Login failed: ${error.message}`, 'error');
    }
}

function handleLogout() {
    authToken = '';
    localStorage.removeItem('access_token');
    showUnauthenticatedState();
    logOutput('Logged out successfully', 'success');
}

async function getUserProfile() {
    try {
        const profile = await apiRequest('/api/auth/profile');
        document.getElementById('profile-data').innerHTML = `
            <h4>Profile Information</h4>
            <pre>${JSON.stringify(profile, null, 2)}</pre>
        `;
    } catch (error) {
        logOutput(`❌ Failed to get profile: ${error.message}`, 'error');
    }
}

/**
 * UI State Management
 */

function showAuthenticatedState() {
    document.getElementById('auth-section').style.display = 'none';
    document.getElementById('profile-section').style.display = 'block';
    document.getElementById('modules-container').style.display = 'block';
    document.getElementById('user-info').style.display = 'inline';
    document.getElementById('logout-btn').style.display = 'inline';
    document.getElementById('user-info').textContent = 'Logged in';
}

function showUnauthenticatedState() {
    document.getElementById('auth-section').style.display = 'block';
    document.getElementById('profile-section').style.display = 'none';
    document.getElementById('modules-container').style.display = 'none';
    document.getElementById('user-info').style.display = 'none';
    document.getElementById('logout-btn').style.display = 'none';
    document.getElementById('profile-data').innerHTML = '';
}

/**
 * Health Check Function
 */

async function performHealthCheck() {
    try {
        const health = await apiRequest('/health');
        logOutput('🔧 Health Check Results:', 'success');
        logOutput(JSON.stringify(health, null, 2));
    } catch (error) {
        logOutput(`❌ Health check failed: ${error.message}`, 'error');
    }
}

/**
 * CRM Module Functions
 */

async function listCustomers() {
    try {
        const customers = await apiRequest('/api/crm/customers');
        logOutput('📋 Customers List:', 'success');
    } catch (error) {
        logOutput(`❌ Failed to list customers: ${error.message}`, 'error');
    }
}

function showCreateCustomerForm() {
    const form = createDynamicForm('Create Customer', [
        { name: 'name', label: 'Customer Name', type: 'text', required: true },
        { name: 'email', label: 'Email', type: 'email', required: true },
        { name: 'phone', label: 'Phone', type: 'text' },
        { name: 'address', label: 'Address', type: 'textarea' }
    ], async (formData) => {
        await apiRequest('/api/crm/customers', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
    });
    showDynamicForm(form);
}

async function listDeals() {
    try {
        const deals = await apiRequest('/api/crm/deals');
        logOutput('💼 Deals List:', 'success');
    } catch (error) {
        logOutput(`❌ Failed to list deals: ${error.message}`, 'error');
    }
}

function showCreateDealForm() {
    const form = createDynamicForm('Create Deal', [
        { name: 'title', label: 'Deal Title', type: 'text', required: true },
        { name: 'amount', label: 'Amount', type: 'number', required: true },
        { name: 'customer_id', label: 'Customer ID', type: 'number', required: true },
        { name: 'stage', label: 'Stage', type: 'text' },
        { name: 'description', label: 'Description', type: 'textarea' }
    ], async (formData) => {
        await apiRequest('/api/crm/deals', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
    });
    showDynamicForm(form);
}

async function listQuotes() {
    try {
        const quotes = await apiRequest('/api/crm/quotes');
        logOutput('📄 Quotes List:', 'success');
    } catch (error) {
        logOutput(`❌ Failed to list quotes: ${error.message}`, 'error');
    }
}

function showCreateQuoteForm() {
    const form = createDynamicForm('Create Quote', [
        { name: 'title', label: 'Quote Title', type: 'text', required: true },
        { name: 'amount', label: 'Amount', type: 'number', required: true },
        { name: 'customer_id', label: 'Customer ID', type: 'number', required: true },
        { name: 'valid_until', label: 'Valid Until', type: 'date' },
        { name: 'description', label: 'Description', type: 'textarea' }
    ], async (formData) => {
        await apiRequest('/api/crm/quotes', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
    });
    showDynamicForm(form);
}

function showSalesCheckinForm() {
    const form = createDynamicForm('Sales Rep Check-in', [
        { name: 'location', label: 'Location', type: 'text', required: true },
        { name: 'customer_visited', label: 'Customer Visited', type: 'text' },
        { name: 'notes', label: 'Notes', type: 'textarea' }
    ], async (formData) => {
        await apiRequest('/api/crm/checkin', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
    });
    showDynamicForm(form);
}

/**
 * Finance Module Functions
 */

async function listInvoices() {
    try {
        const invoices = await apiRequest('/api/finance/invoices');
        logOutput('🧾 Invoices List:', 'success');
    } catch (error) {
        logOutput(`❌ Failed to list invoices: ${error.message}`, 'error');
    }
}

function showCreateInvoiceForm() {
    const form = createDynamicForm('Create Invoice', [
        { name: 'customer_id', label: 'Customer ID', type: 'number', required: true },
        { name: 'amount', label: 'Amount', type: 'number', required: true },
        { name: 'due_date', label: 'Due Date', type: 'date', required: true },
        { name: 'description', label: 'Description', type: 'textarea' }
    ], async (formData) => {
        await apiRequest('/api/finance/invoices', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
    });
    showDynamicForm(form);
}

async function listVendorPayments() {
    try {
        const payments = await apiRequest('/api/finance/vendor-payments');
        logOutput('💰 Vendor Payments List:', 'success');
    } catch (error) {
        logOutput(`❌ Failed to list vendor payments: ${error.message}`, 'error');
    }
}

async function processVendorPaymentSummary() {
    try {
        const summary = await apiRequest('/api/finance/vendor-payments', {
            method: 'POST',
            body: JSON.stringify({ action: 'process_summary' })
        });
        logOutput('📊 Vendor Payment Summary Processed:', 'success');
    } catch (error) {
        logOutput(`❌ Failed to process vendor payment summary: ${error.message}`, 'error');
    }
}

/**
 * HR Module Functions
 */

async function listEmployees() {
    try {
        const employees = await apiRequest('/api/hr/employees');
        logOutput('👥 Employees List:', 'success');
    } catch (error) {
        logOutput(`❌ Failed to list employees: ${error.message}`, 'error');
    }
}

function showCreateEmployeeForm() {
    const form = createDynamicForm('Create Employee', [
        { name: 'first_name', label: 'First Name', type: 'text', required: true },
        { name: 'last_name', label: 'Last Name', type: 'text', required: true },
        { name: 'email', label: 'Email', type: 'email', required: true },
        { name: 'phone', label: 'Phone', type: 'text' },
        { name: 'department', label: 'Department', type: 'text' },
        { name: 'position', label: 'Position', type: 'text' },
        { name: 'salary', label: 'Salary', type: 'number' }
    ], async (formData) => {
        await apiRequest('/api/hr/employees', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
    });
    showDynamicForm(form);
}

async function attendanceCheckin() {
    try {
        const checkin = await apiRequest('/api/hr/attendance/checkin', {
            method: 'POST',
            body: JSON.stringify({ timestamp: new Date().toISOString() })
        });
        logOutput('✅ Attendance Check-in Successful:', 'success');
    } catch (error) {
        logOutput(`❌ Failed to check in: ${error.message}`, 'error');
    }
}

async function attendanceCheckout() {
    try {
        const checkout = await apiRequest('/api/hr/attendance/checkout', {
            method: 'POST',
            body: JSON.stringify({ timestamp: new Date().toISOString() })
        });
        logOutput('✅ Attendance Check-out Successful:', 'success');
    } catch (error) {
        logOutput(`❌ Failed to check out: ${error.message}`, 'error');
    }
}

async function listLeaveRequests() {
    try {
        const leaveRequests = await apiRequest('/api/hr/leave-requests');
        logOutput('🏖️ Leave Requests List:', 'success');
    } catch (error) {
        logOutput(`❌ Failed to list leave requests: ${error.message}`, 'error');
    }
}

function showCreateLeaveRequestForm() {
    const form = createDynamicForm('Create Leave Request', [
        { name: 'start_date', label: 'Start Date', type: 'date', required: true },
        { name: 'end_date', label: 'End Date', type: 'date', required: true },
        { name: 'leave_type', label: 'Leave Type', type: 'text', required: true },
        { name: 'reason', label: 'Reason', type: 'textarea' }
    ], async (formData) => {
        await apiRequest('/api/hr/leave-requests', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
    });
    showDynamicForm(form);
}

async function listTrainingPrograms() {
    try {
        const programs = await apiRequest('/api/hr/training-programs');
        logOutput('🎓 Training Programs List:', 'success');
    } catch (error) {
        logOutput(`❌ Failed to list training programs: ${error.message}`, 'error');
    }
}

function showCreateTrainingProgramForm() {
    const form = createDynamicForm('Create Training Program', [
        { name: 'title', label: 'Program Title', type: 'text', required: true },
        { name: 'description', label: 'Description', type: 'textarea', required: true },
        { name: 'start_date', label: 'Start Date', type: 'date', required: true },
        { name: 'duration_hours', label: 'Duration (hours)', type: 'number' },
        { name: 'instructor', label: 'Instructor', type: 'text' }
    ], async (formData) => {
        await apiRequest('/api/hr/training-programs', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
    });
    showDynamicForm(form);
}

async function listPayroll() {
    try {
        const payroll = await apiRequest('/api/hr/payroll');
        logOutput('💵 Payroll List:', 'success');
    } catch (error) {
        logOutput(`❌ Failed to list payroll: ${error.message}`, 'error');
    }
}

function showCreatePayrollForm() {
    const form = createDynamicForm('Create Payroll', [
        { name: 'employee_id', label: 'Employee ID', type: 'number', required: true },
        { name: 'period_start', label: 'Period Start', type: 'date', required: true },
        { name: 'period_end', label: 'Period End', type: 'date', required: true },
        { name: 'gross_salary', label: 'Gross Salary', type: 'number', required: true },
        { name: 'deductions', label: 'Deductions', type: 'number' },
        { name: 'overtime_hours', label: 'Overtime Hours', type: 'number' }
    ], async (formData) => {
        await apiRequest('/api/hr/payroll', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
    });
    showDynamicForm(form);
}

/**
 * Supply Chain Module Functions
 */

async function listInventory() {
    try {
        const inventory = await apiRequest('/api/supply-chain/inventory');
        logOutput('📦 Inventory List:', 'success');
    } catch (error) {
        logOutput(`❌ Failed to list inventory: ${error.message}`, 'error');
    }
}

function showCreateInventoryForm() {
    const form = createDynamicForm('Create Inventory Item', [
        { name: 'name', label: 'Item Name', type: 'text', required: true },
        { name: 'sku', label: 'SKU', type: 'text', required: true },
        { name: 'quantity', label: 'Quantity', type: 'number', required: true },
        { name: 'unit_price', label: 'Unit Price', type: 'number', required: true },
        { name: 'supplier', label: 'Supplier', type: 'text' },
        { name: 'location', label: 'Storage Location', type: 'text' }
    ], async (formData) => {
        await apiRequest('/api/supply-chain/inventory', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
    });
    showDynamicForm(form);
}

async function listPurchaseOrders() {
    try {
        const orders = await apiRequest('/api/supply-chain/purchase-orders');
        logOutput('📋 Purchase Orders List:', 'success');
    } catch (error) {
        logOutput(`❌ Failed to list purchase orders: ${error.message}`, 'error');
    }
}

function showCreatePurchaseOrderForm() {
    const form = createDynamicForm('Create Purchase Order', [
        { name: 'vendor_id', label: 'Vendor ID', type: 'number', required: true },
        { name: 'items', label: 'Items (JSON)', type: 'textarea', required: true },
        { name: 'total_amount', label: 'Total Amount', type: 'number', required: true },
        { name: 'delivery_date', label: 'Expected Delivery', type: 'date' },
        { name: 'notes', label: 'Notes', type: 'textarea' }
    ], async (formData) => {
        await apiRequest('/api/supply-chain/purchase-orders', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
    });
    showDynamicForm(form);
}

async function listCourierShipments() {
    try {
        const shipments = await apiRequest('/api/supply-chain/courier-shipments');
        logOutput('🚚 Courier Shipments List:', 'success');
    } catch (error) {
        logOutput(`❌ Failed to list courier shipments: ${error.message}`, 'error');
    }
}

function showCreateCourierShipmentForm() {
    const form = createDynamicForm('Create Courier Shipment', [
        { name: 'tracking_number', label: 'Tracking Number', type: 'text', required: true },
        { name: 'courier_name', label: 'Courier Name', type: 'text', required: true },
        { name: 'origin', label: 'Origin', type: 'text', required: true },
        { name: 'destination', label: 'Destination', type: 'text', required: true },
        { name: 'weight', label: 'Weight (kg)', type: 'number' },
        { name: 'estimated_delivery', label: 'Estimated Delivery', type: 'date' }
    ], async (formData) => {
        await apiRequest('/api/supply-chain/courier-shipments', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
    });
    showDynamicForm(form);
}

/**
 * Desk Module Functions
 */

async function listTickets() {
    try {
        const tickets = await apiRequest('/api/desk/tickets');
        logOutput('🎫 Tickets List:', 'success');
    } catch (error) {
        logOutput(`❌ Failed to list tickets: ${error.message}`, 'error');
    }
}

function showCreateTicketForm() {
    const form = createDynamicForm('Create Ticket', [
        { name: 'title', label: 'Ticket Title', type: 'text', required: true },
        { name: 'description', label: 'Description', type: 'textarea', required: true },
        { name: 'priority', label: 'Priority', type: 'text', required: true },
        { name: 'category', label: 'Category', type: 'text' },
        { name: 'assigned_to', label: 'Assigned To', type: 'text' }
    ], async (formData) => {
        await apiRequest('/api/desk/tickets', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
    });
    showDynamicForm(form);
}

async function listWorkOrders() {
    try {
        const workOrders = await apiRequest('/api/desk/work-orders');
        logOutput('🔧 Work Orders List:', 'success');
    } catch (error) {
        logOutput(`❌ Failed to list work orders: ${error.message}`, 'error');
    }
}

function showCreateWorkOrderForm() {
    const form = createDynamicForm('Create Work Order', [
        { name: 'title', label: 'Work Order Title', type: 'text', required: true },
        { name: 'description', label: 'Description', type: 'textarea', required: true },
        { name: 'assigned_to', label: 'Assigned To', type: 'text', required: true },
        { name: 'priority', label: 'Priority', type: 'text' },
        { name: 'due_date', label: 'Due Date', type: 'date' }
    ], async (formData) => {
        await apiRequest('/api/desk/work-orders', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
    });
    showDynamicForm(form);
}

function showWorkOrderCheckinForm() {
    const form = createDynamicForm('Work Order Check-in', [
        { name: 'work_order_id', label: 'Work Order ID', type: 'number', required: true },
        { name: 'status_update', label: 'Status Update', type: 'textarea', required: true },
        { name: 'hours_worked', label: 'Hours Worked', type: 'number' },
        { name: 'notes', label: 'Notes', type: 'textarea' }
    ], async (formData) => {
        const woId = formData.work_order_id;
        delete formData.work_order_id;
        await apiRequest(`/api/desk/work-orders/${woId}/checkin`, {
            method: 'POST',
            body: JSON.stringify(formData)
        });
    });
    showDynamicForm(form);
}

/**
 * Vendors Module Functions
 */

async function listVendors() {
    try {
        const vendors = await apiRequest('/api/vendors');
        logOutput('🏢 Vendors List:', 'success');
    } catch (error) {
        logOutput(`❌ Failed to list vendors: ${error.message}`, 'error');
    }
}

function showCreateVendorForm() {
    const form = createDynamicForm('Create Vendor', [
        { name: 'name', label: 'Vendor Name', type: 'text', required: true },
        { name: 'email', label: 'Email', type: 'email', required: true },
        { name: 'phone', label: 'Phone', type: 'text' },
        { name: 'address', label: 'Address', type: 'textarea' },
        { name: 'category', label: 'Category', type: 'text' },
        { name: 'payment_terms', label: 'Payment Terms', type: 'text' }
    ], async (formData) => {
        await apiRequest('/api/vendors', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
    });
    showDynamicForm(form);
}

function showGetVendorPerformanceForm() {
    const form = createDynamicForm('Get Vendor Performance', [
        { name: 'vendor_id', label: 'Vendor ID', type: 'number', required: true }
    ], async (formData) => {
        const vendorId = formData.vendor_id;
        await apiRequest(`/api/vendors/${vendorId}/performance`);
    });
    showDynamicForm(form);
}

function showUpdateVendorPerformanceForm() {
    const form = createDynamicForm('Update Vendor Performance', [
        { name: 'vendor_id', label: 'Vendor ID', type: 'number', required: true },
        { name: 'rating', label: 'Rating (1-5)', type: 'number', required: true },
        { name: 'on_time_delivery', label: 'On-time Delivery %', type: 'number' },
        { name: 'quality_score', label: 'Quality Score', type: 'number' },
        { name: 'notes', label: 'Notes', type: 'textarea' }
    ], async (formData) => {
        const vendorId = formData.vendor_id;
        delete formData.vendor_id;
        await apiRequest(`/api/vendors/${vendorId}/performance`, {
            method: 'PUT',
            body: JSON.stringify(formData)
        });
    });
    showDynamicForm(form);
}

/**
 * Marketing Module Functions
 */

async function listCampaigns() {
    try {
        const campaigns = await apiRequest('/api/marketing/campaigns');
        logOutput('📢 Marketing Campaigns List:', 'success');
    } catch (error) {
        logOutput(`❌ Failed to list campaigns: ${error.message}`, 'error');
    }
}

function showCreateCampaignForm() {
    const form = createDynamicForm('Create Marketing Campaign', [
        { name: 'name', label: 'Campaign Name', type: 'text', required: true },
        { name: 'description', label: 'Description', type: 'textarea', required: true },
        { name: 'start_date', label: 'Start Date', type: 'date', required: true },
        { name: 'end_date', label: 'End Date', type: 'date' },
        { name: 'budget', label: 'Budget', type: 'number' },
        { name: 'target_audience', label: 'Target Audience', type: 'textarea' }
    ], async (formData) => {
        await apiRequest('/api/marketing/campaigns', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
    });
    showDynamicForm(form);
}

/**
 * Surveys Module Functions
 */

async function listSurveys() {
    try {
        const surveys = await apiRequest('/api/surveys');
        logOutput('📊 Surveys List:', 'success');
    } catch (error) {
        logOutput(`❌ Failed to list surveys: ${error.message}`, 'error');
    }
}

function showCreateSurveyForm() {
    const form = createDynamicForm('Create Survey', [
        { name: 'title', label: 'Survey Title', type: 'text', required: true },
        { name: 'description', label: 'Description', type: 'textarea', required: true },
        { name: 'questions', label: 'Questions (JSON)', type: 'textarea', required: true },
        { name: 'target_audience', label: 'Target Audience', type: 'text' },
        { name: 'expires_at', label: 'Expires At', type: 'date' }
    ], async (formData) => {
        await apiRequest('/api/surveys', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
    });
    showDynamicForm(form);
}

/**
 * Community Module Functions
 */

async function listPosts() {
    try {
        const posts = await apiRequest('/api/community/posts');
        logOutput('💬 Community Posts List:', 'success');
    } catch (error) {
        logOutput(`❌ Failed to list posts: ${error.message}`, 'error');
    }
}

function showCreatePostForm() {
    const form = createDynamicForm('Create Community Post', [
        { name: 'title', label: 'Post Title', type: 'text', required: true },
        { name: 'content', label: 'Content', type: 'textarea', required: true },
        { name: 'category', label: 'Category', type: 'text' },
        { name: 'tags', label: 'Tags (comma-separated)', type: 'text' }
    ], async (formData) => {
        await apiRequest('/api/community/posts', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
    });
    showDynamicForm(form);
}

/**
 * Dynamic Form Helper Functions
 */

function createDynamicForm(title, fields, submitHandler) {
    return {
        title,
        fields,
        submitHandler
    };
}

function showDynamicForm(formConfig) {
    const container = document.getElementById('dynamic-forms');
    
    // Clear previous forms
    container.innerHTML = '';
    
    const formElement = document.createElement('div');
    formElement.className = 'dynamic-form';
    
    let formHTML = `<h3>${formConfig.title}</h3><form id="dynamic-form">`;
    
    formConfig.fields.forEach(field => {
        if (field.type === 'textarea') {
            formHTML += `
                <div class="form-group">
                    <label for="${field.name}">${field.label}${field.required ? ' *' : ''}:</label>
                    <textarea id="${field.name}" name="${field.name}" ${field.required ? 'required' : ''}></textarea>
                </div>
            `;
        } else {
            formHTML += `
                <div class="form-group">
                    <label for="${field.name}">${field.label}${field.required ? ' *' : ''}:</label>
                    <input type="${field.type}" id="${field.name}" name="${field.name}" ${field.required ? 'required' : ''}>
                </div>
            `;
        }
    });
    
    formHTML += `
        <div class="form-actions">
            <button type="submit" class="btn btn-primary">Submit</button>
            <button type="button" class="btn btn-secondary" onclick="hideDynamicForm()">Cancel</button>
        </div>
    </form>`;
    
    formElement.innerHTML = formHTML;
    container.appendChild(formElement);
    
    // Add submit handler
    document.getElementById('dynamic-form').addEventListener('submit', async (event) => {
        event.preventDefault();
        
        const formData = {};
        formConfig.fields.forEach(field => {
            const value = document.getElementById(field.name).value;
            if (value) {
                // Try to parse as JSON for textarea fields that might contain JSON
                if (field.name.includes('questions') || field.name.includes('items')) {
                    try {
                        formData[field.name] = JSON.parse(value);
                    } catch {
                        formData[field.name] = value;
                    }
                } else if (field.type === 'number') {
                    formData[field.name] = parseFloat(value);
                } else {
                    formData[field.name] = value;
                }
            }
        });
        
        try {
            await formConfig.submitHandler(formData);
            hideDynamicForm();
            logOutput(`✅ ${formConfig.title} completed successfully!`, 'success');
        } catch (error) {
            logOutput(`❌ ${formConfig.title} failed: ${error.message}`, 'error');
        }
    });
    
    // Scroll to form
    formElement.scrollIntoView({ behavior: 'smooth' });
}

function hideDynamicForm() {
    document.getElementById('dynamic-forms').innerHTML = '';
}

/**
 * Output Management Functions
 */

function logOutput(message, type = 'info') {
    const outputArea = document.getElementById('output-area');
    const timestamp = new Date().toLocaleTimeString();
    
    let prefix = '';
    let className = '';
    
    switch (type) {
        case 'error':
            prefix = '❌ ERROR';
            className = 'error-message';
            break;
        case 'success':
            prefix = '✅ SUCCESS';
            className = 'success-message';
            break;
        default:
            prefix = 'ℹ️ INFO';
            className = '';
    }
    
    const logEntry = document.createElement('div');
    logEntry.className = className;
    logEntry.textContent = `[${timestamp}] ${prefix}: ${message}`;
    
    outputArea.appendChild(logEntry);
    outputArea.scrollTop = outputArea.scrollHeight;
}

function clearOutput() {
    document.getElementById('output-area').innerHTML = '<p>API responses and errors will appear here...</p>';
}