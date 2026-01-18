#!/usr/bin/env python3
"""
Study Tracker Update Script
Usage: python update_tracker.py [command] [args]

Commands:
    status                          - Show all assessment statuses
    courses                         - List all course codes and assessment keys
    update <course> <assessment> <status> - Update assessment status
    score <course> <assessment> <score>   - Record a score
    hours <hours>                   - Log study hours for current week
    partner <name>                  - Set coursework partner (CV&PR)
    paper <title>                   - Set paper choice for Dist.Optim
    next                            - Show next 5 deadlines

Course Codes:
    pc   / ELEC70028  - Predictive Control
    do   / ELEC70082  - Distributed Optimisation and Learning
    cv   / ELEC70073  - Computer Vision and Pattern Recognition
    ao   / ELEC70066  - Applied Advanced Optimisation

Status options: not_started, in_progress, completed, submitted, overdue

Examples:
    python update_tracker.py status
    python update_tracker.py courses
    python update_tracker.py update pc basic_part_2 submitted
    python update_tracker.py update do ps1 completed
    python update_tracker.py score cv pr_coursework 85
    python update_tracker.py hours 2.5
    python update_tracker.py partner "John Smith"
    python update_tracker.py next
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

TRACKER_PATH = Path(__file__).parent.parent / "tracker.json"

# Short codes for courses (easier to type!)
COURSE_ALIASES = {
    'pc': 'ELEC70028',   # Predictive Control
    'do': 'ELEC70082',   # Distributed Optimisation
    'cv': 'ELEC70073',   # Computer Vision & PR
    'ao': 'ELEC70066',   # Applied Advanced Optimisation
}

COURSE_NAMES = {
    'ELEC70028': 'Predictive Control',
    'ELEC70082': 'Distributed Optimisation and Learning',
    'ELEC70073': 'Computer Vision and Pattern Recognition',
    'ELEC70066': 'Applied Advanced Optimisation',
}

def resolve_course_code(code):
    """Convert short alias to full course code"""
    code_lower = code.lower()
    if code_lower in COURSE_ALIASES:
        return COURSE_ALIASES[code_lower]
    return code.upper()

def load_tracker():
    with open(TRACKER_PATH, 'r') as f:
        return json.load(f)

def save_tracker(data):
    data['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    with open(TRACKER_PATH, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Tracker updated: {TRACKER_PATH}")

def show_courses():
    """Show all course codes and their assessment keys"""
    data = load_tracker()

    print("\n" + "="*70)
    print("COURSE CODES & ASSESSMENT KEYS")
    print("="*70)

    # Show aliases
    print("\nShort codes (use these for quick commands):")
    print("-" * 45)
    for alias, code in COURSE_ALIASES.items():
        print(f"  {alias:4} = {code}  ({COURSE_NAMES[code]})")

    print("\n" + "="*70)
    print("ASSESSMENT KEYS BY COURSE")
    print("="*70)

    for code, course in data['courses'].items():
        alias = [k for k, v in COURSE_ALIASES.items() if v == code][0]
        print(f"\n[{alias}] {code} - {course['name']}")
        print("-" * 50)
        for key, assessment in course['assessments'].items():
            deadline = assessment.get('deadline', 'TBD')
            print(f"  {key:20} - {assessment['name']} ({deadline})")

    print("\n" + "="*70)
    print("EXAMPLE COMMANDS")
    print("="*70)
    print("""
  python update_tracker.py update pc basic_part_2 submitted
  python update_tracker.py update do ps1 completed
  python update_tracker.py score cv pr_coursework 85
  python update_tracker.py score ao irat 5
""")

def show_status():
    data = load_tracker()
    print("\n" + "="*60)
    print("STUDY TRACKER STATUS")
    print(f"Last updated: {data['last_updated']}")
    print("="*60)

    for code, course in data['courses'].items():
        alias = [k for k, v in COURSE_ALIASES.items() if v == code][0]
        print(f"\n[{alias}] {code} - {course['name']}")
        print("-" * 40)
        for key, assessment in course['assessments'].items():
            status = assessment.get('status', 'unknown')
            deadline = assessment.get('deadline', 'TBD')
            weight = assessment.get('weight', '')
            score = assessment.get('score')

            status_emoji = {
                'not_started': '⬜',
                'in_progress': '🔄',
                'completed': '✅',
                'submitted': '📤',
                'overdue': '🔴',
                'ongoing': '🔁'
            }.get(status, '❓')

            score_str = f" [{score}]" if score else ""
            weight_str = f" ({weight})" if weight else ""
            print(f"  {status_emoji} {key:20} {assessment['name']}{weight_str}: {deadline}{score_str}")

def update_status(course_input, assessment_key, new_status):
    course_code = resolve_course_code(course_input)
    data = load_tracker()
    if course_code not in data['courses']:
        print(f"Error: Course '{course_input}' not found")
        print("\nAvailable courses:")
        for alias, code in COURSE_ALIASES.items():
            print(f"  {alias} = {code} ({COURSE_NAMES[code]})")
        return

    course = data['courses'][course_code]
    if assessment_key not in course['assessments']:
        print(f"Error: Assessment '{assessment_key}' not found in {COURSE_NAMES[course_code]}")
        print(f"\nAvailable assessments for {course_code}:")
        for key in course['assessments'].keys():
            print(f"  {key}")
        return

    course['assessments'][assessment_key]['status'] = new_status
    save_tracker(data)
    print(f"Updated {COURSE_NAMES[course_code]} / {assessment_key} → {new_status}")

def record_score(course_input, assessment_key, score):
    course_code = resolve_course_code(course_input)
    data = load_tracker()
    if course_code not in data['courses']:
        print(f"Error: Course '{course_input}' not found")
        print("\nAvailable courses:")
        for alias, code in COURSE_ALIASES.items():
            print(f"  {alias} = {code} ({COURSE_NAMES[code]})")
        return

    course = data['courses'][course_code]
    if assessment_key not in course['assessments']:
        print(f"Error: Assessment '{assessment_key}' not found in {COURSE_NAMES[course_code]}")
        print(f"\nAvailable assessments for {course_code}:")
        for key in course['assessments'].keys():
            print(f"  {key}")
        return

    course['assessments'][assessment_key]['score'] = score
    course['assessments'][assessment_key]['status'] = 'completed'
    save_tracker(data)
    print(f"Recorded score for {COURSE_NAMES[course_code]} / {assessment_key}: {score}")

def log_hours(hours):
    data = load_tracker()
    today = datetime.now()
    week_num = today.strftime('%Y-W%W')
    week_start = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')

    if week_num not in data['weekly_log']:
        data['weekly_log'][week_num] = {
            'week_of': week_start,
            'study_hours': 0,
            'completed_tasks': [],
            'notes': ''
        }

    data['weekly_log'][week_num]['study_hours'] += float(hours)
    save_tracker(data)
    total = data['weekly_log'][week_num]['study_hours']
    print(f"Logged {hours} hours. Total this week: {total} hours")

def set_partner(partner_name):
    data = load_tracker()
    course_code = 'ELEC70073'

    for key in ['pr_coursework', 'cv_coursework']:
        data['courses'][course_code]['assessments'][key]['partner'] = partner_name

    save_tracker(data)
    print(f"Set CV&PR coursework partner to: {partner_name}")

def set_paper(title):
    data = load_tracker()
    data['courses']['ELEC70082']['assessments']['paper_study']['paper_chosen'] = title
    save_tracker(data)
    print(f"Paper study topic set to: {title}")

def show_next_deadlines():
    data = load_tracker()
    deadlines = []

    for code, course in data['courses'].items():
        for key, assessment in course['assessments'].items():
            deadline = assessment.get('deadline', '')
            status = assessment.get('status', '')

            if status in ['completed', 'submitted']:
                continue
            if deadline in ['TBD', 'ongoing', '']:
                continue

            try:
                # Handle date range (e.g., "2026-03-16 to 2026-03-20")
                if ' to ' in deadline:
                    deadline = deadline.split(' to ')[0]
                deadline_date = datetime.strptime(deadline, '%Y-%m-%d')
                deadlines.append((deadline_date, code, assessment['name'], status))
            except:
                pass

    deadlines.sort(key=lambda x: x[0])

    print("\n" + "="*55)
    print("NEXT DEADLINES")
    print("="*55)

    today = datetime.now()
    for dl_date, code, name, status in deadlines[:5]:
        days_left = (dl_date - today).days
        if days_left < 0:
            days_str = f"OVERDUE by {-days_left} days!"
        elif days_left == 0:
            days_str = "DUE TODAY!"
        elif days_left == 1:
            days_str = "DUE TOMORROW!"
        else:
            days_str = f"{days_left} days left"

        alias = [k for k, v in COURSE_ALIASES.items() if v == code][0]
        course_name = COURSE_NAMES.get(code, code)
        print(f"\n{dl_date.strftime('%d %b')}: {name}")
        print(f"  [{alias}] {course_name}")
        print(f"  {status} | {days_str}")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1]

    if command == 'status':
        show_status()
    elif command == 'courses':
        show_courses()
    elif command == 'update' and len(sys.argv) >= 5:
        update_status(sys.argv[2], sys.argv[3], sys.argv[4])
    elif command == 'score' and len(sys.argv) >= 5:
        record_score(sys.argv[2], sys.argv[3], sys.argv[4])
    elif command == 'hours' and len(sys.argv) >= 3:
        log_hours(sys.argv[2])
    elif command == 'partner' and len(sys.argv) >= 3:
        set_partner(' '.join(sys.argv[2:]))
    elif command == 'paper' and len(sys.argv) >= 3:
        set_paper(' '.join(sys.argv[2:]))
    elif command == 'next':
        show_next_deadlines()
    else:
        print(__doc__)

if __name__ == '__main__':
    main()
