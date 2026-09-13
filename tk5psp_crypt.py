import struct

def decrypt_blob(index_key: int, data: bytearray | bytes, file_size: int = None) -> bytearray:
    if file_size is None:
        file_size = len(data)
    
    if file_size <= 0:
        return bytearray(data)

    buf = bytearray(data)
    index_key &= 0xFFFFFFFF

    key = index_key
    keystream_words = []
    for _ in range(512):
        keystream_words.append(key)
        key = (key * 5 + 3) & 0xFFFFFFFF
    
    keystream_bytes = struct.pack('<512I', *keystream_words)


    full_blocks = file_size // 2048
    for b in range(full_blocks):
        offset = b * 2048
        for i in range(2048):
            buf[offset + i] ^= keystream_bytes[i]

    rem_bytes = file_size & 0x7FF
    if rem_bytes > 0:
        offset = full_blocks * 2048
        rem_words = (rem_bytes + 3) >> 2
        rem_len = rem_words * 4
        rem_len = min(rem_len, len(buf) - offset)
        for i in range(rem_len):
            buf[offset + i] ^= keystream_bytes[i]

    return buf