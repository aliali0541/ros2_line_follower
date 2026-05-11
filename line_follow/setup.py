from setuptools import find_packages, setup

package_name = 'line_follow'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ali',
    maintainer_email='zeroa0541@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            "obstacle_avoider_node = line_follow.obstacle_avoider_node:main",
            "line_controller_node = line_follow.line_controller_node:main",
            "cmd_mux_node = line_follow.cmd_mux_node:main",
            "lap_monitor_node = line_follow.lap_monitor_node:main"
        ],
    },
)
