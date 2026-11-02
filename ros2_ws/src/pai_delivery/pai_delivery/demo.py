"""Integration demo: two arrivals, an interrupted trip, and an unknown command."""
import json
from pathlib import Path
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile
from std_msgs.msg import String


def main(args=None):
    rclpy.init(args=args)
    node = Node("delivery_demo")
    pause_seconds = float(node.declare_parameter("pause_seconds", 0.0).value)
    publisher = node.create_publisher(String, "/instruction", 10)
    state = {"last": {}}

    def on_status(msg):
        state["last"] = json.loads(msg.data)

    qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
    node.create_subscription(String, "/delivery/status", on_status, qos)
    result_path = Path("/work/output/demo-result.json")
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps({"passed": False, "steps": []}))
    results = []
    try:
        deadline = time.monotonic() + 30
        while publisher.get_subscription_count() == 0:
            if time.monotonic() > deadline:
                raise RuntimeError("Delivery node did not subscribe to /instruction")
            rclpy.spin_once(node, timeout_sec=0.1)
        for _ in range(10):
            rclpy.spin_once(node, timeout_sec=0.1)
        commands = [
            ("この荷物を受付へ届けてください", "arrived", 60),
            ("資材を倉庫まで運搬してほしい", "moving", 10),
            ("停止して", "stopped", 10),
            ("資材を倉庫まで運搬してほしい", "arrived", 60),
            ("明日の天気を教えて", "rejected", 10),
        ]
        for text, phase, timeout in commands:
            sent_at = time.time()
            print(f"\n指示: {text}", flush=True)
            publisher.publish(String(data=text))
            deadline = time.monotonic() + timeout
            while True:
                rclpy.spin_once(node, timeout_sec=0.1)
                event = state["last"]
                if event.get("instruction") == text and event.get("time", 0) >= sent_at:
                    if event.get("phase") == phase:
                        print(json.dumps(event, ensure_ascii=False), flush=True)
                        results.append(event)
                        break
                    if event.get("phase") in {"rejected", "odometry_unavailable"}:
                        raise RuntimeError(f"Command failed: {event}")
                if time.monotonic() > deadline:
                    raise RuntimeError(f"Timed out waiting for {phase}: {state['last']}")
            if phase == "moving":
                # Interrupt a trip while the robot is moving, then resume it.
                pause_until = time.monotonic() + 2.0
                while time.monotonic() < pause_until:
                    rclpy.spin_once(node, timeout_sec=0.1)
            elif pause_seconds > 0:
                pause_until = time.monotonic() + pause_seconds
                while time.monotonic() < pause_until:
                    rclpy.spin_once(node, timeout_sec=0.1)
        print("\nPASS: two destinations reached, stop accepted, unsupported command rejected.", flush=True)
        result_path.write_text(json.dumps({"passed": True, "steps": results}, ensure_ascii=False, indent=2))
    finally:
        publisher.publish(String(data="停止して"))
        rclpy.spin_once(node, timeout_sec=0.1)
        node.destroy_node()
        rclpy.shutdown()
