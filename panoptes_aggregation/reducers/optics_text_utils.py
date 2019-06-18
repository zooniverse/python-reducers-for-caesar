'''
Utilities for `optics_line_text_reducer`
----------------------------------------
This module provides utilities used to reduce the polygon-text extractions
for :mod:`panoptes_aggregation.reducers.optics_line_text_reducer`.  It
assumes that all extracts are full lines of text in the document.
'''
import numpy as np
import Levenshtein
import collections
import copy
import re


def strip_tags(s):
    '''Remove square bracket tags from text and consolidating whitespace

    Parameters
    ----------
    s : string
        The input string

    Returns
    -------
    clean_s : string
        The cleaned string
    '''
    no_brackets = re.sub('[\[].*?[\]]', '', s)  # noqa: W605
    unify_space = ' '.join(no_brackets.split())
    return unify_space


def metric(a, b, data_in=[]):
    '''Calculate the distance between two drawn lines that have text
    associated with them.  This distance is found by summing the euclidean
    distance between the start points of each line, the euclidean distance
    between the end poitns of each line, and the Levenshtein distance
    of the text for each line.  The Levenshtein distance is done after
    stripping text tags and consolidating whitespace.

    To use this metric within the clustering code without haveing to
    precompute the full distance matrix `a` and `b` are index mappings to
    the data contained in `data_in`.  `a` and `b` also contain the user
    information that is used to help prevent self-clustering.

    Parameters
    ----------
    a : list
        A two element list containing [index mapping to data, index mapping to user]
    b : list
        A two element list containing [index mapping to data, index mapping to user]
    data_in : list
        A list of dicts that take the form
        {`x`: [start_x, end_x], `y`: [start_y, end_y], 'text': ['text for line']}
        There is one element in this list for each classification made.

    Returns
    -------
    distance: float
        The distance between `a` and `b`
    '''
    if a[0] == b[0]:
        # The same data point, the distance is zero
        return 0
    if a[1] == b[1]:
        # The same users, distance is inf
        return np.inf
    data_a = data_in[int(a[0])]
    data_b = data_in[int(b[0])]
    dx = (np.array(data_a['x']) - np.array(data_b['x']))**2
    dy = (np.array(data_a['y']) - np.array(data_b['y']))**2
    dt = Levenshtein.distance(
        strip_tags(data_a['text'][0]),
        strip_tags(data_b['text'][0])
    )
    return np.sqrt(dx + dy).sum() + dt


def get_min_samples(N):
    '''Get the `min_samples` attribute based on the number of
    users who have transcribed the subject.  These values were
    found based on example data from ASM.

    Parameters
    ----------
    N : integer
        The number of users who have see the subject

    Returns
    -------
    min_samples : integer
        The value to use for the min_samples keyword in OPTICS
    '''
    if N <= 6:
        return 2
    elif N <= 10:
        return 3
    elif N <= 15:
        return 4
    elif N <= 20:
        return 5
    else:
        return int(0.25 * N)


def remove_user_duplication(labels_, core_distances_, users):
    '''Make sure a users only shows up in a cluster at most once.
    If a user does show up more than once in a cluster take the point
    with the smallest core distance, all others are assigned as noise (-1).

    Parameters
    ----------
    labels_ : numpy.array
        A list containing the cluster labels for each data point
    core_distances_ : numpy.array
        A list of core distance for each data point
    users : numpy.array
        A list of indices that map to users, one for each data point

    Returns
    -------
    clean_labels_ : numpy.array
        A list containing the new cluster labels.
    '''
    clean_labels = copy.deepcopy(labels_)
    unique_labels = np.unique(labels_)
    gdx = unique_labels > -1
    for l in unique_labels[gdx]:
        cdx = labels_ == l
        user_counts = collections.Counter(users[cdx]).most_common()
        if user_counts[0][1] > 1:
            clean_labels_cdx = clean_labels[cdx]
            for user_count in user_counts:
                udx = users[cdx] == user_count[0]
                clean_labels_cdx_udx = clean_labels_cdx[udx]
                if user_count[1] > 1:
                    min_idx = core_distances_[cdx][udx].argmin()
                    mask = np.ones(udx.sum(), dtype=bool)
                    mask[min_idx] = False
                    clean_labels_cdx_udx[mask] = -1
                else:
                    break
                clean_labels_cdx[udx] = clean_labels_cdx_udx
            clean_labels[cdx] = clean_labels_cdx
    return clean_labels


def cluster_of_one(X, data):
    '''Create "clusters of one" out of the data passed in. Lines of text
    identified as noise are kept around as clusters of one so they can be
    displayed in the front-end to the next user.

    Parameters
    ----------
    X: list
        A nx2 list with each row containing [index mapping to data, index mapping to user]
    data: list
        A list containing dictionaries with the original data that X maps to, of the form
        `{'x': [start_x, end_x], 'y': [start_y, end_y], 'text': ['text for line']}`.

    Returns
    -------
    clusters: list
        A list with n clusters each containing only one calssification
    '''
    clusters = []
    for row in X:
        line = data[int(row[0])]
        dx = line['x'][-1] - line['x'][0]
        dy = line['y'][-1] - line['y'][0]
        slope = np.rad2deg(np.arctan2(dy, dx))
        value = {
            'clusters_x': line['x'],
            'clusters_y': line['y'],
            'clusters_text': [[w] for w in line['text'][0].split()],
            'number_views': 1,
            'line_slope': slope,
            'consensus_score': 1.0
        }
        clusters.append(value)
    return clusters