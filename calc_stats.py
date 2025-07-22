import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

def check_normal_distribution(data, alpha=0.05, plot_results=True):
    """
    Checks if a list of numbers follows a normal distribution using multiple tests
    and optionally plots the data distribution.

    Args:
        data (list or np.array): A list or NumPy array of numerical data.
        alpha (float): The significance level for the statistical tests.
                       Commonly 0.05 (5%).
        plot_results (bool): If True, generates a histogram and Q-Q plot.

    Returns:
        dict: A dictionary containing the results of the tests:
              {
                  "shapiro_wilk_p_value": float,
                  "shapiro_wilk_is_normal": bool,
                  "kstest_p_value": float,        # Kolmogorov-Smirnov test
                  "kstest_is_normal": bool,
                  "dagostino_pearson_p_value": float,
                  "dagostino_pearson_is_normal": bool,
                  "anderson_darling_statistic": float,
                  "anderson_darling_critical_values": list,
                  "anderson_darling_significance_level": list,
                  "anderson_darling_is_normal": bool (based on 5% significance)
              }
    """
    if not isinstance(data, (list, np.ndarray)):
        raise TypeError("Input data must be a list or NumPy array.")
    if len(data) < 3: # Some tests require at least 3 data points
        print("Warning: Data size is too small for some normality tests (need at least 3 points).")
        # You might want to return None or raise an error for very small datasets
        # depending on how strictly you want to enforce test requirements.
        # For this example, we'll proceed but note the limitation.

    data_array = np.array(data)
    results = {}

    # 1. Shapiro-Wilk Test (often preferred for smaller samples < 5000)
    # Null hypothesis: The data is drawn from a normal distribution.
    if len(data_array) >= 3: # Shapiro-Wilk needs at least 3 samples
        shapiro_stat, shapiro_p = stats.shapiro(data_array)
        results["shapiro_wilk_p_value"] = shapiro_p
        results["shapiro_wilk_is_normal"] = shapiro_p > alpha
    else:
        results["shapiro_wilk_p_value"] = None
        results["shapiro_wilk_is_normal"] = None
        print("Shapiro-Wilk test skipped due to insufficient data size.")


    # 2. Kolmogorov-Smirnov (K-S) Test (comparing to a standard normal distribution)
    # Null hypothesis: The data comes from the specified distribution (here, normal).
    # For K-S test against a normal distribution, we need to specify 'norm'
    # and often standardize the data or pass the mean and std.
    # However, scipy.stats.kstest(data, 'norm') tests against a *standard* normal (mean=0, std=1).
    # For a more general test, you can use stats.kstest(data, stats.norm.cdf, args=(np.mean(data), np.std(data)))
    # but this makes the p-values conservative.
    # A common alternative is to use Lilliefors test (a modification of K-S for estimated parameters)
    # which is available in statsmodels: from statsmodels.stats.diagnostic import lilliefors
    # For simplicity here, we'll use the basic K-S against a standard normal,
    # acknowledging its limitations for testing general normality.
    # For a more robust K-S, consider standardizing your data first if you assume it's normal.
    if len(data_array) > 0: # K-S test needs at least 1 sample
        kstest_stat, kstest_p = stats.kstest(data_array, 'norm') # Test against standard normal
        results["kstest_p_value"] = kstest_p
        results["kstest_is_normal"] = kstest_p > alpha
    else:
        results["kstest_p_value"] = None
        results["kstest_is_normal"] = None
        print("Kolmogorov-Smirnov test skipped due to empty data.")


    # 3. D'Agostino and Pearson's Test (combines skewness and kurtosis)
    # Null hypothesis: The data is drawn from a normal distribution.
    if len(data_array) >= 8: # D'Agostino-Pearson needs at least 8 samples
        dagostino_stat, dagostino_p = stats.normaltest(data_array)
        results["dagostino_pearson_p_value"] = dagostino_p
        results["dagostino_pearson_is_normal"] = dagostino_p > alpha
    else:
        results["dagostino_pearson_p_value"] = None
        results["dagostino_pearson_is_normal"] = None
        print("D'Agostino-Pearson test skipped due to insufficient data size (need at least 8).")


    # 4. Anderson-Darling Test
    # Null hypothesis: The data is drawn from a particular distribution (e.g., normal).
    # Returns critical values for different significance levels.
    if len(data_array) > 0:
        anderson_result = stats.anderson(data_array, dist='norm')
        results["anderson_darling_statistic"] = anderson_result.statistic
        results["anderson_darling_critical_values"] = anderson_result.critical_values.tolist()
        results["anderson_darling_significance_level"] = anderson_result.significance_level.tolist()
        # Check if statistic is less than critical value for 5% significance
        # The significance levels are typically 15%, 10%, 5%, 2.5%, 1%
        # We'll check against the 5% level (index 2)
        if len(anderson_result.critical_values) > 2: # Ensure 5% level exists
             results["anderson_darling_is_normal"] = anderson_result.statistic < anderson_result.critical_values[2]
        else:
             results["anderson_darling_is_normal"] = None # Or handle differently
    else:
        results["anderson_darling_statistic"] = None
        results["anderson_darling_critical_values"] = None
        results["anderson_darling_significance_level"] = None
        results["anderson_darling_is_normal"] = None
        print("Anderson-Darling test skipped due to empty data.")


    # Optional: Plotting
    if plot_results and len(data_array) > 0:
        plt.figure(figsize=(12, 5))

        plt.subplot(1, 2, 1)
        sns.histplot(data_array, kde=True)
        plt.title('Histogram of Data')
        plt.xlabel('Value')
        plt.ylabel('Frequency')

        plt.subplot(1, 2, 2)
        stats.probplot(data_array, dist="norm", plot=plt)
        plt.title('Q-Q Plot')

        plt.tight_layout()
        plt.show()

    return results


def check_normality(data, alpha=0.05):
    # uses check_normal_distribution function
    """
    Checks if the provided data sample follows a normal distribution
    """
    results = check_normal_distribution(data, alpha=alpha, plot_results=False)
    return  results.get("shapiro_wilk_is_normal", None) or results.get("kstest_is_normal", None) or results.get("dagostino_pearson_is_normal", None) or results.get("anderson_darling_is_normal", None)

def compare_independent_samples(sample1, sample2, alpha=0.05, equal_var_assumption='auto'):
    """
    Compares two independent data samples using an appropriate statistical test
    based on the normality of the data and variance assumptions.

    Args:
        sample1 (list or np.array): The first data sample.
        sample2 (list or np.array): The second data sample.
        alpha (float): The significance level for the statistical tests.
        equal_var_assumption (str or bool):
            'auto': Performs Levene's test to check for equal variances if data is normal.
            True: Assumes equal variances (uses standard Independent T-test).
            False: Assumes unequal variances (uses Welch's T-test).

    Returns:
        dict: A dictionary containing the test name, statistic, p-value,
              and an interpretation of the result.
    """
    if not isinstance(sample1, (list, np.ndarray)) or not isinstance(sample2, (list, np.ndarray)):
        raise TypeError("Input samples must be lists or NumPy arrays.")

    s1 = np.array(sample1)
    s2 = np.array(sample2)

    if len(s1) == 0 or len(s2) == 0:
        raise ValueError("Input samples cannot be empty.")

    # 1. Check normality for both samples
    is_s1_normal = check_normality(s1, alpha)
    is_s2_normal = check_normality(s2, alpha)

    print(f"Sample 1 normality (Shapiro-Wilk p > {alpha}): {is_s1_normal}")
    print(f"Sample 2 normality (Shapiro-Wilk p > {alpha}): {is_s2_normal}")

    result = {"test_used": None, "statistic": None, "p_value": None, "interpretation": None}

    if is_s1_normal and is_s2_normal:
        # Both samples appear normally distributed - use T-test
        print("Both samples appear normally distributed. Proceeding with T-test.")

        # 2a. Check for homogeneity of variances (if equal_var_assumption is 'auto')
        if equal_var_assumption == 'auto':
            if len(s1) < 3 or len(s2) < 3: # Levene's might not be reliable for very small samples
                print("Warning: Levene's test might be unreliable for very small sample sizes. Consider manually setting equal_var.")
                # Defaulting to Welch's T-test (equal_var=False) for safety with small samples if auto
                equal_variances = False
            else:
                levene_stat, levene_p = stats.levene(s1, s2)
                print(f"Levene's test for equal variances: p-value = {levene_p:.4f}")
                if levene_p > alpha:
                    print("Levene's test suggests variances are equal.")
                    equal_variances = True
                else:
                    print("Levene's test suggests variances are NOT equal.")
                    equal_variances = False
        elif isinstance(equal_var_assumption, bool):
            equal_variances = equal_var_assumption
        else:
            raise ValueError("equal_var_assumption must be 'auto', True, or False.")

        if equal_variances:
            print("Using Independent Two-Sample T-test (assuming equal variances).")
            result["test_used"] = "Independent T-test (equal variances)"
            t_stat, p_val = stats.ttest_ind(s1, s2, equal_var=True, nan_policy='raise')
        else:
            print("Using Welch's T-test (assuming unequal variances).")
            result["test_used"] = "Welch's T-test (unequal variances)"
            t_stat, p_val = stats.ttest_ind(s1, s2, equal_var=False, nan_policy='raise')

        result["statistic"] = t_stat
        result["p_value"] = p_val
        if p_val < alpha:
            result["interpretation"] = f"Reject null hypothesis (p={p_val:.4f}). There is a statistically significant difference between the means of the two samples."
        else:
            result["interpretation"] = f"Fail to reject null hypothesis (p={p_val:.4f}). There is no statistically significant difference between the means of the two samples."

    else:
        # At least one sample is not normally distributed - use non-parametric test
        print("At least one sample does not appear normally distributed. Using Mann-Whitney U test.")
        result["test_used"] = "Mann-Whitney U test"
        # Mann-Whitney U test: Null hypothesis is that for randomly selected values X and Y
        # from the two populations, the probability of X being greater than Y is equal
        # to the probability of Y being greater than X.
        # (Often interpreted as testing for differences in medians or distributions)
        try:
            u_stat, p_val = stats.mannwhitneyu(s1, s2, alternative='two-sided', nan_policy='raise')
            result["statistic"] = u_stat
            result["p_value"] = p_val
            if p_val < alpha:
                result["interpretation"] = f"Reject null hypothesis (p={p_val:.4f}). There is a statistically significant difference in the distributions of the two samples."
            else:
                result["interpretation"] = f"Fail to reject null hypothesis (p={p_val:.4f}). There is no statistically significant difference in the distributions of the two samples."
        except ValueError as e:
            # This can happen if all values in one sample are identical to all in the other
            # or if one sample has all identical values and the other is also small.
            result["statistic"] = None
            result["p_value"] = None
            result["interpretation"] = f"Mann-Whitney U test could not be performed: {e}. This might happen with identical samples or very specific data configurations."
            print(f"Warning: {result['interpretation']}")


    return result

# --- Example Usage ---
if __name__ == "__main__":
    # Example 1: Normally distributed data
    normal_data = [0.4285714285714286,
 0.45454545454545453,
 0.5714285714285714,
 0.8333333333333334,
 0.8034188034188033,
 0.7964601769911505,
 0.66,
 0.5806451612903226,
 0.7378640776699029,
 0.6386554621848739,
 0.6440677966101694,
 0.7786259541984734]
    normal_data1 = [

        0.5319148936170212,
        0.5744680851063829,
        0.6041666666666666,
        0.7931034482758621,
        0.8135593220338982,
        0.8429752066115703,
        0.5,
        0.4651162790697674,
        0.7070707070707071,
        0.6962962962962962,
        0.7343750000000001,
        0.787878787878788
    ]
    print("--- Checking Normally Distributed Data ---")
    normal_results = check_normal_distribution(normal_data1, alpha=0.05)
    for test, p_val_or_is_normal in normal_results.items():
        print(f"{test}: {p_val_or_is_normal}")
    print("\nInterpretation (for p-value based tests):")
    if normal_results.get("shapiro_wilk_is_normal") is not None:
        print(f"Shapiro-Wilk: Data {'looks normal' if normal_results['shapiro_wilk_is_normal'] else 'does NOT look normal'} (p={normal_results['shapiro_wilk_p_value']:.4f})")
    if normal_results.get("kstest_is_normal") is not None:
        print(f"K-S Test: Data {'looks normal' if normal_results['kstest_is_normal'] else 'does NOT look normal'} (p={normal_results['kstest_p_value']:.4f})")
    if normal_results.get("dagostino_pearson_is_normal") is not None:
        print(f"D'Agostino-Pearson: Data {'looks normal' if normal_results['dagostino_pearson_is_normal'] else 'does NOT look normal'} (p={normal_results['dagostino_pearson_p_value']:.4f})")
    if normal_results.get("anderson_darling_is_normal") is not None:
        print(f"Anderson-Darling (at 5%): Data {'looks normal' if normal_results['anderson_darling_is_normal'] else 'does NOT look normal'} (stat={normal_results['anderson_darling_statistic']:.4f})")

    print("-" * 30)
    results3 = compare_independent_samples(normal_data, normal_data1, alpha=0.05, equal_var_assumption='auto')
    print(f"Test: {results3['test_used']}")
    if results3[
        'statistic'] is not None:  # Mann-Whitney U might not always compute a typical 'statistic' in some outputs
        print(f"Statistic: {results3['statistic']:.4f}")
    print(f"P-value: {results3['p_value']:.4f}")
    print(f"Interpretation: {results3['interpretation']}")
    print("-" * 40)


