#!/usr/bin/env python3

"""
match entities in text
"""

import logging
from collections import namedtuple
from glob import glob
from pickle import load
from string import punctuation

# required to read pickled trie
from build_trie import Node

log = logging.getLogger(__name__)

# starts of partial matches which are ignored,
# because they coincide with very frequent words in English
IGNORED_PARTIAL_MATCHES = set(('A', 'The', 'In', 'As'))


# Tuple representing a matched entity mentions in a text with properties
# 'begin' (index of first matching token, counting from zero),
# 'end' (index of next token after the match) and
# 'ids' (list of corresponding Marine Regions identifiers)
Match = namedtuple('Match', ('begin', 'end', 'ids'))


def match_entities(tokens, trie,
                   ignored_partial_matches=set(IGNORED_PARTIAL_MATCHES)):
    """
    Match text tokens to entities in trie
    """
    matches = []
    node = trie
    begin = None
    i = 0

    while True:
        try:
            token = tokens[i]
        except IndexError:
            break

        try:
            # match?
            node = node.children[token]
        except KeyError:
            # no match
            if begin:
                if node.ids:
                    # full match
                    match = Match(begin, i, node.ids)
                    matches.append(match)
                else:
                    # partial match
                    if log.isEnabledFor(logging.DEBUG) and tokens[begin] not in ignored_partial_matches:
                        left_context = ' '.join(tokens[max(0, begin - 5):begin]).ljust(64, '.')
                        focus = ' '.join(tokens[begin:i]).ljust(64, '.')
                        right_context = ' '.join(tokens[i:i + 5])
                        log.debug('PARTIAL: ' + left_context + focus + right_context)
                    # restore position to that of first matched token
                    i = begin
                node = trie
                # reset
                begin = None
        else:
            # does match
            if begin is None:
                # start of new match
                begin = i
        i += 1

    return matches


def tokenize(text):
    # TODO: lousy tokenization
    return [token.strip(punctuation) for token in text.split()]


def load_trie(pkl_fname):
    log.info('reading trie from file ' + pkl_fname)
    return load(open(pkl_fname, 'rb'))


def print_matches(fname, tokens, matches):
    for begin, end, ids in matches:
        matched_string = ' '.join(tokens[begin:end])
        ids = ','.join(ids)
        print('\t'.join((fname, str(begin), str(end), ids, matched_string)))


if __name__ == '__main__':
    # Usage example:
    # python3 mrner/match_ent.py mr_trie.pkl "../nature/abs/soa/*.txt" >abs_matches.txt 2>abs_partial_matches.txt
    import sys

    logging.basicConfig(level=logging.DEBUG)
    # first argument is pickled trie
    trie = load_trie(sys.argv[1])
    # remaining arguments can filenames or quoted glob patterns
    for arg in sys.argv[2:]:
        for fname in glob(arg):
            text = open(fname).read()
            tokens = tokenize(text)
            matches = match_entities(tokens, trie)
            print_matches(fname, tokens, matches)
