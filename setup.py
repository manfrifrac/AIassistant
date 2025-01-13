from setuptools import setup, find_packages

setup(
    name="ai-assistant",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "pytest",
        "pytest-asyncio",
        "psycopg2-binary",
        "sqlalchemy"
    ]
)
