#!/usr/bin/env python3

import rclpy
import math
import time

from rclpy.node import Node
from geometry_msgs.msg import Vector3


class RaceAnalyzer(Node):

    def __init__(self):

        super().__init__('lap_detector_node')

        # ================= STATE =================

        self.start_x = None
        self.start_y = None

        self.last_lap_time = None
        self.lap_count = 0

        self.in_start_zone = False

        # trajectory storage
        self.trajectory = []

        # ================= SUB =================

        self.create_subscription(
            Vector3,
            '/odom_simple',
            self.callback,
            1
        )

        self.get_logger().info("lap_detecor_node Started")

    # =====================================================

    def callback(self, msg):

        x = msg.x
        y = msg.y

        # ================= INIT START POINT =================

        if self.start_x is None:

            self.start_x = x
            self.start_y = y

            self.last_lap_time = time.time()

            self.get_logger().info("Start position set")

            return

        # ================= STORE TRAJECTORY =================

        self.trajectory.append((x, y))

        # ================= DIST FROM START =================

        dist = math.sqrt(
            (x - self.start_x)**2 +
            (y - self.start_y)**2
        )

        # ================= LAP DETECTION =================

        START_ZONE = 0.30  # meters

        if dist < START_ZONE:

            if not self.in_start_zone:

                self.lap_count += 1

                now = time.time()
                lap_time = now - self.last_lap_time
                self.last_lap_time = now

                self.get_logger().info(
                    f"🏁 LAP {self.lap_count} TIME: {lap_time:.2f}s"
                )

            self.in_start_zone = True

        else:

            self.in_start_zone = False

    # =====================================================

    def save_trajectory(self):

        file_name = "trajectory.csv"

        with open(file_name, "w") as f:

            for x, y in self.trajectory:

                f.write(f"{x},{y}\n")

        self.get_logger().info("Trajectory saved to CSV")


# =====================================================

def main():

    rclpy.init()

    node = RaceAnalyzer()

    try:

        rclpy.spin(node)

    except KeyboardInterrupt:

        node.save_trajectory()

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()