// ============================================================================
//  LD06 LiDAR – ESP32 Example Sketch
// ============================================================================

#include "ld06.h"
#include <ESP32Servo.h>

// ---------------- ESP32 UART CONFIG ----------------
#define LD06_RX_PIN 16   // ESP32 RX2
#define LD06_TX_PIN 17   // ESP32 TX2
#define LED_BUILTIN 2
#define MOTOR_PIN 5
#define SERVO_PIN 4


#define PULSE_NEUTRAL 1480               // straight
#define PULSE_MIN 1240                   // full left
#define PULSE_MAX 1720                   // full right
#define PULSE_RANGE_LEFT (PULSE_NEUTRAL - PULSE_MIN)   // 320 us
#define PULSE_RANGE_RIGHT (PULSE_MAX - PULSE_NEUTRAL)  // 160 us

Servo srv;
Servo motor;

HardwareSerial LidarSerial(2); // UART2
LD06 ld06(LidarSerial);

// --------------------------------------------------
void toggleBuiltinLed() {
#ifdef LED_BUILTIN
  static bool ledState = false;
  static uint32_t last = 0;
  if (millis() - last > 300) {
    last = millis();
    ledState = !ledState;
    digitalWrite(LED_BUILTIN, ledState);
  }
#endif
}

void servoTurn(float pos, int timeMs) {  
  int rng;

  if(pos < -100.)
    pos = -100.;
  if(pos > 100.)
    pos = 100.;
  if (pos < 0)
    rng = PULSE_RANGE_LEFT;
  else
    rng = PULSE_RANGE_RIGHT;
  float peak = pos * rng / 100;
  srv.writeMicroseconds(PULSE_NEUTRAL + peak);
  delay(timeMs);
}

void motorRun(float pos) {  
  int rng;

  if(pos < -100.)
    pos = -100.;
  if(pos > 100.)
    pos = 100.;
  if (pos < 0)
    rng = PULSE_RANGE_LEFT;
  else
    rng = PULSE_RANGE_RIGHT;
  float peak = pos * rng / 100;
  motor.writeMicroseconds(PULSE_NEUTRAL + peak);
}

int start = 0;
// --------------------------------------------------
void setup() {
  pinMode(LED_BUILTIN, OUTPUT);

  srv.attach(SERVO_PIN, PULSE_MIN, PULSE_MAX);
  srv.write(PULSE_NEUTRAL);
  motor.attach(MOTOR_PIN, PULSE_MIN, PULSE_MAX);
  motor.write(PULSE_NEUTRAL);
  delay(2000);

  motorRun(50);
  servoTurn(25, 1000);
  servoTurn(50, 1000);
  motorRun(100);
  delay(2000);
  motorRun(0);
  
  //motor.write(PULSE_NEUTRAL + (PULSE_MAX-PULSE_NEUTRAL)/8);
  //delay(1000);
  //motor.write(PULSE_MIN);
  //delay(100);
  //motor.write(PULSE_NEUTRAL);
  // USB debug output
  Serial.begin(921600);
  delay(1000);
  Serial.println("LD06 ESP32 starting...");

  // Start UART2 for LD06
  LidarSerial.begin(
    230400,                // LD06 baudrate
    SERIAL_8N1,
    LD06_RX_PIN,
    LD06_TX_PIN
  );

  // Initialize LD06 driver
  ld06.init();

  // Optional filters (safe defaults)
  ld06.enableFiltering();
  ld06.setDistanceRange(100, 8000); // 0.1m – 8m
  ld06.setAngleRange(0, 360);
  start = millis();

}

int   c = 0;
// --------------------------------------------------
void loop() {
  toggleBuiltinLed();

  // Read LiDAR scan
  if (ld06.readScan()) {

    // --- Real-time visualization ---
    //Serial.printf(">U:|clr\\n");
    //Serial.printf(">U:|clr\n");
    Serial.printf(">!:|clr\n"); 
    ld06.printScanTeleplot(Serial);
    
    //Serial.print("Speed (deg/s): ");
    //Serial.println(ld06.getSpeed(), 1);

    //Serial.print("Points: ");
    //Serial.println(ld06.getNbPointsInScan());
    //c+=1;
    //Serial.print((millis()-start)/c);
    
  }
}

