from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def start_gazebo(context):
    world = PathJoinSubstitution([FindPackageShare("arm_simulation"), "worlds", "lab2.sdf"])
    server_only = " -s" if IfCondition(LaunchConfiguration("headless")).evaluate(context) else ""
    return [IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([
            FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py",
        ])),
        launch_arguments={"gz_args": ["-r", server_only, " \"", world, "\""]}.items(),
    )]


def generate_launch_description():
    simulation = FindPackageShare("arm_simulation")
    description = FindPackageShare("arm_description")
    model = PathJoinSubstitution([description, "urdf", "arm.urdf.xacro"])
    controllers = PathJoinSubstitution([simulation, "config", "controllers.yaml"])
    robot = ParameterValue(Command([
        FindExecutable(name="xacro"), ' "', model, '" simulation:=true controllers:="',
        controllers, '"',
    ]), value_type=str)
    sim_time = {"use_sim_time": True}
    return LaunchDescription([
        DeclareLaunchArgument("headless", default_value="false", description="Run Gazebo without its window."),
        DeclareLaunchArgument("rviz", default_value="true", description="Open RViz2."),
        DeclareLaunchArgument("gui", default_value="false", description="Open the joint sliders."),
        DeclareLaunchArgument("hardware", default_value="false", description="Run the ESP32 UDP bridge."),
        DeclareLaunchArgument("hardware_config", default_value=PathJoinSubstitution([
            FindPackageShare("arm_hardware_bridge"), "config", "hardware.example.yaml",
        ]), description="Path to the UDP bridge settings."),
        OpaqueFunction(function=start_gazebo),
        Node(package="robot_state_publisher", executable="robot_state_publisher",
             parameters=[sim_time, {"robot_description": robot}]),
        Node(package="ros_gz_bridge", executable="parameter_bridge", parameters=[{
            "config_file": PathJoinSubstitution([simulation, "config", "bridge.yaml"]),
        }]),
        Node(package="ros_gz_sim", executable="create",
             arguments=["-world", "lab2", "-name", "lab2_arm", "-topic", "robot_description"]),
        Node(package="controller_manager", executable="spawner", output="screen",
             arguments=["joint_state_broadcaster", "arm_controller",
                        "--controller-manager-timeout", "60"]),
        Node(package="rviz2", executable="rviz2", parameters=[sim_time],
             arguments=["-d", PathJoinSubstitution([description, "rviz", "arm.rviz"])],
             condition=IfCondition(LaunchConfiguration("rviz"))),
        Node(package="arm_control", executable="arm_gui",
             condition=IfCondition(LaunchConfiguration("gui"))),
        Node(package="arm_hardware_bridge", executable="udp_bridge", output="screen",
             parameters=[LaunchConfiguration("hardware_config")],
             condition=IfCondition(LaunchConfiguration("hardware"))),
    ])
