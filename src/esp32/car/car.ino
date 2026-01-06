#include "ld06.h"
#include <ESP32Servo.h>

// ESP32 UART config for lidar ld 06
#define LD06_RX_PIN 16   // ESP32 RX2
#define LD06_TX_PIN 17   // ESP32 TX2

#define MOTOR_PIN 5
#define SERVO_PIN 4

// Values in microseconds (us)
#define SERVO_NEUTRAL		1480		   					// straight
#define SERVO_MIN			1240    	       				// full left
#define SERVO_MAX			1720        	       			// full right
#define SERVO_RANGE_LEFT	(PULSE_NEUTRAL - PULSE_MIN)
#define SERVO_RANGE_RIGHT	(PULSE_MAX - PULSE_NEUTRAL)

#define MOTOR_NEUTRAL		1560							// Neutral
#define MOTOR_NEUTRAL_BACK	1480							// After that can go backward
#define MOTOR_MIN			1080							// Full speed
#define MOTOR_MAX			2000							// Full back/ brake
#define MOTOR_RANGE_BACK	(PULSE_NEUTRAL - PULSE_MIN)
#define MOTOR_RANGE_FRONT	(PULSE_MAX - PULSE_NEUTRAL) 

#define CYCLE				17021							// PWM Cycle for motor and servo

Servo servo;
Servo motor;

HardwareSerial LidarSerial(2); // UART2
LD06 ld06(LidarSerial);

int start = 0;
int c = 0;
  
void setup() {
    
  servo.attach(SERVO_PIN, SERVO_MIN, SERVO_MAX);
  servo.write(SERVO_NEUTRAL);
  motor.attach(MOTOR_PIN, MOTOR_MIN, MOTOR_MAX);
  motor.write(MOTOR_NEUTRAL);
  
  delay(2000);
  motor.write(MOTOR_MAX);
  delay(2000);
  motor.write(MOTOR_NEUTRAL);

  delay(2000);
  servo.write(SERVO_MAX);
  delay(2000);
  servo.write(SERVO_NEUTRAL)
  
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



void loop() {
  // Read LiDAR scan

  if (ld06.readScan()) {
    // --- Real-time visualization ---
    // Serial.printf(">!:|clr\n"); 
    // ld06.printScanTeleplot(Serial);
    
    Serial.print("Speed (deg/s): ");
    Serial.println(ld06.getSpeed(), 1);

    Serial.print("Points: ");
    Serial.println(ld06.getNbPointsInScan());
    
	  c+=1;
	  Serial.print("Hz: ");
    Serial.println((millis() - start) / c)
  }
}

