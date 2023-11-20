import logging, logging.config
import yaml
import os

path = 'tests/logging.yaml'
if os.path.exists(path):
    with open(path, 'rt') as f:
        config = yaml.safe_load(f.read())
    logging.config.dictConfig(config)
else:
    logging.basicConfig(level=logging.DEBUG)
