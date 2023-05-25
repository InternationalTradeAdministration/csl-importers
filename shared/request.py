import os
import urllib.request

DEFAULT_USER_AGENT = os.environ['DEFAULT_USER_AGENT']

def urlopen_with_user_agent(url, user_agent=DEFAULT_USER_AGENT):
    req = urllib.request.Request(url,
                                 data=None,
                                 headers={'User-Agent': user_agent})
    return urllib.request.urlopen(req)
