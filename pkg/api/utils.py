from typing import Optional
import croniter
import pytz
import os
from datetime import datetime

def next_cron_occurrences(occurrences: Optional[int] = 5):
    cron_expression = os.getenv("CRON_SCHEDULE", "0 4 * * *")
    timezone = os.getenv("TZ", "Etc/UTC")
    tz = pytz.timezone(timezone)
    
    # Create a cron iterator with the timezone
    cron = croniter.croniter(cron_expression, datetime.now(tz), tz)
    
    response = {
        "cron": f"{cron_expression}",
        "tz": f"{tz}",
    }
    
    if occurrences == None or occurrences <= 0: 
        occurrences = 1
        
    for i in range(occurrences):
        next_occurrence = cron.get_next(datetime)
        response[i+1] = [next_occurrence.strftime('%A, %B %d, %Y at %I:%M %p'), next_occurrence.strftime('%m/%d/%y %H:%M')]
    
    return response