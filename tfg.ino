#include <PID_v1.h>

// Pines
const int ssrPin = 5;         // SSR 
const int relay1Pin = 3;      // Relay 1 
const int relay2Pin = 4;      // Relay 2 
const int pressureSensorPin = A2;  // sensor de presion
const int flowSensor1Pin = 18;  // sensor flujo 1
const int flowSensor2Pin = 19;  // sensor flujo 2

// pines para sensores de temperatura
int ThermistorPin1 = A0; 
int ThermistorPin2 = A1; 

// varaibles de sensores de flujo
volatile int flowPulses1 = 0;
volatile int flowPulses2 = 0;
float flowRate1 = 0.0;
float flowRate2 = 0.0;
unsigned long oldTime = 0;

// constantes para los sensores de temperatura
float R1 = 22020;
float R2 = 22140;
float c1 = 1.009249522e-03, c2 = 2.378405444e-04, c3 = 2.019202697e-07;

float Tc1, Tc2;

// PID
double pidInput, pidOutput;
double targetTemp = 25.0; // temperatura default
double Kp = 2.0, Ki = 5.0, Kd = 1.0;  // coeficientes de PID 
PID myPID(&pidInput, &pidOutput, &targetTemp, Kp, Ki, Kd, REVERSE);

void setup() {
  
  pinMode(ssrPin, OUTPUT);
  pinMode(relay1Pin, OUTPUT);
  pinMode(relay2Pin, OUTPUT);

  
  pinMode(flowSensor1Pin, INPUT);
  pinMode(flowSensor2Pin, INPUT);
  attachInterrupt(digitalPinToInterrupt(flowSensor1Pin), flowSensor1Pulse, RISING);
  attachInterrupt(digitalPinToInterrupt(flowSensor2Pin), flowSensor2Pulse, RISING);

  
  myPID.SetMode(AUTOMATIC);
  myPID.SetOutputLimits(0, 255); 

  
  digitalWrite(ssrPin, LOW);       // SSR off
  digitalWrite(relay1Pin, LOW);    // Relay 1 off
  digitalWrite(relay2Pin, LOW);    // Relay 2 off

  Serial.begin(9600);  
}

void loop() {
  
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    targetTemp = input.toFloat();  
    Serial.print("\nNew target temperature set to: ");
    Serial.print(targetTemp);
    Serial.println(" C");
  }

  // lectura de temperatura
  Tc1 = readThermistor(ThermistorPin1, R1); // Initial temperature
  Tc2 = readThermistor(ThermistorPin2, R2); // Final temperature

  
  pidInput = Tc2;

  
  myPID.Compute();

  
  if (pidOutput > 0) {
    coolingMode(); 
  } else {
    heatingMode(); 

  // calculo de flujo mediante los sensores
  if (millis() - oldTime > 1000) {
    oldTime = millis();
    
    flowRate1 = (flowPulses1 / 7.5) * 60; 
    flowRate2 = (flowPulses2 / 7.5) * 60; 

    flowPulses1 = 0;  
    flowPulses2 = 0;

    // lectura de presion
    int sensorVal = analogRead(pressureSensorPin);
    float voltage = (sensorVal * 5.0) / 1024.0;
    float pressure_psi = (voltage >= 0.5) ? (voltage - 0.5) * (30.0 / (4.5 - 0.5)) : 0.0;

    Serial.print(Tc1);
    Serial.print(",");
    Serial.print(Tc2);
    Serial.print(",");
    Serial.print(flowRate1);
    Serial.print(",");
    Serial.print(flowRate2);
    Serial.print(",");
    Serial.println(pressure_psi);
  }

  
  analogWrite(ssrPin, abs(pidOutput)); 

  delay(1000); 
}


void flowSensor1Pulse() {
  flowPulses1++;
}

void flowSensor2Pulse() {
  flowPulses2++;
}

// temperatura 
float readThermistor(int thermistorPin, float seriesResistor) {
  int Vo = analogRead(thermistorPin);
  float R2 = seriesResistor * (1023.0 / (float)Vo - 1.0);
  float logR2 = log(R2);
  float T = (1.0 / (c1 + c2 * logR2 + c3 * logR2 * logR2 * logR2));
  float Tc = T - 273.15;  
  return Tc;
}

// modo de enfriamiento
void coolingMode() {
  
  digitalWrite(relay1Pin, LOW);
  digitalWrite(relay2Pin, LOW);
  
  digitalWrite(relay1Pin, LOW);
  digitalWrite(relay2Pin, HIGH);
}

// modo de calentamiento
void heatingMode() {
  
  digitalWrite(relay1Pin, LOW);
  digitalWrite(relay2Pin, LOW);
  

  digitalWrite(relay1Pin, HIGH);
  digitalWrite(relay2Pin, LOW);
}
