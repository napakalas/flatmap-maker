import json
import pandas as pd
from tqdm import tqdm
import ast

from mapknowledge import KnowledgeStore

store = KnowledgeStore(npo=True)
store_sckan = KnowledgeStore()

map_node_name = {}

# a function to load log file
def load_log_file(log_file):
    map_log = {}
    with open(log_file, 'r') as f:
        while line := f.readline():
            line = line[34:]
            if line.startswith('* *'):
                path, completeness = line[4:].split(': ')
                map_log[path] = {'completeness': completeness.strip()}
            if line.startswith('- -'):
                feature, value =  line[4:].split(': ', 1)
                map_log[path][feature] = ast.literal_eval(value)
                
    return map_log

def get_node_name(node):
    if node[0] is not None:
        name = store.label(node[0])
        name = [store_sckan.label(node[0]) if name == node[0] else name]
    else:
        name = [node[0]]
    for n in node[1]:
        if n is not None:
            loc = store.label(n)
            loc = store_sckan.label(n) if n == loc else loc
        else:
            loc = n
        name += [loc]
    map_node_name[node] = (name[0], tuple(name[1:] if len(name)>1 else ()))
    return name

def get_missing_nodes(map_log, save_file):
    nodes_to_neuron_types = {}
    for k, v in map_log.items():
        for node in v.get('missing_nodes', []):
            k_type = 'sparc-nlp' if 'sparc-nlp' in k else 'ApiNATOMY'
            nodes_to_neuron_types[node] = nodes_to_neuron_types.get(node, []) + [k_type]
            
    df = pd.DataFrame(columns=['Node', 'Node Name', 'Appear in'])
    for node, k_types in tqdm(nodes_to_neuron_types.items()):
        name = get_node_name(node)
        name = ' IN '.join(name)
        df.loc[len(df)] = [
            node,
            name,
            '/'.join(list(set(k_types)))
        ]
    
    df = df.sort_values('Appear in')
    df.to_csv(f'{save_file}', index=False)
    return df

# a function to organised data into dataframe and then save it as csv file

def organised_and_save_map_log(map_log, save_file):
    ### complete neuron:
    df = pd.DataFrame(columns=['Neuron NPO', 'Completeness', 'Missing Nodes', 'Missing Node Name', 'Missing Edges', 'Missing Edge Name', 'Rendered Edges', 'Rendered Edge Name'])
    for neuron, value in tqdm(map_log.items()):
        missing_nodes = '\n'.join([str(mn) for mn in list(value.get('missing_nodes',[]))])

        if len(value.get('missing_nodes',[]))>0:
            missing_node_name = [map_node_name[node] for node in value.get('missing_nodes',[])]
        else:
            missing_node_name = ''
        missing_node_name = '\n'.join([str(mnn) for mnn in missing_node_name])
        
        missing_edges = '\n'.join([str(me) for me in list(value.get('missing_edges',[]))])

        if len(value.get('missing_edges',[])):
            for edge in value.get('missing_edges',[]):
                if edge[0] not in map_node_name:
                    get_node_name(edge[0])
                if edge[1] not in map_node_name:
                    get_node_name(edge[1])
            missing_edge_name = [(map_node_name[edge[0]], map_node_name[edge[1]])]
        else:
            missing_edge_name = ''
        missing_edge_name = '\n'.join([str(men) for men in missing_edge_name])

        rendered_edges = '\n'.join([str(me) for me in list(value.get('rendered_edges',[]))])
        
        if len(value.get('rendered_edges',[])):
            for edge in value.get('rendered_edges',[]):
                if edge[0] not in map_node_name:
                    get_node_name(edge[0])
                if edge[1] not in map_node_name:
                    get_node_name(edge[1])
            rendered_edge_name = [(map_node_name[edge[0]], map_node_name[edge[1]])]
        else:
            rendered_edge_name = ''
        rendered_edge_name = '\n'.join([str(men) for men in rendered_edge_name])
        
        df.loc[len(df)] = [
            neuron, 
            value['completeness'], 
            missing_nodes,
            missing_node_name,
            missing_edges,
            missing_edge_name,
            rendered_edges,
            rendered_edge_name
        ]
    df = df.sort_values('Completeness')
    df.to_csv(f'{save_file}', index=False)
    return df


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate missing nodes and edges on the generated flatmaps")
    parser.add_argument('--log_file', metavar='log_file', help='log source file')
    parser.add_argument('--missing_file', metavar='missing_file', help='destination missing csv file')
    parser.add_argument('--rendered_file', metavar='rendered_file', help='destination rendered csv file')

    args = parser.parse_args()
    map_log = load_log_file(args.log_file)
    get_missing_nodes(map_log, args.missing_file)
    organised_and_save_map_log(map_log, args.rendered_file)

if __name__ == '__main__':
    main()