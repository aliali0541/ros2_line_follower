// ============================================================
// ESP32 micro-ROS Line Follower + Encoders
// ESP32 = MUSCLES
// ROS2 = BRAIN
// ============================================================

#include <WiFi.h>
#include <micro_ros_arduino.h>

#include <rcl/rcl.h>
#include <rcl/error_handling.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>

#include <std_msgs/msg/int32_multi_array.h>
#include <geometry_msgs/msg/vector3.h>

// ============================================================
// WIFI CONFIG
// ============================================================

#define WIFI_SSID     "3AZA"
#define WIFI_PASSWORD "Tarek123456789#"
#define AGENT_IP      "192.168.1.69"
#define AGENT_PORT    8888

IPAddress local_IP(192, 168, 1, 75);
IPAddress gateway(192, 168, 1, 1);
IPAddress subnet(255, 255, 255, 0);

// ============================================================
// MOTOR PINS
// ============================================================

#define IN1 16
#define IN2 17
#define ENA 4

#define IN3 5
#define IN4 14
#define ENB 23

// ============================================================
// SENSOR PINS
// ============================================================

#define S0 34
#define S1 35
#define S2 32
#define S3 33
#define S4 25

// ============================================================
// ENCODER PINS
// ============================================================

#define ENCODER_LEFT  18
#define ENCODER_RIGHT 19

// ============================================================
// ULTRASONIC + BUZZER (ADDED ONLY)
// ============================================================

#define TRIG_PIN 26
#define ECHO_PIN 27
#define BUZZER_PIN 13   // changed to safe pin

const float OBSTACLE_DISTANCE = 25.0; // cm
bool obstacle_detected = false;

// ============================================================
// ENCODER VARIABLES
// ============================================================

volatile long left_ticks = 0;
volatile long right_ticks = 0;

// ============================================================
// micro-ROS
// ============================================================

rcl_publisher_t sensor_pub;
rcl_publisher_t encoder_pub;

rcl_subscription_t motor_sub;

std_msgs__msg__Int32MultiArray sensor_msg;
std_msgs__msg__Int32MultiArray encoder_msg;

geometry_msgs__msg__Vector3 motor_msg;

rclc_executor_t executor;
rclc_support_t support;
rcl_allocator_t allocator;
rcl_node_t node;

// ============================================================
// SAFETY TIMEOUT
// ============================================================

unsigned long last_cmd_time = 0;
const unsigned long CMD_TIMEOUT_MS = 500;

// ============================================================

#define RCCHECK(fn) \
{ \
  rcl_ret_t temp_rc = fn; \
  if ((temp_rc != RCL_RET_OK)) { \
    error_loop(); \
  } \
}

// ============================================================
// ENCODER INTERRUPTS
// ============================================================

void IRAM_ATTR leftEncoderISR()
{
  left_ticks++;
}

void IRAM_ATTR rightEncoderISR()
{
  right_ticks++;
}

// ============================================================

void stopMotors();

// ============================================================

void error_loop()
{
  stopMotors();

  while (1)
  {
    Serial.println("micro-ROS Error");
    delay(1000);
  }
}

// ============================================================
// ULTRASONIC FUNCTION (ADDED)
// ============================================================

float readDistanceCM()
{
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 30000);

  float distance = duration * 0.034 / 2.0;

  return distance;
}

// ============================================================
// SAFETY CHECK (ADDED)
// ============================================================

void safetyCheck()
{
  float dist = readDistanceCM();

  if (dist > 0 && dist < OBSTACLE_DISTANCE)
  {
    obstacle_detected = true;

    stopMotors();
    digitalWrite(BUZZER_PIN, HIGH);
  }
  else
  {
    obstacle_detected = false;
    digitalWrite(BUZZER_PIN, LOW);
  }
}

// ============================================================
// MOTOR COMMAND CALLBACK
// ============================================================

void motor_callback(const void * msgin)
{
  const geometry_msgs__msg__Vector3 * msg =
    (const geometry_msgs__msg__Vector3 *)msgin;

  int leftPWM  = (int)msg->x;
  int rightPWM = (int)msg->y;

  last_cmd_time = millis();

  // BLOCK MOTORS IF OBSTACLE
  if (obstacle_detected)
  {
    stopMotors();
    return;
  }

  setLeftMotor(leftPWM);
  setRightMotor(rightPWM);
}

// ============================================================
// SETUP
// ============================================================

void setup()
{
  Serial.begin(115200);

  // MOTOR PINS
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  // SENSOR PINS
  pinMode(S0, INPUT);
  pinMode(S1, INPUT);
  pinMode(S2, INPUT);
  pinMode(S3, INPUT);
  pinMode(S4, INPUT);

  // ENCODERS
  pinMode(ENCODER_LEFT, INPUT_PULLUP);
  pinMode(ENCODER_RIGHT, INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(ENCODER_LEFT), leftEncoderISR, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENCODER_RIGHT), rightEncoderISR, CHANGE);

  // ULTRASONIC + BUZZER (ADDED)
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);

  // PWM
  ledcAttach(ENA, 1000, 8);
  ledcAttach(ENB, 1000, 8);

  stopMotors();

  // WIFI
  if (!WiFi.config(local_IP, gateway, subnet))
  {
    Serial.println("Static IP Failed");
  }

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  WiFi.setSleep(false);

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi Connected");

  set_microros_wifi_transports(
    (char*)WIFI_SSID,
    (char*)WIFI_PASSWORD,
    (char*)AGENT_IP,
    AGENT_PORT
  );

  delay(2000);

  allocator = rcl_get_default_allocator();

  RCCHECK(rclc_support_init(&support, 0, NULL, &allocator));

  RCCHECK(rclc_node_init_default(
    &node,
    "esp32_line_follower",
    "",
    &support
  ));

  RCCHECK(rclc_publisher_init_best_effort(
    &sensor_pub,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32MultiArray),
    "/line_error"
  ));

  RCCHECK(rclc_publisher_init_best_effort(
    &encoder_pub,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32MultiArray),
    "/odom"
  ));

  RCCHECK(rclc_subscription_init_best_effort(
    &motor_sub,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Vector3),
    "/cmd_vel"
  ));

  sensor_msg.data.data = (int32_t*)malloc(5 * sizeof(int32_t));
  sensor_msg.data.size = 5;
  sensor_msg.data.capacity = 5;

  encoder_msg.data.data = (int32_t*)malloc(2 * sizeof(int32_t));
  encoder_msg.data.size = 2;
  encoder_msg.data.capacity = 2;

  RCCHECK(rclc_executor_init(&executor, &support.context, 1, &allocator));

  RCCHECK(rclc_executor_add_subscription(
    &executor,
    &motor_sub,
    &motor_msg,
    &motor_callback,
    ON_NEW_DATA
  ));

  Serial.println("ESP32 Ready");
}

// ============================================================
// LOOP
// ============================================================

void loop()
{
  // SAFETY FIRST
  safetyCheck();

  sensor_msg.data.data[0] = digitalRead(S0);
  sensor_msg.data.data[1] = digitalRead(S1);
  sensor_msg.data.data[2] = digitalRead(S2);
  sensor_msg.data.data[3] = digitalRead(S3);
  sensor_msg.data.data[4] = digitalRead(S4);

  encoder_msg.data.data[0] = left_ticks;
  encoder_msg.data.data[1] = right_ticks;

  rcl_publish(&sensor_pub, &sensor_msg, NULL);
  rcl_publish(&encoder_pub, &encoder_msg, NULL);

  rclc_executor_spin_some(&executor, RCL_MS_TO_NS(1));

  if (millis() - last_cmd_time > CMD_TIMEOUT_MS)
  {
    stopMotors();
  }

  delay(10);
}

// ============================================================
// MOTOR FUNCTIONS
// ============================================================

void setLeftMotor(int pwm)
{
  pwm = constrain(pwm, -255, 255);

  if (pwm > 0)
  {
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
  }
  else if (pwm < 0)
  {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
  }
  else
  {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, LOW);
  }

  ledcWrite(ENA, abs(pwm));
}

void setRightMotor(int pwm)
{
  pwm = constrain(pwm, -255, 255);

  if (pwm > 0)
  {
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
  }
  else if (pwm < 0)
  {
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
  }
  else
  {
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, LOW);
  }

  ledcWrite(ENB, abs(pwm));
}

void stopMotors()
{
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);

  ledcWrite(ENA, 0);
  ledcWrite(ENB, 0);
}
