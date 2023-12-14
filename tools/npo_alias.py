#===============================================================================

import pandas as pd
import ast
import json
import logging
import os

#===============================================================================

class PathError(Exception):
    pass

#===============================================================================

def generate_aliases(aligned_file, connectivity_term_file):
    df_alias = pd.read_csv(aligned_file)
    df_alias = df_alias[df_alias['Selected'].str.len() > 0]
    
    if os.path.exists(connectivity_term_file):
        with open(connectivity_term_file, 'r') as f:
            connectivity_terms = json.load(f)
    else:
        connectivity_terms = []

    current_alias = {}
    for term in connectivity_terms:
        term_id = (term['id'][0], tuple(term['id'][1])) if isinstance(term['id'], list) else term['id']
        current_alias[term_id] = term
        current_alias[term_id]['aliases'] = [(alias[0], tuple(alias[1])) if isinstance(alias, list) else alias
                                             for alias in current_alias[term_id]['aliases']]

    for idx in df_alias.index:
        alias = df_alias.loc[idx]
        if len(alias['Selected'].strip()) > 0:
            alias_id = ast.literal_eval(alias['Align candidates']) if alias['Selected'] == '1' else ast.literal_eval(alias['Selected'])
            alias_id = (alias_id[0], tuple(alias_id[1]))
            alias_node = ast.literal_eval(alias['Node'])
            alias_node = (alias_node[0], tuple(alias_node[1]))
            alias_name = '/'.join(ast.literal_eval(alias['Candidate name']))  if alias['Selected'] == '1' else None
            if alias_id in current_alias:
                if alias_node not in current_alias[alias_id]['aliases']:
                    current_alias[alias_id]['aliases'] += [alias_node]

            else:
                current_alias[alias_id] = {
                    'id': alias_id,
                    'aliases': [
                        alias_node
                    ]
                }

            if alias_name is not None:
                current_alias[alias_id]['name'] = alias_name

    with open(connectivity_term_file, 'w') as f:
        json.dump(list(current_alias.values()), f, indent=4)

def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Checking nodes and edges completeness in the generated flatmap")
    parser.add_argument('--aligned-file', dest='aligned_file', metavar='ALIGNED_FILE', help='Missing node alignment file that is already curated')
    parser.add_argument('--connectivity-terms-file', dest='connectivity_term_file', help='The connectivity terms file that will be merged with the aligned file')
    
    try:
        args = parser.parse_args()
        generate_aliases(args.aligned_file, args.connectivity_term_file)
    except PathError as error:
        sys.stderr.write(f'{error}\n')
        sys.exit(1)
    sys.exit(0)

#===============================================================================

if __name__ == '__main__':
    main()

#===============================================================================

# This script is used to merge the currated align missing node to the existing connectivity_terms.json
# Command:
# python ./npo_alias.py --aligned-file `the aligned file generated by npo_align.py and has been curated`
#                       --connectivity-terms-file `connectivity_terms file to merge`