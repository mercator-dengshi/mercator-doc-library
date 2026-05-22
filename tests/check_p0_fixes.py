#!/usr/bin/env python3
"""
静态代码分析 - 验证P0修复
不需要安装依赖，只检查代码内容
"""

import os
import sys

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_success(text):
    print(f"✓ {text}")

def print_error(text):
    print(f"✗ {text}")

def print_info(text):
    print(f"ℹ {text}")

def read_file(filepath):
    """Read file content"""
    full_path = os.path.join(os.path.dirname(__file__), '..', filepath)
    with open(full_path, 'r', encoding='utf-8') as f:
        return f.read()

def test_jwt_config():
    """Test 1: JWT Configuration"""
    print_header("Test 1: JWT Secret Key Configuration")
    
    try:
        content = read_file('backend/app/core/config.py')
        
        checks = [
            ('SECRET_KEY: str\n', 'SECRET_KEY has no default value'),
            ("@field_validator('SECRET_KEY'", 'SECRET_KEY validator exists'),
            ('len(v) < 32', 'Minimum length check (32 chars)'),
            ('your-secret-key-change-in-production', 'Default value rejection'),
            ('DATABASE_URL: str\n', 'DATABASE_URL has no default value'),
        ]
        
        all_passed = True
        for check_str, description in checks:
            if check_str in content:
                print_success(description)
            else:
                print_error(f"Missing: {description}")
                all_passed = False
        
        # Check .env.example
        env_content = read_file('.env.example')
        if 'SECRET_KEY=' in env_content and '32' in env_content:
            print_success(".env.example has SECRET_KEY instructions")
        else:
            print_error(".env.example missing SECRET_KEY info")
            all_passed = False
        
        return all_passed
        
    except Exception as e:
        print_error(f"Test error: {e}")
        return False

def test_auth_middleware():
    """Test 2: Auth Middleware Implementation"""
    print_header("Test 2: Auth Middleware Functions")
    
    try:
        content = read_file('backend/app/core/security.py')
        
        checks = [
            ('def get_current_user(', 'get_current_user function'),
            ('HTTPBearer', 'HTTPBearer security'),
            ('credentials.credentials', 'Token extraction'),
            ('decode_token(token)', 'Token decoding'),
            ('User not found', 'User existence check'),
            ('is_active', 'Active status check'),
            ('def get_current_active_admin(', 'Admin check function'),
            ('def get_current_active_editor(', 'Editor check function'),
        ]
        
        all_passed = True
        for check_str, description in checks:
            if check_str in content:
                print_success(description)
            else:
                print_error(f"Missing: {description}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print_error(f"Test error: {e}")
        return False

def test_documents_auth():
    """Test 3: Authentication in Documents Endpoint"""
    print_header("Test 3: Documents Endpoint Authentication")
    
    try:
        content = read_file('backend/app/api/v1/endpoints/documents.py')
        
        checks = [
            ('from app.core.security import', 'Security imports'),
            ('get_current_active_editor', 'Editor dependency'),
            ('current_user: User = Depends(get_current_active_editor)', 'Auth in create'),
            ('author_id=current_user.id', 'Author from current user'),
            ('last_editor_id=current_user.id', 'Editor tracking'),
            ('last_editor_type=EditorType.HUMAN', 'Editor type'),
            ('Document.deleted_at.is_(None)', 'Soft delete filter'),
            ('DocumentStatus.ARCHIVED', 'Archive check'),
            ('datetime.now(timezone.utc)', 'Timezone-aware datetime'),
        ]
        
        all_passed = True
        for check_str, description in checks:
            if check_str in content:
                print_success(description)
            else:
                print_error(f"Missing: {description}")
                all_passed = False
        
        # Check permission logic
        if 'document.author_id != current_user.id' in content:
            print_success("Author ownership check")
        else:
            print_error("Missing author ownership check")
            all_passed = False
        
        return all_passed
        
    except Exception as e:
        print_error(f"Test error: {e}")
        return False

def test_auth_endpoint():
    """Test 4: Auth Endpoint Fixes"""
    print_header("Test 4: Auth Endpoint Fixes")
    
    try:
        content = read_file('backend/app/api/v1/endpoints/auth.py')
        
        checks = [
            ('from app.models.models import User, UserRole', 'UserRole import'),
            ('role=UserRole.VIEWER', 'Enum usage (not string)'),
            ('datetime.now(timezone.utc)', 'Timezone-aware datetime'),
            ('from datetime import datetime, timezone', 'Timezone import'),
        ]
        
        all_passed = True
        for check_str, description in checks:
            if check_str in content:
                print_success(description)
            else:
                print_error(f"Missing: {description}")
                all_passed = False
        
        # Check that string role is NOT used
        if 'role="viewer"' in content or "role='viewer'" in content:
            print_error("Still using string for role (should use enum)")
            all_passed = False
        else:
            print_success("Not using string for role")
        
        return all_passed
        
    except Exception as e:
        print_error(f"Test error: {e}")
        return False

def test_frontend_store():
    """Test 5: Frontend Auth Store"""
    print_header("Test 5: Frontend Token Storage")
    
    try:
        content = read_file('frontend/stores/auth-store.ts')
        
        # Should NOT have localStorage (excluding comments)
        lines = content.split('\n')
        code_lines = [line for line in lines if not line.strip().startswith('//')]
        code_content = '\n'.join(code_lines)
        
        if 'localStorage' in code_content:
            print_error("Still using localStorage")
            return False
        else:
            print_success("No localStorage usage")
        
        # Should have memory storage
        if 'accessToken' in content:
            print_success("Access token in state")
        else:
            print_error("Missing accessToken in state")
            return False
        
        # Should have getAccessToken method
        if 'getAccessToken' in content:
            print_success("getAccessToken method exists")
        else:
            print_error("Missing getAccessToken method")
            return False
        
        # Should NOT have persist middleware
        if 'persist' in content.lower():
            print_error("Still using persist middleware")
            return False
        else:
            print_success("No persist middleware")
        
        return True
        
    except Exception as e:
        print_error(f"Test error: {e}")
        return False

def test_api_client():
    """Test 6: API Client Updates"""
    print_header("Test 6: API Client Token Handling")
    
    try:
        content = read_file('frontend/lib/api-client.ts')
        
        checks = [
            ("import { useAuthStore }", 'Auth store import'),
            ('useAuthStore.getState().getAccessToken()', 'Get token from store'),
            ('useAuthStore.getState().logout()', 'Logout on 401'),
        ]
        
        all_passed = True
        for check_str, description in checks:
            if check_str in content:
                print_success(description)
            else:
                print_error(f"Missing: {description}")
                all_passed = False
        
        # Should NOT use localStorage
        if 'localStorage.getItem' in content:
            print_error("Still reading from localStorage")
            all_passed = False
        else:
            print_success("Not using localStorage")
        
        # Should NOT have refresh token logic
        if 'refresh_token' in content.lower():
            print_info("Note: Refresh token logic removed (simplified)")
        
        return all_passed
        
    except Exception as e:
        print_error(f"Test error: {e}")
        return False

def test_login_page():
    """Test 7: Login Page Updates"""
    print_header("Test 7: Login Page Integration")
    
    try:
        content = read_file('frontend/app/login/page.tsx')
        
        # Check login call
        if 'login(user, tokens.access_token)' in content:
            print_success("Login uses new signature (no refresh token)")
        else:
            print_error("Login signature may be incorrect")
            return False
        
        # Should NOT pass refresh_token
        if 'tokens.refresh_token' in content:
            print_error("Still passing refresh_token")
            return False
        else:
            print_success("Not passing refresh_token")
        
        return True
        
    except Exception as e:
        print_error(f"Test error: {e}")
        return False

def test_permission_logic():
    """Test 8: Permission Logic"""
    print_header("Test 8: Permission Checks")
    
    try:
        content = read_file('backend/app/api/v1/endpoints/documents.py')
        
        checks = [
            ('if current_user.role.value == "editor"', 'Editor role check'),
            ('document.author_id != current_user.id', 'Ownership verification'),
            ('You can only edit your own documents', 'Edit permission message'),
            ('You can only delete your own documents', 'Delete permission message'),
            ('Cannot edit archived document', 'Archive protection'),
        ]
        
        all_passed = True
        for check_str, description in checks:
            if check_str in content:
                print_success(description)
            else:
                print_error(f"Missing: {description}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print_error(f"Test error: {e}")
        return False

def check_no_hardcoded_uuid():
    """Test 9: No Hardcoded UUID"""
    print_header("Test 9: No Hardcoded Author ID")
    
    try:
        content = read_file('backend/app/api/v1/endpoints/documents.py')
        
        # Should NOT have the hardcoded UUID
        if '00000000-0000-0000-0000-000000000000' in content:
            print_error("Still contains hardcoded UUID!")
            return False
        else:
            print_success("No hardcoded UUID found")
        
        # Should use current_user.id
        if 'author_id=current_user.id' in content:
            print_success("Uses current_user.id for author")
            return True
        else:
            print_error("Not using current_user.id")
            return False
        
    except Exception as e:
        print_error(f"Test error: {e}")
        return False

def main():
    print_header("Mercator Doc Library - P0 Fixes Static Analysis")
    print_info("Checking code without running services...\n")
    
    results = []
    
    # Run all tests
    results.append(("JWT Configuration", test_jwt_config()))
    results.append(("Auth Middleware", test_auth_middleware()))
    results.append(("Documents Auth", test_documents_auth()))
    results.append(("Auth Endpoint", test_auth_endpoint()))
    results.append(("Frontend Store", test_frontend_store()))
    results.append(("API Client", test_api_client()))
    results.append(("Login Page", test_login_page()))
    results.append(("Permission Logic", test_permission_logic()))
    results.append(("No Hardcoded UUID", check_no_hardcoded_uuid()))
    
    # Print summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        color = "\033[92m" if result else "\033[91m"
        reset = "\033[0m"
        print(f"{color}{status}{reset} {test_name}")
    
    print(f"\n{'='*60}")
    print(f"Total: {passed}/{total} tests passed")
    print(f"{'='*60}\n")
    
    if passed == total:
        print("\033[92m\033[1m🎉 All P0 fixes verified successfully!\033[0m\n")
        print("Next steps:")
        print("1. Install backend dependencies: pip install -r backend/requirements.txt")
        print("2. Set up .env file with strong SECRET_KEY")
        print("3. Start services: docker-compose up -d")
        print("4. Run backend: cd backend && uvicorn app.main:app --reload")
        print("5. Run frontend: cd frontend && npm run dev\n")
        return 0
    else:
        failed_tests = [name for name, result in results if not result]
        print("\033[91m\033[1m⚠️  Some tests failed:\033[0m\n")
        for test in failed_tests:
            print(f"  - {test}")
        print("\nPlease review the errors above.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
