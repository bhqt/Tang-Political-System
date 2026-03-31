#!/bin/bash

# start_server.sh - Start dashboard server and sync loop (background)

REPO_DIR=$(dirname "$(realpath "$0")")
LOG_DIR="$REPO_DIR/logs"
LOG_FILE="$LOG_DIR/dashboard_server.log"
RUN_LOOP_LOG="$LOG_DIR/run_loop.log"
RUN_LOOP_PID="$LOG_DIR/run_loop.pid"

# Create log directory
mkdir -p "$LOG_DIR"

# ==================== Start Dashboard Server ====================

# Check if already running
existing_dashboard=$(ps aux | grep "dashboard/server.py" | grep -v grep)

if [ -n "$existing_dashboard" ]; then
    echo "Dashboard server already running"
    echo "URL: http://127.0.0.1:7891"
else
    echo "Starting dashboard server in background..."
    echo "URL: http://127.0.0.1:7891"
    echo "Log: $LOG_FILE"
    echo ""

    # Start dashboard server in background
    python3 "$REPO_DIR/dashboard/server.py" --port 7891 > "$LOG_FILE" 2> "$LOG_DIR/dashboard_server.error.log" &
    DASHBOARD_PID=$!

    echo "Dashboard server started (PID: $DASHBOARD_PID)"
    
    # Wait and check
    sleep 2
    if ! ps -p $DASHBOARD_PID > /dev/null; then
        echo "Dashboard server failed to start. Check: $LOG_DIR/dashboard_server.error.log"
        exit 1
    fi
fi

echo ""

# ==================== Start Sync Loop ====================

# Check if already running
run_loop_running=false
if [ -f "$RUN_LOOP_PID" ]; then
    old_pid=$(cat "$RUN_LOOP_PID" 2>/dev/null)
    if [ -n "$old_pid" ]; then
        if ps -p $old_pid > /dev/null; then
            run_loop_running=true
            echo "Data refresh loop already running (PID: $old_pid)"
        fi
    fi
fi

if [ "$run_loop_running" = false ]; then
    echo "Starting data refresh loop in background..."
    echo "Log: $RUN_LOOP_LOG"
    echo "Interval: 15s"
    echo ""

    # Start sync loop in background
    bash "$REPO_DIR/scripts/run_loop.sh" 15 > "$RUN_LOOP_LOG" 2>&1 &
    RUN_LOOP_PID=$!

    echo "Data refresh loop started (PID: $RUN_LOOP_PID)"
    
    # Save PID
    echo $RUN_LOOP_PID > "$RUN_LOOP_PID"
    
    sleep 1
fi

echo ""
echo "========================================"
echo "All services started successfully!"
echo "========================================"
echo ""
echo "Dashboard URL: http://127.0.0.1:7891"
echo ""
echo "Commands:"
echo "  View logs:        tail -f $LOG_FILE"
echo "  View sync logs:   tail -f $RUN_LOOP_LOG"
echo "  Stop all:         pkill -f 'dashboard/server.py' && pkill -f 'run_loop.sh'"
echo ""
