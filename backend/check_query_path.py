import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.queries import get_all_users, DEFAULT_DB, PREFERRED_DB_PATH

print('DEFAULT_DB=', DEFAULT_DB)
print('PREFERRED_DB_PATH exists=', os.path.exists(PREFERRED_DB_PATH))
print('DATA db exists=', os.path.exists(os.path.join(os.path.dirname(__file__), '..', 'data', 'club-stats.db')))
print('count=', len(get_all_users()))
