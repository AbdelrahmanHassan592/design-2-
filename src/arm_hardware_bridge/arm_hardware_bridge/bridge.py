import math
import socket

import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory

from arm_control.trajectory import COMMAND_TOPIC, JOINTS


class UdpBridge(Node):
    def __init__(self):
        super().__init__("udp_bridge")
        ip = self.declare_parameter("esp32_ip", "ESP32_IP_HERE").value
        port = self.declare_parameter("udp_port", 4210).value
        self.servo_joints = self.declare_parameter("servo_joints", list(JOINTS)).value

        if not 1 <= port <= 65535:
            raise ValueError("udp_port must be between 1 and 65535.")
        if len(self.servo_joints) != 4 or set(self.servo_joints) != set(JOINTS):
            raise ValueError("servo_joints must list all four joint names once in UDP order.")

        self.destination = None
        if ip == "ESP32_IP_HERE":
            self.get_logger().warn("Set esp32_ip in your local config to enable sending.")
        else:
            try:
                socket.inet_pton(socket.AF_INET, ip)
            except OSError as error:
                raise ValueError("esp32_ip must be an IPv4 address.") from error
            self.destination = (ip, port)

        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.subscription = self.create_subscription(
            JointTrajectory, COMMAND_TOPIC, self.forward_pose, 10,
        )

    def forward_pose(self, trajectory):
        if self.destination is None or not trajectory.points:
            return
        names = trajectory.joint_names
        positions = trajectory.points[-1].positions
        if (len(names) != len(JOINTS) or set(names) != set(JOINTS)
                or len(positions) != len(names) or not all(map(math.isfinite, positions))):
            self.get_logger().warn("Ignoring an invalid arm pose.", throttle_duration_sec=2)
            return

        position_by_joint = dict(zip(names, positions))
        angles = []
        for joint in self.servo_joints:
            # Limit the joint angle before converting it to the servo angle.
            radians = max(-math.pi / 2, min(math.pi / 2, position_by_joint[joint]))
            angles.append(str(round(math.degrees(radians) + 90)))
        packet = (",".join(angles) + "\n").encode("ascii")
        try:
            self.udp.sendto(packet, self.destination)
        except OSError as error:
            self.get_logger().warn(f"Could not send UDP packet: {error}", throttle_duration_sec=2)


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = UdpBridge()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.udp.close()
            node.destroy_node()
        rclpy.try_shutdown()
