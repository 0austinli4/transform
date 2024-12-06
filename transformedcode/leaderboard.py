import asyncio
import os
import json
import enum
import logging
from django.conf import settings
from redis import Redis, RedisError, ConnectionError
logger = logging.getLogger(__name__)

class RankSortKeys(enum.Enum):
    ALL = 'all'
    TOP10 = 'top10'
    BOTTOM10 = 'bottom10'

class RedisClient:

    def __init__(self):
        try:
            if settings.REDIS_URL:
                self.redis_client = Redis.from_url(url=settings.REDIS_URL, decode_responses=True)
            else:
                self.redis_client = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, password=settings.REDIS_PASSWORD, db=settings.REDIS_DB, decode_responses=True)
        except RedisError:
            logger.error(f'Redis failed connection to {settings.REDIS_HOST}:{settings.REDIS_PORT}.')
            return

    def set_init_data(self):
        pending_awaits = {*()}
        with open(os.path.join(settings.BASE_DIR, 'companies_data.json'), 'r') as init_data:
            companies = json.load(init_data)
            try:
                for company in companies:
                    symbol = self.add_prefix_to_symbol(settings.REDIS_PREFIX, company.get('symbol').lower())
                    future_0 = AppRequest('ZADD', settings.REDIS_LEADERBOARD, {symbol: company.get('marketCap')})
                    pending_awaits.add(future_0)
                    future_1 = AppRequest('HSET', symbol, 'company', company.get('company'))
                    pending_awaits.add(future_1)
                    future_2 = AppRequest('HSET', symbol, 'country', company.get('country'))
                    pending_awaits.add(future_2)
            except ConnectionError:
                if settings.REDIS_URL:
                    error_message = f'Redis connection time out to {settings.REDIS_URL}.'
                else:
                    error_message = f'Redis connection time out to {settings.REDIS_HOST}:{settings.REDIS_PORT}.'
                logger.error(error_message)
                return
        return (pending_awaits, None)

    @staticmethod
    def add_prefix_to_symbol(prefix, symbol):
        return f'{prefix}:{symbol}'

    @staticmethod
    def remove_prefix_to_symbol(prefix, symbol):
        return symbol.replace(f'{prefix}:', '')

class CompaniesRanks(RedisClient):

    def update_company_market_capitalization(self, amount, symbol):
        pending_awaits = {*()}
        future_0 = AppRequest('ZINCRBY', settings.REDIS_LEADERBOARD, amount, self.add_prefix_to_symbol(settings.REDIS_PREFIX, symbol))
        pending_awaits.add(future_0)
        return (pending_awaits, None)

    def get_ranks_by_sort_key(self, key):
        sort_key = RankSortKeys(key)
        if sort_key is RankSortKeys.ALL:
            return self.get_zrange(0, -1)
        elif sort_key is RankSortKeys.TOP10:
            return self.get_zrange(0, 9)
        elif sort_key is RankSortKeys.BOTTOM10:
            return self.get_zrange(0, 9, False)

    def get_ranks_by_symbols(self, symbols):
        pending_awaits = {*()}
        companies_capitalization = [self.redis_client.zscore(settings.REDIS_LEADERBOARD, self.add_prefix_to_symbol(settings.REDIS_PREFIX, symbol)) for symbol in symbols]
        companies = []
        for index, market_capitalization in enumerate(companies_capitalization):
            companies.append([self.add_prefix_to_symbol(settings.REDIS_PREFIX, symbols[index]), market_capitalization])
        return (pending_awaits, self.get_result(companies))

    def get_zrange(self, start_index, stop_index, desc=True):
        pending_awaits = {*()}
        query_args = {'name': settings.REDIS_LEADERBOARD, 'start': start_index, 'end': stop_index, 'withscores': True, 'score_cast_func': str}
        if desc:
            future_0 = AppRequest('ZREVRANGE')
            pending_awaits.add(future_0)
        else:
            future_1 = AppRequest('ZRANGE')
            pending_awaits.add(future_1)
        companies = AppResponse(future_1)
        pending_awaits.remove(future_1)
        return (pending_awaits, self.get_result(companies, start_index, desc))

    def get_result(self, companies, start_index=0, desc=True):
        pending_awaits = {*()}
        start_rank = int(start_index) + 1 if desc else len(companies) - start_index
        increase_factor = 1 if desc else -1
        results = []
        company_info = AppResponse(future_0)
        pending_awaits.remove(future_0)
        for company in companies:
            symbol = company[0]
            market_cap = company[1]
            future_0 = AppRequest('HGETALL', symbol)
            pending_awaits.add(future_0)
            company_info = AppResponse(future_0)
            pending_awaits.remove(future_0)
            results.append({'company': company_info['company'], 'country': company_info['country'], 'marketCap': market_cap, 'rank': start_rank, 'symbol': self.remove_prefix_to_symbol(settings.REDIS_PREFIX, symbol)})
            start_rank += increase_factor
        return (pending_awaits, json.dumps(results))