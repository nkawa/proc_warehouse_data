

from glob import glob
import pandas as pd
import datetime
import pytz
import json

dl = glob("../../fromTRUSCO_QNAP/bigdata_2024trusco/task_recognition/20241003/20241003_11/result/*.csv")


#print(dl)
#['Unnamed: 0', 'ID', 'Time', 'pred_task', 'pred_label', 'Ins', 'Trp', 'Srt', 'Time_dt']

alldf = pd.DataFrame()

basetime = datetime.datetime.strptime("2024-10-03 11:00:00", '%Y-%m-%d %H:%M:%S')
jst = pytz.timezone('Asia/Tokyo')
basetime = basetime.astimezone(jst)


fnames = {}

max = -1

for f in dl:
    id = f.split("/")[-1].split("_")[1]
    fnames[int(id)]=f
    if max < int(id):
        max = int(id)


worker_task_json= []

for i in range(max+1):
    if i in fnames:
        f = fnames[i]
    else:
        worker_task_json.append([]) #からの配列を追加
        print(worker_task_json[0])
        print("Skip ",i)
        continue
    worker_data =[]
    # frame 単位で start->end を作りたい。
    # とりあええず 11時スタートで 0-4499 のフレームに対応づける
    df = pd.read_csv(f, encoding="shift_jis")
#    print(df.columns)
#    alldf = pd.concat([alldf,df])

    lastLabel =-1
    lastFrame= -1 
    worklen = 0
    for idx,row in df.iterrows():
        task_time = datetime.datetime.fromisoformat(row['Time_dt'])
        nowFrame = int((task_time-basetime).total_seconds()*2.5)
        nowLabel = row['pred_label']
        if lastFrame == -1: # はじめて
            lastFrame = nowFrame
            lastLabel = nowLabel
        elif lastLabel != nowLabel:
            if nowFrame- lastFrame <= 20: # とりあえず決めてみた。 20/5*2 = 8秒以下の作業は作業とみなさない。
                pass
#                print("too small gap",nowFrame-lastFrame, nowFrame,lastFrame)
            else:
                worker_data.append({
                    "start":lastFrame,
                    "end": nowFrame,
                    "label": lastLabel
                })
            lastFrame = nowFrame
            lastLabel = nowLabel
            worklen = 0
    if nowFrame- lastFrame >20:
        worker_data.append({
                    "start":lastFrame,
                    "end": nowFrame,
                    "label": lastLabel
        })
    
    print("Worker",worker_data[0])

    # 上記で得られたのは、短いのがなくなった列
    # 前後で同じタスクでギャップが小さい場合は、くっつけたい
    lastLabel = -1
    lastTask = None
    update_worker = []
    for task in worker_data:
        if lastFrame == -1:
            lastLabel = task["label"]
            lastTask= task
        elif lastLabel == task["label"]: # 前のと同じラベルだったら
            if task["start"] - lastTask["end"] <= 20: # ギャップが20 以下だったら、くっつける
                lastTask["end"]= task["end"]
            else:
#                print("BigGap!!",lastTask,task)
                if lastTask != None:
                     update_worker.append(lastTask)
                lastLabel = task["label"]
                lastTask= task
        else: # labelが違う場合は、lastTaskを登録
            if lastTask != None:
                update_worker.append(lastTask)
            lastLabel = task["label"]
            lastTask= task
    if lastTask != None:
        update_worker.append(lastTask)
    print("Worker",update_worker[0])


    print("For Worker",row["ID"], "Count:",len(worker_data),len(update_worker))
    worker_task_json.append(update_worker)

print("TotalLen",len(worker_task_json))
    
with open("output/worker_task_eachframe_20241003_11.json","w") as f:
    json.dump(worker_task_json,f,indent=4)

#print(len(alldf))

# 0 検品
# 1 搬送
# 2 仕分け
