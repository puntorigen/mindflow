from setuptools import setup, find_packages

setup(
    name="mindflow",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "customtkinter>=5.2.0"
    ],
    python_requires=">=3.12",
    author="Pablo Schaffner",
    description="A modern mindmap creation tool using CustomTkinter",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/pabloschaffner/mindflow",
    classifiers=[
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Office/Business :: Office Suites",
    ],
)
