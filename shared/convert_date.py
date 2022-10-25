import datetime


def parse_date(date_str):
    try:
        date = datetime.datetime.strptime(date_str, "%d %b %Y").strftime("%Y-%m-%d")
    except ValueError:
        return date_str
    return date


def parse_american_date(date_str):
    try:
        year_len = len(date_str.split('/')[-1]) 
        if year_len == 2:
            date = datetime.datetime.strptime(date_str, "%m/%d/%y").strftime("%Y-%m-%d")
        else:
            date = datetime.datetime.strptime(date_str, "%m/%d/%Y").strftime("%Y-%m-%d")
        return date
    except ValueError:
        return date_str
