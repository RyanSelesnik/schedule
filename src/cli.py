#!/usr/bin/env python3
"""
Study CLI - Main entry point.

Usage: study <command> [args]

Commands:
    status,   s              Show all assessment statuses
    courses,  c              List course codes and assessment keys
    next,     n [count]      Show upcoming deadlines (default: 5)
    update,   u <course> <assessment> <status>
    score       <course> <assessment> <score>
    hours,    h <hours>      Log study hours
    partner     <name>       Set CV&PR coursework partner
    paper       <title>      Set Dist.Optim paper topic

    generate, g              Regenerate markdown files from data
    calendar                 Sync calendar with tracker data
    backup                   List available backups
    restore     <backup>     Restore a backup file

    sync      [message]      Git commit and push
    pull                     Git pull

Course codes: pc (Predictive Control), do (Dist. Optim), cv (CV&PR), ao (Adv. Optim)
Status: not_started, in_progress, completed, submitted (or: done, wip, todo)
"""

import sys
import os
import subprocess
import shutil
from typing import Optional
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
)
from src.data import list_backups, restore_backup
from src.generator import generate_all
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
    """Print help message."""
    print("""
Study CLI - Manage your study schedule

USAGE: study <command> [args]

TRACKER COMMANDS:
    status,   s              Show all assessment statuses
    courses,  c              List course codes and assessment keys
    next,     n [count]      Show upcoming deadlines
    update,   u <course> <assessment> <status>
    score       <course> <assessment> <score>
    hours,    h <hours>      Log study hours
    partner     <name>       Set CV&PR coursework partner
    paper       <title>      Set Dist.Optim paper topic

DATA COMMANDS:
    generate, g              Regenerate markdown files from data
    calendar  [--regen]      Sync calendar (--regen to clear first)
    backup                   List available backups
    restore     <backup>     Restore a backup file

GIT COMMANDS:
    sync      [message]      Commit and push all changes
    pull                     Pull latest changes

COURSE CODES:
    pc = Predictive Control
    do = Distributed Optimisation
    cv = Computer Vision & PR
    ao = Applied Advanced Optimisation

STATUS OPTIONS:
    not_started, in_progress, completed, submitted, overdue
    Aliases: done, wip, todo, finished, working

EXAMPLES:
    study next
    study s
    study u pc basic_part_2 done
    study score do ps1 pass
    study h 2.5
    study sync "Finished PS1"
    study generate
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
    """
    Run a git command with proper error handling.

    Args:
        args: Git command arguments (without 'git' prefix)
        cwd: Working directory
        timeout: Timeout in seconds

    Returns:
        CompletedProcess result

    Raises:
        GitNotInstalledError: If git is not available
        GitNotRepoError: If not in a git repository
        GitCommandError: If command fails
    """
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


def cmd_sync(args):
    """Git sync command with comprehensive error handling."""
    msg = " ".join(args) if args else "Update progress"

    try:
        # Check for changes
        result = _run_git_command(["status", "-s"], cwd=BASE_DIR)

        if not result.stdout.strip():
            print("Nothing to sync - working tree clean")
            return 0

        print("Changes to sync:")
        print(result.stdout)

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
                # Try to set upstream
                branch_result = _run_git_command(
                    ["rev-parse", "--abbrev-ref", "HEAD"], cwd=BASE_DIR
                )
                branch = branch_result.stdout.strip()
                _run_git_command(
                    ["push", "-u", "origin", branch], cwd=BASE_DIR, timeout=120
                )
            elif "could not read from remote" in e.stderr.lower():
                raise GitPushError(
                    "Cannot connect to remote repository. Check your network connection."
                )
            elif "permission denied" in e.stderr.lower():
                raise GitPushError(
                    "Permission denied. Check your SSH keys or credentials."
                )
            else:
                raise GitPushError(e.stderr)

        print("\n✓ Synced successfully!")
        return 0

    except GitNotInstalledError:
        print("\n❌ Git is not installed")
        print("  Install from: https://git-scm.com/downloads")
        return 1
    except GitNotRepoError:
        print("\n❌ Not a git repository")
        print(f"  Run 'git init' in {BASE_DIR}")
        return 1
    except GitPushError as e:
        print(f"\n❌ Push failed: {e.message}")
        print("  Your changes have been committed locally.")
        print("  Try 'study sync' again when network is available.")
        return 1
    except GitCommandError as e:
        print(f"\n❌ Git error: {e.message}")
        return 1


def cmd_pull():
    """Git pull command with error handling."""
    try:
        result = _run_git_command(["pull"], cwd=BASE_DIR, timeout=120)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return 0

    except GitNotInstalledError:
        print("\n❌ Git is not installed")
        return 1
    except GitNotRepoError:
        print("\n❌ Not a git repository")
        return 1
    except GitCommandError as e:
        if "conflict" in e.stderr.lower():
            raise GitPullError(
                "Merge conflicts detected. Resolve manually with 'git status'."
            )
        elif "uncommitted changes" in e.stderr.lower():
            raise GitPullError(
                "You have uncommitted changes. Commit or stash them first."
            )
        elif "could not read from remote" in e.stderr.lower():
            raise GitPullError("Cannot connect to remote repository.")
        print(f"\n❌ Pull failed: {e.stderr}")
        return 1
    except GitPullError as e:
        print(f"\n❌ Pull failed: {e.message}")
        return 1


def cmd_calendar(args):
    """Calendar sync command with comprehensive error handling."""
    from src.calendar_sync import sync_calendar

    regenerate = "--regen" in args or "-r" in args

    try:
        print("Syncing calendar...")
        results = sync_calendar(regenerate=regenerate)

        print(f"✓ Created {results['deadlines']} deadline events")
        print(f"✓ Created {results['study_sessions']} study session events")

        if results.get("failed", 0) > 0:
            print(f"⚠️  {results['failed']} events failed to create")

        if results.get("cleared", 0) > 0:
            print(f"  (Cleared {results['cleared']} existing events)")

        return 0

    except CalendarPermissionError:
        print("\n❌ Calendar access denied")
        print(
            "  Grant access in: System Preferences > Security & Privacy > Privacy > Calendars"
        )
        return 1
    except CalendarConnectionError as e:
        print(f"\n❌ Cannot connect to Calendar: {e.message}")
        print("  Ensure Calendar.app is working correctly")
        return 1
    except CalendarTimeoutError as e:
        print(f"\n❌ Calendar operation timed out: {e.message}")
        print("  Calendar.app may be unresponsive. Try closing and reopening it.")
        return 1
    except CalendarError as e:
        print(f"\n❌ Calendar error: {e.message}")
        return 1


def cmd_backup():
    """List backups."""
    try:
        backups = list_backups()
        if not backups:
            print("No backups found")
            return 0

        print("\nAvailable backups:")
        print("-" * 60)
        for b in backups[:10]:
            size_kb = b["size"] / 1024
            print(
                f"  {b['name']:40} {b['modified'].strftime('%Y-%m-%d %H:%M')} ({size_kb:.1f}KB)"
            )

        print(f"\nBackup directory: {BASE_DIR / 'backups'}")
        return 0

    except OSError as e:
        print(f"\n❌ Cannot read backups: {e}")
        return 1


def cmd_restore(args):
    """Restore a backup with validation."""
    if not args:
        print("Usage: study restore <backup_name>")
        cmd_backup()
        return 1

    backup_name = args[0]

    try:
        restored = restore_backup(backup_name)
        print(f"✓ Restored from {backup_name}")
        print(f"  (Previous data backed up before restore)")
        return 0

    except DataNotFoundError as e:
        print(f"\n❌ {e.message}")
        if e.hint:
            print(f"  {e.hint}")
        return 1
    except DataCorruptedError as e:
        print(f"\n❌ Backup file is corrupted: {e.message}")
        print("  Try a different backup")
        return 1
    except DataWriteError as e:
        print(f"\n❌ Cannot restore: {e.message}")
        return 1


def cmd_generate():
    """Generate markdown files with error handling."""
    try:
        generated = generate_all()
        print("✓ Generated files:")
        for path in generated:
            print(f"  {path}")
        return 0

    except DataNotFoundError as e:
        print(f"\n❌ {e.message}")
        if e.hint:
            print(f"  {e.hint}")
        return 1
    except DataWriteError as e:
        print(f"\n❌ Cannot write files: {e.message}")
        return 1


def main():
    if len(sys.argv) < 2:
        print_help()
        return 0

    cmd = sys.argv[1].lower()
    args = sys.argv[2:]

    try:
        # Tracker commands
        if cmd in ("status", "s"):
            show_status()

        elif cmd in ("courses", "c"):
            show_courses()

        elif cmd in ("next", "n"):
            try:
                count = int(args[0]) if args else 5
                if count < 1:
                    print("Count must be at least 1")
                    return 1
            except ValueError:
                print(f"Invalid count: {args[0]}. Must be a number.")
                return 1
            show_next_deadlines(count)

        elif cmd in ("update", "u"):
            if len(args) < 3:
                print("Usage: study update <course> <assessment> <status>")
                print("Example: study u pc basic_part_2 done")
                return 1
            update_status(args[0], args[1], args[2])

        elif cmd == "score":
            if len(args) < 3:
                print("Usage: study score <course> <assessment> <score>")
                print("Example: study score do ps1 pass")
                return 1
            record_score(args[0], args[1], args[2])

        elif cmd in ("hours", "h"):
            if not args:
                print("Usage: study hours <hours>")
                print("Example: study h 2.5")
                return 1
            log_hours(args[0])

        elif cmd == "partner":
            if not args:
                print("Usage: study partner <name>")
                return 1
            set_partner(" ".join(args))

        elif cmd == "paper":
            if not args:
                print("Usage: study paper <title>")
                return 1
            set_paper(" ".join(args))

        # Data commands
        elif cmd in ("generate", "g"):
            return cmd_generate()

        elif cmd == "calendar":
            return cmd_calendar(args)

        elif cmd == "backup":
            return cmd_backup()

        elif cmd == "restore":
            return cmd_restore(args)

        # Git commands
        elif cmd == "sync":
            return cmd_sync(args)

        elif cmd == "pull":
            return cmd_pull()

        # Help
        elif cmd in ("help", "--help", "-h"):
            print_help()

        else:
            print(f"Unknown command: {cmd}")
            print("Run 'study help' for usage")
            return 1

    except ValidationError as e:
        print(f"\n❌ Validation error: {e.message}")
        if e.hint:
            print(f"  {e.hint}")
        return 1

    except DataNotFoundError as e:
        print(f"\n❌ File not found: {e.message}")
        if e.hint:
            print(f"  {e.hint}")
        return 1

    except DataCorruptedError as e:
        print(f"\n❌ Data corrupted: {e.message}")
        if e.hint:
            print(f"  {e.hint}")
        return 1

    except DataWriteError as e:
        print(f"\n❌ Write error: {e.message}")
        if e.hint:
            print(f"  {e.hint}")
        return 1

    except DataError as e:
        print(f"\n❌ Data error: {e.message}")
        if e.hint:
            print(f"  {e.hint}")
        return 1

    except CalendarError as e:
        print(f"\n❌ Calendar error: {e.message}")
        if e.hint:
            print(f"  {e.hint}")
        return 1

    except GitError as e:
        print(f"\n❌ Git error: {e.message}")
        if e.hint:
            print(f"  {e.hint}")
        return 1

    except StudyTrackerError as e:
        print(f"\n❌ Error: {e.message}")
        if e.hint:
            print(f"  {e.hint}")
        return 1

    except KeyboardInterrupt:
        print("\nCancelled")
        return 130  # Standard exit code for Ctrl+C

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("\nThis is a bug. Please report it with the following info:")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
