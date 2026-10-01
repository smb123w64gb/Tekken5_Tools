import struct
from collections import defaultdict
#Yoinking the system2x6 game unpacker, primarly the sc3 one.

def unpack_sc3game(src):
    src_pos = 0
    dst = bytearray()

    while True:
        flags = src[src_pos]
        src_pos += 1

        if flags == 0:
            break

        while flags > 1:
            if flags & 1:
                dst.append(src[src_pos])
                src_pos += 1
            else:
                token = (src[src_pos] << 8) | src[src_pos + 1]
                src_pos += 2
                offset = token & 0x7FF
                if offset == 0:
                    offset = 0x800
                length = (token >> 11) & 0x1F
                if length == 0:
                    length = 0x20
                pos = len(dst) - offset
                if pos < 0:
                    raise Exception(
                        f"invalid backref offset={offset} length={length} dstlen={len(dst)}"
                    )
                for _ in range(length):
                    dst.append(dst[pos])
                    pos += 1
            flags >>= 1

    return bytes(dst)

def find_match(data, pos, index):

    if pos + 3 > len(data):
        return None

    key = bytes(data[pos:pos + 3])

    candidates = index.get(key)
    if not candidates:
        return None

    best_len = 0
    best_off = 0

    for candidate in reversed(candidates):

        offset = pos - candidate

        if offset > 2048:
            break

        length = 3

        while (
            length < 32
            and pos + length < len(data)
            and data[candidate + length] == data[pos + length]
        ):
            length += 1

        if length > best_len:
            best_len = length
            best_off = offset

            if length == 32:
                break

    if best_len < 3:
        return None

    return best_off, best_len


def pack_sc3game(data):
    data = memoryview(data)
    index = defaultdict(list)
    out = bytearray()
    pos = 0
    while pos < len(data):
        print(f"\r  {pos / len(data) * 100:.1f}%", end="")
        ops = []
        while len(ops) < 7 and pos < len(data):
            match = find_match(data, pos, index)
            if match:
                offset, length = match
                assert 1 <= offset <= 2048
                assert 3 <= length <= 32
                ops.append(("ref", offset, length))
                advance = length
            else:
                ops.append(("lit", data[pos]))
                advance = 1

            for i in range(advance):
                p = pos + i
                if p + 3 <= len(data):
                    key = bytes(data[p:p + 3])
                    index[key].append(p)
            pos += advance

        flags = 1 << len(ops)
        for i, op in enumerate(ops):
            if op[0] == "lit":
                flags |= (1 << i)

        out.append(flags & 0xFF)

        for op in ops:
            if op[0] == "lit":
                out.append(op[1])
            else:
                _, offset, length = op
                if offset == 2048:
                    off_field = 0
                else:
                    off_field = offset
                if length == 32:
                    len_field = 0
                else:
                    len_field = length
                token = (len_field << 11) | off_field
                out.append((token >> 8) & 0xFF)
                out.append(token & 0xFF)
    out.append(0)
    return bytes(out)

'''f = open(sys.argv[1],'rb')
o = open(sys.argv[1]+".dec",'wb')
o.write(unpack_sc3game(f.read()))'''