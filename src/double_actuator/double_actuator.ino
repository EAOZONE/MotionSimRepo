// ===== Dual‐Actuator Control via Python over Serial =====

// Calibration for each actuator (pulses per cm)
const float pulsesPerCm1 = 705.86;         // Actuator 1
const float pulsesPerCmBackwards = 229.16666625;
const float pulsesPerCm2 = 111.67 * 2.0;   // Actuator 2

// Define your half‐stroke distances (in cm)
const float midDist1 = 10.125;  // ← half‐travel for A1
const float midDist2 =  10.125;  // ← half‐travel for A2

// Pin definitions
const int en1Pin   = 12;
const int pwm1A    = 9;    // A1 extend
const int pwm1B    = 10;   // A1 retract
const int hall1Pin = 2;    // A1 sensor

const int en2Pin   = 13;
const int pwm2A    = 6;    // A2 extend
const int pwm2B    = 5;    // A2 retract
const int hall2Pin = 3;    // A2 sensor

const int speed    = 200;  // PWM speed (0–255)

float prev1 = 0;
float prev2 = 0;

// Pulse counters (for ISR)
volatile unsigned long pulseCount1 = 0;
volatile unsigned long pulseCount2 = 0;

// ISR callbacks
void countPulse1() { pulseCount1++; }
void countPulse2() { pulseCount2++; }

// Move each actuator by a signed distance (cm) simultaneously

void resetToZero(){
analogWrite(pwm1A, 0);      analogWrite(pwm1B, 200);
analogWrite(pwm2A, 0);      analogWrite(pwm2B, 200);
wait(20000);
}
void moveRelative(float d1, float d2) {
  unsigned long target1;
  if(d1 < 0){
    target1 = abs(d1)*pulsesPerCmBackwards;
  }
  else{
  target1 = abs(d1) * pulsesPerCm1;
  }
  unsigned long target2 = abs(d2) * pulsesPerCm2;

  // reset counters
  noInterrupts();
    pulseCount1 = 0;
    pulseCount2 = 0;
  interrupts();
  // Figure out how “far” each is moving
  float absD1 = abs(d1), absD2 = abs(d2);
  float maxDist = max(absD1, absD2);

  // Scale each PWM so the longest move uses your full 'speed'
  int speed1 = (maxDist > 0)
    ? int(speed * (absD1 / maxDist))
    : 0;
  int speed2 = (maxDist > 0)
    ? int(speed * (absD2 / maxDist))
    : 0;

  // set directions
  if (d1 >= 0) { analogWrite(pwm1A, speed1);  analogWrite(pwm1B, 0); }
  else         { analogWrite(pwm1A, 0);      analogWrite(pwm1B, speed1); }

  if (d2 >= 0) { analogWrite(pwm2A, speed2);  analogWrite(pwm2B, 0); }
  else         { analogWrite(pwm2A, 0);      analogWrite(pwm2B, speed2); }

  // wait until both reach targets
  while (pulseCount1 < target1 || pulseCount2 < target2) {
    Serial.println(String(pulseCount1));
    if (pulseCount1 >= target1) {
      analogWrite(pwm1A, 0);
      analogWrite(pwm1B, 0);
    }
    if (pulseCount2 >= target2) {
      analogWrite(pwm2A, 0);
      analogWrite(pwm2B, 0);
    }
  }

  // ensure both off
  analogWrite(pwm1A, 0); analogWrite(pwm1B, 0);
  analogWrite(pwm2A, 0); analogWrite(pwm2B, 0);
}

void setup() {
  // enable motor drivers
  pinMode(en1Pin, OUTPUT); digitalWrite(en1Pin, HIGH);
  pinMode(en2Pin, OUTPUT); digitalWrite(en2Pin, HIGH);

  // direction pins
  pinMode(pwm1A, OUTPUT); pinMode(pwm1B, OUTPUT);
  pinMode(pwm2A, OUTPUT); pinMode(pwm2B, OUTPUT);

  // hall sensors + interrupts
  pinMode(hall1Pin, INPUT_PULLUP);
  pinMode(hall2Pin, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(hall1Pin), countPulse1, CHANGE);
  attachInterrupt(digitalPinToInterrupt(hall2Pin), countPulse2, CHANGE);

  Serial.begin(9600);
  while (!Serial) { }

  // go to midpoint once
  resetToZero();
  moveRelative(midDist1, midDist2);
}
void loop() {
  if (!Serial.available()) return;
  String line = Serial.readStringUntil('\n');
  line.trim();
  if (line.length() == 0) return;

  // parse floats
  float d1, d2;
  int comma = line.indexOf(',');
  if (comma < 0) {
    d1 = d2 = line.toFloat();
  } else {
    d1 = line.substring(0, comma).toFloat();
    d2 = line.substring(comma + 1).toFloat();
  }

  Serial.println(F("Moving: "));
  Serial.println("D1 " + String(d1)); 
  Serial.println("D2 " + String(d2));
  d1 = d1 - prev1;
  d2 = d2 - prev2;
  Serial.println("New D1 " + String(d1));
  Serial.println("New D2 " + String(d2));
  moveRelative(d1, d2);
  prev1 = d1+prev1;
  prev2 = d2+prev2;
  Serial.println("Prev1 " + String(prev1));
  Serial.println("Prev2 " + String(prev2));
  Serial.println("DONE");
}
