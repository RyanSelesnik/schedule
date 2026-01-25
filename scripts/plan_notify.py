#!/usr/bin/env python3
"""
Script executed by 'at' command when a study block completes.

Usage: python3 plan_notify.py <block_index>

This script:
1. Sends a macOS notification
2. Logs hours for the completed block
3. Updates plan state
"""

import sys
from pathlib import Path

# Add src to path
SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.parent))

from src.planner import load_plan, save_plan, get_plan_status
from src.notifications import send_study_notification
from src.tracker import log_hours
from src.config import CODE_TO_ALIAS


def main():
    if len(sys.argv) < 2:
        print("Usage: plan_notify.py <block_index>")
        return 1

    try:
        block_idx = int(sys.argv[1])
    except ValueError:
        print(f"Invalid block index: {sys.argv[1]}")
        return 1

    plan = load_plan()
    if not plan:
        print("No active plan")
        return 1

    blocks = plan.get("blocks", [])
    if block_idx >= len(blocks):
        print(f"Block {block_idx} does not exist")
        return 1

    # Get the completed block
    completed_block = blocks[block_idx]
    course_name = completed_block["course_name"]
    course_code = completed_block["course_code"]
    duration_mins = completed_block["duration_mins"]

    # Log hours for the completed block
    hours = duration_mins / 60
    alias = CODE_TO_ALIAS.get(course_code, course_code)
    try:
        log_hours(str(hours), alias)
        print(f"Logged {hours:.2f}h for {course_name}")
    except Exception as e:
        print(f"Failed to log hours: {e}")

    # Determine next block
    next_course = None
    if block_idx + 1 < len(blocks):
        next_block = blocks[block_idx + 1]
        next_course = next_block["course_name"]

    # Send notification
    if next_course:
        send_study_notification(
            course_name,
            action="switch",
            duration_mins=duration_mins,
            next_course=next_course,
        )
        print(f"Notified: {course_name} -> {next_course}")
    else:
        send_study_notification(
            course_name,
            action="end",
            duration_mins=duration_mins,
        )
        print(f"Notified: Plan complete! {course_name} finished.")

    # Mark block as completed in plan
    if "completed_blocks" not in plan:
        plan["completed_blocks"] = []
    plan["completed_blocks"].append(block_idx)
    save_plan(plan)

    return 0


if __name__ == "__main__":
    sys.exit(main())
