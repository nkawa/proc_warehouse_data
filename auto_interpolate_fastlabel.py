# track_file　を firstlabel に変更しながら、
# GAP のある部分を自動的に補完し、
# GAP(認識できてない部分)の画像をみつけて、Captureする
# 参考フォーマット
# https://fastlabel.notion.site/19ea9ec20a6f48b29fa309cc8c00d2b8#527d691d8c5d45c39e82511c7078355e

import json
import numpy as np
import pickle
import cv2
from datetime import datetime,timedelta
from glob import glob
import os.path as path


BASE_X = 3885.356
BASE_Y = 812.703

undis_dir = "/mnt/gazania/trusco-undis/2024/2024-10-03"


base_format = {        
        "name": "new_half_1100_1130_ts2x.mp4", # <- ここに対象となるファイル名を入れることが必要
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

bibs_colors = [
    "#C7132D",
    "#0F56B8",
    "#B6D605",
    "#D62514",
    "#459E23",
    "#DFDFDF",
]

def scolor(n):
    try:
        num  = int(n)
        if num < 6:
            return bibs_colors[num]

    except Exception as e:
        print("SColor_Error[", n, "]",e)
        return "#800080"

    return subj_colors[num % 50]


def load_pj_tscache():
    pj_file = "/mnt/bigdata/01_projects/2024_trusco/asset/pj/projective_matrices_nkawa_handcraft_1934.json"
    ts_cache_file = "/mnt/bigdata/01_projects/2024_trusco/ts_result/20241003-tscaches_adjusted.pkl"

    with open(pj_file) as f:
        pj_dict: dict[str, dict[str, int | list[list[float]]]] = json.load(f)
    with open(ts_cache_file, mode="rb") as f:
        ts_cache: tuple[dict[str, list[tuple[int, int]]], dict[str, int]] = pickle.load(f)

    return pj_dict, ts_cache

def convert_fastlabel(track_json):

    annon = []

# ここに各トラックをつける
    track_ids = {}
# すでに subj_id がついているのはこっち
    subj_ids ={}

    for frame in track_json:
#        if frame['frame_id'] >= 4500*2: #　まずは前半30分
        if frame['frame_id'] >= 2250*2: #　まずは前半15分
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
                        "src_cam": track['src_cam'], ## これ重要！
                        "autogenerated": False
                    }
#                except Exception as e:
#                    print("Error: Converting", e, ssid)
            else:
                if not(tid in track_ids):
                    track_ids[tid] = {}

#                track_ids[tid][str(frame_id+1)]={
#                    "value":[
#                        track['bbox'][0]-BASE_X,
#                        track['bbox'][1]-BASE_Y,
#                        track['bbox'][2]+track['bbox'][0]-BASE_X,
#                        track['bbox'][3]+track['bbox'][1]-BASE_Y
#                    ],
#                    "autogenerated": False
#                }
    
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
#    for tid,v in track_ids.items():        
#        annon.append({
##            "type": "bbox",
 #           "title": "other_"+str(tid),
 #           "value": "other_"+str(tid),
 #           "color": scolor(tid),
 #           "attributes": [],
 #           "points": v
 #           
 #       })

    new_frame['annotations'] = annon

    return new_frame

def _crop(pjs: dict[str, np.ndarray]) -> tuple[dict[str, np.ndarray], tuple[int, int]]:
    stitched_ltrb = [np.inf, np.inf, -np.inf, -np.inf]
    for p in pjs.values():
        tf_corners = cv2.perspectiveTransform(np.array(((0, 0), (1920, 0), (0, 1080), (1920, 1080)), dtype=np.float32)[:, np.newaxis], p).squeeze(axis=1)
        stitched_ltrb[0] = min(stitched_ltrb[0], tf_corners[0, 0], tf_corners[2, 0])
        stitched_ltrb[1] = min(stitched_ltrb[1], tf_corners[0, 1], tf_corners[1, 1])
        stitched_ltrb[2] = max(stitched_ltrb[2], tf_corners[1, 0], tf_corners[3, 0])
        stitched_ltrb[3] = max(stitched_ltrb[3], tf_corners[2, 1], tf_corners[3, 1])
    for n, p in pjs.items():
        pjs[n] = np.dot(np.array((
            (1, 0, -stitched_ltrb[0]),
            (0, 1, -stitched_ltrb[1]),
            (0, 0, 1)
        ), dtype=np.float64), p)

    return pjs, (int(stitched_ltrb[2] - stitched_ltrb[0]), int(stitched_ltrb[3] - stitched_ltrb[1]))


def reverse_proj(pj, x0, y0, x1, y1):
    inv_pj = np.linalg.inv(pj)
    dst_coord_homo0 = np.array([x0, y0, 1.0])
    src_coord_homo0 = np.dot(inv_pj, dst_coord_homo0)
    dst_coord_homo1 = np.array([x1, y1, 1.0])
    src_coord_homo1 = np.dot(inv_pj, dst_coord_homo1)

    src_coord0 = src_coord_homo0[:2]/src_coord_homo0[2]
    src_coord1 = src_coord_homo1[:2]/src_coord_homo1[2]

    return src_coord0[0],src_coord0[1],src_coord1[0],src_coord1[1]

caps = {}

def capImage(cam, frame,ts_cache):
    global caps
    cur_in_sec = int((datetime.strptime("11:00:00", "%H:%M:%S") - datetime(1900, 1, 1)).total_seconds())
    cur_in_sec += frame * 0.4 # 0.4秒ごとにフレームが進む(2x の場合)
    vid_idx, frm_idx = ts_cache[0][cam][int(5 * (cur_in_sec - ts_cache[1][cam]))]
    print("capImage:",cam, frame, vid_idx, frm_idx)
            
    if cam in caps.keys() and caps[cam]["vid_idx"] != vid_idx:
        caps[cam]["cap"].release()
    if cam not in caps.keys() or caps[cam]["vid_idx"] != vid_idx:
        caps[cam] ={
            "cap": cv2.VideoCapture(filename=glob(path.join(undis_dir, f"camera{cam}/video_??-??-??_{vid_idx:02d}.mp4"))[0]),
            "vid_idx": vid_idx,
            "cur_frm":0
        }
    if caps[cam]["cur_frm"] >= frm_idx:
        caps[cam]["cap"].set(cv2.CAP_PROP_POS_FRAMES, frm_idx)

    while caps[cam]["cap"].get(cv2.CAP_PROP_POS_FRAMES) <= frm_idx:
        caps[cam]["frm"] = caps[cam]["cap"].read()[1]  # エラー想定無ｗ
        caps[cam]["cur_frm"] = caps[cam]["cap"].get(cv2.CAP_PROP_POS_FRAMES)

    return caps[cam]["frm"]


def check_annotations(annon, pjs, ts_cache):
    global gapCount
    titles = {}
#    print(len(anon))
    new_anon = []
    new_labels = [] # どのフレームにどのカメラでどの位置にいるか


    for a in annon:
        pts = a["points"]
        keys = list(pts.keys())
        if len(pts) < 20: # 20フレーム未満は無視 (ホントにいいの？)
            print("Ignore Short:",a["title"], len(pts), keys[0],keys[-1])
            continue
        print(a["title"], len(a["points"]))
        

        lastx  =int(keys[0])
        for k in keys:# フレーム番号
            x = int(k)
            if (x-lastx) > 40:
                print("BigGap:",a["title"], lastx, k)
            if (x-lastx) < 10 and (x-lastx) > 1: # small gap
#                print("Small Gap:",a["title"], lastx, k, x-lastx)
                # 小さいGAP は補完したい！
                gapCount += x-lastx-1
                for i in range(lastx+1, x): # 安直に線形補完
                    pts[str(i)] = {
                        "value": [
                            pts[str(lastx)]["value"][0] + (pts[str(x)]["value"][0]-pts[str(lastx)]["value"][0])*(i-lastx)/(x-lastx),
                            pts[str(lastx)]["value"][1] + (pts[str(x)]["value"][1]-pts[str(lastx)]["value"][1])*(i-lastx)/(x-lastx),
                            pts[str(lastx)]["value"][2] + (pts[str(x)]["value"][2]-pts[str(lastx)]["value"][2])*(i-lastx)/(x-lastx),
                            pts[str(lastx)]["value"][3] + (pts[str(x)]["value"][3]-pts[str(lastx)]["value"][3])*(i-lastx)/(x-lastx)
                        ],
                        "autogenerated": True
                    }
#                    print("Gap:",a["title"], i, pts[str(i)]["value"])

                    #この位置でラベルを作ればよい！
                    x0,y0,x1,y1 = reverse_proj(pjs[pts[str(x)]["src_cam"]],
                                pts[str(i)]["value"][0],
                                pts[str(i)]["value"][1],
                                pts[str(i)]["value"][2],
                                pts[str(i)]["value"][3]
                    )
                    if x0 < 0 or y0 < 0 or x1 < 0 or y1 < 0 or x0>=1920 or y0>=1080 or x1>=1920 or y1>=1080:
                        print("Projection Error:",pts[str(x)]["src_cam"], i, x0,y0,x1,y1)
                    else:
                        new_labels.append((pts[str(x)]["src_cam"],i,
                            {
                            "type": "bbox",
                            "title": "worker",
                            "value": "worker",
                            "color": "#FF0000",
                            "points":[
                                x0,y0,x1,y1
                            ]
                      }))
                    if pts[str(lastx)]["src_cam"] != pts[str(x)]["src_cam"]: # 両側のフレームのカメラがあるときは、どっちかが正しい
                        x0,y0,x1,y1 = reverse_proj(pjs[pts[str(lastx)]["src_cam"]],
                                pts[str(i)]["value"][0],
                                pts[str(i)]["value"][1],
                                pts[str(i)]["value"][2],
                                pts[str(i)]["value"][3]
                        )
                        if x0 < 0 or y0 < 0 or x1 < 0 or y1 < 0 or x0>=1920 or y0>=1080 or x1>=1920 or y1>=1080:
                            print("Projection Error:",pts[str(lastx)]["src_cam"], i, x0,y0,x1,y1)
                        else:
                            new_labels.append(
                                (pts[str(lastx)]["src_cam"],i,{
                                    "type": "bbox",
                                    "title": "worker",
                                    "value": "worker",
                                    "color": "#FF0000",
                                    "points":[
                                        x0,y0,x1,y1
                                    ]
                                }))

            lastx= x

        if a["title"] not in titles:
            titles[a["title"]]=f"{a['title']}, {len(pts)}, {keys[0]},{keys[-1]}"
        else:
#            print("Dup Title!",a["title"]) 
            print("Dup", titles[a["title"]])
            print("   ",a["title"], len(pts), keys[0],keys[-1])
        
        new_anon.append(a)
    
    return new_anon, new_labels

#LabelDIR = "/mnt/vanda/01_projects/2024_trusco/20241003-track/1106tracking_result_20241003_worker_body_1100_1200_updated.json"
TrackDIR = "/mnt/bigdata/01_projects/2024_trusco/track_result/with_bibs/make_correct_json/"
gapCount = 0
if __name__ == '__main__':
#    workers = load_json_file("adjusted_tracking_result_2024-10-03_39600_43200_200_99_90_True_150_200_200_9990_10_True_90.json")
#    workers = load_json_file("modify_adjusted_tracking_result_2024-10-03_39600_43200_200_99_90_True_150_200_200_9985_10_True_90.json")
#    workers = load_json_file("correct_tracking_result_2024-10-03_39600_43200_200_99_90_True_150_200_200_9985_10_True_90.json")
    workers = load_json_file(TrackDIR+"1111correct_tracking_result_2024-10-03_39600_43200_200_99_90_True_150_200_200_9985_10_True_90.json")
    new_frame = convert_fastlabel(workers)
    pj_dict, ts_cache = load_pj_tscache()
    cam_names = pj_dict.keys() & ts_cache[0].keys()
    pjs, frm_size = _crop({n: np.array(pj_dict[n]["projective_matrix"], dtype=np.float64) for n in cam_names})


    new_frame_anon, new_lbls= check_annotations(new_frame['annotations'],pjs, ts_cache)
    print("New Labels", len(new_lbls), gapCount)
#    new_frame['annotations'] = new_frame_anon

    with_img = True
    worked_frames = {}
    ct = 0
    for (cam, frm, anon) in new_lbls:
        camstr= f"{cam}_{frm:04d}"
 #       print("Working for ", camstr, ct)
        ct += 1
        if camstr not in worked_frames:
            if with_img:
                img = capImage(cam, frm, ts_cache)
#            out_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                print("Writing_file:",camstr,ct)
                cv2.imwrite(f"imgs/{camstr}.jpg", img)
            worked_frames[camstr] = [
                anon
            ]
        else:
            worked_frames[camstr].append(anon)        

    # 次に、cam-frm 毎に、他のアノテーションも追加
    ct2 = 0
    for camstr, annons in worked_frames.items():
        cam,frm = camstr.split("_")
        fno = int(frm)
        add_annons = []
        print("updatting:",camstr,ct2,"/",len(worked_frames))
        ct2 += 1
        for a in new_frame['annotations']:
            pts = a["points"]
            if str(fno) in pts:
#                print("str(fno)",str(fno), pts)
                if "src_cam" in pts[str(fno)]: # 後は　自動生成
                    if pts[str(fno)]["src_cam"] == cam:
                        x0,y0,x1,y1 = reverse_proj(pjs[cam],
                            pts[str(fno)]["value"][0],
                            pts[str(fno)]["value"][1],
                            pts[str(fno)]["value"][2],
                            pts[str(fno)]["value"][3]
                        )
                        if x0 < 0 or y0 < 0 or x1 < 0 or y1 < 0 or x0>=1920 or y0>=1080 or x1>=1920 or y1>=1080:
                            print("Projection Error:",cam, fno, x0,y0,x1,y1)
                        else:
                            addanon = {
                                    "type": "bbox",
                                    "title": "worker",
                                    "value": "worker",
                                    "color": "#FF0000",
                                    "points":[
                                        x0,y0,x1,y1
                                    ]
                            }
                            add_annons.append(addanon)

        annons.extend(add_annons)

    # これですべて追加されたはず。
    out_json = []

    for camstr, annons in worked_frames.items():
        cam,frm = camstr.split("_")
        fno = int(frm)
        out_json.append({  
            "name": camstr+".jpg",
            "width": 1920,
            "height": 1080,
            "annotations": annons,
        })

    with open('1111_fl_upload_generated_labels_new.json', 'w') as f:
        json.dump(out_json, f, indent=4)



    # ここで得られた new_lbls と new_imgs を使って、画像を取得する


#    with open('1111_fl_upload_with_subj_autofill_new.json', 'w') as f:
#        json.dump([new_frame], f, indent=4)