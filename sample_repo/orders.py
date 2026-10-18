from pricing import calculate_total


def create_order(product):
    return {
        "product": product["name"],
        "total": calculate_total(
            product["price"],
            product["quantity"],
            product.get("discount", 0),
        ),
    }