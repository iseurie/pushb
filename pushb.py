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
                            headers={'Access-Token': api_key},
                            data=dumps(fields))
    payload = await got.json()
    await session.post(payload['upload_url'],
                       data={fname: aiofiles.open(path, 'rb')})
    payload.pop('upload_url')
    return payload


async def mkpush(api_key, session, **kwargs):
    push = {}
    push.update(**kwargs)
    return await session.post(api_root + 'pushes',
                              headers={'Access-Token': api_key},
                              data=dumps(push))


async def push_file(api_key, session, path, **kwargs):
    fparams = await upload_file(session, path)
    mkpush(api_key, session, fparams, type='file')


if __name__ == "__main__":
    curlp = __flag('-F', '--no-files')
    verbose = __flag('-v', '--verbose')
    API_KEY = os.environ.get('PUSHB_API_KEY')

    if API_KEY is None:
        sys.stderr.write("please specify `PUSHB_API_KEY`\n")
        sys.exit(1)

    firstarg = sys.argv[1] if len(sys.argv) > 1 else None
    sys.argv = sys.argv[0] + sys.argv[2:]
    if not firstarg == 'upload' or firstarg == 'u':
        got = requests.get(api_root + 'pushes',
                           params={'limit': rdcount()},
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
                    curlfuts = asyncio.gather(curl_file(session, **to_curl))
                    task = asyncio.Task(curlfuts)
                    asyncio.get_event_loop().create_task(asyncio.Task(curlfuts))
    else:
        from urllib.parse import urlparse
        with aiohttp.ClientSession() as session:
            for i, arg in enumerate(sys.argv[2:]):
                articles = arg.split(':', 3)
                if len(articles) == 1:
                    rider = articles
                    title = body = ''
                if len(articles) == 2:
                    title, body = articles
                    rider = None
                elif len(articles) == 3:
                    # tagged file or url
                    title, body, rider = articles

                push = {'title': title,
                        'body': body}
                if rider != None:
                    if os.path.exists(rider):
                        push_file(rider)
                    else:
                        if len(rider.split('://', 1)) != 2:
                            rider = 'https://' + rider
                        try:
                            urlparse(rider)
                        except Exception as what:
                            sys.stderr.write(
                                "Invalid netloc in argument position #{}: {}\n"
                                .format(i, what))
                            continue
                        push.update({'type': 'link',
                                     'url': rider})
                else:
                    push.update({'type': 'note'})

                mkpush(API_KEY, session, **push)
