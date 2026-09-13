import sys,struct,os
import tk5psp_crypt,tk5psp_dec

def u32(file):
    return struct.unpack("<I", file.read(4))[0]
def s16(file):
    return struct.unpack("<h", file.read(2))[0]
def u16(file):
    return struct.unpack("<H", file.read(2))[0]
def u8(file):
    return struct.unpack("B", file.read(1))[0]

TABLESTART = 0x0027B5B0
TABLECOUNT = 1571

class LUT(object):
    def __init__(self):
        self.offset = 0
        self.size = 0
    def read(self,f):
        self.offset = (u32(f))*0x800
        self.size = u32(f)

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
    if(x.size != 0xFFFFFFFF):
        if(indx >29 and indx < 72):
            fbin.seek(x.offset)
            fil = open(outDir + str("%04i" % (indx)) + ".bin",'wb')
            dataOG = fbin.read(x.size)
            fil.write(dataOG)
        else:
            fbin.seek(x.offset)
            fil = open(outDir + str("%04i" % (indx)) + ".bin",'wb')
            dataOG = fbin.read(x.size)
            data = tk5psp_crypt.decrypt_blob(indx,dataOG,x.size)
            fil.write(data)
    

#print(hex(total))
