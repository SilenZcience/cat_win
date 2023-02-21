# Changelog

All notable changes to this project will be documented in this file. <br>
Start of documentation: 2023-02-16 / v1.1.0

## [1.1.2] - TBA

### Minor Changes

- added -`k`, --`keyword` parameter to only show lines containing queried keywords using `find` or `match`.
- added --`nb`, --`nobreak` parameter to not interrupt the output on queried keywords using `find` or `match` with a message in regard to the position of the keyword.

### Bugfixes

- fix Bug where --nocolor would not apply to --FILES output or the update information.


## [1.1.1] - 2023-02-19

### Major Changes

- included `cat` and `catw` as entrypoint. Using `cat` will show a deprecation warning.

### Minor Changes

- added `message_information`, `message_important` and `message_warning` as customizable colors to the --config menu.
- added unrecognized parameters to --debug menu.
- added -`F`, --`FILES` parameter which ONLY shows the found files. (useful when searching files with pattern like "\*\*/\*.txt")

### Bugfixes

- fix Bug where background colors would colorize linebreaks and unnecessary whitespaces.
- fix Bug where parameters including `-`-characters (like "test-file.txt") would not be recognized as an unknown file to write.


## [1.1.0] - 2023-02-18

This release fully focuses on cleaning up, patching as many Bugs as possible, and renaming commands to a more logical name.

### Major changes

- changed the entrypoint `cat` to `catw`. This change was made to resolve the conflict on various platforms using `cat` natively.

- changed -`x`, --linelength parameter to -`l`, --linelength
- changed -`s`, --`squeeze` parameter to -`u`, --`unique`
- changed -`c`, --`count` parameter to -`s`, --`sum`
- changed -`col`, --nocolor parameter to --`nc`, --nocolor

### Minor Changes

- --config changes are now enumerated from 1 upwards, instead of 0 upwards.
- when using the --help or --version parameter and a new version is available, you will now be informed in case major changes have been made. This works by sticking to the versioning conventions.

### Bugfixes

- fix Bug where --peek parameter does not show the correct number of lines skipped or prints unnecessary line breaks.
- fix Bug where --peek parameter does not evenly show the first and last lines.
- fix Bug where --linelength and --number prefix using background colors would incorrectly colorize whitespaces.
- fix Bug where --config change would crash.
- fix Bug where the Updatechecker would not recognize a new release.
- fix Bug where --clip parameter copied AnsiColor Codes resulting in a bizarre looking content.
- fix Bug where the User had to approve the creation of a temp file.