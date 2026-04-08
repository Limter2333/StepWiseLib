"""
Ralph Loop CLI
==============

Usage:
    python .ralph/cli.py create "Title" "Description" "P0" "claude" "criterion1" "criterion2"
    python .ralph/cli.py status
    python .ralph/cli.py start STORY-001
    python .ralph/cli.py verify STORY-001 0 pass "evidence..."
    python .ralph/cli.py report
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .ralph.user_story import RalphLoop


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1]
    ralph = RalphLoop()

    if command == "create":
        if len(sys.argv) < 5:
            print("Usage: create <title> <description> <priority> <agent> [criteria...]")
            return

        title = sys.argv[2]
        description = sys.argv[3]
        priority = sys.argv[4]
        agent = sys.argv[5]
        criteria = sys.argv[6:] if len(sys.argv) > 6 else []

        story = ralph.create_story(title, description, criteria, priority, agent)
        print(f"Created: {story.id}")

    elif command == "status":
        status = ralph.get_status()
        print(f"Total: {status['total']}, Todo: {status['todo']}, "
              f"In Progress: {status['in_progress']}, Done: {status['done']}, "
              f"Rate: {status['completion_rate']:.1%}")

    elif command == "start":
        if len(sys.argv) < 3:
            print("Usage: start <story_id>")
            return
        story_id = sys.argv[2]
        story = ralph.start_story(story_id)
        print(f"Started: {story.id} - {story.title}")

    elif command == "verify":
        if len(sys.argv) < 5:
            print("Usage: verify <story_id> <criterion_index> <pass|fail> [evidence]")
            return
        story_id = sys.argv[2]
        index = int(sys.argv[3])
        passed = sys.argv[4].lower() == "pass"
        evidence = sys.argv[5] if len(sys.argv) > 5 else ""
        story = ralph.verify_criterion(story_id, index, passed, evidence)
        print(f"Verified: {story.id} criterion {index} -> {'PASS' if passed else 'FAIL'}")
        if story.all_criteria_passed():
            print(f"Story {story.id} is DONE!")

    elif command == "report":
        print(ralph.generate_report())

    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
