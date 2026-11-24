#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESP32Servo.h>
#include <stdlib.h>

#if __has_include("wifi_config.h")
#include "wifi_config.h"
#else
#include "wifi_config.example.h"
#endif

constexpr int JOINT1_PIN = 18;
constexpr int JOINT2_PIN = 19;
constexpr int ANGLE_COUNT = 4;
Servo joint1;
Servo joint2;
WiFiUDP udp;
bool listening = false;
bool servosReady = false;
unsigned long lastReconnect = 0;

bool parseAngles(char *packet, size_t size, int *angles) {
  // Accept four integers with commas and a final newline.
  char *cursor = packet;
  char *end = packet + size;
  for (int index = 0; index < ANGLE_COUNT; ++index) {
    char *digits = cursor;
    if (digits < end && *digits == '-') {
      ++digits;
    }
    char *separator = digits;
    while (separator < end && *separator >= '0' && *separator <= '9') {
      ++separator;
    }
    char expected = index == ANGLE_COUNT - 1 ? '\n' : ',';
    if (separator == digits || separator == end || *separator != expected) {
      return false;
    }
    long value = strtol(cursor, nullptr, 10);
    angles[index] = constrain(value, 0L, 180L);
    cursor = separator + 1;
  }
  return cursor == end;
}

void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_NAME, WIFI_PASSWORD);
}

void loop() {
  // Restart UDP when Wi-Fi comes back.
  if (WiFi.status() != WL_CONNECTED) {
    if (listening) {
      udp.stop();
      listening = false;
    }
    if (millis() - lastReconnect >= 10000) {
      lastReconnect = millis();
      WiFi.reconnect();
    }
    delay(20);
    return;
  }
  if (!listening) {
    listening = udp.begin(UDP_PORT);
    if (!listening) {
      delay(500);
      return;
    }
    Serial.print("ESP32 IP: ");
    Serial.println(WiFi.localIP());
  }

  int packetSize = udp.parsePacket();
  if (packetSize <= 0) {
    delay(2);
    return;
  }

  char packet[64];
  if (packetSize >= static_cast<int>(sizeof(packet))) {
    // Drain this packet so the next one can be read.
    while (udp.available() > 0) {
      if (udp.read(reinterpret_cast<uint8_t *>(packet), sizeof(packet)) <= 0) {
        break;
      }
    }
    return;
  }
  int bytesRead = udp.read(reinterpret_cast<uint8_t *>(packet), packetSize);
  if (bytesRead != packetSize) {
    return;
  }
  packet[bytesRead] = '\0';
  int angles[ANGLE_COUNT];
  if (!parseAngles(packet, bytesRead, angles)) {
    return;
  }

  // Start PWM only after a valid command arrives.
  if (!servosReady) {
    joint1.setPeriodHertz(50);
    joint2.setPeriodHertz(50);
    joint1.attach(JOINT1_PIN, 1000, 2000);
    joint2.attach(JOINT2_PIN, 1000, 2000);
    servosReady = true;
  }
  joint1.write(angles[0]);
  joint2.write(angles[1]);
}
