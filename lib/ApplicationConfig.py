#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from happy_python import HappyConfigBase


class ApplicationConfig(HappyConfigBase):
    def __init__(self):
        super().__init__()

        self.section = 'main'

        self.access_key_id = ''
        self.access_key_secret = ''
        self.region_id = ''
        self.platform_type = ''