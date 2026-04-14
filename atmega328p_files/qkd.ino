
const int TX_PIN = 13; 
const int BAUD_RATE = 100; 
const int HALF_BIT_PERIOD = 1000000 / (BAUD_RATE * 2); 

void setup() {
  Serial.begin(115200);
  pinMode(TX_PIN, OUTPUT);
  digitalWrite(TX_PIN, LOW); 
  Serial.println("--- TX NODE READY ---");
}

void sendBit(bool bit) {
  if (bit) {
    digitalWrite(TX_PIN, LOW); delayMicroseconds(HALF_BIT_PERIOD);
    digitalWrite(TX_PIN, HIGH); delayMicroseconds(HALF_BIT_PERIOD);
  } else {
    digitalWrite(TX_PIN, HIGH); delayMicroseconds(HALF_BIT_PERIOD);
    digitalWrite(TX_PIN, LOW); delayMicroseconds(HALF_BIT_PERIOD);
  }
}

void sendManchesterByte(uint8_t data) {
  sendBit(1);
  for (int i = 0; i < 8; i++) {
    sendBit(bitRead(data, i));
  }
  digitalWrite(TX_PIN, LOW);
}

void loop() {
  if (Serial.available() > 0) {
    char toSend = Serial.read();
    if (toSend != '\n' && toSend != '\r') {
      Serial.println(toSend);
      sendManchesterByte(toSend);
    }
  }
}