import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

def check_normal_distribution(data, alpha=0.05, plot_results=False):
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


def calculate_cohens_d(group1, group2):
    """
    Calculates Cohen's d effect size for two independent samples.

    d = (mean1 - mean2) / pooled_std
    """
    n1, n2 = len(group1), len(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)

    # Calculate pooled standard deviation
    numerator = ((n1 - 1) * var1) + ((n2 - 1) * var2)
    denominator = n1 + n2 - 2
    pooled_std = np.sqrt(numerator / denominator)

    # Calculate Cohen's d
    d = (np.mean(group1) - np.mean(group2)) / pooled_std

    # Interpret
    abs_d = abs(d)
    if abs_d < 0.2:
        interpretation = "Negligible"
    elif abs_d < 0.5:
        interpretation = "Small"
    elif abs_d < 0.8:
        interpretation = "Medium"
    else:
        interpretation = "Large"

    return d, interpretation


def calculate_vargha_delaney_a(group1, group2):
    """
    Calculates Vargha and Delaney's A measure of stochastic superiority.
    Formula: A = (R1/n1 - (n1+1)/2) / n2
    Where R1 is the rank sum of group 1.

    Range: 0 to 1.
    0.5 = No difference (stochastic equality).
    >0.5 = Group 1 is stochastically larger.
    <0.5 = Group 2 is stochastically larger.
    """
    n1 = len(group1)
    n2 = len(group2)

    # Use Mann-Whitney U to get the rank sum logic handled efficiently
    # stats.mannwhitneyu returns U1.
    # The relationship is U1 = R1 - n1(n1+1)/2
    u_statistic, _ = stats.mannwhitneyu(group1, group2, alternative='two-sided')

    # Calculate A
    a = u_statistic / (n1 * n2)

    # Interpret (based on thresholds: 0.56=small, 0.64=medium, 0.71=large)
    dist_from_0_5 = abs(a - 0.5)
    if dist_from_0_5 < 0.06:
        interpretation = "Negligible"  # < 0.56
    elif dist_from_0_5 < 0.14:
        interpretation = "Small"  # < 0.64
    elif dist_from_0_5 < 0.21:
        interpretation = "Medium"  # < 0.71
    else:
        interpretation = "Large"

    return a, interpretation


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
    and calculates the appropriate effect size (Cohen's d or Vargha-Delaney A).
    """
    if not isinstance(sample1, (list, np.ndarray)) or not isinstance(sample2, (list, np.ndarray)):
        raise TypeError("Input samples must be lists or NumPy arrays.")

    s1 = np.array(sample1)
    s2 = np.array(sample2)

    if len(s1) == 0 or len(s2) == 0:
        raise ValueError("Input samples cannot be empty.")

    # 1. Check normality
    is_s1_normal = check_normality(s1, alpha)
    is_s2_normal = check_normality(s2, alpha)

    print(f"Sample 1 Normality Test Passed: {is_s1_normal}")
    print(f"Sample 2 Normality Test Passed: {is_s2_normal}")

    result = {
        "test_used": None,
        "statistic": None,
        "p_value": None,
        "interpretation": None,
        "effect_size_type": None,
        "effect_size_value": None,
        "effect_size_interpretation": None
    }

    # --- PARAMETRIC PATH (Both Normal) ---
    if is_s1_normal and is_s2_normal:
        print("Both samples appear normally distributed. Proceeding with T-test.")

        # Check Variance
        if equal_var_assumption == 'auto':
            if len(s1) < 3 or len(s2) < 3:
                equal_variances = False
            else:
                levene_stat, levene_p = stats.levene(s1, s2)
                equal_variances = levene_p > alpha
        elif isinstance(equal_var_assumption, bool):
            equal_variances = equal_var_assumption
        else:
            raise ValueError("equal_var_assumption must be 'auto', True, or False.")

        # T-Test
        if equal_variances:
            result["test_used"] = "Independent T-test (equal variances)"
            t_stat, p_val = stats.ttest_ind(s1, s2, equal_var=True, nan_policy='raise')
        else:
            result["test_used"] = "Welch's T-test (unequal variances)"
            t_stat, p_val = stats.ttest_ind(s1, s2, equal_var=False, nan_policy='raise')

        result["statistic"] = t_stat
        result["p_value"] = p_val

        # Calculate Cohen's d
        d_val, d_interp = calculate_cohens_d(s1, s2)
        result["effect_size_type"] = "Cohen's d"
        result["effect_size_value"] = d_val
        result["effect_size_interpretation"] = d_interp

        if p_val < alpha:
            result["interpretation"] = f"Significant difference (p={p_val:.4f}). Effect size: {d_interp} ({d_val:.2f})."
        else:
            result[
                "interpretation"] = f"No significant difference (p={p_val:.4f}). Effect size: {d_interp} ({d_val:.2f})."

    # --- NON-PARAMETRIC PATH (At least one not Normal) ---
    else:
        print("At least one sample does not appear normally distributed. Using Mann-Whitney U test.")
        result["test_used"] = "Mann-Whitney U test"

        try:
            u_stat, p_val = stats.mannwhitneyu(s1, s2, alternative='two-sided', nan_policy='raise')
            result["statistic"] = u_stat
            result["p_value"] = p_val

            # Calculate Vargha and Delaney's A
            a_val, a_interp = calculate_vargha_delaney_a(s1, s2)
            result["effect_size_type"] = "Vargha-Delaney A"
            result["effect_size_value"] = a_val
            result["effect_size_interpretation"] = a_interp

            if p_val < alpha:
                result[
                    "interpretation"] = (f"Significant difference (p={p_val:.4f}). Effect size: {a_interp} (A={a_val:.2f})."
                        + f"Reject null hypothesis (p={p_val:.4f}). There is a statistically significant difference between the means of the two samples.")
            else:
                result[
                    "interpretation"] = (f"No significant difference (p={p_val:.4f}). Effect size: {a_interp} (A={a_val:.2f})."
                        +  f"Fail to reject null hypothesis (p={p_val:.4f}). There is no statistically significant difference between the means of the two samples.")

        except ValueError as e:
            result["interpretation"] = f"Error performing Mann-Whitney U: {e}"

    return result


def check_normal(dataset):
    normal_results = check_normal_distribution(dataset, alpha=0.05)
    for test, p_val_or_is_normal in normal_results.items():
        print(f"{test}: {p_val_or_is_normal}")
    print("\nInterpretation (for p-value based tests):")
    if normal_results.get("shapiro_wilk_is_normal") is not None:
        print(
            f"Shapiro-Wilk: Data {'looks normal' if normal_results['shapiro_wilk_is_normal'] else 'does NOT look normal'} (p={normal_results['shapiro_wilk_p_value']:.4f})")
    if normal_results.get("kstest_is_normal") is not None:
        print(
            f"K-S Test: Data {'looks normal' if normal_results['kstest_is_normal'] else 'does NOT look normal'} (p={normal_results['kstest_p_value']:.4f})")
    if normal_results.get("dagostino_pearson_is_normal") is not None:
        print(
            f"D'Agostino-Pearson: Data {'looks normal' if normal_results['dagostino_pearson_is_normal'] else 'does NOT look normal'} (p={normal_results['dagostino_pearson_p_value']:.4f})")
    if normal_results.get("anderson_darling_is_normal") is not None:
        print(
            f"Anderson-Darling (at 5%): Data {'looks normal' if normal_results['anderson_darling_is_normal'] else 'does NOT look normal'} (stat={normal_results['anderson_darling_statistic']:.4f})")


# --- Example Usage ---
if __name__ == "__main__":
    # Example 1: Normally distributed data
    '''
    vibe_light_apd = [
         14.423076923076923, 8.620689655172415, 13.129102844638949, 29.247910863509752, 16.920473773265652,
         13.333333333333334, 6.5420560747663545, 9.97506234413965, 16.417910447761194, 5.338078291814946,
         2.364066193853428, 9.400705052878966
    ]
    similar_light_apd = [

        0.08268221092232006, 0.0, 0.0, 11.133088443063013, 0.5503736747581253, 3.108613056174836, 4.386429896633978,
         2.936138977244923, 12.19623191043961, 0.0, 0.010997349638737065, 0.0
    ]

    open_projs_light_apd = [
        0.038339148104129125, 0.0, 0.0, 4.728267061638373, 0.0, 11.363636363636363, 0.0, 0.0, 3.430173596611585, 0.0,
        4.212299915754002, 0.0, 8.46958314921196, 0.0, 0.03395816354251562, 0.0, 0.0, 16.675931072818234,
        8.13953488372093, 5.404014410705095, 7.374631268436579, 0.0, 0.0, 0.0, 8.849557522123895, 14.553014553014554,
        10.291262135922329, 16.516516516516518, 9.565764631843926, 1.6243183663998144, 0.0, 8.242085724503177,
        27.52293577981651, 0.3184423619324902, 8.227011571763818, 0.0, 0.4025224741714745, 0.6218607988519492,
        11.142061281337048, 0.0, 7.914659325533379, 9.037520391517129, 8.39705269011539, 11.782885841220786, 0.0,
        25.229357798165136, 6.938544321721891, 20.887728459530027, 0.0, 7.830783078307832, 14.574722645203392,
        17.241379310344826, 0.0, 0.0, 5.466207463110998, 0.0, 0.0, 7.882077932113672, 10.985748218527316,
        5.7174271577789995, 9.809932556713672, 0.8797476034461837, 23.970497848801475, 3.993827720795135,
        17.241379310344826, 11.658495755111803, 1.0423181154888472, 0.0, 17.142857142857142, 6.502554575011612,
        1.9807583474816073, 16.927083333333332, 2.284308557371288, 6.804123711340207, 6.772009029345372,
        5.35838552540014, 0.0, 0.0, 0.0, 16.224568632500645, 8.204838025180365, 16.343207354443308, 11.24859392575928,
        5.426885323685537, 19.144144144144143, 1.7678761456867256, 3.1077694235588975, 0.0, 4.249512670565302,
        4.184100418410042, 7.064446662114606, 9.968467093886686, 8.377500427423492, 6.783545319124556,
        3.8422284925256647, 14.640948175691378, 0.0, 0.0, 19.734192509061618, 12.693375644585483, 12.88056206088993,
        7.728894173602854, 0.0, 9.708737864077671, 0.0, 0.0, 5.13791471233702, 0.0, 0.0, 0.0, 7.2727272727272725, 0.0,
        0.0, 6.151142355008788, 5.244272702180513, 0, 13.705103969754253, 0.12292562999385372, 6.655693122450439, 0.0,
        0.22639800769753227, 8.04289544235925, 1.379369800422432, 11.825572801182558, 14.62522851919561, 0.0, 0.0,
        0.940733772342427, 0.0, 3.598200899550225, 5.524058729466493, 12.422360248447205, 0.0, 10.31211329575141,
        9.664229959112873, 0.0, 9.61219754723235, 8.787346221441124, 8.888071594949123, 0.0, 1.5343050598712518,
        0.2593630044610437, 16.38225255972696, 3.916768665850673, 8.763029240844942, 3.452605147520402, 0.0, 0.0,
        12.314493211240922, 0.5786292915005786, 0.0, 0.0, 21.75438596491228, 6.818834338214183, 0.0, 0.2740727206285401,
        3.731472203987147, 0.9587727708533078, 9.588795115819718, 3.890806401004079, 15.017064846416382,
        13.979826579366485, 3.7276949401124417, 1.3969528964945213, 0.0, 11.60069197110003, 3.304692663582287,
        0.012212248885632288, 13.143483023001094, 7.4970203358220475, 0.6487997205170435, 3.992901508429459,
        8.396533044420368, 5.773195876288661, 16.750418760469014, 9.845288326300984, 5.289672544080604,
        3.3695081393313493, 8.467575382073523, 23.036459278070016, 6.882092885465567, 16.8412282789812,
        14.662756598240469, 11.82237600922722, 1.4864362690449646, 0.0, 16.894745734076704, 8.492569002123142,
        7.552870090634441, 0.023323887159033926, 0.0, 11.731062944789263, 0.6998791117897818, 0.0, 0.4045605001838911,
        0.0, 12.311358220810169, 11.759989309100629, 13.457556935817806, 4.273504273504273, 12.742718446601943,
        14.440433212996389, 12.441679626749611, 0.0, 0.5512172714745062, 5.690478609897369, 8.565989847715736,
        2.6235802271636537, 37.16216216216216, 1.8824636743337844, 11.142061281337048, 10.077258985555929,
        5.4008395617897005, 2.6261489401613205, 2.9442939583087977, 0.028338245295851282, 17.629566694987254,
        6.335797254487857, 0.0, 0.7054753993901052, 6.619548353732116, 3.9968596103061884, 21.11145606954362,
        2.09944364743343, 15.968586387434556, 10.38511466897447, 0.7964954201513341, 24.371667936024373,
        10.217350919561582, 8.206613565049482, 1.375515818431912, 8.999550022498875, 8.058945429426664,
        1.45115788191837, 5.583365421640354, 3.115264797507788, 0.24348672997321644, 0.0, 0.07430248541813723,
        17.54385964912281, 0.0, 0.9704455227172474, 0.0, 6.474820143884893, 0.0, 1.876945614356345, 11.795395259158443,
        0.7153272622224668, 0.0, 0.641025641025641, 0.0, 10.355540214014498, 13.626948653657474, 2.27140361094933, 0.0,
        6.658709717947107, 3.186014214524957, 0.0, 5.925250683682771, 0.11530035743110803, 0.0, 7.271047769860122,
        11.965525897414441, 6.894722885176346, 9.566517189835574, 11.408815903197926, 10.787878787878787, 0.0,
        15.809618904975869, 7.347211399309807, 21.05755732335049, 0.26308866087871613, 5.270545859046005,
        3.757044458359424, 10.989010989010989, 8.549157656525018, 14.439096630877453, 4.673788630293781,
        2.350515463917526, 10.223953261927946, 10.945505356311132, 0.6460327714805896, 4.613351287997806,
        1.1275167785234899, 0.0, 2.3331173039533377, 4.527813712807244, 0.0, 5.99354541263255, 9.615384615384615, 0.0,
        0.0, 0.0, 15.306122448979592, 1.3960836180609133, 1.2328473413379075, 5.747126436781609, 19.90984222389181,
        5.4972982694849115, 8.984725965858042, 30.420353982300885, 0.0, 3.451540085924415, 14.41837732160313,
        4.613813263832634, 3.986826139712255, 0.0, 13.238289205702648, 0.5027652086475616, 9.282970550576184,
        0.08268221092232006, 0.0, 0.0, 11.133088443063013, 0.5503736747581253, 3.108613056174836, 4.386429896633978,
        2.936138977244923, 12.19623191043961, 0.0, 0.010997349638737065, 0.0
    ]

    vibe_light_sfp = [
        0.8461538461538461, 0.9047619047619048, 0.8, 0.6923076923076923, 0.7619047619047619, 0.8, 0.9230769230769231,
         0.8461538461538461, 0.8095238095238095, 0.8947368421052632, 0.9629629629629629, 0.8888888888888888
    ]

    similar_light_sfp = [
        0.9925093632958801, 1.0, 1.0, 0.6505576208178439, 0.9525101763907734, 0.8745519713261649, 0.8268506900878294,
        0.9359605911330049, 0.4797687861271676, 1.0, 0.9992576095025983, 1.0
    ]

    open_projs_light_sfp = [
        0.9954545454545455, 1.0, 1.0, 0.5824915824915825, 1.0, 0.8108108108108109, 1.0, 1.0, 0.6428571428571429, 1.0,
        0.912751677852349, 1.0, 0.7247191011235955, 1.0, 0.996031746031746, 1.0, 1.0, 0.6428571428571429,
        0.8947368421052632, 0.8214285714285714, 0.8378378378378378, 1.0, 1.0, 1.0, 0.7966101694915254,
        0.5185185185185185, 0.6865671641791045, 0.6153846153846154, 0.5673469387755102, 0.9487179487179487, 1.0,
        0.6504854368932039, 0.32432432432432434, 0.9732142857142857, 0.6007194244604317, 1.0, 0.9820971867007673,
        0.9538461538461539, 0.7916666666666666, 1.0, 0.7162162162162162, 0.6744791666666666, 0.5407725321888412,
        0.6099397590361446, 1.0, 0.8181818181818182, 0.8208955223880597, 0.696969696969697, 1.0, 0.8353293413173652,
        0.5892857142857143, 0.42857142857142855, 1.0, 1.0, 0.758957654723127, 1.0, 1.0, 0.648766328011611,
        0.7922077922077922, 0.8264462809917356, 0.8795180722891566, 0.9649805447470817, 0.5675675675675675,
        0.5793650793650794, 0.8260869565217391, 0.685, 0.9727891156462585, 1.0, 0.71875, 0.43478260869565216,
        0.9844827586206897, 0.7272727272727273, 0.9113300492610837, 0.8095238095238095, 0.8947368421052632,
        0.9004739336492891, 1.0, 1.0, 1.0, 0.6714285714285714, 0.7105263157894737, 0.5909090909090909,
        0.7857142857142857, 0.7557603686635944, 0.782608695652174, 0.9172661870503597, 0.8666666666666667, 1.0,
        0.8214285714285714, 0.95, 0.7341269841269841, 0.7207207207207207, 0.7041666666666667, 0.6314553990610329,
        0.8725663716814159, 0.7108433734939759, 1.0, 1.0, 0.703125, 0.6590909090909091, 0.8571428571428571,
        0.8452380952380952, 1.0, 0.9154929577464789, 1.0, 1.0, 0.752925877763329, 1.0, 1.0, 1.0, 0.7578125, 1.0, 1.0,
        0.9069767441860465, 0.970954356846473, 0, 0.6756756756756757, 0.9890710382513661, 0.6929824561403509, 1.0,
        0.9830508474576272, 0.9428571428571428, 0.9330143540669856, 0.8444444444444444, 0.7627118644067796, 1.0, 1.0,
        0.8870967741935484, 1.0, 0.33879781420765026, 0.9230769230769231, 0.782608695652174, 1.0, 0.7467532467532467,
        0.7096774193548387, 1.0, 0.3027027027027027, 0.8375, 0.7406417112299465, 1.0, 0.8962962962962963,
        0.9877049180327869, 0.5, 0.8478260869565217, 0.7348484848484849, 0.9166666666666666, 1.0, 1.0, 0.625,
        0.9668508287292817, 1.0, 1.0, 0.7413793103448276, 0.7469135802469136, 1.0, 0.9844961240310077,
        0.8168498168498168, 0.9642857142857143, 0.5254237288135594, 0.8307692307692308, 0.7631578947368421,
        0.5384615384615384, 0.7933333333333333, 0.945273631840796, 1.0, 0.7672413793103449, 0.8670212765957447,
        0.9990757855822551, 0.7804878048780488, 0.60875, 0.9583333333333334, 0.8529411764705882, 0.7866666666666666,
        0.796875, 0.8666666666666667, 0.8333333333333334, 0.8680555555555556, 0.8523489932885906, 0.7613636363636364,
        0.3829787234042553, 0.7097791798107256, 0.12631578947368421, 0.8764044943820225, 0.640625, 0.9716312056737588,
        1.0, 0.6630434782608695, 0.75, 0.8604651162790697, 0.9975757575757576, 1.0, 0.5538089480048367, 0.97, 1.0,
        0.9857142857142858, 1.0, 0.8032786885245902, 0.5108695652173914, 0.9148936170212766, 0.9, 0.775,
        0.6153846153846154, 0.9166666666666666, 1.0, 0.9820359281437125, 0.8321167883211679, 0.7027027027027027,
        0.8801261829652997, 0.65, 0.9292929292929293, 0.9259259259259259, 0.75, 0.7966601178781926, 0.9322033898305084,
        0.845360824742268, 0.9968253968253968, 0.4691358024691358, 0.95, 1.0, 0.9385245901639344, 0.7277628032345014,
        0.8922413793103449, 0.6214285714285714, 0.9109947643979057, 0.3157894736842105, 0.7741935483870968,
        0.9452054794520548, 0.6111111111111112, 0.6578947368421053, 0.8269230769230769, 0.9368029739776952,
        0.6696428571428571, 0.8700564971751412, 0.9304857621440537, 0.8905109489051095, 0.908256880733945,
        0.9940476190476191, 1.0, 0.9922178988326849, 0.8974358974358975, 1.0, 0.9659090909090909, 1.0,
        0.9259259259259259, 1.0, 0.7203389830508474, 0.6190476190476191, 0.9540636042402827, 1.0, 0.95, 1.0, 0.78125,
        0.5031055900621118, 0.9388646288209607, 1.0, 0.723404255319149, 0.8847736625514403, 1.0, 0.40789473684210525,
        0.993421052631579, 1.0, 0.4180672268907563, 0.6424581005586593, 0.8450704225352113, 0.8421052631578947,
        0.7767857142857143, 0.63671875, 1.0, 0.7075471698113207, 0.6875, 0.5714285714285714, 0.9943820224719101,
        0.8221436984687868, 0.9682539682539683, 0.7619047619047619, 0.8260869565217391, 0.6071428571428571,
        0.726643598615917, 0.899641577060932, 0.768, 0.7323943661971831, 0.9757575757575757, 0.8759811616954474,
        0.9712918660287081, 1.0, 0.8530120481927711, 0.79, 1.0, 0.8947368421052632, 0.8666666666666667, 1.0, 1.0, 1.0,
        0.5172413793103449, 0.9134199134199135, 0.9430199430199431, 0.9459459459459459, 0.5510204081632653,
        0.7904494382022472, 0.8157894736842105, 0.0, 1.0, 0.7478448275862069, 0.16363636363636364, 0.917057902973396,
        0.8902439024390244, 1.0, 0.8888888888888888, 0.9587628865979382, 0.8064516129032258, 0.9925093632958801, 1.0,
        1.0, 0.6505576208178439, 0.9525101763907734, 0.8745519713261649, 0.8268506900878294, 0.9359605911330049,
        0.4797687861271676, 1.0, 0.9992576095025983, 1.0
    ]

    vibe_tp_apd = [
        12.737884110039397, 7.07880820856863, 8.875172472121632, 16.894778235856684, 18.254551073882546,
        13.27648504339451, 6.085794995517537, 7.152010024647708, 11.232071472287691, 7.841483238873511,
        3.6093576025737617, 6.183079489076105

    ]
    similar_tp_apd = [
        0.1343585927487701, 0.0, 1.2026153162838404, 6.927919142365181, 0.47539948026915385, 3.7611234766168837,
        2.34331994768505, 4.076188095713291, 6.34150267798198, 0.0, 0.03241324104048819, 0.0
    ]

    vibe_tp_sfp = [
         np.float64(0.8645300267495266), np.float64(0.9329101084854798), np.float64(0.8238890347743846),
         np.float64(0.7832480427992425), np.float64(0.7316404339419194), np.float64(0.7886668417292615),
         np.float64(0.8645300267495266), np.float64(0.8103420374493372), np.float64(0.8322752712136996),
         np.float64(0.8887720219627692), np.float64(0.8956379465329687), np.float64(0.8825926898495897)
    ]
    similar_tp_sfp = [
        np.float64(0.9894465339190643), np.float64(1.0), np.float64(0.8651990142717513), np.float64(0.6857499505267828),
        np.float64(0.930224692203691), np.float64(0.8131582591154761), np.float64(0.8780260316128736),
        np.float64(0.885484495518319), np.float64(0.584663157155774), np.float64(1.0), np.float64(0.994247303288844),
        np.float64(1.0)
    ]'''

    dataset_1 = [] #vibe_tp_sfp
    dataset_2 = [] #similar_tp_sfp
    dataset_3 = [] #similar_tp_sfp

    print("--- Checking Normally Distributed Data ---")
    check_normal(dataset_1)
    check_normal(dataset_2)
    check_normal(dataset_3)
    print("-" * 30)
    res_param = compare_independent_samples(dataset_1, dataset_2)
    print(f"Test: {res_param['test_used']}")
    print(f"P-value: {res_param['p_value']:.4f}")
    print(
        f"Effect Size ({res_param['effect_size_type']}): {res_param['effect_size_value']:.4f} -> {res_param['effect_size_interpretation']}")
    print(res_param['interpretation'])
    print("-" * 40)

    res_param = compare_independent_samples(dataset_1, dataset_3)
    print(f"Test: {res_param['test_used']}")
    print(f"P-value: {res_param['p_value']:.4f}")
    print(
        f"Effect Size ({res_param['effect_size_type']}): {res_param['effect_size_value']:.4f} -> {res_param['effect_size_interpretation']}")
    print(res_param['interpretation'])
    print("-" * 40)


