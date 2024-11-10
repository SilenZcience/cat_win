"""
levenshtein
"""

SIMILARITY_LIMIT = 50.0

def levenshtein(str_a: str, str_b: str) -> float:
    """
    Calculate the levenshtein distance (similarity) between
    two strings and return the result as a percentage value.
    char case is ignored such that uppercase letters match their
    lowercase counterparts perfectly.

    Parameters:
    str_a (str):
        the first string to compare
    str_b (str):
        the second string to compare

    Returns:
    (float):
        the similarity of the two strings as a percentage between 0.0 and 100.0
    """
    str_a, str_b = str_a.lstrip('-'), str_b.lstrip('-')
    len_a, len_b = len(str_a), len(str_b)
    max_len = max(len_a, len_b)
    if len_a*len_b == 0:
        return (100 if max_len == 0 else (1 - (len_a+len_b)/max_len) * 100)

    d_arr = [[i] + ([0] * len_b) for i in range(len_a+1)]
    d_arr[0] = list(range(len_b+1))

    for i in range(1, len_a+1):
        str_a_i = str_a[i-1:i]

        for j in range(1, len_b+1):
            str_b_j = str_b[j-1:j]

            d_arr[i][j] = min(d_arr[i-1][j]+1,
                              d_arr[i][j-1]+1,
                              d_arr[i-1][j-1]+int(str_a_i.lower() != str_b_j.lower()))

    return (1 - d_arr[len_a][len_b]/max_len) * 100

def calculate_suggestions(check_these: list, check_against: list) -> list:
    """
    Calculate the suggestions for each given element passed in
    using the levenshtein distance to all valid options.

    Parameters:
    check_these (list):
        the elements to find suggestions for
    check_against (list):
        a list of iterables. each iterable holds different variants of the same
        suggestion

    Returns:
    element_suggestions (list):
        a list of the structure [(arg1, [suggestions]), (arg2, [suggestions]), ...]
        where suggestions is of the form [(suggestion, similarity), ...]
    """
    element_suggestions = []

    for element in check_these:
        element_suggestion = (element, [])
        for suggestions in check_against:
            leven_distances = [levenshtein(suggestion, element) for suggestion in suggestions]
            for suggestion, distance in zip(suggestions, leven_distances):
                if distance > SIMILARITY_LIMIT:
                    element_suggestion[1].append((suggestion, distance))
                    break
        element_suggestions.append(element_suggestion)

    return element_suggestions
