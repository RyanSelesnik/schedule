#!/usr/bin/env python3
"""
Study CLI - Main entry point with improved UX.

Features:
- Color-coded output
- Confirmation prompts for destructive actions
- Undo functionality
- Progress summaries
- Numbered shortcuts for assessments
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

from src.tracker import (
    show_status,
    show_courses,
    show_next_deadlines,
    update_status,
    record_score,
    log_hours,
    set_partner,
    set_paper,
    show_weekly_summary,
    undo_last_change,
    show_history,
)
from src.data import list_backups, restore_backup
from src.generator import generate_all
from src.ui import (
    Colors,
    bold,
    green,
    yellow,
    red,
    cyan,
    gray,
    dim,
    confirm,
    prompt_choice,
    print_header,
    print_success,
    print_error,
    print_warning,
    print_info,
)
from src.errors import (
    StudyTrackerError,
    ValidationError,
    DataError,
    DataNotFoundError,
    DataCorruptedError,
    DataWriteError,
    CalendarError,
    CalendarConnectionError,
    CalendarPermissionError,
    CalendarTimeoutError,
    GitError,
    GitNotInstalledError,
    GitNotRepoError,
    GitCommandError,
    GitPushError,
    GitPullError,
)


def print_help():
    """Print help message with colors."""
    print(f"""
{bold("Study CLI")} - Manage your study schedule

{bold("USAGE:")} study <command> [args]

{bold("TRACKER COMMANDS:")}
    {cyan("status")},   {cyan("s")}              Show all assessment statuses
    {cyan("courses")},  {cyan("c")}              List course codes and assessment keys
    {cyan("next")},     {cyan("n")} [count]      Show upcoming deadlines
    {cyan("week")},     {cyan("w")}              Show weekly summary
    {cyan("update")},   {cyan("u")} <course> <#|key> <status>
    {cyan("score")}       <course> <#|key> <score>
    {cyan("hours")},    {cyan("h")} <hours> [course]   Log study hours
    {cyan("undo")}                       Undo last change
    {cyan("history")}                    Show recent changes
    {cyan("partner")}     <name>         Set CV&PR coursework partner
    {cyan("paper")}       <title>        Set Dist.Optim paper topic

{bold("DATA COMMANDS:")}
    {cyan("generate")}, {cyan("g")}              Regenerate markdown files
    {cyan("calendar")}  [--regen] [-y]  Sync calendar (--regen to clear first)
    {cyan("backup")}                    List available backups
    {cyan("restore")}     <backup>      Restore a backup file

{bold("GIT COMMANDS:")}
    {cyan("sync")}      [message]       Commit and push all changes
    {cyan("pull")}                      Pull latest changes

{bold("COURSE CODES:")}
    {green("pc")} = Predictive Control
    {green("do")} = Distributed Optimisation
    {green("cv")} = Computer Vision & PR
    {green("ao")} = Applied Advanced Optimisation

{bold("STATUS OPTIONS:")}
    not_started, in_progress, completed, submitted, overdue
    {dim("Aliases: done, wip, todo, finished, working")}

{bold("EXAMPLES:")}
    study next              {dim("# Show upcoming deadlines")}
    study s                 {dim("# Show status with progress")}
    study u pc 2 done       {dim("# Update 2nd PC assessment to done")}
    study u do ps1 wip      {dim("# Update by key name")}
    study h 2.5 pc          {dim("# Log 2.5h for Predictive Control")}
    study undo              {dim("# Undo last change")}
    study week              {dim("# Show weekly summary")}

{bold("FLAGS:")}
    --no-color              Disable colored output
    -y, --yes               Skip confirmation prompts
""")


def _check_git_installed() -> bool:
    """Check if git is available."""
    return shutil.which("git") is not None


def _check_git_repo(path: Path) -> bool:
    """Check if path is inside a git repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def _run_git_command(
    args: list, cwd: Optional[Path] = None, timeout: int = 60
) -> subprocess.CompletedProcess:
    """Run a git command with proper error handling."""
    if not _check_git_installed():
        raise GitNotInstalledError()

    if cwd and not _check_git_repo(cwd):
        raise GitNotRepoError(str(cwd))

    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd or BASE_DIR,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode != 0:
            cmd_str = " ".join(["git"] + args)
            raise GitCommandError(cmd_str, result.stderr, result.returncode)

        return result

    except subprocess.TimeoutExpired:
        cmd_str = " ".join(["git"] + args)
        raise GitCommandError(cmd_str, "Command timed out", -1)
    except FileNotFoundError:
        raise GitNotInstalledError()


def cmd_sync(args: List[str], skip_confirm: bool = False):
    """Git sync command."""
    msg = " ".join([a for a in args if not a.startswith("-")]) or "Update progress"

    try:
        result = _run_git_command(["status", "-s"], cwd=BASE_DIR)

        if not result.stdout.strip():
            print_info("Nothing to sync - working tree clean")
            return 0

        print(f"\n{bold('Changes to sync:')}")
        for line in result.stdout.strip().split("\n"):
            status = line[:2]
            filename = line[3:]
            if status.strip() == "M":
                print(f"  {yellow('M')} {filename}")
            elif status.strip() == "A" or status.strip() == "??":
                print(f"  {green('+')} {filename}")
            elif status.strip() == "D":
                print(f"  {red('-')} {filename}")
            else:
                print(f"  {status} {filename}")

        print()

        # Add all changes
        _run_git_command(["add", "-A"], cwd=BASE_DIR)

        # Commit
        commit_msg = f"{msg}\n\nCo-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
        _run_git_command(["commit", "-m", commit_msg], cwd=BASE_DIR)

        # Push
        try:
            _run_git_command(["push"], cwd=BASE_DIR, timeout=120)
        except GitCommandError as e:
            if "no upstream branch" in e.stderr.lower():
                branch_result = _run_git_command(
                    ["rev-parse", "--abbrev-ref", "HEAD"], cwd=BASE_DIR
                )
                branch = branch_result.stdout.strip()
                _run_git_command(
                    ["push", "-u", "origin", branch], cwd=BASE_DIR, timeout=120
                )
            elif "could not read from remote" in e.stderr.lower():
                raise GitPushError("Cannot connect to remote. Check your network.")
            elif "permission denied" in e.stderr.lower():
                raise GitPushError("Permission denied. Check your SSH keys.")
            else:
                raise GitPushError(e.stderr)

        print_success("Synced successfully!")
        return 0

    except GitNotInstalledError:
        print_error(
            "Git is not installed", "Install from: https://git-scm.com/downloads"
        )
        return 1
    except GitNotRepoError:
        print_error("Not a git repository", f"Run 'git init' in {BASE_DIR}")
        return 1
    except GitPushError as e:
        print_error(f"Push failed: {e.message}")
        print_info("Your changes have been committed locally.")
        return 1
    except GitCommandError as e:
        print_error(f"Git error: {e.message}")
        return 1


def cmd_pull():
    """Git pull command."""
    try:
        result = _run_git_command(["pull"], cwd=BASE_DIR, timeout=120)
        if result.stdout.strip():
            print(result.stdout)
        print_success("Pull complete")
        return 0

    except GitNotInstalledError:
        print_error("Git is not installed")
        return 1
    except GitNotRepoError:
        print_error("Not a git repository")
        return 1
    except GitCommandError as e:
        if "conflict" in e.stderr.lower():
            print_error("Merge conflicts detected", "Resolve with 'git status'")
        elif "uncommitted changes" in e.stderr.lower():
            print_error("Uncommitted changes", "Commit or stash them first")
        elif "could not read from remote" in e.stderr.lower():
            print_error("Cannot connect to remote")
        else:
            print_error(f"Pull failed: {e.stderr}")
        return 1


def cmd_calendar(args: List[str], skip_confirm: bool = False):
    """Calendar sync command with confirmation for regenerate."""
    from src.calendar_sync import sync_calendar

    regenerate = "--regen" in args or "-r" in args

    # Confirm regeneration
    if regenerate and not skip_confirm:
        if not confirm("This will delete existing calendar events. Continue?"):
            print("Cancelled")
            return 0

    try:
        print_info("Syncing calendar...")
        results = sync_calendar(regenerate=regenerate)

        print_success(f"Created {results['deadlines']} deadline events")
        print_success(f"Created {results['study_sessions']} study session events")

        if results.get("failed", 0) > 0:
            print_warning(f"{results['failed']} events failed to create")

        if results.get("cleared", 0) > 0:
            print(dim(f"  (Cleared {results['cleared']} existing events)"))

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


def cmd_backup():
    """List backups."""
    try:
        backups = list_backups()
        if not backups:
            print_info("No backups found")
            return 0

        print_header("BACKUPS")
        print()

        for i, b in enumerate(backups[:10], 1):
            size_kb = b["size"] / 1024
            date_str = b["modified"].strftime("%Y-%m-%d %H:%M")

            if i == 1:
                print(f"  {green('→')} {b['name']}")
                print(f"      {dim(date_str)} ({size_kb:.1f}KB) {dim('← latest')}")
            else:
                print(f"  {dim(str(i) + '.')} {b['name']}")
                print(f"      {dim(date_str)} ({size_kb:.1f}KB)")

        backup_dir = BASE_DIR / "backups"
        print(f"\n{dim('Backup directory:')} {backup_dir}")
        return 0

    except OSError as e:
        print_error(f"Cannot read backups: {e}")
        return 1


def cmd_restore(args: List[str], skip_confirm: bool = False):
    """Restore a backup with confirmation."""
    if not args:
        print("Usage: study restore <backup_name>")
        return cmd_backup()

    backup_name = args[0]

    # Confirm restore
    if not skip_confirm:
        print_warning(f"This will overwrite your current data with {backup_name}")
        if not confirm("Continue?"):
            print("Cancelled")
            return 0

    try:
        restore_backup(backup_name)
        print_success(f"Restored from {backup_name}")
        print(dim("  (Previous data backed up before restore)"))
        return 0

    except DataNotFoundError as e:
        print_error(e.message, e.hint)
        return 1
    except DataCorruptedError as e:
        print_error(f"Backup is corrupted: {e.message}", "Try a different backup")
        return 1
    except DataWriteError as e:
        print_error(f"Cannot restore: {e.message}")
        return 1


def cmd_generate():
    """Generate markdown files."""
    try:
        generated = generate_all()
        print_success("Generated files:")
        for path in generated:
            print(f"  {dim('•')} {path}")
        return 0

    except DataNotFoundError as e:
        print_error(e.message, e.hint)
        return 1
    except DataWriteError as e:
        print_error(f"Cannot write files: {e.message}")
        return 1


def main():
    # Handle global flags
    args = sys.argv[1:]
    skip_confirm = "-y" in args or "--yes" in args

    if "--no-color" in args:
        Colors.disable()
        args = [a for a in args if a != "--no-color"]

    args = [a for a in args if a not in ("-y", "--yes")]

    if len(args) < 1:
        print_help()
        return 0

    cmd = args[0].lower()
    cmd_args = args[1:]

    try:
        # Tracker commands
        if cmd in ("status", "s"):
            show_status()

        elif cmd in ("courses", "c"):
            show_courses()

        elif cmd in ("next", "n"):
            count = None
            if cmd_args:
                try:
                    count = int(cmd_args[0])
                    if count < 1:
                        print_error("Count must be at least 1")
                        return 1
                except ValueError:
                    print_error(f"Invalid count: {cmd_args[0]}")
                    return 1
            show_next_deadlines(count)

        elif cmd in ("week", "w", "weekly"):
            show_weekly_summary()

        elif cmd in ("update", "u"):
            if len(cmd_args) < 3:
                print("Usage: study update <course> <#|assessment> <status>")
                print(f"\n{dim('Examples:')}")
                print("  study u pc 2 done       # Update 2nd PC assessment")
                print("  study u do ps1 wip      # Update by key name")
                return 1
            update_status(cmd_args[0], cmd_args[1], cmd_args[2])

        elif cmd == "score":
            if len(cmd_args) < 3:
                print("Usage: study score <course> <#|assessment> <score>")
                print(f"\n{dim('Example:')} study score do 1 pass")
                return 1
            record_score(cmd_args[0], cmd_args[1], cmd_args[2])

        elif cmd in ("hours", "h"):
            if not cmd_args:
                print("Usage: study hours <hours> [course]")
                print(f"\n{dim('Examples:')}")
                print("  study h 2.5        # Log 2.5 hours")
                print("  study h 2.5 pc     # Log 2.5 hours for Predictive Control")
                return 1

            course = cmd_args[1] if len(cmd_args) > 1 else None
            log_hours(cmd_args[0], course)

        elif cmd == "undo":
            undo_last_change()

        elif cmd == "history":
            count = int(cmd_args[0]) if cmd_args else 10
            show_history(count)

        elif cmd == "partner":
            if not cmd_args:
                print("Usage: study partner <name>")
                return 1
            set_partner(" ".join(cmd_args))

        elif cmd == "paper":
            if not cmd_args:
                print("Usage: study paper <title>")
                return 1
            set_paper(" ".join(cmd_args))

        # Data commands
        elif cmd in ("generate", "g"):
            return cmd_generate()

        elif cmd == "calendar":
            return cmd_calendar(cmd_args, skip_confirm)

        elif cmd == "backup":
            return cmd_backup()

        elif cmd == "restore":
            return cmd_restore(cmd_args, skip_confirm)

        # Git commands
        elif cmd == "sync":
            return cmd_sync(cmd_args, skip_confirm)

        elif cmd == "pull":
            return cmd_pull()

        # Help
        elif cmd in ("help", "--help", "-h"):
            print_help()

        else:
            print_error(f"Unknown command: {cmd}")
            print(f"Run {cyan('study help')} for usage")
            return 1

    except ValidationError as e:
        print_error(f"Validation error: {e.message}", e.hint)
        return 1

    except DataNotFoundError as e:
        print_error(f"File not found: {e.message}", e.hint)
        return 1

    except DataCorruptedError as e:
        print_error(f"Data corrupted: {e.message}", e.hint)
        return 1

    except DataWriteError as e:
        print_error(f"Write error: {e.message}", e.hint)
        return 1

    except DataError as e:
        print_error(f"Data error: {e.message}", e.hint)
        return 1

    except CalendarError as e:
        print_error(f"Calendar error: {e.message}", e.hint)
        return 1

    except GitError as e:
        print_error(f"Git error: {e.message}", e.hint)
        return 1

    except StudyTrackerError as e:
        print_error(f"Error: {e.message}", e.hint)
        return 1

    except KeyboardInterrupt:
        print("\nCancelled")
        return 130

    except Exception as e:
        print_error(f"Unexpected error: {e}")
        print(f"\n{dim('This is a bug. Please report it with the following info:')}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
