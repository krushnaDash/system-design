# Functioncal Requiremetns
- Able to rate limit by user_id, IP address or API key
- Rule are configurable
- Return proper error code(429) and status header

# Non-Functioncal Requiremetns
- High Availablity >> availability over consistency
- Low Latency -> lest 10 ms response time
- Scalable -> 100 M request per seconds

# High Level Design
- API Gateway/Service Layer - Rate Limiter
- Redis - Store rate limit data
- Configuration Service - Store rate limit rules
- Monitoring - Track rate limit violations
- Alerting - Notify on rate limit violations

# Rate limit check from API gateways vs Check from Back-end apps
-> we should do the rate limit check from the api gatways itself as this will save our back-end service from
DDOS attack.

# Deep dive on the Rate limiter Design
Let say we need allow 100 request per minutes per user

## Option 1 -> flexible window, token bucket
 
 Map<User_id, {request_count, last_request_time}>

When new request arrived read the request count

is allowd =  (request count < 100 && currnet time - last request time < 1 min)
                or (currnet time - last request time > 1 min)
when the currnet time - last request time > 1 min, reset the request count=1
else request count+=1

1001 -> 12:59, ctr=99 -> Request 99 -> current time 12:59, allowed
1001 -> 12:59, ctr=100 -> Request 100 -> current time 12:59, allowed
1001 -> 12:59, ctr=100 -> Request 101 -> current time 12:59 , denied
1001 -> 1:00, ctr=100 -> Request 102 -> current time 1:00 , denied
It will never allowed the API, if user is trying call the API in every seconds

## Option 2, fixed token assignment 

User_id -> token_left, token_assign_time

is allowd =  (token_left)
                or (currnet time - token_assign_time > 1 min)

if currnet time - token_assign_time  > 1 min assign99 token again and update the 
token_assign_time


## Redis Implementation

HMGET user:123 request_count last_request_time

MULTI
HSET alice:bucket tokens <new_token_count>
HSET alice:bucket last_refill <current_timestamp>
EXPIRE alice:bucket 3600
EXEC

The MULTI/EXEC block ensures all commands execute as a single atomic operation. The HSET commands update the hash fields with the new token count and timestamp, while EXPIRE automatically deletes the bucket after 1 hour of inactivity to prevent memory leaks.

With the implementation of Redis clsuter it, partation by user_id it can scale horizontally.



@Todo
-- Implement a redis cluster and check how to do atomic transcation, using Lua scripting
-- expalin details abut the Lua scripting
-- leran depth on this





Ref : https://www.hellointerview.com/learn/system-design/problem-breakdowns/distributed-rate-limiter

