/*
** Arduino program to control a laser steering experiment of a liquid lens
**
** Author: German Gambon Bru
** Date: 02 April 2015
** Version: 1.0
*/

/* Command descriptions:
** INVALID: unknown command received
** SETTLING pin time len: settling time experiment with settling time 'time' and
**    number of points len. Result read in A0
** VSET pin value settling: set voltage of output 'pin' [3,9,10,11] to 'value'
**    0..255 and wait 'settling' time
** VREAD pin: read voltage at analog 'pin'
** COMTEST: returns OKREADY_INFO. Use it to test communication
** VERBOSE_FLAG: returns OKREADY_INFO. Set verbose mode flag to 1 or 0
*/
typedef enum CMD {INVALID, SETTLING, VSET, VREAD, COMTEST, VERBOSE_FLAG};

const int STREAMBYTES = 24;
const int MAXPARAMS = 3;

// strings stored in flash memory
const char SETTLING_INFO[] PROGMEM = "Expecting 3 parameters: pin{3,9,10,11}, settling{int[ms]}, points{int}";
const char VSET_INFO[] PROGMEM = "Expecting 3 parameters: pin{3,9,10,11}, voltage{0..255}, settling{int[ms]}";
const char VREAD_INFO[] PROGMEM = "Expecting 1 parameter: pin{0..5}";
const char VERBOSE_INFO[] PROGMEM = "Expecting 1 parameter: flag{0,1}";
const char OKREADY_INFO[] PROGMEM = "OK:ready";
const char OKSTART_INFO[] PROGMEM = "OK:start";
// const char OKEND_INFO[] PROGMEM = "OK:end";

struct {
  CMD cmd;
  int params[MAXPARAMS];
  int numparams;
} task;

bool verbose_flag = 1;


/*
** Functions start here
*/
void setup() {
  // these are the ports that run PWM at 490Hz by default
  pinMode(3, OUTPUT);
  pinMode(9, OUTPUT);
  pinMode(10, OUTPUT);
  pinMode(11, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  while (true) {

    catchMessages();

    delay(10); // idle delay
  }
}

/*
** Add here functions for new commands
*/
void readVoltage() {
  int pin = task.params[0];

  float value = analogRead(constrain(pin, 0, 5)) * (5.0 / 1023.0);

  Serial.println(value);
}

void setVoltage() {
  int pin = task.params[0];
  int value = task.params[1];
  int settling = task.params[2];

  analogWrite(pin, constrain(value, 0, 255));

  delay(settling);
}

void settlingExperiment() {
  float val;
  unsigned char duty;
  int pin = task.params[0];
  int settling = task.params[1];
  int points = task.params[2];

  for (int i = 0; i < points; i++) {

    duty = (char)( i * 255.0 / (points - 1) );

    analogWrite(pin, duty);

    delay(settling); // experiment step delay

    val = analogRead(A0) * (5.0 / 1023.0);
    Serial.println(duty);
    Serial.println(val);
  }
}

/*
** Function managing the serial port
*/
void catchMessages() {
  if (Serial.available() > 0) {

    // initialize data buffer
    char serialData[STREAMBYTES+1];
    for (int i = 0; i < STREAMBYTES; i++) {
      serialData[i] = ' ';
    }

    // read message
    Serial.readBytesUntil('\n', serialData, STREAMBYTES);
    // make sure it is a valid C string. Otherwise, println(str) may give
    // unexpected results due to accessing memory beyond serialData limits
    serialData[STREAMBYTES] = '\0';
    String str = String(serialData);
    str.toLowerCase();

    // acknowledge reception
    if (verbose_flag == 1) {
      Serial.println(F("Received command:"));
      /*Serial.write(serialData, STREAMBYTES);
      Serial.println();*/
      str.trim();
      Serial.println(str);
    }

    // select requested task
    if (str.startsWith(F("settling"))) {
      task.numparams = 3;
      task.cmd = SETTLING;
    }
    else if (str.startsWith(F("vset"))){
      task.numparams = 3;
      task.cmd = VSET;
    }
    else if (str.startsWith(F("vread"))) {
      task.numparams = 1;
      task.cmd = VREAD;
    }
    else if (str.startsWith(F("comtest"))) {
      // special unique handshaking command
      task.numparams = 0;
      task.cmd = COMTEST;
    }
    else if (str.startsWith(F("verbose"))) {
      task.numparams = 1;
      task.cmd = VERBOSE_FLAG;
    }
    else {
      // only option to return false here
      task.cmd = INVALID;
      Serial.println(F("Error: unknown command"));
      return;
    }

    // print parameter information if verbose mode is on
    if (verbose_flag == 1) {
      switch (task.cmd)
      {
        case SETTLING:
          serialPGMPrintln(SETTLING_INFO);
          break;
        case VSET:
          serialPGMPrintln(VSET_INFO);
          break;
        case VREAD:
          serialPGMPrintln(VREAD_INFO);
          break;
        case VERBOSE_FLAG:
          serialPGMPrintln(VERBOSE_INFO);
        default:
          break;
      }
    }

    // extract parameters if any
    bool ok = getParams(task.params, task.numparams, 10000);
    if (!ok) {
      return;
    }

    // run the task and send data stream start headers if appropriate
    switch (task.cmd)
    {
      case SETTLING:
        serialPGMPrintln(OKSTART_INFO);
        settlingExperiment();
        break;
      case VSET:
        setVoltage();
        break;
      case VREAD:
        serialPGMPrintln(OKSTART_INFO);
        readVoltage();
        break;
      case COMTEST:
        break;
      case VERBOSE_FLAG:
        verbose_flag = task.params[0] > 0 ? true : false;
        break;
      default:
        break;
    }

    // task successfully run. Send info terminators
    serialPGMPrintln(OKREADY_INFO);

  }
}

/*
This function returns true if the parameter scanning is successful. In any case
the messages sent through the serial port however, can be positive or negative,
depending on whether the function fails due to user cancelation or to timeout
expiration.
*/
bool getParams(int *params, int paramNumber, int timeout) {
  // timeout in miliseconds
  char serialData[STREAMBYTES+1];
  unsigned long before;
  int i = 0;

  before = millis();

  while (i < paramNumber) {
    if (Serial.available() > 0) {
      // init the array to avoid possible confusion on atoi()
      for (int k = 0; k < STREAMBYTES; k++) {
        serialData[k] = ' ';
      }

      Serial.readBytesUntil('\n', serialData, STREAMBYTES);
      // make sure it is a valid C string. Otherwise, atoi(serialData) may give
      // unexpected results due to accessing memory beyond serialData limits
      serialData[STREAMBYTES] = '\0';

      // cancelable parameter input sequence
      if (strncmp(serialData, "cancel", 6) == 0) {
        if (verbose_flag == 1) {
          Serial.println(F("Command canceled"));
        }
        serialPGMPrintln(OKREADY_INFO);
        return false;
      }

      // char[] to integer conversion
      params[i] = atoi(serialData);
      i++;

      if (verbose_flag == 1) {
        Serial.println(F("Received parameter:"));
        Serial.println(params[i-1]);
      }

      before = millis();
    }

    if (millis() - before > timeout) {
      Serial.println(F("Error: timeout expired"));
      return false;
    }

    delay(1);
  }
  return true;
}

// serial print strings stored in program memory (flash)
void serialPGMPrintln(const char *pgmstring) {
  char c;
  while((c = pgm_read_byte_near(pgmstring++))) Serial.write(c);
  Serial.println();
}
