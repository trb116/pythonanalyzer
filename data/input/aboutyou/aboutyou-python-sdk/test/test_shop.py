#-*- coding: utf-8 -*-
"""
:Author:    Arne Simon [arne.simon@slice-dice.de]
"""
from aboutyou.api import ApiException
from aboutyou.constants import FACET
from aboutyou.shop import Node
from pytest import raises


def test_categories(shop):
    tree = shop.categories()

    assert len(tree) > 0

    categorie = tree[1]

    assert len(categorie.sub_categories) > 0


def test_category_by_name(shop):
    name = 'Subcategory 2.1'
    cat = shop.category_by_name(name)

    assert cat is not None
    assert cat.name == name


def test_category_by_id(shop):
    cat = shop.category_by_id(200)

    assert cat.id == 200
    assert cat.name == 'Main Category 2'


def test_facet_groups(shop):
    groups = shop.facet_groups()

    assert len(groups) > 0


def test_facet_group_by_id(shop):
    group = shop.facet_group_by_id('color')

    assert group.id == FACET.COLOR


def test_products_by_id(shop, mock):
    mock('products/products-full.json')

    ids = [123, 456]
    products, with_errors = shop.products_by_id(ids)

    p = products[456]

    assert p.id in ids

    assert p.categories is not None
    assert p.description_short is not None
    assert p.description_long is not None
    assert p.default_variant is not None
    assert p.default_image is not None
    assert p.variants is not None
    assert p.styles is not None


def test_products_by_ean(shop, mock):
    mock('products/products_eans.json')

    products = shop.products_by_ean([8806159322381], fields=['variants'])


def test_search(shop, session, mock):
    mock('search/product_search.json')

    result = shop.search(session, filter={"categories":[100, 200]})

    assert result.count == 1234

    p1, p2 = result.products[:2]

    assert p1.id == 123

    for product in result.products:
        pass


def test_simple_colors(shop):
    result = shop.simple_colors()

    assert len(result) > 0
    assert isinstance(result[0], Node)


def test_javascript(shop):
    shop.javascript_url()
    shop.javascript_tag()


class TestBasket:
    def test_add(self, shop, session, mock):
        basket = shop.basket(session)

        mock('products/products-full.json')

        products, with_error = shop.products_by_id([123, 456])

        product = products[456]

        variant = product.variants[0]

        mock('basket/basket.json')

        basket.set(variant, 1)

    def test_remove(self, shop, session, mock):
        basket = shop.basket(session)


    def test_costumize(self, shop, session, mock):
        basket = shop.basket(session)

        mock('products/products-full.json')

        products, with_error = shop.products_by_id([123, 456])

        product = products[456]

        variant = product.variants[0]

        assert variant.id == 5145543

        costum = variant.costumize()

        costum.additional_data['description'] = ''

# def test_basket(shop, session):
#     try:
#         basket = shop.basket(session)

#         product = shop.products_by_id([434091])[0]

#         variant = product.variants[0]

#         print variant.live

#         basket.set(variant, 1)

#         costum = variant.costumize()

#         # costum.additional_data['logo'] = 'Green Frog'

#         basket.set(costum, 2)

#         print basket.obj

#         assert len(basket.obj['order_lines']) == 3

#         assert basket.obj['order_lines'][0]['variant_id'] == variant.id

#         print basket.order('http://maumau.de')
#     except Exception as e:
#         raise e
#     finally:
#         basket.dispose()


def test_autocomplete(shop, mock):
    data = mock('autocomplete-sho.json')

    with raises(ApiException):
        products, categories = shop.autocomplete('sho')


def test_suggest(shop, mock):
    data = mock('suggest.json')
    shop.suggest('sho')
