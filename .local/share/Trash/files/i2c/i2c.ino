#include <Wire.h>
#include "HX711.h"

#define LOADCELL_DOUT_PIN  7
#define LOADCELL_SCK_PIN  6

float pressure;
float calibration_factor = 14920.0; // worked for test weight 3lbs

HX711 scale;

void setup() {
  Serial.begin(9600);
  while (!Serial);

  pinMode(2, OUTPUT);    // sets the digital pin as output


  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  // scale.set_scale();
  // scale.tare(); //Reset the scale to 0

  //  long zero_factor = scale.read_average(); //Get a baseline reading
  scale.set_scale(calibration_factor); //Adjust to this calibration factor

  Wire.begin(0x20);
  Wire.onRequest(sendEvent);

}
void sendEvent()
{
  static int i = 0;
  Serial.print(F("Sending  pressure: "));
  Serial.println(pressure);
  digitalWrite(2, HIGH);  // sets the last digital pin off
  Wire.print(pressure, 2);
  delay(500);
  digitalWrite(2, LOW);  // sets the last digital pin off
}

void loop() {

  if (scale.wait_ready_retry(10)) {
Serial.print("read: \t\t");
  Serial.println(scale.read());                 // print a raw reading from the ADC

  Serial.print("read average: \t\t");
  Serial.println(scale.read_average(20));       // print the average of 20 readings from the ADC

  Serial.print("get value: \t\t");
  Serial.println(scale.get_value(5));    // print the average of 5 readings from the ADC minus the tare weight, set with tare()

  Serial.print("get units: \t\t");
  Serial.println(scale.get_units(5), 1);        // print the average of 5 readings from the ADC minus tare weight, divided
            // by the SCALE parameter set with set_scale
  
//pressure = abs(scale.get_units(10));
pressure = 0;
  Serial.print(F(" pressure: "));
  Serial.println(pressure);
  } else {
    Serial.println("HX711 not found.");
  }
  
 
  delay(500);
}
