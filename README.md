# Lab 2 — ROS 2 robotic arm

## Team members

| Name | Student ID |
| --- | --- |
| Abdelrahman Hassan | 2204044 |
| Ahmed Mohamed Ahmed Ali | 2204297 |
| Hamdy Adel | 2204172 |

This workspace runs a four-joint arm in Gazebo Harmonic and shows its motion in
RViz2. A Python bridge also sends commands over Wi-Fi to two servos on an ESP32.

## Workspace

| Path | Contents |
| --- | --- |
| `src/arm_description` | Xacro model, RViz2 settings, and display launch |
| `src/arm_simulation` | Gazebo world, controller and bridge settings, and full launch |
| `src/arm_control` | Python demo publisher and Tk slider window |
| `src/arm_hardware_bridge` | ROS-to-UDP node and example settings |
| `firmware/arm_firmware` | ESP32 Arduino sketch and example Wi-Fi settings |

## Arm geometry

At zero angles, the base, L1, and L2 stand along +Z. L3, the wrist, and
the tool point along +X. The full side profile is 36.25 cm high and 20 cm
wide, including the base. The wrist and tool together span 6 cm from L3
to the tip. Joint 1 turns about +Z. Joints 2, 3, and 4 turn about their
local +Y axes.

| Link | Length or height (m) | Direction at zero |
| --- | ---: | --- |
| `base_link` | 0.08 | +Z |
| `L1` | 0.12 | +Z |
| `L2` | 0.15 | +Z |
| `L3` | 0.09 | +X |
| `wrist_link` | 0.02 | +X |
| `end_effector` | 0.04 | +X |

The chain is `base_link → joint1 → L1 → joint2 → L2 → joint3 → L3 → joint4
→ wrist_link → tool_mount → end_effector`. Joint 4 turns the wrist.
The end effector is fixed to the wrist so it moves with joint 4.
Each moving joint has a range of −π/2 to +π/2 radians. Each link has a box for
its shape and collision and a small mass with box inertia. In Gazebo the base
is fixed to the world.

## Install and build

Use Ubuntu 24.04, ROS 2 Jazzy, and Gazebo Harmonic. Set up the
[ROS 2 Jazzy package repository](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)
before running these commands.

```bash
sudo apt update
sudo apt install ros-jazzy-desktop ros-jazzy-ros-gz ros-jazzy-gz-ros2-control \
  ros-jazzy-ros2-controllers ros-jazzy-xacro ros-jazzy-urdfdom \
  ros-jazzy-joint-state-publisher python3-colcon-common-extensions python3-tk
cd ~/lab2
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

In each new terminal, run both `source` commands from the workspace. The
Gazebo plugin uses the ROS 2 trajectory controller and joint state broadcaster.
See the [gz_ros2_control guide](https://control.ros.org/jazzy/doc/gz_ros2_control/doc/index.html).

## Run the ROS stages

| Stage | Command |
| --- | --- |
| View the model by itself | `ros2 launch arm_description display.launch.py` |
| Simulate with Gazebo and RViz2 | `ros2 launch arm_simulation sim.launch.py` |
| Open the slider window | `ros2 run arm_control arm_gui` |
| Run the moving demo | `ros2 run arm_control arm_demo` |
| Run the UDP bridge after setting it up | `ros2 run arm_hardware_bridge udp_bridge --ros-args --params-file "$PWD/hardware.local.yaml"` |

Close the model-only launch before running the simulation so only one node
publishes `/joint_states`. Use either the demo or the slider window at a time.

To launch Gazebo, RViz2, the sliders, and the UDP bridge together:

```bash
ros2 launch arm_simulation sim.launch.py gui:=true hardware:=true \
  hardware_config:="$PWD/hardware.local.yaml"
```

For the same desktop demo with no ESP32, use `gui:=true` on its own.
Add `headless:=true rviz:=false` to run the Gazebo server without either viewer.

## ESP32 setup

Use a classic ESP32 development board with GPIO 18 and GPIO 19 available.
In Arduino IDE, install the **esp32 by Espressif Systems** board package and
the **ESP32Servo** library. Pick your board and USB port from the Tools menu.

| ESP32 pin | Servo connection |
| --- | --- |
| GPIO 18 | Joint 1 signal wire |
| GPIO 19 | Joint 2 signal wire |
| GND | Both servo grounds and the external supply ground |

Use an external power supply rated for your servos. Connect the servo power
wires to that supply and share ground with the ESP32.

1. Copy `firmware/arm_firmware/wifi_config.example.h` to
   `firmware/arm_firmware/wifi_config.h`. Enter your Wi-Fi name and password
   there.
2. Open `firmware/arm_firmware/arm_firmware.ino`, upload it, and open the Serial
   Monitor at 115200 baud. Read the ESP32's IP address after it joins Wi-Fi.
3. On the ROS computer, copy
   `src/arm_hardware_bridge/config/hardware.example.yaml` to
   `hardware.local.yaml` in the workspace root. Fill in `esp32_ip`. Use the
   same UDP port in both config files. Keep both devices on the same network.

Git ignores the two local config files. The example files contain placeholders.

## UDP message

The bridge sends one ASCII datagram per command to UDP port 4210 by default.
The format is four decimal integers separated by commas, followed by one LF
byte. For example, `90,45,120,10\n` sends 90° and 45° to the two real servos.
The firmware checks all four fields and uses the first two. Values outside
0–180 are limited to that range. Bad packets are ignored.

`servo_joints` sets the joint order in the four UDP fields. The default is
`[joint1, joint2, joint3, joint4]`. The bridge takes the final point in each
trajectory and maps −π/2, 0, and +π/2 radians to 0°, 90°, and 180°. The ESP32
applies that target as soon as it receives the packet. Gazebo moves along the
timed trajectory. The real servo positions are open loop.

## Test the project

### Check the model

```bash
xacro src/arm_description/urdf/arm.urdf.xacro > build/arm.urdf
check_urdf build/arm.urdf
```

### Check Gazebo and RViz2

Start the simulation. In a second terminal, send one pose.

```bash
ros2 control list_controllers
ros2 topic pub --once /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory \
  '{joint_names: [joint1, joint2, joint3, joint4], points: [{positions: [0.3, -0.25, 0.2, 0.15], time_from_start: {sec: 2}}]}'
ros2 topic echo /joint_states --once
ros2 run tf2_ros tf2_echo base_link end_effector
```

Both controllers should be active. Watch the arm move in both windows. RViz2
uses `base_link` as its fixed frame and reads the robot model and TF from
`robot_state_publisher`. The joint state broadcaster sends Gazebo's measured
positions to `/joint_states`. The bridge config carries only the Gazebo clock.

### Check the full pipeline

1. Start the full launch with `gui:=true hardware:=true`. Wait for both
   controllers to activate.
2. In another terminal, run
   `ros2 topic echo /arm_controller/joint_trajectory`. Move one slider a small
   amount near zero and check that the topic shows four joint names, four
   positions in radians, and a move time.
3. With the servo horns clear, test joint 1 and then joint 2. Check the matching
   real servo and both simulator views for each move. Joints 3 and 4 move in
   Gazebo and RViz2.
4. To check network delivery on the ROS computer, run
   `tcpdump -ni any -A 'udp dst port 4210'` with capture permissions. Confirm
   the four angles and the final newline. Change the filter if you changed the
   port.

## Verification checklist

| Check | Result |
| --- | --- |
| Four revolute joints, link sizes, and fixed tool | Checked with `check_urdf` and the generated XML |
| Visual, collision, and inertial on every link | Checked in both versions of the generated XML |
| Model loads in Gazebo and displays in RViz2 | Tested on the desktop |
| One trajectory command moves the arm in Gazebo and RViz2 | Checked Gazebo joint positions and the RViz2 view before and after a command |
| Python demo and sliders publish valid trajectories | Tested with the Gazebo controller and a local UDP receiver |
| Hardware bridge builds and runs | Built with `colcon` and checked the exact UDP bytes on localhost |
| Firmware packet parser | Tested with valid, out-of-range, and bad messages on the computer |
| ESP32 firmware and two real servos | Compile and upload in Arduino IDE, then test both servos on the board |
| Full demo with hardware | Repeat the full launch with the ESP32 and watch both servos |
