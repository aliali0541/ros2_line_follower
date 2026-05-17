#!/usr/bin/env python3

import rclpy
import math

from rclpy.node import Node
from std_msgs.msg import Int32MultiArray
from geometry_msgs.msg import Vector3
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy


class SimpleOdometry(Node):

    def __init__(self):

        super().__init__('simple_odometry')
        
        # ROBOT PARAMETERS

        self.ticks_per_rev = 48
        self.wheel_radius = 0.03
        self.wheel_base = 0.14
        qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE)
        
        self.last_left = 0
        self.last_right = 0

        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0

        

        self.create_subscription(
            Int32MultiArray,
            '/odom',
            self.tick_callback,
            qos
        )

        
        # Odom Publisher

        self.odom_pub = self.create_publisher(
            Vector3,
            '/odom_simple',
            10
        )

        self.get_logger().info("Odometry Node Started")

    

    def tick_callback(self, msg):

        left = msg.data[0]
        right = msg.data[1]

        # tick delta
        d_left_ticks = left - self.last_left
        d_right_ticks = right - self.last_right

        self.last_left = left
        self.last_right = right

        # convert to meters
        d_left = (
            2 * math.pi * self.wheel_radius
            * d_left_ticks
            / self.ticks_per_rev
        )

        d_right = (
            2 * math.pi * self.wheel_radius
            * d_right_ticks
            / self.ticks_per_rev
        )

        # center movement
        d_center = (d_left + d_right) / 2.0

        # heading
        d_theta = (
            d_right - d_left
        ) / self.wheel_base

        # update pose
        self.theta += d_theta

        self.x += d_center * math.cos(self.theta)
        self.y += d_center * math.sin(self.theta)
        
        # Publish Odom        

        odom_msg = Vector3()
        odom_msg.x = self.x
        odom_msg.y = self.y
        odom_msg.z = self.theta

        self.odom_pub.publish(odom_msg)


def main(args=None):

    rclpy.init(args=args)

    node = SimpleOdometry()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()