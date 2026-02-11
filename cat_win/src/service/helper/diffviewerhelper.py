"""
diffviewerhelper
"""

import difflib
import unicodedata
from functools import lru_cache
from typing import Sequence


@lru_cache(maxsize=256)
def is_special_character(char: str) -> bool:
    """
    Check if character is problematic (wide, emoji, control, combining)
    https://www.unicode.org/reports/tr44/#General_Category_Values
    """
    category = unicodedata.category(char)
    # Replace if it's:
    # - Wide character (W or F) - these don't display correctly in curses
    # # - Emoji or symbol that's not basic punctuation
    # - Control character (except allowed whitespace)
    # - Combining mark
    return (
        unicodedata.east_asian_width(char) in 'WF' or  # Wide characters
        # category in ['So', 'Sk'] or  # Other symbols, modifier symbols (emojis)
        category[0] in 'CM' # Control characters (C) or Combining marks (M)
    )


class CustomDiffer(difflib.Differ):
    """
    Custom Differ that only modifies the best_ratio and cutoff values in _fancy_replace
    """

    def __init__(self, linejunk=None, charjunk=None, best_ratio=0.6, cutoff=0.75):
        super().__init__(linejunk, charjunk)
        self.best_ratio = best_ratio
        self.cutoff = cutoff

    def _fancy_replace(self, a, alo, ahi, b, blo, bhi):
        r"""
        When replacing one block of lines with another, search the blocks
        for *similar* lines; the best-matching pair (if any) is used as a
        synch point, and intraline difference marking is done on the
        similar pair. Lots of work, but often worth it.

        Example:

        >>> d = Differ()
        >>> results = d._fancy_replace(['abcDefghiJkl\n'], 0, 1,
        ...                            ['abcdefGhijkl\n'], 0, 1)
        >>> print(''.join(results), end="")
        - abcDefghiJkl
        ?    ^  ^  ^
        + abcdefGhijkl
        ?    ^  ^  ^
        """

        # don't synch up unless the lines have a similarity score of at
        # least cutoff; best_ratio tracks the best score seen so far
        best_ratio, cutoff = self.best_ratio, self.cutoff
        cruncher = difflib.SequenceMatcher(self.charjunk)
        eqi, eqj = None, None   # 1st indices of equal lines (if any)
        best_i, best_j = None, None  # Initialize to avoid None errors

        # search for the pair that matches best without being identical
        # (identical lines must be junk lines, & we don't want to synch up
        # on junk -- unless we have to)
        for j in range(blo, bhi):
            bj = b[j]
            cruncher.set_seq2(bj)
            for i in range(alo, ahi):
                ai = a[i]
                if ai == bj:
                    if eqi is None:
                        eqi, eqj = i, j
                    continue
                cruncher.set_seq1(ai)
                # computing similarity is expensive, so use the quick
                # upper bounds first -- have seen this speed up messy
                # compares by a factor of 3.
                # note that ratio() is only expensive to compute the first
                # time it's called on a sequence pair; the expensive part
                # of the computation is cached by cruncher
                if cruncher.real_quick_ratio() > best_ratio and \
                      cruncher.quick_ratio() > best_ratio and \
                      cruncher.ratio() > best_ratio:
                    best_ratio, best_i, best_j = cruncher.ratio(), i, j
        if best_ratio < cutoff:
            # no non-identical "pretty close" pair
            if eqi is None:
                # no identical pair either -- treat it as a straight replace
                yield from self._plain_replace(a, alo, ahi, b, blo, bhi)
                return
            # no close pair, but an identical pair -- synch up on that
            best_i, best_j, best_ratio = eqi, eqj, 1.0
        else:
            # there's a close pair, so forget the identical pair (if any)
            eqi = None

        # Safety check: if best_i or best_j is still None, fall back to plain replace
        if best_i is None or best_j is None:
            yield from self._plain_replace(a, alo, ahi, b, blo, bhi)
            return

        # a[best_i] very similar to b[best_j]; eqi is None iff they're not
        # identical

        # pump out diffs from before the synch point
        yield from self._fancy_helper(a, alo, best_i, b, blo, best_j)

        # do intraline marking on the synch pair
        aelt, belt = a[best_i], b[best_j]
        if eqi is None:
            # pump out a '-', '?', '+', '?' quad for the synched lines
            atags = btags = ""
            cruncher.set_seqs(aelt, belt)
            for tag, ai1, ai2, bj1, bj2 in cruncher.get_opcodes():
                la, lb = ai2 - ai1, bj2 - bj1
                if tag == 'replace':
                    atags += '^' * la
                    btags += '^' * lb
                elif tag == 'delete':
                    atags += '-' * la
                elif tag == 'insert':
                    btags += '+' * lb
                elif tag == 'equal':
                    atags += ' ' * la
                    btags += ' ' * lb
                else:
                    raise ValueError('unknown tag %r' % (tag,))
            yield from self._qformat(aelt, belt, atags, btags)
        else:
            # the synch pair is identical
            yield '  ' + aelt

        # pump out diffs from after the synch point
        yield from self._fancy_helper(a, best_i+1, ahi, b, best_j+1, bhi)


class DifflibID:
    EQUAL     = 0 # starts with '  '
    INSERT    = 1 # starts with '+ '
    DELETE    = 2 # starts with '- '
    CHANGED   = 3 # either three or four lines with the prefixes ('-', '+', '?'), ('-', '?', '+') or ('-', '?', '+', '?') respectively

class Difflib_Item:
    def __init__(self, line1: str, line2: str,
                 code: int = DifflibID.EQUAL,
                 lineno: str = '',
                 changes1: list = None,
                 changes2: list = None):
        self.line1 = line1
        self.line2 = line2
        self.code = code
        self.lineno = lineno
        self.changes1 = changes1
        self.changes2 = changes2

class DifflibParser:
    """
    DifflibParser
    """

    def __init__(self, text1: Sequence, text2: Sequence,
                 best_ratio: float = 0.74, cutoff: float = 0.75,
                 linejunk=None, charjunk=None):
        self._ndiff = list(
            CustomDiffer(
                linejunk, charjunk, best_ratio, cutoff
            ).compare(
                text1,
                text2
            )
        )

        self._diff = []
        self._c_lineno = 0

        self.count_equal = 0
        self.count_insert = 0
        self.count_delete = 0
        self.count_changed = 0

        self.last_lineno = 0

        self.parse()

    def get_diff(self):
        return self._diff

    def parse(self):
        while self._c_lineno < len(self._ndiff):
            self.advance()
        self.count_equal = len(self._diff) - self.count_insert - self.count_delete - self.count_changed
        self.last_lineno = len(self._diff) - self.count_insert
        l_offset = len(str(self.last_lineno))
        lineno = 1
        for item in self._diff:
            if item.code != DifflibID.INSERT:
                item.lineno = str(lineno)
                lineno += 1
            item.lineno = item.lineno.rjust(l_offset)

    def advance(self):
        c_line = self._ndiff[self._c_lineno]

        c_line_no_tab = ''.join('�' if is_special_character(c) else c for c in c_line[2:].replace('\t', ' '))
        cmp_line = Difflib_Item(
            c_line_no_tab,
            c_line_no_tab
        )

        code = c_line[:2]
        if code == '+ ':
            cmp_line.code = DifflibID.INSERT
            cmp_line.line1 = ''
            self.count_insert += 1
        if code == '- ':
            skip_lines = self._tryGetChangedLine(cmp_line)
            if not skip_lines:
                cmp_line.code = DifflibID.DELETE
                cmp_line.line2 = ''
                self.count_delete += 1
            else:
                cmp_line.code = DifflibID.CHANGED
                self._c_lineno += skip_lines
                self.count_changed += 1

        self._c_lineno += 1
        self._diff.append(cmp_line)

    def _tryGetChangedLine(self, cmp_line: Difflib_Item) -> int:
        line_window = self._ndiff[self._c_lineno:self._c_lineno + 4]
        line_window_prefixes = [line[:2] for line in line_window]

        # case ('-', '?', '+', '?')
        if line_window_prefixes == ['- ', '? ', '+ ', '? ']:
            cmp_line.line2    = ''.join('�' if is_special_character(c) else c for c in line_window[2][2:].replace('\t', ' '))
            cmp_line.changes1 = [i for (i,c) in enumerate(line_window[1][2:]) if c in '-^']
            cmp_line.changes2 = [i for (i,c) in enumerate(line_window[3][2:]) if c in '+^']
            return 3
        # case ('-', '+', '?')
        if line_window_prefixes[:3] == ['- ', '+ ', '? ']:
            cmp_line.line2    = ''.join('�' if is_special_character(c) else c for c in line_window[1][2:].replace('\t', ' '))
            cmp_line.changes1 = []
            cmp_line.changes2 = [i for (i,c) in enumerate(line_window[2][2:]) if c in '+^']
            return 2
        # case ('-', '?', '+')
        if line_window_prefixes[:3] == ['- ', '? ', '+ ']:
            cmp_line.line2    = ''.join('�' if is_special_character(c) else c for c in line_window[2][2:].replace('\t', ' '))
            cmp_line.changes1 = [i for (i,c) in enumerate(line_window[1][2:]) if c in '-^']
            cmp_line.changes2 = []
            return 2
        # No special case matched
        return 0
