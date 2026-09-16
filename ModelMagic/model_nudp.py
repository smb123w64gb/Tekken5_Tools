from fileRW import *

class VIFBlob(object):#This will do fornow
    def __init__(self):
        self.size = 0
        self.data = bytearray()
    def read(self,f:FRead):
        self.size = f.u16()
        f.seek(-2,1)
        self.data = f.read(self.size)
        return self.size
    def __eq__(self, other):
        if not isinstance(other, VIFBlob):
            return NotImplemented
        return self.data == other.data
    def __hash__(self):
        return hash((bytes(self.data)))

class NUDP(object):
    def __init__(self):
        self.header = self.Header()
        self.MeshGroups:set[NUDP.MeshGroup] = []
    def read(self,f:FRead):
        self.header.read(f)
        for x in range(self.header.meshCount):
            curGroup = NUDP.MeshGroup()
            curGroup.read(f)
            self.MeshGroups.append(curGroup)
    def update(self):
        base = 0x20
        
        for x in self.MeshGroups:
            base += 0x18
            for y in x.subMeshs:
                base += 0x28
        #MaterialUpdate
        materials = {}
        for x in self.MeshGroups:
            for y in x.subMeshs:
                matoffset = 0
                for offset,mat in materials.items():
                    if (mat == y.material):
                        matoffset = offset
                        break
                if(matoffset == 0):
                    materials[base] = y.material
                    base+=0x30
        #Dispatch Update
        dispatches = {}
        for x in self.MeshGroups:
            for y in x.subMeshs:
                disoffset = 0
                for offset,disp in dispatches.items():
                    if(disp == y.dispatch):
                        disoffset = offset
                        break
                if(disoffset == 0):
                    dispatches[base] = y.dispatch
                    base+=0x30
        #VifBlob update
        vifs = {}
        for x in self.MeshGroups:
            for y in x.subMeshs:
                vifsize = 0
                #making asumtions here
                vifoffset = 0
                for offset,vif in vifs.items():
                    if(vif[0] == y.vifDMA[0]):
                        vifoffset = offset
                        for z in vif:
                            vifsize+=z.size
                        break
                if(vifoffset == 0):
                    vifs[base] = y.vifDMA
                    for z in y.vifDMA:
                        vifsize+=z.size
                        base+=z.size
                vifsize = vifsize >> 4
                y.packetQWC = vifsize
        self.header.filesize = base
        #Now we write for real
        return materials,dispatches,vifs
    def write(self,f:FWrite):
        materials,dispatches,vifs = self.update()
        self.header.write(f)
        for x in self.MeshGroups:
            x.write(f,materials,dispatches,vifs)
        for off,x in materials.items():
            x.write(f)
        for off,x in dispatches.items():
            x.write(f)
        for off,x in vifs.items():
            for y in x:
                f.write(y.data)
    class Header(object):
        def __init__(self):
            self.magic = b'NUDP'
            self.filesize = 0
            self.verFlags = 0
            self.meshCount = 0
            self.headerSize = 0
            self.modelBounds = [0.0]*4
        def read(self,f : FRead):
            self.magic = f.read(4)
            self.filesize = f.u32()
            self.verFlags = f.u16()
            self.meshCount = f.u16()
            self.headerSize = f.u32()#Padding
            self.modelBounds = f.f32_4()
        def write(self,f:FWrite):
            f.write(b'NUDP')
            f.u32(self.filesize)
            f.u16(self.verFlags)
            f.u16(self.meshCount)
            f.u32(0)
            f.f32_4(self.modelBounds)
    class MeshGroup(object):
        def __init__(self):
            self.meshType = 0
            self.unk1 = 0
            self.categoryMask = 0
            self.subMeshCount = 0
            self.boneNodeID = 0
            self.meshBounds = [0.0]*4
            self.subMeshs:set[NUDP.MeshGroup.SubMesh] = []
        def read(self,f:FRead):
            self.meshType = f.u8()
            self.unk1 = f.u8()
            self.categoryMask = f.u16()
            self.subMeshCount = f.u16()
            self.boneNodeID = f.u16()
            self.meshBounds = f.f32_4()
            for x in range(self.subMeshCount):
                curMesh = self.SubMesh()
                curMesh.read(f)
                self.subMeshs.append(curMesh)
        def write(self,f:FRead,Mats,Disp,Vifs):
            f.u8(self.meshType)
            f.u8(self.unk1)
            f.u16(self.categoryMask)
            self.subMeshCount = len(self.subMeshs)
            f.u16(self.subMeshCount)
            f.u16(self.boneNodeID)
            f.f32_4(self.meshBounds)
            for x in self.subMeshs:
                x.write(f,Mats,Disp,Vifs)


        class SubMesh(object):
            def __init__(self):
                self.subQueueLayer = 0
                self.renderQueue = 0
                self.vuProgramID = 0

                self.dispatch = NUDP.MeshGroup.SubMesh.Dispatch()
                self.material = NUDP.MeshGroup.SubMesh.Material()

                self.gsStateFlags = 0
                self.vifDMA:set[VIFBlob] = []
                self.packetQWC = 0
                self.passType = 0
                self.reserved0 = 0
                self.reserved1 = 0
                self.bonePalette = [255]*10
            def read(self,f:FRead):
                self.subQueueLayer = f.u8()
                self.renderQueue = f.u8()
                self.vuProgramID = f.u16()
                dispatchoff = f.u32()
                materialoff = f.u32()
                self.gsStateFlags = f.u32()
                vifDMAoff = f.u32()
                self.packetQWC = f.u16()
                self.passType = f.u16()
                self.reserved0 = f.u32()
                self.reserved1 = f.u16()
                self.bonePalette = [f.u8() for _x in range(10)]
                #offset Stuff
                ret = f.tell()
                f.seek(dispatchoff)
                self.dispatch.read(f)
                f.seek(materialoff)
                self.material.read(f)
                f.seek(vifDMAoff)
                curQWSize = self.packetQWC * 16
                while(curQWSize>0):
                    curVif = VIFBlob()
                    curQWSize -= curVif.read(f)
                    self.vifDMA.append(curVif)
                f.seek(ret)
            def write(self,f:FWrite,Mats,Disp,Vifs):
                f.u8(self.subQueueLayer)
                f.u8(self.renderQueue)
                f.u16(self.vuProgramID)

                dispatchoff = 0
                for offset, dispatching in Disp.items():
                    if dispatching == self.dispatch:
                        dispatchoff = offset
                f.u32(dispatchoff)

                materialoff = 0
                for offset, material in Mats.items():
                    if material == self.material:
                        materialoff = offset
                f.u32(materialoff)

                f.u32(self.gsStateFlags)

                vifDMAoff = 0
                for offset, vif in Vifs.items():
                    if vif[0] == self.vifDMA[0]:
                        vifDMAoff = offset
                f.u32(vifDMAoff)

                f.u16(self.packetQWC)
                f.u16(self.passType)
                f.u32(self.reserved0)
                f.u16(self.reserved1)
                for x in self.bonePalette:
                    f.u8(x)
            class Dispatch(object):
                def __init__(self):
                    self.runtimeBase = 0
                    self.meshDataOffset = 0
                    self.materialType = 0
                    self.renderFlags = 0
                    self.vuBufferOffset = 0
                    self.depthBias = 1.0
                    self.unk = 0
                def read(self,f:FRead):
                    self.runtimeBase = f.u64()
                    self.meshDataOffset = f.u64()
                    self.materialType = f.u64()
                    self.renderFlags = f.u64()
                    self.vuBufferOffset = f.u64()
                    self.depthBias = f.f32()
                    self.unk = f.u32()
                def write(self,f:FWrite):
                    f.u64(self.runtimeBase)
                    f.u64(self.meshDataOffset)
                    f.u64(self.materialType)
                    f.u64(self.renderFlags)
                    f.u64(self.vuBufferOffset)
                    f.f32(self.depthBias)
                    f.u32(self.unk)
                def __eq__(self, other):
                    if not isinstance(other, NUDP.MeshGroup.SubMesh.Dispatch):
                        return NotImplemented
                    return (
                        self.runtimeBase == other.runtimeBase and
                        self.meshDataOffset == other.meshDataOffset and
                        self.materialType == other.materialType and
                        self.renderFlags == other.renderFlags and
                        self.vuBufferOffset == other.vuBufferOffset and
                        self.depthBias == other.depthBias and
                        self.unk == other.unk
                    )
                def __hash__(self):
                    return hash((
                        self.runtimeBase,
                        self.meshDataOffset,
                        self.materialType,
                        self.renderFlags,
                        self.vuBufferOffset,
                        self.depthBias,
                        self.unk
                    ))
            class Material(object):
                def __init__(self):
                    self.flags = 0
                    self.textureIndex = 0
                    self.alpha = 1.0
                    self.ambient = [1.0]*3
                    self.diffuse = [1.0]*3
                    self.specular = [1.0]*3
                def read(self,f:FRead):
                    self.flags = f.u32()
                    self.textureIndex = f.u32()
                    self.alpha = f.f32()
                    self.ambient = f.f32_3()
                    self.diffuse = f.f32_3()
                    self.specular = f.f32_3()
                def write(self,f:FWrite):
                    f.u32(self.flags)
                    f.u32(self.textureIndex)
                    f.f32(self.alpha)
                    f.f32_3(self.ambient)
                    f.f32_3(self.diffuse)
                    f.f32_3(self.specular)
                def __eq__(self, other):
                    if not isinstance(other, NUDP.MeshGroup.SubMesh.Material):
                        return NotImplemented
                    return (
                        self.flags == other.flags and
                        self.textureIndex == other.textureIndex and
                        self.alpha == other.alpha and
                        self.ambient == other.ambient and
                        self.diffuse == other.diffuse and
                        self.specular == other.specular
                    )
                def __hash__(self):
                    return hash((
                        self.flags,
                        self.textureIndex,
                        self.alpha,
                        tuple(self.ambient),
                        tuple(self.diffuse),
                        tuple(self.specular)
                    ))
    
