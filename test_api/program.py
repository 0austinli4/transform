
class User:
    def __init__(self, name):
        self.name = name
        self.posts = {}

class Twitter:
    def __init__(self):
        self.users = {}
    def add_user(user):
        self.users[user.name] = user

t = Twitter()

def log_info():
    logged = is_logged_in()
    users = t.users
    posts = get_post(users)
    sorted_posts = sort_all_posts()
    return_post(user)
    print(posts)
    print(logged)
    authenticate(logged)
    return 

def basic_move():
    print("a")
    print("b")
    print("c")
    ok = authenticate(logged)

def authenticate(logged):
    if not logged:
        print("Not logged in")
    process_auth()

def sort_all_posts():
    all_posts = []
    initial_posts = get_posts(user)
    for user in t.users:
        posts = get_post(user)
        print(posts)
        all_posts.append(posts)
    
    if len(all_posts) > 10:
        return all_posts
    else:
        u = addUser('temporary')
        all_posts.append(get_post(u))

def addUser(name):
    new_user = User(name)
    t.add_user(new_user)
    return new_user

def get_post(user):
    if user.name not in t:
        return None
    
    return user.posts

@decorator
def add_post(postId: str, postNum: int):
    if not is_logged_in():
        return False

    if postId in posts:
        return False
    posts[postId] = postNum

    return True

def is_logged_in():
    return True

@decorator
def process_auth():
    time.sleep(2)

@decorator
def return_post(user):
    print(user.posts)
    return user.posts