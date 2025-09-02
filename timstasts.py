import statistics
import re, sys

def parse_time(s):
    """
    Converts a string like '2m 4s' or '36s' into total seconds as integer.
    """
    minutes = 0
    seconds = 0
    # Match groups like '2m' and '4s'
    matches = re.findall(r'(\d+)\s*m?', s)
    if 'm' in s:
        # If minutes exist, assume first match is minutes
        minutes = int(matches[0])
        if len(matches) > 1:
            seconds = int(matches[1])
    elif 's' in s:
        # Only seconds
        seconds = int(matches[0])
    return minutes * 60 + seconds

def read_times_from_file(filename):
    """
    Reads times from file and returns a list of values in seconds.
    """
    times_in_seconds = []
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or not re.search(r'\d', line):  # skip blank or non-time lines
                continue
            total_seconds = parse_time(line)
            times_in_seconds.append(total_seconds)
    return times_in_seconds

def main(filename):
    #filename = "times.txt"  # filename goes here
    times = read_times_from_file(filename)
    if not times:
        print("No valid times found.")
        return
    average = statistics.mean(times)
    median = statistics.median(times)
    print(f"Average: {average:.2f} seconds")
    print(f"Median: {median:.2f} seconds")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "times.txt")
