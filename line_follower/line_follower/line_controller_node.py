#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import SetParametersResult
from std_msgs.msg import Int32MultiArray
from geometry_msgs.msg import Vector3
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy

class PIDLineFollower(Node):

    def __init__(self):

        super().__init__('line_controller_node')
        self.get_logger().info("The Node has been initiated!")
        self.last_seen_direction = 0

        # Tuning Parameters.        
        self.declare_parameter('Kp', 25.0)
        self.declare_parameter('Ki', 0.0)
        self.declare_parameter('Kd', 140.0)

        self.declare_parameter('base_speed', 70)
        self.declare_parameter('max_speed', 150)
        self.declare_parameter('recovery_speed', 80)

        self.declare_parameter('alpha', 0.7)
        self.declare_parameter('integral_limit', 20.0)

        qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE
        )
        
        # load parameters.
        self._load_params()

        # live tuning support.
        self.add_on_set_parameters_callback(self.param_callback)

        self.get_logger().info(f"kp:{self.get_parameter('Kp').value}, ki:{self.get_parameter('Ki').value}, kd:{self.get_parameter('Kd').value}")


        # SENSOR WEIGHTS.
        
        self.weights = [-2, -1, 0, 1, 2]

        # State Variables for Memory.
        #         
        self.error = 0.0
        self.filtered_error = 0.0
        self.last_error = 0.0
        self.integral = 0.0

        # Creating Publisher and Subscriber.        
        self.subscription = self.create_subscription(
            Int32MultiArray,
            '/line_error',
            self.sensor_callback,
            qos
        )

        self.motor_pub = self.create_publisher(
            Vector3,
            '/cmd_vel',
            qos
        )

        # Get parameters.
            
    def _load_params(self):

        self.Kp = self.get_parameter('Kp').value
        self.Ki = self.get_parameter('Ki').value
        self.Kd = self.get_parameter('Kd').value

        self.base_speed = self.get_parameter('base_speed').value
        self.max_speed = self.get_parameter('max_speed').value
        self.recovery_speed = self.get_parameter('recovery_speed').value

        self.alpha = self.get_parameter('alpha').value
        self.integral_limit = self.get_parameter('integral_limit').value

        # Update parameters.    
    def param_callback(self, params):

        for p in params:

            if p.name == "Kp":
                self.Kp = p.value

            elif p.name == "Ki":
                self.Ki = p.value

            elif p.name == "Kd":
                self.Kd = p.value

            elif p.name == "base_speed":
                self.base_speed = p.value

            elif p.name == "max_speed":
                self.max_speed = p.value

            elif p.name == "recovery_speed":
                self.recovery_speed = p.value

            elif p.name == "alpha":
                self.alpha = p.value

            elif p.name == "integral_limit":
                self.integral_limit = p.value

        return SetParametersResult(successful=True)
    
    def sensor_callback(self, msg):

        sensors = msg.data

        # Position Calculations.
        
        sum_val = 0      # Weight of active sensors
        active = 0       # NO. sensors that read black.

        for i in range(5):

            if sensors[i] == 1:
                sum_val += self.weights[i]
                active += 1

        # LOST LINE HANDLING
        
        if active == 0:

            if self.last_seen_direction == 0:
                self.publish_motor(0,0)

            elif self.last_seen_direction > 0.0:
                self.publish_motor(self.recovery_speed,0)
                
            else:
                self.publish_motor(0, self.recovery_speed)
            
            return

        # ERROR Calculations.
        
        self.error = sum_val / active

        if self.error > 0:
            self.last_seen_direction = 1
        elif self.error < 0:
            self.last_seen_direction = -1     

        # FILTERING.
        
        self.filtered_error = (
            self.alpha * self.filtered_error
            + (1 - self.alpha) * self.error
        )

        # PID Calculations.
        
        self.integral += self.filtered_error

        # anti-windup.
        self.integral = max(
            min(self.integral, self.integral_limit),
            -self.integral_limit
        )

        derivative = self.filtered_error - self.last_error

        correction = (
            self.Kp * self.filtered_error
            +
            self.Ki * self.integral
            +
            self.Kd * derivative
        )

        self.last_error = self.filtered_error

        # Motor Speed Calculations.
        
        left_speed = int(self.base_speed + correction)
        right_speed = int(self.base_speed - correction)

        # Safety clamp.
        left_speed = max(min(left_speed, self.max_speed), -self.max_speed)
        right_speed = max(min(right_speed, self.max_speed), -self.max_speed)

                
        self.publish_motor(left_speed, right_speed)
    
    def publish_motor(self, left, right):

        msg = Vector3()
        msg.x = float(left)
        msg.y = float(right)

        self.motor_pub.publish(msg)

        # DEBUG.
    
    # def debug(self, left, right):
    #     self.get_logger().info(
    #         f"Err:{self.filtered_error:.2f} L:{left} R:{right}"
    #     )

def main(args=None):

    rclpy.init(args=args)

    node = PIDLineFollower()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()