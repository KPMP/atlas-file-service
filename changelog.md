# Changelog

## Release 3.6 [unreleased]
Brief summary of what's in this release:


### Breaking changes

Breaking changes include any database updates needed, if we need to edit any files on system (like .env or certs, etc). Things that are outside of the code itself that need changed for the system to work.


### Non-breaking changes

Just a place to keep track of things that have changed in the code that we may want to pay special attention to when smoke testing, etc.


## Release 3.5
Brief summary of what's in this release:

We've made a few changes to fix some timeout issues with large files:
- Changed the WSGI server to uWSGI
- Instead of using Flask's send_file, we're now using a FileWrapper and a content disposition of "application/octet-stream"


### Breaking changes
None

### Non-breaking changes
None

## Release 3.4 (10/3/2024)
Brief summary of what's in this release:
- GA download event added

### Breaking changes
None

### Non-breaking changes
None
