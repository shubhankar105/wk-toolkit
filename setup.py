from setuptools import setup, find_packages

setup(
    name="wk-toolkit",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.1",
        "rich>=13.0",
        "httpx>=0.25",
        "pydantic>=2.5",
        "python-dotenv>=1.0",
        "GitPython>=3.1",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "wk=wk_toolkit.cli:cli",
        ],
    },
)
