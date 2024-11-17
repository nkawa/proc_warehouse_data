

#denoize したデータを使って、箱の情報を整理

# 2024/11/16  作業情報も追加する！
#  generate_inspection_box_status.py　の処理と同じにする！

import os
import pandas as pd
import json

from generate_inspection_box_status import inspection_box_status

#with open("denosed_pred_result_11-12_inspection_area.csv") as f:

#boxdf = pd.read_csv("denoised_pred_result_11-12_inspection_area.csv") 
boxdf = pd.read_csv("denoised_pred_result_07-12_inspection_area_with_offset_frame_id.csv") 
boxdf2 = pd.read_csv("denoised_pred_result_07-12_sorting_area_with_offset_frame_id.csv") 

boxdf = pd.concat([boxdf,boxdf2])
#　とりあえず、asayu の結果だけ使ってみる

#json としては、以下の形式が望ましい？


"""
# box毎のフレーム情報 
# 注意すべきは、 boxes の配列は0　からスタート（box ID = 1 からだけど、-1 する！）
boxes = [
    [ // 各box 毎のin/out 情報 
    {
   start: frm,
   end:   frm,
   inspect-start: frm,
   inspect-end: frm,
   pallet_id: id,
   pallet_type: type, // まあ知らんけど
     },...
  ]
]
"""

inscpect_box_data = inspection_box_status() #こっちでは boxid は1から

def diff(x,y):
    return abs(x-y)

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
            foundFlag = False
            for insp in inscpect_box_data:
                if insp['box_id'] == i and (diff(insp['in_frame'],start_frame) < 10 or diff(insp['out_frame'],lastFrame)< 10):
                    print("Found !! insp data",curframe, insp['bm_id'], "as box:", i, "from ", insp['in_frame'],start_frame ,"to", insp['out_frame'], lastFrame)                
                    current_box_data.append(
                        {'start':start_frame,
                         'end':lastFrame,
                         'pallet_id': pallet_id,
                                        'pallet_type':'inspection',
                         'inspect_start':insp['inspect_start'],
                         'inspect_end':insp['inspect_end']
                     })
                    pallet_id += 1
                    foundFlag = True
                    break
                elif insp['box_id'] == i:
                    print("Big diff", insp['bm_id'], "as box:", i, "from ", insp['in_frame'],start_frame ,"to", insp['out_frame'], lastFrame)
            if not foundFlag:
                current_box_data.append(
                    {'start':start_frame,
                    'end':lastFrame,
                    'pallet_id': pallet_id,
                    'pallet_type':row['original_pred_result']})
                pallet_id += 1
            start_frame = curframe
            lastFrame = curframe
    
    if lastFrame != -10:
#        ここでinscpect_box_data にデータがあるかをチェック
        foundFlag = False
        for insp in inscpect_box_data:
            if insp['box_id'] == i and (diff(insp['in_frame'],start_frame) < 10 or diff(insp['out_frame'],lastFrame)< 10):
                print("Found !! insp data", insp['bm_id'], "as box:", i, "from ", insp['in_frame'],start_frame ,"to", insp['out_frame'], lastFrame)
                
                current_box_data.append(
                    {'start':start_frame,
                     'end':lastFrame,
                     'pallet_id': pallet_id,
                     'pallet_type':'inspection',
                     'inspect_start':insp['inspect_start'],
                     'inspect_end':insp['inspect_end']
                    })
                pallet_id += 1
                foundFlag = True
                break
            if insp['box_id'] == i:
                print("Big diff", insp['bm_id'], "as box:", i, "from ", insp['in_frame'],start_frame ,"to", insp['out_frame'], lastFrame)
        if not foundFlag:
            current_box_data.append(
                {'start':start_frame,
                 'end':lastFrame,
                 'pallet_id': pallet_id,
                'pallet_type':row['original_pred_result']})
            pallet_id += 1
    print("Box ",i, len(current_box_data))
    boxdata.append(current_box_data)

        
#with open("box_all_area_07-12.json","w") as f:
#    json.dump(boxdata,f, indent=4)
#
with open("box_omsp_sort_area_07-12.json","w") as f:
    json.dump(boxdata,f, indent=4)
