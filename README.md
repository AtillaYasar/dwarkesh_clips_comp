# turning a youtube video into a vector search engine

# DEMO
https://youtu.be/Q5SWOM0yhmM

# dwarkesh_clips_comp
I'll put some code here that I will write or copypaste from elsewhere, that could help people in this competition.

https://twitter.com/dwarkesh_sp/status/1730630354523091056

this is in the spirit of "let's help the competition by giving away the one advantage i may have had (coding ability), ensuring my lazy broke ass definitely doesnt win any money". it's an interesting kind of philosophy :p

# outdated stuff:
- main_oudated.py
  + screenshot basically sums up current functionality. it just iterates over the list of all of dwarkesh's videos, shows them one at a time (screenshot showing https://www.youtube.com/watch?v=-VeZp2d7mDs&list=UUXl4i9dYBrFOabk0xGmbkRA&index=1&pp=iAQB), and lets you do stuff with them. i guess it's not useful yet for non-coders.
![Screenshot_9](https://github.com/AtillaYasar/dwarkesh_clips_comp/assets/112716905/1fc04976-17cf-425b-8ae6-44298d038ac7)
- embstuff_outdated.py
  + you can use this to create, update, and search over, a small text-embeddings database, using openai's embeddings endpoint. (also has an example of a function that creates an embedding for a single youtube video, and adds metadata).  
*small*, because it's (very clearly) not optimized for efficiency. but should be fine for the purpose of this competition.
