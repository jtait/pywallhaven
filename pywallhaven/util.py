import re
from urllib.parse import quote
from typing import Tuple, List

__regex_map = {
    'q': re.compile(r'(^id:\d+$)|(^like:[a-zA-Z0-9]{6}$)|(^(?!(.*id:.*)|(.*like:.*)).*$)'),
    'categories': re.compile(r'^[01]{3}$'),
    'purity': re.compile(r'^[01]{3}$'),
    'sorting': re.compile(r'^(date_added)|(relevance)|(random)|(views)|(favorites)|(toplist)$'),
    'order': re.compile(r'^(desc)|(asc)$'),
    'topRange': re.compile(r'^(1d)|(3d)|(1w)|(1M)|(3M)|(6M)|(1y)$'),
    'atleast': re.compile(r'^[1-9][0-9]*x[1-9][0-9]*$'),
    'resolutions': re.compile(r'^[1-9][0-9]*x[1-9][0-9]*(,[1-9][0-9]*x[1-9][0-9]*)*$'),
    'ratios': re.compile(r'^[1-9][0-9]*x[1-9][0-9]*(,[1-9][0-9]*x[1-9][0-9]*)*$'),
    'colors': re.compile(r'^[0-9A-F]{6}$'),
    'page': re.compile(r'^[1-9][0-9]*$'),
    'seed': re.compile(r'^[a-zA-Z0-9]{6}$'),
}


def create_parameter_string(**kwargs) -> str:
    """
    Uses given parameters to return a valid url query string
    Validates parameters to ensure the Wallhaven API will recognize them

    :param kwargs: An unpacked dict of parameters
    :return: A properly formatted string to append to the endpoint url
    """
    string = ""
    if kwargs:
        params = []
        string += "?"
        for k, v in kwargs.items():
            v = str(v)  # cast v to string
            validate_parameter(k, v)
            params.append(k + "=" + v)
        string += '&'.join(params)
    return string


def validate_parameter(key, value) -> Tuple[str, str]:
    """
    This helper class will validate a parameter for a search query to prevent sending invalid queries

    :param key: the key or parameter for the url query, as per https://wallhaven.cc/help/api#search
    :param value: the value for the given parameter
    :return: The key and value pair, both as strings, for convenience
    :raises KeyError: if an invalid parameter is given
    :raises TypeError: if either key or value is not a string
    :raises ValueError: if the value fails validation according to the expected regular expression
    """
    if not type(key) == str:
        raise TypeError("key must be a str object")
    if not type(value) == str:
        raise TypeError("value for {} must be a str object".format(str(key)))

    try:
        regex = __regex_map[key]
        if not bool(re.fullmatch(regex, value)):
            raise ValueError("value for {} doesn't match the required regular expression".format(str(key)))
    except KeyError:
        # given filter is not valid
        raise KeyError('invalid parameter "{}"'.format(str(key)))
    else:
        return key, value


def purity_list_as_numeric_string(purity_list: list) -> str:
    """
    Helper method: The API returns purity as a list in some cases. This method will accept the list and return a
    numeric string representation. The numeric string can be used for future calls.

    Example: if the API returns a purity = ['sfw', 'sketchy'] (e.g. from user settings), and you want to make a
    query to match that setting, you can pass the list to this method, and use the result in a new query.

    This is just a convenience method to allow easier automation in some cases.

    :param purity_list: A valid list of purities.
    :return: A 'numerical' string (str) of the purities
    """
    __purity_map = {'sfw': 100, 'sketchy': 10, 'nsfw': 1}
    numerical_purity = 0
    for p in purity_list:
        numerical_purity += __purity_map[p]
    return str(numerical_purity).zfill(3)


def build_q_string(include_tags: List[str] = None, exclude_tags: List[str] = None, username: str = None,
                   image_type: str = None) -> str:
    """
    A helper method to allow easier and more reliable construction of the string for the q parameter in search.
    Doesn't support like: or id: parameters - these should be used on their own

    :param include_tags: A list of tags to include in the search results
    :param exclude_tags: A list of tags to exclude from the search results
    :param username: Limits search results to wallpapers uploaded by this username
    :param image_type: limit search results by image type - must be png, jpg, or jpeg
    :return: A processed string that will work as a q parameter for the API search call
    :raises ValueError: if an invalid image type is given
    :raises TypeError: if an include_tag or exclude_tag is not a string
    """
    string = ""
    if include_tags:
        try:
            include_tags = [f"\"{x}\"" if ' ' in x else x for x in include_tags]  # handle multi-word tags
            include_tags = [quote(str(t)) for t in include_tags]
            string += quote(" +") + quote(" +").join(include_tags)
        except TypeError as e:
            raise e
    if exclude_tags:
        try:
            exclude_tags = [f"\"{x}\"" if ' ' in x else x for x in exclude_tags]  # handle multi-word tags
            exclude_tags = [quote(str(t)) for t in exclude_tags]
            string += quote(" -") + quote(" -").join(exclude_tags)
        except TypeError as e:
            raise e
    if username:
        string += quote(" @" + str(username))
    image_types = ['png', 'jpeg', 'jpg']
    if image_type:
        if image_type in image_types:
            string += quote(" type:" + image_type)
        else:
            raise ValueError('invalid type given, must be one of {}'.format(':'.join(image_types)))

    return string.strip()
