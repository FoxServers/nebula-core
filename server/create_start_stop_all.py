import logging
import logging.handlers
import json

logger = logging.getLogger(__file__)
logging.basicConfig(filename='/opt/foxservers/core/logs/core.log', encoding='utf-8', level=logging.DEBUG)
handler = logging.handlers.RotatingFileHandler(filename='/opt/foxservers/core/logs/core.log', mode='a', maxBytes=8000, backupCount=3, encoding='utf-8')
logger.addHandler(handler)

try:
    with open('/opt/foxservers/core/servers.json', 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []
    data_no_duplicates = []
    for i in data:
        if i not in data_no_duplicates:
            data_no_duplicates.append(i)
        
    with open('/opt/foxservers/core/scripts/foxservers.servers.start_all.sh', 'w') as f:
        f.write(f"#!/bin/sh\n")
        f.write(f'echo "[FoxServers] Starting all servers..."\n')
        for server in data_no_duplicates:
            f.write(f'echo "    Starting {server['server_name']}..."\n')
            f.write(f"/usr/bin/bash /opt/foxservers/core/scripts/foxservers.server.start.sh {server['server_name']}\n")
        f.write(f'echo "[FoxServers] Done!"\n')
    
    with open('/opt/foxservers/core/scripts/foxservers.servers.stop_all.sh', 'w') as f:
        f.write(f"#!/bin/sh\n")
        f.write(f'echo "[FoxServers] Stopping all servers..."\n')
        for server in data_no_duplicates:
            f.write(f'echo "    Stopping {server['server_name']}..."\n')
            f.write(f"/usr/bin/bash /opt/foxservers/core/scripts/foxservers.server.stop.sh {server['server_name']}\n")
        f.write(f'echo "[FoxServers] Done!"\n')

except:
    logger.error(f"[Core] Failed to create start and stop scripts: Could not find servers.json")