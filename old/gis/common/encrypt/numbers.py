def encrypt_phone(phone: str):
    if phone is None:
        return phone
    return phone[:3] + "*****" + phone[-3:]


def encrypt_bank_no(bank_no: str):
    if bank_no is None:
        return bank_no
    return bank_no[:4] + "********" + bank_no[-4:]
