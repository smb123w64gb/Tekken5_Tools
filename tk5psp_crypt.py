import struct

def decrypt_sector_data_fast(data: bytearray, seed: int, size: int) -> None:
    if size <= 0:
        return

    seed &= 0xFFFFFFFF
    keystream = [0] * 512
    key = seed
    for i in range(512):
        keystream[i] = key
        key = (key * 5 + 3) & 0xFFFFFFFF
    keystream_bytes = struct.pack("<512I", *keystream)

    num_blocks = size >> 11
    rem_words = ((size & 0x7FF) + 3) >> 2
    ks_int_2048 = int.from_bytes(keystream_bytes, "little")
    offset = 0

    for _ in range(num_blocks):
        chunk = data[offset : offset + 2048]
        data[offset : offset + 2048] = (
            int.from_bytes(chunk, "little") ^ ks_int_2048
        ).to_bytes(2048, "little")
        offset += 2048
    
    if rem_words != 0:
        rem_len = rem_words * 4
        chunk = data[offset : offset + rem_len]
        rem_ks_int = int.from_bytes(keystream_bytes[:rem_len], "little")
        data[offset : offset + rem_len] = (
            int.from_bytes(chunk, "little") ^ rem_ks_int
        ).to_bytes(rem_len, "little")