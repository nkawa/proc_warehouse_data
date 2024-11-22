
# 大量のイメージを fastlabel にアップロードするスクリプト
# access token

import fastlabel

from glob import glob
from pathlib import Path
import time

client = fastlabel.Client()


#task_id = client.create_image_task(
 #   project="autogen1111",
 #   name="sample.jpg",
 #   file_path="./sample.jpg"
#)

files = glob("imgs/*.jpg")
files.sort()
print(len(files))
count = 0
for file in files:
    print(file, Path(file).name, count,"/", len(files))
    count += 1
    client.create_image_task(
        project="autogen1111",
        name=Path(file).name,
        file_path=file
    )
    time.sleep(0.5)
#    print("done")
