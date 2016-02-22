
from pymongo import MongoClient

from user_pull_requests.settings import MONGO_URI, MONGO_DATABASE

# move these to constants
con = MongoClient(MONGO_URI)
db = con[MONGO_DATABASE]
collection = 'user_pull_requests'

def get_pr_count(handles):
    """Returns a dictionary of the format:
    {
        handle: {closed: <int>, open: <int>}
    }
    @handle: An iterable of user handles to perform aggregation with.
    """
    result = {}
    for handle in handles:
        projects = []
        open_query = {'handle': handle, 'pr_state': 'open'}
        cur = db[collection].find(open_query)
        open_count = cur.count()

        closed_query = {'handle': handle, 'pr_state': 'closed'}
        cur = db[collection].find(closed_query)
        closed_count = cur.count()
        result[handle] = {'open': open_count, 'closed': closed_count}
    return result

