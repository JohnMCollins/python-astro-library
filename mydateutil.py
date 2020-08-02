# Miscalleanous date routines


def sametime(date1, date2):
    """Check if the times and dates are the same where one may have fractions of a second"""

    return  abs((date1 - date2).total_seconds()) < 1


def mysql_datetime(date1):
    """Return date and time suitable for use in a mysql query"""
    return  date1.strftime("%Y-%m-%d %H:%M:%S")
