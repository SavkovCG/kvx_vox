#!/usr/bin/env python3
"""
CLI to convert SLAB6 .kvx to MagicaVoxel .vox
"""
import argparse
import struct
import array
import os


MAGICAVOXEL_VOX_FILE_VERSION = 150


def kvx_to_vox(kvx_filename, vox_filename):
    """
    Self-explanatory
    :param kvx_filename: Path to .kvx file to convert from
    :param vox_filename: Path to .vox file to convert to
    :return: None, raises exceptions
    """
    p_file = open(kvx_filename, 'rb')
    head_format = "L3L3L"
    head_size = struct.calcsize(head_format)
    numbytes, xsiz, ysiz, zsiz, _, _, _ = struct.unpack(head_format, p_file.read(head_size))
    # TO DO: Resolve xyz for pivot point
    xoffset = array.array('L')
    xoffset.fromfile(p_file, xsiz + 1)
    xyoffset = []
    for i in range(xsiz):
        xy_line = array.array('H')
        xy_line.fromfile(p_file, ysiz + 1)
        xyoffset.append(xy_line)
    rawslabdata = array.array('B')
    rawslabdata.fromfile(p_file, numbytes-24-(xsiz+1)*4-xsiz*(ysiz+1)*2)
    # Sanity check
    assert xoffset[0] == (xsiz + 1) * 4 + xsiz * (ysiz + 1) * 2
    ground_zero = xoffset[0]
    p_file.seek(-256*3, os.SEEK_END)
    vga_pal = array.array('B')
    vga_pal.fromfile(p_file, 256*3)

    p_file.close()

    p_file = open(vox_filename, 'wb')
    p_file.write(b'VOX ')
    p_file.write(struct.pack('L', MAGICAVOXEL_VOX_FILE_VERSION))

    vox_size_chunk = b'SIZE' + struct.pack('5L', 12, 0, xsiz, ysiz, zsiz)
    num_voxels = 0
    xyzi = array.array('B')
    z_range = set()
    for x in range(xsiz):
        for y in range(ysiz):
            b_ptr = xoffset[x] + xyoffset[x][y] - ground_zero
            e_ptr = xoffset[x] + xyoffset[x][y + 1] - ground_zero
            assert e_ptr >= b_ptr
            slabs = rawslabdata[b_ptr:e_ptr]
            if slabs:
                while slabs:
                    ztop, height, _ = slabs[:3]
                    # Cullinfo is ignored
                    slabs = slabs[3:]
                    voxels = slabs[:height]
                    slabs = slabs[height:]
                    assert len(voxels) == height
                    for dz, i in enumerate(voxels):
                        xyzi.append(x)
                        xyzi.append(y)
                        z_range.add(zsiz-(ztop+dz))
                        xyzi.append(zsiz-(ztop+dz))
                        xyzi.append(i)
                        num_voxels += 1
    xyzi_size = (num_voxels*4 + 4)
    p_file.write(b'MAIN' + struct.pack('2L', 0, xyzi_size + 12 + 12 + 12 + 12 + 1024))
    p_file.write(vox_size_chunk)
    p_file.write(b'XYZI' + struct.pack('3L', xyzi_size, 0, num_voxels))
    xyzi.tofile(p_file)
    p_file.write(b'RGBA' + struct.pack('2L', 1024, 0))
    for i in range(256):
        r = int(vga_pal[i * 3] * 255 / 63)
        g = int(vga_pal[i * 3 + 1] * 255 / 63)
        b = int(vga_pal[i * 3 + 2] * 255 / 63)
        a = 255
        p_file.write(struct.pack('4B', r, g, b, a))
    p_file.close()


def main():
    """
    CLI Entry point
    :return:
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('source', help='Source .KVX file')
    parser.add_argument('target', help='Target .VOX file')
    args = parser.parse_args()
    kvx_to_vox(args.source, args.target)


if __name__ == '__main__':
    main()
