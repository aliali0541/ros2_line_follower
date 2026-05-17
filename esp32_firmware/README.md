# ESP32 micro-ROS Line Follower Firmware

This firmware acts as the "MUSCLES" for a line follower robot, bridging the physical hardware with a ROS 2 "BRAIN" via micro-ROS. It handles motor control, encoder reading, IR line sensor arrays, and includes built-in ultrasonic safety.

## Configuration (Variables to Change)

Before flashing this firmware to your ESP32, you must update the following variables to match your specific network, micro-ROS agent, and robot dimensions.

### 1. WiFi & Network Settings

Update these definitions located at the top of the file:

- `WIFI_SSID`: Your WiFi network name.
    
- `WIFI_PASSWORD`: Your WiFi password.
    
- `AGENT_IP`: The IP address of the machine running the micro-ROS agent.
    
- `AGENT_PORT`: The port for the micro-ROS agent.
    
- `local_IP`: The static IP for the ESP32.
    
- `gateway`: Your network gateway.
    
- `subnet`: Your network subnet mask.

### 2. Safety & Timeouts

- `OBSTACLE_DISTANCE`: The distance in centimeters at which the ultrasonic sensor will stop the motors (currently `25.0`).
    
- `CMD_TIMEOUT_MS`: The time in milliseconds before motors stop if no new `/cmd_vel` message is received (currently `500`).

## Hardware Wiring Guide

### Motors & Encoders

- **Left Motor:** IN1 (Pin `16`), IN2 (Pin `17`), ENA (Pin `4`).
    
- **Right Motor:** IN3 (Pin `5`), IN4 (Pin `14`), ENB (Pin `23`).
    
- **Encoders:** Left Encoder (Pin `18`), Right Encoder (Pin `19`).

### Sensors & Peripherals

- **IR Line Sensor Array:** S0 (`34`), S1 (`35`), S2 (`32`), S3 (`33`), S4 (`25`).
    
- **Ultrasonic Sensor:** TRIG_PIN (`26`), ECHO_PIN (`27`).
    
- **Buzzer:** BUZZER_PIN (`13`).------

## ROS 2 Interface

This node is named `esp32_line_follower`.

### Publishers

- `/line_error`: Publishes an `Int32MultiArray` containing the binary states of the 5 IR sensors.
    
- `/odom`: Publishes an `Int32MultiArray` containing the left and right encoder tick counts.

### Subscriptions

- `/cmd_vel`: Subscribes to a `Vector3` message. The `x` value represents the left motor PWM, and the `y` value represents the right motor PWM.
    

## Built-In Safety Features

- **Obstacle Detection:** If an object is detected within the configured `OBSTACLE_DISTANCE`, the motors are immediately stopped and the buzzer is activated. Motor commands are ignored until the obstacle is cleared.
    
- **Command Timeout:** If the ESP32 loses connection or stops receiving commands for more than `CMD_TIMEOUT_MS`, the motors automatically stop.