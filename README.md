Simple PushBullet command-line tool I wrote to push things to and from my phone.

### Options

- `-v | --verbose`: Causes the output of raw JSON. Useful for debugging, and in conjunction with `jq`.
- `-F | --no-files`: Causes the client not to download any pushes.

#### Positional arguments

1. `<integer> | u`: Either specifies a count of pushes to retrieve, or specifies that the rest of the positional arguments are upload specifications
  - `<title>:<message>[:rider]`: Specifies either a new `note` push to be uploaded or a new `file` or `link` push, depending on whether `rider` is a valid hostname and path, for which the default URI scheme will be HTTP, some other kind of URL, or a path on the filesystem.
