#!/usr/bin/env python
#                   ,*++++++*,                ,*++++++*,
#                *++.        .+++          *++.        .++*
#              *+*     ,++++*   *+*      *+*   ,++++,     *+*
#             ,+,   .++++++++++* ,++,,,,*+, ,++++++++++.   *+,
#             *+.  .++++++++++++..++    *+.,++++++++++++.  .+*
#             .+*   ++++++++++++.*+,    .+*.++++++++++++   *+,
#              .++   *++++++++* ++,      .++.*++++++++*   ++,
#               ,+++*.    . .*++,          ,++*.      .*+++*
#              *+,   .,*++**.                  .**++**.   ,+*
#             .+*                                          *+,
#             *+.                   Coqui                  .+*
#             *+*              +++   TTS  +++              *+*
#             .+++*.            .          .             *+++.
#              ,+* *+++*...                       ...*+++* *+,
#               .++.    .""""+++++++****+++++++"""".     ++.
#                 ,++.                                .++,
#                   .++*                            *++.
#                       *+++,                  ,+++*
#                           .,*++++::::::++++*,.
#                                  ``````

import os
import subprocess
import sys

import setuptools.command.build_py
import setuptools.command.develop
from setuptools import find_packages, setup


cwd = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(cwd, "TTS", "VERSION")) as fin:
    version = fin.read().strip()


class build_py(setuptools.command.build_py.build_py):  # pylint: disable=too-many-ancestors
    def run(self):
        setuptools.command.build_py.build_py.run(self)


class develop(setuptools.command.develop.develop):
    def run(self):
        setuptools.command.develop.develop.run(self)


# The documentation for this feature is in server/README.md
package_data = ["TTS/server/templates/*"]


def pip_install(package_name):
    subprocess.call([sys.executable, "-m", "pip", "install", package_name])


requirements = open(os.path.join(cwd, "requirements.txt"), "r").readlines()
with open(os.path.join(cwd, "requirements.notebooks.txt"), "r") as f:
    requirements_notebooks = f.readlines()
with open(os.path.join(cwd, "requirements.dev.txt"), "r") as f:
    requirements_dev = f.readlines()
with open(os.path.join(cwd, "requirements.ja.txt"), "r") as f:
    requirements_ja = f.readlines()
requirements_all = requirements_dev + requirements_notebooks + requirements_ja

with open("README.md", "r", encoding="utf-8") as readme_file:
    README = readme_file.read()

setup(
    name="TTS",
    version=version,
    url="https://github.com/coqui-ai/TTS",
    author="Eren Gölge",
    author_email="egolge@coqui.ai",
    description="Deep learning for Text to Speech by Coqui.",
    long_description=README,
    long_description_content_type="text/markdown",
    license="MPL-2.0",
    # package
    include_package_data=True,
    packages=find_packages(include=["TTS"], exclude=["*.tests", "*tests.*", "tests.*", "*tests", "tests"]),
    package_data={
        "TTS": [
            "VERSION",
        ]
    },
    project_urls={
        "Documentation": "https://github.com/coqui-ai/TTS/wiki",
        "Tracker": "https://github.com/coqui-ai/TTS/issues",
        "Repository": "https://github.com/coqui-ai/TTS",
        "Discussions": "https://github.com/coqui-ai/TTS/discussions",
    },
    cmdclass={
        "build_py": build_py,
        "develop": develop,
        # 'build_ext': build_ext
    },
    install_requires=requirements,
    extras_require={
        "all": requirements_all,
        "dev": requirements_dev,
        "notebooks": requirements_notebooks,
        "ja": requirements_ja,
    },
    python_requires=">=3.9.0, <3.12",
    entry_points={"console_scripts": ["tts=TTS.bin.synthesize:main", "tts-server = TTS.server.server:main"]},
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Operating System :: POSIX :: Linux",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    zip_safe=False,
)
