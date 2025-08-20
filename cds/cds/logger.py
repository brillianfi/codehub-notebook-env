import logging.config
import os
from pathlib import Path

import yaml


def setup_logging():
    os.makedirs("/home/jovyan/logs", exist_ok=True)
    with open(os.path.join(Path(__file__).parent, "logger.yaml"), "r") as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
