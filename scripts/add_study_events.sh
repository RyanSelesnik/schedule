#!/bin/bash
# Script to add weekly study events to macOS Calendar
# Usage: ./add_study_events.sh

CALENDAR_NAME="Study Schedule"

# Monday: Predictive Control Study
osascript <<EOF
tell application "Calendar"
    set studyCal to calendar "$CALENDAR_NAME"
    make new event at studyCal with properties {summary:"Study: Predictive Control", start date:date "Monday, 19 January 2026 at 09:00:00", end date:date "Monday, 19 January 2026 at 12:00:00", description:"MATLAB Grader assignments, review lecture notes"}
    make new event at studyCal with properties {summary:"Study: Predictive Control", start date:date "Monday, 26 January 2026 at 09:00:00", end date:date "Monday, 26 January 2026 at 12:00:00", description:"MATLAB Grader assignments, review lecture notes"}
    make new event at studyCal with properties {summary:"Study: Predictive Control", start date:date "Monday, 2 February 2026 at 09:00:00", end date:date "Monday, 2 February 2026 at 12:00:00", description:"MATLAB Grader assignments, review lecture notes"}
    make new event at studyCal with properties {summary:"Study: Predictive Control", start date:date "Monday, 9 February 2026 at 09:00:00", end date:date "Monday, 9 February 2026 at 12:00:00", description:"MATLAB Grader assignments, review lecture notes"}
    make new event at studyCal with properties {summary:"Study: Predictive Control", start date:date "Monday, 16 February 2026 at 09:00:00", end date:date "Monday, 16 February 2026 at 12:00:00", description:"MATLAB Grader assignments, review lecture notes"}
    make new event at studyCal with properties {summary:"Study: Predictive Control", start date:date "Monday, 23 February 2026 at 09:00:00", end date:date "Monday, 23 February 2026 at 12:00:00", description:"MATLAB Grader assignments, review lecture notes"}
    make new event at studyCal with properties {summary:"Study: Predictive Control", start date:date "Monday, 2 March 2026 at 09:00:00", end date:date "Monday, 2 March 2026 at 12:00:00", description:"MATLAB Grader assignments, review lecture notes"}
    make new event at studyCal with properties {summary:"Study: Predictive Control", start date:date "Monday, 9 March 2026 at 09:00:00", end date:date "Monday, 9 March 2026 at 12:00:00", description:"MATLAB Grader assignments, review lecture notes"}
    make new event at studyCal with properties {summary:"Study: Predictive Control", start date:date "Monday, 16 March 2026 at 09:00:00", end date:date "Monday, 16 March 2026 at 12:00:00", description:"Oral exam prep"}
end tell
EOF

# Tuesday: Distributed Optimisation Study
osascript <<EOF
tell application "Calendar"
    set studyCal to calendar "$CALENDAR_NAME"
    make new event at studyCal with properties {summary:"Study: Distributed Optimisation", start date:date "Tuesday, 20 January 2026 at 09:00:00", end date:date "Tuesday, 20 January 2026 at 11:00:00", description:"Problem Sets, review lecture material"}
    make new event at studyCal with properties {summary:"Study: Distributed Optimisation", start date:date "Tuesday, 27 January 2026 at 09:00:00", end date:date "Tuesday, 27 January 2026 at 11:00:00", description:"Problem Sets, review lecture material"}
    make new event at studyCal with properties {summary:"Study: Distributed Optimisation", start date:date "Tuesday, 3 February 2026 at 09:00:00", end date:date "Tuesday, 3 February 2026 at 11:00:00", description:"Problem Sets, review lecture material"}
    make new event at studyCal with properties {summary:"Study: Distributed Optimisation", start date:date "Tuesday, 10 February 2026 at 09:00:00", end date:date "Tuesday, 10 February 2026 at 11:00:00", description:"Problem Sets, review lecture material"}
    make new event at studyCal with properties {summary:"Study: Distributed Optimisation", start date:date "Tuesday, 17 February 2026 at 09:00:00", end date:date "Tuesday, 17 February 2026 at 11:00:00", description:"Problem Sets, review lecture material"}
    make new event at studyCal with properties {summary:"Study: Distributed Optimisation", start date:date "Tuesday, 24 February 2026 at 09:00:00", end date:date "Tuesday, 24 February 2026 at 11:00:00", description:"Problem Sets, review lecture material"}
    make new event at studyCal with properties {summary:"Study: Distributed Optimisation", start date:date "Tuesday, 3 March 2026 at 09:00:00", end date:date "Tuesday, 3 March 2026 at 11:00:00", description:"Problem Sets, review lecture material"}
    make new event at studyCal with properties {summary:"Study: Distributed Optimisation", start date:date "Tuesday, 10 March 2026 at 09:00:00", end date:date "Tuesday, 10 March 2026 at 11:00:00", description:"Problem Sets, review lecture material"}
    make new event at studyCal with properties {summary:"Study: Distributed Optimisation", start date:date "Tuesday, 17 March 2026 at 09:00:00", end date:date "Tuesday, 17 March 2026 at 11:00:00", description:"Paper study work"}
end tell
EOF

# Wednesday: Computer Vision & PR Study
osascript <<EOF
tell application "Calendar"
    set studyCal to calendar "$CALENDAR_NAME"
    make new event at studyCal with properties {summary:"Study: Computer Vision & Pattern Recognition", start date:date "Wednesday, 21 January 2026 at 10:00:00", end date:date "Wednesday, 21 January 2026 at 13:00:00", description:"Coursework, review Friday lectures"}
    make new event at studyCal with properties {summary:"Study: Computer Vision & Pattern Recognition", start date:date "Wednesday, 28 January 2026 at 10:00:00", end date:date "Wednesday, 28 January 2026 at 13:00:00", description:"Coursework, review Friday lectures"}
    make new event at studyCal with properties {summary:"Study: Computer Vision & Pattern Recognition", start date:date "Wednesday, 4 February 2026 at 10:00:00", end date:date "Wednesday, 4 February 2026 at 13:00:00", description:"Coursework, review Friday lectures"}
    make new event at studyCal with properties {summary:"Study: Computer Vision & Pattern Recognition", start date:date "Wednesday, 11 February 2026 at 10:00:00", end date:date "Wednesday, 11 February 2026 at 13:00:00", description:"Coursework, review Friday lectures"}
    make new event at studyCal with properties {summary:"Study: Computer Vision & Pattern Recognition", start date:date "Wednesday, 18 February 2026 at 10:00:00", end date:date "Wednesday, 18 February 2026 at 13:00:00", description:"Coursework, review Friday lectures"}
    make new event at studyCal with properties {summary:"Study: Computer Vision & Pattern Recognition", start date:date "Wednesday, 25 February 2026 at 10:00:00", end date:date "Wednesday, 25 February 2026 at 13:00:00", description:"Coursework, review Friday lectures"}
    make new event at studyCal with properties {summary:"Study: Computer Vision & Pattern Recognition", start date:date "Wednesday, 4 March 2026 at 10:00:00", end date:date "Wednesday, 4 March 2026 at 13:00:00", description:"Coursework, review Friday lectures"}
    make new event at studyCal with properties {summary:"Study: Computer Vision & Pattern Recognition", start date:date "Wednesday, 11 March 2026 at 10:00:00", end date:date "Wednesday, 11 March 2026 at 13:00:00", description:"Test prep + coursework"}
    make new event at studyCal with properties {summary:"Study: Computer Vision & Pattern Recognition", start date:date "Wednesday, 18 March 2026 at 10:00:00", end date:date "Wednesday, 18 March 2026 at 13:00:00", description:"CV Coursework final push"}
end tell
EOF

# Thursday: Review between lectures
osascript <<EOF
tell application "Calendar"
    set studyCal to calendar "$CALENDAR_NAME"
    make new event at studyCal with properties {summary:"Study: Review (Dist.Optim + Pred.Control)", start date:date "Thursday, 22 January 2026 at 12:00:00", end date:date "Thursday, 22 January 2026 at 14:00:00", description:"Review morning lecture, prep for afternoon"}
    make new event at studyCal with properties {summary:"Study: Review (Dist.Optim + Pred.Control)", start date:date "Thursday, 29 January 2026 at 12:00:00", end date:date "Thursday, 29 January 2026 at 14:00:00", description:"Review morning lecture, prep for afternoon"}
    make new event at studyCal with properties {summary:"Study: Review (Dist.Optim + Pred.Control)", start date:date "Thursday, 5 February 2026 at 12:00:00", end date:date "Thursday, 5 February 2026 at 14:00:00", description:"Review morning lecture, prep for afternoon"}
    make new event at studyCal with properties {summary:"Study: Review (Dist.Optim + Pred.Control)", start date:date "Thursday, 12 February 2026 at 12:00:00", end date:date "Thursday, 12 February 2026 at 14:00:00", description:"Review morning lecture, prep for afternoon"}
    make new event at studyCal with properties {summary:"Study: Review (Dist.Optim + Pred.Control)", start date:date "Thursday, 19 February 2026 at 12:00:00", end date:date "Thursday, 19 February 2026 at 14:00:00", description:"Review morning lecture, prep for afternoon"}
    make new event at studyCal with properties {summary:"Study: Review (Dist.Optim + Pred.Control)", start date:date "Thursday, 26 February 2026 at 12:00:00", end date:date "Thursday, 26 February 2026 at 14:00:00", description:"Review morning lecture, prep for afternoon"}
    make new event at studyCal with properties {summary:"Study: Review (Dist.Optim + Pred.Control)", start date:date "Thursday, 5 March 2026 at 12:00:00", end date:date "Thursday, 5 March 2026 at 14:00:00", description:"Review morning lecture, prep for afternoon"}
    make new event at studyCal with properties {summary:"Study: Review (Dist.Optim + Pred.Control)", start date:date "Thursday, 12 March 2026 at 12:00:00", end date:date "Thursday, 12 March 2026 at 14:00:00", description:"Review morning lecture, prep for afternoon"}
    make new event at studyCal with properties {summary:"Study: Review (Dist.Optim + Pred.Control)", start date:date "Thursday, 19 March 2026 at 12:00:00", end date:date "Thursday, 19 March 2026 at 14:00:00", description:"Oral exam prep"}
end tell
EOF

# Friday: Watch Applied Adv. Optimisation videos
osascript <<EOF
tell application "Calendar"
    set studyCal to calendar "$CALENDAR_NAME"
    make new event at studyCal with properties {summary:"WATCH: Applied Adv. Optimisation Videos", start date:date "Friday, 23 January 2026 at 09:00:00", end date:date "Friday, 23 January 2026 at 11:00:00", description:"MUST WATCH before class! iRAT test is based on these"}
    make new event at studyCal with properties {summary:"WATCH: Applied Adv. Optimisation Videos", start date:date "Friday, 30 January 2026 at 09:00:00", end date:date "Friday, 30 January 2026 at 11:00:00", description:"MUST WATCH before class! iRAT test is based on these"}
    make new event at studyCal with properties {summary:"WATCH: Applied Adv. Optimisation Videos", start date:date "Friday, 6 February 2026 at 09:00:00", end date:date "Friday, 6 February 2026 at 11:00:00", description:"MUST WATCH before class! iRAT test is based on these"}
    make new event at studyCal with properties {summary:"WATCH: Applied Adv. Optimisation Videos", start date:date "Friday, 13 February 2026 at 09:00:00", end date:date "Friday, 13 February 2026 at 11:00:00", description:"MUST WATCH before class! iRAT test is based on these"}
    make new event at studyCal with properties {summary:"WATCH: Applied Adv. Optimisation Videos", start date:date "Friday, 20 February 2026 at 09:00:00", end date:date "Friday, 20 February 2026 at 11:00:00", description:"MUST WATCH before class! iRAT test is based on these"}
    make new event at studyCal with properties {summary:"WATCH: Applied Adv. Optimisation Videos", start date:date "Friday, 27 February 2026 at 09:00:00", end date:date "Friday, 27 February 2026 at 11:00:00", description:"MUST WATCH before class! iRAT test is based on these"}
    make new event at studyCal with properties {summary:"WATCH: Applied Adv. Optimisation Videos", start date:date "Friday, 6 March 2026 at 09:00:00", end date:date "Friday, 6 March 2026 at 11:00:00", description:"MUST WATCH before class! iRAT test is based on these"}
    make new event at studyCal with properties {summary:"WATCH: Applied Adv. Optimisation Videos", start date:date "Friday, 13 March 2026 at 09:00:00", end date:date "Friday, 13 March 2026 at 11:00:00", description:"MUST WATCH before class! iRAT test is based on these"}
end tell
EOF

# Saturday: Deep work
osascript <<EOF
tell application "Calendar"
    set studyCal to calendar "$CALENDAR_NAME"
    make new event at studyCal with properties {summary:"Study: Deep Work (Deadline Priority)", start date:date "Saturday, 24 January 2026 at 10:00:00", end date:date "Saturday, 24 January 2026 at 13:00:00", description:"Focus: PS1 + Basic Part 2"}
    make new event at studyCal with properties {summary:"Study: Deep Work (Deadline Priority)", start date:date "Saturday, 31 January 2026 at 10:00:00", end date:date "Saturday, 31 January 2026 at 13:00:00", description:"Focus: Core Part 1"}
    make new event at studyCal with properties {summary:"Study: Deep Work (Deadline Priority)", start date:date "Saturday, 7 February 2026 at 10:00:00", end date:date "Saturday, 7 February 2026 at 13:00:00", description:"Focus: PS2 + PR Coursework"}
    make new event at studyCal with properties {summary:"Study: Deep Work (Deadline Priority)", start date:date "Saturday, 14 February 2026 at 10:00:00", end date:date "Saturday, 14 February 2026 at 13:00:00", description:"Focus: Mid-term exam prep"}
    make new event at studyCal with properties {summary:"Study: Deep Work (Deadline Priority)", start date:date "Saturday, 21 February 2026 at 10:00:00", end date:date "Saturday, 21 February 2026 at 13:00:00", description:"Focus: PS3"}
    make new event at studyCal with properties {summary:"Study: Deep Work (Deadline Priority)", start date:date "Saturday, 28 February 2026 at 10:00:00", end date:date "Saturday, 28 February 2026 at 13:00:00", description:"Focus: Core Part 2 + CV Coursework"}
    make new event at studyCal with properties {summary:"Study: Deep Work (Deadline Priority)", start date:date "Saturday, 7 March 2026 at 10:00:00", end date:date "Saturday, 7 March 2026 at 13:00:00", description:"Focus: PS4 + Test prep"}
    make new event at studyCal with properties {summary:"Study: Deep Work (Deadline Priority)", start date:date "Saturday, 14 March 2026 at 10:00:00", end date:date "Saturday, 14 March 2026 at 13:00:00", description:"Focus: CV Coursework + Oral prep"}
    make new event at studyCal with properties {summary:"Study: Deep Work (Deadline Priority)", start date:date "Saturday, 21 March 2026 at 10:00:00", end date:date "Saturday, 21 March 2026 at 13:00:00", description:"Focus: Paper Study"}
end tell
EOF

# Sunday: Review / Catch-up
osascript <<EOF
tell application "Calendar"
    set studyCal to calendar "$CALENDAR_NAME"
    make new event at studyCal with properties {summary:"Study: Weekly Review & Catch-up", start date:date "Sunday, 25 January 2026 at 14:00:00", end date:date "Sunday, 25 January 2026 at 17:00:00", description:"Review week, prep for next week"}
    make new event at studyCal with properties {summary:"Study: Weekly Review & Catch-up", start date:date "Sunday, 1 February 2026 at 14:00:00", end date:date "Sunday, 1 February 2026 at 17:00:00", description:"Review week, prep for next week"}
    make new event at studyCal with properties {summary:"Study: Weekly Review & Catch-up", start date:date "Sunday, 8 February 2026 at 14:00:00", end date:date "Sunday, 8 February 2026 at 17:00:00", description:"Review week, prep for next week"}
    make new event at studyCal with properties {summary:"Study: Weekly Review & Catch-up", start date:date "Sunday, 15 February 2026 at 14:00:00", end date:date "Sunday, 15 February 2026 at 17:00:00", description:"Mid-term exam prep!"}
    make new event at studyCal with properties {summary:"Study: Weekly Review & Catch-up", start date:date "Sunday, 22 February 2026 at 14:00:00", end date:date "Sunday, 22 February 2026 at 17:00:00", description:"Review week, prep for next week"}
    make new event at studyCal with properties {summary:"Study: Weekly Review & Catch-up", start date:date "Sunday, 1 March 2026 at 14:00:00", end date:date "Sunday, 1 March 2026 at 17:00:00", description:"Review week, prep for next week"}
    make new event at studyCal with properties {summary:"Study: Weekly Review & Catch-up", start date:date "Sunday, 8 March 2026 at 14:00:00", end date:date "Sunday, 8 March 2026 at 17:00:00", description:"Test + deadline prep"}
    make new event at studyCal with properties {summary:"Study: Weekly Review & Catch-up", start date:date "Sunday, 15 March 2026 at 14:00:00", end date:date "Sunday, 15 March 2026 at 17:00:00", description:"Oral exam prep"}
    make new event at studyCal with properties {summary:"Study: Weekly Review & Catch-up", start date:date "Sunday, 22 March 2026 at 14:00:00", end date:date "Sunday, 22 March 2026 at 17:00:00", description:"Paper study + exam prep"}
end tell
EOF

echo "All weekly study events added to calendar '$CALENDAR_NAME'"
