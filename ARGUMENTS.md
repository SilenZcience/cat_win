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
         <a href="#arguments">Arguments & Options</a>
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
                  <li><a href="#settings">Settings</a></li>
                  <li><a href="#encoding">Text Encoding</a></li>
               </ul>
            </li>
            <li>
               <a href="#general-information">General Information</a>
               <ul>
                  <li><a href="#help">-h, --help</a></li>
                  <li><a href="#version">-v, --version</a></li>
                  <li><a href="#debug">--debug, --debug</a></li>
                  <li><a href="#number">-n, --number</a></li>
                  <li><a href="#length">-l, --linelength</a></li>
                  <li><a href="#fileprefix">--fp, --file-prefix</a></li>
                  <li><a href="#ends">-e, --ends</a></li>
                  <li><a href="#chr">--chr, --char</a></li>
                  <li><a href="#blank">-b, --blank</a></li>
                  <li><a href="#peek">-p, --peek</a></li>
                  <li><a href="#reverse">-r, --reverse</a></li>
                  <li><a href="#unique">-u, --unique</a></li>
                  <li><a href="#sort">--sort, --sort</a></li>
                  <li><a href="#echo">-E, --echo</a></li>
                  <li><a href="#interactive">-i, --interactive</a></li>
                  <li><a href="#oneline">-o, --oneline</a></li>
                  <li><a href="#url">-U, --url</a></li>
                  <li><a href="#files">-f, --files</a></li>
                  <li><a href="#sum">-s, --sum</a></li>
                  <li><a href="#wordcount">-w, --wordcount</a></li>
                  <li><a href="#grep">-g, --grep</a></li>
                  <li><a href="#nokeyword">--nk, --nokeyword</a></li>
                  <li><a href="#nobreak">--nb, --nobreak</a></li>
                  <li><a href="#attributes">-a, --attributes</a></li>
                  <li><a href="#checksum">-m, --checksum</a></li>
                  <li><a href="#b64d">--b64d, --b64d</a></li>
                  <li><a href="#b64e">--b64e, --b64e</a></li>
                  <li><a href="#eval">--eval, --EVAL</a></li>
                  <li><a href="#hex">--hex, --HEX</a></li>
                  <li><a href="#dec">--dec, --DEC</a></li>
                  <li><a href="#oct">--oct, --OCT</a></li>
                  <li><a href="#bin">--bin, --BIN</a></li>
                  <li><a href="#binview">--binview, --binview</a></li>
                  <li><a href="#hexview">--hexview, --HEXVIEW</a></li>
                  <li><a href="#plain">--plain, --plain-only</a></li>
                  <li><a href="#dot">--dot, --dotfiles</a></li>
                  <li><a href="#nocolor">--nc, --nocolor</a></li>
                  <li><a href="#editor">-!, --edit</a></li>
                  <li><a href="#clip">-c, --clip</a></li>
                  <li><a href="#config">--config, --config</a></li>
                  <li><a href="#stream">-R, --R&ltstream&gt</a></li>
                  <li><a href="#enc">enc=X, enc&#42889;X</a></li>
                  <li><a href="#find">find=X, find&#42889;X</a></li>
                  <li><a href="#match">match=X, match&#42889;X</a></li>
                  <li><a href="#trunc">trunc=X&#42889;Y, trunc&#42889;X&#42889;Y</a></li>
                  <li><a href="#replace">[a,b]</a></li>
                  <li><a href="#cut">[a&#42889;b&#42889;c]</a></li>
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

# Arguments & Options <a id="arguments"></a>

| Argument / Option | Description | works in shell |
|-------------------|-------------|:--------------:|
| *<a href="#help">-h, --help</a>* | show help message and exit |✔|
| *<a href="#version">-v, --version</a>* | output version information and exit |✔|
| *<a href="#debug">--debug, --debug</a>* | show debug information |✔|
||| |
| *<a href="#length">-l, --linelength</a>* | display the length of each line |✔|
| *<a href="#number">-n, --number</a>* | number all output lines |✔|
| *<a href="#fileprefix">--fp, --file-prefix</a>* | include the file in every line prefix |❌|
||| |
| *<a href="#ends">-e, --ends</a>* | display $ at the end of each line |✔|
| *<a href="#chr">--chr, --char</a>* | display special characters |✔|
||| |
| *<a href="#blank">-b, --blank</a>* | hide empty lines |✔|
| *<a href="#peek">-p, --peek</a>* | only print the first and last lines |❌|
| *<a href="#reverse">-r, --reverse</a>* | reverse output |❌|
| *<a href="#unique">-u, --unique</a>* | suppress repeated output lines |❌|
| *<a href="#sort">--sort, --sort</a>* | sort all lines alphabetically |❌|
||| |
| *<a href="#echo">-E, --echo</a>* | handle every following parameter as stdin |❌|
| *<a href="#interactive">-i, --interactive</a>* | use stdin |❌|
| *<a href="#oneline">-o, --oneline</a>* | take only the first stdin-line |✔|
| *<a href="#url">-U, --url</a>* | display the contents of any provided url |❌|
||| |
| *<a href="#files">-f, --files</a>* | list applied files and file sizes |❌|
| *<a href="#sum">-s, --sum</a>* | show sum of lines |❌|
| *<a href="#wordcount">-w, --wordcount</a>* | display the wordcount |❌|
||| |
| *<a href="#grep">-g, --grep</a>* | only show lines containing queried keywords or patterns |✔|
| *<a href="#nokeyword">--nk, --nokeyword</a>* | inverse the grep output |✔|
| *<a href="#nobreak">--nb, --nobreak</a>* | do not interrupt the output |✔|
||| |
| *<a href="#attributes">-a, --attributes</a>* | show meta-information about the files |❌|
| *<a href="#checksum">-m, --checksum</a>* | show the checksums of all files |❌|
||| |
| *<a href="#b64d">--b64d, --b64d</a>* | decode the input from base64 |✔|
| *<a href="#b64e">--b64e, --b64e</a>* | encode the input to base64 |✔|
| *<a href="#eval">--eval, --EVAL</a>* | evaluate simple mathematical equations |✔|
| *<a href="#hex">--hex, --HEX</a>* | convert hexadecimal numbers to binary, octal and decimal |✔|
| *<a href="#dec">--dec, --DEC</a>* | convert decimal numbers to binary, octal and hexadecimal |✔|
| *<a href="#oct">--oct, --oct</a>* | convert octal numbers to binary, decimal and hexadecimal |✔|
| *<a href="#bin">--bin, --BIN</a>* | convert binary numbers to octal, decimal and hexadecimal |✔|
||| |
| *<a href="#binview">--binview, --binview</a>* | display the raw byte representation in binary |❌|
| *<a href="#hexview">--hexview, --HEXVIEW</a>* | display the raw byte representation in hexadecimal |❌|
||| |
| *<a href="#editor">-!, --edit</a>* | open each file in a simple editor |❌|
| *<a href="#clip">-c, --clip</a>* | copy output to clipboard |✔|
| *<a href="#dot">--dot, --dotfiles</a>* | additionally query and edit dotfiles |❌|
| *<a href="#plain">--plain, --plain-only</a>* | ignore non-plaintext files automatically |❌|
| *<a href="#nocolor">--nc, --nocolor</a>* | disable colored output |✔|
||| |
| *<a href="#config">--config, --config</a>* | change color configuration |✔|
||| |
| *<a href="#stream">-R, --R\<stream\></a>* | reconfigure the std-stream(s) with the parsed encoding </br> \<stream\> = 'in'/'out'/'err' (default is stdin & stdout) | ✔ |
||| |
| *<a href="#enc">enc=X, enc&#42889;X</a>* | set file enconding to X (default is utf-8) |✔|
| *<a href="#find">find=X, find&#42889;X</a>* | find/query a substring X in the given files |✔|
| *<a href="#match">match=X, match&#42889;X</a>* | find/query a pattern X in the given files |✔|
| *<a href="#trunc">trunc=X&#42889;Y, trunc&#42889;X&#42889;Y</a>* | truncate file to lines X and Y (python-like) |❌|
||| |
| *<a href="#replace">[a,b]</a>* | replace a with b in every line (escape chars with '\\') |✔|
| *<a href="#cut">[a&#42889;b&#42889;c]</a>* | python-like string indexing syntax (line by line) |✔|


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
   - When using the --interactive Parameter unknown Files will be automatically written with the content of Stdin.

### <a id="help">-h, --help</a>

Displays the help Message.
This Message is for the most part equivalent to the Table above.
The Code execution will stop after showing this Message.
This Argument has Priority over all other Arguments, hence the Order of passing this Argument in makes no Difference.
If no Arguments or Files are provided, the help Parameter will be used by Default.

### <a id="version">-v, --version</a>

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

### <a id="debug">--debug, --debug</a>

Displays debug Information before and after the Code execution.
This Argument is not shown in the default help Message and is provided for Developers/Development.

<a id="prefix"></a>
### <a id="number">-n, --number</a>

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

### <a id="length">-l, --linelength</a>

Displays the Length of each Line as a Prefix to the Line itself.
This Argument will be used at the end such that other Arguments may influence the Length of the Lines beforehand.

```console
> catw test.txt -l
[ 6] line 1
[10] long_line!
```

### <a id="fileprefix">--fp, --file-prefix</a>

Shows the Path to the File in each Line prefix.
This can be useful when querying for Substrings or Patterns such that only a few Lines are being displayed.
Using this Argument in uppercase (--FP, --FILEPREFIX) will result in the Path being shown as the url file Protocol.
This can be useful in case the Terminal supports interacting with Links such that the File can be instantly opened.
Using the lowercase Argument in Combination with the <a href="#number">-n, --number</a> Parameter a GNU-style link format will be displayed.

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

<a id="simplereplace"></a>
### <a id="ends">-e, --ends</a>

Displays a '$' Character at the End of each Line.
This can be useful to detect Whitespaces.

```console
> catw test.txt --ends
Tab:    $
line 2$
```

### <a id="chr">--chr, --char</a>

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

<a id="linemanipulation"></a>
### <a id="blank">-b, --blank</a>

Removes empty Lines from the Output.
Beware that other Arguments can change a Line to be not empty beforehand.

```console
> catw test.txt -nb
1) Empy Line follows:
3) Empty Line just got skipped!
```

### <a id="peek">-p, --peek</a>

Only displays the first and last 5 Lines of each File.
Between the Beginning and End of the File will be displayed how many Lines have been skipped.
Useful for getting a quick impression of how data in a given File is structured.
This Argument is not being used when provided alongside with Queries for Substrings of Patterns.
Does nothing when the File has at most 10 Lines.

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

### <a id="reverse">-r, --reverse</a>

Simply reverses the Content of all Files as well as the Ordering of all Files themselves.

```console
> catw test1.txt test2.txt -p
Line 2 From Test2
Line 1 From Test2
Line 2 From Test1
Line 1 From Test1
```

### <a id="unique">-u, --unique</a>

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

### <a id="sort">--sort, --sort</a>

Sorts the Output alphabetically without case sensitivity.

```console
> catw test.txt --sort -n
2) A line that has been sorted to the top!
1) This line was originally at the top!
```

<a id="input"></a>
### <a id="echo">-E, --echo</a>

Everything passed in after this Argument will be handled as its own File.
It is not possible to break out of this state therefor this Parameter must be used last.
When using the one-letter Variant of this Parameter the following Input will be decoded with unicode Escape Sequences instead of parsing a raw String.
This way it is possible to define new lines (\n) or other special characters.

```console
> catw -l -E -n The last 'Parameter' does not count!
[37] -n The last Parameter does not count!
```

### <a id="interactive">-i, --interactive</a>

Using this Argument allows to pass in Data via the Stdin Stream.
The Stdin Pipe will be handled as its own File.

```console
> echo Hello World! | catw -in
1) Hello World!
```

### <a id="oneline">-o, --oneline</a>

Limits the Stdin Stream to the first Line.
Can only be used in Combination with <a href="#interactive">-i, --interactive</a>.

```console
> catw test.txt
Line 1
Line 2
Line 3
```
```console
> catw test.txt | catw -io
Line 1
```

### <a id="url">-U, --url</a>

When using this Parameter it is possible to provide URLs as Arguments.
Should an URL not have a scheme (http(s):// or fttp(s):// ...) the default scheme (https://) is being used.
Provided URLs are simply curl'd and handled as its own File.
When not providing a raw Data URL the Content will include the HTML Elements.

```console
> catw -U https://github.com/SilenZcience/cat_win > cat.html
```

<a id="summary"></a>
### <a id="files">-f, --files</a>

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

### <a id="sum">-s, --sum</a>

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

### <a id="wordcount">-w, --wordcount</a>

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

<a id="search"></a>
### <a id="grep">-g, --grep</a>

Skips every Line that does not contain any matched Patterns or queried Substrings.
Literals or Patterns to look for can be set using the <a href="#find">find=X, find&#42889;X</a> and <a href="#match">match=X, match&#42889;X</a> Keywords.
Using this Argument in uppercase (-G, --GREP) will ONLY display the parts of each Line that matched any Pattern or Literal.
Should multiple Queries be found in the same Line they will be seperated by comma.
The uppercase Variant of this Parameter has priority (over the lowercase Variant as well as <a href="#nokeyword">--nk, --nokeyword</a>).

```console
> catw test.txt find=cat -gn
1) cat_win!
4) one cat!& two cat!& three cat
```
```console
> catw test.txt match=.cat. -Gn
4)  cat!, cat!
```

### <a id="nokeyword">--nk, --nokeyword</a>

Inverse to the <a href="#grep">-g, --grep</a> Argument.
Skips every Line that does contain any matched Patterns or queried Substrings.
The Combination of --nokeyword and <a href="#grep">-g, --grep</a> means that no Output will be displayed.

```console
> catw test.txt find=cat -n --nk
2) This Line is boring
3) This Line also does not contain 'c a t'
5) This Line neither
```

### <a id="nobreak">--nb, --nobreak</a>

Using this Argument will open non-plaintext Files automatically without prompting the User.
In Addition the Output will not stop on queried Substrings or Patterns.
This Behaviour is included by Default when using <a href="#nokeyword">--nk, --nokeyword</a> or <a href="#grep">-g, --grep</a>.

<a id="meta"></a>
### <a id="attributes">-a, --attributes</a>

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

### <a id="checksum">-m, --checksum</a>

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

<a id="mathematical"></a>
### <a id="b64d">--b64d, --b64d</a>

Decodes a Base64 encoded Input and continues Code execution with the decoded Text.
This Parameter will be used before most other Arguments such that other Parameters will be used on the decoded Text.
This means a Base64 encoded Input is expected and neccessary.

```console
> echo SGVsbG8gV29ybGQ= | catw -i --b64d
Hello World
```

### <a id="b64e">--b64e, --b64e</a>

Encodes a given Text in Base64.
This Parameter will be used after most other Arguments such that other Parameter will be used on the plain Text beforehand.

```console
> echo Hello World | catw -i --b64e
SGVsbG8gV29ybGQ=
```

### <a id="eval">--eval, --EVAL</a>

Evaluates simple mathematical Expressions within any given Text.
The mathematical Expressions may consist of paranthesis, Operators including Modulo (%) and Exponential (**),
as well as any Number in Hexadecimal, Decimal, Octal or Binary.
The evaluated Value of the Expression will by default be inserted back into the Position of the Text where the Expression was found.
In the uppercase Variant of the Parameter any non-mathematical Text will be stripped thus only evaluated Expressions will remain.
On Error The Expression will evaluate to '???'.

```console
> echo Calculate: (5 * 0x10 * -0b101) % (0o5 ** 2) ! | catw -i --eval
Calculate: 0 !
```
```console
> echo Calculate: (5 * 0x10 * -0b101) % (0o5 ** 2) ! | catw -i --EVAL
0
```

### <a id="hex">--hex, --HEX</a>

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

### <a id="dec">--dec, --DEC</a>

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

### <a id="oct">--oct, --OCT</a>

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

### <a id="bin">--bin, --BIN</a>

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

<a id="byteview"></a>
### <a id="binview">--binview, --binview</a>

Displays a BinaryViewer for each File passed in.
Special Characters like NewLine or BackSpace will be displayed as specific readable Chars if the Font and the Encoding do support that Behaviour.

```console
> catw test.txt --hexview
<Path>\test.txt:
Address  00       01       02       03       04       05       06       07       08       ... # Decoded Text
00000000 01000011 01100001 01110100 01011111 01010111 01101001 01101110 00100001 00001010 ... # C a t _ W i n ! ␤
```

### <a id="hexview">--hexview, --HEXVIEW</a>

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

<a id="settings"></a>
### <a id="plain">--plain, --plain-only</a>

By default the User is being prompted when a non-plaintext File is being encountered as to if the File should be opened in Binary or not.
Using --plain-only these Files will be automaticaly skipped.
Note that these Prompts are not descriptive enough to say that a File can only be opened in Binary.
Often the Problem is being fixed by providing another Codepage using the <a href="#enc">enc=X, enc&#42889;X</a> Parameter.

### <a id="dot">--dot, --dotfiles</a>

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

### <a id="nocolor">--nc, --nocolor</a>

By default different Colors will be used to better highlight specific Parts of the Output or make original and changed Parts of a Line more distinguishable.
Using --nocolor will disable all Colors and only display the Output in plain monochrome Text.

### <a id="editor">-!, --edit</a>

Opens a simple Editor to write/edit the Content of any provided File one by one.
Not-existing Files will be opened first and existing Ones will be able to be edited after that.
The Editor can be closed using the Hotkey ^q (Ctrl-q).
The Editor will not save changes automatically.
To Save the Edits use the Hotkey ^s (Ctrl-s).
Files will be saved with the text Encoding defined by <a href="#enc">enc=X, enc&#42889;X</a>.

### <a id="clip">-c, --clip</a>

Copies the entire Output to the Clipboard additionally to printing it to the Stdout Stream.

### <a id="config">--config, --config</a>

Displays a user interactive config Menu allowing the User to change the Colors for specific Elements and Arguments.
Stops Code execution after finishing the Configuration.
The config File will be saved to the installation Directory of cat_win which is by Default the Python directory.
This means that uninstalling cat_win may result in the config File being left over.
When using the Windows Executables this Parameter will have no (long term) Effect.

<a id="encoding"></a>
### <a id="stream">-R, --R\<stream\></a>

Python uses Utf-8 to encode the Streams by default.
On Windows OS the Encoding may even be Cp1252.
The Encoding can be influenced externally by setting the environment Variable PYTHONIOENCODING to the desired Encoding,
or setting the environment Variable PYTHONUTF8 to 1.
In any case it is often useful to have the stream Encoding variable if a File for example is written in another Codepage like Utf-16.
Using this Parameter allows for specific Stream Reconfiguration meaning setting the Encoding for interpreting the Streams.
The Encoding used is defined by the <a href="#enc">enc=X, enc&#42889;X</a> Argument.
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


### <a id="enc">enc=X, enc&#42889;X</a>

Sets the text Encoding that is being used to read and write Files.
Valid Options are defined by the Python Interpreter used (e.g. for [Python3.10](https://docs.python.org/3.8/library/codecs.html#standard-encodings)).
The default Encoding is Utf-8.

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

### <a id="find">find=X, find&#42889;X</a>

Defines a Literal to search for within the Text of any provided File.
When the Literal contains Whitespaces it is neccessary to encase the entire Parameter with Quotes as defined by the Terminal used.
It is possible to define multiple Substrings to search for by simply providing the Parameter find=X multiple times.

```console
> catw test.txt "find=cats and"
It's raining cats and dogs!
--------------- Found [('cats and', [13, 21])] ---------------
```

### <a id="match">match=X, match&#42889;X</a>

Defines a Pattern to search for within the Text of any provided File.
It is possible to define multiple Patterns to match for by simply providing the Parameter match=X multiple times.
The given Patterns is simply treated as a regular Expression.

```console
> catw test.txt "match=cat.\s.{3,}"
It's raining cats and dogs!
--------------- Matched [('cat.\\s.{3,}', [13, 27])] ---------------
```

### <a id="trunc">trunc=X&#42889;Y, trunc&#42889;X&#42889;Y</a>

Truncates every File by the Specifics defined.
This Parameter uses the default Python slicing Mechanic and uses it on the Lines of each File.
The Argument is valid by defining trunc=\<start\>\:\<stop\> or trunc=\<start\>\:\<stop\>\:\<step\>

```console
> catw test.txt trunc=5:-5:2
 6) Line 6
 8) Line 8
10) there are 5 more Lines following this one
```

### <a id="replace">[a,b]</a>

Replaces the Substring defined by a with the Substring b in every Line of Every File.
Characters within one of the two Substrings can be escaped using a Backslash.
For example this way it is possible to replace a comma which is also used as the delimeter of both Strings.
When one of the Substrings contains Whitespaces it is neccessary to encase the entire Parameter with Quotes as defined by the Terminal used.
It is possible to define multiple replace Arguments.

```console
> catw test.txt "[\,,X]" "[\\,/]"
This is a comma: X
This is a Backslash: /
```

### <a id="cut">[a&#42889;b&#42889;c]</a>

Similiar to the trunc=X\:Y parameter this Argument is used on each Line individually.
Every Line is being cut down as specified by the Elements within the Argument [\<start\>\:\<stop\>\:\<step>].

```console
> catw test.txt [2::2]
2468acegikmoqsuwy
```
