#include <DHT.h>
#include <WiFi.h>
#include <PubSubClient.h>

// === BROCHES ===
#define DHT_PIN 4
#define TRIG_PIN 5
#define ECHO_PIN 18
#define FUITE_PIN 21
#define LED_R 25
#define LED_G 26
#define LED_B 27
#define BUZZER_PIN 32
#define HAUTEUR_CUVE 30

// === SEUILS D'ALERTE ===
#define SEUIL_WARNING 1500
#define SEUIL_DANGER 2500
#define SEUIL_CRITIQUE 3500

// === WIFI & MQTT ===
const char* ssid = "Wokwi-GUEST";
const char* password = "";
const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;
const char* client_id = "iut-bandjoun-cap01";

// === TOPICS MQTT ===
const char* topic_json = "iut/bandjoun/capteur/json";
const char* topic_alerte = "iut/bandjoun/alerte";
const char* topic_heartbeat = "iut/bandjoun/heartbeat/capteur01";
const char* topic_commandes = "iut/bandjoun/commandes/capteur01";

DHT dht(DHT_PIN, DHT22);
WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastSend = 0;
unsigned long lastHeartbeat = 0;
unsigned long lastBip = 0;
bool ledState = false;

// === FONCTIONS UTILITAIRES ===
float mesureDistance() {
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  long duree = pulseIn(ECHO_PIN, HIGH);
  return duree * 0.034 / 2;
}

void setRGB(int r, int g, int b) {
  analogWrite(LED_R, r);
  analogWrite(LED_G, g);
  analogWrite(LED_B, b);
}

// === LOGIQUE LED ===
void gererLED(String niveau) {
  if (niveau == "NORMAL") {
    setRGB(0, 255, 0);
  }
  else if (niveau == "WARNING") {
    setRGB(255, 165, 0);
  }
  else if (niveau == "DANGER") {
    setRGB(255, 0, 0);
  }
  else if (niveau == "CRITIQUE") {
    if (millis() - lastBip >= 200) {
      lastBip = millis();
      ledState = !ledState;
      ledState ? setRGB(255, 0, 0) : setRGB(0, 0, 0);
    }
  }
}

// === LOGIQUE BUZZER ===
void gererBuzzer(String niveau) {
  if (niveau == "NORMAL") {
    digitalWrite(BUZZER_PIN, LOW);
  }
  else if (niveau == "WARNING") {
    if (millis() % 5000 < 100) {
      digitalWrite(BUZZER_PIN, HIGH);
    } else {
      digitalWrite(BUZZER_PIN, LOW);
    }
  }
  else if (niveau == "DANGER") {
    if (millis() % 1000 < 100) {
      digitalWrite(BUZZER_PIN, HIGH);
    } else {
      digitalWrite(BUZZER_PIN, LOW);
    }
  }
  else if (niveau == "CRITIQUE") {
    digitalWrite(BUZZER_PIN, HIGH);
  }
}

// === RECEPTION COMMANDES MQTT ===
void onMessage(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.print("Commande recue: ");
  Serial.println(message);

  if (message == "{\"action\":\"reset_alerte\"}") {
    setRGB(0, 255, 0);
    digitalWrite(BUZZER_PIN, LOW);
    Serial.println("Alerte resetee depuis dashboard!");
  }
  else if (message == "{\"action\":\"test_led\"}") {
    setRGB(0, 0, 255);
    delay(1000);
    Serial.println("Test LED effectue!");
  }
}

// === CONNEXIONS ===
void connectWiFi() {
  Serial.print("Connexion WiFi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" Connecte!");
}

void connectMQTT() {
  while (!client.connected()) {
    Serial.print("Connexion MQTT...");
    if (client.connect(client_id)) {
      Serial.println(" OK!");
      client.subscribe(topic_commandes);
      Serial.println("Abonne aux commandes!");
    } else {
      Serial.println(" Echec, retry 3s");
      delay(3000);
    }
  }
}

// === CALCUL NIVEAU ALERTE ===
String calculerNiveau(int valGaz) {
  if (valGaz > SEUIL_CRITIQUE) return "CRITIQUE";
  if (valGaz > SEUIL_DANGER)   return "DANGER";
  if (valGaz > SEUIL_WARNING)  return "WARNING";
  return "NORMAL";
}

void setup() {
  Serial.begin(115200);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(FUITE_PIN, INPUT_PULLUP);
  pinMode(BUZZER_PIN, OUTPUT);
  dht.begin();
  setRGB(0, 255, 0);

  connectWiFi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(onMessage);
  connectMQTT();

  Serial.println("=== Systeme pret ===");
}

void loop() {
  if (!client.connected()) connectMQTT();
  client.loop();

  // Publier toutes les 2s
  if (millis() - lastSend >= 2000) {
    lastSend = millis();

    // Lecture capteurs
    int valGaz = analogRead(34);
    int valCO = analogRead(35);
    float temp = dht.readTemperature();
    float hum = dht.readHumidity();
    float distance = mesureDistance();
    float niveau_cuve = HAUTEUR_CUVE - distance;

    // Niveau alerte basé uniquement sur le gaz
    String niveauAlerte = calculerNiveau(valGaz);

    // Construire JSON
    char jsonBuffer[256];
    snprintf(jsonBuffer, sizeof(jsonBuffer),
      "{\"capteur_id\":\"CAP01\",\"zone\":\"A\","
      "\"gaz_ppm\":%d,\"co_ppm\":%d,"
      "\"temp_c\":%.1f,\"hum\":%.1f,"
      "\"niveau_cuve_cm\":%.1f,"
      "\"fuite_sol\":false,\"niveau\":\"%s\"}",
      valGaz, valCO, temp, hum,
      niveau_cuve, niveauAlerte.c_str()
    );

    // Publier MQTT
    client.publish(topic_json, jsonBuffer);
    client.publish(topic_alerte, niveauAlerte.c_str());
    Serial.println(jsonBuffer);
  }

  // Heartbeat toutes les 30s
  if (millis() - lastHeartbeat >= 30000) {
    lastHeartbeat = millis();
    client.publish(topic_heartbeat, "{\"statut\":\"alive\"}");
    Serial.println("Heartbeat envoye!");
  }

  // LED et Buzzer en continu
  String niveauActuel = calculerNiveau(analogRead(34));
  gererLED(niveauActuel);
  gererBuzzer(niveauActuel);
}