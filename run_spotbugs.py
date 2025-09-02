# analyze_android_project.py

import os
import subprocess
import argparse
import sys
import re

# --- Configuration ---
# You can hardcode these paths if you don't want to pass them as arguments
# Example: SPOTBUGS_HOME = "/opt/spotbugs-4.7.3"
SPOTBUGS_HOME = os.path.join(os.environ.get("HOME"), "spotbugs",  'spotbugs-4.9.3')
ANDROID_SDK_ROOT = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")


def find_compile_sdk_version(project_path):
    """
    Parses the app's build.gradle file to find the compileSdkVersion.
    This is more reliable than guessing the platform version.
    """
    build_gradle_path = os.path.join(project_path, "app", "build.gradle")
    if not os.path.exists(build_gradle_path):
        # Also check for build.gradle.kts (Kotlin script)
        build_gradle_path = os.path.join(project_path, "app", "build.gradle.kts")
        if not os.path.exists(build_gradle_path):
            return None

    try:
        with open(build_gradle_path, 'r') as f:
            content = f.read()
            # Regex to find 'compileSdk' or 'compileSdkVersion' followed by a number
            match = re.search(r'compileSdk(?:Version)?\s*=?\s*(\d+)', content)
            if match:
                return match.group(1)
    except Exception as e:
        print(f"Warning: Could not read compile SDK version from {build_gradle_path}: {e}")
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Run SpotBugs analysis on an Android project.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("project_path", help="Path to the root of the Android project.")
    parser.add_argument(
        "--spotbugs-home",
        default=SPOTBUGS_HOME,
        help="Path to the SpotBugs installation directory. \n(Defaults to SPOTBUGS_HOME environment variable)"
    )
    parser.add_argument(
        "--sdk-root",
        default=ANDROID_SDK_ROOT,
        help="Path to the Android SDK root directory. \n(Defaults to ANDROID_HOME or ANDROID_SDK_ROOT env vars)"
    )
    parser.add_argument(
        "--variant",
        default="debug",
        help="The build variant to analyze (e.g., 'debug', 'release'). Default is 'debug'."
    )
    parser.add_argument(
        "--format",
        choices=['html', 'xml'],
        default='xml',
        help="The output format for the report. Default is 'html'."
    )
    parser.add_argument(
        "--output",
        default="spotbugs_report",
        help="The base name for the output report file. The extension will be added automatically."
    )

    parser.add_argument(
        "--plugin",
        help="Path to an additional SpotBugs plugin JAR file to include in the analysis."
    )

    args = parser.parse_args()

    # --- 1. Validate paths ---
    if not args.spotbugs_home:
        print("Error: SpotBugs home directory not found.")
        print("Please set the SPOTBUGS_HOME environment variable or use the --spotbugs-home argument.")
        sys.exit(1)

    if not args.sdk_root:
        print("Error: Android SDK root not found.")
        print("Please set the ANDROID_HOME environment variable or use the --sdk-root argument.")
        sys.exit(1)

    if not os.path.isdir(args.project_path):
        print(f"Error: Project path '{args.project_path}' does not exist or is not a directory.")
        sys.exit(1)

    print("--- Configuration ---")
    print(f"Project Path:    {args.project_path}")
    print(f"SpotBugs Home:   {args.spotbugs_home}")
    print(f"Android SDK:     {args.sdk_root}")
    print(f"Build Variant:   {args.variant}")
    print(f"Output Format:   {args.format}")
    print("---------------------\n")

    # --- 2. Locate necessary files and directories ---

    # SpotBugs executable
    spotbugs_executable = os.path.join(args.spotbugs_home, "bin", "spotbugs")
    if sys.platform == "win32":
        spotbugs_executable += ".bat"

    if not os.path.exists(spotbugs_executable):
        print(f"Error: SpotBugs executable not found at '{spotbugs_executable}'")
        sys.exit(1)

    # Android class files to analyze
    # Note: This path can change with Android Gradle Plugin versions.
    classes_path = os.path.join(
        args.project_path, "app", "build", "intermediates", "javac", args.variant, "classes"
    )
    if not os.path.isdir(classes_path):
        print(f"Error: Compiled classes not found at '{classes_path}'")
        print("Have you built the project at least once? (e.g., './gradlew assembleDebug')")
        sys.exit(1)

    # Java source files (for more detailed reports)
    source_path = os.path.join(args.project_path, "app", "src", "main", "java")
    if not os.path.isdir(source_path):
        print(f"Warning: Source path '{source_path}' does not exist.")
        print("SpotBugs will still run, but source code links in the report may not work.")
        source_path = None

    # Android platform JAR (auxiliary classpath)
    sdk_version = find_compile_sdk_version(args.project_path)
    if not sdk_version:
        print("Warning: Could not determine compileSdkVersion. Defaulting to a common version like '33'.")
        print("Analysis might be inaccurate. Please check your app/build.gradle file.")
        sdk_version = "33"  # A reasonable fallback

    android_jar = os.path.join(args.sdk_root, "platforms", f"android-{sdk_version}", "android.jar")
    if not os.path.exists(android_jar):
        print(f"Error: android.jar not found for SDK version {sdk_version} at '{android_jar}'")
        print(f"Please make sure you have Android SDK Platform {sdk_version} installed via the SDK Manager.")
        sys.exit(1)

    # --- 3. Construct and Run the SpotBugs Command ---
    output_file = f"{args.output}.{args.format}"

    spotbugs_command = [
        spotbugs_executable,
        "-textui",  # Use the command-line user interface
        f"-{args.format}",  # Set the output format (e.g., -html, -xml)
        f"-output", output_file,
        "-effort:max",  # Use maximum effort for finding bugs
        "-auxclasspath", android_jar,  # Provide Android framework as a library
        "-sourcepath" if source_path is not None else '', source_path if source_path is not None else '',  # Provide source code for better reports
        classes_path  # The directory of .class files to analyze
    ]

    ### NEW ###
    # Add the plugin to the command if the user provided one
    if args.plugin:
        if not os.path.exists(args.plugin):
            print(f"Error: Plugin JAR not found at '{args.plugin}'")
            sys.exit(1)
        print(f"Including Plugin:  {args.plugin}")
        spotbugs_command.extend(["-pluginList", args.plugin])
    ### END NEW ###

    print("Running SpotBugs analysis... This may take a few minutes.")
    print(f"Command: {' '.join(spotbugs_command)}")

    try:
        process = subprocess.run(
            spotbugs_command,
            capture_output=True,
            text=True,
            check=False  # Don't automatically raise exception on non-zero exit code
        )


        if process.returncode != 0:
            print("\n--- SpotBugs finished with errors ---")
            print("Return Code:", process.returncode)
            # SpotBugs often prints analysis summary to stdout and errors to stderr
            if process.stdout:
                print("\n--- STDOUT ---")
                print(process.stdout)
            if process.stderr:
                print("\n--- STDERR ---")
                print(process.stderr)
            print("---------------------------------------")
        else:
            print("\nAnalysis finished successfully!")
            print(f"Report saved to: {os.path.abspath(output_file)}")

    except FileNotFoundError:
        print(f"Error: Command not found '{spotbugs_executable}'. Is SpotBugs installed correctly?")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()