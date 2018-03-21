Simple PushBullet command-line tool I wrote to push ephemerals between various roadwarrior clients, workstations, browser-hosted extensions, and other clients.

### Options

- `-v | --verbose`: Causes the output of raw JSON. Useful for debugging, and in conjunction with `jq`.
- `-F | --no-files`: Causes the client not to download any pushes.

#### Positional arguments
```
rider :: pathname | netloc + path part of HTTPS URI | full absolute URI
tagspec :: <title>:<message>[:rider]
```
- `<integer>`: Must be first positional argument. Implies retrieval for the execution instance. Specifies a count of pushes to retrieve.
- `<tagspec>[, <tagspec>...]`: Pushes from the command-line by parsing from the syntax outlined above. If the first positional argument cannot be parsed as an integer for any reason, then all positional arguments will be parsed as `tagspec`s. 
	- `-`: Signals that `tagspec`s should be read from stdin for uploading mode.
