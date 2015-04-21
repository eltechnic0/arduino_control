# arduino_control

Application to control an Arduino from a web interface

## Running

Running with privileges is necessary to be able to connect to the serial device.

`sudo python3 app.py --serialport '/dev/ttyACM0'`

For more options type `python3 app.py --help`.

## Custom scripts

### Writing a custom script

Custom scripts are subclasses of the `Script` class from the `app_script`
module. They must implement the `run` function at least, and they should use the
convenience method `serial_write` to send commands to the Arduino. They must be
stored in the scripts folder. For an example, see `script_test.py`.

### Running a script

To run a script either use the web interface (not implemented yet) or make a
request to `/serialScript` with the name of the script and the kwargs as json
payload. For example:

```python
requests.post('http://localhost:8080/serialScript',
  data={'fname':'script_test','string':'Hello world!'})
```

### Available commands

- `vset [pins:(3,9,10,11)] [values:(0-255)] settling:(0:inf)`

- `vread [pins:(0,1,2,3,4,5)]`

- `verbose [flag:(0,1)]`

- `comtest`
