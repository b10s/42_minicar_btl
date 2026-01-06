#define MOTOR_PIN 9
#define FULL_PERIOD 17021
#define NEUTRAL_PULSE 1560
#define MIN_PULSE 1080
#define MAX_PULSE 2000

void setup() {
  pinMode(MOTOR_PIN, OUTPUT);
}

void loop() {

  float cur_t = millis();
  float t_t = millis();
  while (true) {
    t_t = millis();
    if (t_t - cur_t >= 5000) {
      break;
    }
    // servo neutral max
    digitalWrite(MOTOR_PIN, HIGH);
    delayMicroseconds(NEUTRAL_PULSE);
    digitalWrite(MOTOR_PIN, LOW);
    delayMicroseconds(FULL_PERIOD - NEUTRAL_PULSE;
  }

  cur_t = millis();
  t_t = millis();

  while (true) {
    t_t = millis();
    if (t_t - cur_t >= 5000) {
      break;
    }

    // servo left max
    digitalWrite(MOTOR_PIN, HIGH);
    delayMicroseconds(MIN_PULSE);
    digitalWrite(MOTOR_PIN, LOW);
    delayMicroseconds(FULL_PERIOD - MIN_PULSE);
  }
}
