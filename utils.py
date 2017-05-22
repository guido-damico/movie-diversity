'''
Created on May 22, 2017

@author: Guido

Generic utils functions.
'''

similarityThreshold = 0.5

def isSimilar(title1 = "", title2 = ""):
    """Given two strings, it returns True if their
    similarity is closer than Scraper.similarityThreshold
    """
    # first, lowercase all and eliminate all whitespaces
    title1 = "".join(title1.lower().split())
    title2 = "".join(title2.lower().split())

    # then count the letters which are the same
    len1 = len(title1)
    len2 = len(title2)
    same = [x for x in range(0, min(len1, len2)) if title1[x] == title2[x]]

    # similarity ratio
    ratio = len(same) / max(len1, len2)

    return ratio > similarityThreshold

