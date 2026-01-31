#!/usr/bin/env python3
"""
Migrate tracker.json data to Taskwarrior.

Usage: python migrate_to_taskwarrior.py [--dry-run]
"""

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Course code to alias mapping
CODE_TO_ALIAS = {
    "ELEC70028": "pc",
    "ELEC70082": "do",
    "ELEC70073": "cv",
    "ELEC70066": "ao",
}

# Status mapping: tracker status -> (taskwarrior needs 'done', tags to add)
STATUS_MAPPING = {
    "not_started": (False, []),
    "in_progress": (False, ["wip"]),
    "completed": (True, []),
    "submitted": (True, ["submitted"]),
    "overdue": (False, ["overdue"]),
    "ongoing": (False, ["ongoing"]),
}


def run_task(args: list, dry_run: bool = False) -> bool:
    """Run a Taskwarrior command."""
    cmd = ["task", "rc.confirmation:no", "rc.verbose:nothing"] + args
    if dry_run:
        print(f"  [DRY RUN] {' '.join(cmd)}")
        return True
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def migrate_assessment(
    code: str,
    alias: str,
    key: str,
    assessment: dict,
    dry_run: bool = False
) -> bool:
    """Migrate a single assessment to Taskwarrior."""
    name = assessment.get("name", key)
    deadline = assessment.get("deadline", "")
    status = assessment.get("status", "not_started")
    weight = assessment.get("weight")
    score = assessment.get("score")
    notes = assessment.get("notes", "")
    partner = assessment.get("partner")

    # Build task add command
    project = f"{alias}.{key}"
    cmd = ["add", name, f"project:{project}", f"course_code:{code}"]

    # Add due date (skip TBD, ongoing, date ranges for now)
    if deadline and deadline not in ("TBD", "ongoing") and " to " not in deadline:
        cmd.append(f"due:{deadline}")

    # Add UDAs
    if weight:
        cmd.append(f"weight:{weight}")

    # Add tags for status
    mark_done, tags = STATUS_MAPPING.get(status, (False, []))
    for tag in tags:
        cmd.append(f"+{tag}")

    # Add partner as annotation later if present
    print(f"  Adding: [{alias}] {name}")
    success = run_task(cmd, dry_run)

    if not success:
        print(f"    FAILED to add task")
        return False

    # If completed/submitted, mark as done
    if mark_done and not dry_run:
        # Find the task we just created and mark done
        result = subprocess.run(
            ["task", f"project:{project}", "status:pending", "export"],
            capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            tasks = json.loads(result.stdout)
            if tasks:
                task_id = tasks[0].get("id")
                if task_id:
                    run_task([str(task_id), "done"])
                    print(f"    Marked as done")

    # Add score if present
    if score and not dry_run:
        result = subprocess.run(
            ["task", f"project:{project}", "export"],
            capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            tasks = json.loads(result.stdout)
            if tasks:
                task_uuid = tasks[0].get("uuid")
                if task_uuid:
                    run_task([task_uuid, "modify", f"score:{score}"])

    # Add notes as annotation
    if notes and not dry_run:
        result = subprocess.run(
            ["task", f"project:{project}", "export"],
            capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            tasks = json.loads(result.stdout)
            if tasks:
                task_uuid = tasks[0].get("uuid")
                if task_uuid:
                    run_task([task_uuid, "annotate", notes])

    return True


def migrate(tracker_path: Path, dry_run: bool = False):
    """Run the full migration."""
    print(f"Loading tracker from: {tracker_path}")

    with open(tracker_path) as f:
        data = json.load(f)

    courses = data.get("courses", {})
    total = 0
    success = 0

    for code, course in courses.items():
        alias = CODE_TO_ALIAS.get(code, code.lower())
        course_name = course.get("name", code)
        print(f"\n[{alias}] {course_name}")

        assessments = course.get("assessments", {})
        for key, assessment in assessments.items():
            total += 1
            if migrate_assessment(code, alias, key, assessment, dry_run):
                success += 1

    print(f"\n{'=' * 40}")
    print(f"Migration complete: {success}/{total} tasks created")

    if not dry_run:
        # Backup tracker.json
        backup_path = tracker_path.with_suffix(".json.backup")
        shutil.copy2(tracker_path, backup_path)
        print(f"Backed up tracker.json to: {backup_path}")

    # Show task list
    print("\nCurrent Taskwarrior tasks:")
    subprocess.run(["task", "list"])


def main():
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("DRY RUN MODE - no changes will be made\n")

    base_dir = Path(__file__).parent.parent
    tracker_path = base_dir / "tracker.json"

    if not tracker_path.exists():
        print(f"Error: {tracker_path} not found")
        sys.exit(1)

    migrate(tracker_path, dry_run)


if __name__ == "__main__":
    main()
