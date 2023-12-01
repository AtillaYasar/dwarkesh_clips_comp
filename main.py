import youtubesearchpython
import sys, json, os, time

from colorama import init
init()

from youtube_transcript_api import YouTubeTranscriptApi

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

def vidinfo(url):
    video = youtubesearchpython.Video.get(url, mode = youtubesearchpython.ResultMode.json, get_upload_date=True)

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

    print(f'Videos Retrieved: {len(playlist.videos)}')

    while playlist.hasMoreVideos:
        break
        print('Getting more videos...')
        playlist.getNextVideos()
        print(f'Videos Retrieved: {len(playlist.videos)}')

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

teststuff()
