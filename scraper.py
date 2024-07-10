
#!/usr/bin/env python3

import asyncio
import aiohttp
import logging
import pandas as pd
import sqlite3
import os


if os.path.exists('urls.db'):
    os.rename('urls.db', 'urls_old.db')

conn = sqlite3.connect('urls.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS urls (id INTEGER PRIMARY KEY, site TEXT, board TEXT, file TEXT, comment TEXT, ext TEXT)''')
conn.commit()



columns = ['site', 'board', 'file', 'ext', 'nsfw' ,'misc']
all_chans = pd.DataFrame(columns = columns)

def insertFile(site,board,file,ext,nsfw,misc):
    com = "no comment"
    if 'com' in misc:
        com = misc['com'][:1400]

    c.execute("INSERT INTO urls (site, board, file, comment, ext) VALUES (?,?,?,?,?)", (site, board, file, com, ext))
    conn.commit()
    all_chans.loc[len(all_chans)] = {
        'site': site,
        'board' : board,
        'file' : file,
        'ext': ext,
        'nsfw': nsfw,
        'misc' : misc
    } 



logging.basicConfig(level=logging.INFO)

class AsyncAPICaller:
    def __init__(self,base_url):
        self.base_url = base_url

    async def get_data(self,session,endpoint):
        url = f'{self.base_url}{endpoint}'
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                if 'application/json' in response.headers['Content-Type']:
                        return await response.json()
                else:
                    logging.error(f'Response from {url} is not JSON. Content-Type: {response.headers["Content-Type"]}')
                    return None
        except aiohttp.ClientConnectionError as err:
            logging.error(f'HTTP error occurred: {err}')
        except Exception as err:
            logging.error(f'Error occurred: {err}')
        return None

    async def call_api(self,endpoint):
        await asyncio.sleep(1.5)
        async with aiohttp.ClientSession() as session:
            data = await self.get_data(session,endpoint)
            if data:
                logging.info(f'Successfully fetched data from {endpoint}')
                return data
            else:
                logging.error(f'Failed to fetch data from {endpoint}')
                return None          



async def getCatalog(base_url, boards, partial_endpoint,site, url_pattern, params,ext_key, tim_key, extra_stuff):
    
    print("doing: ", site)

    for board in boards:
        caller = AsyncAPICaller(base_url)
        print(f"current board: {board}")
        endpoint = board + partial_endpoint
        result = await caller.call_api(endpoint)

        if result:
            process_generic_catalog(site,board,url_pattern, params, ext_key, tim_key, extra_stuff, result)


def validExtCheck(ext):

    ext_lower = ext.lower()

    return (ext_lower == ".webm" or ext_lower == ".gif" or ext_lower == ".mp4" or ext_lower == ".mov" or ext_lower == ".avi" or ext_lower == ".flv" or ext_lower == ".wmv") and (ext_lower != "deleted")
    

def extractData(data, site, board, nsfw ,url_pattern, params, ext_key, tim_key):

    if (ext_key in data) and (tim_key in data) and validExtCheck(data[ext_key]):

        if "board" in params:
            params["board"] = board

        cur_tim = str(data[tim_key])
        if "/" in cur_tim:
            cur_tim = cur_tim.split('/')[-1]

        
        params["file"] = cur_tim + data[ext_key]

        file_url = url_pattern.format(**params)


        other_data = {}

        for key in data:
            if key != ext_key and key != tim_key:
                other_data[key] = data[key]

        insertFile(site,board,file_url,data[ext_key],nsfw,other_data)




def process_generic_catalog(site,board, url_pattern, params, ext_key, tim_key, extra_stuff, json_res): 
    for page in json_res:
        if 'threads' in page:
            for thread in page['threads']:
                extractData(thread, site, board, 1 ,url_pattern, params, ext_key, tim_key)
                if extra_stuff in thread:
                    for extra in thread[extra_stuff]:
                        extractData(extra, site, board, 1 ,url_pattern, params, ext_key, tim_key)


async def main():
    fourchan_boards = ['3', 'a', 'aco', 'adv', 'an', 'b', 'bant', 'biz', 'c', 'cgl', 'ck', 'cm', 'co', 'd', 'diy', 'e', 'f', 'fa', 'fit', 'g', 'gd', 'gif', 'h', 'hc', 'his', 'hm', 'hr', 'i', 'ic', 'int', 'jp', 'k', 'lgbt', 'lit', 'm', 'mlp', 'mu', 'n', 'news', 'o', 'out', 'p', 'po', 'pol', 'pw', 'qa', 'qst', 'r', 'r9k', 's', 's4s', 'sci', 'soc', 'sp', 't', 'tg', 'toy', 'trash', 'trv', 'tv', 'u', 'v', 'vg', 'vip', 'vm', 'vmg', 'vp', 'vr', 'vrpg', 'vst', 'vt', 'w', 'wg', 'wsg', 'wsr', 'x', 'xs', 'y']

    lain_boards = ['λ', 'diy', 'sec', 'tech', 'inter', 'lit', 'music', 'vis', 'hum', 'drg', 'zzz', 'layer', 'q', 'r']

    eight_boards = ['qresearch', 'vichan', 'random', 'egy', 'hypno', 'pnd', 'rule34', 'safetytest', 'newsplus', 'midnightriders', 'test', 'cuteboys', 'fur', 'cafechan', 'tingles', 'monster', 'qnotables', 'x', 'g', 'christianity', 'kemono', 'wmafsex', 'warroom', 'biz', 'wulkanoid', 'pacman']


    sushi_boards = ["lounge", "arcade", "kawaii", "kitchen", "tunes", "culture", "silicon", "otaku", "yakuza", "hell"]

    lefty_boards = ["overboard", "sfw", "alt", "leftypol", "siberia", "hobby", "tech", "edu", "games", "anime", "music", "draw", "AKM", "meta", "roulette"]


    vecchio_boards = ['b', 's', 'h', 'a', 'biz', 'cuc', 'mm', 't', 'v', 'pol', 'jira']



    await asyncio.gather(
        getCatalog('https://a.4cdn.org/', fourchan_boards ,'/catalog.json', '4chan', 'https://i.4cdn.org/{board}/{file}', {"board": "null", "file": "null"}, "ext", "tim", 'last_replies'), 
        
        getCatalog('https://lainchan.org/', lain_boards ,'/catalog.json', 'lainchan' ,'https://lainchan.org/{board}/src/{file}', {"board": "null", "file": "null"}, "ext", "tim", 'extra_files'),

        getCatalog('https://8kun.top/', eight_boards ,'/catalog.json', '8kun' ,'https://media.128ducks.com/file_store/{file}', {"file": "null"}, "ext", "tim", 'extra_files'), 

        getCatalog('https://sushigirl.us/', sushi_boards ,'/catalog.json', 'sushigirl' ,'https://sushigirl.us/{board}/src/{file}', {"board": "null", "file": "null"}, "ext", "tim", 'extra_files'),

        getCatalog('https://leftypol.org/', lefty_boards ,'/catalog.json', 'leftypol' ,'https://leftypol.org/{board}/src/{file}', {"board": "null", "file": "null"}, "ext", "tim", 'files'),

        getCatalog('https://vecchiochan.com/', vecchio_boards ,'/catalog.json', 'vecchio' ,'https://vecchiochan.com/external/{board}/src/{file}', {"board": "null", "file": "null"}, "ext", "tim", 'extra_files')

       

    )


if __name__ == '__main__':

    asyncio.run(main())
    all_chans.to_csv('all_chans_three.csv', index=False)
    conn.close()
