class RedisClient:
    def get_result(self, companies, start_index=0, desc=True):
        dep_vars_queue = deque()
        pending_awaits = {*()}
        start_rank = int(start_index) + 1 if desc else len(companies) - start_index
        increase_factor = 1 if desc else -1
        results = []
        for company in companies:
            symbol = company[0]
            market_cap = company[1]
            future_0 = AppRequest('HGETALL', symbol)
            dep_vars_queue.append(market_cap)
            dep_vars_queue.append(market_cap)
            dep_vars_queue.append(symbol)
            start_rank += increase_factor
        for company in companies:
            company_info = AppResponse(future_0)
            results.append({'company': company_info['company'], 'country': company_info['country'], 'marketCap': dep_vars_queue.popleft(), 'rank': dep_vars_queue.popleft(), 'symbol': self.remove_prefix_to_symbol(settings.REDIS_PREFIX, dep_vars_queue.popleft())})
        return (pending_awaits, json.dumps(results))