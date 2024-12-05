import asyncio
import redis
import re
import settings
r = settings.r

class Timeline:

    def page(self, page):
        pending_awaits = {*()}
        _from = (page - 1) * 10
        _to = page * 10
        posts = []
        future_0 = AppRequest('LRANGE', 'timeline', _from, _to)
        pending_awaits.add(future_0)
        async_iter_0 = AppResponse(future_0)
        pending_awaits.remove(future_0)
        for post_id in async_iter_0:
            posts.append(Post(post_id))
        return (pending_awaits, posts)

class Model(object):

    def __init__(self, id):
        self.__dict__['id'] = id

    def __eq__(self, other):
        return self.id == other.id

    def __setattr__(self, name, value):
        pending_awaits = {*()}
        if name not in self.__dict__:
            klass = self.__class__.__name__.lower()
            key = '%s:id:%s:%s' % (klass, self.id, name.lower())
            future_0 = AppRequest('SET', key, value)
            pending_awaits.add(future_0)
        else:
            self.__dict__[name] = value
        return (pending_awaits, None)

    def __getattr__(self, name):
        pending_awaits = {*()}
        if name not in self.__dict__:
            klass = self.__class__.__name__.lower()
            future_0 = AppRequest('GET', '%s:id:%s:%s' % (klass, self.id, name.lower()))
            pending_awaits.add(future_0)
            v = AppResponse(future_0)
            pending_awaits.remove(future_0)
            if v:
                v = AppResponse(future_0)
                pending_awaits.remove(future_0)
                return (pending_awaits, v)
            raise AttributeError("%s doesn't exist" % name)
        else:
            self.__dict__[name] = value
        return (pending_awaits, None)

class User(Model):

    @staticmethod
    def find_by_username(username):
        pending_awaits = {*()}
        future_0 = AppRequest('GET', 'user:username:%s' % username)
        pending_awaits.add(future_0)
        _id = AppResponse(future_0)
        pending_awaits.remove(future_0)
        if _id is not None:
            _id = AppResponse(future_0)
            pending_awaits.remove(future_0)
            return (pending_awaits, User(int(_id)))
        else:
            return (pending_awaits, None)
        return (pending_awaits, None)

    @staticmethod
    def find_by_id(_id):
        pending_awaits = {*()}
        future_0 = AppRequest('EXISTS', 'user:id:%s:username' % _id)
        pending_awaits.add(future_0)
        async_cond_0 = AppResponse(future_0)
        pending_awaits.remove(future_0)
        if async_cond_0:
            return (pending_awaits, User(int(_id)))
        else:
            return (pending_awaits, None)
        return (pending_awaits, None)

    @staticmethod
    def create(username, password):
        pending_awaits = {*()}
        future_0 = AppRequest('INCR', 'user:uid')
        pending_awaits.add(future_0)
        future_1 = AppRequest('GET', 'user:username:%s' % username)
        pending_awaits.add(future_1)
        async_cond_0 = AppResponse(future_1)
        pending_awaits.remove(future_1)
        if not async_cond_0:
            future_2 = AppRequest('SET', 'user:id:%s:username' % user_id, username)
            pending_awaits.add(future_2)
            future_3 = AppRequest('SET', 'user:username:%s' % username, user_id)
            pending_awaits.add(future_3)
            salt = settings.SALT
            future_4 = AppRequest('SET', 'user:id:%s:password' % user_id, salt + password)
            pending_awaits.add(future_4)
            future_5 = AppRequest('LPUSH', 'users', user_id)
            pending_awaits.add(future_5)
            user_id = AppResponse(future_0)
            pending_awaits.remove(future_0)
            return (pending_awaits, User(user_id))
        return (pending_awaits, None)

    def posts(self, page=1):
        pending_awaits = {*()}
        _from, _to = ((page - 1) * 10, page * 10)
        future_0 = AppRequest('LRANGE', 'user:id:%s:posts' % self.id, _from, _to)
        pending_awaits.add(future_0)
        posts = AppResponse(future_0)
        pending_awaits.remove(future_0)
        if posts:
            future_1 = AppRequest('LRANGE', 'timeline', _from, _to)
            pending_awaits.add(future_1)
            return_posts = []
            async_iter_0 = AppResponse(future_1)
            pending_awaits.remove(future_1)
            for post_id in async_iter_0:
                return_posts.append(Post(post_id))
            return (pending_awaits, return_posts)
        return (pending_awaits, [])

    def timeline(self, page=1):
        pending_awaits = {*()}
        _from, _to = ((page - 1) * 10, page * 10)
        future_0 = AppRequest('LRANGE', 'user:id:%s:timeline' % self.id, _from, _to)
        pending_awaits.add(future_0)
        timeline = AppResponse(future_0)
        pending_awaits.remove(future_0)
        if timeline:
            future_1 = AppRequest('LRANGE', 'timeline', _from, _to)
            pending_awaits.add(future_1)
            return_posts = []
            async_iter_0 = AppResponse(future_1)
            pending_awaits.remove(future_1)
            for post_id in async_iter_0:
                return_posts.append(Post(post_id))
            return (pending_awaits, return_posts)
        return (pending_awaits, [])

    def mentions(self, page=1):
        pending_awaits = {*()}
        _from, _to = ((page - 1) * 10, page * 10)
        future_0 = AppRequest('LRANGE', 'user:id:%s:mentions' % self.id, _from, _to)
        pending_awaits.add(future_0)
        mentions = AppResponse(future_0)
        pending_awaits.remove(future_0)
        if mentions:
            future_1 = AppRequest('LRANGE', 'timeline', _from, _to)
            pending_awaits.add(future_1)
            async_iter_0 = AppResponse(future_1)
            pending_awaits.remove(future_1)
            for post_id in async_iter_0:
                return_posts.append(Post(post_id))
            return (pending_awaits, return_posts)
        return (pending_awaits, [])

    def add_post(self, post):
        pending_awaits = {*()}
        future_0 = AppRequest('LPUSH', 'user:id:%s:posts' % self.id, post.id)
        pending_awaits.add(future_0)
        future_1 = AppRequest('LPUSH', 'user:id:%s:timeline' % self.id, post.id)
        pending_awaits.add(future_1)
        future_2 = AppRequest('SADD', 'posts:id', post.id)
        pending_awaits.add(future_2)
        return (pending_awaits, None)

    def add_timeline_post(self, post):
        pending_awaits = {*()}
        future_0 = AppRequest('LPUSH', 'user:id:%s:timeline' % self.id, post.id)
        pending_awaits.add(future_0)
        return (pending_awaits, None)

    def add_mention(self, post):
        pending_awaits = {*()}
        future_0 = AppRequest('LPUSH', 'user:id:%s:mentions' % self.id, post.id)
        pending_awaits.add(future_0)
        return (pending_awaits, None)

    def follow(self, user):
        pending_awaits = {*()}
        if user == self:
            return (pending_awaits, None)
        else:
            future_0 = AppRequest('SADD', 'user:id:%s:followees' % self.id, user.id)
            pending_awaits.add(future_0)
            pending_awaits_add_follower, _ = user.add_follower(self)
            pending_awaits.update(pending_awaits_add_follower)
        return (pending_awaits, None)

    def stop_following(self, user):
        pending_awaits = {*()}
        future_0 = AppRequest('SREM', 'user:id:%s:followees' % self.id, user.id)
        pending_awaits.add(future_0)
        pending_awaits_remove_follower, _ = user.remove_follower(self)
        pending_awaits.update(pending_awaits_remove_follower)
        return (pending_awaits, None)

    def following(self, user):
        pending_awaits = {*()}
        future_0 = AppRequest('SISMEMBER', 'user:id:%s:followees' % self.id, user.id)
        pending_awaits.add(future_0)
        async_cond_0 = AppResponse(future_0)
        pending_awaits.remove(future_0)
        if async_cond_0:
            return (pending_awaits, True)
        return (pending_awaits, False)

    @property
    def followers(self):
        pending_awaits = {*()}
        future_0 = AppRequest('SMEMBERS', 'user:id:%s:followers' % self.id)
        pending_awaits.add(future_0)
        followers = AppResponse(future_0)
        pending_awaits.remove(future_0)
        if followers:
            future_1 = AppRequest('LRANGE', 'timeline', _from, _to)
            pending_awaits.add(future_1)
            return_posts = []
            async_iter_0 = AppResponse(future_1)
            pending_awaits.remove(future_1)
            for user_id in async_iter_0:
                return_posts.append(User(int(user_id)))
            return (pending_awaits, return_posts)
        return (pending_awaits, [])

    @property
    def followees(self):
        pending_awaits = {*()}
        future_0 = AppRequest('SMEMBERS', 'user:id:%s:followees' % self.id)
        pending_awaits.add(future_0)
        followees = AppResponse(future_0)
        pending_awaits.remove(future_0)
        if followees:
            future_1 = AppRequest('LRANGE', 'timeline', _from, _to)
            pending_awaits.add(future_1)
            return_posts = []
            async_iter_0 = AppResponse(future_1)
            pending_awaits.remove(future_1)
            for user_id in async_iter_0:
                return_posts.append(User(int(user_id)))
            return (pending_awaits, return_posts)
        return (pending_awaits, [])

    @property
    def tweet_count(self):
        pending_awaits = {*()}
        future_0 = AppRequest('LLEN', 'user:id:%s:posts' % self.id)
        pending_awaits.add(future_0)
        async_return_0 = AppResponse(future_0)
        pending_awaits.remove(future_0)
        return (pending_awaits, async_return_0 or 0)

    @property
    def followees_count(self):
        pending_awaits = {*()}
        future_0 = AppRequest('SCARD', 'user:id:%s:followees' % self.id)
        pending_awaits.add(future_0)
        async_return_0 = AppResponse(future_0)
        pending_awaits.remove(future_0)
        return (pending_awaits, async_return_0 or 0)

    @property
    def followers_count(self):
        pending_awaits = {*()}
        future_0 = AppRequest('SCARD', 'user:id:%s:followers' % self.id)
        pending_awaits.add(future_0)
        async_return_0 = AppResponse(future_0)
        pending_awaits.remove(future_0)
        return (pending_awaits, async_return_0 or 0)

    def add_follower(self, user):
        pending_awaits = {*()}
        future_0 = AppRequest('SADD', 'user:id:%s:followers' % self.id, user.id)
        pending_awaits.add(future_0)
        return (pending_awaits, None)

    def remove_follower(self, user):
        pending_awaits = {*()}
        future_0 = AppRequest('SREM', 'user:id:%s:followers' % self.id, user.id)
        pending_awaits.add(future_0)
        return (pending_awaits, None)

class Post(Model):

    @staticmethod
    def create(user, content):
        pending_awaits = {*()}
        future_0 = AppRequest('INCR', 'post:uid')
        pending_awaits.add(future_0)
        post_id = AppResponse(future_0)
        pending_awaits.remove(future_0)
        post = Post(post_id)
        post.content = content
        post.user_id = user.id
        pending_awaits_add_post, _ = user.add_post(post)
        pending_awaits.update(pending_awaits_add_post)
        future_1 = AppRequest('LPUSH', 'timeline', post_id)
        pending_awaits.add(future_1)
        for follower in user.followers:
            follower.add_timeline_post(post)
        mentions = re.findall('@\\w+', content)
        for mention in mentions:
            u = User.find_by_username(mention[1:])
            if u:
                pending_awaits_add_mention, _ = u.add_mention(post)
                pending_awaits.update(pending_awaits_add_mention)
        return (pending_awaits, None)

    @staticmethod
    def find_by_id(id):
        pending_awaits = {*()}
        future_0 = AppRequest('SISMEMBER', 'posts:id', int(id))
        pending_awaits.add(future_0)
        async_cond_0 = AppResponse(future_0)
        pending_awaits.remove(future_0)
        if async_cond_0:
            return (pending_awaits, Post(id))
        return (pending_awaits, None)

    @property
    def user(self):
        pending_awaits = {*()}
        return (pending_awaits, User.find_by_id(r.get('post:id:%s:user_id' % self.id)))

def main():
    pass
if __name__ == '__main__':
    main()
    return (pending_awaits, None)