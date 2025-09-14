#!/usr/bin/env python3
"""
ERP V2.0 Smoke Tests
Basic smoke tests to validate CRUD operations across all modules
"""

import requests
import json
import time
import sys
from datetime import datetime, timedelta

class ERPSmokeTest:
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.token = None
        self.headers = {}
        self.test_data = {}
        
    def log(self, message):
        """Log test messages with timestamp"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    def make_request(self, method, endpoint, data=None, expect_status=None):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            elif method == 'PUT':
                response = requests.put(url, headers=self.headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if expect_status and response.status_code != expect_status:
                self.log(f"❌ {method} {endpoint} - Expected {expect_status}, got {response.status_code}")
                self.log(f"   Response: {response.text[:200]}")
                return None
            
            return response
            
        except requests.exceptions.RequestException as e:
            self.log(f"❌ {method} {endpoint} - Request failed: {str(e)}")
            return None
    
    def setup_auth(self):
        """Setup authentication and create admin user if needed"""
        self.log("🔐 Setting up authentication...")
        
        # First try to login with default admin credentials
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = self.make_request('POST', '/api/auth/login', login_data)
        
        if response and response.status_code == 200:
            data = response.json()
            self.token = data['access_token']
            self.headers = {'Authorization': f'Bearer {self.token}'}
            self.log("✅ Authentication successful with existing admin user")
            return True
        
        # If login fails, try to register new admin user
        self.log("📝 Creating new admin user...")
        register_data = {
            "username": "admin",
            "email": "admin@test.com",
            "password": "admin123",
            "first_name": "System",
            "last_name": "Administrator",
            "company_name": "Test Company",
            "company_code": "TEST",
            "role": "admin"
        }
        
        response = self.make_request('POST', '/api/auth/register', register_data)
        
        if response and response.status_code == 201:
            self.log("✅ Admin user created successfully")
            # Now login
            return self.setup_auth()
        
        self.log("❌ Failed to setup authentication")
        return False
    
    def test_health_check(self):
        """Test basic health endpoint"""
        self.log("🏥 Testing health check...")
        response = self.make_request('GET', '/api/health', expect_status=200)
        if response:
            data = response.json()
            if data.get('status') == 'ok':
                self.log("✅ Health check passed")
                return True
        self.log("❌ Health check failed")
        return False
    
    def test_profile(self):
        """Test profile endpoint"""
        self.log("👤 Testing profile endpoint...")
        response = self.make_request('GET', '/api/profile', expect_status=200)
        if response:
            data = response.json()
            if data.get('username') == 'admin':
                self.log("✅ Profile endpoint working")
                return True
        self.log("❌ Profile endpoint failed")
        return False
    
    def test_api_metadata(self):
        """Test API metadata endpoint"""
        self.log("📊 Testing API metadata...")
        response = self.make_request('GET', '/api/meta', expect_status=200)
        if response:
            data = response.json()
            if data.get('version') == '2.0' and 'modules' in data:
                self.log(f"✅ API metadata working - {len(data['modules'])} modules available")
                return True
        self.log("❌ API metadata failed")
        return False
    
    def test_crud_operations(self):
        """Test CRUD operations for key entities"""
        tests_passed = 0
        total_tests = 0
        
        # Test Customer CRUD
        total_tests += 1
        if self.test_customer_crud():
            tests_passed += 1
        
        # Test Product CRUD
        total_tests += 1
        if self.test_product_crud():
            tests_passed += 1
        
        # Test User CRUD
        total_tests += 1
        if self.test_user_crud():
            tests_passed += 1
        
        # Test Vendor CRUD
        total_tests += 1
        if self.test_vendor_crud():
            tests_passed += 1
        
        self.log(f"📈 CRUD tests completed: {tests_passed}/{total_tests} passed")
        return tests_passed == total_tests
    
    def test_customer_crud(self):
        """Test Customer CRUD operations"""
        self.log("👥 Testing Customer CRUD...")
        
        # Create customer
        customer_data = {
            "name": "Test Customer Inc",
            "code": "TEST001",
            "email": "test@customer.com",
            "phone": "+1234567890",
            "address": "123 Test Street, Test City",
            "contact_person": "John Doe",
            "industry": "Technology",
            "customer_type": "prospect"
        }
        
        response = self.make_request('POST', '/api/crm/customers', customer_data, expect_status=201)
        if not response:
            return False
        
        customer_id = response.json().get('id')
        self.test_data['customer_id'] = customer_id
        self.log(f"✅ Customer created with ID: {customer_id}")
        
        # Read customer list
        response = self.make_request('GET', '/api/crm/customers', expect_status=200)
        if not response:
            return False
        
        customers = response.json()
        if len(customers) > 0:
            self.log(f"✅ Customer list retrieved - {len(customers)} customers")
        else:
            self.log("❌ No customers found in list")
            return False
        
        # Read customer detail
        response = self.make_request('GET', f'/api/crm/customers/{customer_id}', expect_status=200)
        if not response:
            return False
        
        customer = response.json()
        if customer.get('name') == customer_data['name']:
            self.log("✅ Customer detail retrieved")
        else:
            self.log("❌ Customer detail mismatch")
            return False
        
        # Update customer
        update_data = {
            "name": "Updated Test Customer Inc",
            "customer_type": "customer"
        }
        
        response = self.make_request('PUT', f'/api/crm/customers/{customer_id}', update_data, expect_status=200)
        if response:
            self.log("✅ Customer updated")
        else:
            return False
        
        return True
    
    def test_product_crud(self):
        """Test Product CRUD operations"""
        self.log("📦 Testing Product CRUD...")
        
        # Create product
        product_data = {
            "name": "Test Product",
            "code": "PROD001",
            "description": "A test product for CRUD testing",
            "category": "Electronics",
            "unit_of_measure": "pcs",
            "cost_price": 50.00,
            "selling_price": 75.00,
            "reorder_level": 10.0
        }
        
        response = self.make_request('POST', '/api/products', product_data, expect_status=201)
        if not response:
            return False
        
        product_id = response.json().get('id')
        self.test_data['product_id'] = product_id
        self.log(f"✅ Product created with ID: {product_id}")
        
        # Read product list
        response = self.make_request('GET', '/api/products', expect_status=200)
        if not response:
            return False
        
        products_data = response.json()
        if len(products_data.get('products', [])) > 0:
            self.log(f"✅ Product list retrieved - {len(products_data['products'])} products")
        else:
            self.log("❌ No products found in list")
            return False
        
        # Read product detail
        response = self.make_request('GET', f'/api/products/{product_id}', expect_status=200)
        if not response:
            return False
        
        product = response.json()
        if product.get('name') == product_data['name']:
            self.log("✅ Product detail retrieved")
        else:
            self.log("❌ Product detail mismatch")
            return False
        
        # Update product
        update_data = {
            "name": "Updated Test Product",
            "selling_price": 80.00
        }
        
        response = self.make_request('PUT', f'/api/products/{product_id}', update_data, expect_status=200)
        if response:
            self.log("✅ Product updated")
        else:
            return False
        
        return True
    
    def test_user_crud(self):
        """Test User CRUD operations"""
        self.log("👤 Testing User CRUD...")
        
        # Create user
        user_data = {
            "username": "testuser",
            "email": "testuser@test.com",
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User",
            "department": "IT",
            "position": "Developer",
            "role": "user"
        }
        
        response = self.make_request('POST', '/api/users', user_data, expect_status=201)
        if not response:
            return False
        
        user_id = response.json().get('id')
        self.test_data['user_id'] = user_id
        self.log(f"✅ User created with ID: {user_id}")
        
        # Read user list
        response = self.make_request('GET', '/api/users', expect_status=200)
        if not response:
            return False
        
        users_data = response.json()
        if len(users_data.get('users', [])) > 0:
            self.log(f"✅ User list retrieved - {len(users_data['users'])} users")
        else:
            self.log("❌ No users found in list")
            return False
        
        # Read user detail
        response = self.make_request('GET', f'/api/users/{user_id}', expect_status=200)
        if not response:
            return False
        
        user = response.json()
        if user.get('username') == user_data['username']:
            self.log("✅ User detail retrieved")
        else:
            self.log("❌ User detail mismatch")
            return False
        
        return True
    
    def test_vendor_crud(self):
        """Test Vendor CRUD operations"""
        self.log("🏢 Testing Vendor CRUD...")
        
        # Create vendor
        vendor_data = {
            "name": "Test Vendor Ltd",
            "code": "VEN001",
            "email": "vendor@test.com",
            "phone": "+1234567890",
            "address": "456 Vendor Street, Vendor City",
            "contact_person": "Jane Smith",
            "vendor_type": "supplier",
            "payment_terms": "Net 30"
        }
        
        response = self.make_request('POST', '/api/vendors', vendor_data, expect_status=201)
        if not response:
            return False
        
        vendor_id = response.json().get('id')
        self.test_data['vendor_id'] = vendor_id
        self.log(f"✅ Vendor created with ID: {vendor_id}")
        
        # Read vendor list
        response = self.make_request('GET', '/api/vendors', expect_status=200)
        if not response:
            return False
        
        vendors = response.json()
        if len(vendors) > 0:
            self.log(f"✅ Vendor list retrieved - {len(vendors)} vendors")
        else:
            self.log("❌ No vendors found in list")
            return False
        
        return True
    
    def test_pagination_and_search(self):
        """Test pagination and search functionality"""
        self.log("🔍 Testing pagination and search...")
        
        # Test pagination on customers
        response = self.make_request('GET', '/api/crm/customers?page=1&per_page=5', expect_status=200)
        if response:
            # The response should be a list for customers endpoint
            customers = response.json()
            self.log(f"✅ Pagination working - retrieved page 1")
        else:
            return False
        
        # Test search functionality on products
        response = self.make_request('GET', '/api/products?q=test', expect_status=200)
        if response:
            products_data = response.json()
            self.log(f"✅ Search working - found {len(products_data.get('products', []))} products")
        else:
            return False
        
        return True
    
    def run_all_tests(self):
        """Run complete smoke test suite"""
        self.log("🚀 Starting ERP V2.0 Smoke Tests")
        self.log("="*50)
        
        start_time = time.time()
        
        # Basic connectivity
        if not self.test_health_check():
            self.log("❌ Basic connectivity failed - aborting tests")
            return False
        
        # Authentication
        if not self.setup_auth():
            self.log("❌ Authentication failed - aborting tests")
            return False
        
        # Core endpoints
        tests = [
            ("Profile", self.test_profile),
            ("API Metadata", self.test_api_metadata),
            ("CRUD Operations", self.test_crud_operations),
            ("Pagination & Search", self.test_pagination_and_search)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            self.log(f"\n🧪 Running {test_name} tests...")
            if test_func():
                passed += 1
                self.log(f"✅ {test_name} tests passed")
            else:
                self.log(f"❌ {test_name} tests failed")
        
        end_time = time.time()
        duration = end_time - start_time
        
        self.log("\n" + "="*50)
        self.log(f"📊 Test Results: {passed}/{total} test suites passed")
        self.log(f"⏱️  Total duration: {duration:.2f} seconds")
        
        if passed == total:
            self.log("🎉 All smoke tests passed! ERP V2.0 is working correctly.")
            return True
        else:
            self.log("⚠️  Some tests failed. Please check the logs above.")
            return False

def main():
    """Main function to run smoke tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ERP V2.0 Smoke Tests')
    parser.add_argument('--url', default='http://localhost:5000', 
                       help='Base URL of the ERP system (default: http://localhost:5000)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Create and run tests
    tester = ERPSmokeTest(base_url=args.url)
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()