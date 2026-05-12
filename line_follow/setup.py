"""
setup.py — ROS 2 Humble Python package build script for line_follow.

Key responsibilities:
  • Registers every node as a console_script so ROS 2 can find it
    via `ros2 run line_follow <node_name>`
  • Installs launch files and config YAML into the ament share dir
    so they are found by `ros2 launch` and parameter loading
  • Installs helper scripts (plot_trajectory.py) into share as well

How colcon uses this file:
  colcon build --symlink-install
    → calls `pip install -e .` under the hood
    → copies/links everything into install/line_follow/
    → after sourcing install/setup.bash the node names are on PATH
"""

from setuptools import find_packages, setup
import os
from glob import glob

PACKAGE_NAME = 'line_follow'

setup(
    name=PACKAGE_NAME,
    version='1.0.0',
    # Automatically discovers the line_follow/ Python sub-package
    packages=find_packages(exclude=['test']),

    # ── Static data files installed into the ament share tree ──────
    data_files=[
        # Required: tells ament this package exists
        ('share/ament_index/resource_index/packages',
            ['resource/' + PACKAGE_NAME]),

        # Required: package manifest
        ('share/' + PACKAGE_NAME, ['package.xml']),

        # Launch files — accessible via ros2 launch line_follow <file>
        ('share/' + PACKAGE_NAME + '/launch',
            glob('launch/*.py')),

        # Config / parameter files — loaded by launch file
        ('share/' + PACKAGE_NAME + '/config',
            glob('config/*.yaml')),

        # Helper scripts (plot, etc.) installed into share
        ('share/' + PACKAGE_NAME + '/scripts',
            glob('scripts/*.py')),
    ],

    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Student Name',
    maintainer_email='student@university.edu',
    description='Line-following robot ROS 2 package with PID, obstacle avoidance, and lap monitoring',
    license='MIT',
    tests_require=['pytest'],

    # ── Console scripts ─────────────────────────────────────────────
    # Format: '<ros2_run_name> = <python_package>.<module>:<entry_function>'
    # These become executable commands after `colcon build` + source.
    entry_points={
        'console_scripts': [
            # PID controller: subscribes /line_error, publishes /cmd_vel
            'line_controller_node = line_follow.line_controller_node:main',

            # Obstacle avoidance FSM: subscribes /obstacle, modifies /cmd_vel
            'obstacle_avoider_node = line_follow.obstacle_avoider_node:main',

            # Obstacle avoidance FSM: subscribes /cmd_vel_line and /cmd_vel_safe, modifies /cmd_vel
            'cmd_mux_node = line_follow.cmd_mux_node:main',

            # Lap monitor: watches /odom, signals lap completion via buzzer
            'lap_monitor_node = line_follow.lap_monitor_node:main',
        ],
    },
)
