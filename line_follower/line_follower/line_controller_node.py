import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Vector3
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy


class TunerNode(Node):
    def __init__(self):
        super().__init__('line_controller_node')

        # Declare ROS 2 parameters with default values
        self.declare_parameter('Kp', 10.0)
        self.declare_parameter('Ki', 0.0)
        self.declare_parameter('Kd', 15.0)
        self.declare_parameter('base_speed', 30.0)
        self.declare_parameter('max_speed', 100.0)

        qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE
        )

        # Publishers (Sending to ESP32)
        self.pid_pub = self.create_publisher(Vector3, '/pid_tune', qos)
        self.speed_pub = self.create_publisher(Vector3, '/cmd_vel', qos)

        # Subscriber (Receiving from ESP32)
        self.state_sub = self.create_subscription(Vector3, '/line_error', self.state_callback, qos)

        # Timer to continuously publish parameters (5Hz)
        self.timer = self.create_timer(0.2, self.publish_params)
        
        self.get_logger().info("Line Follower Tuner Node Started.")

    def publish_params(self):
        # Fetch current parameter values
        Kp = self.get_parameter('Kp').value
        Ki = self.get_parameter('Ki').value
        Kd = self.get_parameter('Kd').value
        base_speed = self.get_parameter('base_speed').value
        max_speed = self.get_parameter('max_speed').value

        # Pack and publish PID message
        pid_msg = Vector3()
        pid_msg.x = float(Kp)
        pid_msg.y = float(Ki)
        pid_msg.z = float(Kd)
        self.pid_pub.publish(pid_msg)

        # Pack and publish Speed message
        speed_msg = Vector3()
        speed_msg.x = float(base_speed)
        speed_msg.y = float(max_speed)
        speed_msg.z = 0.0 # Unused in ESP32 currently
        self.speed_pub.publish(speed_msg)

    def state_callback(self, msg):
        # Log the incoming state from ESP32
        self.get_logger().info(f"State -> Error: {msg.x:.2f} | Filtered: {msg.y:.2f} | Integral: {msg.z:.2f}")

def main(args=None):
    rclpy.init(args=args)
    node = TunerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()