import sys,struct,os
import tk5psp_crypt,tk5psp_dec
from ModelMagic.fileRW import *

def u32(file):
    return struct.unpack("<I", file.read(4))[0]
def s16(file):
    return struct.unpack("<h", file.read(2))[0]
def u16(file):
    return struct.unpack("<H", file.read(2))[0]
def u8(file):
    return struct.unpack("B", file.read(1))[0]


def compute_word_sum_fast(data: bytes | bytearray, size_bytes: int) -> int:
    if size_bytes < 0:
        word_count = (size_bytes + 3) >> 2
    else:
        word_count = size_bytes >> 2

    if word_count <= 0:
        return 0

    num_words = min(word_count, len(data) // 4)
    byte_len = num_words * 4
    words = memoryview(data)[:byte_len].cast("I")
    acc = sum(words) & 0xFFFFFFFF

    return (acc - 0x100000000 if acc >= 0x80000000 else acc)&0xFFFFFFFF

TABLESTART = 0x0027B5B0
CHECKSTART = 0x0027E838
TABLECOUNT = 1571

class LUT(object):
    def __init__(self):
        self.offset = 0
        self.size = 0
    def read(self,f:FRead):
        self.offset = (f.u32())*0x800
        self.size = f.u32()

f = open(sys.argv[1],'rb')
def unarchive(f:FRead,fbin:FRead,outDir):
    unarchived = {}
    f.seek(TABLESTART)
    lookups = []
    for x in range(TABLECOUNT):
        cur = LUT()
        cur.read(f)
        lookups.append(cur)
    checksums = []
    f.seek(CHECKSTART)
    for x in range(TABLECOUNT):
        checksums.append(f.u32())
    for indx,x in enumerate(lookups):
        if(x.size != 0xFFFFFFFF):
            fbin.seek(x.offset)
            os.makedirs(outDir, exist_ok=True)
            fil = open(outDir + str("%04i" % (indx)) + ".bin",'wb')
           
            dataOG = fbin.read(x.size)
            if(compute_word_sum_fast(dataOG,x.size) == checksums[indx]):
                fil.write(dataOG)
                #unarchived[str(str("%04i" % (indx)) + ".bin")] = dataOG
                print("leMatch at %04i"%indx)
            else:
                buf = bytearray(dataOG)
                tk5psp_crypt.decrypt_sector_data_fast(buf,indx,x.size)
                if(compute_word_sum_fast(buf,x.size) == checksums[indx]):
                    fil.write(buf)
                    print("leDecriptMatch at %04i"%indx)
                else:
                    print("WeFailed %04i"%indx)
    return unarchived
