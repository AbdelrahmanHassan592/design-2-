from math import radians

from rclpy.duration import Duration
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

COMMAND_TOPIC = "/arm_controller/joint_trajectory"
JOINTS = ("joint1", "joint2", "joint3", "joint4")


def publish_pose(publisher, degrees, seconds):
    """Send one pose. ROS uses radians for joint angles."""
    command = JointTrajectory()
    command.joint_names = list(JOINTS)
    point = JointTrajectoryPoint()
    point.positions = [radians(angle) for angle in degrees]
    point.time_from_start = Duration(seconds=seconds).to_msg()
    command.points = [point]
    publisher.publish(command)
