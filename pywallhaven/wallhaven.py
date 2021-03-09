import json
from datetime import datetime
from typing import List, Tuple

import requests
from dataclasses import dataclass, field
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from pywallhaven import util, exceptions


@dataclass(frozen=True)
class Uploader:
    username: str
    group: str = field(compare=False)
    avatar: dict = field(compare=False)


@dataclass(frozen=True)
class Tag:
    id: int
    name: str = field(compare=False)
    alias: str = field(compare=False)  # this is a comma separated string of aliases
    category_id: str = field(compare=False)
    category: str = field(compare=False)
    purity: str = field(compare=False)
    created_at: str = field(compare=False)

    @property
    def created_at_datetime(self):
        return datetime.strptime(self.created_at, "%Y-%m-%d %H:%M:%S")


@dataclass(frozen=True)
class Wallpaper:
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
    tags: list = field(compare=False, default_factory=list)  # 'search' results don't include tags on wallpapers
    uploader: dict = field(compare=False, default_factory=dict)  # collections don't include uploader in wallpapers

    @property
    def created_at_datetime(self):
        return datetime.strptime(self.created_at, "%Y-%m-%d %H:%M:%S")


@dataclass(frozen=True)
class UserSettings:
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
    id: str
    label: str = field(compare=False)
    views: int = field(compare=False)
    public: bool = field(compare=False)  # this is provided as a 0 or 1
    count: int = field(compare=False)


@dataclass(frozen=True)
class Meta:
    current_page: int
    last_page: int
    per_page: int
    total: int
    query: str = field(default=None)  # collections don't include query in meta
    seed: str = field(default=None)  # collections don't include seed in meta


class Wallhaven(object):
    """
    The main API reference object.  All calls are made from an instance of this.
    """
    def __init__(self, api_key: str = None):
        self.__api_key = api_key
        if self.__api_key:
            self.__headers = {"X-API-Key": self.__api_key}
        else:
            self.__headers = {}

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
        :return: A Wallpaper object
        """
        endpoint = 'https://wallhaven.cc/api/v1/w/{id}'.format(id=wallpaper_id)
        wallpaper = Wallpaper(**self.__get_endpoint(endpoint).get('data'))
        return wallpaper

    def get_tag(self, tag_id: int) -> Tag:
        """
        Make a request to the tag endpoint given the tag ID

        :param tag_id: The ID of the tag to fetch
        :return: A Tag object
        """
        endpoint = 'https://wallhaven.cc/api/v1/tag/{id}'.format(id=tag_id)
        tag = Tag(**self.__get_endpoint(endpoint).get('data'))
        return tag

    def get_user_settings(self) -> UserSettings:
        """
        Make a request to the settings endpoint. Requires the API key is set in the Wallhaven object

        :return: A UserSettings object
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
        :return: A list of Collection objects
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

    def get_collection(self, username: str, collection_id: int, **kwargs) -> Tuple[List[Wallpaper], Meta]:
        """
        Makes a request to the collections endpoint for a specific collection, given by the collection_id and username.
        If the collection spans more than one page you will need to make multiple requests. The Meta object returned
        gives page information, which can be used to make enough calls to return the complete collection.

        :param username: The username of the user that owns the collection
        :param collection_id: The ID of the collection
        :param kwargs: parameters to add to the API request - supports purity and page
        :return: A list of Wallpapers and a Meta object
        """
        endpoint = 'https://wallhaven.cc/api/v1/collections/{username}/{id}'.format(username=username, id=collection_id)
        try:
            endpoint += util.create_parameter_string(**kwargs)
        except ValueError as e:
            raise e
        search_result = self.__get_endpoint(endpoint)
        wallpapers = [Wallpaper(**x) for x in search_result.get('data')]
        meta = Meta(**search_result.get('meta'))
        return wallpapers, meta

    def search(self, **kwargs) -> Tuple[List[Wallpaper], Meta]:
        """
        Makes a search using the given kwargs. The allowed parameters are described at https://wallhaven.cc/help/api.
        See the helper method util.build_q_string to help build valid strings. The q parameter is very permissive,
        so invalid queries are possible. Invalid parameters/keys are checked and will throw an error, but the value of
        the q parameter is difficult to validate by its nature.

        :param kwargs: Parameters for the query string in the URL. See https://wallhaven.cc/help/api for allowed values.
        :return: A list of Wallpapers and a Meta object
        """
        endpoint = 'https://wallhaven.cc/api/v1/search'
        try:
            endpoint += util.create_parameter_string(**kwargs)
        except ValueError as e:
            raise e
        search_result = self.__get_endpoint(endpoint)
        wallpapers = [Wallpaper(**x) for x in search_result.get('data')]
        meta = Meta(**search_result.get('meta'))
        return wallpapers, meta
