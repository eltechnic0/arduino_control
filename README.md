# arduino_control

This is a very specific application designed to control an EWOD experiment using an Arduino from a web interface.

## Dependencies

The app works under Ubuntu 15.04 and Windows 8 (older versions probably too). The following packages must be present in the python installation to make it work:

- pyserial
- pyfirmata
- cherrypy
- mako
- numpy
- scipy
- scikit-image
- matplotlib

Additionally, the camera addon uses the program CommandCam.exe, developed by Ted Burke and available at [github](https://github.com/tedburke/CommandCam). For convenience however, the executable is included in the camera addon folder of the repository.

## Running

On Windows, where the Arduino is usually on the `COM3` port:

`python app.py`

On Ubuntu, running with privileges is necessary to be able to connect to the serial device. On my machine, the Arduino is on `/dev/ttyACM0`:

`sudo python3 app.py`

For more options add the `--help` argument, e.g. `python3 app.py --help`.

## Custom scripts

### Writing a custom script

Custom scripts are subclasses of the `Script` class from the `app_script`
module. They must implement the `run` function at least, and they should use the
convenience method `serial_write` to send commands to the Arduino. They must be
stored in the scripts folder. For an example, see `script_test.py`.

### Running a script

To run a script either use the web interface or make a request to
`/serialScript` with the name of the script and the kwargs as json payload. For
example:

```python
requests.post('http://localhost:8080/serialScript',
  data={'fname':'script_test','string':'Hello world!'})
```

## Addons

These provide more flexibility than a script at the cost of more writing. They are basically composed of a python module that is attached to the server, and an html ui with its js scripts and other resources. The folder structure to use is similar to the camera addon, so check that one for reference.

### Available commands

The following commands can be sent to the Arduino using the aforementioned
convenience method. Use this list as a reference of the parameters for each
command. For more information on the method's signature, see the docstrings.

- `vset [pins:(3,9,10,11)] [values:(0-255)] settling:(0:inf)`

- `vread [pins:(0,1,2,3,4,5)]`

## Console mode

Sometimes the web interface might not be very convenient, especially when experimenting with new things. In these cases, the `serial_controller` file in the modules folder is still very easy to use and effective in controlling the Arduino manually.
