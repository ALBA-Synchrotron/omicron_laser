# -*- coding: utf-8 -*-
#
# This file is part of the Omicron Laser project
#
# Copyright (c) 2021 Alberto López Sánchez
# Distributed under the GNU General Public License v3. See LICENSE for more info.

"""Tango server module for Omicron Laser."""

from .omicron_laser import Omicron_laser


def main():
    import sys
    import logging
    import tango.server
    args = ['Omicron_laser'] + sys.argv[1:]
    fmt = '%(asctime)s %(threadName)s %(levelname)s %(name)s %(message)s'
    logging.basicConfig(level=logging.INFO, format=fmt)
    tango.server.run((Omicron_laser,), args=args, green_mode=tango.GreenMode.Asyncio)
