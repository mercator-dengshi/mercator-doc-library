#!/usr/bin/env python3
"""
API端点与前端页面对应关系检查
确保每个重要的API端点都有对应的前端页面或功能
"""

import os
import sys
import re
from pathlib import Path
from colorama import Fore, Style, init

init(autoreset=True)

def print_header(text):
    print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  {text}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")

def print_success(text):
    print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")

def print_error(text):
    print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")

def print_warning(text):
    print(f"{Fore.YELLOW}⚠ {text}{Style.RESET_ALL}")

def print_info(text):
    print(f"{Fore.BLUE}ℹ {text}{Style.RESET_ALL}")

def extract_api_endpoints(backend_dir):
    """Extract API endpoints from backend routes"""
    endpoints = []
    
    # Search for router definitions in endpoints files
    endpoints_dir = Path(backend_dir) / "app" / "api" / "v1" / "endpoints"
    
    if not endpoints_dir.exists():
        return endpoints
    
    for endpoint_file in endpoints_dir.glob("*.py"):
        with open(endpoint_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Find @router.get/post/put/delete decorators
            patterns = [
                r'@router\.get\(["\']([^"\']+)["\']',
                r'@router\.post\(["\']([^"\']+)["\']',
                r'@router\.put\(["\']([^"\']+)["\']',
                r'@router\.delete\(["\']([^"\']+)["\']',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    method = pattern.split('.')[1].split('(')[0].upper()
                    endpoints.append({
                        'method': method,
                        'path': f"/api/v1{match}",
                        'file': endpoint_file.name
                    })
    
    return sorted(endpoints, key=lambda x: x['path'])

def check_frontend_coverage(endpoints, frontend_dir):
    """Check if endpoints have corresponding frontend pages"""
    
    # Map of critical endpoints to expected frontend features
    critical_mappings = {
        '/api/v1/auth/register': {'page': '/register', 'feature': 'User registration page'},
        '/api/v1/auth/login': {'page': '/login', 'feature': 'User login page'},
        '/api/v1/docs/': {'page': '/docs', 'feature': 'Document list page'},
    }
    
    results = []
    
    for endpoint in endpoints:
        path = endpoint['path']
        
        # Check if this is a critical endpoint
        if path in critical_mappings:
            mapping = critical_mappings[path]
            page_path = Path(frontend_dir) / "app" / mapping['page'].lstrip('/') / "page.tsx"
            
            exists = page_path.exists()
            results.append({
                'endpoint': f"{endpoint['method']} {path}",
                'expected_page': mapping['page'],
                'exists': exists,
                'feature': mapping['feature']
            })
    
    return results

def main():
    print_header("API-Frontend Coverage Check")
    
    # Find project directories
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    backend_dir = project_root / "backend"
    frontend_dir = project_root / "frontend"
    
    if not backend_dir.exists():
        print_error(f"Backend directory not found: {backend_dir}")
        sys.exit(1)
    
    if not frontend_dir.exists():
        print_error(f"Frontend directory not found: {frontend_dir}")
        sys.exit(1)
    
    # Extract API endpoints
    print_info("Extracting API endpoints from backend...")
    endpoints = extract_api_endpoints(backend_dir)
    print_info(f"Found {len(endpoints)} API endpoints\n")
    
    # Check frontend coverage
    print_info("Checking frontend coverage for critical endpoints...\n")
    results = check_frontend_coverage(endpoints, frontend_dir)
    
    passed = 0
    failed = 0
    
    for result in results:
        status = "✓" if result['exists'] else "✗"
        color = Fore.GREEN if result['exists'] else Fore.RED
        
        print(f"{color}{status} {result['endpoint']:30s} → {result['expected_page']:20s} ({result['feature']}){Style.RESET_ALL}")
        
        if result['exists']:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "="*70)
    print_info(f"Results: {passed} passed, {failed} failed\n")
    
    if failed > 0:
        print(f"{Fore.RED}❌ API-Frontend coverage check FAILED{Style.RESET_ALL}")
        sys.exit(1)
    else:
        print(f"{Fore.GREEN}✅ API-Frontend coverage check PASSED{Style.RESET_ALL}")
        sys.exit(0)

if __name__ == "__main__":
    main()
