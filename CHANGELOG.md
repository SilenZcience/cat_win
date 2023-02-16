# Changelog

All notable changes to this project will be documented in this file. <br>
Start of documentation: 2023-02-16 / v1.1.0


## [1.1.0] - TBA

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