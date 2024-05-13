
// global volatile variables are needed to pass data between the

// main program and the ISR's

volatile byte signalA;
volatile byte signalB;

volatile long steps = 0;

// the pins that can be used with interrupts depend on the board you

// are using
const byte inputA = 2;
const byte inputB = 3;

void setup() {

  // initialize serial communication:
	Serial.begin(9600);
	Serial.setTimeout(5000);

  // enable internal resistors on the input pins
	pinMode(inputA, INPUT_PULLUP);
	pinMode(inputB, INPUT_PULLUP);
  // read the initial state of the inputs
	signalA = digitalRead(inputA);
	signalB = digitalRead(inputB);

  // will detect a rising or a falling edge
	attachInterrupt(digitalPinToInterrupt(inputA),signalA_ISR,CHANGE);
	attachInterrupt(digitalPinToInterrupt(inputB),signalB_ISR,RISING);

}

void loop() {
  // This is where the signal information can be used in a program
Serial.println(steps);
delay (500);
}

void signalA_ISR() {
  // when a change is detected it will always be

  // to the opposite of the current state

	signalA = !signalA;
	steps++;
}

void signalB_ISR() {
	signalB = !signalB;
	
}
