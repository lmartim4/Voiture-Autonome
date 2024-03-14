#include <Wire.h>

// Ultrassonic sensor
#define sensorAddress 0x70
#define readCentimeters 0x51

#define readMicroseconds 0x52

#define resultRegister 0x02

// Other sensors
#define speedSensor A7
#define batterySensor A3


int rearDistance = 0;

float speedValue = 0.0;
float batteryVoltage = 0.0;

unsigned long currTimer = micros();
unsigned long prevTimer = micros();


void setup() {
  Wire.begin();

  pinMode(batterySensor, INPUT);
  pinMode(speedSensor, INPUT);
  attachInterrupt(
    digitalPinToInterrupt(speedSensor), interruption, RISING);

  Serial.begin(115200); 
  Serial.setTimeout(1);
}


void loop() {
  sendCommand(sensorAddress, readCentimeters);
  delay(20);

  setRegister(sensorAddress, resultRegister);
  rearDistance = readData(sensorAddress, 2);

  batteryVoltage = analogRead(batterySensor) * 7.2 / 1023.0;

  Serial.print(speedValue);
  Serial.print("/");
  Serial.print(rearDistance);
  Serial.print("/");
  Serial.println(batteryVoltage);
  delay(20);
}


void sendCommand (int address, int command) {
  Wire.beginTransmission(address);
  Wire.write(0x00);
  Wire.write(command);
  Wire.endTransmission();
}


void setRegister(int address, int thisRegister) {
  Wire.beginTransmission(address);
  Wire.write(thisRegister);
  Wire.endTransmission();
}


int readData(int address, int numBytes) {
  int result = 0;

  Wire.requestFrom(address, numBytes);
  while (Wire.available() < 2) {}

  result = Wire.read() * 256;
  return result + Wire.read();
}


void interruption () {
  currTimer = micros();

  float delta = currTimer - prevTimer;
  if (delta >= 600) {
    speedValue = (79.0 / (16 * delta)) * 1000;
    prevTimer = currTimer;
  }
}
