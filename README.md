Simple PushBullet command-line tool I wrote to push ephemerals between various roadwarrior clients, workstations, browser-hosted extensions, and other clients.

### Options

- `-v | --verbose`: Causes the output of raw JSON. Useful for debugging, and in conjunction with `jq`.
- `-F | --no-files`: Causes the client not to download any pushes.

#### Positional arguments
```
rider :: pathname | netloc + path part of HTTPS URI | full absolute URI
tagspec :: <title>:<message>[:rider]
```
1. `<integer> | u`: Either specifies a count of pushes to retrieve, or specifies that the rest of the positional arguments are upload specifications
  - `<tagspec>[, <tagspec>...]`: Pushes from the command-line by parsing from the syntax outlined above.
	- `-`: Signals that `tagspec`s should be read from stdin.
