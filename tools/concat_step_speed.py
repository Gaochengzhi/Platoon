from PIL import Image
import os

in_path = "../res/in_step_idv_speed"

vols = [4500, 5500, 8500]
trucks = ['02', '04', '06']

# vols = "6500"
# trucks = "04"
caccmpr = ["02","04","06"]
caccsize = ['3','4','6']

# Create a blank image to paste the other images into
img_size = Image.open(os.path.join(in_path, f"|{vols[0]}|{caccmpr[0]}|{caccsize[0]}|{trucks[0]}|fcdincsv.png")).size
concatenated_image = Image.new('RGB', (img_size[0] * 3, img_size[1] * 3))

for i, caccmp in enumerate(caccmpr):
    for j, caccsiz in enumerate(caccsize):
        img = Image.open(os.path.join(in_path, f"|{'6500'}|{caccmpr[i]}|{caccsize[j]}|{'02'}|fcdincsv.png"))
        concatenated_image.paste(img, (img_size[0] * j, img_size[1] * i))

out_path = f"../res/out/step_speed{vols}{trucks}{caccmpr}{caccsize}.png"
concatenated_image.save(out_path)

