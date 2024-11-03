from setuptools import setup, find_packages

setup(
    name="defi_health",
    version="0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pandas",
        "aiohttp",
        "asyncio",
    ],
)