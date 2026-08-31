#!/bin/bash
echo "--- Optimizing Robot Hardware ---"
sudo iwconfig wlan0 power off 2>/dev/null

# Ensure all devices are accessible
sudo chmod 666 /dev/ttyUSB0 /dev/ttyUSB1 /dev/input/js0 2>/dev/null

# Clean up any old containers
docker rm -f robot 2>/dev/null

echo "--- Starting Docker Container (ros_robot_final:v2) ---"
docker run -it --name robot --rm --privileged --net=host \
    --ipc=host \
    --dns 8.8.8.8 \
    -v /dev:/dev \
    --device /dev/input/js0:/dev/input/js0 \
        -e ROS_DOMAIN_ID=42 \
    -e ROS_LOCALHOST_ONLY=0 \
    -e RMW_IMPLEMENTATION=rmw_fastrtps_cpp \
    ros_robot_final:v2 \
    bash -c "source /opt/ros/humble/setup.bash && [ -f /root/ros_ws/install/setup.bash ] && source /root/ros_ws/install/setup.bash; ros2 launch /root/robot_bringup.launch.py"


