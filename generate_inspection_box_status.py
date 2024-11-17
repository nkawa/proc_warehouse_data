
# inspection_task_time_intervals から 読み込み用のデータを作成

import os
import pandas as pd
import json
from glob import glob
import numpy as np
import datetime



def inspection_box_status(fname = "inspection_task_time_intervals_07_21.csv"):
    insp_df = pd.read_csv(fname)

#print(insp_df)
#print(insp_df.columns)
# columns
#['area', 'in_time', 'out_time', 'entry_to_first_task','first_to_last_task', 'last_task_to_exit', 'entry_index']

    basetime = datetime.datetime.strptime("2024-10-03 07:00:00", '%Y-%m-%d %H:%M:%S')

    bm_id = 0
    boxdata=[]
    for idx, row in insp_df.iterrows():    
        in_time = datetime.datetime.strptime(row['in_time'], '%Y-%m-%d %H:%M:%S')
        out_time = datetime.datetime.strptime(row['out_time'], '%Y-%m-%d %H:%M:%S')

        in_time = (in_time - basetime).total_seconds()
        out_time = (out_time - basetime).total_seconds()

        in_frame = int(in_time *2.5)
        out_frame = int(out_time *2.5 +0.5)

        frm_data = {
            'bm_id': idx,
            'box_id':int(row['area']),
            'in_frame':in_frame,
            'inspect_start':in_frame+int(row['entry_to_first_task']*60*2.5),
            'inspect_end':in_frame+int((row['entry_to_first_task']+row['first_to_last_task'])*60*2.5),
            'out_frame':out_frame
        }
        boxdata.append(frm_data)

    return boxdata
