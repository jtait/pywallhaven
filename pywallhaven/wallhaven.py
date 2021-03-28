"""
API wrapper functions and dataclasses to retrieve information using the API for wallhaven.cc.
"""

import json
import warnings
from datetime import datetime
from typing import List, Tuple, Dict, Union, Generator

import requests
from dataclasses import dataclass, field
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from ratelimit import sleep_and_retry, limits

from pywallhaven import util, exceptions


@dataclass(frozen=True)
class Uploader:
    """
    A dataclass representation of an Uploader. Uploaders are included in Wallpaper objects.

    This object is read-only after creation.
    """
    username: str
    group: str = field(compare=False)
    avatar: dict = field(compare=False)


@dataclass(frozen=True)
class Tag:
    """
    A dataclass representation of a Tag. Tags are included in Wallpaper objects, as well as having their own endpoint.

    This object is read-only after creation.
    """
    id: int
    name: str = field(compare=False)
    alias: str = field(compare=False)  # this is a comma separated string of aliases
    category_id: str = field(compare=False)
    category: str = field(compare=False)
    purity: str = field(compare=False)
    created_at: str = field(compare=False)

    @property
    def created_at_datetime(self):
        """
        Returns the created_at field as a datetime object instead of a string.

        :return: the created_at field as a properly formatted :class:`datetime`
        """
        return datetime.strptime(self.created_at, "%Y-%m-%d %H:%M:%S")


@dataclass(frozen=True)
class Wallpaper:
    """
    A dataclass representation of a Wallpaper. Wallpapers are returned in lists from some API endpoints.

    This class contains all the properties of a Wallpaper as returned by the API call, as well as some helper properties
    that convert the format of some fields.

    This object is read-only after creation.
    """
    id: str
    url: str = field(compare=False)
    short_url: str = field(compare=False)
    views: int = field(compare=False)
    favorites: int = field(compare=False)
    source: str = field(compare=False)
    purity: str = field(compare=False)
    category: str = field(compare=False)
    dimension_x: int = field(compare=False)
    dimension_y: int = field(compare=False)
    resolution: str = field(compare=False)
    ratio: str = field(compare=False)
    file_size: int = field(compare=False)
    file_type: str = field(compare=False)
    created_at: str = field(compare=False)
    colors: list = field(compare=False)
    path: str = field(compare=False)
    thumbs: list = field(compare=False)

    # 'search' results don't include tags on wallpapers
    tags: List[dict] = field(compare=False, default_factory=list)

    # collections don't include uploader in wallpapers
    uploader: Dict[str, Union[str, dict]] = field(compare=False, default_factory=dict)

    @property
    def created_at_datetime(self):
        """
        Returns the created_at field as a datetime object instead of a string.

        :return: the created_at field as a properly formatted :class:`datetime`
        """
        return datetime.strptime(self.created_at, "%Y-%m-%d %H:%M:%S")

    @property
    def tags_as_class_list(self):
        """
        Returns the Tags of the Wallpaper as a list of Tag objects.

        :return: the tags as a list of :class:`Tag` objects instead of as a list of dicts
        """
        return [Tag(**x) for x in self.tags]

    @property
    def uploader_as_class(self):
        """
        Returns the Uploader of the Wallpaper as an Uploader class.

        :return: the uploader as an instance of :class:`Uploader` instead of as a dict
        """
        return Uploader(**self.uploader)


@dataclass(frozen=True)
class UserSettings:
    """
    A dataclass representation of User Settings.

    This object is read-only after creation.
    """
    thumb_size: str
    per_page: int
    purity: list  # this is a list of purities, not a numerical representation
    categories: list
    resolutions: list
    aspect_ratios: list
    toplist_range: str
    tag_blacklist: list
    user_blacklist: list


@dataclass(frozen=True)
class Collection:
    """
    A dataclass representation of a Collection, as returned by the collections endpoint.

    Note: This is not a list of Wallpapers in a collection, but a description of the collection itself.

    This object is read-only after creation.
    """
    id: str
    label: str = field(compare=False)
    views: int = field(compare=False)
    public: bool = field(compare=False)  # this is provided as a 0 or 1
    count: int = field(compare=False)


@dataclass(frozen=True)
class Meta:
    """
    A dataclass representation of the Meta field in an API response.

    This object is read-only after creation.
    """
    current_page: int
    last_page: int
    per_page: int
    total: int
    query: str = field(default=None)  # collections don't include query in meta
    seed: str = field(default=None)  # collections don't include seed in meta


class Wallhaven(object):
    """
    .. versionchanged:: 0.3
        Endpoint requests are now rate limited. The limit applies globally to all instances of :class:`Wallhaven`
        The limit is 45 calls per minute, as per https://wallhaven.cc/help/api#limits

    The main API reference object.  All calls are made from an instance of this.

    Requires an API key to access NSFW wallpapers, user settings, and private collections.

    :param api_key: An API key from the website. Will be sent in the headers of all requests.
    """

    def __init__(self, api_key: str = None):
        self.__api_key = api_key
        if self.__api_key:
            self.__headers = {"X-API-Key": self.__api_key}
        else:
            self.__headers = {}

    @sleep_and_retry
    @limits(calls=45, period=60)
    def __get_endpoint(self, url):
        with requests.Session() as s:
            retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[429])
            s.mount('https://', HTTPAdapter(max_retries=retries))
            try:
                r = s.get(url, headers=self.__headers)
            except requests.exceptions.ConnectionError as e:
                raise e

        if r.status_code in [400, 404, 422]:
            raise requests.exceptions.RequestException('Bad Request for url {}'.format(url))
        elif r.status_code in [500, 502, 503]:
            raise requests.exceptions.ConnectionError('Server error {}'.format(str(r.status_code)))
        elif r.status_code == 429:
            raise exceptions.RateLimitError('API request speed limit reached')
        elif r.status_code != 200:
            raise requests.exceptions.HTTPError('something broke')
        else:
            try:
                return r.json()
            except json.decoder.JSONDecodeError as e:
                if r.content:
                    raise IOError('invalid content returned')
                else:
                    raise e

    def get_wallpaper(self, wallpaper_id: str) -> Wallpaper:
        """
        Make a request to the wallpaper endpoint given the wallpaper ID

        :param wallpaper_id: The ID of the wallpaper to fetch
        :return: A :class:`Wallpaper` object
        """
        endpoint = 'https://wallhaven.cc/api/v1/w/{id}'.format(id=wallpaper_id)
        wallpaper = Wallpaper(**self.__get_endpoint(endpoint).get('data'))
        return wallpaper

    def get_tag(self, tag_id: int) -> Tag:
        """
        Make a request to the tag endpoint given the tag ID

        :param tag_id: The ID of the tag to fetch
        :return: A :class:`Tag` object
        """
        endpoint = 'https://wallhaven.cc/api/v1/tag/{id}'.format(id=tag_id)
        tag = Tag(**self.__get_endpoint(endpoint).get('data'))
        return tag

    def get_user_settings(self) -> UserSettings:
        """
        Make a request to the settings endpoint. Requires the API key is set in the Wallhaven object

        :return: A :class:`UserSettings` object
        :raises AttributeError: if the :class:`Wallhaven` instance was created without an API key
        """
        if not self.__api_key:
            raise AttributeError('no API key supplied')
        endpoint = 'https://wallhaven.cc/api/v1/settings'
        settings = UserSettings(**self.__get_endpoint(endpoint).get('data'))
        return settings

    def get_collections(self, username: str = None) -> List[Collection]:
        """
        Return the collections of a given user. Returns the collections of the specified user if username is given.
        If no username is given, the API key must be specified in the Wallhaven object

        :param username: If given, returns the collections of this username
        :return: A list of :class:`Collection` objects
        :raises AttributeError: if no username is provided and the :class:`Wallhaven` instance was created without
            an API key
        """
        if username:
            endpoint = 'https://wallhaven.cc/api/v1/collections/{username}'.format(username=username)
        else:
            if self.__api_key:
                endpoint = 'https://wallhaven.cc/api/v1/collections'
            else:
                raise AttributeError('no API key or username supplied')

        search_result = self.__get_endpoint(endpoint)
        collections = search_result.get('data', [])
        if collections:
            collections = [Collection(**x) for x in collections]
        return collections

    def get_collection(
            self, username: str, collection_id: int, page: int = 1, **kwargs
    ) -> Tuple[List[Wallpaper], Meta]:
        """
        .. deprecated:: 0.2
            Use :py:meth:`get_collection_pages` instead.

        Makes a request to the collections endpoint for a specific collection, given by the collection_id and username.

        If the collection spans more than one page you will need to make multiple requests. The Meta object returned
        gives page information, which can be used to make enough calls to return the complete collection.

        :param page: The page of the request.
            If a query results in a multiple page response, the page must be specified.
        :param username: The username of the user that owns the collection
        :param collection_id: The ID of the collection
        :param kwargs: parameters to add to the API request - supports purity and page
        :return: A list of :class:`Wallpaper` and a :class:`Meta` object
        :raises ValueError: if :py:attr:`**kwargs` contains an invalid parameter=value combination
        """
        warnings.warn('get_collection is deprecated in favour of get_collection_pages', category=DeprecationWarning)

        endpoint = 'https://wallhaven.cc/api/v1/collections/{username}/{id}'.format(username=username, id=collection_id)
        try:
            endpoint += util.create_parameter_string(**kwargs, page=page)
        except ValueError as e:
            raise e
        search_result = self.__get_endpoint(endpoint)
        wallpapers = [Wallpaper(**x) for x in search_result.get('data')]
        meta = Meta(**search_result.get('meta'))
        return wallpapers, meta

    def search(self, page: int = 1, **kwargs) -> Tuple[List[Wallpaper], Meta]:
        """
        .. deprecated:: 0.2
            Use :py:meth:`get_search_pages` instead.

        Makes a search using the given kwargs. The allowed parameters are described at
        https://wallhaven.cc/help/api#search.

        See the helper method :py:func:`pywallhaven.util.build_q_string` to help build valid strings. The q parameter
        is very permissive, so invalid queries are possible.

        Invalid parameters/keys are checked and will throw an error, but the value of the q parameter is difficult to
        validate by its nature, so an invalid string may still be passed to the API.

        If the search result spans more than one page you will need to make multiple requests. The Meta object returned
        gives page information, which can be used to make enough calls to return the complete collection.

        :param page: The page of the request.
            If a query results in a multiple page response, the page must be specified.
        :param kwargs: Parameters for the query string in the URL.
            See https://wallhaven.cc/help/api#search for allowed values.
        :return: A list of :class:`Wallpaper` and a :class:`Meta` object
        :raises ValueError: if :py:attr:`**kwargs` contains an invalid parameter=value combination
        """
        warnings.warn('search is deprecated in favour of get_search_pages', category=DeprecationWarning)

        endpoint = 'https://wallhaven.cc/api/v1/search'
        try:
            endpoint += util.create_parameter_string(**kwargs, page=page)
        except ValueError as e:
            raise e
        search_result = self.__get_endpoint(endpoint)
        wallpapers = [Wallpaper(**x) for x in search_result.get('data')]
        meta = Meta(**search_result.get('meta'))
        return wallpapers, meta

    def get_search_pages(self, **kwargs) -> Generator[Tuple[List[Wallpaper], Meta], None, None]:
        """
        .. versionadded:: 0.2

        Makes a search using the given kwargs. The allowed parameters are described at
        https://wallhaven.cc/help/api#search.

        Creates a generator iterator that will return all pages of a collection.

        Use in a for loop such as::

            for wallpapers, meta in Wallhaven().get_search_pages():
                print(wallpapers)

        See the helper method :py:func:`pywallhaven.util.build_q_string` to help build valid strings. The q parameter
        is very permissive, so invalid queries are possible.

        Invalid parameters/keys are checked and will throw an error, but the value of the q parameter is difficult to
        validate by its nature, so an invalid string may still be passed to the API.

        :param kwargs: Parameters for the query string in the URL.
            See https://wallhaven.cc/help/api#search for allowed values.
        :return: A generator iterator that provides a tuple of a list of :class:`Wallpaper` and a :class:`Meta` object
        :raises ValueError: if :py:attr:`**kwargs` contains an invalid parameter=value combination
        :raises AttributeError: if page is included as a keyword argument
        """

        if 'page' in kwargs.keys():
            raise AttributeError('cannot specify page as keyword argument, page is handled by generator')

        search_endpoint = 'https://wallhaven.cc/api/v1/search'

        last_page = 1
        current_page = 1

        while current_page <= last_page:
            try:
                endpoint = search_endpoint + util.create_parameter_string(**kwargs, page=current_page)
            except ValueError as e:
                raise e
            search_result = self.__get_endpoint(endpoint)
            wallpapers = [Wallpaper(**x) for x in search_result.get('data')]
            meta = Meta(**search_result.get('meta'))

            yield wallpapers, meta

            last_page = meta.last_page
            current_page += 1

    def get_collection_pages(
            self, username: str, collection_id: int, **kwargs
    ) -> Generator[Tuple[List[Wallpaper], Meta], None, None]:
        """
        .. versionadded:: 0.2

        Makes a request to the collections endpoint for a specific collection, given by the collection_id and username.

        Creates a generator iterator that will return all pages of a collection.

        Use in a for loop such as::

            for wallpapers, meta in Wallhaven().get_collection_pages():
                print(wallpapers)

        :param username: The username of the user that owns the collection
        :param collection_id: The ID of the collection
        :param kwargs: parameters to add to the API request - only supports purity
        :return: A generator iterator that provides a tuple of a list of :class:`Wallpaper` and a :class:`Meta` object
        :raises ValueError: if :py:attr:`**kwargs` contains an invalid parameter=value combination
        :raises AttributeError: if page is included as a keyword argument
        """

        if 'page' in kwargs.keys():
            raise AttributeError('cannot specify page as keyword argument, page is handled by generator')

        collections_endpoint = 'https://wallhaven.cc/api/v1/collections/{username}/{id}'.format(username=username,
                                                                                                id=collection_id)

        last_page = 1
        current_page = 1

        while current_page <= last_page:
            try:
                endpoint = collections_endpoint + util.create_parameter_string(**kwargs, page=current_page)
            except ValueError as e:
                raise e
            search_result = self.__get_endpoint(endpoint)
            wallpapers = [Wallpaper(**x) for x in search_result.get('data')]
            meta = Meta(**search_result.get('meta'))

            yield wallpapers, meta

            last_page = meta.last_page
            current_page += 1
