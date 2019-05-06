#-*- coding: utf-8 -*-
"""
:Author:    Arne Simon [arne.simon@slice-dice.de]

Some contsants which are blatantly copied from the php-sdk.
"""

class FACET:
    BRAND = 0
    CLOTHING_MEN_BELTS_CM = 190
    CLOTHING_MEN_DE = 187
    CLOTHING_MEN_INCH = 189
    CLOTHING_UNISEX_INCH = 174
    CLOTHING_UNISEX_INT = 173
    CLOTHING_UNISEX_ONESIZE = 204
    CLOTHING_WOMEN_BELTS_CM = 181
    CLOTHING_WOMEN_DE = 175
    CLOTHING_WOMEN_INCH = 180
    COLOR = 1
    CUPSIZE = 4
    DIMENSION3 = 6
    GENDERAGE = 3
    LENGTH = 5
    SHOES_UNISEX_ADIDAS_EUR = 195
    SHOES_UNISEX_EUR = 194
    SIZE = 2
    SIZE_CODE = 206
    SIZE_RUN = 172

    ALL = set([BRAND, CLOTHING_MEN_BELTS_CM,
               CLOTHING_MEN_DE, CLOTHING_MEN_INCH,
               CLOTHING_UNISEX_INCH, CLOTHING_UNISEX_INT,
               CLOTHING_UNISEX_ONESIZE, CLOTHING_WOMEN_BELTS_CM,
               CLOTHING_WOMEN_DE, CLOTHING_WOMEN_INCH,
               COLOR, CUPSIZE, DIMENSION3, GENDERAGE,
               LENGTH, SHOES_UNISEX_ADIDAS_EUR,
               SHOES_UNISEX_EUR, SIZE, SIZE_CODE,
               SIZE_RUN,
             ])


class SORT:
    CREATED = "created_date"
    MOST_VIEWED = "most_viewed"
    PRICE = "price"
    RELEVANCE = "relevance"
    UPDATED = "updated_date"

    ALL = set([RELEVANCE, UPDATED, CREATED,
               MOST_VIEWED, PRICE])


class TYPE:
    CATEGORIES = "categories"
    PRODUCTS = "products"
    ALL = set([CATEGORIES, PRODUCTS])


class PRODUCT_FIELD:
    VARIANTS = "variants"
    DESCRIPTION_LONG = "description_long"
    DESCRIPTION_SHORT = "description_short"
    MIN_PRICE = "min_price"
    MAX_PRICE = "max_price"
    SALE = "sale"
    DEFAULT_VARIANT = "default_variant"
    DEFAULT_IMAGE = "default_image"
    CATEGORIES = "categories"

    ALL = set([VARIANTS,
               DESCRIPTION_LONG,
               DESCRIPTION_SHORT,
               MIN_PRICE,
               MAX_PRICE, SALE,
               DEFAULT_VARIANT,
               DEFAULT_IMAGE,
               CATEGORIES,])