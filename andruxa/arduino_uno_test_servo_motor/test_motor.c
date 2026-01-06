#define MOTOR_PIN 9
#define FULL_PERIOD 17021
#define NEUTRAL_PULSE 1560
#define NEUTRAL_BACK_PULSE 1480

#define MIN_PULSE 1080
#define MED_PULSE 1380
#define MAX_PULSE 1700

void setup() {
  pinMode(MOTOR_PIN, OUTPUT);
}

void loop() {

  float cur_t = millis();
  float t_t = millis();
  while (true) {
    t_t = millis();
    if (t_t - cur_t >= 2000) {
      break;
    }
    // servo neutral max
    digitalWrite(MOTOR_PIN, HIGH);
    delayMicroseconds(NEUTRAL_PULSE);
    digitalWrite(MOTOR_PIN, LOW);
    delayMicroseconds(FULL_PERIOD - NEUTRAL_PULSE);
  }

  cur_t = millis();
  t_t = millis();

  while (true) {
    t_t = millis();
    if (t_t - cur_t >= 2000) {
      break;
    }

    // servo left max
    digitalWrite(MOTOR_PIN, HIGH);
    delayMicroseconds(MIN_PULSE);
    digitalWrite(MOTOR_PIN, LOW);
    delayMicroseconds(FULL_PERIOD - MIN_PULSE);
  }

   cur_t = millis();
  t_t = millis();
   while (true) {
    t_t = millis();
    if (t_t - cur_t >= 2000) {
      break;
    }
    // servo neutral max
    digitalWrite(MOTOR_PIN, HIGH);
    delayMicroseconds(NEUTRAL_PULSE);
    digitalWrite(MOTOR_PIN, LOW);
    delayMicroseconds(FULL_PERIOD - NEUTRAL_PULSE);
  }

  cur_t = millis();
  t_t = millis();
   while (true) {
    t_t = millis();
    if (t_t - cur_t >= 2000) {
      break;
    }

    // servo left max
    digitalWrite(MOTOR_PIN, HIGH);
    delayMicroseconds(MED_PULSE);
    digitalWrite(MOTOR_PIN, LOW);
    delayMicroseconds(FULL_PERIOD - MED_PULSE);
  }


     cur_t = millis();
  t_t = millis();
   while (true) {
    t_t = millis();
    if (t_t - cur_t >= 2000) {
      break;
    }
    // servo neutral max
    digitalWrite(MOTOR_PIN, HIGH);
    delayMicroseconds(NEUTRAL_PULSE);
    digitalWrite(MOTOR_PIN, LOW);
    delayMicroseconds(FULL_PERIOD - NEUTRAL_PULSE);
  }

  cur_t = millis();
  t_t = millis();
   while (true) {
    t_t = millis();
    if (t_t - cur_t >= 2000) {
      break;
    }

    // servo left max
    digitalWrite(MOTOR_PIN, HIGH);
    delayMicroseconds(MAX_PULSE);
    digitalWrite(MOTOR_PIN, LOW);
    delayMicroseconds(FULL_PERIOD - MAX_PULSE);
  }

  
    cur_t = millis();
  t_t = millis();
   while (true) {
    t_t = millis();
    if (t_t - cur_t >= 2000) {
      break;
    }
    // servo neutral max
    digitalWrite(MOTOR_PIN, HIGH);
    delayMicroseconds(NEUTRAL_BACK_PULSE);
    digitalWrite(MOTOR_PIN, LOW);
    delayMicroseconds(FULL_PERIOD - NEUTRAL_BACK_PULSE);
  }

  
  cur_t = millis();
  t_t = millis();
   while (true) {
    t_t = millis();
    if (t_t - cur_t >= 2000) {
      break;
    }

    // servo left max
    digitalWrite(MOTOR_PIN, HIGH);
    delayMicroseconds(MAX_PULSE);
    digitalWrite(MOTOR_PIN, LOW);
    delayMicroseconds(FULL_PERIOD - MAX_PULSE);
  }
}




