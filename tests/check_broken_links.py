#!/usr/bin/env python3
"""
前端内部链接有效性检查
扫描所有前端页面，检查Link组件的href是否指向有效的路由
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

def get_existing_routes(frontend_dir):
    """Get all existing routes from frontend app directory"""
    app_dir = Path(frontend_dir) / "app"
    routes = set()
    
    if not app_dir.exists():
        return routes
    
    for page_file in app_dir.rglob("page.tsx"):
        relative_path = page_file.relative_to(app_dir)
        route_path = str(relative_path.parent).replace(os.sep, "/")
        
        if route_path == ".":
            routes.add("/")
        else:
            routes.add(f"/{route_path}")
    
    return routes

def extract_links_from_file(file_path):
    """Extract Link href values from a TypeScript file"""
    links = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Match href="/some-path" or href={`/some-path`}
        patterns = [
            r'href=["\'](/[^"\']+)["\']',
            r'router\.push\(["\'](/[^"\']+)["\']',
            r'window\.location\.href\s*=\s*["\'](/[^"\']+)["\']',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                # Skip external links and dynamic routes
                if not match.startswith('http') and '[' not in match:
                    links.append(match)
    
    return list(set(links))

def check_suspense_usage(frontend_dir):
    """Check if useSearchParams is wrapped in Suspense"""
    app_dir = Path(frontend_dir) / "app"
    components_dir = Path(frontend_dir) / "components"
    issues = []
    
    # Check all tsx files
    for tsx_file in list(app_dir.rglob("*.tsx")) + list(components_dir.rglob("*.tsx")):
        with open(tsx_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Check if file uses useSearchParams
            if 'useSearchParams' in content:
                # Check if it's wrapped in Suspense
                if 'Suspense' not in content:
                    issues.append({
                        'file': str(tsx_file.relative_to(frontend_dir)),
                        'issue': 'useSearchParams not wrapped in Suspense'
                    })
    
    return issues

def check_all_links(frontend_dir):
    """Check all internal links in frontend pages"""
    app_dir = Path(frontend_dir) / "app"
    existing_routes = get_existing_routes(frontend_dir)
    
    broken_links = []
    checked_files = 0
    
    for tsx_file in app_dir.rglob("*.tsx"):
        links = extract_links_from_file(tsx_file)
        checked_files += 1
        
        for link in links:
            # Normalize link path
            normalized_link = link.rstrip('/')
            if normalized_link == '':
                normalized_link = '/'
            
            # Check if route exists (allow for dynamic routes)
            if normalized_link not in existing_routes:
                # Check if it's a sub-route of an existing route
                parent_route = '/'.join(normalized_link.split('/')[:-1]) or '/'
                
                if parent_route not in existing_routes:
                    broken_links.append({
                        'file': str(tsx_file.relative_to(app_dir)),
                        'link': link,
                        'line': get_line_number(tsx_file, link)
                    })
    
    return broken_links, checked_files

def get_line_number(file_path, search_text):
    """Get line number where text appears in file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            if search_text in line:
                return i
    return None

def main():
    print_header("Frontend Link Validity Check")
    
    # Find frontend directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    frontend_dir = project_root / "frontend"
    
    if not frontend_dir.exists():
        print_error(f"Frontend directory not found: {frontend_dir}")
        sys.exit(1)
    
    # Get existing routes
    print_info("Scanning existing routes...")
    existing_routes = get_existing_routes(frontend_dir)
    print_info(f"Found {len(existing_routes)} existing routes:\n")
    
    for route in sorted(existing_routes):
        print_success(f"  {route}")
    
    # Check Suspense usage
    print("\n" + "="*70)
    print_info("Checking Suspense usage for useSearchParams...\n")
    
    suspense_issues = check_suspense_usage(frontend_dir)
    
    if suspense_issues:
        print_error(f"Found {len(suspense_issues)} Suspense issues:\n")
        for issue in suspense_issues:
            print_error(f"  File: {issue['file']}")
            print_error(f"  Issue: {issue['issue']}\n")
        print(f"{Fore.RED}❌ Suspense check FAILED{Style.RESET_ALL}")
        sys.exit(1)
    else:
        print_success("All useSearchParams properly wrapped in Suspense")
    
    # Check all links
    print("\n" + "="*70)
    print_info("Checking internal links...\n")
    
    broken_links, checked_files = check_all_links(frontend_dir)
    
    print_info(f"Checked {checked_files} files\n")
    
    if broken_links:
        print_error(f"Found {len(broken_links)} broken links:\n")
        for broken in broken_links:
            line_info = f":{broken['line']}" if broken['line'] else ""
            print_error(f"  File: {broken['file']}{line_info}")
            print_error(f"  Link: {broken['link']}\n")
        
        print(f"{Fore.RED}❌ Link validity check FAILED{Style.RESET_ALL}")
        sys.exit(1)
    else:
        print_success("All internal links are valid!")
        print(f"\n{Fore.GREEN}✅ Link validity check PASSED{Style.RESET_ALL}")
        sys.exit(0)

if __name__ == "__main__":
    main()
