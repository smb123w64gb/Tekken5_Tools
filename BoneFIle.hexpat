struct Vec3 {
    float x, y, z;
};

struct EulerAnglesRad {
    float pitch; // Rx (radians)
    float yaw;   // Ry (radians)
    float roll;  // Rz (radians)
};

struct SkeletonHeader {
    u16 formatVersion;          // 50 (0x32)
    u16 totalBoneCount;         // Core 111 + Dynamic Extra
    float characterScale;
    u32 parentIndicesOffset;
    u32 localPositionsOffset;
    u32 localRotationsOffset;
    u32 dynamicBonesOffset;
    u64 padd;
};

struct DynamicBoneTable {
    u32 count;
    u32 boneRemapIndices[count];
};

struct NamcoSkeleton {
    SkeletonHeader hdr;
    s32 parentIndices[hdr.totalBoneCount] @ hdr.parentIndicesOffset;
    Vec3 localPositions[hdr.totalBoneCount] @ hdr.localPositionsOffset;
    EulerAnglesRad localRotations[hdr.totalBoneCount] @ hdr.localRotationsOffset;
    DynamicBoneTable dynamicBones @ hdr.dynamicBonesOffset;
};

NamcoSkeleton skeleton @ 0x00;