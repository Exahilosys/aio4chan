## Contents

- 4chan API reader.

## Installing

```
python3 -m pip install aio4chan
```

## Usage

```py
import asyncio
import aiohttp
import aio4chan

loop = asyncio.get_event_loop()

session = aiohttp.ClientSession(loop = loop)

client = aio4chan.Client(session = session, loop = loop)

async def execute():

    """
    Traverse 4chan.
    """

    boards = await client.get_boards()

    # short names
    board_ids = (board.board for board in boards)

    for board_id in board_ids:

        pages = await client.get_threads(board_id)

        # list of pages, each containing threads
        thread_ids = (thread.no for page in pages for thread in page.threads)

        for thread_id in thread_ids:

            # need both board_id and thread_id
            thread = await client.get_thread(board_id, thread_id)

            for post in thread:

                try:

                    # might not exist
                    comment = post.com

                except AttributeError:

                    continue

                # print where we got it, and the comment
                print(board_id, '>', thread_id, '>', post.no, '\n', post.com)

try:

    loop.run_until_complete(execute())

except KeyboardInterrupt:

    pass

finally:

    loop.run_until_complete(session.close())

    loop.close()
```
