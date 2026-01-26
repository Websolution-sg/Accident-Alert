#!/bin/bash

SERVICE_NAME="waze-accident-monitor"
LOG_FILE="/home/USER/health_monitor.log"
MAX_LOG_LINES=100

# Function to log with timestamp
log_message() {
    echo "$(date): $1" >> "$LOG_FILE"
}

# Check if service is active
if ! systemctl is-active --quiet "$SERVICE_NAME"; then
    log_message "CRITICAL: $SERVICE_NAME is not active - attempting restart"
    sudo systemctl restart "$SERVICE_NAME"
    sleep 5
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_message "SUCCESS: $SERVICE_NAME restarted successfully"
    else
        log_message "ERROR: Failed to restart $SERVICE_NAME"
    fi
else
    log_message "OK: $SERVICE_NAME is running normally"
fi

# Check for recent errors in service logs
ERROR_COUNT=$(sudo journalctl -u "$SERVICE_NAME" --since="5 minutes ago" --grep="ERROR\|Exception\|Failed" | wc -l)
if [ "$ERROR_COUNT" -gt 0 ]; then
    log_message "WARNING: Found $ERROR_COUNT errors in service logs (last 5 minutes)"
fi

# Keep log file manageable
if [ -f "$LOG_FILE" ]; then
    tail -n $MAX_LOG_LINES "$LOG_FILE" > "${LOG_FILE}.tmp"
    mv "${LOG_FILE}.tmp" "$LOG_FILE"
fi