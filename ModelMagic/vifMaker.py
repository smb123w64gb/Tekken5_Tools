from fileRW import *
from typing import Tuple, List

class Vertex(object):
    def __init__(self, 
                 pos: Tuple[float, float, float], 
                 norm: Tuple[float, float, float] = (0.0, 1.0, 0.0),
                 color: Tuple[int, int, int, int] = (128, 128, 128, 255),
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


class TriStrip(object):
    def __init__(self, val: int = 0):
        self.base = val & 0xFF
        self.flag = (val >> 16) & 0xFF
        self.parity = self.flag & 1
        self.enable = (self.flag >> 1) & 1
        self.trim = self.flag >> 2

    @classmethod
    def from_params(cls, vert_index: int, trim: int = 0, parity: int = 0, divisor: int = 5):
        inst = cls()
        inst.parity = parity & 1
        inst.enable = 1
        inst.trim = trim
        inst.flag = (trim << 2) | (inst.enable << 1) | inst.parity
        inst.base = 1 + (vert_index - inst.parity) * divisor
        return inst

    def get_start_vertex(self, divisor: int = 5) -> int:
        return max(0, self.base - 1) // divisor + self.parity

    def to_u32(self) -> int:
        return (0x70 << 24) | (self.flag << 16) | (0x80 << 8) | (self.base & 0xFF)

    def write(self, f: FWrite):
        f.u32(self.to_u32())


class VIFerator(object):
    def __init__(self):
        self.verts: List[Vertex] = []
        self.triStrips: List[TriStrip] = []
        self.divisor = 5
        self.globalFlags = 0x91

    def get_faces(self) -> List[Tuple[int, int, int]]:
        vert_count = len(self.verts)
        if vert_count < 3:
            return []

        if not self.triStrips:
            faces = []
            for i in range(vert_count - 2):
                faces.append((i, i + 1, i + 2) if i % 2 == 0 else (i, i + 2, i + 1))
            return faces

        M = len(self.triStrips)
        positions = [s.get_start_vertex(self.divisor) for s in self.triStrips]
        all_faces = []

        for k in range(M):
            start = positions[k]
            end = positions[k + 1] if (k + 1 < M) else vert_count
            limit_range = (end - 1) if (k + 1 < M) else (end - 2)

            strip_faces = []
            for i in range(start, limit_range):
                if i % 2 == 0:
                    strip_faces.append((i, i + 1, i + 2))
                else:
                    strip_faces.append((i, i + 2, i + 1))

            if k + 1 < M:
                b = self.triStrips[k + 1].trim
                if b > 0:
                    strip_faces = strip_faces[:-b] if b < len(strip_faces) else []

            all_faces.extend(strip_faces)

        return all_faces

    def read_vif(self, f: FRead):
        size = f.u16()
        self.globalFlags = f.u16()
        f.u32()  # STCYCL: WL=1, CL=5
        f.u32()  # UNPACK S-32: vertCount header
        vertCount = f.u32()
        f.u32()  # STMASK
        f.u32()  # Mask: 0x80000000

        # Positions (V3-32)
        f.u16(); f.u8(); f.u8()
        self.verts = [Vertex(pos=tuple(f.f32_3())) for _ in range(vertCount)]

        # Normals (V3-32)
        f.u16(); f.u8(); f.u8()
        for x in range(vertCount):
            self.verts[x].norm = tuple(f.f32_3())

        # Colors (Optional V4-8)
        if self.globalFlags == 0x93:
            f.u16(); f.u8(); f.u8()
            for x in range(vertCount):
                self.verts[x].color = tuple(f.u8_4())

        # UVs (V2-32)
        f.u16(); f.u8(); f.u8()
        for x in range(vertCount):
            self.verts[x].uv = tuple(f.f32_2())

        # Weights (V4-32)
        f.u32()  # STCYCL
        f.u16(); f.u8(); f.u8()
        for x in range(vertCount):
            self.verts[x].weight = tuple(f.f32_4())

        # Bone Indices (V4-8)
        f.u16(); f.u8(); f.u8()
        for x in range(vertCount):
            self.verts[x].bone_ids = tuple(f.u8_4())

        # Tristrip face markers
        f.u32()  # STCYCL
        f.u32()  # STMASK
        f.u32()  # Mask: 0x7FFFFFFF

        curStripVal = f.u32()
        while curStripVal not in (0, 0x01000101, 0x20):
            # Check for 0x70 masked unpack command
            if (curStripVal >> 24) == 0x70:
                self.triStrips.append(TriStrip(curStripVal))
            curStripVal = f.u32()

        # Seek to 16-byte boundary alignment
        while f.tell() % 16 != 0:
            f.seek(4, 1)

    def write_vif(self, f: FWrite):#Untested
        start_pos = f.tell()
        vert_count = len(self.verts)

        f.u16(0)                 # Size placeholder
        f.u16(self.globalFlags)  # 0x91 (no color) or 0x93 (color)

        # 1. Header: STCYCL + VertCount UNPACK
        f.u32(0x01000105)        # STCYCL: CL=5, WL=1
        f.u32(0x60018000)        # UNPACK S-32: count=1, vu_addr=0
        f.u32(vert_count)
        f.u32(0x20000000)        # STMASK
        f.u32(0x80000000)        # Mask value

        # 2. Vertex Positions: UNPACK V3-32 (0x78) at VU address 1
        f.u16(0x8001)
        f.u8(vert_count)
        f.u8(0x78)
        for v in self.verts:
            f.f32_3(v.pos)

        # 3. Normals: UNPACK V3-32 (0x68) at VU address 2
        f.u16(0x8002)
        f.u8(vert_count)
        f.u8(0x68)
        for v in self.verts:
            f.f32_3(v.norm)

        # 4. Colors (if 0x93): UNPACK V4-8 (0x6E)
        if self.globalFlags == 0x93:
            f.u16(0x8003)
            f.u8(vert_count)
            f.u8(0x6E)
            for v in self.verts:
                col = v.color if v.color else (128, 128, 128, 255)
                f.u8_4(col)

        # 5. UV Coordinates: UNPACK V2-32 (0x64) at VU address 4
        f.u16(0x8004)
        f.u8(vert_count)
        f.u8(0x64)
        for v in self.verts:
            f.f32_2(v.uv)

        f.u32(0x01000102)        # STCYCL

        # 6. Weights: UNPACK V4-32 (0x6C) at VU address 0xCC (204)
        f.u16(0x80CC)
        f.u8(vert_count)
        f.u8(0x6C)
        for v in self.verts:
            f.f32_4(v.weight)

        # 7. Bone Indices: UNPACK V4-8 (0x6E) at VU address 0xCD (205)
        f.u16(0xC0CD)
        f.u8(vert_count)
        f.u8(0x6E)
        for v in self.verts:
            f.u8_4(v.bone_ids)

        # 8. Face Markers: STMASK + TriStrip calls
        f.u32(0x00010005)        # STCYCL
        f.u32(0x20000000)        # STMASK
        f.u32(0x7FFFFFFF)        # Mask value

        # Ayo if nothin is stripped, i guess big strip
        strips_to_write = self.triStrips
        if not strips_to_write and vert_count >= 3:
            strips_to_write = [TriStrip.from_params(vert_index=0, trim=0, parity=0)]

        for s in strips_to_write:
            s.write(f)

        # Pad packet to 16-byte boundary
        while (f.tell() - start_pos) % 16 != 0:
            f.u8(0)
        
        # Packet Terminators
        f.u32(0x01000101)        # STCYCL 1, 1

        f.u32(0x20000000)        # STMASK
        f.u32(0x00000000)        # Mask 0

        f.u32(0x14000000)        # FLUSHA

        end_pos = f.tell()
        packet_size = end_pos - start_pos
        f.seek(start_pos)
        f.u16(packet_size)
        f.seek(end_pos)