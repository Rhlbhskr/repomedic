from users import create_user


def register_user(data):
    name = data["name"]
    email = data["email"]

    phone_number = data["phone_number"]

    return create_user(
        name=name,
        email=email,
        phone_number=phone_number
    )