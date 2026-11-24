from setuptools import setup


setup(
    name="arm_hardware_bridge",
    version="0.1.0",
    packages=["arm_hardware_bridge"],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/arm_hardware_bridge"]),
        ("share/arm_hardware_bridge", ["package.xml"]),
        ("share/arm_hardware_bridge/config", ["config/hardware.example.yaml"]),
    ],
    install_requires=["setuptools"],
    maintainer="Lab 2 team",
    maintainer_email="maintainer@example.com",
    description="UDP bridge for the ESP32.",
    license="Apache-2.0",
    entry_points={"console_scripts": ['udp_bridge = arm_hardware_bridge.bridge:main']},
)
