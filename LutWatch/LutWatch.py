
import ctypes
import os
import msvcrt
import platform
import time
import random
from ctypes import c_void_p, c_uint, c_ulong, c_char, c_bool, c_uint64


# we get the correct library extension per os
lib="libpine_c"
cur_os = platform.system()
if(cur_os == "Linux"):
    lib="libpine_c.so"
elif(cur_os == "Windows"):
    lib="pine_c.dll"
elif(cur_os == "Darwin"):
    lib="libpine_c.dylib"


# we load the library, this will require it to be in the same folder
# refer to bindings/c to build the library.
print("readin dll")
libipc = ctypes.CDLL(os.path.join(os.path.dirname(os.path.abspath(__file__)),lib),winmode=0)

libipc.pine_pcsx2_new.restype = c_void_p

libipc.pine_read.argtypes = [c_void_p, c_uint, c_char, c_bool]
libipc.pine_read.restype = c_ulong

libipc.pine_write.argtypes = [c_void_p, c_uint, c_uint64 , c_char, c_bool]
libipc.pine_write.restype = None

libipc.pine_get_error.argtypes = [c_void_p]
libipc.pine_get_error.restype = c_uint

libipc.pine_pcsx2_delete.argtypes = [c_void_p]
libipc.pine_pcsx2_delete.restype = None

ipc = libipc.pine_pcsx2_new()


ValidIDs = [0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x0B,0x0C,0x0D,0x0E,0x0F,0x11,0x12,0x14,0x15,0x16,0x17,0x1A,0x22,0x23,0x24,0x26,0x27,0x28,0x29,0x2A,0x30,0x31,0x32,0x41,0x42,0x43,0x44,0x45,0x46,0x47,0x48,0x4A,0x4B,0x4C,0x4D,0x4E,0x4F,0x51,0x54]
Address = c_uint(0x4BA062)
AddressUS1 = c_uint(0x4B4862)

'''
0 = Read u8
1 = Read u16
2 = Read u32
3 = Read u64

4 = Write u8
5 = Write u16
6 = Write u32
7 = Write u64
'''
def bytes_to_mib(bytes_value):
    mib_value = bytes_value / (1024 * 1024)
    return mib_value

class MemBuff(object):
    def __init__(self,memoryoffset):
        self.MEM_OFFSET = memoryoffset
        self.used = -1
        self.index = 0
        self.name = ''
        self.offset_head = 0
        self.offset_end = 0
        self.space_alloted = 0
        self.space_used = 0
        self.space_left = 0

    def __str__(self,basic = False):
        strpit = ''
        if(self.used==0xFFFF):
            return 'NO DATA\n'
        strpit += str("Used: %i\t Index: %02i\n"% (self.used,self.index))
        strpit += str("name: %s\n"% self.name)
        strpit += str("Offset Range %s - %s\n"% (hex(self.offset_head),hex(self.offset_end)))
        if(basic):
            strpit += str("Data Used %02.02f MiB / %02.02f MiB\n"% (bytes_to_mib(self.space_used),bytes_to_mib(self.space_alloted)))
            strpit += str("Avalable %02.02f MiB\n"% bytes_to_mib(self.space_left))
        else:
            strpit += str("Data Used %s / %s\n"% (hex(self.space_used),hex(self.space_alloted)))
            strpit += str("Avalable %s\n"% hex(self.space_left))
        return strpit
    def read(self,pinIN):
        offset = self.MEM_OFFSET
        self.used = libipc.pine_read(pinIN, offset, c_char(1), False)
        offset+=2
        self.index = libipc.pine_read(pinIN, offset, c_char(1), False)
        offset+=2
        strlen = 32
        result = ""
        tmpChar = bytes(c_char(libipc.pine_read(pinIN, offset, c_char(0), False)))
        strlen -=1
        offset+=1
        while ord(tmpChar) != 0 and strlen > 0:
            result += tmpChar.decode("shift_jis")
            tmpChar = bytes(c_char(libipc.pine_read(pinIN, offset, c_char(0), False)))
            strlen -=1
            offset+=1
        self.name = result
        offset += strlen
        self.offset_head = libipc.pine_read(pinIN, offset, c_char(2), False)
        offset += 4
        self.offset_end = libipc.pine_read(pinIN, offset, c_char(2), False)
        offset += 4
        self.space_alloted = libipc.pine_read(pinIN, offset, c_char(2), False)
        offset += 4
        self.space_used = libipc.pine_read(pinIN, offset, c_char(2), False)
        offset += 4
        self.space_left = libipc.pine_read(pinIN, offset, c_char(2), False)
        offset += 4


curLUT = 0
prevLUT = 0
writeAddr = 0
LookupValueOffset = 0x16359C
LookupWriteOffset = 0x1635A4
os.system('cls')
print("--- LutWatch  --- Press C to clear")
while(1):
    if msvcrt.kbhit():
        key = msvcrt.getch().decode('utf-8').lower()
        if key == 'c':
            os.system('cls')
            print("--- LutWatch  --- Press C to clear")
    curLUT = libipc.pine_read(ipc, LookupValueOffset, c_char(2), False)
    if(prevLUT != curLUT):
        writeAddr = libipc.pine_read(ipc, LookupWriteOffset, c_char(2), False)
        print("Loading: %04i.bin @ %08x" % (curLUT,writeAddr))
        prevLUT = curLUT


