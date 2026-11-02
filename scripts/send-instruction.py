"""Publish text without interpolating it into a shell command or YAML."""
import sys
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

rclpy.init()
node = Node("instruction_sender")
publisher = node.create_publisher(String, "/instruction", 10)
try:
    deadline = time.monotonic() + 10
    while publisher.get_subscription_count() == 0:
        if time.monotonic() > deadline:
            raise RuntimeError("No delivery node is listening")
        rclpy.spin_once(node, timeout_sec=0.1)
    publisher.publish(String(data=sys.argv[1]))
    for _ in range(10):
        rclpy.spin_once(node, timeout_sec=0.1)
    print("送信しました:", sys.argv[1])
finally:
    node.destroy_node()
    rclpy.shutdown()
