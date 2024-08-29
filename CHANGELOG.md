# Changelog

All notable changes to this project will be documented in this file. <br>
Start of documentation: 2023-02-16 / v1.1.0

## [1.8.6] - TBA

### Minor Changes

- made the color of the cat_win REPL (cats) prefix customizable using the color config.
- when selecting an area in the (hex-)editor the search and replace functionality will only be applied to that region.

## Bugfixes

- added missing error message in (hex-)editor for clipboard errors.


## [1.8.5] - 2024-08-24

### Minor Changes

- added -`L`, --`less` parameter to lazily page through a file step by step and pause output each step.
- added the option to use 8-bit or 24-bit (truecolor) colors in the color config.
- added the option to customize the colors of the progress bar.
- display progress bar when reading in large files.

### Bugfixes

- fixed Bug where -`M`, --`more` would crash when jumping out of bounds.
- fixed Bug where the progress bar could go above 100%.


## [1.8.4] - 2024-08-08

### Minor Changes

- display the size of directories when using -`d`, --`dirs`.
- allow -`f`, --`files` and -`d`, --`dirs` to be used simultaneously.
- allow wildcard characters `?` and ranges `[_-_]` to be used in file pattern to provide a full unix style pathname pattern expansion.


## [1.8.3] - 2024-08-02

### Bugfixes

- fixed Bug where the editor would get unresponsive when replacing all.
- fixed Bug where the editor would not count replacing and cutting as making changes.
- fixed Bug where the editor would perform certain actions twice when in selection mode.
- fixed Bug where the editor would have the wrong selection position when using undo/redo.


## [1.8.2] - 2024-07-31

### Minor Changes

- the (hex-)editor now displays a message when search queries do not yield any result.
- updated the file signature lookup table.
- added `^P` hotkey to the editor to replace searched items.
- added `unicode_escaped_editor_replace` option to the config menu to unicode-escape the replace in the editor.

### Bugfixes

- fixed Bug where certain file signatures were not correctly identified.
- fixed Bug where the hex-editor would display the wrong result when searching for certain bytes.
- fixed Bug where the hex-editor would allow invalid symbols to be searched for.
- fixed Bug where the hex-editor would crash when switching to plain text search mode.
- fixed Bug where the hex-editor would wrongly interpret the search query.
- fixed Bug where the hex-editor would not correctly search for edited bytes.


## [1.8.1] - 2024-07-26

### Minor Changes

- added `^X` hotkey to the (hex-)editor to cut the selected text/bytes.

### Bugfixes

- fixed Bug where the hex-editor would crash when performing certain actions of byte selections.
- fixed Bug where the hex-editor would not correctly copy the selection when using `^C`.


## [1.8.0] - 2024-07-24

### Minor Changes

- cat_win will now detect simple tar-archives and display the contained files.
- when using the parameter -`a`, --`attributes` the signature of the file will be displayed.
- instead of `find=` and `match=` using `f=` and `m=` yields the same result.
- added --`visb`, --`visualizeb` to visualize the given files using scan curve byte view.
- added --`visz`, --`visualizez` to visualize the given files using z-order curve byte view.
- added --`vish`, --`visualizeh` to visualize the given files using hilbert curve byte view.
- added --`vise`, --`visualizee` to visualize the given files using hilbert curve shannon entropy.
- added --`visd`, --`visualized` to visualize the given files using digraph dot plot byte view.
- expanded the selection functionality in the editor. hotkeys will now be applied to the entire selection.

### Bugfixes

- fixed Bug where cat_win would crash in certain situations when piping the output.
- fixed Bug where the editor would be in an invalid state when pasting certain command chains in the keystroke buffer.


## [1.7.12] - 2024-06-29

### Minor Changes

- added the option to search for plain text in the hexeditor by pressing the insert-hotkey while in the search menu.
- expanded the selection functionality in the hex-editor. hotkeys will now be applied to the entire selection.

### Bugfixes

- fixed visual Bug in the hex-editor.
- fixed Bug where a warning is shown unnecessarily.
- fixed visual Bug in the editor in case of non-one-width characters. these will now be displayed as unknown symbols.
- fixed Bug in the (hex-)editor where some actions would not count as the file being changed.


## [1.7.11] - 2024-06-10

### Minor Changes

- added `end_marker_symbol` option to the config menu to define the marker that will be displayed when using -`e`, --`ends`.
- added `blank_remove_ws_lines` option to the config menu to remove whitespace lines with -`b`, --`blank` also.
- changed the `^I` hotkey in the editor (insert byte sequence) and hexeditor (insert text) to `^N`.
- changed the `^C` hotkey in the (hex-)editor (KeyboardInterrupt) to `^D`.
- added area selection via shift-click in the (hex-)editor.
- added `^A` hotkey to the (hex-)editor to select everything.
- added `^C` hotkey to the (hex-)editor to copy selected text to the clipboard.

### Bugfixes

- fixed Bug where some keys would not work in the editor.


## [1.7.10] - 2024-05-31

### Minor Changes

- added `^I` hotkey to editor (insert byte sequence) and hexeditor (insert text).
- when using `DOWN <x>` in -`M`, --`more` it is now possible to move up by entering a negative number x.

### Bugfixes

- fixed Bug where the reload-file prompt could not be canceled in the editor.
- fixed Bug where deleting bytes in the hex-editor would not count as changing the file.


## [1.7.9] - 2024-05-20

### Minor Changes

- the editor now loads lazily to improve loading time on large files.
- the hex-editor now loads lazily to improve loading time on large files.
- when searching in the hex-editor it is now possible to search for byte-sequences.
- changed the parameter --`sort`, --`SORT` to two different parameters --`sort`, --`sort` and --`sortl`, --`sortlength`.
- added `unicode_escaped_editor_search` option to the config menu to unicode-escape the search in the editor.
- added the following hotkeys to the hexeditor: `page up`, `page down`, `end`, `ctrl - end`, `home`, `ctrl - home`.

### Bugfixes

- fixed Bug where the hex-editor would not find searched-for bytes.
- fixed Bug where the editor would allow opening unreadable files and potentially corrupt them upon saving them.
- fixed Bug where the prompts in the (hex-) editor would crash when inserting certain keys.


## [1.7.8] - 2024-04-29

### Minor Changes

- added -`#`, --`hexedit` parameter to open a simple hex-editor to write/edit any provided File.
- added `hex_editor_columns` option to the config menu to define the amount of columns in the hex-editor.
- when using the uppercase variant -`E` (of -`E`, --`echo`) the input will no longer be unicode-escaped.
- added `unicode_escaped_echo` option to the config menu to unicode-escape the input using -`E`, --`echo`.

### Bugfixes

- fixed Bug where the Editor would behave unintended when reloading the file.
- fixed Bug where the Editor would display an error message even when the error was resolved in rare cases.
- fixed Bug where the Editor would not recognize the user input in the reload-file prompt.
- fixed Bug where the Editor would crash on special characters like emojis (displays `�` now).


## [1.7.7] - 2024-04-23

### Bugfixes

- fixed Bug where the color-config (--`cconfig`) would not correctly save new values.


## [1.7.6] - 2024-04-23

### Minor Changes

- added -`B`, --`raw` parameter to read a file as binary and write raw binary as output.
- when piping into the repl (cats) the input will also be printed to display a full context.
- added --`config-clear`, --`config-reset` parameter to reset the config to the default settings.
- added --`cconfig-clear`, --`cconfig-reset` parameter to reset the color config to the default settings.
- added --`config-remove`, --`cconfig-remove` parameter to remove/delete the config file.
- added `peek_size` option to the config menu to define the amount of lines shown when using -`p`, --`peek`.

### Bugfixes

- fixed Bug where --`b64d` would not work in the repl.
- fixed Bug where some literals or patterns would not work in the repl (if they included whitespace).
- fixed Bug where the Editor would always auto indent (even if the config setting was set to False).


## [1.7.5] - 2024-04-06

### Minor Changes

- when using -`a`, --`attributes` on windows the output will also inform about advanced data streams (on ntfs systems).
- reworked -`M`, --`more` to work with long lines wrapping around to the next line and lines containing escape-sequences.

### Bugfixes

- fixed Bug where -`M`, --`more` would not work when catw was piped into.
- fixed Bug where the Editor would wrongly indent the next line.
- fixed Bug where the Editor would break the undo/redo capability when indenting the next line.


## [1.7.4] - 2024-04-02

### Minor Changes

- added -`M`, --`more` parameter to page through a file step by step and pause output each step.
- added `more_step_length` option to the config menu to define the step length used by -`M`, --`more`.

### Bugfixes

- fixed Bug where the update notification message was wrong in certain pre-release scenarios.


## [1.7.3] - 2024-03-21

### Minor Changes

- the config menus now scale to the size of the terminal and are better formatted.
- removed `binary_hex_view` from config.
- removed the prompt to open a file in binary mode (the file will now always be opened).
- allow all parameters to be applied to binary files.
- added `ignore_unknown_bytes` option to the config menu to ignore unknown bytes in binary mode instead of replacing them with �.
- added `unicode_escaped_find` option to the config menu to unicode-escape the queried substrings using `find=` (default is True).
- when using `find=` it is now possible to query for an empty substring.
- added `unicode_escaped_replace` option to the config menu to unicode-escape a and b using `[a,b]` (default is True).

### Bugfixes

- fix Bug where the color-config menu would allow to change elements that should not be changed.
- fix Bug where the config menu would not allow the default-command-line to reset (be empty).
- fix Bug where the config menus could not handle utf-8 characters.
- fix Bug where the -`E` command would not correctly handle utf-8 characters.


## [1.7.2] - 2024-03-05

### Minor Changes

- the config menu now decodes the input as unicode-escape sequences making it possible to enter special characters like tabs (\t) and newlines (\n).
- added --`strings`, --`strings` parameter to print the sequences of printable characters in any given file.
- added `strings_minimum_sequence_length` to the config menu to set the minimum length of characters required to identify a sequence as a string using --`string`.
- added `strings_delimeter` to the config menu to set the delimeter of multiple strings found on the same line using --`string`.
- added `binary_hex_view` to the config menu to display unknown bytes in hexadecimal when opening binary files.

### Bugfixes

- when decoding a corrupted base64 string cat_win will now decode as much as possible instead of throwing an error.
- fix Bug where -`w`, --`wordcount` and --`cc`, --`charcount` would display the wrong output when no valid file is given.


## [1.7.1] - 2024-02-22

### Minor Changes

- added --`cc`, --`charcount` parameter to count the occurrence of every char in all given files.
- added functionality to sort lines by length when using uppercase --`SORT`.


## [1.7.0] - 2024-02-20

### Minor Changes

- renamed -`i`, --`interactive` to -, --`stdin`.
- added `Alt+S` hotkey to the editor to save the current changes.
- show associated file display name in editor instead of full path in case of stdin/url or -`E`.
- when using `find=` in uppercase (`FIND=`) the substring search is no longer case sensitive.
- when using `match=` in uppercase (`MATCH=`) the pattern search is no longer case sensitive.

### Bugfixes

- fix Bug where the editor would not correctly respond to setting the --`plain` parameter.
- fix Bug where the --`wordcount` would have incorrect coloring when using background colors.
- fix Bug where the editor would not work when reading from stdin.
- fix Bug where KeyboardInterrupt in editor would leave the curses module open.
- fix Bug where the uppercase versions of `find=` and `match=` would not work as intended.


## [1.6.5] - 2024-02-13

### Minor Changes

- removed the prompt to open zip-files in binary mode.
- added --`sf`, --`specific-format` parameter to automatically format some file types like json or xml.
- renamed --`config`, --`config` to --`cconfig`, --`cconfig`.
- added --`config`, --`config` parameter to configure default parameters.
- added Alt-Arrow hotkeys to the editor to scroll through the file without moving the cursor.
- fix the editor for Python 3.12.
- added `KEY_BTAB`(Shift+Tab) to the editor to decrease indent of the current line.
- added functionality to the editor to jump to specific line using `^E`.
- added functionality to search the file in the editor using `^F`.
- added functionality to put the editor in the background on UNIX using `^B`.
- added functionality to reload the file to the editor using `^R`.

### Bugfixes

- better performance in editor.
- changed windows-curses dependency for better char-detection experience.
- fix Bug where the editor would show the wrong cursor position.


## [1.6.4] - 2023-11-14

### Minor Changes

- providing a directory as an argument will no longer result in a recursive query. Recursion will still be possible using file-patterns.
- added -`d`, --`dirs` parameter to display all found directories.

### Bugfixes

- tested compatibility with pypy-3.7 and pypy-3.10.


## [1.6.3] - 2023-10-31

### Bugfixes

- compatibility for Python v3.12.


## [1.6.2] - 2023-10-10

### Minor Changes

- special characters like ␛ and ␀ will now be able to be used in the editor.
- added -`w`, --`wordcount` parameter to count the occurrence of every token in all given files.

### Bugfixes

- fix Bug where the colors used were not consistent.
- fix Bug where the --`eval`, --`EVAL` parameter would crash on invalid expressions.
- fix Bug where `trunc=` and `[a:b]` would crash on arithmetic errors.


## [1.6.1] - 2023-09-22

### Minor Changes

- added -`!`, --`edit` parameter to open a simple editor to write/edit any provided File. 
- renamed --`chr`, --`chr` to --`chr`, --`char`.
- cat_win will now detect simple zip-archives and display the contained files.
- When using the Parameter Variant -`E` from -`E`, --`echo` the input will be decoded with unicode sequences.
- a combination of using --`number` and --`file-prefix` will result in a prefix of the scheme \<sourcefile\>:\<lineno\> in order to support GNU-style link formats.


## [1.6.0] - 2023-08-22

### Minor Changes

- encoding the content in base64 with --`b64e` will now also include the lineprefix.
- added -`U`, --`url` parameter to display the contents on any url passed in.
- the -`p`, --`peek` parameter will no longer display anything when searching for substrings or patterns.
- the --`nb`, --`nobreak` parameter will now also skip the 'open in binary mode' - dialogue.
- removed -`t`, --`tabs` and --`eof`, --`eof` parameters.
- added --`chr`, --`chr` parameter to display most special characters as readable tokens.
- changed -`E`, --`ECHO` to -`E`, --`echo`.
- added support for octal numbers when evaluating expressions using --`eval`.

### Bugfixes

- implemented more exception handling.
- fix Bug where files would not be processed in the order in which they were provided.
- fix Bug where the repl would crash in rare cases.
- fix Bug where the --`files` parameter would display incorrect results.
- fix Bug where negative hexadecimal and binary numbers would not be recognized using --`eval`.


## [1.5.1] - 2023-08-12

### Bugfixes

- fix Bug where the OS would not be properly deteced.


## [1.5.0] - /

### Minor Changes

- display unknown arguments in order to indicate an erroneous command call.
- display argument suggestions to help fix an erraneous command call.
- -`G`, --`GREP` now shows the found keywords and matched patterns in the order in which they were found.
- included more special characters like '␉', '␀' in the rawviewer.
- allow for --`peek` to be used with the rawviewer.
- added --`fp`, --`file-prefix` parameter to include the file in every line prefix.
- added --`dot`, `--dotfiles` parameter to include dotfiles.
- added --`plain`, --`plain-only` parameter to skip all non-plain files automatically.
- warnings and errors will now be printed on the stderr-stream instead of stdout.
- display warning when trying to pipe a file into itself.
- added --`oct`, --`OCT` parameter to convert octal numbers.
- added some new bugs to fix later.

### Bugfixes

- fix Bug where --`sort` would not correctly sort uppercase characters inbetween lowercase characters and have problems with special chars like 'ß', 'µ' ...
- fix Bug where -`G`, --`GREP` would not show prefixes like line number or line length.
- fix Bug where the asterisk symbol (`*`) would not display correctly when using -`f`, --`files` and a keyword has been found.
- fix Bug where the behaviour was unexpected when using `-g`, --`grep` but not providing any literal or pattern.
- fix Bug where the rawviewer would crash when using a different encoding.
- fix Bug where the -`p`, --`peek` parameter would crash when using a different encoding.
- fix Bug where --`bin`, --`dec` and --`hex` would display wrong outputs on negative numbers.

## [1.4.3] - 2023-07-11

### Minor Changes

- added --`eval`, --`EVAL` parameter to evaluate simple mathematical equations within any text.
- added --`sort`, --`sort` parameter to sort all lines alphabetically.
- added `!clear` command to the cat repl, to reset/delete all previously defined parameters.
- added -`G`, --`GREP` parameter to *only* show the substrings found or matching any queried pattern.

### Bugfixes

- fix Bug where the repl command `!del` would not properly work when using a different command form.
- fix Bug where the `trunc` parameter would crash on not-evaluable inputs.
- fix Bug where the repl would unnecessarily import the clipboard module for each line again (when using the --`clip` parameter).
- fix Bug where the output of `find=` and `match=` was inconsistent and undeterministic.
- fix Bug where the `slice` and `replace` operators could only be used once per command.
- fix Bug where you could not `replace` certain substrings (individual chars are now escapable with **`\`**)


## [1.4.2] - 2023-05-13

### Minor Changes

- display a warning about resources when opening a large file.

### Bugfixes

- made some efficiency improvements.
- fixed a DeprecationWarning.


## [1.4.1] - 2023-05-04

### Minor Changes

- renamed -`d`, --`debug` to --`debug`, --`debug` and hid it from the help menu.
- renamed -`R`, --`reconfigure` to -`R`, --`R`.
- added --`Rin`, --`Rout`, --`Rerr` parameters to specificly reconfigure the stdin, stdout or stderr stream to the given encoding.
- added `!help` command to the cat-repl (cats) in order to see a short help display explaining all other parameters.
- added `!exit` command to the cat-repl (cats) in order to exit repl
- added `!see` command to the cat-repl (cats) in order to see the currently active parameters within one repl session.
- added `!add <OPTION>` and `!del <OPTION>` command to the cat-repl (cats) in order to change the parameters within one repl session.

### Bugfixes

- fix Bug where `match=` and `find=` would display the wrong indices.


## [1.4.0] - 2023-04-21

### Major Changes

- added `cats` entry point, for a repl version of the programm. This way you can enter and edit custom input line by line, instead of restarting the programm every time. Useful for the number conversion feature or a line by line base64 encoding/decoding (note that some parameters will not work with this entry-point since they will not make any sense in the context).
- added -`R`, --`reconfigure` parameter to decide if the standard-input (stdin) and standard-output (stdout) should be reconfigured to the parsed encoding parameter. Some repls handle text encoding different than others, so there is no uniform output when using uncommon encoding formats. Using this parameter the users can decide for themselves if the stdout should be encoded. Some users may experience readable console output when using the parameter while others may experience it when not using the argument.

### Minor Changes

- searching for patterns or literals within a file now also works for files that have been opened in binary mode (beware that some keywords might be overlooked).
- --`hexview` and --`binview` will now, dependant on the installed font, also show specific symbols for carriage return and line feed.
- creating a file with an specific text encoding set will now result in an actually encoded file.
- opening a file in binary will no longer display the `b''` wrapper.

### Bugfixes

- fix Bug where the ENTER-char '⏎' would be displayed incorrectly when using different encodings.


## [1.3.1] - 2023-04-10

### Minor Changes

- -`f`, --`files` now shows a `*` symbol on specific files, indicating the file contains a keyword or pattern that has been searched for using `find=` or `match=`.


## [1.3.0] - 2023-03-29

### Major Changes

- renamed -`k`, --`keyword` to -`g`, --`grep`.
- removed `requests` dependency.

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
- elevated dependency `colorama` from >=0.4.5 to >=0.4.6 (also switched from init() to just_fix_windows_console()).

### Minor Changes

- added appeal to raise official github issue when encountering an exception.
- added ability to create files in subdirectories that do not yet exist. The path will be created in the process, on error it will be cleaned up again.
- redesigned --config menu.
- added file sizes to -`F`, --`FILES`.
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
- added -`F`, --`FILES` parameter which ONLY shows the found files. (useful when searching files with pattern like "\*\*/\*.txt").

### Bugfixes

- fix Bug where background colors would colorize linebreaks and unnecessary whitespaces.
- fix Bug where parameters including `-`-characters (like "test-file.txt") would not be recognized as an unknown file to write.


## [1.1.0] - 2023-02-18

This release fully focuses on cleaning up, patching as many Bugs as possible, and renaming commands to a more logical name.

### Major changes

- changed the entrypoint `cat` to `catw`. This change was made to resolve the conflict on various platforms using `cat` natively.

- changed -`x`, --linelength parameter to -`l`, --linelength.
- changed -`s`, --`squeeze` parameter to -`u`, --`unique`.
- changed -`c`, --`count` parameter to -`s`, --`sum`.
- changed -`col`, --nocolor parameter to --`nc`, --nocolor.

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
