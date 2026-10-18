"""Trace the red pixels of the original RGBA PNG into native KiCad polygons.

Uses only Python's standard library and pcbnew; retains the outline and eye,
while excluding the dark background and faint glow. No generated replacement.
"""
import struct
import zlib


def rgba_png(path):
    data = path.read_bytes()
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    offset, compressed = 8, bytearray()
    while offset < len(data):
        length = struct.unpack('>I', data[offset:offset+4])[0]
        kind = data[offset+4:offset+8]
        chunk = data[offset+8:offset+8+length]
        if kind == b'IHDR':
            w, h, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB',chunk)
            assert (depth,color,compression,filtering,interlace) == (8,6,0,0,0)
        elif kind == b'IDAT':
            compressed.extend(chunk)
        offset += length+12
    raw = zlib.decompress(compressed)
    stride, rows, previous, offset = w*4, [], bytearray(w*4), 0
    for _ in range(h):
        method = raw[offset]; offset += 1
        row = bytearray(raw[offset:offset+stride]); offset += stride
        for x in range(stride):
            a = row[x-4] if x >= 4 else 0
            b = previous[x]
            c = previous[x-4] if x >= 4 else 0
            if method == 0:
                predictor = 0
            elif method == 1:
                predictor = a
            elif method == 2:
                predictor = b
            elif method == 3:
                predictor = (a+b)//2
            elif method == 4:
                guess = a+b-c
                distances = (abs(guess-a),abs(guess-b),abs(guess-c))
                predictor = (a,b,c)[distances.index(min(distances))]
            else:
                raise ValueError('Unknown PNG filter')
            row[x] = (row[x]+predictor) & 255
        rows.append(row); previous = row
    return w,h,rows


def bird_mask(path, pcbnew, vector, center, width=12.0):
    w,h,rows = rgba_png(path)
    pixels = set()
    for y,row in enumerate(rows):
        for x in range(w):
            r,g,b,a = row[4*x:4*x+4]
            if a >= 128 and r >= 128 and r > 2*g and r > 2*b:
                pixels.add((x,y))
    assert pixels, 'No bird artwork found'
    x0,x1 = min(x for x,y in pixels),max(x for x,y in pixels)+1
    y0,y1 = min(y for x,y in pixels),max(y for x,y in pixels)+1
    scale = width/(x1-x0)
    left,top = center[0]-width/2,center[1]-(y1-y0)*scale/2
    result = pcbnew.SHAPE_POLY_SET()
    for y in range(y0,y1):
        row_poly = pcbnew.SHAPE_POLY_SET()
        x=x0
        while x < x1:
            if (x,y) not in pixels:
                x += 1; continue
            start=x
            while x < x1 and (x,y) in pixels:
                x += 1
            row_poly.NewOutline()
            for px,py in [(start,y),(x,y),(x,y+1),(start,y+1)]:
                v=vector((left+(px-x0)*scale,top+(py-y0)*scale))
                row_poly.Append(v.x,v.y)
        if row_poly.OutlineCount():
            result.BooleanAdd(row_poly)
    print(f'Traced original birb: {width:.2f} x {(y1-y0)*scale:.2f} mm')
    return result
