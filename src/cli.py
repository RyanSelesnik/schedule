#!/usr/bin/env python3
"""
Study CLI - Thin wrapper around Taskwarrior with custom features.

Custom features kept:
- calendar: Sync to macOS Calendar
- plan: Timed study blocks with notifications
- hours: Log to Timewarrior

Everything else delegates to Taskwarrior.
"""

import sys
import os
import subprocess
import shutil
from typing import Optional, List
from pathlib import Path

# Add src to path
SRC_DIR = Path(__file__).parent
BASE_DIR = SRC_DIR.parent
sys.path.insert(0, str(SRC_DIR.parent))

from src.planner import (
    create_plan,
    get_plan_status,
    stop_plan,
    load_plan,
    log_hours_timewarrior,
)
from src.ui import (
    Colors,
    bold,
    green,
    yellow,
    cyan,
    dim,
    print_header,
    print_success,
    print_error,
    print_warning,
    print_info,
)
from src.errors import (
    ValidationError,
    CalendarError,
    CalendarConnectionError,
    CalendarPermissionError,
    CalendarTimeoutError,
)


def print_help():
    """Print help message with colors."""
    print(f"""
{bold("Study CLI")} - Thin wrapper around Taskwarrior

{bold("CUSTOM COMMANDS:")}
    {cyan("calendar")}                  Sync deadlines to macOS Calendar
    {cyan("hours")}, {cyan("h")} <hrs> [course]  Log study hours to Timewarrior
    {cyan("plan")} <blocks>             Start timed study plan {dim("(e.g., '1h do, 1h pc')")}
    {cyan("plan:status")}               Show current plan
    {cyan("plan:stop")}                 Stop plan and log hours

{bold("GIT:")}
    {cyan("sync")} [message]            Commit and push changes
    {cyan("pull")}                      Pull latest changes

{bold("TASKWARRIOR (use directly):")}
    task                      List all tasks
    task pc                   List Predictive Control tasks
    task do                   List Distributed Optimisation tasks
    task <id> done            Mark task complete
    task <id> modify +wip     Mark as in progress
    task due.before:2w        Show tasks due in 2 weeks
    task undo                 Undo last change

{bold("TIMEWARRIOR (use directly):")}
    timew summary :week       Show weekly hours
    timew track 2h study pc   Log 2 hours for PC

{bold("COURSE CODES:")}
    {green("pc")} = Predictive Control
    {green("do")} = Distributed Optimisation
    {green("cv")} = Computer Vision & PR
    {green("ao")} = Applied Advanced Optimisation

{bold("EXAMPLES:")}
    study calendar            {dim("# Sync to macOS Calendar")}
    study h 2.5 pc            {dim("# Log 2.5h for PC via Timewarrior")}
    study plan 1h do, 1h pc   {dim("# Start 2-block study session")}
    task project:pc           {dim("# Show all PC tasks")}
    task 5 done               {dim("# Mark task 5 complete")}
""")


def cmd_calendar():
    """Calendar sync command."""
    from src.calendar_sync import sync_calendar

    try:
        print_info("Syncing calendar from Taskwarrior...")
        results = sync_calendar()

        print_success(f"Created {results['deadlines']} deadline events")
        print_success(f"Created {results['study_sessions']} study session events")

        if results.get("failed", 0) > 0:
            print_warning(f"{results['failed']} events failed to create")

        return 0

    except CalendarPermissionError:
        print_error(
            "Calendar access denied",
            "Grant access in: System Preferences > Privacy > Calendars",
        )
        return 1
    except CalendarConnectionError as e:
        print_error(f"Cannot connect to Calendar: {e.message}")
        return 1
    except CalendarTimeoutError as e:
        print_error(f"Calendar timed out: {e.message}")
        return 1
    except CalendarError as e:
        print_error(f"Calendar error: {e.message}")
        return 1


def cmd_hours(args: List[str]):
    """Log hours to Timewarrior."""
    if not args:
        print("Usage: study hours <hours> [course]")
        print(f"\n{dim('Examples:')}")
        print("  study h 2.5        # Log 2.5 hours (general study)")
        print("  study h 2.5 pc     # Log 2.5 hours for Predictive Control")
        print()
        print(f"{dim('Or use Timewarrior directly:')}")
        print("  timew track 2.5h study pc")
        return 1

    try:
        hours = float(args[0])
    except ValueError:
        print_error(f"Invalid hours: {args[0]}")
        return 1

    course = args[1] if len(args) > 1 else "general"

    if log_hours_timewarrior(hours, course):
        print_success(f"Logged {hours}h for {course}")
        print(dim("  View with: timew summary :week"))
        return 0
    else:
        print_error("Failed to log hours to Timewarrior")
        print(dim("  Is Timewarrior installed? brew install timewarrior"))
        return 1


def cmd_plan(args: List[str]):
    """Start a study plan."""
    if not args:
        return cmd_plan_status()

    plan_str = " ".join(args)

    existing = load_plan()
    if existing:
        status = get_plan_status()
        if status and not status.get("completed"):
            print_warning("A plan is already active!")
            print(f"  Current: {status.get('current_course', 'Unknown')}")
            print(f"  Time remaining: {status.get('time_remaining_mins', 0):.0f} min")
            print()
            print(f"Run {cyan('study plan:stop')} to stop it first.")
            return 1

    try:
        plan = create_plan(plan_str)
        blocks = plan["blocks"]

        print_success("Study plan started!")
        print()
        print_header("BLOCKS")
        total_mins = 0
        for i, block in enumerate(blocks):
            duration = block["duration_mins"]
            total_mins += duration
            if duration >= 60:
                dur_str = f"{duration // 60}h{duration % 60}m" if duration % 60 else f"{duration // 60}h"
            else:
                dur_str = f"{duration}m"
            print(f"  {i + 1}. {block['course_name']} ({dur_str})")

        print()
        print(f"Total: {total_mins / 60:.1f} hours")

        if plan.get("notifications_scheduled"):
            print(dim("\nNotifications scheduled. You'll be notified when blocks end."))

        return 0

    except ValidationError as e:
        print_error(e.message)
        print(f"\n{dim('Examples:')}")
        print("  study plan 1h do, 1h pc")
        print("  study plan 30m cv, 1.5h predictive")
        return 1


def cmd_plan_status():
    """Show current plan status."""
    status = get_plan_status()

    if not status:
        print_info("No active plan")
        print(f"\nStart one with: {cyan('study plan 1h do, 1h pc')}")
        return 0

    if status.get("completed"):
        print_success("Plan completed!")
        total = status.get("total_mins", 0)
        print(f"  Total: {total / 60:.1f} hours across {len(status.get('blocks', []))} blocks")
        return 0

    print_header("ACTIVE PLAN")
    print()

    current = status.get("current_course", "Unknown")
    remaining = status.get("time_remaining_mins", 0)
    print(f"  {green('▶')} {bold(current)}")
    print(f"    {remaining:.0f} min remaining")

    next_course = status.get("next_course")
    if next_course:
        print(f"\n  {dim('Next:')} {next_course}")

    print()
    current_idx = status.get("current_block", 0)
    for i, block in enumerate(status.get("blocks", [])):
        dur = block["duration_mins"]
        dur_str = f"{dur}m" if dur < 60 else f"{dur // 60}h{dur % 60}m" if dur % 60 else f"{dur // 60}h"
        if i < current_idx:
            print(f"  {green('✓')} {dim(block['course_name'])} ({dur_str})")
        elif i == current_idx:
            print(f"  {yellow('▶')} {bold(block['course_name'])} ({dur_str})")
        else:
            print(f"  {dim('○')} {block['course_name']} ({dur_str})")

    return 0


def cmd_plan_stop():
    """Stop the current plan and log hours to Timewarrior."""
    status = get_plan_status()

    if not status:
        print_info("No active plan to stop")
        return 0

    if status.get("completed"):
        print_info("Plan already completed")
        from src.planner import clear_plan
        clear_plan()
        return 0

    result = stop_plan(log_partial=True)

    if result and result.get("logged"):
        print_success("Plan stopped. Hours logged to Timewarrior:")
        for entry in result["logged"]:
            status_str = "complete" if entry.get("complete") else "partial"
            print(f"  {green('✓')} {entry['course']}: {entry['hours']:.2f}h ({status_str})")
        print(dim("\n  View with: timew summary :week"))
    else:
        print_success("Plan stopped (no hours to log)")

    return 0


def cmd_sync(args: List[str]):
    """Git sync command."""
    msg = " ".join(args) or "Update progress"

    try:
        result = subprocess.run(
            ["git", "status", "-s"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )

        if not result.stdout.strip():
            print_info("Nothing to sync - working tree clean")
            return 0

        print(f"\n{bold('Changes to sync:')}")
        print(result.stdout)

        subprocess.run(["git", "add", "-A"], cwd=BASE_DIR)
        subprocess.run(
            ["git", "commit", "-m", f"{msg}\n\nCo-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"],
            cwd=BASE_DIR,
        )
        subprocess.run(["git", "push"], cwd=BASE_DIR)

        print_success("Synced!")
        return 0

    except Exception as e:
        print_error(f"Git error: {e}")
        return 1


def cmd_pull():
    """Git pull command."""
    try:
        subprocess.run(["git", "pull"], cwd=BASE_DIR)
        print_success("Pull complete")
        return 0
    except Exception as e:
        print_error(f"Git error: {e}")
        return 1


def main():
    args = sys.argv[1:]

    if "--no-color" in args:
        Colors.disable()
        args = [a for a in args if a != "--no-color"]

    if len(args) < 1:
        print_help()
        return 0

    cmd = args[0].lower()
    cmd_args = args[1:]

    try:
        if cmd == "calendar":
            return cmd_calendar()

        elif cmd in ("hours", "h", "log"):
            return cmd_hours(cmd_args)

        elif cmd == "plan":
            return cmd_plan(cmd_args)

        elif cmd == "plan:status":
            return cmd_plan_status()

        elif cmd == "plan:stop":
            return cmd_plan_stop()

        elif cmd == "sync":
            return cmd_sync(cmd_args)

        elif cmd == "pull":
            return cmd_pull()

        elif cmd in ("help", "--help", "-h"):
            print_help()
            return 0

        else:
            # Pass through to Taskwarrior
            print(dim(f"Passing to Taskwarrior: task {' '.join(args)}"))
            return subprocess.run(["task"] + args).returncode

    except KeyboardInterrupt:
        print("\nCancelled")
        return 130

    except Exception as e:
        print_error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
