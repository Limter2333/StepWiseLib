#!/usr/bin/env python
"""
Verify all user stories have correct format and pass criteria

Usage: python scripts/verify_user_stories.py
"""
import json
import sys
from pathlib import Path

USER_STORIES_DIR = Path(__file__).parent.parent / "docs" / "user-stories"

def verify_user_stories():
    """Verify all user story JSON files"""
    has_errors = False

    if not USER_STORIES_DIR.exists():
        print(f"  No {USER_STORIES_DIR} directory found")
        return True

    json_files = list(USER_STORIES_DIR.glob("*.json"))

    if not json_files:
        print(f"  No .json files found in {USER_STORIES_DIR}")
        return True

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                content = json.load(f)

            # Validate structure
            if not isinstance(content, list):
                print(f"  {json_file.name} - must be a JSON array")
                has_errors = True
                continue

            for i, item in enumerate(content):
                if not isinstance(item, dict):
                    print(f"  {json_file.name}[{i}] - item must be an object")
                    has_errors = True
                    continue

                if 'description' not in item:
                    print(f"  {json_file.name}[{i}] - missing 'description'")
                    has_errors = True

                if 'steps' not in item:
                    print(f"  {json_file.name}[{i}] - missing 'steps'")
                    has_errors = True
                elif not isinstance(item['steps'], list) or len(item['steps']) == 0:
                    print(f"  {json_file.name}[{i}] - 'steps' must be non-empty array")
                    has_errors = True

                if 'passes' not in item:
                    print(f"  {json_file.name}[{i}] - missing 'passes'")
                    has_errors = True

            passing = sum(1 for item in content if item.get('passes', False))
            total = len(content)
            status = "PASSING" if passing == total else "NEEDS WORK"
            print(f"  {json_file.name} ({passing}/{total} passing) - {status}")

        except json.JSONDecodeError as e:
            print(f"  {json_file.name} - invalid JSON: {e}")
            has_errors = True
        except Exception as e:
            print(f"  {json_file.name} - error: {e}")
            has_errors = True

    return not has_errors

if __name__ == "__main__":
    print("\nVerifying user stories...\n")
    success = verify_user_stories()
    print()
    if success:
        print("All user stories valid\n")
        sys.exit(0)
    else:
        print("Verification failed\n")
        sys.exit(1)
