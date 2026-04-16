"""
contentbuffer
"""


class ContentBuffer:
    """A synchronized content container for prefixes, lines, and suffixes."""

    __slots__ = ('lines', 'prefixes', 'suffixes')

    def __init__(self, lines=None, prefixes=None, suffixes=None) -> None:
        self.lines = list(lines or [])
        self.prefixes = list(prefixes or [])
        self.suffixes = list(suffixes or [])
        if not len(self.lines) == len(self.prefixes) == len(self.suffixes):
            raise ValueError('prefixes, lines and suffixes must have the same length!')

    @classmethod
    def from_lines(cls, lines, default_prefix='', default_suffix='') -> None:
        """
        Create a ContentBuffer from a sequence of lines.

        Parameters:
        lines (Iterable[str]):
            the lines to include in the buffer.
        default_prefix (str):
            the default prefix for each line.
        default_suffix (str):
            the default suffix for each line.

        Returns:
        (ContentBuffer):
            a new ContentBuffer containing the specified lines.
        """
        line_list = list(lines)
        return cls(
            line_list,
            [default_prefix] * len(line_list),
            [default_suffix] * len(line_list),
        )

    @classmethod
    def from_rows(cls, rows) -> None:
        """
        Create a ContentBuffer from a sequence of rows.

        Parameters:
        rows (Iterable[Tuple[str, ...]]):
            the rows to include in the buffer.

        Returns:
        (ContentBuffer):
            a new ContentBuffer containing the specified rows.
        """
        prefixes = []
        lines = []
        suffixes = []
        for row in rows:
            if isinstance(row, str):
                line = row
                prefix = suffix = ''
            elif len(row) == 1:
                line = row[0]
                prefix = suffix = ''
            elif len(row) == 2:
                line, prefix = row
                suffix = ''
            elif len(row) == 3:
                line, prefix, suffix = row
            else:
                raise ValueError('Rows must be (line, prefix) or (line, prefix, suffix)')
            prefixes.append(prefix)
            lines.append(line)
            suffixes.append(suffix)
        return cls(lines, prefixes, suffixes)

    @classmethod
    def ensure(cls, content):
        """
        Ensure that the given content is a ContentBuffer.

        Parameters:
        content (Union[ContentBuffer, Iterable[Tuple[str, ...]]]):
            the content to ensure is a ContentBuffer.

        Returns:
        (ContentBuffer):
            a ContentBuffer containing the specified content.
        """
        if isinstance(content, cls):
            return content
        return cls.from_rows(content)

    def __len__(self) -> int:
        return len(self.lines)

    def __bool__(self) -> bool:
        return bool(self.lines)

    def __iter__(self):
        return iter(zip(self.lines, self.prefixes, self.suffixes))

    def __getitem__(self, item):
        if isinstance(item, slice):
            return ContentBuffer(self.lines[item], self.prefixes[item], self.suffixes[item])
        return (self.lines[item], self.prefixes[item], self.suffixes[item])

    def __add__(self, other):
        other = ContentBuffer.ensure(other)
        return ContentBuffer(
            self.lines + other.lines,
            self.prefixes + other.prefixes,
            self.suffixes + other.suffixes,
        )

    def __eq__(self, value):
        if not isinstance(value, ContentBuffer):
            return False
        return (self.lines == value.lines and
                self.prefixes == value.prefixes and
                self.suffixes == value.suffixes)

    def append(self, line, prefix='', suffix='') -> None:
        """
        Append a line to the buffer.

        Parameters:
        line (str):
            the line to append.
        prefix (str):
            the prefix for the line.
        suffix (str):
            the suffix for the line.
        """
        self.lines.append(line)
        self.prefixes.append(prefix)
        self.suffixes.append(suffix)

    def reverse(self) -> None:
        """
        Reverse the order of lines in the buffer.
        """
        self.lines.reverse()
        self.prefixes.reverse()
        self.suffixes.reverse()

    def sort(self, key=None, reverse=False) -> None:
        """
        Sort the lines in the buffer.

        Parameters:
        key (Callable[[Tuple[str, str, str], Any]):
            a function to extract a comparison key from each line.
        reverse (bool):
            whether to sort in reverse order.
        """
        idx = list(range(len(self.lines)))
        if key is None:
            raise NotImplementedError('Sorting without a key is not supported.')
        idx.sort(key=lambda i: key(self[i]), reverse=reverse)
        self.lines = [self.lines[i] for i in idx]
        self.prefixes = [self.prefixes[i] for i in idx]
        self.suffixes = [self.suffixes[i] for i in idx]

    def filter(self, predicate):
        """
        filter the lines in the buffer by a predicate.

        Parameters:
        predicate (Callable[[Tuple[str, str, str], bool]):
            a function that takes a line and returns True if it should be included.
        """
        lines = []
        prefixes = []
        suffixes = []
        for line, prefix, suffix in self:
            if predicate(line, prefix, suffix):
                lines.append(line)
                prefixes.append(prefix)
                suffixes.append(suffix)
        self.lines = lines
        self.prefixes = prefixes
        self.suffixes = suffixes
        return self

    def map(self, mapper):
        """
        Apply mapper to each line and return a new ContentBuffer.
        mapper(line, prefix, suffix) -> new_line.

        Parameters:
        mapper (Callable[[Tuple[str, str, str], Tuple[str, str, str]]]):
            a function that takes a line and returns a new line.

        Returns:
        (ContentBuffer):
            a new ContentBuffer containing the mapped lines.
        """
        lines = []
        prefixes = []
        suffixes = []
        for line, prefix, suffix in self:
            new_line, new_prefix, new_suffix = mapper(line, prefix, suffix)
            lines.append(new_line)
            prefixes.append(new_prefix)
            suffixes.append(new_suffix)
        return ContentBuffer(lines, prefixes, suffixes)
