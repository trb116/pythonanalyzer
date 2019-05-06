from decimal import Decimal

from django.test import SimpleTestCase, override_settings
from sellmo.apps.pricing import Price


A = 'A'
B = 'B'


@override_settings(
    INSTALLED_APPS=[
        'sellmo.apps.pricing',
        'sellmo'
    ]
)
class PricingTestCase(SimpleTestCase):

    def test_init(self):
        self.assertEqual(Price(100).amount, 100)
        self.assertEqual(Price(100.5).amount, 100.5)
        self.assertEqual(Price('100.513').amount, Decimal('100.513'))
        self.assertEqual(Price(10, component=A).amount, 10)

    def test_equal(self):
        self.assertEqual(Price(100), Price(100))
        self.assertEqual(Price(10, component=A), Price(10, component=A))

    def test_not_equal(self):
        self.assertNotEqual(Price(100), Price(200))
        self.assertNotEqual(Price(10, component=A), Price(10, component=B))

    def test_addition(self):
        self.assertEqual(
            Price(100) + Price(100),
            Price(200)
        )

        self.assertEqual(
            (Price(50) + Price(10, component=A) + Price(50))[A],
            Price(10, component=A)
        )
