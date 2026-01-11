#include "ld06.h"
#include <ESP32Servo.h>

// ESP32 UART config for lidar ld 06
#define LD06_RX_PIN 16   // ESP32 RX2
#define LD06_TX_PIN 17   // ESP32 TX2

#define LED_BUILTIN 2
#define MOTOR_PIN 19
#define SERVO_PIN 18

#define SERVO_CHANNEL 0
#define MOTOR_CHANNEL 1

// Values in microseconds (us)
#define SERVO_NEUTRAL		1560		   					// straight
#define SERVO_MIN			1240    	       				// full left
#define SERVO_MAX			1720        	       			// full right
#define SERVO_RANGE_LEFT	(SERVO_NEUTRAL - SERVO_MIN)
#define SERVO_RANGE_RIGHT	(SERVO_MAX - SERVO_NEUTRAL)

#define MOTOR_NEUTRAL		1560							// Neutral
#define MOTOR_NEUTRAL_BACK	1480							// After that can go backward
#define MOTOR_MIN			1080							// Full speed
#define MOTOR_MAX			2000							// Full back/ brake
#define MOTOR_SLOW			1620							// Slow speed

#define MOTOR_RANGE_BACK	(MOTOR_NEUTRAL - MOTOR_MIN)
#define MOTOR_RANGE_FRONT	(MOTOR_MAX - MOTOR_NEUTRAL) 

#define CYCLE				17021							// PWM Cycle for motor and servo

Servo servo;
Servo motor;

HardwareSerial LidarSerial(2); // UART2
LD06 ld06(LidarSerial);

int start = 0;
int c = 0;
  
void setup() {
  Serial.begin(921600);
  delay(1000);

  pinMode(SERVO_PIN, OUTPUT);
  pinMode(MOTOR_PIN, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);

  servo.setPeriodHertz(50);
  motor.setPeriodHertz(50);

  servo.attach(SERVO_PIN, SERVO_MIN, SERVO_MAX);
  motor.attach(MOTOR_PIN, MOTOR_MIN, MOTOR_MAX);
  delay(5000);

  Serial.println("Start servo, init motor");
  servo.writeMicroseconds(SERVO_NEUTRAL);
  for(int i = 97; i < 103; i++){
    motor.write(i);
    delay(500);
  }

  Serial.println("Init motor done, starting motor");
  
  motor.writeMicroseconds(MOTOR_NEUTRAL);
  digitalWrite(LED_BUILTIN, HIGH);
  delay(5000);
  digitalWrite(LED_BUILTIN, LOW);
  
  motor.writeMicroseconds(MOTOR_SLOW);
  digitalWrite(LED_BUILTIN, HIGH);
  delay(5000);
  digitalWrite(LED_BUILTIN, LOW);
  Serial.println("Spin done, stop");
  
  motor.writeMicroseconds(MOTOR_NEUTRAL);
  digitalWrite(LED_BUILTIN, HIGH);
  delay(5000);
  digitalWrite(LED_BUILTIN, LOW);
  Serial.println("Waiting done, start servo");
  
  servo.writeMicroseconds(SERVO_MAX);
  digitalWrite(LED_BUILTIN, HIGH);
  delay(5000);
  digitalWrite(LED_BUILTIN, LOW);
  
  Serial.println("Servo to opposite");
  servo.writeMicroseconds(SERVO_MIN);
  digitalWrite(LED_BUILTIN, HIGH);
  delay(5000);
  digitalWrite(LED_BUILTIN, LOW);
  
  Serial.println("Servo to neutral");
  servo.writeMicroseconds(SERVO_NEUTRAL);
  
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
    
    //Serial.print("Speed (deg/s): ");
    //Serial.println(ld06.getSpeed(), 1);

    //Serial.print("Points: ");
    //Serial.println(ld06.getNbPointsInScan());
    
	  c+=1;
	  //Serial.print("Hz: ");
    //Serial.println((millis() - start) / c);
  }
}

