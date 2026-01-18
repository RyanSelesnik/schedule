#!/bin/bash
# Script to create the Study Schedule calendar
# Usage: ./create_calendar.sh

osascript -e 'tell application "Calendar" to make new calendar with properties {name:"Study Schedule"}'
echo "Calendar 'Study Schedule' created"
