# TODO list

- DONE: Suppress extra output for batch sends. It looks ugly to see many 'OK:ready' in a row

- Prettify communication history visualization

- Useful data logging of the session. Possibly useful using some of the bus channels or class proxies to receive event information

- Improve error and general info logging

- Save session log to a file specially for tracking errors, since the web interface should better minimize the error info

- Write some usual initialization scripts, or find a better way to solve so

- DONE: Use flash messages instead of the current comm history

- Auto find Arduino port. Print the tty list before and after connecting it and pick the new device

- Implement the periodic vread as seen in the web interface

- DONE: Change the p-list comm history implementation with p tags to ul/li, which is semantically more appropriate

- Develop a coherent script data storage and/or manipulation

- DONE: Provide better workflow for adding custom addons similar to cam_calibration

  - Check if cherrypy objects for routing can be added and removed at runtime

  - Find a way to be able to load an indefinite number of such addons, that might be located inside some folder

### DONE: cam_calibration dialog

- Find a better way to activate the dialog

- Better error info display

- Ability to specify or list camera devices to take a screenshot from

- Remove picture after uploading it?

- Block backgound clicking or open up in another tab
