import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="flight-log-bot",
    version="0.0.1",
    author="posts-scarcity",
    license='GPLv3',
    description="Quote-tweets posts from accounts known to be on the Epstein flight logs. Quote tweet will report the number of times they appear in flight logs from either court records or FOIA'd FAA documents.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/posts-scarcity/flight-log-bot",
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=['tweepy', 'pandas'],
    entry_points = {
        'console_scripts': [
            'flight-log-bot=flight-log-bot.bot:main',
            ],
    },
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
    ],
)
