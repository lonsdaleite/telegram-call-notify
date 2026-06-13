#!/bin/bash

LOG_FILE=$1

bot_file_name="main.py"

dir=$(dirname "$0")

stop_service() {
    pid=$(ps aux | grep "$dir/$bot_file_name" | grep -vw grep | awk '{print $2}')

    if [ -n "$pid" ]; then
        kill "$pid"
        sleep 1
        pid=$(ps aux | grep "$dir/$bot_file_name" | grep -vw grep | awk '{print $2}')
        if [ -n "$pid" ]; then
            kill -9 "$pid"
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
