"""
Unit tests for pywallhaven.wallhaven
"""


import json
import os
import unittest
from datetime import datetime

import responses
import requests
import dataclasses

from pywallhaven import Wallpaper, Tag, UserSettings, Uploader, Wallhaven, Meta, Collection


def get_resource_file(file_name: str):
    """
    Helper method to grab resource file path
    :param file_name: The basename of the file
    :return: The full path to the file
    """
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources', file_name)


class TestWallpaper(unittest.TestCase):
    def test_init(self):
        with open(get_resource_file("test_wallpaper.json"), 'r') as fp:
            wallpaper = Wallpaper(**json.load(fp)['data'])
            self.assertIsInstance(wallpaper, Wallpaper)
            self.assertGreater(len(wallpaper.tags), 0)
            self.assertIsInstance(Tag(**wallpaper.tags[0]), Tag)
            self.assertIsInstance(Uploader(**wallpaper.uploader), Uploader)
            self.assertIsInstance(wallpaper.created_at_datetime, datetime)

    def test_tags_as_class_list(self):
        with open(get_resource_file("test_wallpaper.json"), 'r') as fp:
            wallpaper = Wallpaper(**json.load(fp)['data'])
            for tag in wallpaper.tags_as_class_list:
                self.assertIsInstance(tag, Tag)
                self.assertIsInstance(tag.name, str)
                self.assertIsInstance(tag.id, int)
                self.assertIn(tag.purity, ['sfw', 'sketchy', 'nsfw'])

    def test_uploader_as_class(self):
        with open(get_resource_file("test_wallpaper.json"), 'r') as fp:
            wallpaper = Wallpaper(**json.load(fp)['data'])
            uploader = wallpaper.uploader_as_class
            self.assertIsInstance(uploader, Uploader)
            self.assertIsInstance(uploader.username, str)
            self.assertIsInstance(uploader.group, str)
            self.assertIsInstance(uploader.avatar, dict)


class TestUserSettings(unittest.TestCase):
    def test_init(self):
        with open(get_resource_file("test_user_settings.json"), 'r') as fp:
            user_settings = UserSettings(**json.load(fp)['data'])
            self.assertIsInstance(user_settings, UserSettings)


class TestTag(unittest.TestCase):
    def test_init(self):
        with open(get_resource_file("test_tag.json"), 'r') as fp:
            tag = Tag(**json.load(fp)['data'])
            self.assertIsInstance(tag, Tag)
            self.assertIsInstance(tag.created_at_datetime, datetime)


class TestWallhaven(unittest.TestCase):
    def test_init_no_api_key(self):
        w = Wallhaven()
        self.assertIsInstance(w, Wallhaven)

    def test_init_with_api_key(self):
        api_key = 'testkeyisinvalid'
        w = Wallhaven(api_key=api_key)
        self.assertIsInstance(w, Wallhaven)
        self.assertEqual(w._Wallhaven__api_key, api_key)


class TestUserSettingsEndpoint(unittest.TestCase):
    def test_without_api_key(self):
        w = Wallhaven()
        with self.assertRaises(AttributeError):
            w.get_user_settings()


class TestSearchEndpoint(unittest.TestCase):
    def test_invalid_parameters(self):
        w = Wallhaven()
        with self.assertRaises(ValueError):
            w.search(purity='1111')
        with self.assertRaises(KeyError):
            w.search(test_parameter='1111')
        with self.assertRaises(ValueError):
            w.search(q='id:r4e5tg')


class TestCollectionsEndpoint(unittest.TestCase):
    def test_without_api_key(self):
        w = Wallhaven()
        with self.assertRaises(AttributeError):
            w.get_collections()


class TestCollectionEndpoint(unittest.TestCase):
    def test_invalid_parameters(self):
        w = Wallhaven()
        username = 'test'
        collection_id = 1
        with self.assertRaises(KeyError):
            w.get_collection(username, collection_id, test_parameter='1111')
        with self.assertRaises(ValueError):
            w.get_collection(username, collection_id, purity='1111')
        with self.assertRaises(ValueError):
            w.get_collection(username, collection_id, page='-1')


class TestMockEndpoint(unittest.TestCase):
    def setUp(self):
        """
        Helps cleanup responses after test runs to ensure clean state.
        :return:
        """
        self.responses = responses.RequestsMock()
        self.responses.start()
        self.addCleanup(self.responses.stop)
        self.addCleanup(self.responses.reset)

    @responses.activate
    def test_error_code_response(self):
        w = Wallhaven()
        for e in [400, 404, 422]:
            responses.add(responses.GET, 'https://wallhaven.cc/api/v1/search', status=e)
            with self.assertRaises(requests.exceptions.RequestException):
                w.search()
            responses.reset()
        for e in [500, 502, 503]:
            responses.add(responses.GET, 'https://wallhaven.cc/api/v1/search', status=e)
            with self.assertRaises(requests.exceptions.ConnectionError):
                w.search()
            responses.reset()
        for e in [201]:
            responses.add(responses.GET, 'https://wallhaven.cc/api/v1/search', status=e)
            with self.assertRaises(requests.exceptions.HTTPError):
                w.search()
            responses.reset()

    @responses.activate
    def test_connection_error(self):
        w = Wallhaven()
        responses.add(responses.GET, 'https://wallhaven.cc/api/v1/search', body=requests.exceptions.ConnectionError())
        with self.assertRaises(requests.exceptions.ConnectionError):
            w.search()

    @responses.activate
    def test_empty_response(self):
        responses.add(
            responses.GET, 'https://wallhaven.cc/api/v1/search', status=200, body=''
        )
        w = Wallhaven()
        with self.assertRaises(json.decoder.JSONDecodeError):
            w.search()

    @responses.activate
    def test_invalid_json(self):
        responses.add(
            responses.GET, 'https://wallhaven.cc/api/v1/search', status=200, body='{}}'
        )
        w = Wallhaven()
        with self.assertRaises(IOError):
            w.search()

    @responses.activate
    def test_valid_wallpaper_json(self):
        wallpaper_id = '6k3oox'
        with open(get_resource_file("test_wallpaper.json"), 'r') as fp:
            mock_json = json.load(fp)
            responses.add(
                responses.GET, 'https://wallhaven.cc/api/v1/w/{}'.format(wallpaper_id), status=200, json=mock_json
            )
            w = Wallhaven()
            wallpaper = w.get_wallpaper(wallpaper_id)
            self.assertIsInstance(wallpaper, Wallpaper)
            self.assertEqual(dataclasses.asdict(wallpaper), mock_json['data'])

    @responses.activate
    def test_valid_tag_json(self):
        tag_id = 4
        with open(get_resource_file("test_tag.json"), 'r') as fp:
            mock_json = json.load(fp)
            responses.add(
                responses.GET, 'https://wallhaven.cc/api/v1/tag/{}'.format(str(tag_id)), status=200,
                json=mock_json
            )
            w = Wallhaven()
            tag = w.get_tag(tag_id)
            self.assertIsInstance(tag, Tag)
            self.assertEqual(dataclasses.asdict(tag), mock_json['data'])

    @responses.activate
    def test_valid_user_settings_json(self):
        with open(get_resource_file("test_user_settings.json"), 'r') as fp:
            mock_json = json.load(fp)
            responses.add(
                responses.GET, 'https://wallhaven.cc/api/v1/settings', status=200,
                json=mock_json
            )
            w = Wallhaven(api_key='testkeyisinvalid')
            settings = w.get_user_settings()
            self.assertIsInstance(settings, UserSettings)
            self.assertEqual(dataclasses.asdict(settings), mock_json['data'])

    @responses.activate
    def test_valid_search_json(self):
        with open(get_resource_file("test_search.json"), 'r') as fp:
            mock_json = json.load(fp)
            responses.add(
                responses.GET, 'https://wallhaven.cc/api/v1/search', status=200,
                json=mock_json
            )
            w = Wallhaven()
            result_wallpapers, result_meta = w.search()
            self.assertEqual(dataclasses.asdict(result_meta), mock_json['meta'])
            self.assertIsInstance(result_wallpapers, list)
            for w in result_wallpapers:
                self.assertIsInstance(w, Wallpaper)
            self.assertIsInstance(result_meta, Meta)

    @responses.activate
    def test_valid_search_json_with_page_in_kwargs(self):
        with open(get_resource_file("test_search.json"), 'r') as fp:
            mock_json = json.load(fp)
            responses.add(
                responses.GET, 'https://wallhaven.cc/api/v1/search', status=200,
                json=mock_json
            )
            w = Wallhaven()
            result_wallpapers, result_meta = w.search(**{'page': 1})
            self.assertEqual(dataclasses.asdict(result_meta), mock_json['meta'])
            self.assertIsInstance(result_wallpapers, list)
            for w in result_wallpapers:
                self.assertIsInstance(w, Wallpaper)
            self.assertIsInstance(result_meta, Meta)

    @responses.activate
    def test_valid_collections_json(self):
        with open(get_resource_file("test_collections.json"), 'r') as fp:
            mock_json = json.load(fp)
            responses.add(
                responses.GET, 'https://wallhaven.cc/api/v1/collections', status=200,
                json=mock_json
            )
            w = Wallhaven(api_key='testkeyisinvalid')
            collections = w.get_collections()
            self.assertIsInstance(collections, list)
            for c in collections:
                self.assertIsInstance(c, Collection)

    @responses.activate
    def test_valid_user_collections_json(self):
        with open(get_resource_file("test_user_collections.json"), 'r') as fp:
            mock_json = json.load(fp)
            username = 'test_user'
            responses.add(
                responses.GET, 'https://wallhaven.cc/api/v1/collections/{}'.format(username), status=200,
                json=mock_json
            )
            w = Wallhaven()
            collections = w.get_collections(username=username)
            self.assertIsInstance(collections, list)
            for c in collections:
                self.assertIsInstance(c, Collection)

    @responses.activate
    def test_valid_user_collection_json(self):
        with open(get_resource_file("test_user_collection.json"), 'r') as fp:
            mock_json = json.load(fp)
            username = 'test_user'
            collection_id = 1
            responses.add(
                responses.GET, 'https://wallhaven.cc/api/v1/collections/{}/{}'.format(username, str(collection_id)),
                status=200,
                json=mock_json
            )
            w = Wallhaven()
            collection, meta = w.get_collection(username, collection_id)
            self.assertIsInstance(collection, list),
            for w in collection:
                self.assertIsInstance(w, Wallpaper)
            self.assertIsInstance(meta, Meta)

    @responses.activate
    def test_valid_user_collection_json_with_page_in_kwargs(self):
        with open(get_resource_file("test_user_collection.json"), 'r') as fp:
            mock_json = json.load(fp)
            username = 'test_user'
            collection_id = 1
            responses.add(
                responses.GET, 'https://wallhaven.cc/api/v1/collections/{}/{}'.format(username, str(collection_id)),
                status=200,
                json=mock_json
            )
            w = Wallhaven()
            collection, meta = w.get_collection(username, collection_id, **{'page': 1})
            self.assertIsInstance(collection, list),
            for w in collection:
                self.assertIsInstance(w, Wallpaper)
            self.assertIsInstance(meta, Meta)


class TestPagedCollection(unittest.TestCase):
    def setUp(self):
        """
        Helps cleanup responses after test runs to ensure clean state.
        :return:
        """
        self.responses = responses.RequestsMock()
        self.responses.start()
        self.addCleanup(self.responses.stop)
        self.addCleanup(self.responses.reset)

    @responses.activate
    def test_paged_collection(self):
        username = 'test_user'
        collection_id = 1
        for i in range(1, 4):
            with open(get_resource_file(os.path.join("test_paged_collection", f"page{i}.json")), 'r') as fp:
                responses.add(
                    responses.GET,
                    f"https://wallhaven.cc/api/v1/collections/{username}/{collection_id}?page={i}",
                    status=200,
                    json=json.load(fp)
                )
        w = Wallhaven()
        collection_pages = w.get_collection_pages(username, collection_id)
        for wallpapers, meta in collection_pages:
            self.assertIsInstance(meta, Meta)
            for w in wallpapers:
                self.assertIsInstance(w, Wallpaper)

    def test_paged_collection_invalid_parameters(self):
        w = Wallhaven()
        username = 'test'
        collection_id = 1
        with self.assertRaises(KeyError):
            next(w.get_collection_pages(username, collection_id, test_parameter='1111'))
        with self.assertRaises(ValueError):
            next(w.get_collection_pages(username, collection_id, purity='1111'))
        with self.assertRaises(AttributeError):
            next(w.get_collection_pages(username, collection_id, page='-1'))


class TestPagedSearch(unittest.TestCase):
    def setUp(self):
        """
        Helps cleanup responses after test runs to ensure clean state.
        :return:
        """
        self.responses = responses.RequestsMock()
        self.responses.start()
        self.addCleanup(self.responses.stop)
        self.addCleanup(self.responses.reset)

    @responses.activate
    def test_paged_search(self):
        # cheat a bit and reuse the collection pages for testing the generator
        for i in range(1, 4):
            with open(get_resource_file(os.path.join("test_paged_collection", f"page{i}.json")), 'r') as fp:
                responses.add(
                    responses.GET,
                    f"https://wallhaven.cc/api/v1/search?page={i}",
                    status=200,
                    json=json.load(fp)
                )
        w = Wallhaven()
        pages = w.get_search_pages()
        for wallpapers, meta in pages:
            self.assertIsInstance(meta, Meta)
            for w in wallpapers:
                self.assertIsInstance(w, Wallpaper)

    def test_paged_collection_invalid_parameters(self):
        w = Wallhaven()
        with self.assertRaises(KeyError):
            next(w.get_search_pages(test_parameter='1111'))
        with self.assertRaises(ValueError):
            next(w.get_search_pages(purity='1111'))
        with self.assertRaises(AttributeError):
            next(w.get_search_pages(page='-1'))
