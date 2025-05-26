# GridNight Commander

GridNight Commander (`gnc`) is a terminal-based tool for managing files in GridFS.

## Design

The goal is to have a console that will let you browse files in the terminal.
Users should be able to list files, upload new files, delete existing files,
and preview the contents of files. The console should look like this:

```
+---------------+-----------------------+
| collection_1/ |  # File 2 Contents    |
|    file_1     |  This is a preview of |
|   =file_2=    |  what's in file_2,    |
|    ...        |  maybe rendered if it |
|               |  is a MarkDown file.  |
+---------------+-----------------------+
| <Connect>     | File 2 Metadata...    |
+---------------+-----------------------+
```

The idea is something like [Midnight Commander](https://midnight-commander.org/)
but tailored for working with GridFS file stores.