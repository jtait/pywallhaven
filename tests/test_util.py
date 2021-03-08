import unittest

from pywallhaven.util import create_parameter_string, validate_parameter, purity_list_as_numeric_string, build_q_string


class TestCreateParameterString(unittest.TestCase):
    def test_one_parameter(self):
        string = create_parameter_string(purity=111)
        self.assertIsInstance(string, str)
        self.assertEqual("?purity=111", string)

    def test_two_parameters(self):
        string = create_parameter_string(purity=111, page=4)
        self.assertIsInstance(string, str)
        self.assertTrue("page=4" in string)
        self.assertTrue("purity=111" in string)
        self.assertTrue(string[0] == "?")
        self.assertTrue(string.count("&") == 1)

    def test_invalid_keys(self):
        with self.assertRaises(KeyError):
            create_parameter_string(invalid='a')

    def test_invalid_values(self):
        for x in [2.0, None]:
            with self.assertRaises(ValueError):
                create_parameter_string(purity=x)


class TestValidateParameter(unittest.TestCase):

    def test_validate_non_string(self):
        for x in [1, 4.0, None]:
            with self.assertRaises(TypeError):
                validate_parameter('test', x)
            with self.assertRaises(TypeError):
                validate_parameter(x, 'test')
            with self.assertRaises(TypeError):
                validate_parameter(x, x)

    def test_purity_valid(self):
        for x in ['000', '001', '010', '011', '100', '101', '110', '111']:
            self.assertEqual(('purity', x), validate_parameter('purity', x))

    def test_purity_invalid(self):
        for x in ['1111', '1', '2', '11']:
            with self.assertRaises(ValueError):
                validate_parameter('purity', x)

    def test_order_valid(self):
        for x in ['asc', 'desc']:
            self.assertEqual(('order', x), validate_parameter('order', x))

    def test_order_invalid(self):
        for x in ['dsc', 'ascending']:
            with self.assertRaises(ValueError):
                validate_parameter('order', x)
        for x in [1, 4.0, True, False]:
            with self.assertRaises(TypeError):
                validate_parameter('order', x)

    def test_topRange_valid(self):
        for x in ['1d', '3d', '1w', '1M', '3M', '6M', '1y']:
            self.assertEqual(('topRange', x), validate_parameter('topRange', x))

    def test_topRange_invalid(self):
        for x in ['1m', 'ascending', '1', '4M', '1Y']:
            with self.assertRaises(ValueError):
                validate_parameter('topRange', x)
        for x in [1, 4.0, True, False]:
            with self.assertRaises(TypeError):
                validate_parameter('topRange', x)

    def test_q_valid(self):
        for x in ['tree', '+tree', 'like:123abc', 'id:54']:
            self.assertEqual(('q', x), validate_parameter('q', x))

    def test_q_invalid(self):
        for x in ['id:14 +tree', 'green like:123abc', 'id:4r']:
            with self.assertRaises(ValueError):
                validate_parameter('q', x)

class TestPurityListAsNumericString(unittest.TestCase):
    def test_valid(self):
        for x in [
            ([], '000'),
            (['sfw'], '100'),
            (['sketchy'], '010'),
            (['sfw', 'sketchy'], '110'),
            (['nsfw'], '001'),
            (['nsfw', 'sfw'], '101'),
            (['nsfw', 'sketchy'], '011'),
            (['nsfw', 'sketchy', 'sfw'], '111')
        ]:
            self.assertEqual(purity_list_as_numeric_string(x[0]), x[1])


class TestBuildQString(unittest.TestCase):
    def test_valid(self):
        s = build_q_string(
            include_tags=['trees', 'green', 'two words', 1],
            exclude_tags=['spruce'],
            username='test_user',
            image_type='png'
        )
        self.assertEqual(s, '%20%2Btrees%20%2Bgreen%20%2Btwo+words%20%2B1%20-spruce @test_user type:png')

    def test_invalid_image_type(self):
        with self.assertRaises(ValueError):
            build_q_string(
                include_tags=['trees', 'green', 'two words'],
                exclude_tags=['spruce'],
                username='test_user',
                image_type='invalid'
            )
