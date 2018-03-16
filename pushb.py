#!/usr/bin/env python3

import requests
import os
import sys
import asyncio
import aiohttp
import aiofiles
from json import dumps

api_root = 'https://api.pushbullet.com/v2/'

def rdcount():
    try:
        n = int(sys.argv[1])
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        return n
    except IndexError:
        return 1
    except ValueError:
        sys.stderr.write('Count must be an integer\n')
        sys.exit(1)


async def curl_file(session, path, uri):
    fp = aiofiles.open(path, mode='w')
    got = await session.get(uri, headers={'Access-Token': token})
    await fp.write(await got.read())


def __flag(brief: str, full: str) -> bool:
    do_rm = brief in sys.argv or full in sys.argv
    if do_rm:
        rm = brief if brief in sys.argv else full
        i = sys.argv.index(rm)
        sys.argv = [sys.argv[i-1]] + sys.argv[i+1:]
    return do_rm


async def upload_file(session, path):
    got = await session.get(api_root + 'upload-request',
                            headers={'Access-Token': token})

    payload = await got.json()

if __name__ == "__main__":
    curlp = __flag('-F', '--no-files')
    verbose = __flag('-v', '--verbose')
    token = os.environ.get('PUSHB_API_KEY')

    if token is None:
        sys.stderr.write("please specify `PUSHB_API_KEY`\n")
        sys.exit(1)


    if not sys.argv[1] == 'u' | sys.argv[1] == 'upload':
        got = requests.get(api_root + 'pushes',
                           params={'limit': rdcount()},
                           headers={'Access-Token': token})

        pushes = got.json()['pushes']

        summaries = {'link': '{url}',
                     'note': '{title}: {body}',
                     'file': '{file_name}'}

        for push in pushes:
            push['body'] = push.get('body', '')
            push['title'] = push.get('title', '')
            if not verbose:
                print(summaries[push['type']].format(**push))
            else:
                print(dumps(push))
            if curlp and push['type'] == 'file':
                to_curl = (map(lambda x: push[x],
                               ('file_name', 'file_url')))
                with aiohttp.ClientSession() as session:
                    curlfuts = asyncio.gather(curl_file(session, **to_curl))
                    task = asyncio.Task(curlfuts)
                    asyncio.get_event_loop().create_task(asyncio.Task(curlfuts))
    else:
        
