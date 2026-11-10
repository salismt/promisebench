"""Card number helpers: normalisation, checksum, brand and masking."""


def normalize(number):
    """Strip the spaces and dashes customers type into card fields."""
    return "".join(ch for ch in str(number) if ch.isdigit())


def luhn_valid(number):
    digits = normalize(number)
    if not 12 <= len(digits) <= 19:
        return False
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def card_brand(number):
    digits = normalize(number)
    if digits.startswith("4"):
        return "visa"
    if digits[:2] in ("34", "37"):
        return "amex"
    if digits[:2] in ("51", "52", "53", "54", "55") or 2221 <= int(digits[:4] or 0) <= 2720:
        return "mastercard"
    if digits.startswith("6011") or digits.startswith("65"):
        return "discover"
    return "unknown"


def last4(number):
    return normalize(number)[-4:]


def mask_pan(number):
    """Return the PCI-safe display form: first 6 and last 4 digits only."""
    digits = normalize(number)
    if len(digits) < 12:
        return "*" * len(digits)
    return digits[:6] + "*" * (len(digits) - 10) + digits[-4:]
