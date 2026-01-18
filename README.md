# Study Schedule Management System

A personal study management system for Imperial College EEE MSc courses (Spring 2026).

## Courses Tracked

| Code | Course | Assessment |
|------|--------|------------|
| ELEC70028 | Predictive Control | 100% Coursework + Oral |
| ELEC70082 | Distributed Optimisation and Learning | Mixed (PS 20%, Paper 20%, Exams 60%) |
| ELEC70073 | Computer Vision and Pattern Recognition | Coursework + Test |
| ELEC70066 | Applied Advanced Optimisation | iRAT/tRAT 25%, Peer 10%, Exam 65% |

## Quick Start

```bash
# Check your next deadlines
python scripts/update_tracker.py next

# See all assessment statuses
python scripts/update_tracker.py status
```

## Project Structure

```
study/
├── README.md                 # This file
├── courses.json              # Course database (JSON)
├── deadlines.md              # Deadline overview (human-readable)
├── weekly_schedule.md        # Weekly study plan
├── syllabus_detailed.md      # Week-by-week topic breakdowns
├── tracker.json              # Progress tracking data
└── scripts/
    ├── create_calendar.sh    # Create macOS calendar
    ├── add_study_events.sh   # Add study sessions to calendar
    ├── add_deadlines.sh      # Add deadlines to calendar
    └── update_tracker.py     # Progress tracker CLI
```

## Features

### 1. macOS Calendar Integration

A **"Study Schedule"** calendar is created with:
- Weekly study sessions for each course
- All assessment deadlines
- Exam dates and reminders

**Recreate calendar events:**
```bash
# If you need to recreate the calendar
./scripts/create_calendar.sh
./scripts/add_study_events.sh
./scripts/add_deadlines.sh
```

### 2. Progress Tracker CLI

Track your progress through assessments using the command-line tool.

#### View Status
```bash
# Show all assessment statuses with visual indicators
python scripts/update_tracker.py status

# Output shows:
# ⬜ not_started
# 🔄 in_progress
# ✅ completed
# 📤 submitted
# 🔴 overdue
# 🔁 ongoing
```

#### View Next Deadlines
```bash
# Show upcoming deadlines with days remaining
python scripts/update_tracker.py next
```

#### Update Assessment Status
```bash
python scripts/update_tracker.py update <COURSE_CODE> <assessment_key> <status>

# Examples:
python scripts/update_tracker.py update ELEC70028 basic_part_2 submitted
python scripts/update_tracker.py update ELEC70082 ps1 completed
python scripts/update_tracker.py update ELEC70073 pr_coursework in_progress

# Status options: not_started, in_progress, completed, submitted, overdue
```

#### Record Scores
```bash
python scripts/update_tracker.py score <COURSE_CODE> <assessment_key> <score>

# Examples:
python scripts/update_tracker.py score ELEC70082 ps1 pass
python scripts/update_tracker.py score ELEC70082 midterm 78
python scripts/update_tracker.py score ELEC70073 pr_coursework 85
```

#### Log Study Hours
```bash
python scripts/update_tracker.py hours <hours>

# Example: Log 3 hours of study
python scripts/update_tracker.py hours 3
```

#### Set Coursework Partner (CV&PR)
```bash
python scripts/update_tracker.py partner ELEC70073 "Partner Name"
```

#### Set Paper Study Topic (Distributed Optimisation)
```bash
python scripts/update_tracker.py paper "Federated Learning with Differential Privacy"
```

### 3. Assessment Keys Reference

Use these keys with the tracker:

**ELEC70028 (Predictive Control)**
- `basic_part_1` - Basic Part 1 (due 16 Jan)
- `basic_part_2` - Basic Part 2 (due 30 Jan)
- `core_part_1` - Core Part 1 (due 6 Feb)
- `core_part_2` - Core Part 2 (due 13 Mar)
- `oral_exam` - Oral Examination (16-20 Mar)

**ELEC70082 (Distributed Optimisation)**
- `ps1` - Problem Set 1 (due 29 Jan)
- `ps2` - Problem Set 2 (due 12 Feb)
- `midterm` - Mid-term Exam (17 Feb)
- `ps3` - Problem Set 3 (due 26 Feb)
- `ps4` - Problem Set 4 (due 12 Mar)
- `paper_study` - Paper Study (due 26 Mar)
- `final_exam` - Final Exam (TBD)

**ELEC70073 (Computer Vision & PR)**
- `pr_coursework` - Pattern Recognition CW (due 12 Feb)
- `cv_coursework` - Computer Vision CW (due 18 Mar)
- `wiseflow_test` - Wiseflow Test (13 Mar)

**ELEC70066 (Applied Adv. Optimisation)**
- `irat` - Weekly individual test
- `trat` - Weekly team test
- `peer_assessment` - Peer Assessment
- `final_exam` - Final Exam (TBD)

### 4. Reference Files

#### `deadlines.md`
Human-readable deadline overview with:
- Chronological list of all deadlines
- Weekly priority focus guide
- Assessment weight summary

#### `weekly_schedule.md`
Your study schedule showing:
- Fixed class times
- Recommended study blocks for each day
- Subject rotation guide

#### `syllabus_detailed.md`
Detailed breakdown including:
- Week-by-week topics for each course
- Key concepts to master
- Assessment strategies and tips

#### `courses.json`
Machine-readable database with:
- Course schedules
- Assessment details and deadlines
- Topic lists
- Lecturer contact info

## Weekly Workflow

### Monday - Predictive Control Day
1. Morning: Study/MATLAB work (9:00-12:00)
2. Lecture at 16:00

### Tuesday - Distributed Optimisation Day
1. Study before class (9:00-11:00)
2. Class at 11:00

### Wednesday - CV & PR Day
1. No classes - full study day
2. Work on coursework with partner

### Thursday - Split Day
1. Dist. Optim lecture (9:00-11:00)
2. Review time (12:00-14:00)
3. Pred. Control lecture (15:00-16:00)

### Friday - Heavy Lecture Day
1. **WATCH Applied Adv. Optim videos** (9:00-11:00)
2. Applied Adv. Optim class (11:00-13:00)
3. CV & PR lecture (14:00-16:00)

### Saturday - Deep Work
Focus on most urgent deadline (10:00-13:00)

### Sunday - Review
Weekly review and catch-up (14:00-17:00)

## Key Reminders

### Predictive Control
- Basic assignments: **First submission counts** (5 attempts)
- Core assignments: **Last submission counts** (20 attempts)
- Test code locally before MATLAB Grader submission
- **Do NOT book travel 16-20 March** (oral exam period)

### Distributed Optimisation
- Problem sets are **pass/fail** (5% each)
- All deadlines at **16:00**
- Mid-term covers Parts I & II only
- Paper study: reproduce numerical results

### Computer Vision & PR
- Coursework done in **pairs** - find partner early!
- Wiseflow test is **closed book, in-person**

### Applied Advanced Optimisation
- **MUST watch videos before Friday class**
- iRAT tests video content immediately
- Participate actively for peer assessment marks

## Syncing Changes

```bash
# After updating tracker or files
git add -A
git commit -m "Update progress"
git push
```

## License

Personal use only.
