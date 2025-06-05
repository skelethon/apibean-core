from datetime import datetime, timezone
import re

_cached_date = None
_cached_result = None

def format_time_pattern(template: str) -> str:
    global _cached_date, _cached_result

    # Nếu template không chứa {time:...} → không cần xử lý
    if "{time:" not in template:
        return template

    now = datetime.now(timezone.utc)
    today = now.date()

    # Nếu ngày không đổi, dùng cache
    if _cached_date == today and _cached_result is not None:
        return _cached_result

    # Nếu ngày đã thay đổi → xử lý lại
    pattern = re.compile(r"\{time:(.+?)\}")

    def replacer(match):
        fmt = match.group(1)
        fmt = fmt.replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d")
        fmt = fmt.replace("HH", "%H").replace("mm", "%M").replace("ss", "%S")
        return now.strftime(fmt)

    result = pattern.sub(replacer, template)

    # Cập nhật cache
    _cached_date = today
    _cached_result = result

    return result
