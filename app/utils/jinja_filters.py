from datetime import datetime

def datetimeformat(value, format="%m/%d/%y"):
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value) if isinstance(value, str) else value
        return dt.strftime(format)
    except Exception:
        return value
