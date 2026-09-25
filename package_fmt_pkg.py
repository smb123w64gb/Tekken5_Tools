import struct,sys,os

def u8(file):
    return struct.unpack("B", file.read(1))[0]
def u16(file):
    return struct.unpack("<H", file.read(2))[0]
def u32(file):
    return struct.unpack("<I", file.read(4))[0]

def w32(file,val):
    file.write(struct.pack("<I", val))
def rR(f,o,l):#Read n Return, Takes file,offset,size returns data
    c = f.tell()
    f.seek(o)
    d = f.read(l)
    f.seek(c)
    return d

def magicCheck(magic):
    match magic:
        case 843925844:
            return ".tm2"
        case 1414678595:
            return ".chrtk4"
        case 542066755:
            return ".cho"
        case 1346655566:
            return ".nud"
        case 860902478:
            return ".nut"
        case 860898382:
            return ".nud"
        case _:
            return ".bin"

class PKG(object):
    def __init__(self):
        self.files = []
    def read(self,f):
        count = u32(f)
        if(count<30):
            print(count)
            mappings = []
            for _a in range(count):
                mappings.append([u32(f),u32(f)])
            for a in mappings:
                f.seek(a[0])
                self.files.append(f.read(a[1]))
    def write(self,f):
        w32(f,len(self.files))
        offsets = []
        base = (len(self.files)*8) + 4
        if(base % 0x10):
            base += 0x10-(base%0x10)
        for x in self.files:
            w32(f,base)
            w32(f,len(x))
            offsets.append(base)
            base+=len(x)
            if(base % 0x10):
                base += 0x10-(base%0x10)
        for indx,d in enumerate(self.files):
            f.seek(offsets[indx])
            f.write(d)

