from setuptools import setup, find_packages

setup(
    name="my-ai-tools",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "dashscope",
        "sqlalchemy",
        "python-dotenv",
        "pandas",
        "openpyxl",  # for reading Excel files
    ],
)
