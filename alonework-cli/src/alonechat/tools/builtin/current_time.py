from datetime import datetime, timezone
from typing import Any

from alonechat.core.base_tool import BaseTool


class CurrentTimeTool(BaseTool):
    name = "current_time"
    description = "Get the current date and time. Returns ISO 8601 formatted string. Optionally specify a timezone offset in hours."
    parameters = {
        "type": "object",
        "properties": {
            "timezone_offset_hours": {
                "type": "number",
                "description": "Timezone offset from UTC in hours (e.g. 8 for UTC+8, -5 for UTC-5). Default is 0 (UTC).",
                "default": 0,
            },
            "format": {
                "type": "string",
                "description": "Output format: 'iso', 'human'. Default is 'iso'.",
                "default": "iso",
            },
        },
        "required": [],
    }

    def execute(self, timezone_offset_hours: float = 0, format: str = "iso") -> str:
        tz = timezone.utc if timezone_offset_hours == 0 else timezone(
            offset=__import__("datetime").timedelta(hours=timezone_offset_hours)
        )
        now = datetime.now(tz)
        if format == "human":
            return now.strftime("%Y-%m-%d %H:%M:%S %Z")
        return now.isoformat()
