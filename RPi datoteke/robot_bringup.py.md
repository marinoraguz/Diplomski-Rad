import ros
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import TimerAction, LogInfo

def generate_launch_description():
    # Paletar URDF
    urdf_content = """
    <robot name="paletar">
      <link name="base_link" />
      <link name="laser" />
      <joint name="laser_joint" type="fixed">
        <parent link="base_link"/>
        <child link="laser"/>
        <origin xyz="0.45 0 0.1" rpy="0 0 0"/>
      </joint>
    </robot>
    """
    
    # 1. LIDAR NODE (Forced initialization for A1)
    rplidar_node = Node(
        package='rplidar_ros',
        executable='rplidar_node',
        name='rplidar',
        parameters=[{
            'serial_port': '/dev/ttyUSB0',
            'serial_baudrate': 115200,
            'frame_id': 'laser',
            'inverted': False,
            'angle_compensate': True,
            'auto_reconnect': True,
            'motor_pwm': 1000
        }],
        output='screen'
    )

    # 2. MOTOR & JOYSTICK
    motor_node = Node(
        executable='python3',
        arguments=['/root/motor_driver.py'],
        output='screen'
    )

    joy_node = Node(
        package='joy',
        executable='joy_node',
        parameters=[{'dev': '/dev/input/js0', 'autorepeat_rate': 20.0}]
    )

    teleop_node = Node(
        package='teleop_twist_joy',
        executable='teleop_node',
        name='teleop_twist_joy_node',
        parameters=[{
            'require_enable_button': False,
            'axis_linear.x': 1,
            'scale_linear.x': 0.8,
            'axis_angular.yaw': 0,
            'scale_angular.yaw': 1.2,
            'enable_button': -1,
        }]
    )

    # 3. TRANSFORMS
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{'robot_description': urdf_content}]
    )

    static_odom = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='odom_to_base_link',
        arguments=['0', '0', '0', '0', '0', '0', 'odom', 'base_link']
    )

    return LaunchDescription([
        rplidar_node,
        robot_state_publisher,
        static_odom,
        TimerAction(
            period=15.0,
            actions=[
                LogInfo(msg="--- LIDAR STABILIZED. STARTING MOTORS ---"),
                motor_node,
                joy_node,
                teleop_node
            ]
        )
    ])



