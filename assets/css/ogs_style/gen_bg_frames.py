from PIL import Image
import matplotlib.pyplot as plt
from tqdm import tqdm
import numpy as np

EPOCHS = 100

# 2160 x 3840 px corresponds to 108 x 192 square of size 20 x 20
# ogs bg color is (26, 26, 26)
# ogs text color is (220, 220, 220)


def main():

    gol = np.zeros((108, 192)).astype(bool)

    gol[24 : 27, 95 : 98] = [
        [False, True, True],
        [True, True, False],
        [False, True, False],
    ]

    for epoch in tqdm(range(1, EPOCHS + 1), total=EPOCHS):
        gol2jpg(gol, f"bg_frames/{epoch}.jpg")

        gol_step(gol)


def gol_step(gol):


    n = np.empty_like(gol).astype(int)

    for y in range(n.shape[0]):
        for x in range(n.shape[1]):

            n[y, x] = sum(get_ns(y, x, gol))


    for y, d in enumerate(gol):
        for x, l in enumerate(d):

            if n[y, x] < 2 or n[y, x] > 3:
                gol[y, x] = False
            elif n[y, x] == 3:
                gol[y, x] = True


def gol2jpg(gol, fp):

    im_data = np.full((2160, 3840, 3), 26)

    for y, d in enumerate(gol):
        for x, l in enumerate(d):
            if l:
                im_data[y * 20 : (y + 1) * 20, x * 20 : (x + 1) * 20] = (220, 220, 220)

    im = Image.fromarray(im_data.astype("uint8")).convert("RGB")
    im.save(fp)


def get_ns(y, x, gol):

    n = []

    if y > 0:
        n += [gol[y-1, x]]
        if x > 0:
            n += [gol[y-1, x-1]]
        if x < gol.shape[1] - 1:
            n += [gol[y-1, x+1]]

    if y < gol.shape[0] - 1:
        n += [gol[y+1, x]]

        if x > 0:
            n += [gol[y+1, x-1]]
        if x < gol.shape[1] - 1:
            n += [gol[y+1, x+1]]


    if x > 0:
        n += [gol[y, x-1]]

    if x < gol.shape[1] - 1:
        n += [gol[y, x+1]]

    return n

if __name__ == "__main__":
    main()