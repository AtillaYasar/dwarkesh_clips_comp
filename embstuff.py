from secret_things import openai_key
import numpy as np
import os, sys, json, time, requests
import youtubesearchpython

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
    def __init__(self):
        self.stov_path = 'stov.json'
        self.stom_path = 'stom.json'
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
        writefile('embdata_backup/'+str(time.time()).replace('.','_')+'.json',string_to_metadata_dict)
        strings = string_to_metadata_dict.keys()
        to_embed = [s for s in strings if s not in self.stov.keys()]
        print(f'will embed {len(to_embed)}/{len(strings)} strings')

        if to_embed != []:
            per_call = 50
            for i in range(0, len(to_embed), per_call):
                vectors = embedder_api(to_embed[i:i+per_call])
                for n, v in enumerate(vectors):
                    idx = i*per_call + n
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

def embed_video(url, extra_tags=[]):
    eh = EmbeddingsHandler()
    v = vidinfo(url)
    lines = []
    for item in [
        f'title: {v["title"]}',
        f'description: {v["description"]}',
        f'channelname: {v["channelname"]}',
    ]:
        lines.append(item)
    
    string = '\n'.join(lines)
    meta = {
        'tags': ['youtube'] + extra_tags,
        'link': v['link'],
        'channel': v['channelname'],
    }
    eh.update_database({string:meta})
