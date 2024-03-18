#!/usr/bin/env python3
from pyspectator.processor import Cpu
from time import sleep

while True:
    cpu = Cpu(monitoring_latency=1)
    print(cpu.temperature)
    sleep(1)