Facebook's Post Search
https://www.hellointerview.com/learn/system-design/problem-breakdowns/fb-post-search#1-users-should-be-able-to-create-and-like-posts

## The functional rexquirements are:
- Users should be able to create and like posts
- Users should be able to search posts by keyword
- Users should be able to get search results sorted by recency or like count

## NFR
- 1 Billion daily active user
- 1 Trillion posts per day -> which means 10000K write perseconds

- Eventually consistent system
- new post to index with in a minute
- search result with 500 ms for P90
- create post API response time < 200 ms

- system is read heavy, beacuse of search and fan-out



## The constraints are:

- Do not use a search engine like Elasticsearch or a pre-built full-text index

## Requirements

## core Entities
- User
- Post
- Like

## API or interface

``` JSON
POST / v1/posts 
Reuest body:  
{
content : string
}

GET v1/posts

{
    posts: []
    nextPageToken: String
}

GET v1/post?q= {keywords} & sortBy={recency|likes} & pageToken={} & pageSize={}

Response Body
{
Posts: []
nextPageToken:String
}

POST /v1/like/{post_id}
{
like : boolean
}
```


## High level architecture

## Deep dives
