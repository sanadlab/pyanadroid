# Installation Guide

This guide gives the instructions to install PyAnaDroid.

## Prerequisites

- Python 3.9 or later.
- The Android SDK. Set the `ANDROID_HOME` environment variable and put `adb` in the `PATH`.
- A JDK. PyAnaDroid selects JDK 8, 11, 17 or 21 for each project (see "JDK selection" in `README.md`).
- For tests on a device: an Android device or emulator that `adb devices` shows.

See `requirements.md` for the full list.

## Install from PyPI

```bash
pip install anadroid
```

## Install from source

```bash
git clone --recurse-submodules https://github.com/sanadlab/pyanadroid.git
cd pyanadroid
pip install -e .
```

## Download the external tools

PyAnaDroid runs external jars (JInst, DAAP, aDoctor and others). Download them one time:

```bash
pyanadroid --setup
```

PMD, SpotBugs, Detekt and Infer are not downloaded. Install them if you use the related static analyzers.

## Verify the installation

```bash
pyanadroid -h
```

## Upgrade

```bash
pip install -U anadroid
```

## Uninstall

```bash
pip uninstall anadroid
```
