import struct
import io
class FRead(object): #Generic file reader
    def __init__(self,f,big_endian=False):
        self.endian='<'
        if(big_endian):
            self.endian ='>'
        self.file = f
        if not isinstance(f, io.IOBase):
            self.file = io.BytesIO(f)
    def swapEndian(self):
        if(self.endian == '>'):
            self.endian = '<'
        else:
            self.endian = '>'
    def u64(self):
        return struct.unpack(self.endian+'Q', self.file.read(8))[0]
    def u32(self):
        return struct.unpack(self.endian+'I', self.file.read(4))[0]
    def u16(self):
        return struct.unpack(self.endian+'H', self.file.read(2))[0]
    def b16(self):#Sometimes i dont want to endian swap
            return struct.unpack('>H', self.file.read(2))[0]
    def u8(self):
        return struct.unpack(self.endian+'B', self.file.read(1))[0]
    def u8_4(self):
        return struct.unpack(self.endian+'BBBB', self.file.read(4))[0:4]
    def s32(self):
        return struct.unpack(self.endian+'i', self.file.read(4))[0]
    def s16(self):
        return struct.unpack(self.endian+'h', self.file.read(2))[0]
    def s8(self):
        return struct.unpack(self.endian+'b', self.file.read(1))[0]
    def f16(self):
        return struct.unpack(self.endian+'e', self.file.read(2))[0]
    def g16(self):
        val = struct.unpack(self.endian+'h', self.file.read(2))[0]
        val = val/8192
        return val
    def g16_2(self):
        val = [self.g16(),self.g16()]
        return val
    def g16_3(self):
        val = [self.g16(),self.g16(),self.g16()]
        return val
    def u16_3(self):
        val = [self.u16(),self.u16(),self.u16()]
        return val
    def f32(self):
        return struct.unpack(self.endian+'f', self.file.read(4))[0]
    def f32_4(self):
        return struct.unpack(self.endian+'ffff', self.file.read(16))[0:4]
    def f32_3(self):
        return struct.unpack(self.endian+'fff', self.file.read(12))[0:3]
    def f32_2(self):
        return struct.unpack(self.endian+'ff', self.file.read(8))[0:2]
    def seek(self,offset,whence=0):
        self.file.seek(offset,whence)
    def tell(self):
        return self.file.tell()
    def read(self,x):
        return self.file.read(x)
    def getString(self,offset = 0):
        if(offset):
            ret = self.file.tell()
            self.seek(offset)
        result = ""
        tmpChar = self.file.read(1)
        while ord(tmpChar) != 0:
            result += tmpChar.decode("utf-8")
            tmpChar = self.file.read(1)
        if(offset):
            self.seek(ret)
        return result
    def getStringSpecal(self,offset = 0):
        if(offset):
            ret = self.file.tell()
            self.seek(offset)
        result = ""
        tmpChar = chr(self.u8()-0x40)
        while ord(tmpChar) != 0:
            result += tmpChar
            tmpChar = chr(self.u8()-0x40)
        if(offset):
            self.seek(ret)
        return result
class FWrite(object): #Generic file writer
    def __init__(self,f,big_endian=False):
        self.endian='<'
        if(big_endian):
            self.endian ='>'
        self.file = f
    def swapEndian(self):
        if(self.endian == '>'):
            self.endian = '<'
        else:
            self.endian = '>'
    def u64(self,val):
        self.file.write(struct.pack(self.endian+'Q', val))
    def u32(self,val):
        self.file.write(struct.pack(self.endian+'I', val))
    def u16(self,val):
        self.file.write(struct.pack(self.endian+'H', val))
    def u16_3(self,val):
        self.file.write(struct.pack(self.endian+'HHH', val[0],val[1],val[2]))
    def u8(self,val):
        self.file.write(struct.pack(self.endian+'B', val))
    def u8_4(self,val):
        self.file.write(struct.pack(self.endian+'BBBB', val[0],val[1],val[2],val[3]))
    def s32(self,val):
        self.file.write(struct.pack(self.endian+'i', val))
    def s16(self,val):
        self.file.write(struct.pack(self.endian+'h', val))
    def s8(self,val):
        self.file.write(struct.pack(self.endian+'b', val))
    def f16(self,val):
        self.file.write(struct.pack(self.endian+'e', val))
    def f32(self,val):
        self.file.write(struct.pack('f', val))
    def f32_4(self,val):
        self.file.write(struct.pack('ffff',val[0],val[1],val[2],val[3]))
    def f32_3(self,val):
        self.file.write(struct.pack('fff',val[0],val[1],val[2]))
    def f32_2(self,val):
        self.file.write(struct.pack('ff',val[0],val[1]))
    def seek(self,offset,whence=0):
        self.file.seek(offset,whence)
    def tell(self):
        return self.file.tell()
    def write(self,x):
        return self.file.write(x)
    def getString(self,offset = 0):
        if(offset):
            ret = self.file.tell()
            self.seek(offset)
        result = ""
        tmpChar = self.file.read(1)
        while ord(tmpChar) != 0:
            result += tmpChar.decode("utf-8")
            tmpChar = self.file.read(1)
        if(offset):
            self.seek(ret)
        return result