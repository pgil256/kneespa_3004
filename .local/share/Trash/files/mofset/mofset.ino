
#include <elapsedMillis.h>
elapsedMillis timeElapsed;

int RPWM = 10;
int LPWM = 11;
int sensorPin = A0;

int FITENABLE = 44; // Needs to be a PWM pin to be able to control motor speed
int FITFORWARD = 42;
int FITREVERSE = 43;
// global volatile variables are needed to pass data between the

int sensorVal;
int Speed = 255;
float strokeLength = 6.0;                           //customize to your specific stroke length
float extensionLength;

int maxAnalogReading;
int minAnalogReading;

void setup() {
  // declare Relay as output
  pinMode(FITENABLE, OUTPUT);
  pinMode(FITFORWARD, OUTPUT);
  pinMode(FITREVERSE, OUTPUT);


  pinMode(sensorPin, INPUT);
  Serial.begin(9600);
  Serial.println("\n\n\n\n\n\n\n\nStarting");

  maxAnalogReading = moveToLimit(1);
  minAnalogReading = moveToLimit(-1);
    Serial.print("minAnalogReading ");
  Serial.print(minAnalogReading);
  Serial.print(" ");
  Serial.println(maxAnalogReading);

}

void loop() {
  Serial.println("Extending...");
  sensorVal = analogRead(sensorPin);
  Serial.println(sensorVal);
  while (sensorVal < maxAnalogReading) {
    driveActuator(1, Speed);
    displayOutput();
    delay(20);
  }
  driveActuator(0, Speed);
  delay(1000);

  Serial.println("Retracting...");
  sensorVal = analogRead(sensorPin);
  while (sensorVal > minAnalogReading) {
    driveActuator(-1, Speed);
    displayOutput();
    delay(20);
  }
  driveActuator(0, Speed);
  delay(1000);
}

int moveToLimit(int Direction) {
  int prevReading = 0;
  int currReading = 0;
  do {
    prevReading = currReading;
    driveActuator(Direction, Speed);
    timeElapsed = 0;
    while (timeElapsed < 200*5) {
      delay(1); //keep moving until analog reading remains the same for 200ms
    }
    currReading = analogRead(sensorPin);
    Serial.println(currReading);
  } while (prevReading != currReading);
  return currReading;
}

float mapfloat(float x, float inputMin, float inputMax, float outputMin, float outputMax) {
  return (x - inputMin) * (outputMax - outputMin) / (inputMax - inputMin) + outputMin;
}

void displayOutput() {
  sensorVal = analogRead(sensorPin);
  extensionLength = mapfloat(sensorVal, float(minAnalogReading), float(maxAnalogReading), 0.0, strokeLength);
  Serial.print("Analog Reading: ");
  Serial.print(sensorVal);
  Serial.print("\tActuator extension length: ");
  Serial.print(extensionLength);
  Serial.println(" inches");
}

void driveActuator(int Direction, int Speed) {

  digitalWrite(FITENABLE, HIGH);

  switch (Direction) {
    case 1:       //extension
      Serial.println("Fit extending.");
      digitalWrite(FITFORWARD, HIGH);
      digitalWrite(FITREVERSE, LOW);
      break;

    case 0:       //stopping
      Serial.println("Fit stopped.");
      digitalWrite(FITFORWARD, LOW);
      digitalWrite(FITREVERSE, LOW);
      break;

    case -1:      //retraction
      Serial.println("Fit reversing.");
      digitalWrite(FITFORWARD, LOW);
      digitalWrite(FITREVERSE, HIGH);
      break;
  }
}
