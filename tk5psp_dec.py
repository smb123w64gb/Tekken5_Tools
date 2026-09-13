def decompress_blob(data: bytes | bytearray) -> bytearray:
    """
    Decompresses an LZSS-compressed byte stream.
    
    :param data: Compressed input bytes
    :return: Decompressed bytearray
    """
    src = memoryview(data)
    src_len = len(src)
    src_idx = 0
    
    out = bytearray()
    
    if src_idx >= src_len:
        return out

    flag = src[src_idx]
    
    while flag != 0:
        src_idx += 1
        if flag < 2:
            if src_idx < src_len:
                flag = src[src_idx]
            else:
                break
        else:
            while flag > 1:
                bit = flag & 1
                flag >>= 1
                
                if bit == 0:
                    # Match / Back-reference (2 bytes)
                    b1 = src[src_idx]
                    src_idx += 1
                    b2 = src[src_idx]
                    
                    val = (b1 << 8) | b2
                    offset = val & 0x7FF
                    if offset == 0:
                        offset = 0x800
                        
                    length = val >> 11
                    if length == 0:
                        length = 0x20
                    
                    # Copy 'length' bytes from 'offset' positions back.
                    # Negative indexing (out[-offset]) automatically handles 
                    # overlapping repeat copies (RLE).
                    for _ in range(length):
                        out.append(out[-offset])
                else:
                    # Literal byte (1 byte)
                    out.append(src[src_idx])
                
                src_idx += 1
                
            if src_idx < src_len:
                flag = src[src_idx]
            else:
                break

    return out