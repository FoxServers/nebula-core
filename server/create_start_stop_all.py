import logging
import logging.handlers
import json

logger = logging.getLogger(__file__)
logging.basicConfig(filename='/opt/nebula/logs/core.log', encoding='utf-8', level=logging.DEBUG)
handler = logging.handlers.RotatingFileHandler(filename='/opt/nebula/logs/core.log', mode='a', maxBytes=8000, backupCount=3, encoding='utf-8')
logger.addHandler(handler)

try:
    # Load the JSON data
    try:
        with open('/opt/nebula/config.json', 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}

    # Error handling
    if 'servers' not in data:
        data['servers'] = {}
    
    # Extract server names
    server_names = list(data.get('servers', {}).keys())
        
    with open('/opt/nebula/core/scripts/start_all', 'w') as f:
        f.write(f"#!/bin/sh\n")
        f.write(f'echo "[Nebula] Starting all servers..."\n')
        for server in server_names:
            if 'core' in data['servers'][server] and data['servers'][server]['core'] == True:
                f.write(f'echo "    Starting {server}..."\n')
                f.write(f"/usr/bin/bash /opt/nebula/core/scripts/start '{server}'\n")
        f.write(f'echo "[Nebula] Done!"\n')
    
    with open('/opt/nebula/core/scripts/stop_all', 'w') as f:
        f.write(f"#!/bin/sh\n")
        f.write(f'echo "[Nebula] Stopping all servers..."\n')
        for server in server_names:
            if 'core' in data['servers'][server] and data['servers'][server]['core'] == True:
                f.write(f'echo "    Stopping {server}..."\n')
                f.write(f"/usr/bin/bash /opt/nebula/core/scripts/stop '{server}'\n")
        f.write(f'echo "[Nebula] Done!"\n')

    logger.info(f"[Nebula] start_all and stop_all scripts created successfully!")

except Exception as e:
    logger.error(f"[Nebula] A critical error has occurred: {e}")