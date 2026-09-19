#!/bin/bash

LOG_FILE=$1

bot_file_name="main.py"

dir=$(cd "$(dirname "$0")" && pwd)

# Match only the interpreter process itself: the pattern is anchored to the start
# of the command line, so shells or editors that merely mention the path are skipped.
find_pids() {
    pgrep -f "^python3 -u $dir/$bot_file_name"
}

stop_service() {
    pid=$(find_pids)

    if [ -n "$pid" ]; then
        # shellcheck disable=SC2086
        kill $pid
        sleep 1
        pid=$(find_pids)
        if [ -n "$pid" ]; then
            # shellcheck disable=SC2086
            kill -9 $pid
            echo "Service killed"
        else
            echo "Service stopped"
        fi
    else
        echo "Service not found"
    fi
}

if [ -n "$LOG_FILE" ]; then
    touch "$LOG_FILE"
    if [ ! -f "$LOG_FILE" ]; then
        echo "File $LOG_FILE does not exist"
    fi
fi

if [ -z "$LOG_FILE" ] || [ ! -f "$LOG_FILE" ]; then
    stop_service
else
    stop_service 2>&1 | tee -a "$LOG_FILE"
fi
