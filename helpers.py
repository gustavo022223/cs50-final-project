
from cs50 import SQL
from flask import redirect, render_template, session
from functools import wraps
from datetime import datetime

db = SQL("sqlite:///hospital.db")

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

# Format date and time from database
def format_date_and_time(date_str):
    # If there's date and time values and it's not "Unavailable"
    if date_str and date_str != "Unavailable":
        # Try to format date and time if both are present
        try:
            # Format data from database into datetime format
            date_object = datetime.strptime(date_str, "%Y-%m-%dT%H:%M")
            # Format date into "Month Day, Year"
            formatted_date = date_object.strftime("%B %d, %Y")
            # Format time into "Hour:Minutes"
            formatted_time = date_object.strftime("%H:%M")
            # Return formated date and time string
            return f"{formatted_date} ({formatted_time})"
        except ValueError:
            # If only date value is available
            try:
                # Format date into "Month Day, Year"
                date_object = datetime.strptime(date_str, "%Y-%m-%d")
                formatted_date = date_object.strftime("%B %d, %Y")
                # Return formated date string
                return f"{formatted_date}"
            # If data is not in the expected format, return error
            except ValueError:
                return "Invalid Date"
    # If there's no date and time data, return "Unavailable"
    else:
        return "Unavailable"
    
