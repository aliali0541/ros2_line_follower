#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class CmdMuxNode(Node):
    def __init__(self):
        super().__init__('cmd_mux_node')
        self.get_logger().info('Cmd Mux Node has been started.')

        #state variable to track if we are currently avoiding an obstacle
        self.avoiding = False

        # creating publisher
        self.cmd_vel_ = self.create_publisher(
            Twist, '/cmd_vel', 10)

        # creating subscriber
        self.cmd_vel_safe_subscriber_ = self.create_subscription(
            Twist, '/cmd_vel_safe', self.cmd_vel_safe_callback, 10)
        
        self.cmd_vel_line_subscriber_ = self.create_subscription(
            Twist, '/cmd_vel_line', self.cmd_vel_line_callback, 10)
        

    def cmd_vel_safe_callback(self, msg: Twist):

        # if obstacle avoider is turning -> we are avoiding
            if msg.angular.z != 0.0:
                self.avoiding = True
                self.cmd_vel_.publish(msg)

        # if it sends straight motion -> obstacle finished
            else:
                self.avoiding = False



    def cmd_vel_line_callback(self, msg: Twist):

        # only publish line follower if NOT avoiding
            if not self.avoiding:
                self.cmd_vel_.publish(msg)

 

def main(args=None):
    rclpy.init(args=args)
    node = CmdMuxNode()
    rclpy.spin(node)
    rclpy.shutdown()
