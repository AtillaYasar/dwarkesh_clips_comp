import youtubesearchpython
import sys, json, os, time

from colorama import init
init()

from youtube_transcript_api import YouTubeTranscriptApi
import numpy as np
from secret_things import openai_key
import requests
import webbrowser

def get_transcript(url):
    video_id = url.split('v=')[1]
    t = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])

    class Transcript(list):
        def __init__(self, t):
            super().__init__(t)
            self.duration = t[-1]['start'] + t[-1]['duration']

        def get_timerange(self, start, end):
            # grabs a subset of the transcript, can pass seconds or 'hh:mm:ss' strings
            def t_to_s(t):
                h, m, s = t.split(':')
                return int(h) * 3600 + int(m) * 60 + int(s)
            in_seconds = type(start) in (int, float)
            if not in_seconds:
                start = t_to_s(start)
                end = t_to_s(end)
            subset = [i for i in self if i['start'] >= start and i['start'] <= end]
            lines = [i['text'] for i in subset]
            return '\n'.join(lines)

        def get_full_text(self):
            return '\n'.join([i['text'] for i in self])

    return Transcript(t)

def col(ft, s):
    """For printing text with colors.
    
    Uses ansi escape sequences. (ft is "first two", s is "string")"""
    # black-30, red-31, green-32, yellow-33, blue-34, magenta-35, cyan-36, white-37
    u = '\u001b'
    numbers = dict([(string,30+n) for n, string in enumerate(('bl','re','gr','ye','blu','ma','cy','wh'))])
    n = numbers[ft]
    return f'{u}[{n}m{s}{u}[0m'

def bgcol(ft, s):
    u = '\u001b'
    numbers = dict([(string,40+n) for n, string in enumerate(('bl','re','gr','ye','blu','ma','cy','wh'))])
    n = numbers[ft]
    return f'{u}[{n}m{s}{u}[0m'

def readfile(path):
    with open(path, 'r', encoding='utf-8') as f:
        if path.endswith('.json'):
            content = json.load(f)
        else:
            content = f.read()
    return content

def writefile(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        if isinstance(content, (dict, list)):
            json.dump(content, f, indent=2)
        else:
            f.write(content)


def embedder_api(strings):
    headers = {
        "Authorization": f"Bearer {openai_key}",
        "Content-Type": "application/json"
    }
    data = {
        "input": strings,
        "model": "text-embedding-ada-002"
    }
    response = requests.post("https://api.openai.com/v1/embeddings", headers=headers, json=data)

    if response.status_code != 200:
        print(vars(response))
        raise Exception
    else:
        print(f'successfully embedded {len(strings)} strings')
    data = response.json()['data']
    return [d['embedding'] for d in data]

class EmbeddingsHandler:
    # stov = string to vector, a dictionary
    # stom = string to metadata, a dictionary
    def __init__(self, stov_path='stov.json', stom_path='stom.json'):
        self.stov_path = stov_path
        self.stom_path = stom_path
        self.load()

    def save(self):
        writefile(self.stov_path, self.stov)
        writefile(self.stom_path, self.stom)
    def load(self):
        self.stov = readfile(self.stov_path) if os.path.exists(self.stov_path) else {}
        self.stom = readfile(self.stom_path) if os.path.exists(self.stom_path) else {}
    def clear(self):
        writefile(self.stov_path, {})
        writefile(self.stom_path, {})
        self.load()

    def update_database(self, string_to_metadata_dict):
        bfolder = 'embdata_backup'
        if not os.path.isdir(bfolder):
            os.mkdir(bfolder)
        writefile(bfolder+'/'+str(time.time()).replace('.','_')+'.json',string_to_metadata_dict)
        strings = string_to_metadata_dict.keys()
        to_embed = [s for s in strings if s not in self.stov.keys()]
        print(f'will embed {len(to_embed)}/{len(strings)} strings')

        if to_embed != []:
            per_call = 50
            for i in range(0, len(to_embed), per_call):
                vectors = embedder_api(to_embed[i:i+per_call])
                for n, v in enumerate(vectors):
                    idx = i+n
                    string = to_embed[idx]
                    metadata = string_to_metadata_dict[string]

                    self.stov[string] = v
                    self.stom[string] = metadata

            self.save()

    def search(self, q):
        self.load()
        query_emb = embedder_api([q])
        strings = list(self.stov.keys())
        vectors = list(self.stov.values())

        triplets = sorted(
            [(
                n,
                strings[n],
                float(np.dot(query_emb,vectors[n])[0])
            ) for n in range(len(strings))],
            key=lambda triplet: triplet[2],
            reverse=True
        )
        return triplets  # to get metadata youd need to use self.stom[string]

def vidinfo(url):
    video = youtubesearchpython.Video.get(
        url,
        mode=youtubesearchpython.ResultMode.json,
        get_upload_date=True
    )

    to_return = {
        'title': video['title'],
        'seconds': video['duration']['secondsText'],
        'views': video['viewCount']['text'],
        'description': video['description'],
        'upload_date': video['uploadDate'],
        'category': video['category'],
        'keywords': video['keywords'],
        'link': video['link'],
        'channelname': video['channel']['name'],
        'channellink': video['channel']['link'],
        'channelid': video['channel']['id'],
    }

    return to_return

def channelvids(vid_url):
    channel_id = vidinfo(vid_url)['channelid']
    print(channel_id)
    playlist = youtubesearchpython.Playlist(youtubesearchpython.playlist_from_channel_id(channel_id))

    while playlist.hasMoreVideos:
        playlist.getNextVideos()

    return playlist.videos

def teststuff():
    dwarkesh_vid = 'https://www.youtube.com/watch?v=-VeZp2d7mDs'
    vids = channelvids(dwarkesh_vid)  # all videos on his channel

    def transcript(v):
        try:
            t = get_transcript(v['link'])
            writefile('test.json', list(t))
        except:
            print(col('re', f'sorry couldnt get a transcript for {v["title"]} at {v["link"]}'))
            writefile('test.json', f'sorry couldnt get a transcript for {v["title"]} at {v["link"]}')

    def info(v):
        info = vidinfo(v['link'])
        writefile('test.json', info)

    def comments(v):
        # not implemented yet
        writefile('test.json', get_comments(v['link']))

    d = {
        'transcript': [transcript, 'get a transcript of the video, write to test.json'],
        'info': [info, 'get info of the video, write to test.json'],
        'next': [lambda: None, 'go to the next video in the list']
    }

    for v in vids:
        print(json.dumps(v,indent=2))
        print('---')
        print()
        print('\n'.join([
            col('ma','write one of these commands:'),
            *[f'{col("cy",k)}: {v[1]}' for k,v in d.items()]
        ]))
        while True:
            i = input('> ')
            if i == 'next':
                break
            elif i in d:
                func = d[i][0]
                func(v)
                break
            else:
                print(col('re', 'invalid input'))

def emb_cli():
    expl = '\n'.join([
        'just write a link and itll add that video',
    ])
    print(col('gr', expl))
    while True:
        i = input('> ')

        if 'youtube.com' not in i:
            print(col('re', 'youtube.com not in input'))
        else:
            embed_video(i)

def grab_playlist(pl):
    playlist = pl
    while playlist.hasMoreVideos:
        playlist.getNextVideos()

    return playlist.videos

def jprint(obj):
    print(json.dumps(obj,indent=2))

"""url = 'https://www.youtube.com/playlist?list=PLYpZzg5x9QczXFsI-0G5z6npJl9vqymHW'
pl = youtubesearchpython.Playlist(url)
print(json.dumps(grab_playlist(pl)[0],indent=2))
jprint(youtubesearchpython.Playlist.getInfo(url))
"""

def embed_playlist(url):
    plinfo = youtubesearchpython.Playlist.getInfo(url)
    jprint(plinfo)
    pl = grab_playlist(
        youtubesearchpython.Playlist(url)
    )
    print(f'got playlist. it has {len(pl)} videos.')
    tags = [
        'youtube',
        'playlist',
        plinfo['title'],
    ]
    print(col('ma', 'first doing prep.'))
    while True:
        print('\n'.join([
            f'these tags will be used for each video in the playlist. write {col("cy","embed")} to embed, or write {col("cy", "something else")} to add it as a tag, or write {col("cy", "--tag")} to delete it',
            str(tags),
        ]))
        i = input('> ')
        if i == 'embed':
            break
        elif i.startswith('--'):
            todel = i[2:]
            if todel in tags:
                tags.pop(tags.index(todel))
                print(col('gr', f'removed "{todel}"'))
            else:
                print(col('re', f'{todel} not in tags.'))
        else:
            tags.append(i)
            print(col('gr', f'added "{i}"'))

    print(col('ma', 'on to embedding.'))

    function_names = []

    class Item:
        def __init__(self, item):
            self.vidinfo = vidinfo(item['link'])
        
    for n, item in enumerate(pl):
        jprint(item)

        print('\n'.join([
            col('ma', 'lets create some functions to turn this into a database item.'),
            'current functions:',
            str(function_names),
        ]))
        while True:
            pass

def emb_pickone(query, options, count=1):
    assert type(query) == str
    assert type(options) == list
    vectors = embedder_api([query]+options)
    query_emb = vectors[0]
    options_embs = vectors[1:]

    triplets = sorted(
        [(
            n,
            options[n],
            np.dot(query_emb,options_embs[n])
        ) for n in range(len(options))],
        key=lambda triplet: triplet[2],
        reverse=True
    )
    if count == 1:
        idx = triplets[0][0]
        return options[idx]
    elif count > 1:
        top = []
        for t in triplets[:count]:
            idx = t[0]
            top.append(options[idx])
        return top
    else:
        raise ValueError

def t_to_s(t):
    h, m, s = t.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)
def s_to_t(s):
    h = s // 3600
    s -= h * 3600
    m = s // 60
    s -= m * 60
    return f'{h}:{m}:{s}'

def open_chrome_tab(url):
    #import webbrowser

    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))
    webbrowser.get('chrome').open_new_tab(url)

#embed_playlist('https://www.youtube.com/playlist?list=PLYpZzg5x9QczXFsI-0G5z6npJl9vqymHW')

def video_dataset(folder, url):
    if not os.path.isdir(folder):
        os.mkdir(folder)
    eh = EmbeddingsHandler(
        f'{folder}/stov.json',
        f'{folder}/stom.json'
    )
    # grab transcript
    tpath = f'{folder}/transcript.json'
    if os.path.exists(tpath):
        transcript = readfile(tpath)
    else:
        transcript = get_transcript(url)
        writefile(tpath, transcript)
    # grab info
    ipath = f'{folder}/info.json'
    if os.path.exists(ipath):
        info = readfile(ipath)
    else:
        info = vidinfo(url)
        writefile(ipath, info)

    class Subset:
        def __init__(self):
            self.items = []

        def convert_self(self):
            first = self.items[0]
            last = self.items[-1]
            duration = last['start']+last['duration']-first['start']
            timelink = self.get_timelink()

            string = '\n'.join([i['text'] for i in self.items])
            metadata = {
                'link': timelink,
                'duration': duration,
            }
            return string, metadata

        def isdone(self):
            # if this returns true, it means the subset is "full"

            def checkduration():
                minlength = 60
                first = self.items[0]
                last = self.items[-1]
                l = last['start']+last['duration']-first['start']
                return l >= minlength
            def checklength():
                minlength = 500
                return len('\n'.join([i['text'] for i in self.items])) >= minlength
            def positive_negative():
                pos = 'something alarming about dangerous artificial intelligence'
                neg = 'something about math'
                query = '\n'.join([i['text'] for i in self.items])

                highest = emb_pickone(
                    query,
                    [pos, neg]
                )
                return highest == pos

            checkers = {
                'time': checkduration,
                'string': checklength,
                'embedding': positive_negative,
            }
            checker = checkers['time']

            return checker()

        def add(self, item):
            self.items.append(item)

        def __repr__(self):
            return json.dumps(self.items, indent=2)

        def get_timelink(self):
            vid_id = url.partition('v=')[2].partition('&ab_channel')[0]
            t = int(self.items[0]['start'])
            link = f'youtu.be/{vid_id}?t={t}'
            return link

    all_subsets = []
    cur_subset = Subset()
    for n, item in enumerate(transcript):
        cur_subset.add(item)
        if cur_subset.isdone():
            all_subsets.append(cur_subset)
            cur_subset = Subset()

    # now that the transcript portions are gathered, create a database
    pairs = []
    for s in all_subsets:
        string, metadata = s.convert_self()
        pairs.append((string,metadata))
    eh.update_database({s:m for s,m in pairs})

    def highlight_relevant_line(full, query, count=1):
        assert len(full) > len(query)
        color = 'cy'
        lines = full.split('\n')
        if count == 1:
            relevant = emb_pickone(
                query,
                lines,
            )
            return full.replace(relevant, col(color, relevant))
        elif count > 1:
            top_few = emb_pickone(
                query,
                lines,
                count,
            )
            assert count == len(top_few)
            for s in top_few:
                full = full.replace(s, col(color, s))
            return full
        else:
            raise ValueError

    # start cli to test and search inside the database
    while True:
        i = input('query: ')
        print(col('ma', i))
        words = []
        for portion in i.split(', '):
            for w in portion.split(', '):
                words.append(w)
        print(f'words:', col('cy', str(words)))
        res = eh.search(i)
        for idx, r in enumerate(res[:3]):
            score = r[2]
            string = r[1]
            print(f'{col("ma",idx)}. {score}')
            """# highlight each word in the result results that matches the query.
            for word in words:
                string = string.replace(word, col('cy', word))"""
            # highlight the 3 most relevant lines, inside the transcript, relative to the query.
            highlighted = highlight_relevant_line(string, i, 3)
            print(highlighted)
            #print(string)
            print(eh.stom[r[1]])
            print()
        while True:
            i = input(f'type a {col("cy","number")} to {col("cy","play")} the video at that location, or {col("cy","q")} to write a new search term. > ')
            if not i in ['0','1','2','q']:
                print(col('re', 'wrong input.'))
            elif i == 'q':
                break
            else:
                r = res[int(i)]
                link = eh.stom[r[1]]['link']
                open_chrome_tab(link)

if 0:  # for showing that embedding a youtube video is practically free.
    url = 'https://www.youtube.com/watch?v=oDyviiN4NVo&t=861s&ab_channel=DwarkeshPatel' # the grant sanderson episode
    transcript = get_transcript(url)
    fullt = '\n'.join([i['text'] for i in transcript])
    print(fullt)
    cost = len(fullt.split()) * 1.5 /1000 *0.0001  # https://openai.com/pricing, doing wordcount*1.5 to approximate token count
    print(cost)  # 0.0025 dollars to embed the full transcript
    exit()

video_dataset('eliezer', 'https://www.youtube.com/watch?v=41SUp-TRVlg')

