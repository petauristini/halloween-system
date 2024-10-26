#include <WiFi.h>               // For ESP32
#include <WebServer.h>          // Web server library

// Replace with your network credentials
const char* ssid = "ssid";
const char* password = "password";

// Create a web server on port 80
WebServer server(80);

void function1() {
  Serial.println("Function 1 triggered!");
  server.send(200, "text/plain", "Function 1 executed!");
}

// Function to run when /trigger/function2 is accessed
void function2() {
  Serial.println("Function 2 triggered!");
  server.send(200, "text/plain", "Function 2 executed!");
}

// General trigger handler for dynamic routing
void handleTrigger() {
  String path = server.uri();

  if (path == "/trigger/function1") {
    function1();
  } else if (path == "/trigger/function2") {
    function2();
  } else {
    // Handle unknown trigger function
    server.send(404, "text/plain", "Function not found!");
  }
}

void setup() {
  Serial.begin(115200);

  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi...");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(100);
    Serial.print(".");
  }
  
  Serial.println("\nConnected to WiFi!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  // Define the general /trigger endpoint
  server.on("/trigger/function1", HTTP_GET, handleTrigger);
  server.on("/trigger/function2", HTTP_GET, handleTrigger);

  // Start the server
  server.begin();
  Serial.println("Server started");
}

void loop() {
  // Handle incoming client requests
  server.handleClient();
}