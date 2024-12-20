import redis
import time
import os
import json
import threading
import logging
from logging.handlers import RotatingFileHandler

# Configure logging with rolling logs
logger = logging.getLogger(__file__)
logging.basicConfig(filename='/opt/nebula/logs/core.log', encoding='utf-8', level=logging.DEBUG)
handler = logging.handlers.RotatingFileHandler(filename='/opt/nebula/logs/core.log', mode='a', maxBytes=8000, backupCount=3, encoding='utf-8')
logger.addHandler(handler)

# Read config.json
config_file = "/opt/nebula/config.json"
with open(config_file) as f:
    config = json.load(f)

# Parse config
redis_config = config.get("redis")
servers = config.get("servers")
file_paths = []
for server in servers:
    try:
        logger.debug(f"Checking for custom log path for {server}...")
        custom_filepath = server.get("logfilepath")
    except:
        logger.debug(f"Critical error, setting log path to None...")
        custom_filepath = None
    if custom_filepath:
        logger.debug(f"Found custom log path for {server}: {custom_filepath}")
        file_paths.append(custom_filepath)
    else:
        logger.debug(f"Applying default log path for {server}: {"/srv/nebula/{server}/logs/latest.log"}")
        file_paths.append(f"/srv/nebula/{server}/logs/latest.log")

# Redis Config    
logger.debug(f"Found logreader configs in config.json: {redis_config, file_paths}")
if redis_config:
    host = redis_config.get("ip", "localhost")
    port = redis_config.get("port", 6379)
else:
    host = "localhost"
    port = 6379
logger.debug(f"Communicating with redis at: {host, port}")

# Connect to Redis
try:
    r = redis.StrictRedis(host=host, port=port, db=0)
    r.ping()
except redis.ConnectionError as e:
    logger.critical(f"Failed to connect to Redis: {e}")
    raise SystemExit("Critical error: Unable to connect to Redis.")

# Redis hash key to store message hashes
seen_messages_key = "seen_messages"

# Message expiration time (in seconds)
message_expiration_time = 3600

# Global stop event
stop_event = threading.Event()

def open_file(file_path):
    if os.path.exists(file_path):
        file = open(file_path, 'r')
        file.seek(0, os.SEEK_END)
        return file
    return None

def compare_word(message, word):
    if word.lower() in message.lower():
        return True
    else:
        return False
    
def get_word_lists_files():
    lists = []
    for file in os.listdir("/etc/nebula/core/logreader/"):
        if file.endswith(".json"):
            lists.append(file)
    return lists

def create_default_word_lists():
    logger.debug(f"Creating default word list...")
    with open("/etc/nebula/core/logreader/default.json", "w+") as file:
        data = {
            "connection_logs": [
                "User Authenticator", "connect"
            ],
            "rcon_logs": [
                "rcon", "Listener"
            ],
            "info_logs": [
                "/info"
            ],
            "warn_logs": [
                "/warn"
            ],
            "error_logs": [
                "/error"
            ]
        }
        json.dump(data, file, indent=4)

def catagorize_message(message):
    set_channels = ["all_logs"]
    words_lists_files = get_word_lists_files()
    if len(words_lists_files) <= 0:
        create_default_word_lists()
        get_word_lists_files()
    for word_lists_file in words_lists_files:
        with open(word_lists_file) as f:
            config = json.load(f)
        for channel, word_list in config:
            for word in word_list:
                if compare_word(message=message, word=word):
                    set_channels.append(channel)
    logger.debug(f"Catagorizing message: {message, set_channels}")
    return set_channels

def publish_message_if_unique(file_path, line):
    message = f"{file_path}: {line.strip()}"
    try:
        # Get channels for message
        channels = catagorize_message(message=line.strip())
        # Use Redis for deduplication with expiration
        if r.setex(name=message, time=message_expiration_time, value=1):
            for channel in channels:
                r.publish(channel, message)
            logger.info(f"Sent message to {channels}: {message}")
        else:
            logger.debug(f"Duplicate message skipped for {channels}: {message}")
    except redis.RedisError as e:
        logger.error(f"Redis error while publishing message to {channels}: {e}")
        stop_event.set()
        raise


def monitor_file(file_path):
    file = open_file(file_path)
    last_position = file.tell() if file else 0
    try:
        while not stop_event.is_set():
            if os.path.exists(file_path):
                if file is None:
                    file = open_file(file_path)
                    last_position = 0
                    logger.info(f"[{file_path}] File recreated. Starting fresh.")

                current_size = os.path.getsize(file_path)
                if current_size < last_position:
                    logger.info(f"[{file_path}] File was truncated. Resetting pointer to beginning.")
                    file.seek(0, os.SEEK_SET)
                    last_position = 0

                if current_size > last_position:
                    file.seek(last_position, os.SEEK_SET)
                    new_content = file.read(current_size - last_position)
                    
                    for line in new_content.splitlines():
                        publish_message_if_unique(file_path, line)

                    last_position = file.tell()

            else:
                logger.warning(f"[{file_path}] File does not exist, waiting...")
                while not os.path.exists(file_path) and not stop_event.is_set():
                    time.sleep(0.1)
                file = open_file(file_path)
                last_position = 0

            time.sleep(0.1)

    except Exception as e:
        logger.error(f"Error in monitoring {file_path}: {e}")
        stop_event.set()
        raise

# Create and start a thread for each file
threads = []
try:
    for file_path in file_paths:
        thread = threading.Thread(target=monitor_file, args=(file_path,), name=f"Monitor-{file_path}")
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

except KeyboardInterrupt:
    logger.warning("Keyboard interrupt received. Stopping...")
    stop_event.set()

except Exception as e:
    logger.critical(f"Unhandled exception in main thread: {e}")
    stop_event.set()

finally:
    # Ensure all threads have stopped
    for thread in threads:
        thread.join()
    logger.info("All threads have stopped. Exiting program.")
