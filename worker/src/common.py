import logging
import os
import sys
import yaml

# Load logging config from logging.yaml
def setup_logging(default_path='./conf/logging.yaml',
                  default_level=logging.DEBUG,
                  env_key='LOG_CFG'):
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.safe_load(f)
        logging.config.dictConfig(config)
        logging.info("Configured logging from yaml")
    else:
        logging.basicConfig(level=default_level)
        logging.info("Configured logging basic")


# Load config from yaml file
def load_config(path='./conf/all.yaml'):
    config = None
    log = logging.getLogger(__name__)
    if os.path.exists(path):
        log.debug("Loading config from: " + str(path))
        with open(path, 'r') as y:
            config = yaml.safe_load(y)
    else:
        log.error("Config file not found: " + path)
        sys.exit()
    return config