# Changelog

All notable changes to this project will be documented in this file. <br>
Start of documentation: 2023-02-16 / v1.1.0

## [1.3.0] - 2023-03-29

### Major Changes

- renamed -`k`, --`keyword` to -`g`, --`grep`
- removed `requests` dependency

### Minor Changes

- -`F` and -`f` will now show `Amount` displaying the amount of files found.
- added --`nk`, --`nokeyword` parameter to reverse the --`grep` output, essentially showing only lines that do not match any queried keyword.


## [1.2.0] - 2023-03-14

### Major Changes

- removed `cat` entrypoint.

### Minor Changes

- added --`binview`, --`binview` parameter to display the raw byte representation of any given file in binary.


## [1.1.7] - 2023-03-12

### Minor Changes

- added --`hexview`, --`hexview` parameter to display the raw byte representation of any given file in hexadecimal.


## [1.1.6] - 2023-03-10

### Minor Changes

- show file sizes on -`f`, --`files` parameter.
- added -`S`, --`SUM` parameter to only show the sum of lines of all files.


## [1.1.5] - 2023-03-01

### Minor Changes

- the `match` and `find` parameters now ignore previously set ANSI-Colorcodes, and therefor gain color priority. This solves the issue, that these parameters sometimes would not find a substring because of invisible escape codes within the line string.
- added some caches which should speed up the process a little, when passing the same file as parameter multiple times.


## [1.1.4] - 2023-02-27

### Major Changes

- reverted from colorama just_fix_windows_console() to init(), such that stripping ANSI-Codes (e.g. on piping) can be enabled.

### Minor Changes

- -`F`, --`FILES` now also shows the size of the stdin content using -`i`.
- added -`E`, --`ECHO` parameter to ignore every following parameter and handle them like stdin.


## [1.1.3] - 2023-02-26

### Major Changes

- it is now possible to use either the '`pyclip`', '`pyperclip3`', or '`pyperclip`' module in order to use the --`clip` parameter. If none of these options are installed, the --clip parameter will not work yet the programm won't crash. This change was made due to some problems using the --clip parameter on macOS.
- the `default` clipboard module was changed from '`pyperclip3`' to '`pyperclip`'. This module however is not included in the necessary dependencies. It can be added to the installation dependencies by using 'pip install cat_win<b>[clip]</b>'. This chang was made to ensure compatibility with `pypy-3.8` and `pypy-3.9`.
- elevated dependency `colorama` from >=0.4.5 to >=0.4.6 (also switched from init() to just_fix_windows_console())

### Minor Changes

- added appeal to raise official github issue when encountering an exception.
- added ability to create files in subdirectories that do not yet exist. The path will be created in the process, on error it will be cleaned up again.
- redesigned --config menu
- added file sizes to -`F`, --`FILES`
- added "`NONE`" - option to color --`config`, in order to disable highlighting for specific elements.

### Bugfixes

- fix Bug where -f and -F together would result in an unwanted output.


## [1.1.2] - 2023-02-22

### Minor Changes

- added -`k`, --`keyword` parameter to only show lines containing queried keywords using `find` or `match`.
- added --`nb`, --`nobreak` parameter to not interrupt the output on queried keywords using `find` or `match` with a message in regard to the position of the keyword.

### Bugfixes

- fix Bug where --nocolor would not apply to --FILES output or the update information.
- fix Bug where --FILES would have unwanted behaviour when no files have been found.
- fix Bug where -l, --linelength would have the wrong offset when using files with only one line.


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
