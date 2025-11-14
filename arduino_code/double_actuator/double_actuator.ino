// ===================== USER-CONFIGURABLE CONSTANTS =====================
const float MAX_SPEED_IPS = 2.16;   // actuator speed in inches/second at full power
const float STROKE_IN     = 12.0;   // total stroke length in inches

// MegaMoto #1 (Actuator 1)
const int ENABLE1 = 8;
const int FWD1    = 11;   // PWM pin
const int REV1    = 3;    // PWM pin

// MegaMoto #2 (Actuator 2)
const int ENABLE2 = 7;
const int FWD2    = 10;   // PWM pin
const int REV2    = 5;    // PWM pin

// ===================== STATE VARIABLES =====================
float pos1_in = 0.0;  // estimated position of actuator 1 in inches (0 = fully retracted)
float pos2_in = 0.0;  // estimated position of actuator 2 in inches

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

// ===================== SETUP =====================
void setup() {
  pinMode(ENABLE1, OUTPUT);
  pinMode(FWD1, OUTPUT);
  pinMode(REV1, OUTPUT);

  pinMode(ENABLE2, OUTPUT);
  pinMode(FWD2, OUTPUT);
  pinMode(REV2, OUTPUT);

  stopActuator1();
  stopActuator2();

  Serial.begin(9600);
  Serial.println("System starting...");

  resetActuators();   // <<< run reset here

  Serial.println("Ready for serial commands: pos1,pos2,time");
}
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
// ===================== MAIN LOOP =====================
void loop() {
  if (Serial.available() > 0) {
    // Parse 3 numbers: pos1, pos2, time
    float target1 = Serial.parseFloat();   // actuator 1 target position (inches)
    float target2 = Serial.parseFloat();   // actuator 2 target position (inches)
    float target3 = Serial.parseFloat();
    float moveTime = Serial.parseFloat();  // move time (seconds)

    // optional: eat the rest of the line
    while (Serial.available() > 0) {
      char c = Serial.read();
      if (c == '\n' || c == '\r') break;
    }

    // Validate move time
    if (moveTime <= 0) {
      Serial.println("Error: time must be > 0");
      return;
    }

    // Constrain positions to stroke range
    target1 = constrain(target1, 0.0, STROKE_IN);
    target2 = constrain(target2, 0.0, STROKE_IN);

    Serial.print("Command received: ");
    Serial.print(target1); Serial.print(" in, ");
    Serial.print(target2); Serial.print(" in, ");
    Serial.print(moveTime); Serial.println(" s");

    moveActuatorsToTargets(target1, target2, moveTime);
  }
}

// ===================== MOTION FUNCTION =====================
void moveActuatorsToTargets(float target1, float target2, float moveTime) {
  // Compute distance to move
  float delta1 = target1 - pos1_in;
  float delta2 = target2 - pos2_in;

  float dist1 = fabs(delta1);
  float dist2 = fabs(delta2);

  // Determine directions
  int dir1 = (delta1 > 0) - (delta1 < 0); // +1, 0, or -1
  int dir2 = (delta2 > 0) - (delta2 < 0);

  // If no movement requested, just stop
  if (dist1 == 0 && dist2 == 0) {
    Serial.println("No movement required.");
    stopActuator1();
    stopActuator2();
    return;
  }

  // Required speeds to reach each target in the given time
  float reqSpeed1 = (moveTime > 0) ? dist1 / moveTime : 0.0; // in/s
  float reqSpeed2 = (moveTime > 0) ? dist2 / moveTime : 0.0; // in/s

  // Convert required speeds to PWM (assuming linear from 0 to MAX_SPEED_IPS)
  // pwm = 255 * (required_speed / max_speed)
  float pwm1f = (MAX_SPEED_IPS > 0) ? (255.0 * reqSpeed1 / MAX_SPEED_IPS) : 0.0;
  float pwm2f = (MAX_SPEED_IPS > 0) ? (255.0 * reqSpeed2 / MAX_SPEED_IPS) : 0.0;

  // Limit PWM to [0,255]
  pwm1f = constrain(pwm1f, 0.0, 255.0);
  pwm2f = constrain(pwm2f, 0.0, 255.0);

  int pwm1 = (int)pwm1f;
  int pwm2 = (int)pwm2f;

  // Check if we’re asking more than the actuator can physically do
  if (reqSpeed1 > MAX_SPEED_IPS || reqSpeed2 > MAX_SPEED_IPS) {
    Serial.println("Warning: requested move is faster than max speed.");
    Serial.println("Actuators will run at max speed and may not reach targets in the given time.");
  }

  // Start motion
  driveActuator1(dir1, pwm1);
  driveActuator2(dir2, pwm2);

  // Block until moveTime has passed (simple version)
  unsigned long ms = (unsigned long)(moveTime * 1000.0);
  delay(ms);

  // Stop both actuators
  stopActuator1();
  stopActuator2();

  // Update our estimated positions
  // If speed was within range, assume we hit the target; otherwise approximate
  if (reqSpeed1 <= MAX_SPEED_IPS) {
    pos1_in = target1;
  } else {
    // moved ~MAX_SPEED_IPS * time in the desired direction
    pos1_in += dir1 * MAX_SPEED_IPS * moveTime;
    pos1_in = constrain(pos1_in, 0.0, STROKE_IN);
  }

  if (reqSpeed2 <= MAX_SPEED_IPS) {
    pos2_in = target2;
  } else {
    pos2_in += dir2 * MAX_SPEED_IPS * moveTime;
    pos2_in = constrain(pos2_in, 0.0, STROKE_IN);
  }

  Serial.print("New estimated positions: A1 = ");
  Serial.print(pos1_in);
  Serial.print(" in, A2 = ");
  Serial.print(pos2_in);
  Serial.println(" in");
}
