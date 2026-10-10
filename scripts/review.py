#!/usr/bin/env python3
"""Owner-only issue state transitions. Issue text is data, never code."""
import argparse, datetime as dt, json, pathlib, re
from urllib.parse import urlparse
P = pathlib.Path("data/projects.json")
ASSETS = re.compile(r"https?://[^\s<>)\]\"']+")
CREATE = re.compile(r"<!--\s*FILM_CREATE_V1\s*(\{.*?\})\s*-->", re.S)
KINDS = {"H":"真人剧情","S":"诗意风景","C":"真人＋风景"}

def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

def allowed(url):
    try:
        p=urlparse(url)
        if p.scheme!="https" or p.username or p.password: return False
        h=(p.hostname or "").lower()
        if h=="github.com": return p.path.startswith("/user-attachments/assets/") or p.path.startswith("/1464356758/douyin-XT/")
        if h=="user-images.githubusercontent.com": return True
        if h=="raw.githubusercontent.com": return p.path.startswith("/1464356758/douyin-XT/")
        return False
    except ValueError: return False

def media(text):
    out=[]
    for raw in ASSETS.findall(text):
        url=raw.rstrip(".,;!，。；）")
        if allowed(url) and url not in out: out.append(url)
    return out[:15]

def record(p,command,detail=""):
    p.setdefault("history",[]).append({"action":command,"detail":detail[:800],"at":now()})
    p["updated_at"]=now()

def gate(p,stage,command):
    if p["stage"] not in stage: raise ValueError(command+" 当前阶段禁止操作："+p["stage"])

def apply(doc,event,owner):
    if (event.get("sender") or {}).get("login","").casefold()!=owner.casefold(): return False
    issue=event.get("issue") or {}
    if issue.get("pull_request") or not isinstance(issue.get("number"),int): return False
    n=issue["number"]
    items=doc.setdefault("projects",[])
    if event.get("action")=="opened":
        m=CREATE.search(issue.get("body") or "")
        if not m or any(p["issue"]==n for p in items): return False
        d=json.loads(m.group(1))
        title=str(d.get("title","")).strip()[:100]
        quote=str(d.get("quote","")).strip()[:300]
        original=str(d.get("original","")).strip()[:7000]
        kind=str(d.get("kind","C")).upper()
        if not title or not quote or not original or kind not in KINDS: raise ValueError("新增内容不完整")
        items.append({"id":"F"+str(n),"issue":n,"title":title,"quote":quote,"original":original,"kind":kind,"kind_label":KINDS[kind],"review_focus":["原稿不能漂移","人物、视角与动作正确","字幕音画同步"],"stage":"IMAGE_PREP","images":[],"videos":[],"last_image_batch":[],"last_video_batch":[],"image_revision":0,"video_revision":0,"notes":[],"history":[{"action":"created","at":now(),"detail":"新建原稿锁定"}],"published_url":"","stats":{"views":0,"likes":0,"shares":0,"follows":0},"updated_at":now()})
        return True
    if event.get("action")!="created": return False
    body=((event.get("comment") or {}).get("body") or "").strip()
    first=body.splitlines()[0].strip() if body else ""
    p=next((p for p in items if p["issue"]==n),None)
    if not p or not first.startswith("/"): return False
    command,_,reason=first.partition(" ")
    command=command.lower();reason=reason.strip()
    if command=="/submit-image":
        gate(p,{"IMAGE_PREP","IMAGE_REWORK"},command)
        urls=media(body)
        if not urls: raise ValueError("请在同一评论附上真实图片附件或链接")
        p["image_revision"]+=1; p["last_image_batch"]=urls
        p.setdefault("images",[]).append({"version":p["image_revision"],"urls":urls,"at":now()})
        p["stage"]="IMAGE_REVIEW";record(p,command,"图片V"+str(p["image_revision"]))
    elif command=="/approve-image":
        gate(p,{"IMAGE_REVIEW"},command)
        if not p.get("last_image_batch"): raise ValueError("没有实际图片不能审核通过")
        p["stage"]="VIDEO_PREP";record(p,command)
    elif command=="/revise-image":
        gate(p,{"IMAGE_REVIEW"},command)
        if len(reason)<3: raise ValueError("请附具体返修理由")
        p["stage"]="IMAGE_REWORK";p.setdefault("notes",[]).append({"type":"image","text":reason[:800],"at":now()});record(p,command,reason)
    elif command=="/submit-video":
        gate(p,{"VIDEO_PREP","VIDEO_REWORK"},command)
        urls=media(body)
        if not urls: raise ValueError("请在同一评论附上实际视频附件或链接")
        p["video_revision"]+=1;p["last_video_batch"]=urls
        p.setdefault("videos",[]).append({"version":p["video_revision"],"urls":urls,"at":now()})
        p["stage"]="VIDEO_REVIEW";record(p,command,"成片V"+str(p["video_revision"]))
    elif command=="/approve-video":
        gate(p,{"VIDEO_REVIEW"},command)
        if not p.get("last_video_batch"): raise ValueError("没有实际成片不能通过终审")
        p["stage"]="READY_PUBLISH";record(p,command)
    elif command=="/revise-video":
        gate(p,{"VIDEO_REVIEW"},command)
        if len(reason)<3: raise ValueError("请附具体返修理由")
        p["stage"]="VIDEO_REWORK";p.setdefault("notes",[]).append({"type":"video","text":reason[:800],"at":now()});record(p,command,reason)
    elif command=="/published":
        gate(p,{"READY_PUBLISH"},command)
        u=urlparse(reason)
        if u.scheme!="https" or (u.hostname or "").lower() not in {"www.douyin.com","douyin.com","v.douyin.com"}: raise ValueError("需要抖音视频有效URL")
        p["published_url"]=reason[:500];p["stage"]="PUBLISHED";record(p,command,reason)
    elif command=="/stats":
        gate(p,{"PUBLISHED"},command)
        vals=re.findall(r"\b(views|likes|shares|follows)=(\d+)\b",reason)
        if not vals: raise ValueError("格式：/stats views=100 likes=10 shares=2 follows=1")
        for key,val in vals:p.setdefault("stats",{})[key]=min(int(val),10**12)
        record(p,command,reason)
    else:return False
    return True

if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("--event",required=True);a.add_argument("--owner",required=True)
    x=a.parse_args()
    d=json.loads(P.read_text(encoding="utf-8"))
    event=json.loads(pathlib.Path(x.event).read_text(encoding="utf-8"))
    if apply(d,event,x.owner):
        P.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("STATE UPDATED")
    else:print("No state change")
