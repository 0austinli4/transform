import redis
import re
import settings
r = settings.r

class Timeline:

    def page(self, page):
        _from = (page - 1) * 10
        _to = page * 10
        return [Post(post_id) for post_ids in send_request(session_id, 'LRANGE', 'timeline', _from, _to)]

class Model(object):

    def __init__(self, id):
        self.__dict__['id'] = id

    def __eq__(self, other):
        return self.id == other.id

    def __setattr__(self, name, value):
        if name not in self.__dict__:
            klass = self.__class__.__name__.lower()
            key = '%s:id:%s:%s' % (klass, self.id, name.lower())
            future_0 = send_request(session_id, 'SET', key, value)
            await_request(session_id, future_0)
        else:
            self.__dict__[name] = value

    def __getattr__(self, name):
        if name not in self.__dict__:
            klass = self.__class__.__name__.lower()
            future_0 = send_request(session_id, 'GET', '%s:id:%s:%s' % (klass, self.id, name.lower()))
            v = await_request(session_id, future_0)
            if v:
                return v
            raise AttributeError("%s doesn't exist" % name)
        else:
            self.__dict__[name] = value

class User(Model):

    @staticmethod
    def find_by_username(username):
        future_0 = send_request(session_id, 'GET', 'user:username:%s' % username)
        _id = await_request(session_id, future_0)
        if _id is not None:
            return User(int(_id))
        else:
            return None

    @staticmethod
    def find_by_id(_id):
        future_0 = send_request(session_id, 'EXISTS', 'user:id:%s:username' % _id)
        async_cond_0 = await_request(session_id, future_0)
        if async_cond_0:
            return User(int(_id))
        else:
            return None

    @staticmethod
    def create(username, password):
        future_0 = send_request(session_id, 'INCR', 'user:uid')
        user_id = await_request(session_id, future_0)
        future_1 = send_request(session_id, 'GET', 'user:username:%s' % username)
        async_cond_0 = await_request(session_id, future_1)
        if not async_cond_0:
            future_2 = send_request(session_id, 'SET', 'user:id:%s:username' % user_id, username)
            await_request(session_id, future_2)
            future_3 = send_request(session_id, 'SET', 'user:username:%s' % username, user_id)
            await_request(session_id, future_3)
            salt = settings.SALT
            future_4 = send_request(session_id, 'SET', 'user:id:%s:password' % user_id, salt + password)
            await_request(session_id, future_4)
            future_5 = send_request(session_id, 'LPUSH', 'users', user_id)
            await_request(session_id, future_5)
            return User(user_id)
        return None

    def posts(self, page=1):
        _from, _to = ((page - 1) * 10, page * 10)
        future_0 = send_request(session_id, 'LRANGE', 'user:id:%s:posts' % self.id, _from, _to)
        posts = await_request(session_id, future_0)
        if posts:
            return [Post(int(post_id)) for post_id in posts]
        return []

    def timeline(self, page=1):
        _from, _to = ((page - 1) * 10, page * 10)
        future_0 = send_request(session_id, 'LRANGE', 'user:id:%s:timeline' % self.id, _from, _to)
        timeline = await_request(session_id, future_0)
        if timeline:
            return [Post(int(post_id)) for post_id in timeline]
        return []

    def mentions(self, page=1):
        _from, _to = ((page - 1) * 10, page * 10)
        future_0 = send_request(session_id, 'LRANGE', 'user:id:%s:mentions' % self.id, _from, _to)
        mentions = await_request(session_id, future_0)
        if mentions:
            return [Post(int(post_id)) for post_id in mentions]
        return []

    def add_post(self, post):
        future_0 = send_request(session_id, 'LPUSH', 'user:id:%s:posts' % self.id, post.id)
        await_request(session_id, future_0)
        future_1 = send_request(session_id, 'LPUSH', 'user:id:%s:timeline' % self.id, post.id)
        await_request(session_id, future_1)
        future_2 = send_request(session_id, 'SADD', 'posts:id', post.id)
        await_request(session_id, future_2)

    def add_timeline_post(self, post):
        future_0 = send_request(session_id, 'LPUSH', 'user:id:%s:timeline' % self.id, post.id)
        await_request(session_id, future_0)

    def add_mention(self, post):
        future_0 = send_request(session_id, 'LPUSH', 'user:id:%s:mentions' % self.id, post.id)
        await_request(session_id, future_0)

    def follow(self, user):
        if user == self:
            return
        else:
            future_0 = send_request(session_id, 'SADD', 'user:id:%s:followees' % self.id, user.id)
            await_request(session_id, future_0)
            user.add_follower(self)

    def stop_following(self, user):
        future_0 = send_request(session_id, 'SREM', 'user:id:%s:followees' % self.id, user.id)
        await_request(session_id, future_0)
        user.remove_follower(self)

    def following(self, user):
        future_0 = send_request(session_id, 'SISMEMBER', 'user:id:%s:followees' % self.id, user.id)
        async_cond_0 = await_request(session_id, future_0)
        if async_cond_0:
            return True
        return False

    @property
    def followers(self):
        future_0 = send_request(session_id, 'SMEMBERS', 'user:id:%s:followers' % self.id)
        followers = await_request(session_id, future_0)
        if followers:
            return [User(int(user_id)) for user_id in followers]
        return []

    @property
    def followees(self):
        future_0 = send_request(session_id, 'SMEMBERS', 'user:id:%s:followees' % self.id)
        followees = await_request(session_id, future_0)
        if followees:
            return [User(int(user_id)) for user_id in followees]
        return []

    @property
    def tweet_count(self):
        return send_request(session_id, 'LLEN', 'user:id:%s:posts' % self.id) or 0

    @property
    def followees_count(self):
        return send_request(session_id, 'SCARD', 'user:id:%s:followees' % self.id) or 0

    @property
    def followers_count(self):
        return send_request(session_id, 'SCARD', 'user:id:%s:followers' % self.id) or 0

    def add_follower(self, user):
        future_0 = send_request(session_id, 'SADD', 'user:id:%s:followers' % self.id, user.id)
        await_request(session_id, future_0)

    def remove_follower(self, user):
        future_0 = send_request(session_id, 'SREM', 'user:id:%s:followers' % self.id, user.id)
        await_request(session_id, future_0)

class Post(Model):

    @staticmethod
    def create(user, content):
        future_0 = send_request(session_id, 'INCR', 'post:uid')
        post_id = await_request(session_id, future_0)
        post = Post(post_id)
        post.content = content
        post.user_id = user.id
        user.add_post(post)
        future_1 = send_request(session_id, 'LPUSH', 'timeline', post_id)
        await_request(session_id, future_1)
        for follower in user.followers:
            follower.add_timeline_post(post)
        mentions = re.findall('@\\w+', content)
        for mention in mentions:
            u = User.find_by_username(mention[1:])
            if u:
                u.add_mention(post)

    @staticmethod
    def find_by_id(id):
        future_0 = send_request(session_id, 'SISMEMBER', 'posts:id', int(id))
        async_cond_0 = await_request(session_id, future_0)
        if async_cond_0:
            return Post(id)
        return None

    @property
    def user(self):
        return User.find_by_id(r.get('post:id:%s:user_id' % self.id))

def main():
    pass
if __name__ == '__main__':
    main()