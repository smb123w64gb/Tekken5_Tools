import sys,struct,os
import tk5psp_crypt,tk5psp_dec
import zlib

def u64(file):
    return struct.unpack(">Q", file.read(8))[0]
def u32(file):
    return struct.unpack(">I", file.read(4))[0]
def s16(file):
    return struct.unpack(">h", file.read(2))[0]
def u16(file):
    return struct.unpack(">H", file.read(2))[0]
def u8(file):
    return struct.unpack("B", file.read(1))[0]

TABLESTART = 0x003B3940
TABLECOUNT = 2297

class LUT(object):
    def __init__(self):
        self.offset = 0
        self.size = 0
        self.crc = 0
        self.unk0 = 0
        self.id = 0
        self.unk1 = 0
    def read(self,f):
        self.offset = (u32(f))*0x800
        self.size = u32(f)
        self.crc = u64(f)
        self.unk0 = u32(f)
        self.id = u32(f)
        self.unk1 = u32(f)
f = open(sys.argv[1],'rb')
f.seek(TABLESTART)
lookups = []
for x in range(TABLECOUNT):
    cur = LUT()
    cur.read(f)
    lookups.append(cur)
f.close()
total = 0
offsets = []
fbin = open(sys.argv[2],'rb')
outDir = str(sys.argv[2]+"_Extract/")
os.makedirs(outDir, exist_ok=True)
for indx,x in enumerate(lookups):
    if(x.size != 0xFFFFFFFF and x.size):
        fbin.seek(x.offset)
        fil = open(outDir + str("%04i_%04x" % (indx,x.id)) + ".bin",'wb')
        dataOG = fbin.read(x.size)
        data = tk5psp_crypt.decrypt_blob(x.id,dataOG,x.size)

        try:
            decData = zlib.decompress(data)
            if(len(decData)<len(data)):
                fil.write(data)
            else:
                fil.write(decData)
        except zlib.error:
            fil.write(data)
    

#print(hex(total))
