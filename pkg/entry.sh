#!/bin/bash

# Echo the CRON schedule for logging/debugging
echo "Installing CRON schedule: $CRON_SCHEDULE"

# Dump the current cron jobs to a temporary file
crontab -l > tempcron

# Remove the existing cron job for your backup script from the file
sed -i '/\/app\/backup.sh/d' tempcron

# Add the new cron job to the file
echo "$CRON_SCHEDULE bash /app/backup.sh" >> tempcron

# Install the new cron jobs
crontab tempcron
rm tempcron

# Start cron and keep container running
/usr/sbin/crond -f -l 8
