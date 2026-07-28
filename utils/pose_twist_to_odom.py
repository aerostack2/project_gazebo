#!/usr/bin/env python3

"""Fuse a PoseStamped and a TwistStamped topic into a single nav_msgs/Odometry topic."""

import argparse

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import PoseStamped, TwistStamped
from nav_msgs.msg import Odometry


class PoseTwistToOdom(Node):
    """Publish an Odometry message on every pose, using the last received twist."""

    def __init__(self, namespace: str, pose_topic: str, twist_topic: str, odom_topic: str,
                 odom_frame: str, base_frame: str, use_sim_time: bool) -> None:
        super().__init__('pose_twist_to_odom', namespace=namespace)

        self.set_parameters([Parameter('use_sim_time', Parameter.Type.BOOL, use_sim_time)])

        self.odom_frame = odom_frame
        self.base_frame = base_frame
        self.last_twist = TwistStamped()

        self.pub = self.create_publisher(Odometry, odom_topic, qos_profile_sensor_data)
        self.pose_sub = self.create_subscription(
            PoseStamped, pose_topic, self.pose_callback, qos_profile_sensor_data)
        self.twist_sub = self.create_subscription(
            TwistStamped, twist_topic, self.twist_callback, qos_profile_sensor_data)

        self.get_logger().info(
            f"Fusing '{pose_topic}' + '{twist_topic}' -> '{odom_topic}' "
            f"({odom_frame} -> {base_frame})")

    def twist_callback(self, msg: TwistStamped) -> None:
        """Store the latest twist to be paired with the next pose."""
        self.last_twist = msg

    def pose_callback(self, msg: PoseStamped) -> None:
        """Publish the odometry message built from this pose and the last twist."""
        odom = Odometry()
        odom.header.stamp = msg.header.stamp
        odom.header.frame_id = self.odom_frame
        odom.child_frame_id = self.base_frame
        odom.pose.pose = msg.pose
        odom.twist.twist = self.last_twist.twist
        self.pub.publish(odom)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Fuse a pose and a twist topic into an odometry topic')

    parser.add_argument('-n', '--namespace',
                        type=str,
                        default='drone0',
                        help='Drone namespace')
    parser.add_argument('-p', '--pose-topic',
                        type=str,
                        default='ground_truth/pose',
                        help='PoseStamped topic to subscribe to')
    parser.add_argument('-t', '--twist-topic',
                        type=str,
                        default='ground_truth/twist',
                        help='TwistStamped topic to subscribe to, expressed in the base frame')
    parser.add_argument('-o', '--odom-topic',
                        type=str,
                        default='ground_truth/odom',
                        help='Topic to publish the fused odometry to')
    parser.add_argument('--odom-frame',
                        type=str,
                        default=None,
                        help='Odometry header frame id (default: <namespace>/odom)')
    parser.add_argument('--base-frame',
                        type=str,
                        default=None,
                        help='Odometry child frame id (default: <namespace>/base_link)')
    parser.add_argument('-s', '--use-sim-time',
                        action='store_true',
                        default=True,
                        help='Use simulation time')

    args = parser.parse_args()

    odom_frame = args.odom_frame or f'{args.namespace}/odom'
    base_frame = args.base_frame or f'{args.namespace}/base_link'

    rclpy.init()
    node = PoseTwistToOdom(args.namespace, args.pose_topic, args.twist_topic, args.odom_topic,
                           odom_frame, base_frame, args.use_sim_time)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
