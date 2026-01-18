#!/bin/bash
# Add alerts to all deadline/exam events in Study Schedule calendar
# Run this after adding new deadlines

osascript <<'EOF'
tell application "Calendar"
    set studyCal to calendar "Study Schedule"
    set today to current date
    set endDate to today + (90 * days)

    set allEvents to (every event of studyCal whose start date ≥ today and start date ≤ endDate)
    set updatedCount to 0

    repeat with evt in allEvents
        set evtName to summary of evt
        if evtName contains "DEADLINE" or evtName contains "EXAM" or evtName contains "TEST" then
            tell evt
                -- Remove existing alarms first to avoid duplicates
                delete every sound alarm
                -- Add new alerts
                make new sound alarm with properties {trigger interval:-1440} -- 1 day before
                make new sound alarm with properties {trigger interval:-120} -- 2 hours before
                make new sound alarm with properties {trigger interval:-30} -- 30 mins before
            end tell
            set updatedCount to updatedCount + 1
        end if
    end repeat

    return "Added alerts to " & updatedCount & " events"
end tell
EOF

echo "Alerts updated for deadline events"
