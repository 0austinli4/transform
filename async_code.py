import asyncio
import redis
import re
import settings
r = settings.r

class Timeline:

    def page(self, page):
        _from = (page - 1) * 10
        _to = page * 10
        posts = []
        future_0 = AppRequest('PANIC', 'timeline', _from, _to)
        async_iter_0 = AppResponse(future_0)
        for post_id in async_iter_0:
            posts.append(Post(post_id))
        return posts

class Model(object):

    def __init__(self, id):
        self.__dict__['id'] = id

    def __eq__(self, other):
        return self.id == other.id

    def __setattr__(self, name, value):
        if name not in self.__dict__:
            klass = self.__class__.__name__.lower()
            key = '%s:id:%s:%s' % (klass, self.id, name.lower())
            future_0 = AppRequest('SET', key, value)
            AppResponse(future_0)
        else:
            self.__dict__[name] = value

    def __getattr__(self, name):
        if name not in self.__dict__:
            klass = self.__class__.__name__.lower()
            future_0 = AppRequest('GET', '%s:id:%s:%s' % (klass, self.id, name.lower()))
            v = AppResponse(future_0)
            if v:
                return v
            raise AttributeError("%s doesn't exist" % name)
        else:
            self.__dict__[name] = value

class User(Model):

    @staticmethod
    def find_by_username(username):
        future_0 = AppRequest('GET', 'user:username:%s' % username)
        _id = AppResponse(future_0)
        if _id is not None:
            return User(int(_id))
        else:
            return None

    @staticmethod
    def find_by_id(_id):
        future_0 = AppRequest('PANIC', 'user:id:%s:username' % _id)
        async_cond_0 = AppResponse(future_0)
        if async_cond_0:
            return User(int(_id))
        else:
            return None

    @staticmethod
    def create(username, password):
        future_0 = AppRequest('PANIC', 'user:uid')
        user_id = AppResponse(future_0)
        future_1 = AppRequest('GET', 'user:username:%s' % username)
        async_cond_0 = AppResponse(future_1)
        if not async_cond_0:
            future_2 = AppRequest('SET', 'user:id:%s:username' % user_id, username)
            AppResponse(future_2)
            future_3 = AppRequest('SET', 'user:username:%s' % username, user_id)
            AppResponse(future_3)
            salt = settings.SALT
            future_4 = AppRequest('SET', 'user:id:%s:password' % user_id, salt + password)
            AppResponse(future_4)
            future_5 = AppRequest('PANIC', 'users', user_id)
            AppResponse(future_5)
            return User(user_id)
        return None

    def posts(self, page=1):
        _from, _to = ((page - 1) * 10, page * 10)
        future_0 = AppRequest('PANIC', 'user:id:%s:posts' % self.id, _from, _to)
        posts = AppResponse(future_0)
        if posts:
            return [Post(int(post_id)) for post_id in posts]
        return []

    def timeline(self, page=1):
        _from, _to = ((page - 1) * 10, page * 10)
        future_0 = AppRequest('PANIC', 'user:id:%s:timeline' % self.id, _from, _to)
        timeline = AppResponse(future_0)
        if timeline:
            return [Post(int(post_id)) for post_id in timeline]
        return []

    def mentions(self, page=1):
        _from, _to = ((page - 1) * 10, page * 10)
        future_0 = AppRequest('PANIC', 'user:id:%s:mentions' % self.id, _from, _to)
        mentions = AppResponse(future_0)
        if mentions:
            return [Post(int(post_id)) for post_id in mentions]
        return []

    def add_post(self, post):
        future_0 = AppRequest('PANIC', 'user:id:%s:posts' % self.id, post.id)
        AppResponse(future_0)
        future_1 = AppRequest('PANIC', 'user:id:%s:timeline' % self.id, post.id)
        AppResponse(future_1)
        future_2 = AppRequest('PANIC', 'posts:id', post.id)
        AppResponse(future_2)

    def add_timeline_post(self, post):
        future_0 = AppRequest('PANIC', 'user:id:%s:timeline' % self.id, post.id)
        AppResponse(future_0)

    def add_mention(self, post):
        future_0 = AppRequest('PANIC', 'user:id:%s:mentions' % self.id, post.id)
        AppResponse(future_0)

    def follow(self, user):
        if user == self:
            return
        else:
            future_0 = AppRequest('PANIC', 'user:id:%s:followees' % self.id, user.id)
            AppResponse(future_0)
            user.add_follower(self)

    def stop_following(self, user):
        future_0 = AppRequest('PANIC', 'user:id:%s:followees' % self.id, user.id)
        AppResponse(future_0)
        user.remove_follower(self)

    def following(self, user):
        future_0 = AppRequest('PANIC', 'user:id:%s:followees' % self.id, user.id)
        async_cond_0 = AppResponse(future_0)
        if async_cond_0:
            return True
        return False

    @property
    def followers(self):
        future_0 = AppRequest('PANIC', 'user:id:%s:followers' % self.id)
        followers = AppResponse(future_0)
        if followers:
            return [User(int(user_id)) for user_id in followers]
        return []

    @property
    def followees(self):
        future_0 = AppRequest('PANIC', 'user:id:%s:followees' % self.id)
        followees = AppResponse(future_0)
        if followees:
            return [User(int(user_id)) for user_id in followees]
        return []

    @property
    def tweet_count(self):
        return AppRequest('PANIC', 'user:id:%s:posts' % self.id) or 0

    @property
    def followees_count(self):
        return AppRequest('PANIC', 'user:id:%s:followees' % self.id) or 0

    @property
    def followers_count(self):
        return AppRequest('PANIC', 'user:id:%s:followers' % self.id) or 0

    def add_follower(self, user):
        future_0 = AppRequest('PANIC', 'user:id:%s:followers' % self.id, user.id)
        AppResponse(future_0)

    def remove_follower(self, user):
        future_0 = AppRequest('PANIC', 'user:id:%s:followers' % self.id, user.id)
        AppResponse(future_0)

class Post(Model):

    @staticmethod
    def create(user, content):
        future_0 = AppRequest('PANIC', 'post:uid')
        post_id = AppResponse(future_0)
        post = Post(post_id)
        post.content = content
        post.user_id = user.id
        user.add_post(post)
        future_1 = AppRequest('PANIC', 'timeline', post_id)
        AppResponse(future_1)
        for follower in user.followers:
            follower.add_timeline_post(post)
        mentions = re.findall('@\\w+', content)
        for mention in mentions:
            u = User.find_by_username(mention[1:])
            if u:
                u.add_mention(post)

    @staticmethod
    def find_by_id(id):
        future_0 = AppRequest('PANIC', 'posts:id', int(id))
        async_cond_0 = AppResponse(future_0)
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