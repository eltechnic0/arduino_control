import time
import modules.serial_controller as sc

ard = None

def main():
  # Create object and connect to the Arduino board
  ard = sc.Arduino('COM3')
  ard.connect()
  return ard

def cycle_pulses(pulse_duration, delay):
  # Alternate the direction of the current through the two outputs
  try:
    while True:
      ard._sw_control('pulse_a', pulse_duration)
      time.sleep(delay)
      ard._sw_control('pulse_b', pulse_duration)
      time.sleep(delay)
  except KeyboardInterrupt:
    ard._sw_control('z')
    print('Back to HI-Z')

def release_charge():
  # Set these states for a short duration, to check if they help in freeing the
  # droplet after it stops moving
  ard._sw_control('v+')
  time.sleep(0.5)
  ard._sw_control('0')
  time.sleep(0.5)
  ard._sw_control('z')

if __name__ == '__main__':
  ard = main()
