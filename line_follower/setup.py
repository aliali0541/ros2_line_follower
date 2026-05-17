from setuptools import setup
from glob import glob
import os

package_name = 'line_follower'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],

    data_files=[
        # Required for ROS2 to find package
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),

        ('share/' + package_name, ['package.xml']),

        # Launch files
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.py')),

        # Config files (YAML)
        (os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')),
    ],

    install_requires=['setuptools'],

    zip_safe=True,

    maintainer='your_name',
    maintainer_email='your_email@example.com',

    description='ROS2 Line Follower Robot',

    license='MIT',

    entry_points={
        'console_scripts': [
            'line_controller_node = line_follower.line_controller_node:main'
        ],
    },
)
