#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Лаунчер для правильного запуску програми"""

import sys
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_dir)

from ventilation_company.gui import main

if __name__ == "__main__":
    main()
