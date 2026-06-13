#!/bin/bash

LOG_FILE=$1

bot_file_name="main.py"

dir=$(dirname "$0")
"$dir/stop.sh" "$LOG_FILE"

if [ -n "$LOG_FILE" ]; then
    touch "$LOG_FILE"
    if [ ! -f "$LOG_FILE" ]; then
        echo "File $LOG_FILE does not exist"
    fi
fi

check_network() {
    inc=0
    until nc -z api.telegram.org 443; do
        echo "api.telegram.org:443 unavailable. Waiting..."
        inc=$(($inc + 1))
        if [ $inc -gt 120 ]; then
            echo "ERROR: api.telegram.org:443 unavailable"
        fi
        sleep 5
    done
}

activate_venv() {
    if [ -f "$dir/.venv/bin/activate" ]; then
        # shellcheck disable=SC1091
        source "$dir/.venv/bin/activate"
    elif [ -f "$dir/venv/bin/activate" ]; then
        # shellcheck disable=SC1091
        source "$dir/venv/bin/activate"
    fi
}

if [ -z "$LOG_FILE" ] || [ ! -f "$LOG_FILE" ]; then
    check_network
    echo "Service started"
    pushd "$dir" >/dev/null || exit 1
    activate_venv
    python3 -u "$dir/$bot_file_name"
    popd >/dev/null || exit 1
else
    check_network 2>&1 | tee -a "$LOG_FILE"
    pushd "$dir" >/dev/null || exit 1
    activate_venv
    nohup python3 -u "$dir/$bot_file_name" >>"$LOG_FILE" 2>&1 &
    popd >/dev/null || exit 1
    echo "Service started" | tee -a "$LOG_FILE"
fi
