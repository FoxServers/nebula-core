import logging
import logging.handlers
import sys
import json

logger = logging.getLogger(__file__)
logging.basicConfig(filename='/opt/nebula/logs/core.log', encoding='utf-8', level=logging.DEBUG)
handler = logging.handlers.RotatingFileHandler(filename='/opt/nebula/logs/core.log', mode='a', maxBytes=8000, backupCount=3, encoding='utf-8')
formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)

if (len(sys.argv) < 2):
    logger.error(f"[Server Manager] Failed to remove server: Missing server name")
    raise ValueError("[Server Manager] Failed to remove server: Missing server name")


def save_data(data):
    # Save the changes
    with open('/opt/nebula/config.json', 'w') as file:
        json.dump(data, file, indent=4)

def remove_server(server_name, data, logger):
    del data['servers'][server_name]
    logger.info(f"[Server Manager] Removed all data from {server_name}")
    save_data(data)

def update_server(server_name, data, logger):
    data['servers'][server_name]['core'] = False
    logger.info(f"[Server Manager] Updated {server_name} core to False")
    save_data(data)

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

    server_names = list(data['servers'].keys())
    if sys.argv[1] in server_names:
        if (len(sys.argv) > 2 and sys.argv[2] == "--delete"):
            remove_server(server_name=sys.argv[1], data=data, logger=logger)
        else:
            update_server(server_name=sys.argv[1], data=data, logger=logger)
    else:
        logger.error(f"[Server Manager] Server {sys.argv[1]} not found in data.")
        raise ValueError(f"Server {sys.argv[1]} not found in the configuration.")

except Exception as e:
    logger.error(f"[Server Manager] A critical error has occurred: {e}")