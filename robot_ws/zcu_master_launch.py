import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    
    # Common variables
    map_yaml = '/home/ubuntu/robot_ws/maps/factory_floor_map.yaml'
    params_yaml = '/home/ubuntu/robot_ws/paletar_nav_params.yaml'
    filter_yaml = '/home/ubuntu/robot_ws/my_laser_filter.yaml'

    # 1. Localization
    localization_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(nav2_bringup_dir, 'launch', 'localization_launch.py')),
        launch_arguments={
            'map': map_yaml,
            'use_sim_time': 'false',
            'params_file': params_yaml,
            # Note: Overriding dictionary params in launch files requires specific syntax or keeping it inside the yaml. 
            # It's highly recommended to put 'base_frame_id': 'base_link' directly inside paletar_nav_params.yaml under amcl.
        }.items()
    )

    # 2. Navigation
    navigation_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(nav2_bringup_dir, 'launch', 'navigation_launch.py')),
        launch_arguments={
            'use_sim_time': 'false',
            'params_file': params_yaml,
        }.items()
    )
    # 4. Set Initial Pose (0,0,0) so Nav2 initializes automatically
    # Nav2 waits for a pose on /initialpose before bringing up the controller/planner servers.
    initial_pose_cmd = ExecuteProcess(
        cmd=[
            'ros2', 'topic', 'pub', '-1', '/initialpose', 'geometry_msgs/PoseWithCovarianceStamped',
            '{header: {frame_id: "map"}, pose: {pose: {position: {x: 0.0, y: 0.0, z: 0.0}, orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}}}}'
        ],
        output='screen'
    )

    return LaunchDescription([
        localization_cmd,
        navigation_cmd,
        TimerAction(
            period=5.0, # Wait 5 seconds for AMCL to load before publishing pose
            actions=[initial_pose_cmd]
        )
    ])
