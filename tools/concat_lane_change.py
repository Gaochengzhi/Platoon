from PIL import Image
import matplotlib.pyplot as plt
import os
before_path = "../res/before_idv_lane_pos_lane_index"
in_path = "../res/in_idv_lane_pos_lane_index"
out_path = "../res/out_idv_lane_pos_lane_index"
images = []

vol_values = ["4500", "5500", "6500"]

cacc_mpr ="04"
cacc_size = 4
# Define the list of XX values
# xx_values = ["02", "04", "06"]
xx_values = ["06"]
image_paths = []
for vol in vol_values:
    for xx in xx_values:
        # Generate the before image path
        before_image_path = os.path.join(before_path, f"|vol|{cacc_mpr}|{cacc_size}|{xx}|fcdbeforecsv.png".replace("vol", vol))
        image_paths.append(before_image_path)

        # Generate the in image path
        in_image_path = os.path.join(in_path, f"|{vol}|{cacc_mpr}|{cacc_size}|{xx}|fcdincsv.png")
        image_paths.append(in_image_path)

        # Generate the out image path
        out_image_path = os.path.join(out_path, f"|{vol}|{cacc_mpr}|{cacc_size}|{xx}|fcdoutcsv.png")
        image_paths.append(out_image_path)

# Open the first image to get its size
first_image = Image.open(image_paths[0])
image_width, image_height = first_image.size

# Calculate the output dimensions based on the number of rows and columns
num_rows = len(image_paths) // 3
output_width = image_width * 3
output_height = image_height * num_rows

# Create an empty image object to store the concatenated images
concatenated_image = Image.new('RGB', (output_width, output_height))

# Loop over the image paths and paste each image onto the concatenated image
for i, image_path in enumerate(image_paths):
    image = Image.open(image_path)
    x_offset = (i % 3) * image_width
    y_offset = (i // 3) * image_height
    concatenated_image.paste(image, (x_offset, y_offset))

# Save the concatenated image
# Save the final image
concatenated_image.save(f"../res/out/step_lane{cacc_mpr}#{cacc_size}#{xx_values}.png")
