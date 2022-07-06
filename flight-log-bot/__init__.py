import os, json


CONFIGFILE = os.path.join(os.environ.get('HOME'), '.config/flight-log-bot/config.json')

with open(CONFIGFILE, 'r') as f:
    CONFIG = json.load(f)
