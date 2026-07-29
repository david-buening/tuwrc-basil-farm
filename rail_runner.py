#!/usr/bin/env python3
"""
rail_runner.py
==============

Drive only the X-rail (`rail_joint`) through a list of positions, one after
another. Unlike waypoint_runner.py this does NOT use MoveIt/IK -- it commands
`rail_joint` directly and simply holds the other arm joints at their current
position, so it only needs Gazebo + the controllers running (no MoveIt).

PREREQUISITES (inside the container, in this order):
    ros2 launch lerobot_description so101_gazebo.launch.py
    ros2 launch lerobot_controller  so101_controller.launch.py

HOW TO RUN (inside the container; repo mounted at /workspace):
    source /opt/ros/humble/setup.bash
    source /workspace/lerobot/install/setup.bash
    python3 /workspace/rail_runner.py
"""

import time

import rclpy
from rclpy.node import Node

from builtin_interfaces.msg import Duration
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


# ===========================================================================
# CONFIGURATION -- edit this block to change the motion
# ===========================================================================

# Rail positions to visit, in order, in METERS. Valid range: -0.5 .. +0.5
RAIL_POSITIONS = [0.0, 0.3, -0.3, 0.0]

# How long (seconds) each move should take. Larger = slower & smoother.
MOVE_DURATION = 3.0

# Extra pause (seconds) to stand still at each waypoint before continuing.
DWELL_TIME = 1.0

# ---------------------------------------------------------------------------
# Fixed project settings (normally no need to touch these).
# ---------------------------------------------------------------------------
ARM_TRAJECTORY_TOPIC = "/arm_controller/joint_trajectory"
# All joints the arm_controller expects, in order. The revolute joints (1..5)
# are held at their current position while only rail_joint moves.
ARM_CONTROLLER_JOINTS = ["rail_joint", "1", "2", "3", "4", "5"]
REACHED_TOLERANCE = 0.02  # meters


class RailRunner(Node):
    def __init__(self):
        super().__init__("rail_runner")
        self._joint_positions = {}
        self.create_subscription(JointState, "/joint_states", self._on_joint_state, 10)
        self._arm_pub = self.create_publisher(JointTrajectory, ARM_TRAJECTORY_TOPIC, 10)

    def _on_joint_state(self, msg: JointState):
        for name, position in zip(msg.name, msg.position):
            self._joint_positions[name] = position

    def wait_until_ready(self, timeout_sec=30.0):
        self.get_logger().info("Waiting for /joint_states ...")
        deadline = time.time() + timeout_sec
        while rclpy.ok() and not all(j in self._joint_positions for j in ARM_CONTROLLER_JOINTS):
            rclpy.spin_once(self, timeout_sec=0.1)
            if time.time() > deadline:
                raise RuntimeError(
                    "No /joint_states for all arm joints. Are Gazebo and the controllers running?"
                )
        self.get_logger().info("Ready.")

    def send_rail_target(self, rail_position, duration_sec):
        """Move rail_joint to rail_position, holding joints 1..5 where they are."""
        target = dict(self._joint_positions)
        target["rail_joint"] = rail_position

        names = [j for j in ARM_CONTROLLER_JOINTS if j in target]
        positions = [target[j] for j in names]

        traj = JointTrajectory()
        traj.joint_names = names
        point = JointTrajectoryPoint()
        point.positions = positions
        point.time_from_start = Duration(
            sec=int(duration_sec),
            nanosec=int((duration_sec % 1.0) * 1e9),
        )
        traj.points = [point]
        self._arm_pub.publish(traj)
        return {"rail_joint": rail_position}

    def wait_until_reached(self, target, timeout_sec):
        deadline = time.time() + timeout_sec
        while rclpy.ok() and time.time() < deadline:
            rclpy.spin_once(self, timeout_sec=0.05)
            if abs(self._joint_positions.get("rail_joint", 1e9) - target["rail_joint"]) < REACHED_TOLERANCE:
                return True
        return False

    def run(self, positions):
        for index, rail_position in enumerate(positions, start=1):
            self.get_logger().info(
                f"[{index}/{len(positions)}] rail_joint -> {rail_position:+.3f} m"
            )
            target = self.send_rail_target(rail_position, MOVE_DURATION)

            if self.wait_until_reached(target, timeout_sec=MOVE_DURATION + 5.0):
                self.get_logger().info("  -> reached.")
            else:
                self.get_logger().warn("  -> timed out before reaching target.")

            end = time.time() + DWELL_TIME
            while rclpy.ok() and time.time() < end:
                rclpy.spin_once(self, timeout_sec=0.05)

        self.get_logger().info("Rail sequence finished.")


def main():
    rclpy.init()
    node = RailRunner()
    try:
        node.wait_until_ready()
        node.run(RAIL_POSITIONS)
    except (KeyboardInterrupt, RuntimeError) as exc:
        node.get_logger().error(str(exc))
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
