"""商品模块业务逻辑."""

from apps.products.models import Product, ProductImage


def get_cover_image(product: Product) -> ProductImage | None:
    """返回商品的封面图."""
    return product.cover_image


def change_product_status(product: Product, new_status: str) -> Product:
    """变更商品状态（带基本校验）."""
    valid_statuses = dict(Product.Status.choices).keys()
    if new_status not in valid_statuses:
        raise ValueError(f"无效的商品状态: {new_status}")
    product.status = new_status
    product.save(update_fields=["status", "updated_at"])
    return product
