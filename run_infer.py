# analyze_with_infer.py

import os
import subprocess
import argparse
import sys
import shutil


def run_command(command, cwd):
    """A helper function to run a command and exit on failure."""
    print(f"\n> Running command: {' '.join(command)}")
    try:
        process = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False  # Don't raise exception automatically
        )

        if process.returncode != 0:
            print(f"--- Command failed with exit code {process.returncode} ---")
            print("--- STDOUT ---")
            print(process.stdout)
            print("--- STDERR ---")
            print(process.stderr)
            print("-------------------------------------------------")
            sys.exit(1)
        else:
            print("--- Command finished successfully ---")
            # Print stdout for user feedback, especially for gradle
            if process.stdout:
                # Print only last few lines of Gradle output to avoid clutter
                lines = process.stdout.strip().splitlines()
                if len(lines) > 10:
                    print("... (truncated stdout)")
                    for line in lines[-10:]:
                        print(line)
                else:
                    print(process.stdout)

        return process

    except FileNotFoundError:
        print(f"Error: Command not found '{command[0]}'. Is it installed and in your PATH?")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Run Facebook's Infer analysis on an Android project.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("project_path", help="Path to the root of the Android project.")
    parser.add_argument(
        "--variant",
        default="debug",
        help="The build variant to analyze (e.g., 'debug', 'release'). Default is 'debug'."
    )
    parser.add_argument(
        '--no-clean',
        dest='clean',
        action='store_false',
        help="Do not run './gradlew clean' before the analysis. \n(Recommended to ensure a full capture)"
    )
    parser.add_argument(
        "--out",
        default="infer-out",
        help="The output directory for Infer's results. Default is 'infer-out'."
    )

    args = parser.parse_args()

    # --- 1. Validate prerequisites and paths ---
    if not shutil.which("infer"):
        print("Error: The 'infer' command was not found.")
        print("Please install Infer and ensure it is in your system's PATH.")
        print("Installation instructions: https://fbinfer.com/docs/getting-started/")
        sys.exit(1)

    project_path = os.path.abspath(args.project_path)
    if not os.path.isdir(project_path):
        print(f"Error: Project path '{project_path}' does not exist or is not a directory.")
        sys.exit(1)

    gradlew_path = os.path.join(project_path, "gradlew")
    if sys.platform == "win32":
        gradlew_path += ".bat"

    if not os.path.exists(gradlew_path):
        print(f"Error: Gradle wrapper 'gradlew' not found in '{project_path}'.")
        print("Please run this script from the root of a valid Android project.")
        sys.exit(1)

    print("--- Configuration ---")
    print(f"Project Path:  {project_path}")
    print(f"Build Variant: {args.variant}")
    print(f"Output Dir:    {args.out}")
    print(f"Run Clean:     {args.clean}")
    print("---------------------\n")

    # --- 2. Handle existing output directory ---
    infer_out_dir = os.path.join(project_path, args.out)
    if os.path.exists(infer_out_dir):
        choice = input(f"The output directory '{infer_out_dir}' already exists. Remove it? (y/n): ").lower()
        if choice == 'y':
            print(f"Removing existing directory: {infer_out_dir}")
            shutil.rmtree(infer_out_dir)
        else:
            print("Aborting. Please remove the directory manually or use a different output directory with --out.")
            sys.exit(0)

    # --- 3. Construct and Run the Infer Commands ---

    # Command to clean the project
    if args.clean:
        clean_command = [gradlew_path, "clean"]
        print("Step 1: Cleaning the Gradle project.")
        run_command(clean_command, cwd=project_path)

    # Command to capture the build
    # Infer works by wrapping the normal build command.
    build_task = f"assemble{args.variant.capitalize()}"
    capture_command = [
        "infer", "capture",
        "--out", infer_out_dir,
        '--keep-going',
        "--",  # Separator: the rest of the command is the build command
        gradlew_path,
        build_task
    ]
    print(f"Step 2: Capturing the build with Infer (Task: {build_task}). This will take a while.")
    run_command(capture_command, cwd=project_path)

    # Command to analyze the captured data
    analyze_command = ["infer", "analyze", "--out", infer_out_dir]
    print("Step 3: Analyzing the captured data.")
    run_command(analyze_command, cwd=project_path)

    # --- 4. Final Report ---
    print("\n\n✅ Infer analysis complete!")
    print("Results are located in:", infer_out_dir)
    print(f"  - Human-readable report: {os.path.join(infer_out_dir, 'report.txt')}")
    print(f"  - Machine-readable report: {os.path.join(infer_out_dir, 'report.json')}")


if __name__ == "__main__":
    main()