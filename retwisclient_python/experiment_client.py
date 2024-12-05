#!/usr/bin/env python3

import argparse
import random
import time
import signal
import sys
import cProfile
import logging
from typing import List
import numpy as np
from retwisclient import User, Post

class ZipfGenerator:
    def __init__(self, n, s, seed=None):
        self.n = n
        self.s = s
        self.rng = random.Random(seed)
        
        # Calculate Zeta values
        self.zeta_n = sum(1.0 / (i ** s) for i in range(1, n + 1))
        
    def next(self) -> int:
        u = self.rng.random()
        sum_prob = 0.0
        for i in range(1, self.n + 1):
            sum_prob += 1.0 / (i ** self.s) / self.zeta_n
            if sum_prob >= u:
                return i - 1
        return self.n - 1

def profile_handler(signum, frame):
    print("Received signal to stop profiling")
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description='Retwis Python Client Experiment')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--cpu-profile', type=str, help='CPU profile output file')
    parser.add_argument('--num-keys', type=int, default=1000000, help='Number of keys')
    parser.add_argument('--zipf-s', type=float, default=0.9, help='Zipf distribution parameter')
    parser.add_argument('--exp-length', type=int, default=60, help='Experiment length in seconds')
    parser.add_argument('--rand-sleep', type=int, default=0, help='Random sleep in milliseconds')
    parser.add_argument('--ramp-up', type=int, default=0, help='Ramp up time in seconds')
    parser.add_argument('--ramp-down', type=int, default=0, help='Ramp down time in seconds')
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if args.cpu_profile:
        signal.signal(signal.SIGINT, profile_handler)
        pr = cProfile.Profile()
        pr.enable()

    # Initialize Zipf generator
    zipf = ZipfGenerator(args.num_keys, args.zipf_s, seed=int(time.time()))
    count = 0

    # Initialize state variables
    global_timeline = zipf.next()
    next_post_id = zipf.next()
    next_user_id = zipf.next()
    auths = zipf.next()
    auth = zipf.next()
    users = zipf.next()
    users_by_time = zipf.next()

    # Store initial state
    retwis_types = ["login", "logout", "register", "post", "follow", "timeline", "profile"]
    selector = 0

    start_time = time.time()
    current_time = start_time

    while int(current_time - start_time) < args.exp_length:
        if args.rand_sleep > 0:
            time.sleep(random.randint(0, args.rand_sleep) / 1000.0)  # Convert to seconds

        op_type = random.randint(0, 99)
        before = time.time()

        if op_type < 2:  # Login 2%
            selector = 0
            # Implement login operation using Python client
            user_id = zipf.next() % users
            User.find_by_id(user_id)
            
        elif op_type < 4:  # Logout 2%
            selector = 1
            # Implement logout operation
            auth_id = zipf.next() % auths
            # Note: Logout might not have direct equivalent in Python client
            
        elif op_type < 5:  # Register 1%
            selector = 2
            username = f"user_{zipf.next()}"
            password = f"pass_{zipf.next()}"
            User.create(username, password)
            
        elif op_type < 15:  # Post 10%
            selector = 3
            user = User.find_by_id(zipf.next() % users)
            if user:
                Post.create(user, f"Post content {zipf.next()}")
            
        elif op_type < 35:  # Follow 20%
            selector = 4
            follower = User.find_by_id(zipf.next() % users)
            followee = User.find_by_id(zipf.next() % users)
            if follower and followee:
                follower.follow(followee)
            
        elif op_type < 85:  # ShowTimeline 50%
            selector = 5
            user = User.find_by_id(zipf.next() % users)
            if user:
                user.timeline()
            
        else:  # Profile 15%
            selector = 6
            user = User.find_by_id(zipf.next() % users)
            if user:
                user.posts()

        after = time.time()
        count += 1
        logging.debug(f"AppRequests attempted: {count}")

        curr_runtime = int(current_time - start_time)
        if args.ramp_up <= curr_runtime < (args.exp_length - args.ramp_down):
            lat = int((after - before) * 1e9)  # Convert to nanoseconds
            print(f"app,{lat},0,{count}")
            print(f"{retwis_types[selector]},{lat},0,{count}")

        current_time = time.time()

    logging.info(f"Total AppRequests attempted: {count}")
    logging.info(f"Experiment over after {current_time - start_time} seconds")

    if args.cpu_profile:
        pr.disable()
        pr.dump_stats(args.cpu_profile)

if __name__ == '__main__':
    main()
