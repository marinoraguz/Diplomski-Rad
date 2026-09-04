#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import serial
import json
import math
from struct import pack
from geometry_msgs.msg import Twist, TransformStamped, Quaternion
from nav_msgs.msg import Odometry
from std_msgs.msg import String
from tf2_ros import TransformBroadcaster

class MiljenkoMotorDriver(Node):
    def __init__(self):
        super().__init__('motor_driver')

       self.L = 0.578              # Track width (meters)
        self.TICK_TO_M = 0.00095    # Conversion factor (meters per tick)
        self.line_buffer = ""

        # --- Odometry State ---
        self.x = 0.0
        self.y = 0.0
        self.th = 0.0
        self.last_l_ticks = None
        self.last_r_ticks = None
        self.last_time = self.get_clock().now()

        # --- Serial Connection ---
        try:
            self.ser = serial.Serial(port='/dev/ttyUSB1', baudrate=19200, timeout=0.01)
            self.get_logger().info("!!! MOTORS & ODOMETRY ACTIVE ON USB1 !!!")
        except Exception as e:
            self.get_logger().error(f"SERIAL ERROR: {e}")
            self.ser = None

        # --- ROS 2 Infrastructure ---
        self.subscription = self.create_subscription(Twist, 'cmd_vel', self.velocity_callback, 10)
        self.odom_pub = self.create_publisher(Odometry, 'odom', 10)
        self.telemetry_pub = self.create_publisher(String, 'wheel_telemetry', 10)
        self.tf_broadcaster = TransformBroadcaster(self)

        # Poll at 50Hz
        self.timer = self.create_timer(0.02, self.control_loop)

    def velocity_callback(self, msg):
        if self.ser:
            vr = (msg.linear.x + 0.5 * msg.angular.z * self.L) * 1000
            vl = (vr - (msg.angular.z * self.L * 1000))
            cmd = pack("<BhhHH", 1, int(vl), int(vr), 1000, 1000)
            try:
                self.ser.write(cmd + b'\r')
            except: pass

    def control_loop(self):
        if not self.ser: return
        try:
            self.ser.write(pack('<BhhHH', 2, 0, 0, 0, 0) + b'\r')
        except: return

        while self.ser.in_waiting > 0:
            char = self.ser.read().decode('utf-8', errors='ignore')
            if char == '\r':
                self.process_json(self.line_buffer)
                self.line_buffer = ""
            else:
                self.line_buffer += char

    def process_json(self, raw_string):
        try:
            start_idx = raw_string.find('{')
            end_idx = raw_string.rfind('}') + 1
            if start_idx == -1 or end_idx == -1: return

            data = json.loads(raw_string[start_idx:end_idx])
            if "positionM1" not in data: return

            cur_l = data["positionM1"]
            cur_r = data["positionM2"]
            current_time = self.get_clock().now()

            # --- Odometry Calculation ---
            if self.last_l_ticks is not None:
                # 1. Delta Distance per wheel
                dl = (cur_l - self.last_l_ticks) * self.TICK_TO_M
                dr = (cur_r - self.last_r_ticks) * self.TICK_TO_M

                # 2. Kinematics
                d_dist = (dl + dr) / 2.0
                d_th = (dr - dl) / self.L

                # 3. Update Pose
                self.x += d_dist * math.cos(self.th + (d_th / 2.0))
                self.y += d_dist * math.sin(self.th + (d_th / 2.0))
                self.th += d_th

                # 4. Publish Odometry Message
                self.publish_odom(current_time, d_dist, d_th)

            self.last_l_ticks = cur_l
            self.last_r_ticks = cur_r
            self.last_time = current_time

            # Keep raw telemetry for debugging
            t_msg = String()
            t_msg.data = f"L: {cur_l} | R: {cur_r}"
            self.telemetry_pub.publish(t_msg)

        except: pass

    def publish_odom(self, current_time, d_dist, d_th):
        q = self.euler_to_quaternion(0, 0, self.th)

        # Create TF transform
        t = TransformStamped()
        t.header.stamp = current_time.to_msg()
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.rotation = q
        self.tf_broadcaster.sendTransform(t)

        # Create Odometry message
        odom = Odometry()
        odom.header.stamp = current_time.to_msg()
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_link'
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation = q
        self.odom_pub.publish(odom)

    def euler_to_quaternion(self, roll, pitch, yaw):
        qx = math.sin(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) - math.cos(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
        qy = math.cos(roll/2) * math.sin(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.cos(pitch/2) * math.sin(yaw/2)
        qz = math.cos(roll/2) * math.cos(pitch/2) * math.sin(yaw/2) - math.sin(roll/2) * math.sin(pitch/2) * math.cos(yaw/2)
        qw = math.cos(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
        return Quaternion(x=qx, y=qy, z=qz, w=qw)

def main():
    rclpy.init()
    rclpy.spin(MiljenkoMotorDriver())
    rclpy.shutdown()

if __name__ == '__main__':
    main()



