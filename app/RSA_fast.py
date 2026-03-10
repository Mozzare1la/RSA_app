import random

# определяем простоту числа
def is_prime_fast(min, max):

    prime = False

    while prime == False:

        n = random.randint(min, max)

        k = 0
        for i in range(2, n // 2 + 1):
            if n % i == 0:
                k = 1
        if k == 0:
            prime = True
            return n


# генерируем ключи
def RSA_key_gen_fast():

    p = is_prime_fast(1000, 9999)
    q = is_prime_fast(1000, 9999)

    n = p * q

    phi = (p - 1) * (q - 1)

    e = is_prime_fast(1000000, phi)

    d = pow(e, -1, phi)

    d = abs(d)

    pub_key = [e, n]

    priv_key = [d, n]

    return (pub_key, priv_key)


# шифрование
def RSA_encrypt_fast(text, pub_key):

    print("fast")

    text = [ord(c) for c in text]
    cipher = []

    for i in text:

        cipher_part = pow(i, pub_key[0], pub_key[1])

        cipher.append(cipher_part)

    return cipher


# расшифрование
def RSA_decrypt_fast(cipher, priv_key):

    print("fast")

    text = []

    for i in cipher:

        text_part = pow(i, priv_key[0], priv_key[1])

        text.append(text_part)

    text = [chr(c) for c in text]

    return text
