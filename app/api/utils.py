from typing import Any, Optional, Union
import croniter
import pytz
import os
from datetime import datetime


def next_cron_occurrences(
    occurrences: Optional[int] = 5, now: Optional[datetime] = None
) -> Optional[dict[str | int, Any]]:
    cron_enabled = os.getenv("CRON_SCHEDULE_ENABLED", "true").lower()
    if cron_enabled == "false":
        return None

    cron_expression = os.getenv("CRON_SCHEDULE", "0 4 * * *")
    timezone = os.getenv("TZ", "Etc/UTC")
    tz = pytz.timezone(timezone)

    if now == None:
        now = datetime.now(tz)

    # Create a cron iterator with the timezone
    cron = croniter.croniter(cron_expression, start_time=now)

    response: dict[Union[str, int], Any] = {
        "cron": f"{cron_expression}",
        "tz": f"{tz}",
    }

    if occurrences == None or occurrences <= 0:
        occurrences = 1
    elif occurrences >= 100:
        occurrences = 100

    for i in range(occurrences):
        next_occurrence: datetime = cron.get_next(datetime)
        response[str(i + 1)] = [
            next_occurrence.strftime("%A, %B %d, %Y at %I:%M %p"),
            next_occurrence.strftime("%m/%d/%y %H:%M"),
        ]

    return response
