from itertools import cycle

import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory

from arm_control.trajectory import COMMAND_TOPIC, publish_pose


class ArmDemo(Node):
    def __init__(self):
        super().__init__("arm_demo")
        self.publisher = self.create_publisher(JointTrajectory, COMMAND_TOPIC, 10)
        self.poses = cycle([(0, 0, 0, 0), (35, -30, 25, 10),
                            (-30, -40, 15, 25), (0, -20, 30, -15)])
        self.timer = self.create_timer(3.0, self.send_pose)

    def send_pose(self):
        if self.publisher.get_subscription_count():
            publish_pose(self.publisher, next(self.poses), 2.0)


def main(args=None):
    rclpy.init(args=args)
    node = ArmDemo()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
