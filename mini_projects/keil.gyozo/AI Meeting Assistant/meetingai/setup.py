"""
Setup script for MeetingAI
"""

from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="meetingai",
    version="0.1.0",
    description="AI-Powered Meeting Note Taker + Task Assigner + Summarizer Agent",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="MeetingAI Team",
    author_email="team@meetingai.com",
    url="https://github.com/meetingai/meetingai",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=requirements,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    entry_points={
        "console_scripts": [
            "meetingai=meetingai.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)