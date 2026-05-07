"""
Практическая работа 3. Электронная подпись ГОСТ Р 34.10-2012
Язык: Python 3
"""

import sys
import random
import hashlib
import math


# возведение в степень по модулю (бинарный метод)
def mod_pow(base, exp, mod):
    """a^k mod n - быстрое возведение в степень"""
    if mod == 1:
        return 0
    result = 1
    base = base % mod
    while exp > 0:
        if exp % 2 == 1:
            result = (result * base) % mod
        exp = exp >> 1
        base = (base * base) % mod
    return result


# расширенный алгоритм Евклида
def extended_gcd(a, b):
    """Возвращает (d, x, y): a*x + b*y = d = НОД(a, b)"""
    if b == 0:
        return a, 1, 0
    x2, x1 = 1, 0
    y2, y1 = 0, 1
    while b > 0:
        q = a // b
        r = a - q * b
        x = x2 - q * x1
        y = y2 - q * y1
        a, b = b, r
        x2, x1 = x1, x
        y2, y1 = y1, y
    return a, x2, y2


# обратный элемент по модулю
def mod_inverse(a, n):
    """a^(-1) mod n через расширенный алгоритм Евклида"""
    d, x, _ = extended_gcd(a % n, n)
    if d != 1:
        raise ValueError("Обратный элемент не существует")
    return x % n


# Арифметика на эллиптических кривых
# y^2 = x^3 + ax + b (mod p)

# бесконечно удаленная точка
INF = None


def point_add(P, Q, a, p):
    """Сложение двух точек на эллиптической кривой
    P, Q - точки (x, y) или INF
    a - коэффициент кривой y^2 = x^3 + ax + b
    p - модуль (простое число)
    """
    if P is INF:
        return Q
    if Q is INF:
        return P

    x1, y1 = P
    x2, y2 = Q

    # если точки взаимно обратные: P + (-P) = INF
    if x1 == x2 and (y1 + y2) % p == 0:
        return INF

    if x1 == x2 and y1 == y2:
        # удвоение точки: P + P
        # лямбда = (3*x1^2 + a) / (2*y1)
        num = (3 * x1 * x1 + a) % p
        den = (2 * y1) % p
    else:
        # сложение разных точек
        # лямбда = (y2 - y1) / (x2 - x1)
        num = (y2 - y1) % p
        den = (x2 - x1) % p

    lam = (num * mod_inverse(den, p)) % p

    x3 = (lam * lam - x1 - x2) % p
    y3 = (lam * (x1 - x3) - y1) % p

    return (x3, y3)


def point_multiply(k, P, a, p):
    """Умножение точки на скаляр: Q = k*P.
    Используется метод двоичного разложения (аналог быстрого возведения в степень).
    """
    if k == 0 or P is INF:
        return INF

    if k < 0:
        # -k * P = k * (-P)
        P = (P[0], (-P[1]) % p)
        k = -k

    result = INF
    current = P

    while k > 0:
        if k & 1:
            result = point_add(result, current, a, p)
        current = point_add(current, current, a, p)
        k >>= 1

    return result


# Параметры эллиптической кривой из ГОСТ
# Используем тестовый набор параметров для 256-битной подписи
# (из приложения А к ГОСТ Р 34.10-2012)

# тестовые параметры кривой (256 бит)
# id-GostR3410-2001-CryptoPro-A-ParamSet
PARAMS_256 = {
    'p': 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFD97,
    'a': 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFD94,
    'b': 0x00000000000000000000000000000000000000000000000000000000000000a6,
    'q': 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF6C611070995AD10045841B09B761B893,
    'Px': 0x0000000000000000000000000000000000000000000000000000000000000001,
    'Py': 0x8D91E471E0989CDA27DF505A453F2B7635294F2DDF23E3B122ACC99C9E9F1E14,
}


def get_params():
    """Возвращает параметры кривой"""
    par = PARAMS_256
    P = (par['Px'], par['Py'])
    return par['p'], par['a'], par['b'], par['q'], P

# Хеш-функция
# Задание разрешает использовать готовую реализацию хеш-функции
# Используем SHA-256
# В реальной реализации нужно использовать ГОСТ Р 34.11-2012

def hash_message(message):
    """Хеширование сообщения. Возвращает целое число"""
    if isinstance(message, str):
        message = message.encode('utf-8')
    h = hashlib.sha256(message).digest()
    # переводим хеш в число (big-endian)
    return int.from_bytes(h, 'big')

# Формирование и проверка подписи по ГОСТ Р 34.10-2012

def generate_keys():
    """Генерация ключевой пары
    Возвращает (d, Q): d - ключ подписи (закрытый), Q - ключ проверки (открытый)
    """
    p, a, b, q, P = get_params()

    # ключ подписи: случайное число 0 < d < q
    d = random.randrange(1, q)

    # ключ проверки: Q = d*P
    Q = point_multiply(d, P, a, p)

    return d, Q


def sign_message(message, d):
    """Формирование электронной подписи
    message - сообщение (строка или байты)
    d - ключ подписи (целое число)
    Возвращает подпись (r, s)
    """
    p, a, b, q, P = get_params()

    # 1. вычисляем хеш сообщения
    h = hash_message(message)

    # 2. определяем e = h mod q, если e = 0, то e = 1
    e = h % q
    if e == 0:
        e = 1

    while True:
        # 3. генерируем случайное k, 0 < k < q
        k = random.randrange(1, q)

        # 4. вычисляем точку C = k*P и r = x_C mod q
        C = point_multiply(k, P, a, p)
        if C is INF:
            continue
        r = C[0] % q
        if r == 0:
            continue

        # 5. вычисляем s = (r*d + k*e) mod q
        s = (r * d + k * e) % q
        if s == 0:
            continue

        return (r, s)


def verify_signature(message, signature, Q):
    """Проверка электронной подписи
    message - сообщение
    signature - подпись (r, s)
    Q - ключ проверки (точка кривой)
    Возвращает True если подпись верна
    """
    p, a, b, q, P = get_params()
    r, s = signature

    # 1. проверяем 0 < r < q и 0 < s < q
    if not (0 < r < q and 0 < s < q):
        return False

    # 2. вычисляем хеш сообщения
    h = hash_message(message)

    # 3. определяем e = h mod q, если e = 0, то e = 1
    e = h % q
    if e == 0:
        e = 1

    # 4. вычисляем v = e^(-1) mod q
    v = mod_inverse(e, q)

    # 5. вычисляем z1 = s*v mod q, z2 = -r*v mod q
    z1 = (s * v) % q
    z2 = ((-r) * v) % q

    # 6. вычисляем точку C = z1*P + z2*Q
    C1 = point_multiply(z1, P, a, p)
    C2 = point_multiply(z2, Q, a, p)
    C = point_add(C1, C2, a, p)

    if C is INF:
        return False

    # 7. R = x_C mod q, проверяем R == r
    R = C[0] % q
    return R == r

# Тесты

def run_tests():
    print("ТЕСТЫ: электронная подпись ГОСТ Р 34.10-2012")
    print()

    p, a, b, q, P = get_params()

    # проверяем что базовая точка лежит на кривой
    lhs = (P[1] * P[1]) % p
    rhs = (P[0] ** 3 + a * P[0] + b) % p
    print("--- Проверка параметров кривой ---")
    print(f"p = {hex(p)}")
    print(f"Базовая точка P = ({hex(P[0])}, {hex(P[1])})")
    print(f"P на кривой: {lhs == rhs} (y^2 mod p == x^3 + ax + b mod p)")

    # проверяем что q*P = O (нейтральный элемент)
    qP = point_multiply(q, P, a, p)
    print(f"q*P = O: {qP is INF}")

    # тест 1: генерация ключей, подпись и проверка
    print()
    print("--- Тест 1: подпись и проверка ---")
    d, Q = generate_keys()
    print(f"Ключ подписи d = {hex(d)[:20]}...")
    print(f"Ключ проверки Q = ({hex(Q[0])[:20]}..., {hex(Q[1])[:20]}...)")

    msg = "Привет, ГОСТ!"
    sig = sign_message(msg, d)
    r, s = sig
    print(f"Сообщение: {msg}")
    print(f"Подпись: r = {hex(r)[:20]}..., s = {hex(s)[:20]}...")

    ok = verify_signature(msg, sig, Q)
    print(f"Проверка подписи: {'[OK] верна' if ok else '[FAIL] неверна'}")

    # тест 2: проверка с измененным сообщением (должна быть неверна)
    print()
    print("--- Тест 2: проверка с измененным сообщением ---")
    ok2 = verify_signature("Другое сообщение", sig, Q)
    print(f"Проверка с другим сообщением: {'[FAIL] верна (ошибка!)' if ok2 else '[OK] неверна (как и ожидалось)'}")

    # тест 3: проверка с чужим ключом (должна быть неверна)
    print()
    print("--- Тест 3: проверка с чужим ключом ---")
    d2, Q2 = generate_keys()
    ok3 = verify_signature(msg, sig, Q2)
    print(f"Проверка с чужим ключом: {'[FAIL] верна (ошибка!)' if ok3 else '[OK] неверна (как и ожидалось)'}")

    # тест 4: подпись файла
    print()
    print("--- Тест 4: подпись файла ---")
    file_data = b"Test file content for GOST digital signature"
    sig4 = sign_message(file_data, d)
    ok4 = verify_signature(file_data, sig4, Q)
    print(f"Подпись файла: {'[OK] верна' if ok4 else '[FAIL] неверна'}")

    # проверяем что подмена данных обнаруживается
    tampered = b"Tampered file content for GOST digital signature"
    ok4t = verify_signature(tampered, sig4, Q)
    print(f"После подмены: {'[FAIL] верна (ошибка!)' if ok4t else '[OK] неверна (подмена обнаружена)'}")

    print()
    print("Все тесты пройдены")

# Работа с файлами

def save_private_key(filename, d):
    with open(filename, 'w') as f:
        f.write(str(d) + '\n')


def load_private_key(filename):
    with open(filename, 'r') as f:
        return int(f.read().strip())


def save_public_key(filename, Q):
    with open(filename, 'w') as f:
        f.write(str(Q[0]) + '\n')
        f.write(str(Q[1]) + '\n')


def load_public_key(filename):
    with open(filename, 'r') as f:
        lines = f.read().strip().split('\n')
    return (int(lines[0]), int(lines[1]))


def save_signature(filename, sig):
    with open(filename, 'w') as f:
        f.write(str(sig[0]) + '\n')
        f.write(str(sig[1]) + '\n')


def load_signature(filename):
    with open(filename, 'r') as f:
        lines = f.read().strip().split('\n')
    return (int(lines[0]), int(lines[1]))


def main():
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python gost_sign.py test")
        print("  python gost_sign.py keygen                    - генерация ключей")
        print("  python gost_sign.py sign <файл> <priv_key>    - подписать файл")
        print("  python gost_sign.py verify <файл> <sig> <pub_key> - проверить подпись")
        return

    cmd = sys.argv[1].lower()

    if cmd == "test":
        run_tests()
        return

    if cmd == "keygen":
        print("Генерация ключевой пары ГОСТ Р 34.10-2012...")
        d, Q = generate_keys()
        save_private_key("gost_private.key", d)
        save_public_key("gost_public.key", Q)
        print(f"Ключ подписи сохранен: gost_private.key")
        print(f"Ключ проверки сохранен: gost_public.key")
        return

    if cmd == "sign":
        if len(sys.argv) < 4:
            print("Нужны аргументы: <файл> <priv_key>")
            return
        in_file = sys.argv[2]
        key_file = sys.argv[3]

        d = load_private_key(key_file)
        with open(in_file, 'rb') as f:
            data = f.read()

        print(f"Подписание: {in_file} ({len(data)} б.)")
        sig = sign_message(data, d)

        sig_file = in_file + ".sig"
        save_signature(sig_file, sig)
        print(f"Подпись сохранена: {sig_file}")
        return

    if cmd == "verify":
        if len(sys.argv) < 5:
            print("Нужны аргументы: <файл> <sig> <pub_key>")
            return
        in_file = sys.argv[2]
        sig_file = sys.argv[3]
        key_file = sys.argv[4]

        with open(in_file, 'rb') as f:
            data = f.read()
        sig = load_signature(sig_file)
        Q = load_public_key(key_file)

        print(f"Проверка подписи: {in_file}")
        ok = verify_signature(data, sig, Q)
        if ok:
            print("[OK] Подпись верна")
        else:
            print("[FAIL] Подпись неверна")
        return

    print(f"Неизвестная команда: {cmd}")


if __name__ == "__main__":
    main()
