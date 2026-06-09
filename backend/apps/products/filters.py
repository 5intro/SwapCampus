"""商品模块 django-filter 筛选器."""

import django_filters as filters

from apps.products.models import Product


class ProductFilter(filters.FilterSet):
    """商品高级筛选."""

    seller = filters.UUIDFilter(field_name="seller_id", lookup_expr="exact")
    category = filters.UUIDFilter(field_name="category_id", lookup_expr="exact")
    price_min = filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = filters.NumberFilter(field_name="price", lookup_expr="lte")
    condition = filters.ChoiceFilter(choices=Product.Condition.choices)
    campus = filters.CharFilter(field_name="campus", lookup_expr="icontains")
    status = filters.ChoiceFilter(choices=Product.Status.choices)
    tag = filters.UUIDFilter(field_name="tags__id", lookup_expr="exact", label="按标签筛选")
    sort_by = filters.OrderingFilter(
        fields={
            "price": "price_asc",
            "-price": "price_desc",
            "-created_at": "newest",
            "created_at": "oldest",
            "-view_count": "popular",
        },
    )

    class Meta:
        model = Product
        fields = ["category", "price_min", "price_max", "condition", "campus", "status"]
