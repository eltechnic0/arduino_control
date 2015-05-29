import time
import modules.serial_controller as sc

ard = None

def main():
  global ard
  ard = sc.Arduino('COM3')
  ard.connect()

def cycle_pulses(pulse_duration, delay):
  # global ard
  while True:
    ard._sw_control('pulse_a', pulse_duration)
    time.sleep(delay)
    ard._sw_control('pulse_b', pulse_duration)
    time.sleep(delay)

def release_charge():
  # global ard
  ard._sw_control('v+')
  ard._sw_control('0')
  ard._sw_control('z')
