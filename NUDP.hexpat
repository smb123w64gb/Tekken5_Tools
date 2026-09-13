#pragma endian little

struct vec3 {
    float x, y, z;
};

struct BoundingSphere {
    float x, y, z;
    float radius;
};

struct Material {
    u32 flags;
    u32 textureIndex;
    float alpha;
    vec3 ambient;
    vec3 diffuse;
    vec3 specular;
};

struct DispatchHeader {
    u64 runtimeBase;
    u64 meshDataOffset;
    u64 materialType;
    u64 renderFlags;
    u64 vuBufferOffset;
    float depthBias;
     padding[4];
};

struct VifPacket {
    u16 packetSizeBytes;
    u16 containerFlags;
    u8 rawData[packetSizeBytes - 4];
};

struct SubMesh {
    u8  subQueueLayer;      // was low byte of drawOrder (e.g. 0x08, 0x1F)
    u8  renderQueue;        // was high byte of drawOrder (0x20 = Opaque, 0x21 = Alpha/Decal)
    u16 vuProgramID;        // Microcode program ID (0x1040)?
    u32 dispatchOffset;
    DispatchHeader dispHDR @ dispatchOffset;
    
    u32 materialOffset;
    Material mat @ materialOffset;
    
    u32 gsStateFlags;       // Packed GS registers (TEST_1, ALPHA_1)
    u32 vifOffset;
    
    
    u16 packetQWC;          // Size in Quadwords (QWC * 16 = packetSizeBytes)
    
    VifPacket vif[while($<vifOffset+(packetQWC*16))] @ vifOffset;
    u16 passType;           // 1 = Opaque single-pass, 2 = Base Pass, 3 = Detail overlay pass
    u32 reserved0;
    u16 reserved1;
    u8  bonePalette[10];    // Maps VIF matrix offsets (multiples of 7) to skeleton bones
};

struct MeshGroup {
    u8  meshType;           // 0x00 = Static, 0x20 = Multi-bone Skinned, 0x24 = Rigid Limb
    u8  unk1;
    u16 categoryMask;       // Visibility / Equipment group mask
    u16 subMeshCount;
    u16 boneNodeID;         // Parent bone / node ID
    BoundingSphere bounds;
    SubMesh subMeshes[subMeshCount];
};

struct NUDPHeader {
    char magic[4];
    u32  fileSize;
    u16  versionFlags;
    u16  meshCount;
    u32  headerSize;
    BoundingSphere modelBounds;
};

struct NUDP {
    NUDPHeader header;
    MeshGroup meshes[header.meshCount];
};

NUDP model @ 0x00;