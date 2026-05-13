# Use ROS 2 Humble base image with ARM64 support
FROM ros:humble-ros-base
ENV DEBIAN_FRONTEND=noninteractive

# Install desktop environment and VNC/NoVNC
RUN apt-get update && apt-get install -y \
    xfce4 xfce4-terminal tigervnc-standalone-server tigervnc-common \
    novnc python3-websockify dbus-x11 x11-utils sudo curl wget git \
    nano net-tools mesa-utils libgl1-mesa-dri libglu1-mesa \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install additional ROS packages
RUN apt-get update && apt-get install -y \
    ros-humble-joint-state-publisher-gui \
    ros-humble-rqt-graph ros-humble-rqt-topic ros-humble-rqt-console \
    ros-humble-rqt-reconfigure ros-humble-teleop-twist-keyboard \
    ros-humble-rviz2 ros-humble-xacro \
    ros-humble-ros-gz ros-humble-gz-ros2-control \
    ros-humble-controller-manager ros-humble-joint-state-broadcaster \
    ros-humble-joint-trajectory-controller ros-humble-ros2controlcli \
    ros-humble-moveit \
    python3-colcon-common-extensions python3-rosdep \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create rosuser
RUN useradd -m -s /bin/bash -G sudo rosuser \
    && echo "rosuser:ros" | chpasswd \
    && echo "rosuser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Install additional dependencies if needed (e.g., for building)
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-colcon-common-extensions \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /workspace

# Copy the project files
COPY . /workspace

# Build the ROS 2 workspace
RUN /bin/bash -c "source /opt/ros/humble/setup.bash && colcon build"

# Source ROS and the workspace automatically for interactive bash shells.
RUN printf '\nsource /opt/ros/humble/setup.bash\nif [ -f /workspace/install/setup.bash ]; then\n  source /workspace/install/setup.bash\nfi\n' \
    >> /home/rosuser/.bashrc \
    && printf 'source ~/.bashrc\n' >> /home/rosuser/.bash_profile \
    && chown rosuser:rosuser /home/rosuser/.bashrc /home/rosuser/.bash_profile

# Start VNC and keep a shell open
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

USER rosuser
WORKDIR /home/rosuser

# Setup VNC
RUN mkdir -p ~/.vnc \
    && echo "ros" | vncpasswd -f > ~/.vnc/passwd \
    && chmod 600 ~/.vnc/passwd \
    && printf '#!/bin/sh\nunset SESSION_MANAGER\nunset DBUS_SESSION_BUS_ADDRESS\nexec startxfce4\n' \
       > ~/.vnc/xstartup && chmod +x ~/.vnc/xstartup

ENV DISPLAY=:1
CMD ["/usr/local/bin/docker-entrypoint.sh"]
