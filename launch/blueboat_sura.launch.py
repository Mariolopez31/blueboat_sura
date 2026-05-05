from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node
import os
import yaml


def _load_navigator_bridge_alpha():
    params_file = os.path.join(
        get_package_share_directory("blueboat_bringup"),
        "config",
        "ros2_control_params.yaml"
    )
    try:
        with open(params_file, "r", encoding="utf-8") as stream:
            data = yaml.safe_load(stream) or {}
        return data.get("navigator_bridge", {}).get("ros__parameters", {}).get(
            "linear_lpf_alpha", 0.35
        )
    except Exception:
        return 0.35


def _load_thruster_lpf_alpha():
    params_file = os.path.join(
        get_package_share_directory("blueboat_bringup"),
        "config",
        "ros2_control_params.yaml"
    )
    try:
        with open(params_file, "r", encoding="utf-8") as stream:
            data = yaml.safe_load(stream) or {}
        return data.get("thrusters_system", {}).get("ros__parameters", {}).get(
            "thruster_lpf_alpha", 0.25
        )
    except Exception:
        return 0.25


def _launch_stonefish_if_needed(context, lookup_csv):
    environment = LaunchConfiguration("environment").perform(context)
    if environment != "sim":
        return []

    stonefish_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("blueboat_stonefish_core"),
                "launch",
                "blueboat_cirtesu_fastlio.launch.py"
            )
        ),
        launch_arguments={
            "lookup_csv": lookup_csv.perform(context),
        }.items(),
    )
    return [stonefish_launch]


def generate_launch_description():
    environment = LaunchConfiguration("environment")
    lookup_csv = LaunchConfiguration("lookup_csv")
    thruster_lpf_alpha = LaunchConfiguration("thruster_lpf_alpha")

    enable_gps = LaunchConfiguration("enable_gps")
    enable_gps_anchor = LaunchConfiguration("enable_gps_anchor")

    use_teleop = LaunchConfiguration("use_teleop")
    teleop_config_file = LaunchConfiguration("teleop_config_file")
    joy_device_id = LaunchConfiguration("joy_device_id")

    navigator_linear_lpf_alpha = _load_navigator_bridge_alpha()
    thruster_lpf_alpha_default = _load_thruster_lpf_alpha()

    bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("blueboat_bringup"),
                "launch",
                "bringup.launch.py"
            )
        ),
        launch_arguments={
            "environment": environment,
            "lookup_csv": lookup_csv,
            "thruster_lpf_alpha": thruster_lpf_alpha,
            "enable_gps": enable_gps,
            "enable_gps_anchor": enable_gps_anchor,
        }.items()
    )

    navigator_common_params = [{
        "navigator_topic": "/navigator_msg",
        "linear_lpf_alpha": navigator_linear_lpf_alpha,
    }]

    navigator_sim_params = navigator_common_params + [{
        "odom_topic": "/catamaran/odometry",
        "odom_twist_in_body_frame": True,
        "odom_invert_angular_z": False,
        "twist_odom_topic": "/blueboat/navigator/odometry",
        "twist_odom_twist_in_body_frame": True,
        "twist_odom_invert_angular_z": False,
    }]

    navigator_real_params = navigator_common_params + [{
        "odom_topic": "/catamaran/odometry",
        "odom_twist_in_body_frame": True,
        "odom_invert_angular_z": True,
    }]

    navigator_sim_node = Node(
        package="catamaran_navigator",
        executable="navigator_sim",
        name="navigator_sim",
        output="screen",
        parameters=navigator_sim_params,
        condition=IfCondition(
            PythonExpression(["'", environment, "' == 'sim'"])
        )
    )

    tf_debug_poses_node = Node(
        package="blueboat_stonefish_core",
        executable="tf_debug_poses.py",
        name="tf_debug_poses",
        output="screen",
        parameters=[{
            "world_frame": "world_ned",
            "map_frame": "map",
            "base_link_enu_frame": "blueboat/base_link_enu",
            "base_link_frame": "blueboat/base_link",
            "base_link_enu_topic": "/debug/base_link_enu_pose",
            "map_base_link_enu_topic": "/debug/map_base_link_enu_pose",
            "base_link_topic": "/debug/base_link_pose",
            "publish_rate_hz": 10.0,
        }],
        condition=IfCondition(
            PythonExpression(["'", environment, "' == 'sim'"])
        )
    )

    navigator_real_node = Node(
        package="catamaran_navigator",
        executable="navigator_real",
        name="navigator_real",
        output="screen",
        parameters=navigator_real_params,
        condition=IfCondition(
            PythonExpression(["'", environment, "' == 'real'"])
        )
    )

    teleop_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("blueboat_teleop"),
                "launch",
                "blueboat_teleop.launch.py"
            )
        ),
        launch_arguments={
            "config_file": teleop_config_file,
            "joy_device_id": joy_device_id,
        }.items(),
        condition=IfCondition(use_teleop)
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            "environment",
            default_value="real",
            description="Execution environment: real or sim"
        ),
        DeclareLaunchArgument(
            "lookup_csv",
            default_value="",
            description="Path to thruster lookup CSV"
        ),
        DeclareLaunchArgument(
            "thruster_lpf_alpha",
            default_value=str(thruster_lpf_alpha_default),
            description="Low-pass alpha for thruster commands in ThrustersSystem"
        ),
        DeclareLaunchArgument(
            "enable_gps",
            default_value="true",
            description="Launch GPS node through blueboat_bringup"
        ),
        DeclareLaunchArgument(
            "enable_gps_anchor",
            default_value="false",
            description="Launch GPS anchor node through blueboat_bringup"
        ),
        DeclareLaunchArgument(
            "use_teleop",
            default_value="false",
            description="Launch joy_node and blueboat_teleop for gamepad control"
        ),
        DeclareLaunchArgument(
            "teleop_config_file",
            default_value=os.path.join(
                get_package_share_directory("blueboat_teleop"),
                "config",
                "logitech_f310.yaml"
            ),
            description="Teleop config file for the selected gamepad"
        ),
        DeclareLaunchArgument(
            "joy_device_id",
            default_value="0",
            description="Joystick device index passed to joy_node"
        ),

        bringup_launch,

        OpaqueFunction(function=_launch_stonefish_if_needed, kwargs={
            "lookup_csv": lookup_csv,
        }),

        navigator_sim_node,
        tf_debug_poses_node,
        navigator_real_node,
        teleop_launch,
    ])