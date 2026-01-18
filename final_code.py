import redis
import re
import settings
r = settings.r

class Timeline:

    def page(self, page):
        pending_awaits = {*()}
        _from = (page - 1) * 10
        _to = page * 10
        return (pending_awaits, [Post(post_id) for post_ids in send_request(session_id, 'LRANGE', 'timeline', _from, _to)])

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
            future_0 = send_request(session_id, 'SET', key, value)
            pending_awaits.add(future_0)
        else:
            self.__dict__[name] = value
        return (pending_awaits, None)

    def __getattr__(self, name):
        pending_awaits = {*()}
        if name not in self.__dict__:
            klass = self.__class__.__name__.lower()
            future_0 = send_request(session_id, 'GET', '%s:id:%s:%s' % (klass, self.id, name.lower()))
            pending_awaits.add(future_0)
            if v:
                v = await_request(session_id, future_0)
                pending_awaits.remove(session_id)
                return (pending_awaits, v)
                v = await_request(session_id, future_0)
            raise AttributeError("%s doesn't exist" % name)
        else:
            self.__dict__[name] = value
        return (pending_awaits, None)

class User(Model):

    @staticmethod
    def find_by_username(username):
        pending_awaits = {*()}
        future_0 = send_request(session_id, 'GET', 'user:username:%s' % username)
        pending_awaits.add(future_0)
        if _id is not None:
            _id = await_request(session_id, future_0)
            pending_awaits.remove(session_id)
            return User(int(_id))
            _id = await_request(session_id, future_0)
        else:
            return None
        for future in pending_awaits:
            await_request(session_id, future)
        return None

    @staticmethod
    def find_by_id(_id):
        pending_awaits = {*()}
        future_0 = send_request(session_id, 'EXISTS', 'user:id:%s:username' % _id)
        pending_awaits.add(future_0)
        if async_cond_0:
            return User(int(_id))
            async_cond_0 = await_request(session_id, future_0)
        else:
            return None
        for future in pending_awaits:
            await_request(session_id, future)
        return None

    @staticmethod
    def create(username, password):
        pending_awaits = {*()}
        future_0 = send_request(session_id, 'INCR', 'user:uid')
        pending_awaits.add(future_0)
        future_1 = send_request(session_id, 'GET', 'user:username:%s' % username)
        pending_awaits.add(future_1)
        if not async_cond_0:
            future_2 = send_request(session_id, 'SET', 'user:id:%s:username' % user_id, username)
            pending_awaits.add(future_2)
            future_3 = send_request(session_id, 'SET', 'user:username:%s' % username, user_id)
            pending_awaits.add(future_3)
            salt = settings.SALT
            future_4 = send_request(session_id, 'SET', 'user:id:%s:password' % user_id, salt + password)
            pending_awaits.add(future_4)
            future_5 = send_request(session_id, 'LPUSH', 'users', user_id)
            pending_awaits.add(future_5)
            user_id = await_request(session_id, future_0)
            pending_awaits.remove(session_id)
            return User(user_id)
            user_id = await_request(session_id, future_0)
            async_cond_0 = await_request(session_id, future_1)
        for future in pending_awaits:
            await_request(session_id, future)
        return None

    def posts(self, page=1):
        pending_awaits = {*()}
        _from, _to = ((page - 1) * 10, page * 10)
        future_0 = send_request(session_id, 'LRANGE', 'user:id:%s:posts' % self.id, _from, _to)
        pending_awaits.add(future_0)
        if posts:
            posts = await_request(session_id, future_0)
            pending_awaits.remove(session_id)
            return (pending_awaits, [Post(int(post_id)) for post_id in posts])
            posts = await_request(session_id, future_0)
        return (pending_awaits, [])

    def timeline(self, page=1):
        pending_awaits = {*()}
        _from, _to = ((page - 1) * 10, page * 10)
        future_0 = send_request(session_id, 'LRANGE', 'user:id:%s:timeline' % self.id, _from, _to)
        pending_awaits.add(future_0)
        if timeline:
            timeline = await_request(session_id, future_0)
            pending_awaits.remove(session_id)
            return (pending_awaits, [Post(int(post_id)) for post_id in timeline])
            timeline = await_request(session_id, future_0)
        return (pending_awaits, [])

    def mentions(self, page=1):
        pending_awaits = {*()}
        _from, _to = ((page - 1) * 10, page * 10)
        future_0 = send_request(session_id, 'LRANGE', 'user:id:%s:mentions' % self.id, _from, _to)
        pending_awaits.add(future_0)
        if mentions:
            mentions = await_request(session_id, future_0)
            pending_awaits.remove(session_id)
            return (pending_awaits, [Post(int(post_id)) for post_id in mentions])
            mentions = await_request(session_id, future_0)
        return (pending_awaits, [])

    def add_post(self, post):
        pending_awaits = {*()}
        future_0 = send_request(session_id, 'LPUSH', 'user:id:%s:posts' % self.id, post.id)
        pending_awaits.add(future_0)
        future_1 = send_request(session_id, 'LPUSH', 'user:id:%s:timeline' % self.id, post.id)
        pending_awaits.add(future_1)
        future_2 = send_request(session_id, 'SADD', 'posts:id', post.id)
        pending_awaits.add(future_2)
        return (pending_awaits, None)

    def add_timeline_post(self, post):
        pending_awaits = {*()}
        future_0 = send_request(session_id, 'LPUSH', 'user:id:%s:timeline' % self.id, post.id)
        pending_awaits.add(future_0)
        return (pending_awaits, None)

    def add_mention(self, post):
        pending_awaits = {*()}
        future_0 = send_request(session_id, 'LPUSH', 'user:id:%s:mentions' % self.id, post.id)
        pending_awaits.add(future_0)
        return (pending_awaits, None)

    def follow(self, user):
        pending_awaits = {*()}
        if user == self:
            return (pending_awaits, None)
        else:
            future_0 = send_request(session_id, 'SADD', 'user:id:%s:followees' % self.id, user.id)
            pending_awaits.add(future_0)
            pending_awaits_add_follower, _ = user.add_follower(self)
            pending_awaits.update(pending_awaits_add_follower)
        return (pending_awaits, None)

    def stop_following(self, user):
        pending_awaits = {*()}
        future_0 = send_request(session_id, 'SREM', 'user:id:%s:followees' % self.id, user.id)
        pending_awaits.add(future_0)
        pending_awaits_remove_follower, _ = user.remove_follower(self)
        pending_awaits.update(pending_awaits_remove_follower)
        return (pending_awaits, None)

    def following(self, user):
        pending_awaits = {*()}
        future_0 = send_request(session_id, 'SISMEMBER', 'user:id:%s:followees' % self.id, user.id)
        pending_awaits.add(future_0)
        if async_cond_0:
            return (pending_awaits, True)
            async_cond_0 = await_request(session_id, future_0)
        return (pending_awaits, False)

    @property
    def followers(self):
        pending_awaits = {*()}
        future_0 = send_request(session_id, 'SMEMBERS', 'user:id:%s:followers' % self.id)
        pending_awaits.add(future_0)
        if followers:
            followers = await_request(session_id, future_0)
            pending_awaits.remove(session_id)
            return [User(int(user_id)) for user_id in followers]
            followers = await_request(session_id, future_0)
        for future in pending_awaits:
            await_request(session_id, future)
        return []

    @property
    def followees(self):
        pending_awaits = {*()}
        future_0 = send_request(session_id, 'SMEMBERS', 'user:id:%s:followees' % self.id)
        pending_awaits.add(future_0)
        if followees:
            followees = await_request(session_id, future_0)
            pending_awaits.remove(session_id)
            return [User(int(user_id)) for user_id in followees]
            followees = await_request(session_id, future_0)
        for future in pending_awaits:
            await_request(session_id, future)
        return []

    @property
    def tweet_count(self):
        pending_awaits = {*()}
        for future in pending_awaits:
            await_request(session_id, future)
        return send_request(session_id, 'LLEN', 'user:id:%s:posts' % self.id) or 0

    @property
    def followees_count(self):
        pending_awaits = {*()}
        for future in pending_awaits:
            await_request(session_id, future)
        return send_request(session_id, 'SCARD', 'user:id:%s:followees' % self.id) or 0

    @property
    def followers_count(self):
        pending_awaits = {*()}
        for future in pending_awaits:
            await_request(session_id, future)
        return send_request(session_id, 'SCARD', 'user:id:%s:followers' % self.id) or 0

    def add_follower(self, user):
        pending_awaits = {*()}
        future_0 = send_request(session_id, 'SADD', 'user:id:%s:followers' % self.id, user.id)
        pending_awaits.add(future_0)
        return (pending_awaits, None)

    def remove_follower(self, user):
        pending_awaits = {*()}
        future_0 = send_request(session_id, 'SREM', 'user:id:%s:followers' % self.id, user.id)
        pending_awaits.add(future_0)
        return (pending_awaits, None)

class Post(Model):

    @staticmethod
    def create(user, content):
        pending_awaits = {*()}
        future_0 = send_request(session_id, 'INCR', 'post:uid')
        pending_awaits.add(future_0)
        future_1 = send_request(session_id, 'LPUSH', 'timeline', post_id)
        pending_awaits.add(future_1)
        post_id = await_request(session_id, future_0)
        pending_awaits.remove(session_id)
        post = Post(post_id)
        post.content = content
        post.user_id = user.id
        pending_awaits_add_post, _ = user.add_post(post)
        pending_awaits.update(pending_awaits_add_post)
        for follower in user.followers:
            pending_awaits_add_timeline_post, _ = follower.add_timeline_post(post)
            pending_awaits.update(pending_awaits_add_timeline_post)
        mentions = re.findall('@\\w+', content)
        for mention in mentions:
            pending_awaits_find_by_username, u = User.find_by_username(mention[1:])
            pending_awaits.update(pending_awaits_find_by_username)
            if u:
                pending_awaits_add_mention, pending_awaits_add_mention, _ = u.add_mention(post)
                pending_awaits.update(pending_awaits_add_mention)
                pending_awaits.update(pending_awaits_add_mention)
                post_id = await_request(session_id, future_0)
        for future in pending_awaits:
            await_request(session_id, future)
        return None

    @staticmethod
    def find_by_id(id):
        pending_awaits = {*()}
        future_0 = send_request(session_id, 'SISMEMBER', 'posts:id', int(id))
        pending_awaits.add(future_0)
        if async_cond_0:
            return Post(id)
            async_cond_0 = await_request(session_id, future_0)
        for future in pending_awaits:
            await_request(session_id, future)
        return None

    @property
    def user(self):
        pending_awaits = {*()}
        for future in pending_awaits:
            await_request(session_id, future)
        return User.find_by_id(r.get('post:id:%s:user_id' % self.id))

def main():
    pass
if __name__ == '__main__':
    main()
    return None