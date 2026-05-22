#!/usr/bin/env python3
"""
前端路由完整性检查工具
扫描frontend/app目录，检查所有路由页面是否存在
"""

import os
import sys
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

def scan_routes(frontend_dir):
    """Scan frontend app directory for routes"""
    app_dir = Path(frontend_dir) / "app"
    
    if not app_dir.exists():
        print_error(f"App directory not found: {app_dir}")
        return []
    
    routes = []
    
    # Scan for page.tsx files
    for page_file in app_dir.rglob("page.tsx"):
        relative_path = page_file.relative_to(app_dir)
        route_path = str(relative_path.parent).replace(os.sep, "/")
        
        if route_path == ".":
            route_path = "/"
        else:
            route_path = f"/{route_path}"
        
        routes.append({
            'path': route_path,
            'file': str(page_file),
            'exists': True
        })
    
    return sorted(routes, key=lambda x: x['path'])

def check_expected_routes(routes):
    """Check if all expected routes exist"""
    expected_routes = [
        "/",
        "/login",
        "/register",
        "/docs",
        "/docs/[slug]",  # Dynamic route for document detail
    ]
    
    existing_paths = [r['path'] for r in routes]
    missing = []
    
    for expected in expected_routes:
        # Check exact match or dynamic route pattern
        found = False
        for existing in existing_paths:
            if existing == expected:
                found = True
                break
            # Check dynamic route pattern (e.g., /docs/[slug] matches /docs/test-doc)
            if '[' in expected and expected.split('[')[0] == existing.split('/')[0]:
                # Check if there's a dynamic route under this path
                expected_base = expected.rstrip('/').split('/')
                existing_base = existing.rstrip('/').split('/')
                if len(expected_base) == len(existing_base) and expected_base[:-1] == existing_base[:-1]:
                    if '[' in existing_base[-1]:
                        found = True
                        break
        
        if not found:
            missing.append(expected)
    
    return missing

def main():
    print_header("Frontend Route Completeness Check")
    
    # Find frontend directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    frontend_dir = project_root / "frontend"
    
    if not frontend_dir.exists():
        print_error(f"Frontend directory not found: {frontend_dir}")
        sys.exit(1)
    
    # Scan routes
    print_info("Scanning frontend routes...")
    routes = scan_routes(frontend_dir)
    
    print_info(f"Found {len(routes)} routes:\n")
    for route in routes:
        print_success(f"{route['path']:30s} → {os.path.basename(route['file'])}")
    
    # Check expected routes
    print("\n" + "="*70)
    print_info("Checking expected routes...\n")
    
    missing = check_expected_routes(routes)
    
    if missing:
        print_error(f"Missing {len(missing)} required routes:\n")
        for route in missing:
            print_error(f"  - {route}")
        print(f"\n{Fore.RED}❌ Route completeness check FAILED{Style.RESET_ALL}")
        sys.exit(1)
    else:
        print_success("All expected routes exist!")
        print(f"\n{Fore.GREEN}✅ Route completeness check PASSED{Style.RESET_ALL}")
        sys.exit(0)

if __name__ == "__main__":
    main()
