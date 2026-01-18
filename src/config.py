"""
Configuration management for study tracker.
"""
import os
from pathlib import Path

# Base directory (can be overridden by env var)
BASE_DIR = Path(os.environ.get('STUDY_DIR', Path(__file__).parent.parent))

# Data files
DATA_DIR = BASE_DIR
TRACKER_PATH = DATA_DIR / "tracker.json"
COURSES_PATH = DATA_DIR / "courses.json"
BACKUP_DIR = BASE_DIR / "backups"

# Generated files
DEADLINES_PATH = DATA_DIR / "deadlines.md"
WEEKLY_SCHEDULE_PATH = DATA_DIR / "weekly_schedule.md"

# Ensure backup directory exists
BACKUP_DIR.mkdir(exist_ok=True)

# Course aliases (short codes)
COURSE_ALIASES = {
    'pc': 'ELEC70028',
    'do': 'ELEC70082',
    'cv': 'ELEC70073',
    'ao': 'ELEC70066',
}

# Reverse lookup
ALIAS_TO_CODE = COURSE_ALIASES
CODE_TO_ALIAS = {v: k for k, v in COURSE_ALIASES.items()}

# Course names
COURSE_NAMES = {
    'ELEC70028': 'Predictive Control',
    'ELEC70082': 'Distributed Optimisation and Learning',
    'ELEC70073': 'Computer Vision and Pattern Recognition',
    'ELEC70066': 'Applied Advanced Optimisation',
}

# Valid statuses
VALID_STATUSES = frozenset([
    'not_started',
    'in_progress',
    'completed',
    'submitted',
    'overdue',
    'ongoing',
])

# Backup settings
MAX_BACKUPS = 10  # Keep last N backups
