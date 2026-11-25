import sys

def calculate_median(values):
    """
    Calculates the median of a list of numerical values.
    """
    if not values:
        return None  # Or raise an error, depending on desired behavior

    sorted_values = sorted(values)
    n = len(sorted_values)
    midpoint = n // 2

    if n % 2 == 1:
        # Odd number of values, median is the middle one
        median = sorted_values[midpoint]
    else:
        # Even number of values, median is the average of the two middle ones
        median = (sorted_values[midpoint - 1] + sorted_values[midpoint]) / 2
    return median

if __name__ == "__main__":
    # sys.argv[0] is the script name, actual arguments start from index 1
    args = sys.argv[1:]

    if not args:
        print("Usage: python your_script_name.py <value1> <value2> ...")
        print("Example: python your_script_name.py 10 2 5 8 3")
        sys.exit(1) # Exit with an error code

    numbers = []
    invalid_args = []

    for arg in args:
        try:
            # Attempt to convert argument to a float (to handle decimals)
            num = float(arg)
            numbers.append(num)
        except ValueError:
            invalid_args.append(arg)

    if invalid_args:
        print(f"Warning: The following arguments are not valid numbers and will be ignored: {', '.join(invalid_args)}")

    if not numbers:
        print("Error: No valid numerical values were provided.")
        sys.exit(1)

    median_value = calculate_median(numbers)

    if median_value is not None:
        print(f"Input values (after filtering non-numeric): {numbers}")
        print(f"Sorted values: {sorted(numbers)}")
        print(f"The median is: {median_value}")
    else:
        # This case should ideally be caught by the "if not numbers:" check above
        print("Error: Could not calculate median (empty dataset).")