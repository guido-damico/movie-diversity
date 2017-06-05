'''
Created on May 22, 2017

@author: Guido

Generic utils functions.
'''

similarityThreshold = 0.5

def isSimilar(title1 = "", title2 = ""):
    """Given two strings, it returns True if their
    similarity ratio is closer than similarityThreshold.

    The similarity ration is:
    (number of equal characters) / (length of the longest of the two titles)
    """

    # first, lowercase and eliminate all whitespaces
    title1 = "".join(title1.lower().split())
    title2 = "".join(title2.lower().split())

    # then count the letters which are the same
    len1 = len(title1)
    len2 = len(title2)
    same = [x for x in range(0, min(len1, len2)) if title1[x] == title2[x]]

    # similarity ratio
    ratio = len(same) / max(len1, len2)

    # if they are similar but the differences are only numbers, then these are
    # probably two different movies
    # (e.g., "Madagascar", "Madagascar 2", "Madagascar 3")
    # in which case the similarity should be 0
    if ratio > similarityThreshold:
        different = [title1[x] for x in range(0, min(len1, len2)) if title1[x] != title2[x]]

        if len1 > len2:
            different = different + [title1[x] for x in range(len2, len1)]
        elif len2 > len1:
            different = different + [title2[x] for x in range(len1, len2)]

        # if all different characters are numbers, then these titles are not similar:
        if "".join(different).isnumeric():
            ratio = 0

    return ratio > similarityThreshold
