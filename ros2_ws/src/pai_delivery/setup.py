from setuptools import find_packages, setup

setup(
    name="pai_delivery",
    version="0.1.0",
    packages=find_packages(),
    package_data={"pai_delivery": ["data/*.json"]},
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/pai_delivery"]),
        ("share/pai_delivery", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=False,
    description="A minimal offline AI delivery robot",
    license="MIT",
    entry_points={"console_scripts": [
        "delivery = pai_delivery.node:main",
        "demo = pai_delivery.demo:main",
        "evaluate = pai_delivery.intent:main",
    ]},
)
