#!/usr/bin/python3
import sys
import argparse
import asyncio, aiohttp
import re


# handle args
p = argparse.ArgumentParser()
p.add_argument('-f', '--filename', type=str, required=True, help='input file containing list of hosts to process')
p.add_argument('-x', '--proxy', type=str, help='Specify proxy, (http://127.0.0.1:10809)')
p.add_argument('--max-conn', type=int, default=1000, help='Aiohttp max conn')
p.add_argument('--single-waiting', type=int, default=30, help='Aiohhtp single waiting')
args = p.parse_args()

# read urls
urls = []
with open(args.filename, 'r') as f:
    for line in f.readlines():
        url = line.strip('\r').strip('\n')
        urls.append(url)

succeeded, failed = 0, 0
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
}

def fetch_resp(urllist, proxy=None, max_conn=None, single_waiting=None):

    async def access(session, url):
        global succeeded
        global failed

        for protocol in ['https', 'http']:
            if not re.search('^https?://', url):
                _url = f'{protocol}://{url}'
            else:
                _url = url
            try:
                async with session.get(_url, proxy=proxy, allow_redirects=False) as resp:
                    text = await resp.text()
                    succeeded += 1
                    sys.stdout.write(f'{_url} [{resp.status}]\n')
            except (asyncio.TimeoutError, aiohttp.ClientConnectorCertificateError, aiohttp.ClientConnectionError, aiohttp.ClientOSError, aiohttp.ClientConnectorError, aiohttp.ClientProxyConnectionError, aiohttp.ClientSSLError, aiohttp.ClientConnectorSSLError, aiohttp.ClientPayloadError, aiohttp.ClientResponseError, aiohttp.ClientHttpProxyError, aiohttp.WSServerHandshakeError, aiohttp.ContentTypeError,) as e:
                failed += 1
            except (RuntimeError, UnicodeDecodeError,) as e:
                failed += 1

    async def main():
        timeout = aiohttp.ClientTimeout(total=single_waiting, sock_connect=single_waiting, sock_read=single_waiting)
        connector = aiohttp.TCPConnector(limit=max_conn, verify_ssl=False)

        async with aiohttp.ClientSession(headers=headers, connector=connector, timeout=timeout) as session:
            tasks = []
            for url in urllist:
                tasks.append(asyncio.ensure_future(access(session, url)))
            await asyncio.gather(*tasks)

        sys.stderr.write(f'X/Y is {succeeded}/{failed}\n')

    asyncio.run(main())


if __name__ == '__main__':
    max_conn = args.max_conn
    single_waiting = args.single_waiting
    count = 0
    while count < len(urls):
        sliced = urls[count:count+max_conn]
        fetch_resp(sliced, max_conn=max_conn, single_waiting=single_waiting, proxy=args.proxy)
        count += max_conn