from setuptools import setup

def readme():
    with open('README.md') as f:
        README = f.read()
    return README


setup(
    name="ez-life",
    version="1.0.1",
    description="A Python Package to make life ez for pythonistas",
    long_description=readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/Josiah-tan/ez_life",
    author="Josiah Tan",
    author_email="josiah123t@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
				"Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
				"Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    packages=["ez_life"],
    include_package_data=True,
    install_requires=[],
    entry_points={},
)
