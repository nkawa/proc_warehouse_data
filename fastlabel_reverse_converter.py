# track_file　を firstlabel に変更
# firstlabel からのフォーマットを track_file に変更
# 参考フォーマット
# https://fastlabel.notion.site/19ea9ec20a6f48b29fa309cc8c00d2b8#527d691d8c5d45c39e82511c7078355e

import json
import numpy as np
import gzip
import zipfile
import io
import glob

BASE_X = 3885.356
BASE_Y = 812.703


base_format = {        
        "name": "new_half_1100_1130_ts2x_pallet.mp4",
        "status": "registered",
        "externalStatus": "registered",
        "width": 3932,
        "height": 2312,
        "fps": 30,
        "frameCount": 4498,
        "duration": 149.9333333333,
        "secondsToAnnotate": 0,
        "annotations": [
            {
                "type": "bbox",
                "title": "worker",
                "value": "worker",
                "color": "#D10069",
                "attributes": [],
                "points": {
                    "1": {           # number of frame
                        "value": [
                            271.63,  # top-left x point
                            130.96,  # top-left y point
                            755.36,  # bottom-right x point
                            470.29   # bottom-right y point
                        ],
                    }
                }
            }
        ],
        "tags": [],
    }

def load_json_file(file):
    with open(file, 'r') as f:
        workers = json.load(f)

    return workers

from colorsys import hls_to_rgb

def get_distinct_colors(n):
    colors = []
    for i in np.arange(0., 360., 360. / n):
        h = i / 360.
        l = (50 + np.random.rand() * 10) / 100.
        s = (90 + np.random.rand() * 10) / 100.
        colors.append(hls_to_rgb(h, l, s))

    return colors



subj_colors = get_distinct_colors(50)

def scolor(n):
    try:
        num  = int(n)
    except Exception as e:
        print("SColor_Error[", n, "]",e)
        return "#800080"

    return subj_colors[num % 50]

def convert_fastlabel(track_json):

    annon = []

# ここに各トラックをつける
    track_ids = {}
# すでに subj_id がついているのはこっち
    subj_ids ={}

    for frame in track_json:
        if frame['frame_id'] >= 4498*2: #　まずは前半30分
            break
        if frame['frame_id'] % 2 == 1:
            continue
        frame_id = frame['frame_id'] // 2
        print("Frame_id: ", frame_id)
        for track in frame['tracks']:
            tid = track['track_id']
            if 'subj_id' in track and not(track['subj_id'].startswith("track")):
                ssid = track['subj_id']
                if ssid == "None":
                    continue
                if True:
                    sid = ssid

                    if not(sid in subj_ids):
                        subj_ids[sid] = {}

                    subj_ids[sid][str(frame_id+1)]={
                        "value":[
                            track['bbox'][0]-BASE_X,
                            track['bbox'][1]-BASE_Y,
                            track['bbox'][2]+track['bbox'][0]-BASE_X,
                            track['bbox'][3]+track['bbox'][1]-BASE_Y
                        ],
                        "autogenerated": False
                    }
#                except Exception as e:
#                    print("Error: Converting", e, ssid)
            else:
                if not(tid in track_ids):
                    track_ids[tid] = {}

                track_ids[tid][str(frame_id+1)]={
                    "value":[
                        track['bbox'][0]-BASE_X,
                        track['bbox'][1]-BASE_Y,
                        track['bbox'][2]+track['bbox'][0]-BASE_X,
                        track['bbox'][3]+track['bbox'][1]-BASE_Y
                    ],
                    "autogenerated": False
                }
    
    new_frame = base_format
#    print(track_ids)

    annon = []
    for sid,v in subj_ids.items():        
        annon.append({
            "type": "bbox",
            "title": "worker_"+str(sid),
            "value": "worker_"+str(sid),
            "color": scolor(sid),
            "attributes": [],
            "points": v
            
    })
    print("Subj_ids: ", len(subj_ids))
    for tid,v in track_ids.items():        
        annon.append({
            "type": "bbox",
            "title": "pallet_"+str(tid),
            "value": "pallet_"+str(tid),
            "color": scolor(tid),
            "attributes": [],
            "points": v
            
        })

    new_frame['annotations'] = annon

    return new_frame


#　まずは、繋がっていないアノテーションを同じにして、番号をそろえる。
def clean_firstlabel(anon):
    titles = {}
    for a in anon:
        pts = a["points"]
        frames = list(pts.keys()) # フレーム番号のリスト

        fl = 0
        if a["title"] not in titles:
            titles[a["title"]] = {
                        "type": "bbox",
                        "title": a["title"],
                        "value": a["title"],
                        "color" : a["color"],
                        "attributes": [],
                        "points": a["points"],
            }
        else: # 同じタイトルがある場合
            points = titles[a["title"]]["points"]
            for f in pts:
                if f not in titles[a["title"]]["points"]:
                    titles[a["title"]]["points"][f] = a["points"][f]
                    fl+=1
                else:
                    print("Dup Frame", a["title"], f)
#            points.extend(a["points"])
#            titles[a["title"]]["points"] = points
#        print("Add points", a["title"], len(titles[a["title"]]["points"]),fl)

    newannon = []
    palcount = 0
    otcount = 0
    for t in titles.keys():
        if "pallet" in t:
            palcount+=1
            pname = f"pallet_{palcount:03d}"
        else:
            otcount += 1

            pname = f"other_{otcount:03d}"

        pp = titles[t]
        pp["title"] = pname
        pp["value"] = pname
        newannon.append(pp)

    return newannon

def check_annotations(annon):
    titles = {}
#    print(len(anon))
    
    for a in annon:
        print(a["title"], len(a["points"]))
        pts = a["points"]
        keys = list(pts.keys())
        if len(pts) < 10:
            print("Short:",a["title"], len(pts), keys[0],keys[-1])

        lastx  =int(keys[0])
        for k in keys:
            x = int(k)
            if (x-lastx) > 1:
                print("Gap:",a["title"], lastx, k)
            lastx= x
            if k not in pts:
                print("Key Error",a["title"], k)

        if a["title"] not in titles:
            titles[a["title"]]=f"{a['title']}, {len(pts)}, {keys[0]},{keys[-1]}"
        else:
#            print("Dup Title!",a["title"]) 
            print("Dup", titles[a["title"]])
            print("   ",a["title"], len(pts), keys[0],keys[-1])



def reverse_convert_prep(annon):    
    titles = {}
    for a in annon:
#        print(a)
        pts = a["points"]  # １つのtrack_id (worker に関する情報)
        frames = list(pts.keys()) # フレーム番号のリスト

        fl = 0
        if a["title"] not in titles:
            titles[a["title"]] = {
                        "type": "bbox",
                        "title": a["title"],
                        "value": a["title"],
                        "color" : a["color"],
                        "attributes": [],
                        "points": a["points"],
            }
        else: # 同じタイトルがある場合
            points = titles[a["title"]]["points"]
            for f in pts:
                if f not in titles[a["title"]]["points"]:
                    titles[a["title"]]["points"][f] = a["points"][f]
                    fl+=1
                else:
                    print("Dup Frame", a["title"], f)
#            points.extend(a["points"])
#            titles[a["title"]]["points"] = points
#        print("Add points", a["title"], len(titles[a["title"]]["points"]),fl)

    newannon = []
    palcount = 0
    otcount = 0
    newTitles = []
    for t in titles.keys():
        if "worker" in t:
            wkd = t.split("_")
            try:
                num = int(wkd[1])
            except Exception as e:
#                print("non int Error", e, wkd)
                continue
            if num < 0 or num >= 39:
                print("toobig")
                continue
            wname = f"worker_{num:02d}"
        else:
            print("Other:",t)
            continue


        pp = titles[t]
        newTitles.append(wname)
        pp["title"] = wname
        pp["value"] = wname
        pp["track_id"]= num
        newannon.append(pp)

# ここからは、フレームに変更

#    for t in newannon:

    return newannon,newTitles


def reverse_convert(new_anon):
    frames = {}
    for a in new_anon:
        pts = a["points"]
        track_id = a["track_id"]
        for f in pts.keys():
            frame_id = int(f)-1  # ここで文字列の"1" -> 0 へ
            bbox =pts[f]["value"] 
            if frame_id not in frames:
                frames[frame_id] = {
                    "frame_id": frame_id,
                    "tracks": []
                }
            frames[frame_id]["tracks"].append(
                {
                    "track_id": track_id,
                    "bbox" :[
                        bbox[0]+BASE_X,
                        bbox[1]+BASE_Y,
                        bbox[2]-bbox[0],
                        bbox[3]-bbox[1]
                    ],
                })
    print("Rev:", len(frames))
            
    final = []
#    print(frames.keys())
    for i in range(0,4600):
        if i in frames:
            print("Appending!",i)
            f = frames[i] 
            final.append(f)
#        else:
#            print("No ",i)

    return final

if __name__ == '__main__':
#    workers = load_json_file("adjusted_tracking_result_2024-10-03_39600_43200_200_99_90_True_150_200_200_9990_10_True_90.json")
#    workers = load_json_file("modify_adjusted_tracking_result_2024-10-03_39600_43200_200_99_90_True_150_200_200_9985_10_True_90.json")
#    workers = load_json_file("correct_tracking_result_2024-10-03_39600_43200_200_99_90_True_150_200_200_9985_10_True_90.json")
#    pallets = load_json_file("tracking_result_20241003_pallet_085_1100_1200_updated.json")
#   new_frame = convert_fastlabel(pallets)

#    with open('fastlabel_upload_with_subj.json', 'w') as f:
#        json.dump([new_frame], f, indent=4)

#    FastLabelのアノテーションは zip 済なので、これを直接開きたいｗ


    files = glob.glob("*.zip")
    print(files[-1])

    with zipfile.ZipFile(files[-1]) as zf:
        for x in zf.namelist():
            if "annotations.json" in x:
                with zf.open(x,'r') as f:
                    anon = json.load(f)

    print("AnonFile: ", len(anon[0]))
    annotations = anon[0]["annotations"]
    print("Annotations: ", len(annotations))


#    check_annotations(annotations)
#    print("Before",len(annotations))

    new_anon ,keys= reverse_convert_prep(annotations)

    keys.sort()
    print("Rev!", len(new_anon),"keys:", len(keys))

    for tt in keys:
        print("key",tt)
        for a in new_anon:
            if a["title"] == tt:
                print(a["title"],":len", len(a["points"]))
                lastp =-2
                state = False
                points = a["points"]
                for v,p in points.items():                    
                    if int(v) != lastp+1 and not state:
                        print("S:",v,sep="",end="-")
                        state = True
                    elif int(v) != lastp+1:
                        print(lastp,"[",(int(v)-lastp),"],S:",v,sep="",end="-")
                        state = True
                    lastp = int(v)
                if state:
                    print(lastp,"End")
                else:
                    print("")
                break




    final_frame = reverse_convert(new_anon)

    
#    with open('frame_based_woker_1110.json', 'w') as f:
#        json.dump(final_frame, f, indent=4)

    
#    with open('pallet_id_based_track.json', 'w') as f:
#        json.dump(new_anon, f, indent=4)    

#    annotations = clean_firstlabel(annotations)
#    print(annotations)
#    print("After",len(annotations))

#    print("annotaion", json.dumps(annotations, indent=4))

#    check_annotations(annotations)
    
#    anon[0]["annotations"] = annotations
#    with open('fastlabel_upload_fixed_pallet.json', 'w') as f:
#        json.dump(anon, f, indent=4)