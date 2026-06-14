#!/usr/bin/env python3

"""Republish a PoseStamped topic with a fixed delay, keeping the original header timestamp."""

import argparse
from collections import deque

import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import PoseStamped


class PoseDelayer(Node):
    """Buffer incoming PoseStamped messages and republish them after a fixed delay."""

    def __init__(self, namespace: str, input_topic: str, output_topic: str,
                 delay_ms: float, use_sim_time: bool) -> None:
        super().__init__('pose_delayer', namespace=namespace)

        self.set_parameters([Parameter('use_sim_time', Parameter.Type.BOOL, use_sim_time)])

        self.delay = Duration(seconds=delay_ms / 1000.0)
        self.queue = deque()

        self.pub = self.create_publisher(PoseStamped, output_topic, qos_profile_sensor_data)
        self.sub = self.create_subscription(
            PoseStamped, input_topic, self.callback, qos_profile_sensor_data)

        # 100 Hz flush rate: small enough error margin for delays in the 100s of ms range.
        self.timer = self.create_timer(0.01, self.flush)

        self.get_logger().info(
            f"Delaying '{input_topic}' -> '{output_topic}' by {delay_ms} ms")

    def callback(self, msg: PoseStamped) -> None:
        """Queue message with the time at which it should be republished."""
        release_time = self.get_clock().now() + self.delay
        self.queue.append((release_time, msg))

    def flush(self) -> None:
        """Publish all queued messages whose release time has passed."""
        now = self.get_clock().now()
        while self.queue and self.queue[0][0] <= now:
            _, msg = self.queue.popleft()
            self.pub.publish(msg)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Delay a PoseStamped topic, keeping the original timestamp')

    parser.add_argument('-n', '--namespace',
                         type=str,
                         default='drone0',
                         help='Drone namespace')
    parser.add_argument('-i', '--input-topic',
                         type=str,
                         default='ground_truth/pose',
                         help='Topic to subscribe to')
    parser.add_argument('-o', '--output-topic',
                         type=str,
                         default='ground_truth/pose_delayed',
                         help='Topic to publish the delayed messages to')
    parser.add_argument('-d', '--delay',
                         type=float,
                         default=400.0,
                         help='Delay in milliseconds')
    parser.add_argument('-s', '--use-sim-time',
                         action='store_true',
                         default=True,
                         help='Use simulation time')

    args = parser.parse_args()

    rclpy.init()
    node = PoseDelayer(args.namespace, args.input_topic, args.output_topic,
                        args.delay, args.use_sim_time)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
