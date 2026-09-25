import sys
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

f = open(sys.argv[1],'rb')
o = open(sys.argv[1]+".dec",'wb')
o.write(unpack_sc3game(f.read()))