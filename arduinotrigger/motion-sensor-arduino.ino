#include <WiFi.h>
#include <HTTPClient.h>

const char* ssid = "ssid";
const char* password = "password";

const char* triggerEndpoint = "http://<ip>:<port>/trigger/<triggerId>";

const int triggerPin = 15;

void setup() {

  Serial.begin(115200);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");

  pinMode(triggerPin, INPUT_PULLDOWN);

}

void loop() {

  if (digitalRead(triggerPin) == HIGH) {

    if (WiFi.status() == WL_CONNECTED) {

      HTTPClient http;
      
      Serial.print("Sending HTTP GET request to: ");
      Serial.println(triggerEndpoint);
      
      http.begin(triggerEndpoint);
      int httpResponseCode = http.GET();

      if (httpResponseCode > 0) {
        String response = http.getString();
        Serial.print("HTTP Response code: ");
        Serial.println(httpResponseCode);
        Serial.println("Response: " + response);
      } else {
        Serial.print("Error on sending request: ");
        Serial.println(httpResponseCode);
      }

      http.end();

    } else {

      Serial.println("WiFi Disconnected");

    }
  }
}
