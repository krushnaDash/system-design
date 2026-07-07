## FR

* Users can create a profile with preferences (e.g. age range, interests) and specify a maximum distance.
* Users can view a stack of potential matches in line with their preferences and within max distance of their current location.
* Users can swipe right / left on profiles one-by-one, to express "yes" or "no" on other users

* Users get a match notification if they mutually swipe on each other

* Once swipe left, that partifular profile will not be shown next time

### Out of Scope
* User should abe to register and login
* User able to DM and chat with match profile
* User able to upload picture, vide0 etc.

## NFR
* Daily active user 10 M with average 100 swipes, which means  10* 100  1B daily request, with peak goes to 100K request per seconds. Sysatem should scale atleast 100K RPS

* Strong consistency for Matching, that is If a user swipes "yes" on a user who already swiped "yes" on them, they should get a match notification.

* The system should load the potential matches stack with low latency, < 300ms
* The system should avoid showing user profiles that the user has previously swiped on [ part of FR also]


Core Enties.                 
 MatchedStack
   user_id
   match_id
   .... 

 Profile
   min-age
   max-age
   prefred-gender
   radius-within
   .... 

           
 Swipe
   userid1_user_id2
   userid1_decison
   userid2_decison
   .... 


API
post /v1/profile , body {profile}
post /v1/swipe/{user_id}
{
decision : yes|No
} 
get v1/match/ {List of Match profile }

For match notification user 2 we can one of push notification 


Deep Dives
How can we ensure that swiping is consistent and low latency
Since we have choose cassndra

Race condition
1-> write -> A swipe yes for B 
2-> read -> is B swipe yes ? ( write is not propagte to all nodes)

1-> write -> B swipe yes for A
2- read -> is A swipe yes ? ( write is not propagte to all nodes) 

In this case this match will be lost




Ref: https://www.hellointerview.com/learn/system-design/problem-breakdowns/tinder