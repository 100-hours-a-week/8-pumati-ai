# import csv
# import json

# json_list = []
# with open("/Users/hbin/KTD/pumati-ai/8-pumati-ai/app/model_inference/fine_tuning_data/training_images/caption.txt", newline='') as csvfile:
#     reader = csv.reader(csvfile)
#     for row in reader:
#         json_list.append({
#             "file_name": row[0],
#             "text": row[1]
#         })

# with open("in.json", "w") as f:
#     json.dump(json_list, f, indent=2)

import os
import pandas as pd

# caption.txt를 불러와서
df = pd.read_csv('/Users/hbin/KTD/pumati-ai/8-pumati-ai/app/model_inference/fine_tuning_data/training_images/caption.txt', header=None, names=["filename", "caption"])

for index, row in df.iterrows():
    image_name = row['filename'].strip()
    caption = row['caption']
    txt_path = f"/Users/hbin/KTD/pumati-ai/8-pumati-ai/app/model_inference/fine_tuning_data/training_images/{os.path.splitext(image_name)[0]}.txt"
    with open(txt_path, 'w') as f:
        f.write(caption)
