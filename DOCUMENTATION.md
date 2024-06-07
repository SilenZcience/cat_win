<div align="center">
<h2 align="center">cat_win</h2>
   <p align="center">
      Simple Command-line Tool made in Python
      <br/>
      <a href="https://github.com/SilenZcience/cat_win/blob/main/cat_win/cat.py">
         <strong>Explore the code »</strong>
      </a>
      <br/>
      <br/>
      <a href="https://github.com/SilenZcience/cat_win/issues">Report Bug</a>
      ·
      <a href="https://github.com/SilenZcience/cat_win/issues">Request Feature</a>
   </p>
</div>

<details>
   <summary>Table of Contents</summary>
   <ol>
      <li>
         <a href="#arguments--options">Arguments & Options</a>
         <ul>
            <li>
               <a href="#general-information">Quick-Find Headers</a>
               <ul>
                  <li><a href="#prefix">Line Prefix</a></li>
                  <li><a href="#simplereplace">Special Characters</a></li>
                  <li><a href="#linemanipulation">Line Manipulation</a></li>
                  <li><a href="#input">Input Types</a></li>
                  <li><a href="#summary">Summaries</a></li>
                  <li><a href="#search">Search and Match</a></li>
                  <li><a href="#meta">Meta Information</a></li>
                  <li><a href="#mathematical">Mathematical</a></li>
                  <li><a href="#byteview">Byte Representation</a></li>
                  <li><a href="#edit">Editor</a></li>
                  <li><a href="#settings">Settings/Behaviour</a></li>
                  <li><a href="#configuration">Configuration</a></li>
                  <li><a href="#encoding">Text Encoding</a></li>
               </ul>
            </li>
            <li>
               <a href="#general-information">General Information</a>
               <ul>
                  <li><a href="#-h---help">-h, --help</a></li>
                  <li><a href="#-v---version">-v, --version</a></li>
                  <li><a href="#--debug---debug">--debug, --debug</a></li>
                  <li><a href="#-l---linelength">-l, --linelength</a></li>
                  <li><a href="#-n---number">-n, --number</a></li>
                  <li><a href="#--fp---file-prefix">--fp, --file-prefix</a></li>
                  <li><a href="#-e---ends">-e, --ends</a></li>
                  <li><a href="#--chr---char">--chr, --char</a></li>
                  <li><a href="#-b---blank">-b, --blank</a></li>
                  <li><a href="#-p---peek">-p, --peek</a></li>
                  <li><a href="#-r---reverse">-r, --reverse</a></li>
                  <li><a href="#-u---unique">-u, --unique</a></li>
                  <li><a href="#--sort---sort">--sort, --sort</a></li>
                  <li><a href="#--sortl---sortlength">--sortl, --sortlength</a></li>
                  <li><a href="#--sf---specific-format">--sf, --specific-format</a></li>
                  <li><a href="#-e---echo">-E, --echo</a></li>
                  <li><a href="#----stdin">-, --stdin</a></li>
                  <li><a href="#-o---oneline">-o, --oneline</a></li>
                  <li><a href="#-u---url">-U, --url</a></li>
                  <li><a href="#-f---files">-f, --files</a></li>
                  <li><a href="#-d---dirs">-d, --dirs</a></li>
                  <li><a href="#-s---sum">-s, --sum</a></li>
                  <li><a href="#-w---wordcount">-w, --wordcount</a></li>
                  <li><a href="#--cc---charcount">--cc, --charcount</a></li>
                  <li><a href="#-g---grep">-g, --grep</a></li>
                  <li><a href="#--nk---nokeyword">--nk, --nokeyword</a></li>
                  <li><a href="#--nb---nobreak">--nb, --nobreak</a></li>
                  <li><a href="#-a---attributes">-a, --attributes</a></li>
                  <li><a href="#-m---checksum">-m, --checksum</a></li>
                  <li><a href="#--strings---strings">--strings, --strings</a></li>
                  <li><a href="#--b64d---b64d">--b64d, --b64d</a></li>
                  <li><a href="#--b64e---b64e">--b64e, --b64e</a></li>
                  <li><a href="#--eval---eval">--eval, --EVAL</a></li>
                  <li><a href="#--hex---hex">--hex, --HEX</a></li>
                  <li><a href="#--dec---dec">--dec, --DEC</a></li>
                  <li><a href="#--oct---oct">--oct, --OCT</a></li>
                  <li><a href="#--bin---bin">--bin, --BIN</a></li>
                  <li><a href="#--binview---binview">--binview, --binview</a></li>
                  <li><a href="#--hexview---hexview">--hexview, --HEXVIEW</a></li>
                  <li><a href="#----edit">-!, --edit</a></li>
                  <li><a href="#----hexedit">-#, --hexedit</a></li>
                  <li><a href="#-m---more">-M, --more</a></li>
                  <li><a href="#-b---raw">-B, --raw</a></li>
                  <li><a href="#-c---clip">-c, --clip</a></li>
                  <li><a href="#--dot---dotfiles">--dot, --dotfiles</a></li>
                  <li><a href="#--plain---plain-only">--plain, --plain-only</a></li>
                  <li><a href="#--nc---nocolor">--nc, --nocolor</a></li>
                  <li><a href="#--config---config">--config, --config</a></li>
                  <li><a href="#--cconfig---cconfig">--cconfig, --cconfig</a></li>
                  <li><a href="#--config-clear---config-reset">--config-clear, --config-reset</a></li>
                  <li><a href="#--cconfig-clear---cconfig-reset">--cconfig-clear, --cconfig-reset</a></li>
                  <li><a href="#--config-remove---cconfig-remove">--config-remove, --cconfig-remove</a></li>
                  <li><a href="#-r---rstream">-R, --R&ltstream&gt</a></li>
                  <li><a href="#encx-encx">enc=X, enc&#42889;X</a></li>
                  <li><a href="#findx-findx">find=X, find&#42889;X</a></li>
                  <li><a href="#matchx-matchx">match=X, match&#42889;X</a></li>
                  <li><a href="#truncxy-truncxy">trunc=X&#42889;Y, trunc&#42889;X&#42889;Y</a></li>
                  <li><a href="#ab">[a,b]</a></li>
                  <li><a href="#abc">[a&#42889;b&#42889;c]</a></li>
               </ul>
            </li>
         </ul>
      </li>
   </ol>
</details>
</br>

```console
> catw [FILE]... [OPTION]...
> catw --help
```

```console
> cats [OPTION]...
> cats --help
```

# <a id="arguments">Arguments & Options</a>

| Argument / Option | Description | works in REPL |
|-------------------|-------------|:--------------:|
| *<a href="#-h---help">-h, --help</a>* | show help message and exit |✔|
| *<a href="#-v---version">-v, --version</a>* | output version information and exit |✔|
| *<a href="#--debug---debug">--debug, --debug</a>* | show debug information |✔|
||||
| *<a href="#-l---linelength">-l, --linelength</a>* | display the length of each line |✔|
| *<a href="#-n---number">-n, --number</a>* | number all output lines |✔|
| *<a href="#--fp---file-prefix">--fp, --file-prefix</a>* | include the file in every line prefix |❌|
||||
| *<a href="#-e---ends">-e, --ends</a>* | mark the end of each line |✔|
| *<a href="#--chr---char">--chr, --char</a>* | display special characters |✔|
||||
| *<a href="#-b---blank">-b, --blank</a>* | hide empty lines |✔|
| *<a href="#-p---peek">-p, --peek</a>* | only print the first and last lines |❌|
| *<a href="#-r---reverse">-r, --reverse</a>* | reverse output |❌|
| *<a href="#-u---unique">-u, --unique</a>* | suppress repeated output lines |❌|
| *<a href="#--sort---sort">--sort, --sort</a>* | sort all lines alphabetically |❌|
| *<a href="#--sortl---sortlength">--sortl, --sortlength</a>* | sort all lines by length |❌|
| *<a href="#--sf---specific-format">--sf, --specific-format</a>* | automatically format specific file types |❌|
||||
| *<a href="#-e---echo">-E, --echo</a>* | handle every following parameter as stdin |❌|
| *<a href="#----stdin">-, --stdin</a>* | use stdin |❌|
| *<a href="#-o---oneline">-o, --oneline</a>* | take only the first stdin-line |✔|
| *<a href="#-u---url">-U, --url</a>* | display the contents of any provided url |❌|
||||
| *<a href="#-f---files">-f, --files</a>* | list applied files and file sizes |❌|
| *<a href="#-d---dirs">-d, --dirs</a>* | list found directories |❌|
| *<a href="#-s---sum">-s, --sum</a>* | show sum of lines |❌|
| *<a href="#-w---wordcount">-w, --wordcount</a>* | display the wordcount |❌|
| *<a href="#--cc---charcount">--cc, --charcount</a>* | display the charcount |❌|
||||
| *<a href="#-g---grep">-g, --grep</a>* | only show lines containing queried keywords or patterns |✔|
| *<a href="#--nk---nokeyword">--nk, --nokeyword</a>* | inverse the grep output |✔|
| *<a href="#--nb---nobreak">--nb, --nobreak</a>* | do not interrupt the output |✔|
||||
| *<a href="#-a---attributes">-a, --attributes</a>* | show meta-information about the files |❌|
| *<a href="#-m---checksum">-m, --checksum</a>* | show the checksums of all files |❌|
| *<a href="#--strings---strings">--strings, --strings</a>* | print the sequences of printable characters |✔|
||||
| *<a href="#--b64d---b64d">--b64d, --b64d</a>* | decode the input from base64 |✔|
| *<a href="#--b64e---b64e">--b64e, --b64e</a>* | encode the input to base64 |✔|
| *<a href="#--eval---eval">--eval, --EVAL</a>* | evaluate simple mathematical equations |✔|
| *<a href="#--hex---hex">--hex, --HEX</a>* | convert hexadecimal numbers to binary, octal and decimal |✔|
| *<a href="#--dec---dec">--dec, --DEC</a>* | convert decimal numbers to binary, octal and hexadecimal |✔|
| *<a href="#--oct---oct">--oct, --oct</a>* | convert octal numbers to binary, decimal and hexadecimal |✔|
| *<a href="#--bin---bin">--bin, --BIN</a>* | convert binary numbers to octal, decimal and hexadecimal |✔|
||||
| *<a href="#--binview---binview">--binview, --binview</a>* | display the raw byte representation in binary |❌|
| *<a href="#--hexview---hexview">--hexview, --HEXVIEW</a>* | display the raw byte representation in hexadecimal |❌|
||||
| *<a href="#----edit">-!, --edit</a>* | open each file in a simple editor |❌|
| *<a href="#----hexedit">-#, --hexedit</a>* | open each file in a simple hex-editor |❌|
| *<a href="#-m---more">-M, --more</a>* | page through the file step by step |❌|
| *<a href="#-b---raw">-B, --raw</a>* | open the file as raw bytes |❌|
||||
| *<a href="#-c---clip">-c, --clip</a>* | copy output to clipboard |✔|
| *<a href="#--dot---dotfiles">--dot, --dotfiles</a>* | additionally query and edit dotfiles |❌|
| *<a href="#--plain---plain-only">--plain, --plain-only</a>* | ignore non-plaintext files automatically |❌|
| *<a href="#--nc---nocolor">--nc, --nocolor</a>* | disable colored output |✔|
||||
| *<a href="#--config---config">--config, --config</a>* | change default parameters |✔|
| *<a href="#--cconfig---cconfig">--cconfig, --cconfig</a>* | change color configuration |✔|
| *<a href="#--config-clear---config-reset">--config-clear, --config-reset</a>* | reset the config to default settings |✔|
| *<a href="#--cconfig-clear---cconfig-reset">--cconfig-clear, --cconfig-reset</a>* | reset the color config to default settings |✔|
| *<a href="#--config-remove---cconfig-remove">--config-remove, --cconfig-remove</a>* | remove the config-file |✔|
||||
| *<a href="#-r---rstream">-R, --R\<stream\></a>* | reconfigure the std-stream(s) with the parsed encoding </br> \<stream\> = 'in'/'out'/'err' (default is stdin & stdout) | ✔ |
||||
| *<a href="#encx-encx">enc=X, enc&#42889;X</a>* | set file enconding to X (default is utf-8) |✔|
| *<a href="#findx-findx">find=X, find&#42889;X</a>* | find/query a substring X in the given files |✔|
| *<a href="#matchx-matchx">match=X, match&#42889;X</a>* | find/query a pattern X in the given files |✔|
| *<a href="#truncxy-truncxy">trunc=X&#42889;Y, trunc&#42889;X&#42889;Y</a>* | truncate file to lines X and Y (python-like) |❌|
||||
| *<a href="#ab">[a,b]</a>* | replace a with b in every line |✔|
| *<a href="#abc">[a&#42889;b&#42889;c]</a>* | python-like string indexing syntax (line by line) |✔|


### General Information

- Order of Operation
   - Files will be used in the same Order as they were provided.
   - When passing in a File-pattern or a Directory the Files will be used in the Order in which they were found. This will often be alphabetically, although this is not guaranteed.
   - URLs will be used in the Order as they were provided, after all Files have been displayed.
   - Arguments will for the most part be used in the same Order as they were provided, yet there are some Exceptions.
- Case-Sensitivity
   - The Arguments are case-sensitive.
   - Some Arguments have slightly different Behaviour when using upper- or lowercase Letters.
- Chaining
   - One-letter Arguments can be chained together (e.g. `-l -n -c` is equivalent to `-lnc`)
- Input Order
   - No specific Order for passing in Arguments or Files is neccessary.
   - Arguments, Files and Urls may be passed in without any Rules to ordering (e.g. catw file1 -argument url -argument2 file2).
   - If the same Argument is passed in multiple times only the first occurence is being counted.
- Unknown Files
   - When encountering unknown Files the User is being prompted to write to Stdin.
   - The Stdin is being used to then write the Files.
   - When using the --stdin Parameter unknown Files will be automatically written with the content of StdIn.
- Coloring
   - The Output will contain Color by Default.
   - cat_win will not explicitly add Color if the Argument <a href="#--nc---nocolor">--nc, --nocolor</a> is used. (The Output may still contain Color if a File itself contains the ANSI-Color-Coding.)
   - The Output will be stripped of any Color if the Output is piped and the Configuration `strip_color_on_pipe` is set to `true` .

- - - -
### <a id="-h---help">-h, --help</a>

Displays the help Message.
This Message is for the most part equivalent to the Table above.
The Code execution will stop after showing this Message.
This Argument has Priority over all other Arguments, hence the Order of passing this Argument in makes no Difference.
If no Arguments or Files are provided, the help Parameter will be used by Default.

### <a id="-v---version">-v, --version</a>

Displays a short Message containing basic Information about the Code.
This includes the version Number but also the installation Directory.
The Code execution will stop after showing this Message.

```console
> catw -v

------------------------------------------------------------------------------
Catw <Version> - from <Path>
------------------------------------------------------------------------------

Built with:     Python <PyVersion>
Install time:   YYYY-MM-DD HH:MM:SS
Author:         Silas A. Kraume
```

### <a id="--debug---debug">--debug, --debug</a>

Displays debug Information before and after the Code execution.
This Argument is not shown in the default help Message and is provided for Developers/Development.

- - - -
<a id="prefix"></a>
### <a id="-l---linelength">-l, --linelength</a>

Displays the Length of each Line as a Prefix to the Line itself.
This Argument will be used at the end such that other Arguments may influence the Length of the Lines beforehand.

```console
> catw test.txt -l
[ 6] line 1
[10] long_line!
```

### <a id="-n---number">-n, --number</a>

Numbers all Lines.
The Numberisation is done at the Beginning such that different Arguments may disorganize the Numberisation again.
Each File starts with line Number 1 therefor multiple Files are not consecutively numbered.
If multiple Files are provided, the Prefix will also include the Number of the File.

```console
> catw test.txt -n
1) line 1
2) line 2
```
```console
> catw test.txt test.txt -n
1.1) line 1
1.2) line 2
2.1) line 1
2.2) line 2
```

### <a id="--fp---file-prefix">--fp, --file-prefix</a>

Shows the Path to the File in each Line prefix.
This can be useful when querying for Substrings or Patterns such that only a few Lines are being displayed.
Using this Argument in uppercase (--FP, --FILEPREFIX) will result in the Path being shown as the url file Protocol.
This can be useful in case the Terminal supports interacting with Links such that the File can be instantly opened.
Using the lowercase Argument in Combination with the <a href="#-n---number">-n, --number</a> Parameter a GNU-style link format will be displayed.

```console
> catw test.txt --fp
<Path>/test.txt line 1
<Path>/test.txt line 2
```
```console
> catw test.txt --FP -n
1) file:///<Path>/test.txt line 1
2) file:///<Path>/test.txt line 2
```
```console
> catw test.txt --fp -n
<Path>/test.txt:1 line 1
<Path>/test.txt:2 line 2
```

- - - -
<a id="simplereplace"></a>
### <a id="-e---ends">-e, --ends</a>

Displays a '$' Character at the End of each Line.
This can be useful to detect Whitespaces.
The Character to display can be configured using the `end_marker_symbol` element in the config menu (<a href="#--config---config">--config, --config</a>).

```console
> catw test.txt --ends
Tab:    $
line 2$
```

### <a id="--chr---char">--chr, --char</a>

Replaces every special Character with a readable Token.
Each Token starts with the '^' Character, followed by a short ASCII Descriptor.
Note that the special Char ␛ will not be displayed as ^ESC because it is needed for the colored output.

```console
> catw test.txt
    
```
```console
> catw test.txt --chr
^SUB^SUB^NUL^SUB^SUB^TAB^BEL
```

- - - -
<a id="linemanipulation"></a>
### <a id="-b---blank">-b, --blank</a>

Removes empty Lines from the Output.
Beware that other Arguments can change a Line to be not empty beforehand.
When toggling the `blank_remove_ws_lines` element in the config menu (<a href="#--config---config">--config, --config</a>) also lines which only contain Whitespaces such as Space or Tab will be removed from the Output.

```console
> catw test.txt -nb
1) Empy Line follows:
3) Empty Line just got skipped!
```

### <a id="-p---peek">-p, --peek</a>

Only displays the first and last 5 Lines of each File.
Between the Beginning and End of the File will be displayed how many Lines have been skipped.
Useful for getting a quick impression of how data in a given File is structured.
This Argument is ignored when provided alongside with Queries for Substrings of Patterns or the <a href="#-m---more">-M, --more</a> Parameter.
Does nothing when the File has at most 10 Lines.
The `peek_size` element in the config menu (<a href="#--config---config">--config, --config</a>) defines how many Lines to display.

```console
> catw test.txt -p
Line 1
Line 2
Line 3
Line 4
Line 5
  :
  10
  :
Line 16
Line 17
Line 18
Line 19
Line 20
```

### <a id="-r---reverse">-r, --reverse</a>

Simply reverses the Content of all Files as well as the Ordering of all Files themselves.

```console
> catw test1.txt test2.txt -p
Line 2 From Test2
Line 1 From Test2
Line 2 From Test1
Line 1 From Test1
```

### <a id="-u---unique">-u, --unique</a>

Suppresses repeated Lines if they occur exactly one after the other.

```console
> catw test.txt
This is a line!
This is a line!
This is a line!
This is also a line!
This is a line!
```
```console
> catw test.txt --unique
This is a line!
This is also a line!
This is a line!
```

### <a id="--sort---sort">--sort, --sort</a>

Sorts the Output alphabetically without case sensitivity.

```console
> catw test.txt --sort -n
2) A line that has been sorted to the top!
1) This line was originally at the top!
```

### <a id="--sortl---sortlength">--sortl, --sortlength</a>

Sorts the Output by Line Length.

```console
> catw test.txt --sortl -l
[13] A short line!
[21] This line was on top!
```

### <a id="--sf---specific-format">--sf, --specific-format</a>

Automatically format specific File Types.
Currently supported are .json and .xml.

```console
> catw --sf -E '{"person":{"name":"Alice","age":25,"employees":[{"name":"Bob"},{"name:":"David"}]}}'
{
  "person": {
    "name": "Alice",
    "age": 25,
    "employees": [
      {
        "name": "Bob"
      },
      {
        "name:": "David"
      }
    ]
  }
}
```
```console
> catw --sf -E '<lib><book id="1"><title>Cats</title></book><book id="2"></book></lib>'
<?xml version="1.0" ?>
<lib>
  <book id="1">
    <title>Cats</title>
  </book>
  <book id="2"/>
</lib>
```

- - - -
<a id="input"></a>
### <a id="-e---echo">-E, --echo</a>

Everything passed in after this Argument will be handled as its own File.
It is not possible to break out of this state therefor this Parameter must be used last.
The Input is unicode-escaped (\\n will be interpreted as an actual Newline) if the Config Option `unicode_escaped_echo` is set but in Case of an unicode-error the Input will simply be used literally.
This way it is possible to define new lines (\\n) or other special characters.

```console
> catw -l --echo -n The last 'Parameter' does not count!\nThis is not a newline!
[57] -n The last Parameter does not count!\nThis is not a newline!
```

```console
> catw -l -E -n The last 'Parameter' does not count!\nThis is a newline!
[37] -n The last Parameter does not count!
[18] This is a newline!
```

### <a id="----stdin">-, --stdin</a>

Using this Argument allows to pass in Data via the Stdin Stream.
The Stdin Pipe will be handled as its own File.

```console
> echo Hello World! | catw - -n
1) Hello World!
```

### <a id="-o---oneline">-o, --oneline</a>

Limits the Stdin Stream to the first Line.
Can only be used in Combination with <a href="#----stdin">-, --stdin</a>.

```console
> catw test.txt
Line 1
Line 2
Line 3
```
```console
> catw test.txt | catw - -o
Line 1
```

### <a id="-u---url">-U, --url</a>

When using this Parameter it is possible to provide URLs as Arguments.
Should an URL not have a scheme (http(s):// or fttp(s):// ...) the default scheme (https://) is being used.
Provided URLs are simply curl'd and handled as its own File.
When not providing a raw Data URL the Content will include the HTML Elements.

```console
> catw -U https://github.com/SilenZcience/cat_win > cat.html
```

- - - -
<a id="summary"></a>
### <a id="-f---files">-f, --files</a>

Displays a small Summary at the End of Code execution showing every File used and their file Size.
Using this Argument in uppercase (-F, --FILES) will ONLY display the Summary and stop Code execution.

```console
> catw test.txt -f
Line 1
Line 2

applied FILE(s):
        13.0 B   <Path>/test.txt
Sum:    13.0 B
Amount: 1
```
```console
> catw test.txt --FILES
applied FILE(s):
        13.0 B   <Path>/test.txt
Sum:    13.0 B
Amount: 1
```

### <a id="-d---dirs">-d, --dirs</a>

Displays a small Summary at the End of Code execution showing every Directory found.
Using this Argument in uppercase (-D, --DIRS) will ONLY display the Summary and stop Code execution.

```console
> catw ./** -d
Line 1
Line 2
...

found DIR(s):
        <Path>
        <Path>/<PathA>
        <Path>/<PathA>/<PathAA>
        <Path>/<PathB>
Amount: 4
```
```console
> catw ./** -D
found DIR(s):
        <Path>
        <Path>/<PathA>
        <Path>/<PathA>/<PathAA>
        <Path>/<PathB>
Amount: 4
```

### <a id="-s---sum">-s, --sum</a>

Displays a small Message at the End of Code execution showing the Number of the Amount of all Lines received.
Using this Argument in uppercase (-S, --SUM) will ONLY show this Message as well as a small Summary.
This Summary will show the line Sum for each File.
Duplicate Files will not be displayed multiple times within the Summary.
The uppercase version of this Parameter will stop Code execution.

```console
> catw test.txt --sum
Line 1
Line 2

Lines (Sum): 2
```
```console
> catw test.txt test.txt --SUM
File             LineCount
<Path>/test.txt  2

Lines (Sum): 4
```

### <a id="-w---wordcount">-w, --wordcount</a>

Displays a Summary of all Tokens/Words found in the given Files and how frequent they occured.
The Output will be sorted by the Frequency of Occurrence starting with the most common Word.
In Addition the used Files will be displayed beforehand.
Using this Argument in uppercase (-W, --WORDCOUNT) will ONLY display this Message and stop Code execution.

```console
> catw test.txt
it is true for all that, that that 'that' which that 'that' refers to is not the same 'that' which that 'that' refers to
```
```console
> catw test.txt -W
The word count includes the following files:
    <Path>

that: 9
': 8
is: 2
refers: 2
to: 2
which: 2
,: 1
all: 1
for: 1
it: 1
not: 1
same: 1
the: 1
true: 1
```

### <a id="--cc---charcount">--cc, --charcount</a>

Displays a Summary of all Chars/Letters found in the given Files and how frequent they occured.
Whitespace Chars like Spaces and Tabs will be wrapped with quotes.
The Output will be sorted by the Frequency of Occurrence starting with the most common Char.
In Addition the used Files will be displayed beforehand.
Using this Argument in uppercase (--CC, --CHARCOUNT) will ONLY display this Message and stop Code execution.

```console
> catw test.txt
it is true for all that, that that 'that' which that 'that' refers to is not the same 'that' which that 'that' refers to
```
```console
> catw test.txt --CC
The char count includes the following files:
    <Path>

t: 24
' ': 23
h: 14
a: 11
': 8
e: 7
r: 6
i: 5
s: 5
o: 4
f: 3
c: 2
l: 2
w: 2
,: 1
m: 1
n: 1
u: 1
```

- - - -
<a id="search"></a>
### <a id="-g---grep">-g, --grep</a>

Skips every Line that does not contain any matched Patterns or queried Substrings.
Literals or Patterns to look for can be set using the <a href="#findx-findx">find=X, find&#42889;X</a> and <a href="#matchx-matchx">match=X, match&#42889;X</a> Keywords.
Using this Argument in uppercase (-G, --GREP) will ONLY display the parts of each Line that matched any Pattern or Literal.
Should multiple Queries be found in the same Line they will be seperated by comma.
The uppercase Variant of this Parameter has priority (over the lowercase Variant as well as <a href="#--nk---nokeyword">--nk, --nokeyword</a>).

```console
> catw test.txt find=cat -gn
1) cat_win!
4) one cat!& two cat!& three cat
```
```console
> catw test.txt match=.cat. -Gn
4)  cat!, cat!
```

### <a id="--nk---nokeyword">--nk, --nokeyword</a>

Inverse to the <a href="#-g---grep">-g, --grep</a> Argument.
Skips every Line that does contain any matched Patterns or queried Substrings.
The Combination of --nokeyword and <a href="#-g---grep">-g, --grep</a> means that no Output will be displayed.

```console
> catw test.txt find=cat -n --nk
2) This Line is boring
3) This Line also does not contain 'c a t'
5) This Line neither
```

### <a id="--nb---nobreak">--nb, --nobreak</a>

Using this Argument will open non-plaintext Files automatically without prompting the User.
In Addition the Output will not stop on queried Substrings or Patterns.
This Behaviour is included by Default when using <a href="#--nk---nokeyword">--nk, --nokeyword</a> or <a href="#-g---grep">-g, --grep</a>.

- - - -
<a id="meta"></a>
### <a id="-a---attributes">-a, --attributes</a>

Shows meta Information for each File provided and stops Code execution.
The meta Information includes file Size, Time of Access, -Modified and -Created.
On Windows OS Systems this Parameter will also display the classic file Attributes.

```console
> catw test.txt -a
<Path>/test.txt
Size:           1.55 KB
ATime:          YYYY-MM-DD HH:MM:SS.
MTime:          YYYY-MM-DD HH:MM:SS.
CTime:          YYYY-MM-DD HH:MM:SS.
+Archive, Indexed
-System, Hidden, Readonly, Compressed, Encrypted
```

### <a id="-m---checksum">-m, --checksum</a>

Shows different Checksums for each File provided and stops Code execution.
The displayed Checksums include CRC32, MD5, SHA1, SHA256 and SHA512.

```console
> catw test.txt -m
Checksum of '<Path>/test.txt':
        CRC32:   F67C071D
        MD5:     95de18c87649e804c15ccdd73ae6eddc
        SHA1:    cecdcba1cd12a9fdfdb32a1aa1bc40bdb9b1261c
        SHA256:  1d4bf9f69b9d1529a5f6231b4edeba61a86deeebf00060c4de6f67f0c4e3b711
        SHA512:  db9a71ef22360f171daa4e4aed033337f4f97812baf38a51bdd6ed64b5c2a0d4a5c4152e20b68f881df9e5f1087c1293853eac13f928b845b9b71c3ce517c9e3
```

### <a id="--strings---strings">--strings, --strings</a>

Only displays Sequences of printable Characters that exceed a certain Length.
This Length can be configured using the `strings_minimum_sequence_length` element in the config menu (<a href="#--config---config">--config, --config</a>).
The Delimeter of different Sequences on the same Line can be configured using the `strings_delimeter` element in the config menu.

```console
> catw --strings test.bin
/lib64/ld-linux-x86-64.so.2
__cxa_finalize
__libc_start_main
puts
libc.so.6
GLIBC_2.2.5
GLIBC_2.34
...
```

- - - -
<a id="mathematical"></a>
### <a id="--b64d---b64d">--b64d, --b64d</a>

Decodes a Base64 encoded Input and continues Code execution with the decoded Text.
This Parameter will be used before most other Arguments such that other Parameters will be used on the decoded Text.
This means a Base64 encoded Input is expected and neccessary.

```console
> echo SGVsbG8gV29ybGQ= | catw - --b64d
Hello World
```

### <a id="--b64e---b64e">--b64e, --b64e</a>

Encodes a given Text in Base64.
This Parameter will be used after most other Arguments such that other Parameter will be used on the plain Text beforehand.

```console
> echo Hello World | catw - --b64e
SGVsbG8gV29ybGQ=
```

### <a id="--eval---eval">--eval, --EVAL</a>

Evaluates simple mathematical Expressions within any given Text.
The mathematical Expressions may consist of paranthesis, Operators including Modulo (%) and Exponential (**),
as well as any Number in Hexadecimal, Decimal, Octal or Binary.
The evaluated Value of the Expression will by default be inserted back into the Position of the Text where the Expression was found.
In the uppercase Variant of the Parameter any non-mathematical Text will be stripped thus only evaluated Expressions will remain.
On Error The Expression will evaluate to '???'.

```console
> echo Calculate: (5 * 0x10 * -0b101) % (0o5 ** 2) ! | catw - --eval
Calculate: 0 !
```
```console
> echo Calculate: (5 * 0x10 * -0b101) % (0o5 ** 2) ! | catw - --EVAL
0
```

### <a id="--hex---hex">--hex, --HEX</a>

If a Line only contains a hexadecimal Number this Parameter will append the equivalent Value in Binary, Octal and Decimal.
Negative Numbers are allowed.
Numbers are allowed to start with the Prefix 0x.
When using the uppercase Variant (--HEX) the Numbers will not include their Prefixes (like 0x, 0b or 0o).

```console
> catw test.txt --hex
FF [Bin: 0b11111111, Oct: 0o377, Dec: 255]
0x610 [Bin: 0b11000010000, Oct: 0o3020, Dec: 1552]
```
```console
> catw test.txt --HEX
FF [Bin: 11111111, Oct: 377, Dec: 255]
0x610 [Bin: 11000010000, Oct: 3020, Dec: 1552]
```

### <a id="--dec---dec">--dec, --DEC</a>

If a Line only contains a decimal Number this Parameter will append the equivalent Value in Binary, Octal and Hexadecimal.
Negative Numbers are allowed.
When using the uppercase Variant (--DEC) the Numbers will not include their Prefixes (like 0x, 0b or 0o).

```console
> catw test.txt --dec
255 [Bin: 0b11111111, Oct: 0o377, Hex: 0xff]
1552 [Bin: 0b11000010000, Oct: 0o3020, Hex: 0x610]
```
```console
> catw test.txt --DEC
255 [Bin: 11111111, Oct: 377, Hex: ff]
1552 [Bin: 11000010000, Oct: 3020, Hex: 610]
```

### <a id="--oct---oct">--oct, --OCT</a>

If a Line only contains an octal Number this Parameter will append the equivalent Value in Binary, Decimal and Hexadecimal.
Negative Numbers are allowed.
Numbers are allowed to start with the Prefix 0o.
When using the uppercase Variant (--OCT) the Numbers will not include their Prefixes (like 0x, 0b or 0o).

```console
> catw test.txt --oct
0o377 [Bin: 0b11111111, Dec: 255, Hex: 0xff]
3020 [Bin: 0b11000010000, Dec: 1552, Hex: 0x610]
```
```console
> catw test.txt --OCT
0o377 [Bin: 11111111, Dec: 255, Hex: ff]
3020 [Bin: 11000010000, Dec: 1552, Hex: 610]
```

### <a id="--bin---bin">--bin, --BIN</a>

If a Line only contains a binary Number this Parameter will append the equivalent Value in Octal, Decimal and Hexadecimal.
Negative Numbers are allowed.
Numbers are allowed to start with the Prefix 0b.
When using the uppercase Variant (--BIN) the Numbers will not include their Prefixes (like 0x, 0b or 0o).

```console
> catw test.txt --bin
11111111 [Oct: 0o377, Dec: 255, Hex: 0xff]
0b11000010000 [Oct: 0o3020, Dec: 1552, Hex: 0x610]
```
```console
> catw test.txt --BIN
11111111 [Oct: 377, Dec: 255, Hex: ff]
0b11000010000 [Oct: 3020, Dec: 1552, Hex: 610]
```

- - - -
<a id="byteview"></a>
### <a id="--binview---binview">--binview, --binview</a>

Displays a BinaryViewer for each File passed in.
Special Characters like NewLine or BackSpace will be displayed as specific readable Chars if the Font and the Encoding do support that Behaviour.

```console
> catw test.txt --binview
<Path>\test.txt:
Address  00       01       02       03       04       05       06       07       08       ... # Decoded Text
00000000 01000011 01100001 01110100 01011111 01010111 01101001 01101110 00100001 00001010 ... # C a t _ W i n ! ␤
```

### <a id="--hexview---hexview">--hexview, --HEXVIEW</a>

Displays a Hexviewer for each File passed in.
Special Characters like NewLine or BackSpace will be displayed as specific readable Chars if the Font and the Encoding do support that Behaviour.
When using the uppercase Variant of this Parameter (--HEXVIEW) the hexadecimal Numbers within the Hexviewer will also be uppercase.

```console
> catw test.txt --hexview
<Path>\test.txt:
Address  00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F # Decoded Text
00000000 48 65 6c 6c 6f 20 57 6f 72 6c 64 20 46 72 6f 6d # H e l l o   W o r l d   F r o m
00000010 20 43 61 74 21 0a                               #   C a t ! ␤
```
```console
> catw test.txt --HEXVIEW
<Path>\test.txt:
Address  00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F # Decoded Text
00000000 48 65 6C 6C 6F 20 57 6F 72 6C 64 20 46 72 6F 6D # H e l l o   W o r l d   F r o m
00000010 20 43 61 74 21 0A                               #   C a t ! ␤
```

- - - -
<a id="edit"></a>
### <a id="----edit">-!, --edit</a>

Opens a simple Editor to write/edit the Content of any provided File one by one.
Not-existing Files will be opened first and existing Ones will be able to be edited after that.
The Editor will not save Changes automatically.
Files will be saved with the text Encoding defined by <a href="#encx-encx">enc=X, enc&#42889;X</a>.
Note that ^c (Ctrl-c) is reserved for the KeyboardInterrupt meaning that it will stop the entire Program instantly.
The Auto-Indendation Feature can be turned on in the config menu using the `editor_auto_indent` element.
The Indendation when using Auto-Indendation can be configured in the config menu (<a href="#--config---config">--config, --config</a>) using `editor_indentation`.
The Input inside the Find Prompt (see Key bindings) is unicode-escaped (\\n will be interpreted as an actual Newline) if the Config Option `unicode_escaped_editor_search` is set but in Case of an unicode-error the Input will simply be used literally.
On Windows this Feature uses the [windows-curses](https://pypi.org/project/windows-curses/) Module.
The currently supported Key bindings are as follows:

| Key(s) | default behaviour | shift click | control click | alt click |
|--------|:-----------------:|:-----------:|:-------------:|:---------:|
| <kbd>Arrows</kbd> | move cursor by char | move cursor by char | move cursor by word | scroll window by char |
| <kbd>Page Up/Down</kbd> | move cursor by page | move cursor by page | move cursor by page | scroll window by page |
| <kbd>Home/Pos</kbd> | move cursor to start of line | move cursor to start of line | move cursor to start of file | scroll window to start of file |
| <kbd>End</kbd> | move cursor to end of line | move cursor to end of line | move cursor to end of file | scroll window to end of file |
| <kbd>Tab</kbd> | insert a tab or </br> indent on empty line | decrease indent | - | - |
||||||
| <kbd>Enter</kbd> | write newline | write newline | write newline | - |
| <kbd>Backspace</kbd> | delete char on the left | delete char on the left | delete word on the left | delete char on the left |
| <kbd>Delete</kbd> | delete char on the right | delete char on the right | delete word on the right | delete char on the right |
||||||
| <kbd>Undo/^Z</kbd> | - | - | undo an action | - |
| <kbd>Redo/^Y</kbd> | - | - | redo an action | - |
||||||
| <kbd>Save/^S</kbd> | - | - | save changes | save changes |
| <kbd>Jump/^E</kbd> | - | - | prompt to jump to specific line | - |
| <kbd>Find/^F</kbd> | - | - | prompt to search in the file | - |
| <kbd>Background/^B</kbd> | - | - | put the editor in the background</br>(UNIX only) | - |
| <kbd>Reload/^R</kbd> | - | - | prompt to reload the file | - |
| <kbd>Insert/^I</kbd> | - | - | Insert a Byte Sequence | - |
| <kbd>Quit/^Q</kbd> | - | - | close editor</br>(prompt to save, if neccessary) | - |
| <kbd>Interrupt/^C</kbd> | - | - | interrupt program | - |

### <a id="----hexedit">-#, --hexedit</a>

Opens a simple Hex-Editor to write/edit the Content of any provided File one by one.
Not-existing Files will be opened first and existing Ones will be able to be edited after that.
The Editor will not save Changes automatically.
Note that ^c (Ctrl-c) is reserved for the KeyboardInterrupt meaning that it will stop the entire Program instantly.
The displayed Columns per Row can be configured in the config menu (<a href="#--config---config">--config, --config</a>) using `hex_editor_columns`.
On Windows this Feature uses the [windows-curses](https://pypi.org/project/windows-curses/) Module.
The currently supported Key bindings are as follows:

| Key(s) | default behaviour | shift click | control click | alt click |
|--------|:-----------------:|:-----------:|:-------------:|:---------:|
| <kbd>Arrows</kbd> | move cursor by byte | move cursor by byte | move cursor multiple bytes | - |
| <kbd>Page Up/Down</kbd> | move cursor by page | move cursor by page | move cursor by page | - |
| <kbd>Home/Pos</kbd> | move cursor to start of line | move cursor to start of line | move cursor to start of file | - |
| <kbd>End</kbd> | move cursor to end of line | move cursor to end of line | move cursor to end of file | - |
||||||
| <kbd>0-9 & A-F</kbd> | edit the current byte | - | - | - |
| <kbd><</kbd> | insert a new byte to the left | - | - | - |
| <kbd>> & ␣</kbd> | insert a new byte to the right | - | - | - |
| <kbd>Backspace</kbd> | reset current byte | reset current byte | remove current byte | reset current byte |
| <kbd>Delete</kbd> | reset current byte | reset current byte | remove current byte | reset current byte |
||||||
| <kbd>Save/^S</kbd> | - | - | save changes | save changes |
| <kbd>Jump/^E</kbd> | - | - | prompt to jump to a specific byte | - |
| <kbd>Find/^F</kbd> | - | - | prompt to search a byte(-sequence) in the file | - |
| <kbd>Background/^B</kbd> | - | - | put the hex-editor in the background</br>(UNIX only) | - |
| <kbd>Reload/^R</kbd> | - | - | prompt to reload the file | - |
| <kbd>Insert/^I</kbd> | - | - | Insert a Text Sequence | - |
| <kbd>Quit/^Q</kbd> | - | - | close hex-editor</br>(prompt to save, if neccessary) | - |
| <kbd>Interrupt/^C</kbd> | - | - | interrupt program | - |

### <a id="-m---more">-M, --more</a>

Page through the File Contents Step by Step.
Each Step the Output is paused until User Interaction.
The first Step always fills the entire Screen.
The following Steps have the Size as defined by the config Element `more_step_length`.
Display the available Commands by entering `?` or `h` or `help`.

```console
> catw file -M
line 1
line 2
...
line 29
> -- More ( 6%) --
line 30
...
> -- More (11%) --
...
```
```console
> catw file -M
...
> --More (10%) -- ?
H HELP       display this help message
Q QUIT       quit
N NEXT       skip to next file
L LINE       display current line number
D DOWN <x>   step x lines down
S SKIP <x>   skip x lines
J JUMP <x>   jump to line x
...
```

### <a id="-b---raw">-B, --raw</a>

Opens the given Files in Binary Mode.
Prints the Output as Raw Binary to the stdout-Stream.
The only valid Parameters in Combination to -`b`, --`raw` are <a href="#--b64e---b64e">--b64e, --b64e</a>, <a href="#--b64d---b64d">--b64d, --b64d</a> and <a href="#--strings---strings">--strings, --strings</a>.

```console
> catw img.png > copy.png
UnicodeEncodeError: 'charmap' codec can't encode character '\ufffd' in position 0: character maps to <undefined>
...
> catw img.png -R > copy.png
(works but copy.png is corrupted)
```
```console
> catw img.png --raw > copy.png
⇕
> catw img.png --b64e --raw | catw - --b64d --raw > copy.png
```

- - - -
<a id="settings"></a>
### <a id="-c---clip">-c, --clip</a>

Copies the entire Output to the Clipboard additionally to printing it to the Stdout Stream.

### <a id="--dot---dotfiles">--dot, --dotfiles</a>

When providing file Patterns or entire Directories cat_win will find every File including those set to hidden (e.g. on Windows OS).
However Dotfiles, meaning Files that start with a literal Dot, will not be found by Default.
Using this Parameter cat_win will also include Dotfiles.

```console
> catw * -F
found FILE(s):
        12.35 KB   <Path>/CHANGELOG.md
        1.06 KB    <Path>/LICENSE
        15.07 KB   <Path>/README.md
...
```
```console
> catw * -F --dot
found FILE(s):
        969.0 B    <Path>/.gitignore
        12.35 KB   <Path>/CHANGELOG.md
        1.06 KB    <Path>/LICENSE
        15.07 KB   <Path>/README.md
...
```

### <a id="--plain---plain-only">--plain, --plain-only</a>

By default the User is being prompted when a non-plaintext File is being encountered as to if the File should be opened in Binary or not.
Using --plain-only these Files will be automaticaly skipped.
Note that these Prompts are not descriptive enough to say that a File can only be opened in Binary.
Often the Problem is being fixed by providing another Codepage using the <a href="#encx-encx">enc=X, enc&#42889;X</a> Parameter.

### <a id="--nc---nocolor">--nc, --nocolor</a>

By default different Colors will be used to better highlight specific Parts of the Output or make original and changed Parts of a Line more distinguishable.
Using --nocolor will disable all Colors and only display the Output in plain monochrome Text.

- - - -
<a id="configuration"></a>
### <a id="--config---config">--config, --config</a>

Displays a user interactive config Menu allowing the User to change specific default parameters.
Stops Code execution after finishing the Configuration.
The config File will be saved to the installation Directory of cat_win which is by Default the Python directory.
This means that uninstalling cat_win may result in the config File being left over.
When using the Windows Executables this Parameter will have no (long term) Effect.
Valid Options are:
| Option | Description | Example | Default |
|--------|-------------|---------|---------|
| default_command_line | custom Command Line containing Parameters </br> used additionally to the specific Parameters </br> of the Program Call | -n 'find= ' | |
| default_file_encoding | the File Encoding used by Default | utf-16 | utf-8 |
| large_file_size | the Size (Bytes) at which a Warning occurs | 1024 | 104857600 (100Mb) |
| strip_color_on_pipe | indicate if the Output should be stripped of any Color | false | true |
| ignore_unknown_bytes | ignore unknown Bytes instead of replacing them with � | true | false |
| end_marker_symbol | define the Marker that will be displayed at EOL when using <a href="#-e---ends">-e, --ends</a> | ^EOL | $ |
| blank_remove_ws_lines | additionally remove whitespace Lines when using <a href="#-b---blank">-b, --blank</a> | true | false |
| peek_size | define the amount of Lines shown by <a href="#-p---peek">-p, --peek</a> | 10 | 5 |
| strings_minimum_sequence_length | set the minimum Length of a String </br> (for the <a href="#--strings---strings">--strings, --strings</a> Parameter) | 2 | 4 |
| strings_delimeter | set the Delimeter for Strings found on the same Line </br> (for the <a href="#--strings---strings">--strings, --strings</a> Parameter) | \| | \\n |
| editor_indentation | set the Indentation used in the Editor (<a href="#----edit">-!, --edit</a>)</br> when pressing ↹ on an empty Line | <b>␣ ␣ ␣ ␣</b> | ↹ |
| editor_auto_indent | set whether the Editor (<a href="#----edit">-!, --edit</a>) should auto indent or not | true | false |
| hex_editor_columns | set the amount of columns per row in the HexEditor (<a href="#----hexedit">-#, --hexedit</a>) | 8 | 16 |
| more_step_length | define the Step Length used by <a href="#-m---more">-M, --more</a></br>a Value of 0 is equivalent to the Size/Height of the Terminal Window | 5 | 0 |
| unicode_escaped_echo | unicode-escape the input when using <a href="#-e---echo">-E, --echo</a> | false | true |
| unicode_escaped_editor_search | unicode-escape the Search in the Editor (<a href="#----edit">-!, --edit</a>) | false | true |
| unicode_escaped_find | unicode-escape the queried Substring when using <a href="#findx-findx">find=X, find&#42889;X</a> | false | true |
| unicode_escaped_replace | unicode-escape a and b when using <a href="#ab">[a,b]</a> | false | true |

Accepted Input for enabling a Setting:  `true, yes, y, 1`
</br>
Accepted Input for disabling a Setting: `false, no, n, 0`
</br>
(Input is not case sensitive)

### <a id="--cconfig---cconfig">--cconfig, --cconfig</a>

Displays a user interactive config Menu allowing the User to change the Colors for specific Elements and Arguments.
Stops Code execution after finishing the Configuration.
The config File will be saved to the installation Directory of cat_win which is by Default the Python directory.
This means that uninstalling cat_win may result in the config File being left over.
When using the Windows Executables this Parameter will have no (long term) Effect.
Valid Options are:

| Option | Description |
|--------|-------------|
| line_length | the display of each line length using <a href="#-l---linelength">-l, --linelength</a> |
| line_numbers | the numbering of each line using <a href="#-n---number">-n, --number</a> |
| file_prefix | the file prefix using <a href="#--fp---file-prefix">--fp, --file-prefix</a> |
| line_ends | the end of line marker using <a href="#-e---ends">-e, --ends</a> |
| special_chars | special chars using <a href="#--chr---char">--chr, --char</a> |
| summary_message | the message displayed using <a href="#-f---files">-f, --files</a>/<a href="#-d---dirs">-d, --dirs</a>/<a href="#-s---sum">-s, --sum</a>/<a href="#-w---wordcount">-w, --wordcount</a>/<a href="#--cc---charcount">--cc, --charcount</a> |
| number_evaluation | the evaluated value using <a href="#--eval---eval">--eval, --EVAL</a> |
| number_conversion | the converted values using <a href="#--bin---bin">--bin</a>/<a href="#--oct---oct">--oct</a>/<a href="#--dec---dec">--dec</a>/<a href="#--hex---hex">--hex</a> |
| file_attribute_message | the message containing time stamps and file size using <a href="#-a---attributes">-a, --attributes</a> |
| active_file_attributes | the attributes a file has set using <a href="#-a---attributes">-a, --attributes</a> |
| missing_file_attributes | the attributes a file has not set using <a href="#-a---attributes">-a, --attributes</a> |
| checksum_message | the calculated checksum of a given file using <a href="#-m---checksum">-m, --checksum</a> |
| raw_viewer | the output using <a href="#--hexview---hexview">--hexview, --HEXVIEW</a>/<a href="#--binview---binview">--binview, --binview</a> |
| found_keyword | the found substring using <a href="#findx-findx">find=X, find&#42889;X</a> |
| found_keyword_message | the message displayed when using <a href="#findx-findx">find=X, find&#42889;X</a> |
| matched_pattern | the matched pattern using <a href="#matchx-matchx">match=X, match&#42889;X</a> |
| matched_pattern_message | the message displayed when using <a href="#matchx-matchx">match=X, match&#42889;X</a> |
| substring_replacement | the replaced string using <a href="#ab">[a,b]</a> |
| message_information | any informational message like update information |
| message_important | any important message like large file sizes |
| message_warning | any warning message like overwriting a file with itself |

### <a id="--config-clear---config-reset">--config-clear, --config-reset</a>

Reset the Configuration (of <a href="#--config---config">--config, --config</a>) to their Default Values.

```console
> catw --config-clear
Successfully updated config file:
   <Path>\cat.config
```

### <a id="--cconfig-clear---cconfig-reset">--cconfig-clear, --cconfig-reset</a>

Reset the Configuration (of <a href="#--cconfig---cconfig">--cconfig, --cconfig</a>) to their Default Values.

```console
> catw --config-clear
Successfully updated config file:
   <Path>\cat.config
```

### <a id="--config-remove---cconfig-remove">--config-remove, --cconfig-remove</a>

Delete the Config File.
This will reset both <a href="#--config---config">--config, --config</a> and <a href="#--cconfig---cconfig">--cconfig, --cconfig</a> Configurations to their Default Values.
The cat.config File will be erased from the System.

```console
> catw --config-remove
The config file has successfully been removed!
> catw --config-remove
No active config file has been found.
```

- - - -
<a id="encoding"></a>
### <a id="-r---rstream">-R, --R\<stream\></a>

Python uses Utf-8 to encode the Streams by default.
On Windows OS the Encoding may even be Cp1252.
The Encoding can be influenced externally by setting the environment Variable PYTHONIOENCODING to the desired Encoding,
or setting the environment Variable PYTHONUTF8 to 1.
In any case it is often useful to have the stream Encoding variable if a File for example is written in another Codepage like Utf-16.
Using this Parameter allows for specific Stream Reconfiguration meaning setting the Encoding for interpreting the Streams.
The Encoding used is defined by the <a href="#encx-encx">enc=X, enc&#42889;X</a> Argument.
By Default Stdout and Stderr are reconfigured.
Valid Streams are Stdout (--Rout), Stdin (--Rin) and Stderr (--Rerr).
When encountering UnicodeErrors the Problem is most likely being fixed by using -R (or --Rout).

```console
> catw ./CHANGELOG.md > test.txt
UnicodeEncodeError: 'charmap' codec can't encode character ...
```
```console
> catw ./CHANGELOG.md --Rout > test.txt
```

### <a id="encx-encx">enc=X, enc&#42889;X</a>

Sets the text Encoding that is being used to read and write Files.
Valid Options are defined by the Python Interpreter used (e.g. for [Python3.10](https://docs.python.org/3.8/library/codecs.html#standard-encodings)).
The default Encoding is Utf-8.
The default Encoding can be configured using the `default_file_encoding` element in the config menu (<a href="#--config---config">--config, --config</a>).

```console
> catw test.txt
Failed to open: <Path>\test.txt
Do you want to open the file as a binary, without parameters?
[Y/⏎] Yes, Continue       [N] No, Abort :
```
```console
> catw test.txt enc=utf-16
This Text is written in Utf-16!
```

### <a id="findx-findx">find=X, find&#42889;X</a>

Defines a Literal to search for within the Text of any provided File.
The Substring is unicode-escaped (\\n will be interpreted as an actual Newline) if the Config Option `unicode_escaped_find` is set but in Case of an unicode-error the Substring will simply be used literally.
When the Literal contains Whitespaces it is neccessary to encase the entire Parameter with Quotes as defined by the Terminal used.
It is possible to define multiple Substrings to search for by simply providing the Parameter find=X multiple times.
When using this Parameter in Uppercase the Case of the Substring will be ignored.

```console
> catw test.txt "find=cats and"
It's raining cats and dogs!
---------- Found:   ('cats and' 13-21) ----------

> catw test.txt "find=CATS and"
It's raining cats and dogs!
```

```console
> catw test.txt "FIND=CATS and"
It's raining cats and dogs!
---------- Found:   ('CATS and' 13-21) ----------
```

### <a id="matchx-matchx">match=X, match&#42889;X</a>

Defines a Pattern to search for within the Text of any provided File.
It is possible to define multiple Patterns to match for by simply providing the Parameter match=X multiple times.
The given Patterns is simply treated as a regular Expression.
When using this Parameter in Uppercase the Case of the Pattern will be ignored.

```console
> catw test.txt "match=cat.\s.{3,}"
It's raining cats and dogs!
---------- Matched: ('cat.\\s.{3,}' 13-27) ----------

> catw test.txt "match=CAT.\s.{3,}"
It's raining cats and dogs!
```

```console
> catw test.txt "MATCH=CAT.\s.{3,}"
It's raining cats and dogs!
---------- Matched: ('CAT.\\s.{3,}' 13-27) ----------
```

### <a id="truncxy-truncxy">trunc=X&#42889;Y, trunc&#42889;X&#42889;Y</a>

Truncates every File by the Specifics defined.
This Parameter uses the default Python slicing Mechanic and uses it on the Lines of each File.
The Argument is valid by defining trunc=\<start\>\:\<stop\> or trunc=\<start\>\:\<stop\>\:\<step\>

```console
> catw test.txt trunc=5:-5:2
 6) Line 6
 8) Line 8
10) there are 5 more Lines following this one
```

### <a id="ab">[a,b]</a>

Replaces the Substring defined by a with the Substring b in every Line of Every File.
The Substrings a and b are unicode-escaped (\\n will be interpreted as an actual Newline) if the Config Option `unicode_escaped_replace` is set but in Case of an unicode-error the Substrings will simply be used literally.
Comma (,) can be escaped using `\,` despite it not being a valid unicode-escape Sequence.
When one of the Substrings contains Whitespaces it is neccessary to encase the entire Parameter with Quotes as defined by the Terminal used.

```console
> catw test.txt "[\,,X]" "[\\,/]"
This is a comma: X
This is a Backslash: /
```

### <a id="abc">[a&#42889;b&#42889;c]</a>

Similiar to the <a href="#truncxy-truncxy">trunc=X&#42889;Y, trunc&#42889;X&#42889;Y</a> parameter this Argument is used on each Line individually.
Every Line is being cut down as specified by the Elements within the Argument [\<start\>\:\<stop\>\:\<step>].

```console
> catw test.txt [2::2]
2468acegikmoqsuwy
```
