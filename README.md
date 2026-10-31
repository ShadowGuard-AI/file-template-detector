![Banner](banner.png)

# file-template-detector
Identifies if a file conforms to a known template format (e.g., configuration files, logs) by comparing its structure against predefined template definitions.  Useful for detecting unauthorized modifications or deviations. - Focused on File operations and analysis

## Install
`git clone https://github.com/ShadowStrikeHQ/file-template-detector`

## Usage
`./file-template-detector [params]`

## Parameters
- `--log_level`: Set the logging level.

A template line starting with `REGEX:` is matched as a regular expression against the corresponding file line. Every other template line must match exactly, and the file and the template must have the same number of lines: a file with extra or missing lines does not conform, and an empty file conforms only to an empty template.

File ownership is never a reason to refuse a check. A symbolic link, world writable permissions, or a large file size are logged as warnings, and the comparison runs anyway.

## Exit codes
Exit 0 means the file conforms to the template. Exit 1 means the file does not conform, or the file or the template is missing.

## License
Copyright (c) ShadowStrikeHQ
