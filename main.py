import struct
from sboxes import T1, T2, T3, T4

MASK = 0xFFFFFFFFFFFFFFFF

def _mul(a, m):
    return (a * m) & MASK

def _add(a, b):
    return (a + b) & MASK

def _sub(a, b):
    return (a - b) & MASK


def tiger_round(a, b, c, x, mul):
    c ^= x

    a = _sub(a,
        T1[c & 0xFF] ^
        T2[(c >> 16) & 0xFF] ^
        T3[(c >> 32) & 0xFF] ^
        T4[(c >> 48) & 0xFF]
    )

    b = _add(b,
        T4[(c >> 8) & 0xFF] ^
        T3[(c >> 24) & 0xFF] ^
        T2[(c >> 40) & 0xFF] ^
        T1[(c >> 56) & 0xFF]
    )

    b = _mul(b, mul)

    return a & MASK, b & MASK, c & MASK


def tiger_pass(a, b, c, x, mul):
    for i in range(8):
        a, b, c = tiger_round(a, b, c, x[i], mul)
        a, b, c = b, c, a
    return a, b, c


def key_schedule(x):
    x = list(x)

    x[0] = (x[0] - (x[7] ^ 0xA5A5A5A5A5A5A5A5)) & MASK
    x[1] ^= x[0]
    x[2] = (x[2] + x[1]) & MASK
    x[3] = (x[3] - (x[2] ^ (((~x[1] & MASK) << 19) & MASK))) & MASK
    x[4] ^= x[3]
    x[5] = (x[5] + x[4]) & MASK
    x[6] = (x[6] - (x[5] ^ (((~x[4] & MASK) >> 23) & MASK))) & MASK
    x[7] ^= x[6]

    x[0] = (x[0] + x[7]) & MASK
    x[1] = (x[1] - (x[0] ^ (((~x[7] & MASK) << 19) & MASK))) & MASK
    x[2] ^= x[1]
    x[3] = (x[3] + x[2]) & MASK
    x[4] = (x[4] - (x[3] ^ (((~x[2] & MASK) >> 23) & MASK))) & MASK
    x[5] ^= x[4]
    x[6] = (x[6] + x[5]) & MASK
    x[7] = (x[7] - (x[6] ^ 0x0123456789ABCDEF)) & MASK

    return x


def pad(data):
    length = len(data)

    # добавляем 0x01
    data = data + b'\x01'

    # добиваем нулями до 56 байт (mod 64)
    pad_len = (56 - len(data) % 64) % 64
    data += b'\x00' * pad_len

    # добавляем длину (в битах)
    data += struct.pack('<Q', length * 8)

    return data


def tiger(data):
    a = 0x0123456789ABCDEF
    b = 0xFEDCBA9876543210
    c = 0xF096A5B4C3B2E187

    data = pad(data)

    for i in range(0, len(data), 64):
        block = data[i:i+64]
        x = list(struct.unpack('<8Q', block))

        aa, bb, cc = a, b, c

        a, b, c = tiger_pass(a, b, c, x, 5)
        x = key_schedule(x)
        a, b, c = tiger_pass(a, b, c, x, 7)
        x = key_schedule(x)
        a, b, c = tiger_pass(a, b, c, x, 9)

        a ^= aa
        b = (b - bb) & MASK
        c = (c + cc) & MASK

    return struct.pack('<3Q', a, b, c)


# ---------------------------
# SELF TEST
# ---------------------------

def self_test():
    tests = {
        b"abc": "2aab1484e8c158f2bfb8c5ff41b57a525129131c957b5f93",
        b"Tiger": "dd00230799f5009fec6debc838bb6a27df2b9d6f110c7937",
    }

    all_ok = True

    for data, expected in tests.items():
        result = tiger(data).hex()
        ok = result == expected

        print(f"Input: {data}")
        print(f"My:   {result}")
        print(f"Ref:  {expected}")
        print("OK" if ok else "ERROR")
        print("-" * 40)

        if not ok:
            all_ok = False

    print("RESULT:", "ALL TESTS PASSED " if all_ok else "SOME TESTS FAILED ")

if __name__ == "__main__":
    print("=== TEST ===")
    self_test()

    print("\n")
    s = input("Введите строку: ")
    print(tiger(s.encode()).hex())