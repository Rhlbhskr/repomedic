from config import TAX_RATE


def calculate_total(price, quantity, discount=0):
    subtotal = price * quantity

    discounted_total = subtotal - discount

    tax = subtotal * TAX_RATE

    return discounted_total + tax