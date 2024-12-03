import logging
import logging.handlers
import sys
import json

logger = logging.getLogger(__file__)
logging.basicConfig(filename='/opt/foxservers/core/logs/core.log', encoding='utf-8', level=logging.DEBUG)
handler = logging.handlers.RotatingFileHandler(filename='/opt/foxservers/core/logs/core.log', mode='a', maxBytes=8000, backupCount=3, encoding='utf-8')
logger.addHandler(handler)

if (sys.argv[1] == None):
    logger.error(f"[Server Manager] Failed to remove server: Missing server name")
    ValueError("[Server Manager] Failed to remove server: Missing server name")

try:
    with open('/opt/foxservers/core/servers.json', 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []

    data_no_duplicates = []
    for i in data:
        if i not in data_no_duplicates:
            if i['server_name'] == sys.argv[1]:
                continue
            else:
                data_no_duplicates.append(i)
    with open('/opt/foxservers/core/servers.json', 'w') as f:
        json.dump(data_no_duplicates, f, indent=1)


except:
    logger.error(f"[Server Manager] Failed to remove server: Could not find servers.json")