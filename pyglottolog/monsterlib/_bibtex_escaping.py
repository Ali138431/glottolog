# coding: utf-8
"""
Unfortunately out bibtex source files are not encoded consistently across files. I.e.
latex commands with the same name may be used with different definitions in different
files.

So far identified problems:
- \:n is used in sala.bib for N WITH DOT ABOVE, but is also defined in the textipa
  package, commands of which have been used in various other source files.


See also:
- textipa package reference
  http://www.ling.ohio-state.edu/~mbeckman/ling600.01/tipachart.pdf
- comprehensive latex symbol list
  http://www.math.boun.edu.tr/instructors/gurel/symbols-a4.pdf

see also:
  _bibtex_undiacritic.py rules
  http://github.com/clld/clld/blob/master/clld/lib/bibtex.py
  http://github.com/clld/clld/blob/master/clld/lib/latex.py
  http://github.com/mcmtroffaes/latexcodec/blob/develop/latexcodec/codec.py#L97

"""

import re
import codecs
import unicodedata

from six import text_type, unichr
import latexcodec

__all__ = [
    'u_escape', 'u_unescape', 'latex_to_utf8', 'ulatex_postprocess', 'ulatex_preprocess']

LATEX_TABLE = {
    u'COMBINING DOT BELOW': br'\textsubdot',
    u'COMBINING MACRON': [br'\=', br'\textbar'],
    u'COMBINING MACRON BELOW': [br'\textsubbar', br'\textsubline'],
    u'COMBINING COMMA BELOW': [br'\,', br'\cb'],
    u'COMBINING TILDE BELOW': br'\textsubtilde',
    u'COMBINING CARON': br'\v',
    u'COMBINING CARON BELOW': br'\textsubwedge',
    u'COMBINING CIRCUMFLEX ACCENT': br'\^',
    u'COMBINING ACUTE ACCENT': br"\'",
    u'COMBINING GRAVE ACCENT': br"\`",
    u'COMBINING DIAERESIS': br'\"',
    u'COMBINING LATIN SMALL LETTER C': br'\textsuperscript{c}',
    u'COMBINING RING BELOW': br'\textsubring',
    u'COMBINING OGONEK': br'\textpolhook',
    u'COMBINING TILDE': br'\~',
    u'COMBINING DOUBLE GRAVE ACCENT': br'\textdoublegrave',
    u'COMBINING BREVE BELOW': br'\textsubu',
    u'COMBINING BRIDGE BELOW': br'\textsubbridge',

    # FIXME: may clash with commands from the textipa package!!
    u'COMBINING HORN': br'\;',
    u'COMBINING DOT ABOVE': [br'\.', br'\textdot', br'\:'],
    # FIXME: that's what textipa provides: but not how it is used in sala.bib!
    #u'LATIN SMALL LETTER N WITH RETROFLEX HOOK': [br'\:{n}', br'\:n'],

    u'MASCULINE ORDINAL INDICATOR': br'\textordmasculine',
    u'LEFT SINGLE QUOTATION MARK': [br'\textquoteleft', br'\grq'],
    u'SINGLE LOW-9 QUOTATION MARK': br'\glq',
    u'RIGHT SINGLE QUOTATION MARK': br'\textquoteright',
    u'NOT SIGN': br'\textlnot',
    u'VULGAR FRACTION THREE QUARTERS': br'\textthreequarters',
    u'LATIN SMALL LETTER A WITH RING ABOVE': br'\r{a}',
    u'LATIN CAPITAL LETTER A WITH RING ABOVE': br'\r{A}',
    u'MODIFIER LETTER SMALL W': br'\textsuperscript{w}',
    u'SUPERSCRIPT ONE': br'\textsuperscript{1}',
    u'SUPERSCRIPT TWO': br'\textsuperscript{2}',
    u'SUPERSCRIPT THREE': br'\textsuperscript{3}',
    u'SUPERSCRIPT FOUR': br'\textsuperscript{4}',
    u'SUPERSCRIPT LATIN SMALL LETTER N': br'\textsuperscript{n}',
    u'PERCENT SIGN': br'\%',
    u'LATIN SMALL LETTER D WITH HOOK': [br'\texthtd', br'\texthooktopd', br'\textrhooktopd', '\!d'],
    u'LATIN SMALL LETTER D WITH TAIL': br'\:{d}',
    u'LATIN SMALL LETTER B WITH HOOK': [br'\texthtb', br'\texthooktopb'],
    u'LATIN SMALL LETTER N WITH LEFT HOOK': br'\textltailn',
    u'LATIN SMALL LETTER S WITH HOOK': br'\textrtails',
    u'LATIN SMALL LETTER ETH': [br'\dh', br'\textdh'],
    u'LATIN CAPITAL LETTER ETH': br'\DH',
    u'LATIN SMALL LETTER ENG': [br'\ng', br'\textipa{N}'],
    u'LATIN CAPITAL LETTER ENG': br'\NG',
    u'LATIN SMALL LETTER OPEN O': br'\textopeno',
    u'LATIN CAPITAL LETTER THORN': br'\TH',
    u'LATIN SMALL LETTER THORN': [br'\textthorn', br'\th'],
    u'LATIN LETTER GLOTTAL STOP': br'\textglotstop',
    u'LATIN LETTER INVERTED GLOTTAL STOP': br'\textrevglotstop',
    u'LATIN SMALL LETTER SCHWA': br'\textschwa',
    u'LATIN SMALL LETTER R WITH TAIL': br'\textrtailr',
    u'LATIN SMALL LETTER BARRED O': br'\texttheta',
    u'LATIN SMALL LETTER O WITH HORN': br'\ohorn',
    u'MODIFIER LETTER GLOTTAL STOP': br'\textraiseglotstop',
    u'LATIN SMALL LETTER I WITH STROKE': br'\textbari',
    u'LATIN SMALL LETTER E WITH TILDE': br'\~e',
    u'INVERTED QUESTION MARK': br'\textquestiondown',
    u'INVERTED EXCLAMATION MARK': [br'\textexclamationdown', br'\textexclamdown'],
    u'HORIZONTAL ELLIPSIS': br'\dots',
    u'RIGHT DOUBLE QUOTATION MARK': br'\textquotedblright',
    u'LEFT DOUBLE QUOTATION MARK': br'\textquotedblleft',
    u'LEFT-POINTING DOUBLE ANGLE QUOTATION MARK': br'\guillemotleft',
    u'RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK': br'\guillemotright',
    u'LATIN LETTER ALVEOLAR CLICK': [br'\textdoublebarpipe', br'\textdoublebarpipevar'],
    u'PLUS-MINUS SIGN': br'\plusminus',
    u'LATIN SMALL LETTER E WITH MACRON AND ACUTE': br'\textacutemacron e',
    u'LATIN SMALL LETTER E WITH OGONEK': br'\textpolhook e',
    u'LATIN SMALL LETTER A WITH OGONEK': br'\c{a}',
    u'LATIN SMALL LETTER TURNED M': br'\textturnm',
    u'MODIFIER LETTER TRIANGULAR COLON': br'\textlengthmark',
    u'LESS-THAN SIGN': br'\textless',
    u'GREATER-THAN SIGN': br'\textgreater',
    # a bit of a misuse, but that's how it is used in goba.bib:
    u'LATIN CROSS': br'\textbarpipe',
    # again a mis-use:
    u'LATIN SMALL LETTER OPEN E': br'\textepsilon',
    u'LATIN SMALL LETTER GAMMA': [br'\textgamma', br'\gamma'],
    u'LATIN SMALL LETTER TURNED V': br'\textturnv',
    u'GREEK SMALL LETTER BETA': br'\textbeta',
    u'GREEK CAPITAL LETTER ETA': br'\textEta',
    u'GREEK SMALL LETTER OMEGA': br'\textomega',
    u'LATIN SMALL LETTER UPSILON': br'\textupsilon',
    u'LATIN SMALL LETTER ESH': br'\textesh',
    u'CYRILLIC SMALL LETTER HARD SIGN': br'\texthardsign',
    u'EURO SIGN': br'\eurosign',
    u'DEGREE SIGN': br'\circ',
    u'VERTICAL LINE': br'\textvertline',
    u'DOUBLE VERTICAL LINE': br'\textdoublevertline',
    u'LATIN SMALL LETTER T WITH RETROFLEX HOOK': br'\:{t}',
    u'LATIN SMALL LETTER H WITH STROKE': br'\textcrh',
    u'LATIN SMALL LETTER REVERSED OPEN E': br'\textrevepsilon',
    u'LATIN SMALL LETTER PHI': br'\textphi',
    u'GREEK SMALL LETTER CHI': br'\textchi',
}

_LC_TABLES = (
    latexcodec.codec._LATEX_UNICODE_TABLE, latexcodec.codec._ULATEX_UNICODE_TABLE)

assert u'\xe4'.encode('latex') == r'\"a'
assert r'\"a'.decode('latex') == u'\xe4'

for unicode_text, latex_text in sorted(
        list(LATEX_TABLE.items()), key=lambda t: t[0], reverse=True):
    if not isinstance(latex_text, (list, tuple)):
        latex_text = [latex_text]
    uchar = unicodedata.lookup(unicode_text)
    for table in _LC_TABLES:
        for lt in latex_text:
            table.register(uchar, lt)


numcharref_patterns = [
    re.compile('\\\\?&#(?P<dec>[0-9]+);'),
    re.compile('\?\[\\\\u\s*(?P<dec>[0-9]+)\]')]

command_patterns = [
    re.compile('\\\\%s \{(?P<arg>[^\}]+)\}' % name)
    for name in ['url', 'emph', 'textit', 'texttt']]


def numcharref_repl(m):
    return unichr(int(m.group('dec')))


def is_combining(c):
    try:
        return unicodedata.name(c).startswith('COMBINING')
    except ValueError:
        return False


def ulatex_preprocess(s):
    s = unicodedata.normalize('NFC', s.decode('utf8'))
    for c in s:
        if is_combining(c):
            print s
            raise ValueError
    return s


language_tags = {
    'latin': 'lat',
    'zh': 'zho',
    'hindi': 'hin',
    'eng': 'eng',
    'viet': 'vie',
    'tib': 'bod',
    'skt': 'san',  # Sanskrit
    'gujarati': 'guj',
    'pacoh': 'pac',
    'thai': 'tha',
    'dutch': 'nld',
    'burm': 'mya',
    'dan': 'dan',
    'norw': 'nor',
    'oldkhmer': 'qok',
    'ital': 'ita',
    'santali': 'sat',
    'span': 'spa',
    'germ': 'deu',
    'fr': 'fra',
    'rus': 'rus'}
language_tag_pattern = re.compile(
    u"\\\\(?P<tag>%s)\s+" % '|'.join(list(language_tags.keys())))


def recode_language_tags(s):
    def repl(m):
        return '[%s] ' % language_tags[m.group('tag')]
    return language_tag_pattern.sub(repl, s)


def ulatex_postprocess(s, debracket=re.compile(u"\{([^\}]+)\}")):
    if not isinstance(s, text_type):
        s = s.decode('ascii')
    for p in command_patterns:
        s = p.sub(lambda m: m.group('arg'), s)
    s = debracket.sub(u"\\1", debracket.sub(u"\\1", s.replace('{}', '')))
    n = []
    comb = []
    for c in s:
        if is_combining(c):
            comb.append(c)
        else:
            n.append(c)
            while comb:
                n.append(comb.pop())
    s = u''.join(n)
    for p in numcharref_patterns:
        s = p.sub(numcharref_repl, s)
    for cmd in ['relax', 'it', 'em', 'textsc', 'cite', 'citet']:
        s = s.replace('\\' + cmd + ' ', '')
    s = recode_language_tags(s)
    return unicodedata.normalize('NFC', s)


def ulatex_decode(s):
    return ulatex_postprocess(ulatex_preprocess(s).decode('ulatex'))


# legacy
def u_escape(s):
    def iterchunks(s):
        for c in s:
            o = ord(c)
            if o <= 127:
                yield c
            else:
                yield r'?[\u%d]' % o

    return ''.join(iterchunks(s))


def u_unescape(s, pattern=re.compile(r'\?\[\\u(\d{3,5})\]')):
    def iterchunks(s, matches):
        pos = 0
        for m in matches:
            start, end = m.span()
            yield s[pos:start]
            yield unichr(int(m.group(1)))
            pos = end
        yield s[pos:]

    return ''.join(iterchunks(s, pattern.finditer(s)))


class U_escapeCodec(codecs.Codec):

    def encode(self, input, erors='strict'):
        return u_escape(input.encode('ascii')), len(input)

    def decode(self, input, erors='strict'):
        return u_unescape(input.decode('ascii')), len(input)


class U_escapeStreamWriter(U_escapeCodec, codecs.StreamWriter):
    pass


class U_escapeStreamReader(U_escapeCodec, codecs.StreamReader):
    pass


def _find_u_escape(encoding):
    if encoding == 'ascii+u_escape':
        return codecs.CodecInfo(name='ascii+u_escape',
            encode=U_escapeCodec().encode, decode=U_escapeCodec().decode,
            streamwriter=U_escapeStreamWriter, streamreader=U_escapeStreamReader)


codecs.register(_find_u_escape)

# legacy

def latex_to_utf8(s, verbose=True, debracket=re.compile("\{(.)\}")):
    us = s.decode("latex")
    us = debracket.sub("\\1", us)
    if verbose:
        remaininglatex(us)
    return us


platexspc = [re.compile(pattern) for pattern in [
    r'''\\(?P<typ>[^\%'\`\^\~\=\_\"\s\{]+)\{(?P<ch>[a-zA-Z]?)\}''',  # \typ{opt ch}
    r'''\\(?P<typ>['\`\^\~\=\_\"]+?)\{(?P<ch>[a-zA-Z])\}''',  # \typ {ch}
    r'\\(?P<typ>[^a-zA-Z\s\%\_])(?P<ch>[a-zA-Z])',
    r'\\(?P<typ>[^a-zA-Z\s\%\{\_]+)(?P<ch>[a-zA-Z])',
    r'\\(?P<typ>[^\{\%\_]+)\{(?P<ch>[^\}]+)\}',
    r'\\(?P<typ>[^\{\_\\\s\%]+)(?P<ch>\s)',
]]


def remaininglatex(txt):
    for pattern in platexspc:
        o = pattern.findall(txt)
        if o:
            print o[:100] #txt[o.start()-10:o.start()+10], o.groups()
