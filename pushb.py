#!/usr/bin/env python3

import requests
import os
import sys
import asyncio
import aiohttp
import aiofiles
from json import dumps
from functools import partial, reduce
from operator import add

api_root = 'https://api.pushbullet.com/v2/'


async def curl_file(session, path, uri):
    fp = aiofiles.open(path, mode='w')
    got = await session.get(uri, headers={'Access-Token': API_KEY})
    await fp.write(await got.read())


def __flag(brief: str, full: str) -> bool:
    do_rm = brief in sys.argv or full in sys.argv
    if do_rm:
        rm = brief if brief in sys.argv else full
        i = sys.argv.index(rm)
        sys.argv = [sys.argv[i-1]] + sys.argv[i+1:]
    return do_rm


async def upload_file(api_key, session, path):
    fname = os.path.basename(path)
    fields = {'file_name': fname,
              'file_type': '*/*'}
    got = await session.get(api_root + 'upload-request',
                            headers={'Access-Token': api_key,
                                     'Content-Type': 'application/json'},
                            data=dumps(fields))
    payload = await got.json()
    await session.post(payload['upload_url'],
                       data={fname: aiofiles.open(path, 'rb')})
    payload.pop('upload_url')
    return payload


async def mkpush(api_key, session, **kwargs):
    push = kwargs
    resp = await session.post(api_root + 'pushes',
                              headers={'Access-Token': api_key,
                                       'Content-Type': 'application/json'},
                              data=dumps(push))
    resp.close()


async def push_file(api_key, session, path, **kwargs):
    fparams = await upload_file(api_key, session, path)
    mkpush(api_key, session, fparams, type='file')


if __name__ == "__main__":
    curlp = __flag('-F', '--no-files')
    verbose = __flag('-v', '--verbose')
    stdin_rd = __flag('-', None)
    API_KEY = os.environ.get('PUSHB_API_KEY')

    if API_KEY is None:
        sys.stderr.write("please specify `PUSHB_API_KEY`\n")
        sys.exit(1)

    entries = ' '.join(sys.argv[1:])
    if stdin_rd:
        entries += sys.stdin.read()
    entries = entries.split(',')
    entries = map(str.strip, entries)
    try:
        retrieval_limit = int(entries[0])
    except IndexError:
        uploading = False
        retrieval_limit = 1
    except Exception:
        # cannot be parsed as an integer!
        uploading = True

    if not uploading:
        got = requests.get(api_root + 'pushes',
                           params={'limit': retrieval_limit},
                           headers={'Access-Token': API_KEY})

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
                    curlfuts = asyncio.gather(map(partial(curl_file, session),
                                                  *to_curl))
                    asyncio.get_event_loop().run_until_complete(curlfuts)
    else:
        from urllib.parse import urlparse
        pushfuts = []
        session = aiohttp.ClientSession()
        for i, arg in enumerate(entries):
            push = {}
            articles = arg.split(':', 3)
            if len(articles) == 2:
                # textual note
                title, body = articles
                push.update({'type': 'note'})
                rider = None
            elif len(articles) == 3:
                # tagged file or url
                title, body, rider = articles
            else:
                sys.stderr.write("Invalid tagspec (position #{})\n"
                                 .format(i + 1))
                continue

            push.update({'title': title,
                         'body': body})
            if rider is not None:
                if os.path.exists(rider):
                    pushfuts.append(push_file(API_KEY, session, rider))
                    continue
                else:
                    if len(rider.split('://', 1)) != 2:
                        rider = 'https://' + rider
                    try:
                        parsed_link = urlparse(rider)
                        push.update({'type': 'link',
                                     'url': rider})
                    except Exception:
                        emsg = "Invalid linkspec in argument position #{}\n"
                        sys.stderr.write(emsg.format(i))
                        sys.exit(1)
            pushfuts.append(mkpush(API_KEY, session, **push))
        final = asyncio.gather(*pushfuts)
        asyncio.get_event_loop().run_until_complete(final)
        session.close()
