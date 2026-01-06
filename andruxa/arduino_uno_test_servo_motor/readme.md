не уверен что этот код работает )

но только он остался у меня лишь
йо

вот код который я брал за основу 
от Саши

```
void loop() {
  float width = 1000000./58.75;
  float wdef = 1560;
  float wlow = width - wdef;
  digitalWrite(LED_BUILTIN, HIGH);  // turn the LED on (HIGH is the voltage level)
  delayMicroseconds(wdef);                      // wait for a second
  digitalWrite(LED_BUILTIN, LOW);   // turn the LED off by making the voltage LOW
  delayMicroseconds(wlow);                      // wait for a second
}

```



сегодня смогли шевелить мотором на разных скоростях и даже крутить его назад
код в файлике test_motor.c 
