from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="task_manager",
    version="1.0.0",
    author="Thomas Bagnardi",
    description="Simple CLI To-Do List Manager using JSON for storage",
    long_description=long_description,
    long_description_content_type="text/markdown",
    py_modules=["python_json_task_manager"],
    install_requires=[
        "rich>=10.0.0",
        "python-dateutil>=2.8.0",
    ],
    entry_points={
        "console_scripts": [
            "task-manager=python_json_task_manager:main",
        ],
    },
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
        ],
    },
    python_requires=">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
