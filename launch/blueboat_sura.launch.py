from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node
import os


def generate_launch_description():
    environment = LaunchConfiguration("environment")
    lookup_csv = LaunchConfiguration("lookup_csv")
    use_teleop = LaunchConfiguration("use_teleop")
    teleop_config_file = LaunchConfiguration("teleop_config_file")
    joy_device_id = LaunchConfiguration("joy_device_id")

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
        }.items()
    )

    stonefish_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("blueboat_stonefish_core"),
                "launch",
                "blueboat_cirtesu_fastlio.launch.py"
            )
        ),
        launch_arguments={
            "lookup_csv": lookup_csv,
        }.items(),
        condition=IfCondition(
            PythonExpression(["'", environment, "' == 'sim'"])
        )
    )

    navigator_sim_node = Node(
        package="catamaran_navigator",
        executable="navigator_sim",
        name="navigator_sim",
        output="screen",
        parameters=[{
            # FastLIO publishes the odometry used by navigator_sim in sim.
            "odom_topic": "/catamaran/odometry",
            "navigator_topic": "/navigator_msg",
            "odom_twist_in_body_frame": False,
            "linear_lpf_alpha": 0.25,
        }],
        condition=IfCondition(
            PythonExpression(["'", environment, "' == 'sim'"])
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
        stonefish_launch,
        navigator_sim_node,
        teleop_launch,
    ])
