#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range
from geometry_msgs.msg import Twist
import time

class ObstacleAvoiderNode(Node):
    def __init__(self):
        super().__init__('obstacle_avoider_node')
        self.get_logger().info('Obstacle Avoider Node has been started.')


        self.obstacle_distance_threshold = 0.25 #meter
        self.avoiding_ = False # are u in the process of avoiding an obstacle?

        
        #creating publisher 
        self.cmd_vel_safe_=self.create_publisher(
            Twist, '/cmd_vel_safe', 10)

        #creating subscriber
        self.obstacle_subscriber_=self.create_subscription(
            Range, '/obstacle', self.obstacle_callback, 10)


      

    def obstacle_callback(self, msg: Range):
        # if there is an obstacle within the threshold distance and we are not already avoiding, start the arc maneuver
        if msg.range < self.obstacle_distance_threshold and not self.avoiding_:
            self.get_logger().warn('Obstacle detected! Starting Arc Maneuver...')
            self.execute_arc_maneuver()
        
        # if there is no obstacle and we are not already avoiding, publish a "free road" message to the Mux
        elif not self.avoiding_:
            free_msg = Twist()
            free_msg.linear.x = 1.0 # code for the Mux indicating the road is clear
            self.cmd_vel_safe_.publish(free_msg)

    def execute_arc_maneuver(self):

        self.avoiding_ = True
        
        arc_msg = Twist()
        
        #stage 1
        arc_msg.linear.x = 0.2
        arc_msg.angular.z = 0.8
        self.cmd_vel_safe_.publish(arc_msg)
        time.sleep(2.0) 

        # stage 2
        arc_msg.linear.x = 0.2
        arc_msg.angular.z = 0.0
        self.cmd_vel_safe_.publish(arc_msg)
        time.sleep(1.5)

        # stage 3
        arc_msg.linear.x = 0.1
        arc_msg.angular.z = -0.8 
        self.cmd_vel_safe_.publish(arc_msg)
        time.sleep(2.0)

        self.get_logger().info('Maneuver complete. Searching for line...')
        self.avoiding_ = False

def main(args=None):
    rclpy.init(args=args)
    node = ObstacleAvoiderNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()


