import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from std_msgs.msg import Float32
import math

class LapCompletePublisher(Node):
    def __init__(self):
        super().__init__('lap_monitor_node')
        
        self.get_logger().info('The node has been initiated!')

        # Configuration Parameters.

        self.declare_parameter('start_radius', 0.2) 
        self.declare_parameter('leave_radius', 0.5) 
        
        # State Variables for Memory.
        self.has_left_start = False
        self.lap_count = 0
        self.lap_start_time = None 
        
        # Subscriber
        self.odom_sub = self.create_subscription(
            Odometry, 
            '/odom', 
            self.odom_callback, 
            10
        )
        
        # Publisher
        self.lap_pub = self.create_publisher(Float32, '/lap_complete', 10)

    def odom_callback(self, msg):
        current_time = self.get_clock().now()
        
        # Start the clock on the very first odometry message
        # Modified logic to start timer ONLY when robot first moves 1cm
        
        # Extract current coordinates
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        
        # Calculate straight-line distance to (0,0)
        distance = math.sqrt(x**2 + y**2)
        
        start_r = self.get_parameter('start_radius').value
        leave_r = self.get_parameter('leave_radius').value

        if self.lap_start_time is None:
            if distance > 0.01: # Has it moved at least 1cm?
                self.lap_start_time = current_time
                self.get_logger().info('Movement detected! Timer started.')
            return
        
        # --- STATE MACHINE LOGIC ---
        
        # Check if the robot has moved far enough away to start a lap
        if not self.has_left_start and distance > leave_r:
            self.has_left_start = True
            self.get_logger().info('Robot has left the start zone. Counting...')
            
        # Check if the robot has returned to the start zone after leaving
        elif self.has_left_start and distance < start_r:
            # Calculate the time it took
            duration = (current_time - self.lap_start_time).nanoseconds / 1e9
            self.lap_count += 1
            
            # Log the result
            self.get_logger().warn(f'Lap {self.lap_count} Complete! Time: {duration:.2f}s')
            
            # Publish the time to /lap_complete
            time_msg = Float32()
            time_msg.data = duration
            self.lap_pub.publish(time_msg)
            
            # Reset state for the next lap
            self.has_left_start = False 
            self.lap_start_time = current_time 

def main(args=None):
    rclpy.init(args=args)
    node = LapCompletePublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()