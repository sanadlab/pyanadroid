# Requirements for PyAnaDroid

## Overview

PyAnaDroid automates the analysis and benchmarking of the energy consumption of Android applications.
It can instrument and build the source code of an application, run tests with different testing frameworks, measure energy with different profilers, and run static analyzers.

## System requirements

- A Unix-like operating system (Linux or macOS).
- Python 3.9 or later, with `pip`.
- The Android SDK, with the `ANDROID_HOME` environment variable set and `adb` in the `PATH`.
- A JDK for the Gradle version of each project (8, 11, 17 or 21). Set `JAVA_HOME_<version>` if PyAnaDroid does not find it.
- An Android device or emulator, for the tests that run applications.

## Python dependencies

The dependencies are in `requirements.txt`. `pip` installs them with the package.

## External tools

- Jars that PyAnaDroid runs (JInst, DAAP, aDoctor, EcoAndroid resource leaks, DroidLens and others). `pyanadroid --setup` downloads them. The list is in `src/anadroid/resources/tools.json`.
- Optional static analyzers that you install: PMD 7 (`PMD_HOME` or `PATH`), SpotBugs (`SPOTBUGS_HOME`), Detekt and Infer (`PATH`). The `Dockerfile` has an environment with SpotBugs, Detekt and Infer.

## Installation

See `install.md`.

## Usage

```
from anadroid.Anadroid import AnaDroid
from anadroid.Types import TESTING_FRAMEWORK

folder_of_app = "demoProjects/SampleApp"
anadroid = AnaDroid(folder_of_app, testing_framework=TESTING_FRAMEWORK.MONKEY)
anadroid.default_workflow()
```

## Tests

```
pip install pytest
python -m pytest                # unit tests, no device needed
python -m pytest tests/device   # tests that need a connected device
```

## Contributing

Contributions to PyAnaDroid are welcome. Run the unit tests and `ruff check src tests` before you open a pull request.

## License

This package is released under the MIT License.
