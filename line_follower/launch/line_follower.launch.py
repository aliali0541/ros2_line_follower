from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    return LaunchDescription([

        Node(
            package='line_follower',
            executable='line_controller_node',
            name='line_controller_node',
            output='screen',

            parameters=[
                'config/pid_params.yaml'
            ]
        ),
         Node(
            package='line_follower',
            executable='odometry_node',
            name='odometry_node',
            output='screen',

            
        ),
        Node(
            package='line_follower',
            executable='lap_detector_node',
            name='lap_detector_node',
            output='screen',

            
        )


    ])