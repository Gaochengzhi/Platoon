from PIL import Image
import matplotlib.pyplot as plt
import os
before_path = "../res/before_idv_lane_pos_idv_speed"
in_path = "../res/in_idv_lane_pos_idv_speed"
out_path = "../res/out_idv_lane_pos_idv_speed"
images = []

vol = 6500
volist = [4500,5500,6500]
caccmpr = "00"
cacclist = ["02","04","06"]
caccsize = 4
truck="02"

# for truck in ["02", "04", "06"]:
for caccmpr in cacclist:
# for vol in volist:
    # Open the before image
    if caccmpr == "00":
        caccsize = 0
    else:
        caccsize = 5
    
    before_file = os.path.join(before_path, f"|{vol}|{caccmpr}|{caccsize}|{truck}|fcdbeforecsv.png")
    before_img = Image.open(before_file)
    
    # Open the in image
    in_file = os.path.join(in_path, f"|{vol}|{caccmpr}|{caccsize}|{truck}|fcdincsv.png")
    in_img = Image.open(in_file)
    
    # Open the out image
    out_file = os.path.join(out_path, f"|{vol}|{caccmpr}|{caccsize}|{truck}|fcdoutcsv.png")
    out_img = Image.open(out_file)
    
    # Add the images to the list
    images.append(before_img)
    images.append(in_img)
    images.append(out_img)

# max_width = max(i.width for i in images)
# max_height = max(i.height for i in images)

# Create a figure with 3x3 subplots and a title
max_width = max(i.width for i in images)-30
max_height = max(i.height for i in images)-35

# Create a new blank image to contain the grid
grid_img = Image.new('RGB', (max_width * 3, max_height * 3))

# Loop through the images and paste them onto the grid
for i in range(3):
    for j in range(3):
        idx = i * 3 + j
        if idx >= len(images):
            break
        img = images[idx]
        x_offset = j * max_width-10
        y_offset = i * max_height-10
        grid_img.paste(img, (x_offset, y_offset))

# Save the final image
grid_img.save(f"../res/out/compare{vol}{caccsize}{caccmpr}speed_positon.png")
