#!/bin/bash
# Script to add deadline events to macOS Calendar
# Usage: ./add_deadlines.sh

CALENDAR_NAME="Study Schedule"

osascript <<EOF
tell application "Calendar"
    set studyCal to calendar "$CALENDAR_NAME"

    -- January Deadlines
    make new event at studyCal with properties {summary:"DEADLINE: Dist.Optim PS1 (16:00)", start date:date "Thursday, 29 January 2026 at 15:00:00", end date:date "Thursday, 29 January 2026 at 16:00:00", description:"Problem Set 1: Inference and optimisation (5%, pass/fail)"}
    make new event at studyCal with properties {summary:"DEADLINE: Pred.Control Basic Part 2 (23:00)", start date:date "Friday, 30 January 2026 at 22:00:00", end date:date "Friday, 30 January 2026 at 23:00:00", description:"Gantry Crane Model, LQ-RHC. First submission counts, 5 attempts."}

    -- February Deadlines
    make new event at studyCal with properties {summary:"DEADLINE: Pred.Control Core Part 1 (23:00)", start date:date "Friday, 6 February 2026 at 22:00:00", end date:date "Friday, 6 February 2026 at 23:00:00", description:"Core assignment + report via TurnitIn. Last submission counts, 20 attempts."}
    make new event at studyCal with properties {summary:"DEADLINE: Dist.Optim PS2 (16:00)", start date:date "Thursday, 12 February 2026 at 15:00:00", end date:date "Thursday, 12 February 2026 at 16:00:00", description:"Problem Set 2: Distributed learning with fusion center (5%, pass/fail)"}
    make new event at studyCal with properties {summary:"DEADLINE: CV&PR - Pattern Recognition CW (16:00)", start date:date "Thursday, 12 February 2026 at 15:00:00", end date:date "Thursday, 12 February 2026 at 16:00:00", description:"Pattern Recognition coursework (pair work)"}
    make new event at studyCal with properties {summary:"EXAM: Dist.Optim Mid-term (30%)", start date:date "Tuesday, 17 February 2026 at 14:00:00", end date:date "Tuesday, 17 February 2026 at 15:30:00", description:"Covers Parts I and II: Inference, Learning, Distributed GD, Federated learning"}
    make new event at studyCal with properties {summary:"DEADLINE: Dist.Optim PS3 (16:00)", start date:date "Thursday, 26 February 2026 at 15:00:00", end date:date "Thursday, 26 February 2026 at 16:00:00", description:"Problem Set 3: Graphs (5%, pass/fail)"}

    -- March Deadlines
    make new event at studyCal with properties {summary:"DEADLINE: Dist.Optim PS4 (16:00)", start date:date "Thursday, 12 March 2026 at 15:00:00", end date:date "Thursday, 12 March 2026 at 16:00:00", description:"Problem Set 4: Decentralised learning (5%, pass/fail)"}
    make new event at studyCal with properties {summary:"DEADLINE: Pred.Control Core Part 2 (23:00)", start date:date "Friday, 13 March 2026 at 22:00:00", end date:date "Friday, 13 March 2026 at 23:00:00", description:"Core assignment + report via TurnitIn. Last submission counts, 20 attempts."}
    make new event at studyCal with properties {summary:"TEST: CV&PR Wiseflow (14:00, closed book)", start date:date "Friday, 13 March 2026 at 14:00:00", end date:date "Friday, 13 March 2026 at 16:00:00", description:"In-person, closed book test"}
    make new event at studyCal with properties {summary:"EXAM: Pred.Control Oral (16-20 Mar)", start date:date "Monday, 16 March 2026 at 09:00:00", end date:date "Friday, 20 March 2026 at 17:00:00", description:"In-person oral examination. Do NOT book travel during this period!"}
    make new event at studyCal with properties {summary:"DEADLINE: CV&PR - Computer Vision CW (16:00)", start date:date "Wednesday, 18 March 2026 at 15:00:00", end date:date "Wednesday, 18 March 2026 at 16:00:00", description:"Computer Vision coursework (pair work)"}
    make new event at studyCal with properties {summary:"DEADLINE: Dist.Optim Paper Study (16:00)", start date:date "Thursday, 26 March 2026 at 15:00:00", end date:date "Thursday, 26 March 2026 at 16:00:00", description:"2-page report on recent paper (20%). Identify contribution, limitation, reproduce results."}

    return "All deadline events added"
end tell
EOF

echo "All deadline events added to calendar '$CALENDAR_NAME'"
