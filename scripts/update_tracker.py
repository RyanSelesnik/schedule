#!/usr/bin/env python3
"""
Study Tracker Update Script
Usage: python update_tracker.py [command] [args]

Commands:
    status                          - Show all assessment statuses
    update <course> <assessment> <status> - Update assessment status
    score <course> <assessment> <score>   - Record a score
    hours <hours>                   - Log study hours for current week
    partner <course> <name>         - Set coursework partner
    paper <title>                   - Set paper choice for Dist.Optim
    next                            - Show next 3 deadlines

Status options: not_started, in_progress, completed, submitted, overdue

Examples:
    python update_tracker.py status
    python update_tracker.py update ELEC70028 basic_part_2 submitted
    python update_tracker.py score ELEC70082 ps1 pass
    python update_tracker.py hours 15
    python update_tracker.py partner ELEC70073 "John Smith"
    python update_tracker.py next
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

TRACKER_PATH = Path(__file__).parent.parent / "tracker.json"

def load_tracker():
    with open(TRACKER_PATH, 'r') as f:
        return json.load(f)

def save_tracker(data):
    data['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    with open(TRACKER_PATH, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Tracker updated: {TRACKER_PATH}")

def show_status():
    data = load_tracker()
    print("\n" + "="*60)
    print("STUDY TRACKER STATUS")
    print(f"Last updated: {data['last_updated']}")
    print("="*60)

    for code, course in data['courses'].items():
        print(f"\n{code} - {course['name']}")
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
            print(f"  {status_emoji} {assessment['name']}{weight_str}: {deadline}{score_str}")

def update_status(course_code, assessment_key, new_status):
    data = load_tracker()
    if course_code not in data['courses']:
        print(f"Error: Course {course_code} not found")
        print(f"Available: {list(data['courses'].keys())}")
        return

    course = data['courses'][course_code]
    if assessment_key not in course['assessments']:
        print(f"Error: Assessment {assessment_key} not found")
        print(f"Available: {list(course['assessments'].keys())}")
        return

    course['assessments'][assessment_key]['status'] = new_status
    save_tracker(data)
    print(f"Updated {course_code}/{assessment_key} status to: {new_status}")

def record_score(course_code, assessment_key, score):
    data = load_tracker()
    if course_code not in data['courses']:
        print(f"Error: Course {course_code} not found")
        return

    course = data['courses'][course_code]
    if assessment_key not in course['assessments']:
        print(f"Error: Assessment {assessment_key} not found")
        return

    course['assessments'][assessment_key]['score'] = score
    course['assessments'][assessment_key]['status'] = 'completed'
    save_tracker(data)
    print(f"Recorded score for {course_code}/{assessment_key}: {score}")

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

def set_partner(course_code, partner_name):
    data = load_tracker()
    if course_code != 'ELEC70073':
        print("Partner only applicable to ELEC70073 (CV&PR)")
        return

    for key in ['pr_coursework', 'cv_coursework']:
        data['courses'][course_code]['assessments'][key]['partner'] = partner_name

    save_tracker(data)
    print(f"Set coursework partner to: {partner_name}")

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

    print("\n" + "="*50)
    print("NEXT DEADLINES")
    print("="*50)

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

        print(f"\n{dl_date.strftime('%d %b')}: {name}")
        print(f"  Course: {code}")
        print(f"  Status: {status} | {days_str}")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1]

    if command == 'status':
        show_status()
    elif command == 'update' and len(sys.argv) >= 5:
        update_status(sys.argv[2], sys.argv[3], sys.argv[4])
    elif command == 'score' and len(sys.argv) >= 5:
        record_score(sys.argv[2], sys.argv[3], sys.argv[4])
    elif command == 'hours' and len(sys.argv) >= 3:
        log_hours(sys.argv[2])
    elif command == 'partner' and len(sys.argv) >= 4:
        set_partner(sys.argv[2], ' '.join(sys.argv[3:]))
    elif command == 'paper' and len(sys.argv) >= 3:
        set_paper(' '.join(sys.argv[2:]))
    elif command == 'next':
        show_next_deadlines()
    else:
        print(__doc__)

if __name__ == '__main__':
    main()
