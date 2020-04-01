import math


def rgb2hsv(r,g,b):
    maxim = maxim = max(max(r, g), b)
    minim = min(min(r, g), b)
    dif = maxim - minim
    h = 0
    s = dif / maxim if maxim != 0 else 0
    v = maxim
    if s != 0:
        rc = (maxim - r) / dif
        gc = (maxim - g) / dif
        bc = (maxim - b) / dif

        if r == maxim:
            h = bc - gc

        elif g == maxim:
            h = 2 + rc - bc

        elif b == maxim:
            h = 4 + gc - rc

        if h < 0:
            h += 6
    return(h, s, v)


def hsv2rgb(h, s, v):
    while h >= 6:
        h -= 6
    while h < 0:
        h += 6

    j = int(math.floor(h))
    f = h - j
    p = v * (1 - s)
    q = v * (1 - (s * f))
    t = v * (1 - (s * (1 - f)))

    if j == 0:
        r = v
        g = t
        b = p
    elif j == 1:
        r = q
        g = v
        b = p
    elif j == 2:
        r = p
        g = v
        b = t
    elif j == 3:
        r = p
        g = q
        b = v
    elif j == 4:
        r = t
        g = p
        b = v
    elif j == 5:
        r = v
        g = p
        b = q
    else:
        r = v
        g = t
        b = p
    return(r, g, b)

def rgb_adjust_saturation(factor, r,g,b):
    h,s,v = rgb2hsv(r,g,b)
    s *= factor
    r,g,b = hsv2rgb(h, s, v)
    return(r,g,b)