# -*- coding: utf-8 -*-
#
# This file is part of the Omicron Laser project
#
# Copyright (c) 2021 Alberto López Sánchez
# Distributed under the GNU General Public License v3. See LICENSE for more info.

"""
.. code-block:: yaml

    devices:
    - class: Omicron_laser
      package: omicron_laser.simulator
      transports:
      - type: tcp
        url: :5000

A simple *nc* client can be used to connect to the instrument:

    $ nc 0 5000
    *IDN?
    GE,Pace5000,204683,1.01A
"""

from sinstruments.simulator import BaseDevice


class Omicron_laser(BaseDevice):

    def handle_message(self, line):
        pass
