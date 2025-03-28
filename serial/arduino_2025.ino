#include <Wire.h>

/*
  Ultrasonic sensor
  Address / Commands for SRFxx-like or similar I2C ultrasonic sensors
*/
#define SENSOR_ADDRESS      0x70
#define CMD_IN_CM           0x51
#define CMD_IN_US           0x52
#define RESULT_REGISTER     0x02

/*
  Other sensors
*/
#define PIN_SPEED_SENSOR    A7    // Adjust if needed for attachInterrupt
#define PIN_BATTERY_SENSOR  A3

/*
  Globals used for data
*/
volatile float pulsesPerSecond = 0.0; // We will measure interrupts as pulses/second.
int rearDistance               = 0;   // in centimeters (from ultrasonic)
float batteryVoltage           = 0.0;

/*
  These track times for measuring interrupt frequency
*/
volatile unsigned long lastPulseTime = 0;  // last time we got an interrupt (micros)

// How long to wait (in ms) before we decide there are no more pulses
#define NO_PULSE_TIMEOUT 250  // 500 ms -> Adjust to your preference

void setup() {
  // Initialize serial port
  Serial.begin(9600);

  // Initialize I2C
  Wire.begin();
  
  // Set pin modes
  pinMode(PIN_BATTERY_SENSOR, INPUT);

  /*
    If you are using attachInterrupt on a typical Arduino UNO, 
    you generally must attach to digital pins 2 or 3 (interrupt 0 or 1),
    e.g. "attachInterrupt(digitalPinToInterrupt(2), isrCountPulses, RISING);"

    If your board allows attaching interrupts to A7, that must be a special board
    or a non-UNO device. Adjust accordingly.
  */
  pinMode(PIN_SPEED_SENSOR, INPUT_PULLUP);

  // Attach the ISR for measuring pulses on rising edge
  attachInterrupt(digitalPinToInterrupt(PIN_SPEED_SENSOR), isrCountPulses, RISING);
}

/**
 * Main loop: read sensor data, print to Serial
 */
void loop() {
  // 1) Trigger ultrasonic measurement in centimeters
  sendCommandToUltrasonic(CMD_IN_CM);

  // 2) Wait for the sensor to do its measurement
  //    (typical datasheet suggests up to ~65ms for max distance, 
  //     but you can try smaller if it’s enough)
  delay(20);

  // 3) Read ultrasonic distance
  rearDistance = readUltrasonicDistance();
  
  // 4) Read battery voltage
  batteryVoltage = readBatteryVoltage();

  // 5) Check if we’ve timed out on pulses => no more speed
  unsigned long currentMillis = millis();
  // Convert lastPulseTime (micros) to ms if needed, or store lastPulseTime in millis in the ISR
  // For simplicity, we convert the microseconds measurement to ms:
  unsigned long lastPulseTimeMs = lastPulseTime / 1000UL;
  
  if (currentMillis - lastPulseTimeMs > NO_PULSE_TIMEOUT) {
    pulsesPerSecond = 0.0;
  }

  // 6) Print out the results
  Serial.print(pulsesPerSecond);
  Serial.print("/");
  Serial.print(rearDistance);
  Serial.print("/");
  Serial.println(batteryVoltage);

  // Small delay to avoid flooding Serial
  delay(50);
}

/**
 * ISR: called on rising edge of speedSensor pin.
 * Computes pulses per second based on the time between edges.
 */
void isrCountPulses() {
  unsigned long currentTime = micros();
  
  // Protect from a first-run scenario
  if (lastPulseTime == 0) {
    lastPulseTime = currentTime;
    return;
  }

  unsigned long dt = currentTime - lastPulseTime;
  lastPulseTime    = currentTime;

  // Convert time between pulses (in microseconds) to pulses/second
  // pulsesPerSecond = 1 / (dt [seconds]) => 1e6 / dt [microseconds]
  if (dt > 0) {
    pulsesPerSecond = 1000000.0f / (float)dt;
  }
}

/**
 * Sends a measurement command to the ultrasonic sensor (either in cm or in us).
 */
void sendCommandToUltrasonic(uint8_t command) {
  Wire.beginTransmission(SENSOR_ADDRESS);
  Wire.write(0x00);       // Command register for SRFxx-like sensor
  Wire.write(command);    // e.g. CMD_IN_CM (0x51) or CMD_IN_US (0x52)
  Wire.endTransmission();
}

/**
 * Reads the 16-bit distance value from the ultrasonic sensor's result registers.
 * Return distance in centimeters, or -1 if an error occurred.
 */
int readUltrasonicDistance() {
  // Set pointer to the result register
  Wire.beginTransmission(SENSOR_ADDRESS);
  Wire.write(RESULT_REGISTER); 
  Wire.endTransmission();

  // Request 2 bytes from the sensor
  Wire.requestFrom(SENSOR_ADDRESS, (uint8_t)2);

  unsigned long start = millis();
  // Wait for up to ~10ms for the 2 bytes to be available
  while (Wire.available() < 2) {
    if (millis() - start > 10) {
      // Timeout
      return -1; 
    }
  }

  // Read high byte and low byte
  int highByte = Wire.read();
  int lowByte  = Wire.read();

  return (highByte << 8) | (lowByte & 0xFF);
}

/**
 * Reads the battery voltage from an analog pin and returns the scaled voltage.
 * The factor 9.1 / 1023.0 is from your original code; adjust if needed.
 */
float readBatteryVoltage() {
  int rawVal = analogRead(PIN_BATTERY_SENSOR);
  // Example scaling: measure up to ~9.1 V if using a voltage divider.
  // (Adjust 9.1 to the actual ratio based on your hardware)
  return (rawVal * 9.1f) / 1023.0f;
}
