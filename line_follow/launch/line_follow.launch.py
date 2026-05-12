"""
line_follow.launch.py
=====================
ROS 2 Humble launch file for the Line-Following Robot project.

Launches:
  - line_controller_node   : PID controller (line_error → cmd_vel)
  - obstacle_avoider_node  : State-machine obstacle avoidance
  - lap_monitor_node       : Lap timing + buzzer/LED signal
  - cmd_mux_node           :

All tunable gains are exposed as ROS parameters and can be
overridden at launch time or via the YAML config file.

Usage:
  # Default launch
  ros2 launch line_follow line_follow.launch.py

  # Override a single gain at the command line
  ros2 launch line_follow line_follow.launch.py kp:=1.5 base_speed:=0.18

  # Load your own config file
  ros2 launch line_follow line_follow.launch.py \
      config_file:=/path/to/my_gains.yaml
"""

import os
from ament_index_python.packages import get_package_share_directory  # type: ignore
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # ------------------------------------------------------------------ #
    #  Locate the default config file shipped with the package           #
    # ------------------------------------------------------------------ #
    pkg_share = FindPackageShare("line_follow")
    default_config = PathJoinSubstitution([pkg_share, "config", "pid_gains.yaml"])

    # ------------------------------------------------------------------ #
    #  Declare every tunable parameter as a launch argument              #
    #  so the user can override from the CLI without editing code.       #
    # ------------------------------------------------------------------ #
    declare_config_file = DeclareLaunchArgument(
        "config_file",
        default_value=default_config,
        description="Path to YAML file containing PID gains and speeds",
    )

    declare_kp = DeclareLaunchArgument(
        "kp",
        default_value="1.2",
        description="Proportional gain for the PID line controller",
    )
    declare_ki = DeclareLaunchArgument(
        "ki",
        default_value="0.0",
        description="Integral gain (start at 0; add only if steady-state error persists)",
    )
    declare_kd = DeclareLaunchArgument(
        "kd",
        default_value="0.05",
        description="Derivative gain (dampens oscillations on sharp turns)",
    )
    declare_base_speed = DeclareLaunchArgument(
        "base_speed",
        default_value="0.15",
        description="Forward linear velocity [m/s] while following the line",
    )
    declare_max_angular = DeclareLaunchArgument(
        "max_angular",
        default_value="2.0",
        description="Maximum allowed angular velocity [rad/s]",
    )
    declare_obstacle_threshold = DeclareLaunchArgument(
        "obstacle_distance_threshold",
        default_value="0.25",
        description="Distance [m] below which obstacle avoidance triggers",
    )

    declare_avoiding_ = DeclareLaunchArgument(
        "__avoiding__",
        default_value="0.0",
        description="choosing the right cmd_Vel to publish",
    )

    # ------------------------------------------------------------------ #
    #  Convenient handles to every argument value                        #
    # ------------------------------------------------------------------ #
    kp          = LaunchConfiguration("kp")
    ki          = LaunchConfiguration("ki")
    kd          = LaunchConfiguration("kd")
    base_speed  = LaunchConfiguration("base_speed")
    max_angular = LaunchConfiguration("max_angular")
    obs_thresh  = LaunchConfiguration("obstacle_distance_threshold")
    __avoiding__= LaunchConfiguration("__avoiding__")

    # ------------------------------------------------------------------ #
    #  Node 1 — line_controller_node                                     #
    #  Subscribes : /line_error  (std_msgs/Float32)                      #
    #  Publishes  : /cmd_vel_line     (geometry_msgs/Twist)              #
    # ------------------------------------------------------------------ #
    line_controller = Node(
        package="line_follow",
        executable="line_controller_node",
        name="line_controller_node",
        output="screen",
        parameters=[
            # Load gains from YAML first …
            LaunchConfiguration("config_file"),
            # … then CLI overrides win (later dict entries shadow YAML).
            {
                "kp": kp,
                "ki": ki,
                "kd": kd,
                "base_speed": base_speed,
                "max_angular": max_angular,
            },
        ],
        remappings=[
            # If your ESP32 publishes on a different topic, remap here:
            # ("/line_error", "/robot/line_error"),
        ],
    )

    # ------------------------------------------------------------------ #
    #  Node 2 — obstacle_avoider_node                                     #
    #  Subscribes : /obstacle   (std_msgs/Float32 — distance in metres)  #
    #                                                                     #
    #  Publishes  : /cmd_vel_safe  (overrides controller during avoidance)#
    # ------------------------------------------------------------------ #
    obstacle_avoider = Node(
        package="line_follow",
        executable="obstacle_avoider_node",
        name="obstacle_avoider_node",
        output="screen",
        parameters=[
            LaunchConfiguration("config_file"),
            {
                "obstacle_distance_threshold": obs_thresh,
                "base_speed": base_speed,
                "max_angular": max_angular,
            },
        ],
    )

     # ----------------------------------------------------------------- #
    #  Node 3 — cmd_mux_node                                             #
    #  Subscribes : /cmd_vel_line  (geometry_msgs/msg/Twist)             #
    #               /cmd_vel_safe  (geometry_msgs/msg/Twist)             #
    #  Publishes  : /lap_complete (std_msgs/Bool)                        #
    # ------------------------------------------------------------------ #
    cmd_mux = Node(
        package="line_follow",
        executable="cmd_mux_node",
        name="cmd_mux_node",
        output="screen",
        parameters=[
            LaunchConfiguration("config_file"),
            {
                
                "__avoiding__": __avoiding__,
                
                
            },
        ],
    )


    # ------------------------------------------------------------------ #
    #  Node 4 — lap_monitor_node                                          #
    #  Subscribes : /odom  (nav_msgs/Odometry)                            #
    #  Publishes  : /lap_complete (std_msgs/Bool)                         #
    # ------------------------------------------------------------------ #
    lap_monitor = Node(
        package="line_follow",
        executable="lap_monitor_node",
        name="lap_monitor_node",
        output="screen",
        parameters=[
            LaunchConfiguration("config_file"),
            {
                # How close (metres) to start pose counts as lap completion
                "lap_completion_radius": 0.15,
                # Minimum travel distance before lap detection is armed (m)
                "min_lap_distance": 0.5,
            },
        ],
    )
     

     
    # ------------------------------------------------------------------ #
    #  Assemble the LaunchDescription                                     #
    # ------------------------------------------------------------------ #
    return LaunchDescription(
        [
            # Argument declarations (must come first)
            declare_config_file,
            declare_kp,
            declare_ki,
            declare_kd,
            declare_base_speed,
            declare_max_angular,
            declare_obstacle_threshold,
            declare_avoiding_,

            # Informational banner printed at launch
            LogInfo(msg="========== Line-Follow Robot Launching =========="),
            LogInfo(msg=["PID gains  →  kp=", kp, "  ki=", ki, "  kd=", kd]),
            LogInfo(msg=["base_speed=", base_speed, "  max_angular=", max_angular]),
            LogInfo(msg=["Obstacle threshold=", obs_thresh, " m"]),
            LogInfo(msg="================================================="),

            # Nodes
            line_controller,
            obstacle_avoider,
            lap_monitor,
            cmd_mux,

        ]
    )
