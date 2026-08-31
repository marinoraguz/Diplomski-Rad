###INSTRUCTION MANUAL###
Login:marino
Pass: diplomski1

#SETTING THE TIME
# On the Pi AND the ZCU
sudo date -s "$(curl -s --head http://google.com | grep ^Date: | sed 's/Date: //')"

#MASTER LAUNCH COMMAND
sudo ./start_robot.sh


#TERMINAL 1
#Entering the docker
sudo ./start_robot.sh

#Editing start script
nano start_robot.sh

#run camera
ros2 run v4l2_camera v4l2_camera_node --ros-args -p video_device:="/dev/video0"

#start s manjom rezolucijom
ros2 run v4l2_camera v4l2_camera_node --ros-args \
  -p video_device:="/dev/video0" \
  -p image_size:="[320,240]" \
  -p frame_rate:="8"


  ros2 run usb_cam usb_cam_node_exe --ros-args \
  -p video_device:="/dev/video0" \
  -p pixel_format:="mjpeg2rgb" \
  -p image_width:=320 \
  -p image_height:=240 \
  -p framerate:=10.0

#TERMINAL 2
docker ps
docker exec -it <YOUR_CONTAINER_ID> bash
source /opt/ros/humble/setup.bash
ros2 run rplidar_ros rplidar_node --ros-args -p serial_port:=/dev/ttyUSB0 -p serial_baudrate:=115200 -p frame_id:=laser


#ENTERING THE DOCKER (TROUBLESHOOTING)
docker run -it --privileged --net=host ros_robot_final:v2 bash

source /opt/ros/humble/setup.bash
# 1. Stop any "stuck" discovery processes
ros2 daemon stop

# 2. Set the variables explicitly for this session
export ROS_DOMAIN_ID=42
export ROS_LOCALHOST_ONLY=0
export FASTDDS_BUILTIN_TRANSPORTS=UDPv4

# 3. Start a fresh discovery process
ros2 daemon start

# 4. Try listing again
ros2 topic list
# Enter the container
docker exec -it <container_id> bash

# Inside the container:
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=42
ros2 topic list

#Finding container ID for closed docker
docker ps -a | head -n 2

#SAVING
docker commit <ID> ros_robot_final:v2
docker commit $(docker ps -aq | head -n 1) ros_robot_final:v2

#ENTERING THE ZCU SSH TERMINAL
ssh ubuntu@10.42.0.151

export ROS_DOMAIN_ID=42
export ROS_DISCOVERY_SERVER=10.42.0.151:11811

#Second terminal
ssh ubuntu@10.42.0.151

export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=42
export ROS_LOCALHOST_ONLY=0

#PI 
#TERMINAL 1
sudo ./start_robot.sh

#TERMINAL 2
docker exec -it robot bash
source /opt/ros/humble/setup.bash
ros2 daemon stop
export ROS_DOMAIN_ID=42
export ROS_LOCALHOST_ONLY=0
export FASTDDS_BUILTIN_TRANSPORTS=UDPv4
ros2 daemon start
ros2 topic list


#ZCU
#TERMINAL 1

ros2 launch /home/ubuntu/robot_ws/zcu_master_launch.py
