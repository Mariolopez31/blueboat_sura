from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    environment = LaunchConfiguration("environment")
    lookup_csv = LaunchConfiguration("lookup_csv")

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
        bringup_launch,
        stonefish_launch,
    ])