import sys
import os
import glob
import struct
import shutil
from io import BytesIO
import pycdlib

import decNLZ1
import package_fmt_pkg
import FileTableGetPS2
import tk5psp_crypt

TABLESTART = 0x0027B5B0
CHECKSTART = 0x0027E838
TABLECOUNT = 1571
SECTOR_SIZE = 0x800

TekkenCodeFile = '/TK5DATA3.BIN;1'
TekkenDataFile = '/TK5DATA1.BIN;1'


def compute_word_sum(data: bytes | bytearray, size_bytes: int) -> int:
    return FileTableGetPS2.compute_word_sum_fast(data, size_bytes)


def parse_toc_and_checksums(code_buf: bytearray):
    lookups = []
    for i in range(TABLECOUNT):
        entry_offset = TABLESTART + (i * 8)
        sector, size = struct.unpack_from("<II", code_buf, entry_offset)
        lookups.append({"index": i, "sector": sector, "offset": sector * SECTOR_SIZE, "size": size})

    checksums = []
    for i in range(TABLECOUNT):
        entry_offset = CHECKSTART + (i * 4)
        csum = struct.unpack_from("<I", code_buf, entry_offset)[0]
        checksums.append(csum)

    return lookups, checksums


def patch_toc_and_checksum(code_buf: bytearray, index: int, sector: int, size: int, checksum: int):
    table_entry_offset = TABLESTART + (index * 8)
    struct.pack_into("<II", code_buf, table_entry_offset, sector, size)

    check_entry_offset = CHECKSTART + (index * 4)
    struct.pack_into("<I", code_buf, check_entry_offset, checksum)


def get_disc_extents_and_limits(iso: pycdlib.PyCdlib):
    """
    Finds exact byte offsets on the disc for all root files without modifying metadata.
    """
    all_files = []
    for child in iso.list_children(iso_path='/'):
        if not child.is_dir():
            ident = child.file_identifier().decode('latin-1')
            extents = iso.get_file_byte_extents(iso_path=f"/{ident}")
            if extents:
                all_files.append((extents[0][0], extents[0][1], f"/{ident}"))

    all_files.sort(key=lambda x: x[0])

    code_info = None
    data_info = None

    for i, (offset, length, name) in enumerate(all_files):
        if name.upper() == TekkenCodeFile.upper():
            limit = (all_files[i + 1][0] - offset) if (i + 1 < len(all_files)) else length
            code_info = {"offset": offset, "len": length, "limit": limit}
        elif name.upper() == TekkenDataFile.upper():
            limit = (all_files[i + 1][0] - offset) if (i + 1 < len(all_files)) else length
            data_info = {"offset": offset, "len": length, "limit": limit}

    return code_info, data_info


def inject_file(index: int, new_data: bytes, blob: bytearray, code_buf: bytearray,
                lookups: list, checksums: list, max_blob_capacity: int):
    orig = lookups[index]
    orig_size = orig["size"]
    orig_offset = orig["offset"]
    orig_sector = orig["sector"]
    orig_csum = checksums[index]

    new_size = len(new_data)
    new_csum = compute_word_sum(new_data, new_size)

    # 1. Determine if original asset was encrypted
    was_encrypted = False
    if orig_size != 0xFFFFFFFF and orig_size > 0:
        orig_slice = blob[orig_offset : orig_offset + orig_size]
        if compute_word_sum(orig_slice, orig_size) != orig_csum:
            test_buf = bytearray(orig_slice)
            pad_needed = ((orig_size + 3) & ~3) - len(test_buf)
            if pad_needed > 0:
                test_buf.extend(b'\x00' * pad_needed)

            tk5psp_crypt.decrypt_sector_data_fast(test_buf, index, orig_size)
            if compute_word_sum(test_buf, orig_size) == orig_csum:
                was_encrypted = True

    # 2. Encrypt if necessary
    payload = bytearray(new_data)
    align_pad = ((new_size + 3) & ~3) - new_size
    if align_pad > 0:
        payload.extend(b'\x00' * align_pad)

    if was_encrypted:
        print(f"[{index:04d}] Encrypting replacement asset (seed={index})...")
        tk5psp_crypt.decrypt_sector_data_fast(payload, index, new_size)
    else:
        print(f"[{index:04d}] Asset is unencrypted.")

    # 3. Sector placement inside TK5DATA1.BIN
    orig_sectors = ((orig_size + 0x7FF) // 0x800) if orig_size != 0xFFFFFFFF else 0
    orig_capacity = orig_sectors * SECTOR_SIZE

    new_sectors = (new_size + 0x7FF) // 0x800
    delta_sectors = new_sectors - orig_sectors

    if orig_size != 0xFFFFFFFF and delta_sectors <= 0:
        # In-place overwrite
        target_offset = orig_offset
        target_sector = orig_sector
        blob[target_offset : target_offset + len(payload)] = payload

        # Zero out remaining slack in sector
        remainder = orig_capacity - len(payload)
        if remainder > 0:
            blob[target_offset + len(payload) : target_offset + orig_capacity] = b'\x00' * remainder

        patch_toc_and_checksum(code_buf, index, target_sector, new_size, new_csum)
        lookups[index]["size"] = new_size
        checksums[index] = new_csum
        print(f"[{index:04d}] In-place overwritten @ sector {target_sector} (size {new_size}/{orig_capacity} bytes)")

    else:
        # Shift following files
        delta_bytes = delta_sectors * SECTOR_SIZE
        new_total_len = len(blob) + delta_bytes

        if new_total_len > max_blob_capacity:
            raise OverflowError(
                f"Injection failed on file {index:04d}: Expanding by {delta_sectors} sector(s) exceeds "
                f"physical disc allocation ({max_blob_capacity} bytes)! Use --export-bins to rebuild."
            )

        print(f"[{index:04d}] Expanding by {delta_sectors} sector(s) (+{delta_bytes} bytes). Shifting following files...")

        shift_start = orig_offset + orig_capacity
        blob[shift_start:shift_start] = b'\x00' * delta_bytes

        target_offset = orig_offset
        target_sector = orig_sector
        new_capacity = new_sectors * SECTOR_SIZE
        blob[target_offset : target_offset + len(payload)] = payload

        remainder = new_capacity - len(payload)
        if remainder > 0:
            blob[target_offset + len(payload) : target_offset + new_capacity] = b'\x00' * remainder

        patch_toc_and_checksum(code_buf, index, target_sector, new_size, new_csum)
        lookups[index]["size"] = new_size
        checksums[index] = new_csum

        shifted_count = 0
        for entry in lookups:
            if entry["index"] != index and entry["size"] != 0xFFFFFFFF and entry["offset"] >= shift_start:
                entry["sector"] += delta_sectors
                entry["offset"] += delta_bytes
                struct.pack_into("<I", code_buf, TABLESTART + (entry["index"] * 8), entry["sector"])
                shifted_count += 1

        print(f"[{index:04d}] Shifted {shifted_count} following file(s) in TOC by +{delta_sectors} sectors.")


def main():
    if len(sys.argv) < 4:
        print("Usage:")
        print("  Batch folder inject: python TK5AssetInjectPS2.py <clean_in_iso> <mod_folder> <out_iso>")
        print("  Single file inject:  python TK5AssetInjectPS2.py <clean_in_iso> <file_idx> <new_file> <out_iso>")
        print("  Export BINs only:    python TK5AssetInjectPS2.py <clean_in_iso> <mod_folder> --export-bins")
        sys.exit(1)

    in_iso_path = sys.argv[1]
    export_bins_only = ("--export-bins" in sys.argv)

    files_to_inject = {}
    if len(sys.argv) == 4 and not export_bins_only:
        mod_dir = sys.argv[2]
        out_iso_path = sys.argv[3]
        for fpath in glob.glob(os.path.join(mod_dir, "*.bin")):
            base = os.path.splitext(os.path.basename(fpath))[0]
            if base.isdigit():
                files_to_inject[int(base)] = fpath
    elif export_bins_only:
        mod_dir = sys.argv[2]
        out_iso_path = None
        for fpath in glob.glob(os.path.join(mod_dir, "*.bin")):
            base = os.path.splitext(os.path.basename(fpath))[0]
            if base.isdigit():
                files_to_inject[int(base)] = fpath
    else:
        file_idx = int(sys.argv[2])
        new_file_path = sys.argv[3]
        out_iso_path = sys.argv[4]
        files_to_inject[file_idx] = new_file_path

    if not files_to_inject:
        print("No valid .bin files found to inject.")
        sys.exit(1)

    # 1. Inspect original disc layout using PyCdlib solely as a reader
    print(f"Inspecting clean original ISO: {in_iso_path}")
    iso = pycdlib.PyCdlib()
    iso.open(in_iso_path)
    code_info, data_info = get_disc_extents_and_limits(iso)
    iso.close()

    print(f"  TK5DATA3.BIN @ offset 0x{code_info['offset']:08X} (len: {code_info['len']})")
    print(f"  TK5DATA1.BIN @ offset 0x{data_info['offset']:08X} (len: {data_info['len']}, max: {data_info['limit']})")

    # 2. Read archives directly via file offsets
    print("Reading archives from disc...")
    with open(in_iso_path, "rb") as f:
        f.seek(code_info["offset"])
        code_raw = f.read(code_info["len"])

        f.seek(data_info["offset"])
        blob = bytearray(f.read(data_info["len"]))

    code_stream = BytesIO(code_raw)
    code_archive = package_fmt_pkg.PKG()
    code_archive.read(code_stream)
    code_stream.close()

    print("Decompressing subfile 5 (Game Code)...")
    code_decompressed = bytearray(decNLZ1.unpack_sc3game(code_archive.files[5]))
    lookups, checksums = parse_toc_and_checksums(code_decompressed)

    # 3. Inject modifications
    for idx, path in sorted(files_to_inject.items()):
        if idx >= TABLECOUNT:
            print(f"Skipping index {idx}: exceeds TABLECOUNT ({TABLECOUNT})")
            continue
        with open(path, "rb") as f:
            data = f.read()
        print(f"Injecting index {idx:04d} from '{path}'...")
        inject_file(idx, data, blob, code_decompressed, lookups, checksums, data_info["limit"])

    # 4. Recompress subfile 5
    print("\nRecompressing subfile 5 (decNLZ1.pack_sc3game)...")
    code_archive.files[5] = decNLZ1.pack_sc3game(code_decompressed)
    print()

    print("Repacking TK5DATA3.BIN...")
    new_code_pkg_io = BytesIO()
    code_archive.write(new_code_pkg_io)
    new_code_pkg_bytes = new_code_pkg_io.getvalue()
    new_code_pkg_io.close()

    if len(new_code_pkg_bytes) > code_info["len"]:
        print(f"Error: Recompressed TK5DATA3.BIN ({len(new_code_pkg_bytes)}) exceeds original size ({code_info['len']})!")
        sys.exit(1)

    # Pad TK5DATA3.BIN to original length
    if len(new_code_pkg_bytes) < code_info["len"]:
        new_code_pkg_bytes += b'\x00' * (code_info["len"] - len(new_code_pkg_bytes))

    # Pad TK5DATA1.BIN if it shrunk
    if len(blob) < data_info["len"]:
        blob.extend(b'\x00' * (data_info["len"] - len(blob)))

    # 5. Output handling
    if export_bins_only:
        print("Writing standalone archives to disk (--export-bins mode)...")
        with open("TK5DATA3_MODDED.BIN", "wb") as f:
            f.write(new_code_pkg_bytes)
        with open("TK5DATA1_MODDED.BIN", "wb") as f:
            f.write(blob)
        print("Saved TK5DATA3_MODDED.BIN and TK5DATA1_MODDED.BIN successfully!")
        return

    # Clone clean original ISO to target destination
    if os.path.abspath(in_iso_path) != os.path.abspath(out_iso_path):
        print(f"Cloning clean original ISO to: {out_iso_path}...")
        shutil.copyfile(in_iso_path, out_iso_path)

    # 6. Direct binary patch (Zero PyCdlib metadata rewriting)
    print(f"Writing data sectors directly to: {out_iso_path}...")
    with open(out_iso_path, "r+b") as f:
        # Patch TK5DATA3.BIN
        f.seek(code_info["offset"])
        f.write(new_code_pkg_bytes)

        # Patch TK5DATA1.BIN
        f.seek(data_info["offset"])
        f.write(blob)

    print("Injection complete! Disc headers, SYSTEM.CNF, and Sony UDF structures are 100% preserved.")


if __name__ == "__main__":
    main()