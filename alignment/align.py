import ast
import pandas as pd
from mapknowledge import KnowledgeStore
from tqdm import tqdm

store = KnowledgeStore(npo=True)
store_sckan = KnowledgeStore()

map_node_name = {}

def load_log_file(log_file):
    # a function to load log file
    map_log = {}
    with open(log_file, "r") as f:
        while line := f.readline():
            line = line[34:]
            if line.startswith("* *"):
                path, completeness = line[4:].split(": ")
                map_log[path] = {"completeness": completeness.strip()}
            if line.startswith("- -"):
                feature, value = line[4:].split(": ", 1)
                map_log[path][feature] = ast.literal_eval(value)

    return map_log

def get_node_name(node):
    if node in map_node_name:
        return map_node_name[node]
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
    map_node_name[node] = (name[0], tuple(name[1:] if len(name) > 1 else ()))
    return name

def get_missing_nodes(map_log, save_file):
    nodes_to_neuron_types = {}
    for k, v in map_log.items():
        for node in v.get("missing_nodes", []):
            nodes_to_neuron_types[node] = nodes_to_neuron_types.get(node, []) + [k]

    df = pd.DataFrame(columns=["Node", "Node Name", "Appear in"])
    for node, k_types in tqdm(nodes_to_neuron_types.items()):
        name = get_node_name(node)
        name = " IN ".join(name)
        df.loc[len(df)] = [node, name, "\n".join(list(set(k_types)))]

    df = df.sort_values("Appear in")
    df.to_csv(f"{save_file}", index=False)
    return df

def organised_and_save_map_log(map_log, save_file):
    # a function to organised data into dataframe and then save it as csv file
    ### complete neuron:
    columns = [
        "Neuron NPO",
        "Completeness",
        "Missing Nodes",
        "Missing Node Name",
        "Missing Edges",
        "Missing Edge Name",
        "Missing Segments",
        "Missing Segment Name",
        "Rendered Edges",
        "Rendered Edge Name",
    ]
    df = pd.DataFrame(columns=columns)
    keys = ["missing_nodes", "missing_edges", "missing_segments", "rendered_edges"]
    for neuron, value in tqdm(map_log.items()):
        info = {}
        for key in keys:
            info[key] = "\n".join([str(mn) for mn in list(value.get(key, []))])

            if len(value.get(key, [])) > 0:
                if key not in ["missing_edges", "rendered_edges"]:
                    names = [get_node_name(node) for node in value.get(key, [])]
                else:
                    names = []
                    for edge in value.get(key, []):
                        names += [(get_node_name(edge[0]), get_node_name(edge[1]))]
            else:
                names = ""
            info[key + "_name"] = "\n".join([str(mnn) for mnn in names])
        df.loc[len(df)] = [neuron, value["completeness"]] + list(info.values())

    df = df.sort_values("Completeness")
    df.to_csv(f"{save_file}", index=False)
    return df

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Generate missing nodes and edges on the generated flatmaps"
    )
    parser.add_argument("--log_file", metavar="log_file", help="log source file")
    parser.add_argument(
        "--missing_file", metavar="missing_file", help="destination missing csv file"
    )
    parser.add_argument(
        "--rendered_file", metavar="rendered_file", help="destination rendered csv file"
    )
    args = parser.parse_args()
    map_log = load_log_file(args.log_file)
    get_missing_nodes(map_log, args.missing_file)
    organised_and_save_map_log(map_log, args.rendered_file)

if __name__ == "__main__":
    main()
