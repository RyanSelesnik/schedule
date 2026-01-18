# Study Schedule Management System

A personal study management system for Imperial College EEE MSc courses (Spring 2026).

## Features

- **Progress Tracking** - Track assessment status, scores, and study hours
- **Data Validation** - Prevents invalid data entry with helpful error messages
- **Automatic Backups** - Every save creates a timestamped backup
- **Calendar Integration** - Syncs deadlines to macOS Calendar with alerts
- **Single Source of Truth** - Markdown files generated from JSON data
- **Flexible CLI** - Short codes and status aliases for quick updates

## Courses Tracked

| Code | Short | Course | Assessment |
|------|-------|--------|------------|
| ELEC70028 | `pc` | Predictive Control | 100% Coursework + Oral |
| ELEC70082 | `do` | Distributed Optimisation and Learning | PS 20%, Paper 20%, Exams 60% |
| ELEC70073 | `cv` | Computer Vision and Pattern Recognition | Coursework + Test |
| ELEC70066 | `ao` | Applied Advanced Optimisation | iRAT/tRAT 25%, Peer 10%, Exam 65% |

## Quick Start

```bash
# See upcoming deadlines
study next

# See all assessment statuses
study status

# List course codes and assessment keys
study courses

# Update an assessment (uses validation!)
study u pc basic_part_2 done

# Log study hours
study h 2.5

# Sync to git
study sync "Finished PS1"
```

## Installation

The `study` CLI should be in your PATH. If not:

```bash
echo 'export PATH="$PATH:/Users/ryanselesnik/study/scripts"' >> ~/.zshrc
source ~/.zshrc
```

## CLI Reference

```
USAGE: study <command> [args]

TRACKER COMMANDS:
    status,   s              Show all assessment statuses
    courses,  c              List course codes and assessment keys
    next,     n [count]      Show upcoming deadlines (default: 5)
    update,   u <course> <assessment> <status>
    score       <course> <assessment> <score>
    hours,    h <hours>      Log study hours
    partner     <name>       Set CV&PR coursework partner
    paper       <title>      Set Dist.Optim paper topic

DATA COMMANDS:
    generate, g              Regenerate markdown files from tracker.json
    calendar  [--regen]      Sync calendar with tracker (--regen clears first)
    backup                   List available backups
    restore     <backup>     Restore a backup file

GIT COMMANDS:
    sync      [message]      Commit and push all changes
    pull                     Pull latest changes
```

## Course Codes

Use short codes for faster typing:

| Short | Full Code | Course |
|-------|-----------|--------|
| `pc` | ELEC70028 | Predictive Control |
| `do` | ELEC70082 | Distributed Optimisation |
| `cv` | ELEC70073 | Computer Vision & PR |
| `ao` | ELEC70066 | Applied Advanced Optimisation |

## Status Options

Valid statuses and their aliases:

| Status | Aliases |
|--------|---------|
| `not_started` | `todo`, `pending` |
| `in_progress` | `wip`, `working`, `started` |
| `completed` | `done`, `finished` |
| `submitted` | `submit`, `sent` |
| `overdue` | `late` |

## Project Structure

```
study/
├── README.md                 # This file
├── tracker.json              # Main data file (source of truth)
├── courses.json              # Course metadata
├── deadlines.md              # Generated from tracker.json
├── weekly_schedule.md        # Study schedule
├── syllabus_detailed.md      # Topic breakdowns
├── pytest.ini                # Test configuration
│
├── src/                      # Python package
│   ├── __init__.py
│   ├── cli.py               # Main CLI entry point
│   ├── config.py            # Configuration and constants
│   ├── data.py              # Data loading/saving with backups
│   ├── validation.py        # Input validation
│   ├── tracker.py           # Core tracker operations
│   ├── generator.py         # Markdown generation
│   └── calendar_sync.py     # macOS Calendar integration
│
├── scripts/                  # Shell scripts
│   ├── study                # CLI wrapper (delegates to src/cli.py)
│   └── *.sh                 # Legacy scripts
│
├── tests/                    # Unit tests
│   ├── test_validation.py
│   └── test_data.py
│
└── backups/                  # Automatic backups
    └── tracker_YYYYMMDD_HHMMSS.json
```

## Data Validation

The system validates all inputs:

```bash
# Invalid course code
$ study u invalid ps1 done
❌ Validation error: Unknown course: 'invalid'
Valid options: ELEC70028, ELEC70066, ELEC70073, ELEC70082, ao, cv, do, pc

# Invalid status
$ study u pc ps1 badstatus
❌ Validation error: Invalid status: 'badstatus'
Valid options: completed, in_progress, not_started, ongoing, overdue, submitted
Aliases: done, finished, submit, started, working, wip, todo, pending, late

# Ambiguous assessment key
$ study u pc basic done
❌ Validation error: Ambiguous assessment key: 'basic'
Did you mean one of: basic_part_1, basic_part_2?
```

## Automatic Backups

Every time you save data, a backup is created:

```bash
# List backups
$ study backup
Available backups:
  tracker_20260118_143309.json     2026-01-18 14:33

# Restore a backup
$ study restore tracker_20260118_143309.json
✓ Restored from tracker_20260118_143309.json
```

Backups are stored in `backups/` and the 10 most recent are kept.

## Generating Files

The `deadlines.md` file is generated from `tracker.json`:

```bash
$ study generate
✓ Generated files:
  /Users/ryanselesnik/study/deadlines.md
```

Run this after making changes to keep markdown files in sync.

## Calendar Integration

Sync deadlines to macOS Calendar:

```bash
# Add deadline events with alerts
$ study calendar
Syncing calendar...
✓ Created 12 deadline events
✓ Created 70 study session events

# Regenerate all events (clears existing first)
$ study calendar --regen
```

Events get alerts at 1 day, 2 hours, and 30 minutes before deadlines.

## Running Tests

```bash
# Install pytest first
pip install pytest

# Run tests
pytest tests/ -v
```

## Workflow Example

```bash
# Start of day - pull latest
study pull

# Check what's due
study next

# Do some work...

# Log progress
study u pc basic_part_2 done
study h 3

# Regenerate markdown
study generate

# Sync to git
study sync "Completed Basic Part 2"
```

## Assessment Keys Reference

Run `study courses` for the full list. Common ones:

**Predictive Control (pc)**
- `basic_part_1`, `basic_part_2`, `core_part_1`, `core_part_2`, `oral_exam`

**Distributed Optimisation (do)**
- `ps1`, `ps2`, `ps3`, `ps4`, `midterm`, `paper_study`, `final_exam`

**Computer Vision & PR (cv)**
- `pr_coursework`, `cv_coursework`, `wiseflow_test`

**Applied Advanced Optimisation (ao)**
- `irat`, `trat`, `peer_assessment`, `final_exam`

## Key Reminders

- **Predictive Control**: Basic = first submission counts (5 attempts), Core = last submission counts (20 attempts)
- **Distributed Optimisation**: Problem sets are pass/fail, deadlines at 16:00
- **CV & PR**: Coursework done in pairs - find partner early!
- **Applied Advanced Optimisation**: MUST watch videos before Friday class for iRAT

## License

Personal use only.
