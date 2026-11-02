"""Classify a Japanese command, then drive to a fixed waypoint using odometry."""
import json
import math
from pathlib import Path
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.clock import Clock, ClockType
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile
from std_msgs.msg import String

from pai_delivery.intent import IntentClassifier


GOALS = {"reception": (1.8, 1.2), "warehouse": (-1.8, 1.2)}


class DeliveryNode(Node):
    def __init__(self):
        super().__init__("ai_delivery")
        self.classifier = IntentClassifier()
        self.target = None
        self.instruction = ""
        self.pose = None
        self.last_odom = 0.0
        self.result = {}
        self.velocity = self.create_publisher(Twist, "/cmd_vel", 10)
        qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.status = self.create_publisher(String, "/delivery/status", qos)
        self.create_subscription(Odometry, "/odom", self.on_odom, 10)
        self.create_subscription(String, "/instruction", self.on_instruction, 10)
        self.create_timer(0.1, self.control, clock=Clock(clock_type=ClockType.STEADY_TIME))
        log_path = self.declare_parameter("log_path", "/work/output/events.jsonl").value
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        self.log = open(log_path, "a", encoding="utf-8", buffering=1)
        self.emit("ready")

    def emit(self, phase):
        event = {"time": time.time(), "phase": phase, "instruction": self.instruction, **self.result}
        if self.pose:
            event["position"] = [round(v, 3) for v in self.pose[:2]]
        line = json.dumps(event, ensure_ascii=False)
        self.status.publish(String(data=line))
        self.log.write(line + "\n")
        self.get_logger().info(
            f"{phase.upper()} | {self.instruction}\n"
            f"  intent={self.result.get('label', '-')} score={self.result.get('score', '-')} "
            f"position={event.get('position', '-')}"
        )

    def on_odom(self, msg):
        position = msg.pose.pose.position
        q = msg.pose.pose.orientation
        yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
        self.pose = (position.x, position.y, yaw)
        self.last_odom = time.monotonic()

    def on_instruction(self, msg):
        self.instruction = msg.data
        self.result = self.classifier.predict(msg.data)
        # Any new instruction first cancels the old goal and sends zero velocity.
        self.target = None
        self.velocity.publish(Twist())
        if not self.result["accepted"]:
            self.emit("rejected")
        elif self.result["label"] == "stop":
            self.emit("stopped")
        elif self.pose is None or time.monotonic() - self.last_odom > 1.0:
            self.emit("odometry_unavailable")
        else:
            self.target = GOALS[self.result["label"]]
            self.emit("moving")

    def control(self):
        velocity = Twist()
        if self.target is not None:
            if self.pose is None or time.monotonic() - self.last_odom > 1.0:
                self.target = None
                self.emit("odometry_unavailable")
            else:
                x, y, yaw = self.pose
                dx, dy = self.target[0] - x, self.target[1] - y
                distance = math.hypot(dx, dy)
                angle = math.atan2(math.sin(math.atan2(dy, dx) - yaw), math.cos(math.atan2(dy, dx) - yaw))
                if distance < 0.15:
                    self.target = None
                    self.emit("arrived")
                else:
                    velocity.angular.z = max(-1.2, min(1.2, 2.0 * angle))
                    if abs(angle) < 0.45:
                        velocity.linear.x = min(0.35, 0.8 * distance) * (1 - abs(angle) / 0.45)
        self.velocity.publish(velocity)


def main(args=None):
    rclpy.init(args=args)
    node = DeliveryNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            node.velocity.publish(Twist())
        node.log.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
