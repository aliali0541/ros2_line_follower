#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
from geometry_msgs.msg import Twist

class LineControllerNode(Node):
    def __init__(self):
        super().__init__('line_controller_node')
        self.get_logger().info("The Node has been initiated!")
        
        # Tuning Parameters.
        self.declare_parameter('kp', 1.0)
        self.declare_parameter('ki', 0.0)
        self.declare_parameter('kd', 0.1)
        self.declare_parameter('base_speed', 0.2)
        self.declare_parameter('max_brake_ratio', 0.5)
        
        # State Variables for Memory.
        self.prev_error = 0.0
        self.integral = 0.0
        self.prev_time = self.get_clock().now()
        
        # Creating Publisher and Subscriber.
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel_line', 10)
        self.error_sub = self.create_subscription(Float32, '/line_error', self.error_callback, 10)

    def error_callback(self, msg):
        # Get current time and calculate delta time (dt) in seconds.
        current_time = self.get_clock().now()
        dt = (current_time - self.prev_time).nanoseconds / 1e9
        
        # Prevent division by zero on the very first loop.
        if dt <= 0.0:
            return
            
        current_error = msg.data
        
        # IF incoming error was over +-2, robot stops and spins around to find the line.
        if abs(current_error) > 2.0:
            twist_msg = Twist()
            twist_msg.linear.x = 0.0
            self.get_logger().warn('Line lost! Executing emergency recovery spin.')            
            if current_error > 0.0:
                twist_msg.angular.z = 0.5  
            else:
                twist_msg.angular.z = -0.5 
                
            self.cmd_pub.publish(twist_msg)
            self.prev_time = current_time 
            return
        
        # Get parameters.
        kp = self.get_parameter('kp').value
        ki = self.get_parameter('ki').value
        kd = self.get_parameter('kd').value
        base_speed = self.get_parameter('base_speed').value
        max_brake = self.get_parameter('max_brake_ratio').value


        # --- PID CALCULATIONS ---
        
        # Proportional.
        P = kp * current_error
        
        # Integral.
        self.integral += (current_error * dt)
        I = ki * self.integral
        
        windup_limit = 2.0 
        self.integral = max(-windup_limit, min(windup_limit, self.integral))
        
        # Derivative.
        derivative = (current_error - self.prev_error) / dt
        D = kd * derivative
        
        # Total PID Equation.
        steering_command = P + I + D
        
        # --- COMMAND GENERATION ---
        twist_msg = Twist()
        
        twist_msg.linear.x = base_speed * (1.0 - min(abs(current_error), max_brake)) 
        twist_msg.angular.z = steering_command
        self.cmd_pub.publish(twist_msg)
        
        # Update memory for the next loop.
        self.prev_error = current_error
        self.prev_time = current_time

def main(args=None):
    rclpy.init(args=args)
    node = LineControllerNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()