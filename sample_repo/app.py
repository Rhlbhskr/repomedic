from auth import register_user
from orders import create_order


def main():
    payload = {
        "name": "Rahul",
        "email": "rahul@example.com",
    }

    user = register_user(payload)
    print("User:", user)

    product = {
        "name": "Keyboard",
        "price": 100,
        "quantity": 2,
        "discount": 50,
    }

    order = create_order(product)
    print("Order:", order)


if __name__ == "__main__":
    main()