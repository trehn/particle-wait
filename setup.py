try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name="particle-wait",
    version="0.1.0",
    description="wait for particle.io events on the command line",
    author="Torsten Rehn",
    author_email="torsten@rehn.email",
    license="GPLv3",
    url="https://github.com/trehn/particle-wait",
    keywords=[
        "button",
        "console",
        "curses",
        "delay",
        "event",
        "iot",
        "particle",
        "terminal",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console :: Curses",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Operating System :: Unix",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Topic :: Utilities",
    ],
    install_requires=[
        "requests >= 1.0.0",
    ],
    py_modules=['particlewait'],
    entry_points={
        'console_scripts': [
            "particle-wait=particlewait:main",
        ],
    },
)
