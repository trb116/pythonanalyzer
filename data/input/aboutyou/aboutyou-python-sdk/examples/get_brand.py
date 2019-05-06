#-*- coding: utf-8 -*-
"""
:Author: Arne Simon [arne.simon@slice-dice.de]
"""
from aboutyou.shop import ShopApi
from aboutyou.config import Credentials

shop = ShopApi(Credentials(123, 'token'))

products, with_erros = shop.products_by_id([239982])

for product in products.values():
    print product.name

    for v in product.variants:
        print v.id
        print [f.name for f in v.attributes["brand"]]