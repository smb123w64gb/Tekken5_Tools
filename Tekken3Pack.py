from ModelMagic.fileRW import *

class LUT(object):
    def __init__(self):
        self.name = ''
        self.data = bytearray()
    def read(self,f:FRead):
        entrySize = f.u32()
        self.name = f.getString()
        while(f.tell()%4):
            f.seek(1,1)
        offset = f.u32()
        size = f.u32()
        ret = f.tell()
        f.seek(offset)
        self.data = f.read(size)
        f.seek(ret)
import sys,os

entrys = []

infile = open(sys.argv[1],'rb')
inread = FRead(infile)

for x in range(inread.u32()):
    lut = LUT()
    lut.read(inread)
    entrys.append(lut)
outDir = str(sys.argv[1]+"_Extract/")
os.makedirs(outDir, exist_ok=True)
for x in entrys:
    fil = open(outDir + x.name,'wb')
    fil.write(x.data)
    fil.close()
