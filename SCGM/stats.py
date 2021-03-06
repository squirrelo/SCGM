#!/usr/bin/env python

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, SCGM course project"
__credits__ = ["Jose Antonio Navas Molina"]
__license__ = "GPL"
__version__ = "0.0.1-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.com"
__status__ = "Development"

from numpy import array, mean, std, zeros, dtype, sqrt
from numpy.random import randint
from qiime.stats import quantile
from SCGM.profile import normalize_profiles, compare_profiles

def bootstrap_profiles(profiles, alpha=0.05, repetitions=1000,
    randfunc=randint):
    """Performs bootstrapping over the sample 'profiles'

    Inputs:
        profiles: list of profiles
        alpha: defines the confidence interval as 1 - alpha
        repetitions: number of bootstrap iterations
        randfunc: random function for generate the bootstrap samples

    Returns:
        profile: the bootstrapped profile of the profiles list
        sample_mean: the bootstrap mean of the amount shared
        sample_stdev: the bootstrap standard deviation of the amount shared
        ci: the confidence interval for the bootstrap mean
    """
    length = len(profiles)
    normalize_profiles(profiles)
    boot_shared = []
    boot_profiles = []
    for i in range(repetitions):
        # Construct the bootstrap sample
        resample = [profiles[randfunc(0, length)] for j in range(length)]
        profile = compare_profiles(resample)
        # Store the amount shared
        boot_shared.append(1.0 - profile['not_shared'])
        # Store the result profile
        boot_profiles.append(profile)
    # Convert data to a numpy array
    boot_shared = array(boot_shared)
    # Get the mean and the standard deviation of the shared data
    sample_mean = mean(boot_shared)
    sample_stdev = std(boot_shared)
    # Compute the confidence interval for the bootstrapped data
    # using bootstrap percentile interval
    ci = quantile(boot_shared, [alpha/2, 1-(alpha/2)])
    # Compute the bootstrapped profile of the profiles list
    profile = compare_profiles(profiles)

    return profile, 1.0-profile['not_shared'], sample_stdev, ci

def build_similarity_matrix(profiles, key_order):
    """Builds the similarity matrix between the profiles, using the given order
    Inputs:
        profiles: dictionary of profiles lists, keyed by category values
        key_order: a list of the dictionary keys ordered
    Returns:
        sim_mat: the result similarity matrix, where rows and columns are
            ordered by 'key_order'
    """
    # Get the matrix dimensions (size x size)
    size = len(key_order)
    sim_mat = zeros([size, size], dtype='4float64')
    # Initialize the group profiles list
    group_profiles = {}
    # Populate the matrix
    for i in range(size):
        # The similarity between the profile of a value with itself is the
        # the amount shared between the profiles in that category values
        profs = profiles[key_order[i]]
        if len(profs) == 1:
            sim_mat[i, i] = (1.0, 0.0, 1.0, 1.0)
            group_profiles[key_order[i]] = profs[0]
        else:
            val_prof, val_shared, val_stdev, val_ci = bootstrap_profiles(profs)
            sim_mat[i, i] = (val_shared, val_stdev, val_ci[0], val_ci[1])
            group_profiles[key_order[i]] = val_prof
        for j in range(i+1, size):
            # Get a list with the profiles of the two category values
            profs = []
            profs.extend(profiles[key_order[i]])
            profs.extend(profiles[key_order[j]])

            # Perform the comparison
            comp_prof, comp_shared, comp_stdev, comp_ci = \
                bootstrap_profiles(profs)
            # Save the shared results on the similarity matrix
            sim_mat[i,j] = sim_mat[j,i] = (comp_shared, comp_stdev, comp_ci[0],\
                                            comp_ci[1])
    return sim_mat, group_profiles

def is_diagonal_matrix(matrix):
    """Returns true if the matrix is diagonal (zeros everywhere except diagonal)
    Inputs:
        matrix: the similarity matrix to test
    """
    size = len(matrix)
    for i in range(size):
         # First check: all the values in the diagonal are different from zero
        if matrix[i, i][0] == 0:
            return False
        # Second check: all the values except the diagonal are different from zero
        for j in range(i+1, size):
            if matrix[i ,j][0] != 0:
                return False
    return True

def build_consensus_matrix(matrix_list):
    height, width, data = matrix_list[0].shape
    consensus_matrix = zeros([height, width], dtype='4float64')
    n = len(matrix_list)
    for i in range(height):
        for j in range(i, width):
            values_list = [mat[i][j][0] for mat in matrix_list]
            cons_mean = mean(values_list)
            cons_stdev = std(values_list)
            cons_ci_low = cons_mean - 1.96*(cons_stdev/sqrt(n))
            cons_ci_high = cons_mean + 1.96*(cons_stdev/sqrt(n))
            consensus_matrix[i][j] = consensus_matrix[j][i] = (cons_mean, 
                                        cons_stdev, cons_ci_low, cons_ci_high)
    return consensus_matrix