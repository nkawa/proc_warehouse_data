



#kisho のタスク分類を可視化したい（分単位）

import os
import pandas as pd
import json
from glob import glob

with open("pallet_id_based_track.json") as f:
    pallet_data = json.load(f)




print(len(pallet_data))


jbase = []

for ptrace in pallet_data:
    pid = int(ptrace['value'][-3:])
    points = ptrace['points']
    pdata = {
        'id':pid,
    }
    last = -1
    pts = []
    for k, v in points.items():
        if last == -1:
            pdata['start'] = int(k)
        elif last != int(k)-1:
            print("Gap!!!", pid, last, k, v)
        last = int(k)
        bbox = v['value']
        pts.append(
            [(bbox[0]+bbox[2])/2, (bbox[1]+bbox[3])/2]
        )
    pdata['points'] = pts
    if last != -1:
        pdata['end'] = last

    jbase.append(pdata)

# 本当は同じ場所にある trace の start-endはつなげたい。そうすると、同じtrace になる。。。


with open("pallet_trace_20241003_1100-1130.json","w") as f:
    json.dump(jbase,f,indent=4)