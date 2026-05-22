#!/usr/bin/env python3
"""
快速验证脚本 - 测试P0修复的核心逻辑
不需要运行完整服务，只测试代码逻辑
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

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

def test_jwt_secret_validation():
    """Test 1: JWT Secret Key Validation"""
    print_header("Test 1: JWT Secret Key Validation")
    
    try:
        from app.core.config import get_settings
        
        # Test with weak secret (should fail)
        os.environ['SECRET_KEY'] = 'weak'
        os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost/test'
        
        # Clear cache to force reload
        from functools import lru_cache
        get_settings.cache_clear()
        
        try:
            settings = get_settings()
            print_error("Weak secret was accepted (validation not working)")
            return False
        except ValueError as e:
            print_success(f"Weak secret correctly rejected: {e}")
            
        # Test with default secret (should fail)
        os.environ['SECRET_KEY'] = 'your-secret-key-change-in-production'
        get_settings.cache_clear()
        
        try:
            settings = get_settings()
            print_error("Default secret was accepted")
            return False
        except ValueError as e:
            print_success(f"Default secret correctly rejected: {e}")
            
        # Test with strong secret (should pass)
        os.environ['SECRET_KEY'] = 'this-is-a-very-strong-secret-key-for-testing-purposes-only!'
        get_settings.cache_clear()
        
        try:
            settings = get_settings()
            print_success("Strong secret accepted")
            print_info(f"SECRET_KEY length: {len(settings.SECRET_KEY)}")
            return True
        except Exception as e:
            print_error(f"Strong secret rejected: {e}")
            return False
            
    except Exception as e:
        print_error(f"Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_auth_middleware_exists():
    """Test 2: Auth Middleware Functions Exist"""
    print_header("Test 2: Auth Middleware Functions")
    
    try:
        from app.core.security import (
            get_current_user,
            get_current_active_admin,
            get_current_active_editor,
            security
        )
        
        print_success("get_current_user function exists")
        print_success("get_current_active_admin function exists")
        print_success("get_current_active_editor function exists")
        print_success("HTTPBearer security instance exists")
        
        # Check function signatures
        import inspect
        
        sig = inspect.signature(get_current_user)
        params = list(sig.parameters.keys())
        
        if 'credentials' in params and 'db' in params:
            print_success("get_current_user has correct parameters")
            return True
        else:
            print_error(f"get_current_user parameters incorrect: {params}")
            return False
            
    except ImportError as e:
        print_error(f"Import failed: {e}")
        return False
    except Exception as e:
        print_error(f"Test error: {e}")
        return False

def test_user_role_enum():
    """Test 3: User Role Enum Usage"""
    print_header("Test 3: User Role Enum")
    
    try:
        from app.models.models import User, UserRole
        
        # Check enum values
        roles = [role.value for role in UserRole]
        print_info(f"Available roles: {roles}")
        
        if 'admin' in roles and 'editor' in roles and 'viewer' in roles:
            print_success("All required roles exist")
        else:
            print_error("Missing required roles")
            return False
        
        # Check that UserRole.VIEWER is an enum, not string
        if isinstance(UserRole.VIEWER, UserRole):
            print_success("UserRole.VIEWER is proper enum type")
            return True
        else:
            print_error("UserRole.VIEWER is not enum type")
            return False
            
    except Exception as e:
        print_error(f"Test error: {e}")
        return False

def test_datetime_timezone():
    """Test 4: Timezone-aware Datetime"""
    print_header("Test 4: Timezone-aware Datetime")
    
    try:
        from datetime import datetime, timezone
        
        # Check imports in auth endpoint
        with open('backend/app/api/v1/endpoints/auth.py', 'r') as f:
            content = f.read()
            
        if 'timezone' in content and 'datetime.now(timezone.utc)' in content:
            print_success("auth.py uses timezone-aware datetime")
        else:
            print_error("auth.py still uses naive datetime")
            return False
        
        # Check imports in documents endpoint
        with open('backend/app/api/v1/endpoints/documents.py', 'r') as f:
            content = f.read()
            
        if 'timezone' in content and 'datetime.now(timezone.utc)' in content:
            print_success("documents.py uses timezone-aware datetime")
            return True
        else:
            print_error("documents.py still uses naive datetime")
            return False
            
    except Exception as e:
        print_error(f"Test error: {e}")
        return False

def test_auth_in_documents_endpoint():
    """Test 5: Authentication in Documents Endpoint"""
    print_header("Test 5: Authentication in Documents Endpoint")
    
    try:
        with open('backend/app/api/v1/endpoints/documents.py', 'r') as f:
            content = f.read()
        
        checks = [
            ('get_current_active_editor', 'Authentication dependency imported'),
            ('current_user: User = Depends(get_current_active_editor)', 'Auth dependency used'),
            ('author_id=current_user.id', 'Author ID from current user'),
            ('last_editor_id=current_user.id', 'Editor ID tracked'),
            ('Document.deleted_at.is_(None)', 'Soft delete check'),
            ('DocumentStatus.ARCHIVED', 'Archive status check'),
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

def test_frontend_token_storage():
    """Test 6: Frontend Token Storage"""
    print_header("Test 6: Frontend Token Storage")
    
    try:
        # Check auth store
        with open('frontend/stores/auth-store.ts', 'r') as f:
            store_content = f.read()
        
        if 'localStorage' in store_content:
            print_error("auth-store.ts still uses localStorage")
            return False
        else:
            print_success("auth-store.ts does not use localStorage")
        
        if 'accessToken' in store_content and 'memory' in store_content.lower():
            print_success("Token stored in memory")
        
        # Check API client
        with open('frontend/lib/api-client.ts', 'r') as f:
            client_content = f.read()
        
        if 'useAuthStore' in client_content:
            print_success("API client uses auth store")
        else:
            print_error("API client doesn't use auth store")
            return False
        
        if 'localStorage.getItem' in client_content:
            print_error("API client still reads from localStorage")
            return False
        else:
            print_success("API client doesn't use localStorage")
        
        return True
        
    except Exception as e:
        print_error(f"Test error: {e}")
        return False

def test_permission_checks():
    """Test 7: Permission Checks in Code"""
    print_header("Test 7: Permission Checks")
    
    try:
        with open('backend/app/api/v1/endpoints/documents.py', 'r') as f:
            content = f.read()
        
        checks = [
            ('current_user.role.value == "editor"', 'Editor role check'),
            ('document.author_id != current_user.id', 'Author ownership check'),
            ('Insufficient permissions', 'Permission error message'),
            ('You can only edit your own documents', 'Edit permission message'),
            ('You can only delete your own documents', 'Delete permission message'),
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

def main():
    print_header("Mercator Doc Library - P0 Fixes Verification")
    print_info("Testing code logic without running services...\n")
    
    results = []
    
    # Run all tests
    results.append(("JWT Secret Validation", test_jwt_secret_validation()))
    results.append(("Auth Middleware Exists", test_auth_middleware_exists()))
    results.append(("User Role Enum", test_user_role_enum()))
    results.append(("Timezone-aware Datetime", test_datetime_timezone()))
    results.append(("Auth in Documents", test_auth_in_documents_endpoint()))
    results.append(("Frontend Token Storage", test_frontend_token_storage()))
    results.append(("Permission Checks", test_permission_checks()))
    
    # Print summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        color = "\033[92m" if result else "\033[91m"  # Green or Red
        reset = "\033[0m"
        print(f"{color}{status}{reset} {test_name}")
    
    print(f"\n{'='*60}")
    print(f"Total: {passed}/{total} tests passed")
    print(f"{'='*60}\n")
    
    if passed == total:
        print("\033[92m\033[1m🎉 All P0 fixes verified successfully!\033[0m\n")
        return 0
    else:
        print("\033[91m\033[1m⚠️  Some tests failed. Please review the errors above.\033[0m\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
