#include <gtest/gtest.h>
#include "redisstore.h"

// Test for basic PUT and GET
TEST(RedisStoreTest, PutAndGet) {
    RedisStore store;
    store.put("key1", Value::NewString("Hello"));

    auto result = store.get("key1");
    ASSERT_TRUE(result.has_value());
    EXPECT_EQ(result->str, "Hello");
}

TEST(RedisStoreTest, GetNonExistentKey) {
    RedisStore store;
    auto result = store.get("nonexistent");
    EXPECT_FALSE(result.has_value());
}

// Test for INCR
TEST(RedisStoreTest, Incr) {
    RedisStore store;
    store.put("counter", Value::NewString("5"));

    auto result = store.incr("counter");
    EXPECT_EQ(result.str, "6");

    result = store.incr("counter");
    EXPECT_EQ(result.str, "7");
}

TEST(RedisStoreTest, IncrNonExistent) {
    RedisStore store;
    auto result = store.incr("new_counter");
    EXPECT_EQ(result.str, "1");
}

TEST(RedisStoreTest, IncrInvalidValue) {
    RedisStore store;
    store.put("invalid_counter", Value::NewString("hello"));
    auto result = store.incr("invalid_counter");
    EXPECT_EQ(result.str, "0");
}

// Test for SET (alias for PUT)
TEST(RedisStoreTest, Set) {
    RedisStore store;
    auto result = store.set("greet", Value::NewString("Hi"));
    EXPECT_EQ(result.str, "OK");

    auto getResult = store.get("greet");
    ASSERT_TRUE(getResult.has_value());
    EXPECT_EQ(getResult->str, "Hi");
}

// Test for SADD
TEST(RedisStoreTest, SAdd) {
    RedisStore store;
    auto result1 = store.sadd("myset", "apple");
    EXPECT_EQ(result1.str, "1");  // 1 element added

    auto result2 = store.sadd("myset", "banana");
    EXPECT_EQ(result2.str, "2");  // 2 elements in set

    // Adding duplicate should not change set size
    auto result3 = store.sadd("myset", "apple");
    EXPECT_EQ(result3.str, "2"); 
}

// Test for EXISTS
TEST(RedisStoreTest, Exists) {
    RedisStore store;
    store.put("key_exists", Value::NewString("value"));

    EXPECT_TRUE(store.exists("key_exists"));
    EXPECT_FALSE(store.exists("key_does_not_exist"));
}

// Test for HSET and HGETALL
TEST(RedisStoreTest, HSetAndHGetAll) {
    RedisStore store;

    auto result1 = store.hset("myhash", "field1", "value1");
    EXPECT_EQ(result1.str, "1");  // Field created

    auto result2 = store.hset("myhash", "field1", "new_value");
    EXPECT_EQ(result2.str, "0");  // Field already existed

    auto result3 = store.hset("myhash", "field2", "value2");
    EXPECT_EQ(result3.str, "1");

    auto result = store.hgetall("myhash");
    EXPECT_EQ(result.hash.size(), 2);
    EXPECT_EQ(result.hash["field1"], "new_value");
    EXPECT_EQ(result.hash["field2"], "value2");
}

// Test for HMGET with existing fields
TEST(RedisStoreTest, HMGetExistingFields) {
    RedisStore store;

    // Set up a hash with two fields
    store.hset("myhash", "field1", "value1");
    store.hset("myhash", "field2", "value2");

    std::vector<std::string> fields = {"field1", "field2"};
    auto result = store.hmget("myhash", fields);

    EXPECT_EQ(result.hash.size(), 2);
    EXPECT_EQ(result.hash["field1"], "value1");
    EXPECT_EQ(result.hash["field2"], "value2");
}

// Test for HMGET with missing fields
TEST(RedisStoreTest, HMGetWithMissingFields) {
    RedisStore store;

    // Only one field exists
    store.hset("myhash", "field1", "value1");

    std::vector<std::string> fields = {"field1", "field2"};
    auto result = store.hmget("myhash", fields);

    EXPECT_EQ(result.hash.size(), 2);
    EXPECT_EQ(result.hash["field1"], "value1");
    EXPECT_EQ(result.hash["field2"], ""); // Missing field should return an empty string
}

// Test for HMGET with all missing fields
TEST(RedisStoreTest, HMGetWithAllMissingFields) {
    RedisStore store;

    store.hset("myhash", "field1", "value1");

    std::vector<std::string> fields = {"field3", "field4"};
    auto result = store.hmget("myhash", fields);

    EXPECT_EQ(result.hash.size(), 2);
    EXPECT_EQ(result.hash["field3"], ""); // Missing field should return empty
    EXPECT_EQ(result.hash["field4"], ""); // Missing field should return empty
}

// Test for HMGET on non-existent key
TEST(RedisStoreTest, HMGetWithMissingKey) {
    RedisStore store;

    std::vector<std::string> fields = {"field1", "field2"};
    auto result = store.hmget("nonexistent_key", fields);

    EXPECT_EQ(result.hash.size(), 0); // No values should be returned
}
