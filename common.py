#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import PurePath

from happy_python import HappyConfigParser
from happy_python import HappyLog

from lib.ApplicationConfig import ApplicationConfig

CONFIG_DIR = PurePath(__file__).parent / 'resource'
CONFIG_FILENAME = str(CONFIG_DIR / 'application.ini')
LOG_CONFIG_FILENAME = str(CONFIG_DIR / 'log.ini')

config = ApplicationConfig()
HappyConfigParser.load(CONFIG_FILENAME, config)

hlog = HappyLog.get_instance(LOG_CONFIG_FILENAME)
