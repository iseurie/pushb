#!/usr/bin/env python3

import requests
import os
import sys
import asyncio
import aiohttp
from json import dumps
import aiofiles

api_root = 'https://api.pushbullet.com/v2/'


async def curl_file(session, path, uri):
    fp = await aiofiles.open(path, mode='wb')
    stream = await session.get(uri, headers={'Access-Token': API_KEY})
    await fp.write(await stream.read())
    await fp.flush()
    stream.close()


def __flag(brief: str, full: str) -> bool:
    rtn = brief in sys.argv or full in sys.argv
    for v in brief, full:
        sys.argv = filter(v.__ne__, sys.argv)
    sys.argv = list(sys.argv)
    return rtn


async def mkpush(api_key, session, **kwargs):
    push = kwargs
    resp = await session.post(api_root + 'pushes',
                              headers={'Access-Token': api_key,
                                       'Content-Type': 'application/json'},
                              data=dumps(push))
    resp.close()


async def upload_file(api_key, session, path):
    fname = os.path.basename(path)
    fields = {'file_name': fname,
              'file_type': '*/*'}
    got = await session.post(api_root + 'upload-request',
                             headers={'Access-Token': api_key,
                                      'Content-Type': 'application/json'},
                             data=dumps(fields))
    payload = await got.json()
    (await session.post(payload.pop('upload_url'),
                        data={'file': open(path, 'rb')})).close()
    return payload


async def push_file(api_key, session, body, path, **kwargs):
    fparams = await upload_file(api_key, session, path)
    keys = ('title', 'body', 'file_type', 'file_name', 'file_url')
    fparams = {k if k in keys else None: v
               for (k, v) in fparams.items()}
    del fparams[None]
    fparams['type'] = 'file'
    await mkpush(api_key, session, **fparams)


if __name__ == "__main__":
    curlp = not __flag('-F', '--no-files')
    verbose = __flag('-v', '--verbose')
    stdin_rd = __flag('-', None)
    API_KEY = os.environ.get('PUSHB_API_KEY')

    if API_KEY is None:
        sys.stderr.write("please specify `PUSHB_API_KEY`\n")
        sys.exit(1)

    try:
        retrieval_limit = int(sys.argv[1])
    except IndexError:
        retrieval_limit = 1
    except ValueError:
        retrieval_limit = None

    if retrieval_limit is not None:
        entries = ' '.join(sys.argv[1:])
        if stdin_rd:
            entries += sys.stdin.read()
        entries = entries.split(',')
        entries = list(map(str.strip, entries))
 
        cursor = 0
        while cursor is not None:
            getparams = {'Access-Token': API_KEY}
            if cursor != 0:
                getparams['cursor'] = cursor
            got = requests.get(api_root + 'pushes',
                               params=getparams,
                               headers={'Access-Token': API_KEY})
            payload = got.json()
            pushes = payload['pushes']
            cursor = payload.get('cursor', None)

            summaries = {'link': '{url}',
                         'note': '{title}: {body}',
                         'file': '{file_name}'}

            session = None
            curlfuts = []
            for push in pushes:
                push['body'] = push.get('body', '')
                push['title'] = push.get('title', '')
                if not verbose:
                    print(summaries[push['type']].format(**push))
                else:
                    print(dumps(push))
                if curlp and push['type'] == 'file':
                    if session is None:
                        session = aiohttp.ClientSession()
                    props = tuple([push[x] for x in ('file_name', 'file_url')])
                    if os.path.exists("./" + props[0]):
                        sys.stderr.write("{} not downloaded: file exists\n"
                                         .format(props[0]))
                        continue
                    curlfuts.append(curl_file(session, *props))
            looper = asyncio.gather(*curlfuts)
            asyncio.get_event_loop().run_until_complete(looper)
            if session is not None:
                session.close()
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
                sys.stderr.write("Invalid tagspec in argument position #{}\n"
                                 .format(i + 1))
                continue

            push.update({'title': title,
                         'body': body})
            if rider is not None:
                if os.path.exists(rider):
                    pushfuts.append(push_file(API_KEY, session, body, rider))
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
                        sys.stderr.write(emsg.format(i + 1))
                        sys.exit(1)
            pushfuts.append(mkpush(API_KEY, session, **push))
        final = asyncio.gather(*pushfuts)
        asyncio.get_event_loop().run_until_complete(final)
        session.close()
