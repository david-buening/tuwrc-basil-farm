#!/usr/bin/env python3
"""Quick test: print current end-effector pose via tf2."""
import math
import rclpy
from rclpy.node import Node
import tf2_ros


def quaternion_to_rpy(x, y, z, w):
    # Roll (x-axis)
    roll  = math.atan2(2*(w*x + y*z), 1 - 2*(x*x + y*y))
    # Pitch (y-axis)
    sinp  = 2*(w*y - z*x)
    pitch = math.copysign(math.pi/2, sinp) if abs(sinp) >= 1 else math.asin(sinp)
    # Yaw (z-axis)
    yaw   = math.atan2(2*(w*z + x*y), 1 - 2*(y*y + z*z))
    return roll, pitch, yaw


class PoseChecker(Node):
    def __init__(self):
        super().__init__("pose_checker")
        self.tf_buffer   = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

    def print_pose(self):
        try:
            t = self.tf_buffer.lookup_transform("world", "gripper", rclpy.time.Time())
            p = t.transform.translation
            r = t.transform.rotation
            roll, pitch, yaw = quaternion_to_rpy(r.x, r.y, r.z, r.w)
            print(f"Position  x={p.x:.4f}  y={p.y:.4f}  z={p.z:.4f}")
            print(f"Rotation  roll={math.degrees(roll):.2f}°  pitch={math.degrees(pitch):.2f}°  yaw={math.degrees(yaw):.2f}°")
        except tf2_ros.LookupException as e:
            print(f"TF not ready yet: {e}")


def main():
    rclpy.init()
    node = PoseChecker()

    # spin in background so TF listener can receive messages
    import threading, time
    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    time.sleep(1.5)

    for _ in range(5):
        node.print_pose()
        time.sleep(0.5)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
