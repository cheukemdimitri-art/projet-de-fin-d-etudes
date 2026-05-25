void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  Serial.println("Hello, ESP32!");
}

void loop() {
  int val = analogRead(34);
  Serial.println(val);
  delay(1000);
}
