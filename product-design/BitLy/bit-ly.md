## What is Bit.ly?
Bit.ly is a URL shortening service that converts long URLs into shorter, manageable links. It also provides analytics for the shortened URLs.

## Functional Requirements
- Users should be able to shorten long URLs
- Optionally, users should be able to specify a custom alias for their shortened URL (ie. "www.short.ly/my-custom-alias")
- Optionally, users should be able to specify an expiration date for their shortened URL
- Users should be able to access the original URL by using the shortened URL.
## out of scope
- User authentication
- Analytics for the shortened URLs

## Non-Functional Requirements
- 1 Billion shortened URLs
- 100 M Daily Active Users
- avalibiltiy 99.99% (avalibilty > cosnsistency)
- The redirection should occur with minimal delay (< 100ms)
- All api response by < 100 ms



