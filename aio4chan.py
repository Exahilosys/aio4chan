import asyncio
import aiohttp
import yarl

__version__ = '0.0.0'

__all__ = ('Client',)


class Asset(dict):

    __slots__ = ()

    def _convert(self, value):

        cls = value.__class__

        if cls is dict:

            value = self.__class__(value)

        elif cls is list:

            value = tuple(map(self._convert, value))

        return value

    def _consistent(self, key, old):

        value = self._convert(old)

        if not value is old:

            self.__setitem__(key, value)

        return value

    def __getitem__(self, key):

        value = super().__getitem__(key)

        value = self._consistent(key, value)

        return value

    def __getattr__(self, key):

        try:

            value = self.__getitem__(key)

        except KeyError as error:

            raise AttributeError(*error.args) from None

        return value


class Client:

    """
    Main means of reading the 4chan API.

    Parameters:
        http: bool [True]
            whether to use http or https scheme
        hold: int [1]
            waiting time between requests
            consult https://github.com/4chan/4chan-API#api-rules
        limit: int [8000]
            maximum amount of concurrent requests
            this is to prevent "too many files" exceptions
        session: aiohttp.ClientSession [None]
            used for requesting
            if None, created automatically
        loop: asyncio.AbstractEventLoop [None]
            used and passed whethever applicable
            if None, fetched from asyncio.get_event_loop
    """

    __slots__ = ('_url', '_session', '_hold', '_lock', '_limit', '_loop')

    _base = yarl.URL('http://a.4cdn.org')

    _urls = (_base.with_scheme('https'), _base)

    def __init__(self,
                 http = True,
                 hold = 1,
                 limit = 8000,
                 session = None,
                 loop = None):

        if not loop:

            loop = asyncio.get_event_loop()

        if not session:

            session = aiohttp.ClientSession(loop = loop)

        self._url = self._urls[http]

        self._hold = hold

        self._lock = asyncio.Lock(loop = loop)

        self._limit = asyncio.Semaphore(value = limit, loop = loop)

        self._session = session

        self._loop = loop

    @property
    def url(self):

        """
        Get the yarl.URL used for requests.
        """

        return self._url

    @property
    def session(self):

        """
        Get the aiohttp.ClientSession used for requests.
        """

        return self._session

    @property
    def loop(self):

        """
        Get the event loop used for async operations.
        """

        return self._loop

    async def _comply(self):

        await asyncio.sleep(self._hold, loop = self._loop)

        self._lock.release()

    async def interact(self, route):

        """
        Execute the request.

        Paramters:
            route: str
                base/{route}.json part of the url
            **kwargs: dict
                passed to the request call
        """

        if self._hold > 0:

            await self._lock.acquire()

            self._loop.create_task(self._comply())

        url = self._url.with_path(f'{route}.json')

        await self._limit.acquire()

        try:

            response = await self._session.request('GET', url)

        finally:

            self._limit.release()

        response.raise_for_status()

        payload = await response.json()

        return payload

    async def get_boards(self):

        """
        Get all boards.
        """

        data = await self.interact(f'boards')

        value = tuple(map(Asset, data['boards']))

        return value

    async def get_threads(self, board_id, page = None):

        """
        Get the board's active threads.

        Parameters:
            board_id: str
                board name
            page: int [None]
                board index
                omitting this will return all pages
        """

        route = f'{board_id}/' + (str(page) if page else 'threads')

        data = await self.interact(route)

        value = tuple(map(Asset, data))

        return value

    async def get_archive(self, board_id):

        """
        Get the board's archived threads.

        Parameters:
            board_id: str
                board name
        """

        route = f'{board_id}/archive'

        try:

            data = await self.interact(route)

        except aiohttp.ClientResponseError as error:

            if error.status == 404:

                return ()

            raise

        value = tuple(data)

        return value

    async def get_thread(self, board_id, thread_id):

        """
        Get the board thread's posts.

        Parameters:
            board_id: str
                board name
            thread_id: int
                thread identifier
        """

        route = f'{board_id}/thread/{thread_id}'

        data = await self.interact(route)

        value = tuple(map(Asset, data['posts']))

        return value

    async def get_catalog(self, board_id):

        """
        Get the board's catalog.

        Parameters:
            board_id: str
                board name
        """

        route = f'{board_id}/catalog'

        data = await self.interact(route)

        value = Asset(data)

        return value
