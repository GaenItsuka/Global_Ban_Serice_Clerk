import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="Global_Ban_Service_Clerk",
    version="0.8.0",
    author="Gaen Itsuka",
    author_email="",
    description="A python based telegram bot.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.24.1",
        "python-telegram-bot==20.0",
        "pandas==1.5.3",
        "Pillow==9.4.0",
        "Click==8.0.3",
        "matplotlib==3.6.3",
        "toml==0.10.2",
    ],
)
