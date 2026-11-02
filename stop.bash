#!/bin/bash

# Prevent killing this script's own process so the full clean up happens
# correctly at the end
trap '' HUP

# Get the directory of the current script
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# Get drone namespaces from command-line argument
drones_namespace_comma=$1
IFS=',' read -r -a drone_namespaces <<< "$drones_namespace_comma"

# Make a tmux list of sessions to be killed
tmux_session_list=()

# Add drones from user input
for namespace in ${drone_namespaces[@]}; do
  tmux_session_list+=("$namespace")
done

# Add drones from config/world.yaml file
drone_namespaces=$(python3 ${script_dir}/utils/get_drones.py -p ${script_dir}/config/world.yaml --sep ' ')
for namespace in ${drone_namespaces[@]}; do
  tmux_session_list+=("$namespace")
done

# Add drones from config/world_swarm.yaml file
drone_namespaces=$(python3 ${script_dir}/utils/get_drones.py -p ${script_dir}/config/world_swarm.yaml --sep ' ')
for namespace in ${drone_namespaces[@]}; do
  tmux_session_list+=("$namespace")
done

tmux_session_list+=("ground_station")

${script_dir}/utils/stop_tmux_sessions.bash "${tmux_session_list[@]}"


# Kill gazebo
pkill -9 -f 'gz' < /dev/null
pkill -9 -f "gazebo" < /dev/null
pkill -9 -f "ruby" < /dev/null

# Kill gazebo bridges
pkill -9 -f "ros_gz_bridge"
