from PIL import Image
import os

input_folder = "../res/in_/"
output_folder = "../res/out/"
image_files = [f for f in os.listdir(input_folder) if f.endswith(".png")]

# Group images by len
grouped_images = {}
for image_file in image_files:
    len_value = image_file.split('.')[1]
    cacc_value = float(image_file.split('.')[0])

    if len_value not in grouped_images:
        grouped_images[len_value] = []

    grouped_images[len_value].append(input_folder + image_file)

# Sort image groups by len
sorted_groups = sorted(grouped_images.items(), key=lambda x: x[0])
sorted_groups = [(num, sorted(paths, key=lambda x: int(x.split("/")[-1].split(".")[0]))) for num, paths in sorted_groups]
concatenated_groups = []

for i, (len_value, image_group) in enumerate(sorted_groups):
    images = [Image.open(img_path) for img_path in image_group]

    # Find total width and max height
    total_width = sum(img.width for img in images)
    max_height = max(img.height for img in images)

    # Create a new image with the calculated dimensions
    new_image = Image.new('RGB', (total_width, max_height))

    # Paste images side by side
    x_offset = 0
    for img in images:
        new_image.paste(img, (x_offset, 0))
        x_offset += (img.width-140)

    concatenated_groups.append(new_image)

# Calculate total height and max width for the final image
total_height = sum(img.height for img in concatenated_groups)
max_width = max(img.width for img in concatenated_groups)

# Create the final image
final_image = Image.new('RGB', (max_width, total_height))

# Paste concatenated groups one below the other
y_offset = 0
for img in concatenated_groups:
    final_image.paste(img, (-10, y_offset))
    y_offset += img.height

# Save the final image
output_path = os.path.join(output_folder, "line_plot_image.png")
final_image.save(output_path)

print("Images have been concatenated and saved as a single image.")
