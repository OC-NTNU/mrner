#!/usr/bin/env python

"""
build trie from export of Marine Regions database
"""

from collections import namedtuple
from pickle import dump

import re
import logging

log = logging.getLogger(__name__)

# place types which are skipped because that are unlikely to appear in normal text,
# e.g. area identifiers like '72M7'
SKIPPED_PLACE_TYPES = {'ICES Statistical Rectangles',
                       'FAO Subdivisions',
                       'NAFO Area',
                       'ICES Areas'}

# names which are skipped because they coincide with very frequent words in English
SKIPPED_GEO_NAMES = {'As', 'Of'}

# other names which are skipped because of collisions, e.g. "H2"
SKIPPED_GEO_NAMES_PAT = r"^[A-Z]+[0-9][A-Z0-9]*$"

# Tuple representing an entity with a list of tokens and a unique id
Entity = namedtuple('Entity', ('tokens', 'id'))


def read_mr_entities(csv_fname,
                     skipped_geo_names=SKIPPED_GEO_NAMES,
                     skipped_geo_names_pat=SKIPPED_GEO_NAMES_PAT,
                     skipped_place_types=SKIPPED_PLACE_TYPES):
    """
    Read partial export of Marine Regions database in CSV format
    with fields MRGID, GeoName, Language and Placetype.
    Skips certain types and names.
    Returns a list of Entity tuples.
    """
    entities = []
    skipped_geo_names_re = re.compile(skipped_geo_names_pat)


    log.info('reading entities from file ' + csv_fname)
    with open(csv_fname) as f:
        # skip header line
        f.readline()
        for line in f:
            line = line.rstrip('\n')
            try:
                mrgid, geo_name, language, place_type = line.split('\t')
            except:
                log.warn('ill-formed line: ' + line)
                continue

            if (place_type in skipped_place_types or
                geo_name in skipped_geo_names or
                skipped_geo_names_re.match(geo_name)):
                log.debug('skipping: ' + line)
                continue

            # TODO: handle cases like "Narrows, The"
            # TODO: handle punctuation etc.
            tokens = geo_name.split()
            entities.append(Entity(tokens, mrgid))

    log.info('{} entites'.format(len(entities)))
    return entities


# Tuple representing a node in the trie with properties 'ids' and 'children'.
# 'ids' lists the id of each entity whole tokens equal the path through the trie,
# possibly an empty list for non-terminal nodes.
# 'children' is a dict mapping tokens to child nodes, representing further paths
# down the trie.
Node = namedtuple('Node', ('ids', 'children'))


def build_trie(entities):
    """
    Build a trie from entities for fast matching of token sequences to entities
    """
    trie = Node([], {})
    node_count = 1
    token_count = 0

    for tokens, id in entities:
        node = trie
        token_count += len(tokens)

        for token in tokens:
            # traverse trie, adding new nodes where required
            try:
                node = node.children[token]
            except KeyError:
                new_node = Node([], {})
                node.children[token] = new_node
                node = new_node
                node_count += 1

        node.ids.append(id)

    log.info('{} tokens'.format(token_count))
    log.info('{} trie nodes'.format(node_count))
    return trie


def dump_trie(trie, pkl_fname):
    log.info('writing trie to file ' + pkl_fname)
    dump(trie, open(pkl_fname, 'wb'))


# utility/debug functions


def print_node(node, indent=0):
    for child_token, child_node in node.children.items():
        print(indent * ' ' + child_token, child_node.ids or '')
        print_node(child_node, indent + 4)


def print_trie(node, start_token):
    print(start_token, node.ids)
    print_node(node.children[start_token], 4)


if __name__ == '__main__':
    # Usage example:
    # mrner/build_trie.py marineregions_gazetteer_export_2016-03-30.csv mr_trie.pkl
    import sys
    logging.basicConfig(level=logging.DEBUG)
    csv_fname, pkl_fname = sys.argv[1:3]
    entities = read_mr_entities(csv_fname)
    trie = build_trie(entities)
    # print_trie(trie, 'West')
    dump_trie(trie, pkl_fname)
