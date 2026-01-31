# Plan: Migrate Study Tracker to Taskwarrior

## Goal
Replace custom `tracker.json` with Taskwarrior as the task backend, keeping:
- macOS Calendar sync (AppleScript-based)
- Study plan feature (`study plan 1h do, 1h pc`)

## Taskwarrior Setup

### UDAs (User Defined Attributes)
```bash
task config uda.weight.type string
task config uda.weight.label Weight
task config uda.score.type string
task config uda.score.label Score
task config uda.course_code.type string
task config uda.course_code.label Course
```

### Task Structure
```
project:pc.basic_part_1   # Course.assessment hierarchy
due:2026-01-30            # Deadline
weight:10%                # UDA
+wip                      # Tag for in_progress status
```

### Status Mapping
| Current | Taskwarrior |
|---------|-------------|
| not_started | pending |
| in_progress | pending +wip |
| completed | completed |
| submitted | completed +submitted |
| ongoing | pending +ongoing |

---

## Implementation

### 1. Create `src/taskwarrior.py` (new file)
Adapter module for Taskwarrior operations:
```python
def get_all_tasks() -> List[Dict]
    # subprocess.run(['task', 'export'], ...)

def get_tasks_by_course(alias: str) -> List[Dict]
    # Filter by project prefix

def update_task(task_id: int, **changes)
    # subprocess.run(['task', str(id), 'modify', ...])
```

### 2. Modify `src/calendar_sync.py`
Replace `collect_deadline_events()` to read from Taskwarrior:

```python
def collect_deadline_events() -> List[Dict]:
    result = subprocess.run(
        ['task', 'status:pending', 'due.any:', 'export'],
        capture_output=True, text=True
    )
    tasks = json.loads(result.stdout)

    events = []
    for task in tasks:
        # Parse ISO 8601 date from task['due']
        # Get course from task['project'].split('.')[0]
        # Build event dict (same format as now)
    return events
```

Keep unchanged:
- `add_events_batch()` - AppleScript logic
- `sync_calendar()` - just uses new data source
- `add_plan_to_calendar()` - study blocks

### 3. Modify `src/cli.py`
Slim down to wrapper commands:

**Keep:**
- `study calendar` - Sync to macOS Calendar
- `study plan` / `plan:status` / `plan:stop` - Timed study blocks
- `study hours <h> [course]` - Log hours via Timewarrior

**Remove/delegate to `task`:**
- `study status` → `task project.any:`
- `study next` → `task due.before:2w`
- `study update` → `task <id> modify`
- `study done` → `task <id> done`

### 4. Modify `src/planner.py`
Update `stop_plan()` to log hours via Timewarrior:
```python
def log_hours_timewarrior(hours: float, course: str):
    subprocess.run(['timew', 'track', f'{hours}h', 'study', course, ':yes'])
```

### 4b. Hours tracking with Timewarrior
- `study hours 2.5 pc` → `timew track 2.5h study pc`
- `study plan` auto-logs completed blocks to Timewarrior
- Weekly summary queries: `timew summary :week`

### 5. Create `scripts/migrate_to_taskwarrior.py`
One-time migration script:
- Read tracker.json
- Create Taskwarrior tasks with UDAs
- Mark completed tasks as done
- Backup tracker.json

### 6. Update `src/config.py`
Add Taskwarrior configuration and status mapping constants.

### 7. Remove/deprecate
- `src/data.py` - Most functions obsolete (Taskwarrior handles storage)
- `src/tracker.py` - Most functions replaced by `task` CLI
- `src/validation.py` - Taskwarrior validates input
- `src/history.py` - Use `task undo`
- `scripts/update_tracker.py` - Legacy, remove

---

## Files to Modify
1. `src/taskwarrior.py` - **NEW** - Adapter module
2. `src/calendar_sync.py` - Change data source in `collect_deadline_events()`
3. `src/cli.py` - Slim down, keep calendar/plan commands
4. `src/planner.py` - Update hours logging
5. `src/config.py` - Add Taskwarrior constants
6. `scripts/migrate_to_taskwarrior.py` - **NEW** - Migration script

## Files to Remove (after migration)
- `tracker.json` → `tracker.json.backup`
- `src/data.py` (or gut it)
- `src/tracker.py` (or gut it)
- `src/validation.py`
- `src/history.py`

---

## Verification

1. **Setup**: Run UDA configuration commands, install Timewarrior
2. **Migration**: Run migration script, verify tasks appear in `task list`
3. **Calendar**: Run `study calendar`, check events in macOS Calendar app
4. **Plan**: Run `study plan 1h pc`, verify notifications fire and hours logged to Timewarrior
5. **Hours**: Run `timew summary :week`, verify hours appear
6. **Native commands**: Verify `task pc`, `task 1 done`, `task undo` work
