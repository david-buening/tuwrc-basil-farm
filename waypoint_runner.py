#!/usr/bin/env python3
"""
waypoint_runner.py
==================

Drive the SO-101 (+ X-rail) robot in Gazebo through a list of full 6-DOF
Cartesian waypoints, one after another.

Each waypoint is a target pose for the end-effector expressed as SIX numbers:

    (x, y, z, roll, pitch, yaw)
     |  |  |   |     |      |
     |  |  |   +-----+------+---- orientation in DEGREES (roll=X, pitch=Y, yaw=Z)
     +--+--+-------------------- position in METERS

For every waypoint the script:
  1. asks MoveIt's inverse-kinematics service (/compute_ik) for a joint
     solution that reaches the pose (this automatically includes the new
     prismatic `rail_joint`, because it is part of the "arm" planning group),
  2. sends that solution as a timed trajectory to the arm controller,
  3. waits until the robot has actually reached it,
  4. moves on to the next waypoint.

--------------------------------------------------------------------------
PREREQUISITES (all must be running inside the container, in this order):
    ros2 launch lerobot_description so101_gazebo.launch.py
    ros2 launch lerobot_controller  so101_controller.launch.py
    ros2 launch lerobot_moveit      so101_moveit.launch.py     # provides /compute_ik

HOW TO RUN (inside the container; the repo is mounted at /workspace):
    source /opt/ros/humble/setup.bash
    source /workspace/lerobot/install/setup.bash
    python3 /workspace/waypoint_runner.py

NOTES:
  * Poses are expressed in the fixed `world` frame (NOT `base`, which now
    travels with the rail carriage).
  * Because kinematics.yaml uses `position_only_ik: False`, the orientation
    IS targeted. The arm has only 5 revolute joints, so not every orientation
    is reachable -- if IK fails for a waypoint the script prints a warning and
    skips to the next one instead of aborting.
  * The easiest way to find valid numbers is the web GUI (localhost:3000):
    move the robot somewhere, press "Fill current", and copy the X/Y/Z + RPY.
"""

import math
import time

import rclpy
from rclpy.node import Node

from builtin_interfaces.msg import Duration
from geometry_msgs.msg import PoseStamped
from moveit_msgs.srv import GetPositionIK
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


# ===========================================================================
# CONFIGURATION -- edit this block to change the motion
# ===========================================================================

# The waypoints to visit, in order. Each entry is:
#   (x_m, y_m, z_m, roll_deg, pitch_deg, yaw_deg)
#
# The values below are only EXAMPLES. Replace them with poses that are
# reachable for your setup (read them from the web GUI via "Fill current").
WAYPOINTS = [
    (0.10, -0.2775, 0.2819, -156.5, -90.0, 66.5),   # start / centered on the rail
    #(0.20, -0.1775, 0.2819, 113.5, -90.0, 120),   # tilt the wrist (pitch -90 -> -70)
    #(-0.20, -0.2775, 0.2819, 113.5, -90.0, 180),  # slide to the other side (-X)
   # (0.00, -0.2775, 0.2819, -156.5, -90.0, 66.5),   # back to start
]

# How long (seconds) each move should take. Larger = slower & smoother.
MOVE_DURATION = 3.0

# Extra pause (seconds) to stand still at each waypoint before continuing.
DWELL_TIME = 1.0

# ---------------------------------------------------------------------------
# Fixed project settings (normally no need to touch these).
# ---------------------------------------------------------------------------
POSE_FRAME = "world"                 # fixed reference frame for all targets
END_EFFECTOR_LINK = "tcp"            # tool frame: Z = approach direction
MOVEIT_GROUP = "arm"                 # planning group (rail_joint + joints 1..5)
IK_SERVICE = "/compute_ik"           # MoveIt inverse-kinematics service
ARM_TRAJECTORY_TOPIC = "/arm_controller/joint_trajectory"

# Joints commanded by the arm controller, in the order it expects them.
# NOTE: `rail_joint` is prismatic (meters); joints 1..5 are revolute (radians).
ARM_CONTROLLER_JOINTS = ["rail_joint", "1", "2", "3", "4", "5"]

# A move is considered "reached" when every joint is within this distance of
# its target (radians for revolute joints, meters for the rail -- 0.02 works
# as a reasonable threshold for both).
REACHED_TOLERANCE = 0.02


# ===========================================================================
# MATH HELPER
# ===========================================================================

def euler_to_quaternion(roll, pitch, yaw):
    """Convert roll/pitch/yaw (radians) to a quaternion (x, y, z, w).

    Uses the same intrinsic RPY convention as the web GUI so that numbers
    copied from the GUI behave identically here.
    """
    cy, sy = math.cos(yaw * 0.5),   math.sin(yaw * 0.5)
    cp, sp = math.cos(pitch * 0.5), math.sin(pitch * 0.5)
    cr, sr = math.cos(roll * 0.5),  math.sin(roll * 0.5)

    x = sr * cp * cy - cr * sp * sy
    y = cr * sp * cy + sr * cp * sy
    z = cr * cp * sy - sr * sp * cy
    w = cr * cp * cy + sr * sp * sy
    return x, y, z, w


# ===========================================================================
# ROS NODE
# ===========================================================================

class WaypointRunner(Node):
    def __init__(self):
        super().__init__("waypoint_runner")

        # Keep the latest joint positions {name: value}. Used both to seed the
        # IK solver (for a deterministic, unique-ish solution) and to detect
        # when a move has finished.
        self._joint_positions = {}
        self.create_subscription(
            JointState, "/joint_states", self._on_joint_state, 10
        )

        # Publisher that feeds timed trajectories to the arm controller.
        self._arm_pub = self.create_publisher(
            JointTrajectory, ARM_TRAJECTORY_TOPIC, 10
        )

        # Client for MoveIt's inverse-kinematics service.
        self._ik_client = self.create_client(GetPositionIK, IK_SERVICE)

    # ---- callbacks --------------------------------------------------------

    def _on_joint_state(self, msg: JointState):
        for name, position in zip(msg.name, msg.position):
            self._joint_positions[name] = position

    # ---- startup helpers --------------------------------------------------

    def wait_until_ready(self, timeout_sec=30.0):
        """Block until /compute_ik is up and joint states are flowing."""
        self.get_logger().info(f"Waiting for IK service {IK_SERVICE} ...")
        if not self._ik_client.wait_for_service(timeout_sec=timeout_sec):
            raise RuntimeError(
                f"IK service {IK_SERVICE} not available. Is MoveIt running?"
            )

        self.get_logger().info("Waiting for /joint_states ...")
        deadline = time.time() + timeout_sec
        while rclpy.ok() and not self._joint_positions and time.time() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
        if not self._joint_positions:
            raise RuntimeError("No /joint_states received. Is the controller running?")
        self.get_logger().info("Ready.")

    # ---- core steps -------------------------------------------------------

    def solve_ik(self, x, y, z, roll_deg, pitch_deg, yaw_deg):
        """Return {joint_name: value} for the given pose, or None if unreachable."""
        pose = PoseStamped()
        pose.header.frame_id = POSE_FRAME
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = float(x)
        pose.pose.position.y = float(y)
        pose.pose.position.z = float(z)
        qx, qy, qz, qw = euler_to_quaternion(
            math.radians(roll_deg), math.radians(pitch_deg), math.radians(yaw_deg)
        )
        pose.pose.orientation.x = qx
        pose.pose.orientation.y = qy
        pose.pose.orientation.z = qz
        pose.pose.orientation.w = qw

        request = GetPositionIK.Request()
        request.ik_request.group_name = MOVEIT_GROUP
        request.ik_request.ik_link_name = END_EFFECTOR_LINK
        request.ik_request.pose_stamped = pose
        request.ik_request.timeout.sec = 2
        # Seed the solver with the current robot state -> the returned solution
        # stays close to where we are now, which keeps the motion predictable.
        request.ik_request.robot_state.joint_state.name = list(self._joint_positions.keys())
        request.ik_request.robot_state.joint_state.position = list(self._joint_positions.values())

        future = self._ik_client.call_async(request)
        rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
        response = future.result()
        if response is None:
            self.get_logger().warn("IK call returned no response.")
            return None
        if response.error_code.val != 1:  # 1 == SUCCESS
            self.get_logger().warn(f"IK failed (error code {response.error_code.val}).")
            return None

        return dict(zip(
            response.solution.joint_state.name,
            response.solution.joint_state.position,
        ))

    def send_arm_trajectory(self, solution, duration_sec):
        """Publish the arm-controller joints from an IK solution as one move."""
        names, positions = [], []
        for joint in ARM_CONTROLLER_JOINTS:
            if joint in solution:
                names.append(joint)
                positions.append(solution[joint])

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
        return dict(zip(names, positions))

    def wait_until_reached(self, target, timeout_sec):
        """Spin until all target joints are within tolerance, or time out."""
        deadline = time.time() + timeout_sec
        while rclpy.ok() and time.time() < deadline:
            rclpy.spin_once(self, timeout_sec=0.05)
            if all(
                abs(self._joint_positions.get(name, 1e9) - value) < REACHED_TOLERANCE
                for name, value in target.items()
            ):
                return True
        return False

    # ---- the main loop ----------------------------------------------------

    def run(self, waypoints):
        for index, (x, y, z, roll, pitch, yaw) in enumerate(waypoints, start=1):
            self.get_logger().info(
                f"[{index}/{len(waypoints)}] target "
                f"x={x:.3f} y={y:.3f} z={z:.3f}  "
                f"rpy=({roll:.1f}, {pitch:.1f}, {yaw:.1f}) deg"
            )

            solution = self.solve_ik(x, y, z, roll, pitch, yaw)
            if solution is None:
                self.get_logger().warn("  -> unreachable, skipping this waypoint.")
                continue

            target = self.send_arm_trajectory(solution, MOVE_DURATION)
            rail = target.get("rail_joint")
            if rail is not None:
                self.get_logger().info(f"  -> moving (rail_joint = {rail:+.3f} m)")

            if self.wait_until_reached(target, timeout_sec=MOVE_DURATION + 5.0):
                self.get_logger().info("  -> reached.")
            else:
                self.get_logger().warn("  -> timed out before reaching target.")

            # Stand still for a moment before the next waypoint.
            end = time.time() + DWELL_TIME
            while rclpy.ok() and time.time() < end:
                rclpy.spin_once(self, timeout_sec=0.05)

        self.get_logger().info("Waypoint sequence finished.")


def main():
    rclpy.init()
    node = WaypointRunner()
    try:
        node.wait_until_ready()
        node.run(WAYPOINTS)
    except (KeyboardInterrupt, RuntimeError) as exc:
        node.get_logger().error(str(exc))
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
