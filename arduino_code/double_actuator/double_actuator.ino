// ===================== USER-CONFIGURABLE CONSTANTS =====================
const float MAX_SPEED_IPS = 2.16;   // actuator speed in inches/second at full power
const float STROKE_IN     = 6.0;   // total stroke length in inches
const float RPM = 36.0;

// MegaMoto #1 (Actuator 1)
const int ENABLE1 = 12;
const int FWD1    = 9;   // PWM pin
const int REV1    = 10;    // PWM pin

// MegaMoto #2 (Actuator 2)
const int ENABLE2 = 13;
const int FWD2    = 6;   // PWM pin
const int REV2    = 5;    // PWM pin

// Motor Controller (Motor)
const int ENABLE3 = 100000; //Need to figure out the write spot
const int FWD3 = 3;
const int REV3 = 11;

// ===================== STATE VARIABLES =====================
float pos1_in = 0.0;  // estimated position of actuator 1 in inches (0 = fully retracted)
float pos2_in = 0.0;  // estimated position of actuator 2 in inches
float pos3_in = 0.0;

// ===================== BASIC MOTOR CONTROL HELPERS =====================
void stopActuator1() {
  digitalWrite(ENABLE1, LOW);
  analogWrite(FWD1, 0);
  analogWrite(REV1, 0);
}

void stopActuator2() {
  digitalWrite(ENABLE2, LOW);
  analogWrite(FWD2, 0);
  analogWrite(REV2, 0);
}

void stopMotor()
{
  digitalWrite(ENABLE3, LOW);
  analogWrite(FWD3, 0);
  analogWrite(REV3, 0);
}

void driveActuator1(int direction, int pwm) {
  // direction: +1 = extend (FWD), -1 = retract (REV), 0 = stop
  if (direction == 0 || pwm == 0) {
    stopActuator1();
    return;
  }

  digitalWrite(ENABLE1, HIGH);
  if (direction > 0) {
    // Extend
    analogWrite(REV1, 0);
    analogWrite(FWD1, pwm);
  } else {
    // Retract
    analogWrite(FWD1, 0);
    analogWrite(REV1, pwm);
  }
}

void driveActuator2(int direction, int pwm) {
  // direction: +1 = extend (FWD), -1 = retract (REV), 0 = stop
  if (direction == 0 || pwm == 0) {
    stopActuator2();
    return;
  }

  digitalWrite(ENABLE2, HIGH);
  if (direction > 0) {
    // Extend
    analogWrite(REV2, 0);
    analogWrite(FWD2, pwm);
  } else {
    // Retract
    analogWrite(FWD2, 0);
    analogWrite(REV2, pwm);
  }
}
void driveMotor(int direction, int pwm) {
  // direction: +1 = extend (FWD), -1 = retract (REV), 0 = stop
  if (direction == 0 || pwm == 0) {
    stopMotor();
    return;
  }

  digitalWrite(ENABLE3, HIGH);
  if (direction > 0) {
    // Extend
    analogWrite(REV3, 0);
    analogWrite(FWD3, pwm);
  } else {
    // Retract
    analogWrite(FWD3, 0);
    analogWrite(REV3, pwm);
  }
}


// ===================== RESET FUNCTION =====================
void resetActuators() {
  Serial.println("Resetting actuators (full retract)…");

  // Full reverse, both actuators
  driveActuator1(-1, 255);   // direction -1 = retract
  driveActuator2(-1, 255);

  delay(7000);  // long enough to fully retract (adjust as needed)

  stopActuator1();
  stopActuator2();

  // Set known positions
  pos1_in = 0.0;
  pos2_in = 0.0;

  Serial.println("Reset complete. Both actuators set to 0 inches.");
}

// ===================== SETUP =====================
void setup() {
  pinMode(ENABLE1, OUTPUT);
  pinMode(FWD1, OUTPUT);
  pinMode(REV1, OUTPUT);

  pinMode(ENABLE2, OUTPUT);
  pinMode(FWD2, OUTPUT);
  pinMode(REV2, OUTPUT);

  pinMode(ENABLE3, OUTPUT);
  pinMode(FWD3, OUTPUT);
  pinMode(REV3, OUTPUT);

  stopActuator1();
  stopActuator2();
  stopMotor();

  Serial.begin(9600);
  Serial.println("System starting...");

  resetActuators();   // run reset here

  Serial.println("Ready for serial commands: pos1,pos2");
}

// ===================== MAIN LOOP =====================
void loop() {
  if (Serial.available() > 0) {
    // Parse 2 numbers: pos1, pos2
    float target1 = Serial.parseFloat();   // actuator 1 target position (inches)
    float target2 = Serial.parseFloat();   // actuator 2 target position (inches)
    float target3 = Serial.parseFloat();
    Serial.println(target1);
    Serial.println(target2);
    Serial.println(target3);


    // optional: eat the rest of the line
    while (Serial.available() > 0) {
      char c = Serial.read();
      if (c == '\n' || c == '\r') break;
    }

    // Constrain positions to stroke range
    target1 = constrain(target1, 0.0, STROKE_IN);
    target2 = constrain(target2, 0.0, STROKE_IN);
    target3 = constrain(target3, -45.0, 45.0);

    Serial.print("Command received: ");
    Serial.print(target1); Serial.print(" in, ");
    Serial.print(target2); Serial.println(" in");

    moveActuatorsToTargets(target1, target2, target3);
  }
}

// ===================== MOTION FUNCTION =====================
// Runs actuators at full speed until they *should* reach the requested positions,
// then prints "Finished".
void moveActuatorsToTargets(float target1, float target2, float target3) {
  // Compute distance to move
  float delta1 = target1 - pos1_in;
  float delta2 = target2 - pos2_in;
  float delta3 = target3 - pos3_in;

  float dist1 = fabs(delta1);
  float dist2 = fabs(delta2);
  float dist3 = fabs(delta3);

  // Determine directions
  int dir1 = (delta1 > 0) - (delta1 < 0); // +1, 0, or -1
  int dir2 = (delta2 > 0) - (delta2 < 0);
  int dir3 = (delta3 > 0) - (delta3 < 0);

  // If no movement requested, just stop
  if (dist1 == 0 && dist2 == 0 && dist3 ==0) {
    Serial.println("No movement required.");
    stopActuator1();
    stopActuator2();
    stopMotor();
    Serial.println("Finished");
    return;
  }

  // Compute run times (seconds) based on full speed
  // Avoid divide-by-zero
  float time1_s = (dir1 != 0 && MAX_SPEED_IPS > 0) ? (dist1 / MAX_SPEED_IPS) : 0.0;
  float time2_s = (dir2 != 0 && MAX_SPEED_IPS > 0) ? (dist2 / MAX_SPEED_IPS) : 0.0;
  float time3_s = (dir3 != 0 && RPM > 0) ? (dist3/216) : 0.0;

  time1_s = time1_s*200/255;
  time2_s = time2_s *200/255;
  time3_s= 255*time3_s/200;
  unsigned long duration1_ms = (unsigned long)(time1_s * 1000.0);
  unsigned long duration2_ms = (unsigned long)(time2_s * 1000.0);
  unsigned long duration3_ms = (unsigned long)(time3_s * 1000.0);
  Serial.print("Motor Time: ");
  Serial.println(duration3_ms);

  bool a1Done = (dir1 == 0 || duration1_ms == 0);
  bool a2Done = (dir2 == 0 || duration2_ms == 0);
  bool a3Done = (dir3 == 0 || duration3_ms == 0);

  // Start motion (full speed for any actuator that needs to move)
  if (!a1Done) driveActuator1(dir1, 255);
  if (!a2Done) driveActuator2(dir2, 255);
  if (!a3Done) driveMotor(dir3, 200);

  unsigned long startMs = millis();

  // Simple blocking loop until both are "done"
  while (!a1Done || !a2Done || !a3Done) {
    unsigned long elapsed = millis() - startMs;

    if (!a1Done && elapsed >= duration1_ms) {
      stopActuator1();
      pos1_in = target1;
      a1Done = true;
    }

    if (!a2Done && elapsed >= duration2_ms) {
      stopActuator2();
      pos2_in = target2;
      a2Done = true;
    }

    if (!a3Done && elapsed >= duration3_ms) {
      stopMotor();
      pos3_in = target3;
      a3Done = true;
    }

    // Tiny delay to avoid hammering the CPU
    delay(5);
  }

  // Safety clamp positions
  pos1_in = constrain(pos1_in, 0.0, STROKE_IN);
  pos2_in = constrain(pos2_in, 0.0, STROKE_IN);
  pos3_in = constrain(pos3_in, -45.0, 45.0);

  Serial.print("New estimated positions: A1 = ");
  Serial.print(pos1_in);
  Serial.print(" in, A2 = ");
  Serial.print(pos2_in);
  Serial.print(" in, Motor = ");
  Serial.print(pos3_in);
  Serial.println(" degs");

  Serial.println("Finished");
}
