

#kisho のタスク分類を可視化したい（分単位）

import os
import pandas as pd
import json
from glob import glob

#with open("denosed_pred_result_11-12_inspection_area.csv") as f:

#print(glob("../../fromTRUSCO_QNAP/2024/bigdata_task_recognition/*.csv"))

workdf = pd.read_csv("../../fromTRUSCO_QNAP/2024/bigdata_task_recognition/tasklog_20241003_11.csv")

print(workdf.columns)

['bibs_ID', '検品[%]', '搬送[%]', '仕分け[%]', '移動距離[m]', 'worker_ID']

jbase = []
for idx, row in workdf.iterrows():
    jbase.append(
        {'id':int(row['bibs_ID']),
         'workTimes':{
             'inspect':int(60*row['検品[%]'])/100,
             'transport':int(60*row['搬送[%]'])/100,
             'sorting':int(60*row['仕分け[%]'])/100,
         },
         'distance':int(row['移動距離[m]'])
        }
    )

with open("worker_stat_20241003_11.json","w") as f:
    json.dump(jbase,f,indent=4)

