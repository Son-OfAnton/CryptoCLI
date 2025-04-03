from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="CryptoCLI",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    entry_points="""
        [console_scripts]
        CryptoCLI=app.main:cli
    """,
    author="Admas Terefe Girma",
    author_email="aadmasterefe00@gmail.com",
    description="A command-line tool for viewing cryptocurrency statistics from CoinGecko",
)