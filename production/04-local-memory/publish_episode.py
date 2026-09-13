"""Explicit public release of Episode 4 only; default invocation is read-only.

No global private-default is disabled. --public records the user's one-episode
authorization. The local upload marker prevents blind retries after uncertainty.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

from facelessyt import config

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/video/04-local-memory'
TITLE="Your AI Model Fits. Your Conversation Doesn't."


def save(path,data):
    path.write_text(json.dumps(data,indent=2),encoding='utf-8')


def check_channel(yt):
    rows=yt.channels().list(part='snippet,contentDetails,status',mine=True).execute().get('items',[])
    if len(rows)!=1 or rows[0]['snippet']['title']!='Outlier Engineering':
        raise RuntimeError('Authorized channel is not uniquely Outlier Engineering')
    channel=rows[0]
    expected=config.my_channel_id()
    if channel['id']!=expected:raise RuntimeError('Channel ID differs from MY_CHANNEL_ID')
    found=[];token=None
    while True:
        args={'part':'snippet','playlistId':channel['contentDetails']['relatedPlaylists']['uploads'],'maxResults':50}
        if token:args['pageToken']=token
        page=yt.playlistItems().list(**args).execute()
        for item in page.get('items',[]):
            s=item['snippet'];found.append({'id':s['resourceId']['videoId'],'title':s['title']})
        token=page.get('nextPageToken')
        if not token:break
    return channel,found


def validate_assets():
    qa=json.loads((OUT/'render-qa.json').read_text())
    if not qa.get('technical_pass') or not all(qa['checks'].values()):raise RuntimeError('Render QA has not passed')
    for name,key in [('04-local-memory-final.mp4','video_sha256'),('thumbnail.jpg','thumbnail_sha256'),('description.txt','description_sha256')]:
        if hashlib.sha256((OUT/name).read_bytes()).hexdigest()!=qa[key]:raise RuntimeError(f'QA asset hash mismatch: {name}')
    if not 60<qa['duration_seconds']<900:raise RuntimeError('Unexpected duration for Episode 4')
    return qa


def upload_body(description):
    if len(description)>5000:raise ValueError('Description exceeds YouTube limit')
    return {'snippet':{'title':TITLE,'description':description,'categoryId':'28',
        'tags':['local AI','LLM memory','KV cache','Python','AI engineering'],
        'defaultLanguage':'en','defaultAudioLanguage':'en'},
        'status':{'privacyStatus':'public','selfDeclaredMadeForKids':False}}


def main():
    from facelessyt import auth
    from googleapiclient.http import MediaFileUpload
    parser=argparse.ArgumentParser();parser.add_argument('--public',action='store_true')
    parser.add_argument('--status',action='store_true');args=parser.parse_args()
    yt=auth.youtube(interactive=False)
    channel,existing=check_channel(yt)
    print(json.dumps({'channel':channel['snippet']['title'],'channel_id':channel['id'],'uploads':existing}),flush=True)
    receipt=OUT/'upload-receipt.json';marker=OUT/'upload-in-progress.json'
    if args.status or receipt.exists():
        if not receipt.exists():raise RuntimeError('No upload receipt exists')
        known=json.loads(receipt.read_text())
        state=yt.videos().list(part='snippet,status,processingDetails,contentDetails',id=known['video_id']).execute()
        save(OUT/'youtube-status.json',state)
        print(json.dumps(state,indent=2),flush=True);return
    duplicates=[e for e in existing if e['title'].casefold()==TITLE.casefold()]
    if duplicates:raise RuntimeError('Matching Episode 4 title already exists; no duplicate upload: '+json.dumps(duplicates))
    if not args.public:
        print('READ-ONLY PREFLIGHT: correct channel; no Episode 4 duplicate. No upload performed.');return
    qa=validate_assets()
    if marker.exists():raise RuntimeError('Earlier upload outcome uncertain; inspect channel before retrying. No new insertion.')
    description=(OUT/'description.txt').read_text(encoding='utf-8')
    if len(description)>5000:raise RuntimeError('Description exceeds YouTube limit')
    # Record intent before insertion; this file is ignored by Git and contains no credentials.
    OUT.mkdir(parents=True,exist_ok=True)
    with marker.open('x',encoding='utf-8') as fh:
        json.dump({'state':'upload_starting','channel_id':channel['id'],'video_sha256':qa['video_sha256'],
                   'privacy_requested':'public','authorization':'User explicitly requested direct public release of Episode 4'},fh)
    body=upload_body(description)
    request=yt.videos().insert(part='snippet,status',body=body,
        media_body=MediaFileUpload(str(OUT/'04-local-memory-final.mp4'),mimetype='video/mp4',
                                  chunksize=5*1024*1024,resumable=True))
    response=None
    while response is None:
        status,response=request.next_chunk(num_retries=2)
        if status:print(f'PUBLIC UPLOAD {int(status.progress()*100)}%',flush=True)
    video_id=response['id']
    record={'video_id':video_id,'url':'https://www.youtube.com/watch?v='+video_id,'channel_id':channel['id'],
            'privacy_requested':'public','privacy_returned':response.get('status',{}).get('privacyStatus'),
            'video_sha256':qa['video_sha256'],'thumbnail_set':False}
    save(receipt,record)  # Persist ID BEFORE any thumbnail call can fail.
    save(marker,{'state':'upload_returned_id','video_id':video_id})
    thumbnail=yt.thumbnails().set(videoId=video_id,media_body=MediaFileUpload(str(OUT/'thumbnail.jpg'))).execute()
    record['thumbnail_set']=True;save(receipt,record)
    save(OUT/'thumbnail-response.json',thumbnail)
    state=yt.videos().list(part='snippet,status,processingDetails,contentDetails',id=video_id).execute()
    save(OUT/'youtube-status.json',state)
    print(json.dumps(record,indent=2),flush=True)
    print(json.dumps(state,indent=2),flush=True)


if __name__=='__main__':main()
