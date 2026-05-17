# ROS 2 Line Follower

This repository contains the high-level ROS 2 (Humble) control software for a hybrid ESP32/ROS 2 line-following robot. It handles dynamic PID line tracking, odometry calculation, and track lap detection.

## System Architecture

The package is broken down into modular nodes for clean separation of concerns:

* **`line_controller_node`**: The core brain of the robot. Subscribes to line sensor data (weighted centroid) and computes the required `/cmd_vel` using a tuned PID controller.
* **`odometry_node`**: Subscribes to wheel encoder ticks from the microcontroller and computes the robot's pose and trajectory using differential-drive kinematics.
* **`lap_detector_node`**: Monitors the robot's coordinates to detect when it has successfully returned to its starting position and completed a lap.

### Additional Tools
* **Config (`pid_params.yaml`)**: Centralized configuration file for live-tuning PID gains and speed limits without recompiling.
* **Plotting (`trajectory.py`)**: A standalone Python tool used to visualize the robot's odometry and driven path.


## Prerequisites

Before building this package, ensure your host machine meets the following requirements:
* **Operating System:** Ubuntu 22.04 LTS (Jammy Jellyfish)
* **Framework:** ROS 2 Humble Hawksbill (Desktop Install recommended)
* **Build Tools:** `colcon` and `rosdep` initialized


## Installation & Build Instructions

This package is designed to be built in a standard ROS 2 workspace using `colcon`.

**1. Create a workspace (if you don't have one):**
```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
```

**2. Clone this repository:**
```bash
git clone https://github.com/aliali0541/ros2_line_follower.git
```

**3. Install dependencies:**
```bash
cd ~/ros2_ws
rosdep update
rosdep install --from-paths src --ignore-src -r -y
```

**4. Build the package:**
```bash
colcon build --packages-select line_follower
```

**5. Source the workspace:**
```bash
source install/setup.bash
```


> [!tip] Add `source ~/ros2_ws/install/setup.bash` to your `~/.bashrc` to do this automatically).



## Usage

**Launch the Entire System:** To spin up the line controller, odometry, lap detector, and load the PID parameters simultaneously, use the provided launch file:
```bash
ros2 launch line_follower line_follower.launch.py
```

**Plotting the Trajectory:** After running the robot and recording odometry data, you can visualize the path by running:
```bash
python3 src/ros2_line_follower/line_follower/plot/trajectory.py
```


<p align="center">
  <img src="https://miro.medium.com/v2/resize:fit:640/format:webp/0*Eu4dXHrukJQmo_4o.gif" alt="Centered GIF">
</p>
