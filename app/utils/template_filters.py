from datetime import datetime

def format_date(date_string):
    """Format a date string in a human-readable format"""
    if not date_string:
        return ""
    
    try:
        date_obj = datetime.fromisoformat(date_string)
        return date_obj.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return date_string
