from setuptools import setup


setup(
    name="arm_control",
    version="0.1.0",
    packages=["arm_control"],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/arm_control"]),
        ("share/arm_control", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    maintainer="Lab 2 team",
    maintainer_email="maintainer@example.com",
    description="Trajectory demo and sliders.",
    license="Apache-2.0",
    entry_points={"console_scripts": ['arm_demo = arm_control.demo:main', 'arm_gui = arm_control.gui:main']},
)
