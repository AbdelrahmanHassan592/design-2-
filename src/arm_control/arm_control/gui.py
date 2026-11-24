import tkinter as tk
from tkinter import ttk

import rclpy
from trajectory_msgs.msg import JointTrajectory

from arm_control.trajectory import COMMAND_TOPIC, JOINTS, publish_pose


class ArmSliders:
    def __init__(self, root, publisher):
        self.root = root
        self.publisher = publisher
        self.pending = None
        self.angles = [tk.IntVar(value=0) for _ in JOINTS]
        root.title("Lab 2 Arm Control")
        panel = ttk.Frame(root, padding=16)
        panel.pack(fill="both", expand=True)
        for joint, angle in zip(JOINTS, self.angles):
            tk.Scale(
                panel, label=f"{joint} (degrees)", from_=-90, to=90,
                orient="horizontal", length=320, variable=angle,
                command=self.queue_pose,
            ).pack(fill="x")
        ttk.Button(panel, text="Send pose", command=self.send_pose).pack(pady=8)
        self.status = ttk.Label(panel, text="Move a slider or select Send pose.")
        self.status.pack()

    def queue_pose(self, _value):
        # Wait briefly so a slider drag sends only the latest pose.
        if self.pending is not None:
            self.root.after_cancel(self.pending)
        self.pending = self.root.after(120, self.send_pose)

    def send_pose(self):
        if self.pending is not None:
            self.root.after_cancel(self.pending)
            self.pending = None
        if self.publisher.get_subscription_count() == 0:
            self.status.config(text="Waiting for an arm controller or bridge.")
            return
        publish_pose(self.publisher, [angle.get() for angle in self.angles], 1.0)
        self.status.config(text="Pose sent.")


def main(args=None):
    rclpy.init(args=args)
    node = rclpy.create_node("arm_gui")
    try:
        root = tk.Tk()
        ArmSliders(root, node.create_publisher(JointTrajectory, COMMAND_TOPIC, 10))

        def poll_ros():
            if rclpy.ok():
                rclpy.spin_once(node, timeout_sec=0)
                root.after(50, poll_ros)
            else:
                root.destroy()

        root.after(50, poll_ros)
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
