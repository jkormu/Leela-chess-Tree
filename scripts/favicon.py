from PIL import Image, ImageDraw
import PIL
Z = 1280#640

def circle(img, x,y,r, color):
    x = int(round(Z*x))
    y = int(round(Z*y))
    r = int(round(Z*r))
    print(x, y, r)
    bounding_box = [(x-r, y-r), (x+r, y+r)]
    print(bounding_box)
    img.ellipse(bounding_box, fill=color, outline=None, width=1)
    return(img)

def line(img, x0, y0, x1, y1, width, color):
    x0 = int(round(Z*x0))
    y0 = int(round(Z*y0))
    x1 = int(round(Z*x1))
    y1 = int(round(Z*y1))
    xy = [(x0, y0), (x1, y1)]
    width = int(round(Z*width))
    img.line(xy, fill=color, width=width, joint=None)
    return(img)

def rectangle(img, x0, y0, x1, y1, color):
    x0 = int(round(x0*Z))
    y0 = int(round(y0*Z))
    x1 = int(round(x1*Z))
    y1 = int(round(y1*Z))
    box = [(x0, y0), (x1, y1)]
    img.rectangle(box, fill =color)
    return(img)

def polygon(img, xy, color):
    xy = [int(round(p*Z)) for p in xy]
    img.polygon(xy, fill = color)
    return(img)

DY = 0
DX = 0

UX = 1/8
DUX = 3*UX

UY = 1/4
DUY = 2*UY

X0 = UX + DX
X1 = UX + DUX + DX
X2 = UX + 2*DUX + DX

Y0 = UY + DY
Y1 = UY + DUY + DY

newimg = Image.new("RGBA", (Z, Z))
img = ImageDraw.Draw(newimg)

LINE_W = 0.08
LINE_C = "#000000"
R = 0.125
ODD_C = "#1f77b4"
EVEN_C = "#ff7f0e"
PV_LINE_C = "#000000"


a = 1.25
up_y = UY/4
down_y = 1 - UY/4
left_cut = 0
right_cut = 0



img = line(img, X1, Y0, X0, Y1, LINE_W, LINE_C) 
img = line(img, X1, Y0, X1, Y1, LINE_W, LINE_C) 
img = line(img, X1, Y0, X2, Y1, LINE_W, LINE_C)


img = circle(img, X1, Y0, R, "#FF0000")
img = circle(img, X0, Y1, R, EVEN_C)

img = circle(img, X1, Y1, R, ODD_C)
img = circle(img, X2, Y1, R, EVEN_C)
resample = PIL.Image.LANCZOS
favicon_sizes = [16, 32, 128, 640]

for size in favicon_sizes:
    img_resized = newimg.resize((size, size), resample=resample)
    img_resized.save(f'favicon_{size}x{size}.png')

newimg.show()
