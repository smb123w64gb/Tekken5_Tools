from fileRW import *
from typing import Tuple 

class Vertex(object):
    def __init__(self, 
                 pos: Tuple[float, float, float], 
                 norm: Tuple[float, float, float] = (0.0, 1.0, 0.0),
                 color: Tuple[int, int, int, int] = (None, None, None, None),
                 uv: Tuple[float, float] = (0.0, 0.0),
                 weight: Tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.0),
                 bone_ids: Tuple[int, int, int, int] = (0, 0, 0, 0)):
        self.pos = pos
        self.norm = norm
        self.color = color
        self.uv = uv
        self.weight = weight
        self.bone_ids = bone_ids

    def __eq__(self, other):
        return (self.pos == other.pos and self.norm == other.norm and 
                self.uv == other.uv and self.weight == other.weight and 
                self.bone_ids == other.bone_ids)
class TriStrip(object):#Prob oh so wrong
    def __init__(self,val = 1):
        self.base = val & 0xFF
        self.stripCount = (val>>16) & 0xFF
    def write(self,f:FWrite):
        f.u8(self.base)
        f.u8(0x80)
        f.u8(self.stripCount)
        f.u8(0x70)

class VIFerator(object):
    def __init__(self):
        self.verts = []
        self.triStrips = []
    def read_vif(self,f:FRead):
        size = f.u16()
        globalFlags = f.u16()
        f.u32() #STCYCL CMD,00,WL,CL
        f.u32() #UNPACK S-32 CMD,COUNT,ADDRESS(Short)
        vertCount = f.u32()
        f.u32()#STMASK
        f.u32()#Masking 0x80000000
        verBufBase = f.u16()
        f.u8()#CountAgain
        vertUnpackType = f.u8()
        for x in range(vertCount):
            newVert = Vertex(pos = tuple(f.f32_3()))
            self.verts.append(newVert)
        normBufBase = f.u16()
        f.u8()#CountAgain
        normUnpackType = f.u8()
        for x in range(vertCount):
            self.verts[x].norm = tuple(f.f32_3())
        if(globalFlags == 0x93):
            uvBufBase = f.u16()
            f.u8()#CountAgain
            uvUnpackType = f.u8()
            for x in range(vertCount):
                self.verts[x].color = tuple(f.u8_4())
        uvBufBase = f.u16()
        f.u8()#CountAgain
        uvUnpackType = f.u8()
        for x in range(vertCount):
            self.verts[x].uv = tuple(f.f32_2())
        
        f.u32() #STCYCL CMD,00,WL,CL
        wgtBufBase = f.u16()
        f.u8()#CountAgain
        wgtUnpackType = f.u8()
        for x in range(vertCount):
            self.verts[x].weight = tuple(f.f32_4())
        bixBufBase = f.u16()
        f.u8()#CountAgain
        bixUnpackType = f.u8()
        for x in range(vertCount):
            self.verts[x].bone_ids = tuple(f.u8_4())

        f.u32()#STCYCL CMD,00,WL,CL
        f.u32()#STMASK
        f.u32()#Masking 0x7FFFFFFF
        curStipVal = f.u32()
        while(curStipVal != 0 and curStipVal != 0x1000101):
            self.triStrips.append(TriStrip(curStipVal))
            curStipVal = f.u32()
        '''
        Yeah its smth else.
        '''
        if(curStipVal == 0x1000101):
            f.u32()
        else:
            while f.tell() % 16 != 0:f.seek(4,1)
            f.u64()
        f.u64()


    def write_vif(self,f:FWrite):
        f.u16(0)#Placeholder
        f.u16(0x91)
        f.u32(0x01000105) #STCYCL CMD,00,WL,,CL
        f.u32(0x60018000) #UNPACK S-32 CMD,COUNT,ADDRESS(Short)
        f.u32()