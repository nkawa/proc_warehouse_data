

#denoize したデータを使って、箱の情報を整理

import os
import pandas as pd
import json


#with open("denosed_pred_result_11-12_inspection_area.csv") as f:

#boxdf = pd.read_csv("denoised_pred_result_11-12_inspection_area.csv") 
boxdf = pd.read_csv("denoised_pred_result_07-12_inspection_area_with_offset_frame_id.csv") 

#　とりあえず、asayu の結果だけ使ってみる

#json としては、以下の形式が望ましい？


"""
# box毎のフレーム情報
boxes = [
    [ // 各box 毎のin/out 情報 
    {
   start: frm,
   end:   frm,
   pallet_id: id,
   pallet_type: type, // まあ知らんけど
     },...
  ]
]
"""


print ("Max Box:",max(boxdf['box_no']))
maxbox = max(boxdf['box_no'])

boxdf.describe()

boxdata = []
pallet_id = 0
for i in range(1,maxbox+1):
    current_box_data = []
    print ("Box:",i)
    box = boxdf[boxdf['box_no']==i]
    lastFrame = -10
    for idx, row in box.iterrows():
        exist = row['pred_result']        
        curframe = row['offset_frame_id']
        if exist==1 and lastFrame == -10: # 最初
            start_frame = curframe
            lastFrame = curframe
        elif exist == 1 and lastFrame +1 == curframe: #前もある
            lastFrame = curframe
        elif exist == 1 : #飛んでいた場合
            current_box_data.append(
                {'start':start_frame,
                 'end':lastFrame,
                 'pallet_id': pallet_id,
                 'pallet_type':row['original_pred_result']})
            pallet_id += 1
            start_frame = curframe
            lastFrame = curframe
    if lastFrame != -10:
        current_box_data.append(
            {'start':start_frame,
             'end':lastFrame,
             'pallet_id': pallet_id,
             'pallet_type':row['original_pred_result']})
        pallet_id += 1
    print("Box ",i, len(current_box_data))
    boxdata.append(current_box_data)

        
with open("box_inspection_area_07-12.json","w") as f:
    json.dump(boxdata,f, indent=4)
#