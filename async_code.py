def set_init_data(self):
    with open(os.path.join(settings.BASE_DIR, 'companies_data.json'), 'r') as init_data:
        companies = json.load(init_data)
        try:
            for company in companies:
                symbol = self.add_prefix_to_symbol(settings.REDIS_PREFIX, company.get('symbol').lower())
                future_0 = AppRequest('ZADD', settings.REDIS_LEADERBOARD, {symbol: company.get('marketCap')})
                AppResponse(future_0)
                future_1 = AppRequest('HSET', symbol, 'company', company.get('company'))
                AppResponse(future_1)
                future_2 = AppRequest('HSET', symbol, 'country', company.get('country'))
                AppResponse(future_2)
        except ConnectionError:
            if settings.REDIS_URL:
                error_message = f'Redis connection time out to {settings.REDIS_URL}.'
            else:
                error_message = f'Redis connection time out to {settings.REDIS_HOST}:{settings.REDIS_PORT}.'
            logger.error(error_message)
            return