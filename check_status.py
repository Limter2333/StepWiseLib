#!/usr/bin/env python3
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

def check_file_exists(path, description):
    full_path = PROJECT_ROOT / path
    status = "[OK]" if full_path.exists() else "[MISSING]"
    desc = description.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
    print(f"  {status} {desc}: {path}")
    return full_path.exists()

def main():
    print("=" * 60)
    print("AI Multi-Agent System - Project Status Check")
    print("=" * 60)
    print()
    
    print("[Architecture Files]")
    check_file_exists("core/exceptions.py", "Unified Exception Handling")
    check_file_exists("core/dependencies.py", "Dependency Injection")
    check_file_exists("agents/orchestrator/agent_manager.py", "Agent Manager")
    print()
    
    print("[Frontend Pages]")
    pages = [
        "web/src/pages/api-dashboard.html",
        "web/src/pages/agent-workbench.html",
        "web/src/pages/knowledge-manager.html",
        "web/src/pages/session-manager.html",
        "web/src/pages/monitoring-dashboard.html",
        "web/src/pages/mcp-playground.html",
        "web/src/pages/report-generator.html",
        "web/src/pages/log-viewer.html",
        "web/src/pages/settings.html",
    ]
    for page in pages:
        check_file_exists(page, page.split("/")[-1])
    print()
    
    print("[Test Files]")
    check_file_exists("tests/test_health_api.py", "Health API Tests")
    check_file_exists("tests/test_rag_api.py", "RAG API Tests")
    check_file_exists("tests/test_chat_api.py", "Chat API Tests")
    print()
    
    print("[Documentation]")
    check_file_exists("docs/DEPENDENCY_INJECTION.md", "Dependency Injection Guide")
    check_file_exists("docs/PROJECT_STATUS.md", "Project Status Report")
    check_file_exists("docs/DEPLOYMENT_CHECKLIST.md", "Deployment Checklist")
    check_file_exists("docs/API_REFERENCE.md", "API Reference")
    print()
    
    print("=" * 60)
    print("Check Complete")
    print("=" * 60)

if __name__ == "__main__":
    main()
