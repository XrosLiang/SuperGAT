import os
from typing import List, Tuple

from sklearn.manifold import TSNE
import networkx as nx
import torch
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def _get_key(args):
    return "{}-{}-{}".format(args.model_name, args.dataset_name, args.custom_key) if args is not None else "raw"


def _get_key_and_makedirs(args, base_path, exist_ok=True, **kwargs) -> Tuple[str, str]:
    _key = _get_key(args)
    _path = os.path.join(base_path, _key)
    os.makedirs(_path, exist_ok=exist_ok, **kwargs)
    return _key, _path


def plot_multiple_dist(data_list: List[torch.Tensor], name_list: List[str], x, y,
                       args=None, extension="png", custom_key="",
                       ylim=None, plot_func=None,
                       **kwargs):

    plt.figure(figsize=(3 * len(name_list), 7))

    # data_list, name_list -> pd.Dataframe {x: [name...], y: [datum...]}
    pd_data = {x: [], y: []}
    for data, name in zip(data_list, name_list):
        data = data.cpu().numpy()
        pd_data[x] = pd_data[x] + [name for _ in range(len(data))]
        pd_data[y] = pd_data[y] + list(data)
    df = pd.DataFrame(pd_data)

    plot_func = plot_func or sns.boxenplot
    plot = plot_func(x=x, y=y, data=df, **kwargs)

    if ylim:
        plot.set_ylim(*ylim)

    key, path = _get_key_and_makedirs(args, base_path="../figs")
    plot.get_figure().savefig("{}/fig_dist_{}_{}.{}".format(path, key, custom_key, extension),
                              bbox_inches='tight')
    plt.clf()


def plot_nodes_by_tsne(xs, ys, args=None, extension="png"):
    x_embed = TSNE(n_components=2).fit_transform(xs)

    df = pd.DataFrame({
        "x_coord": x_embed[:, 0],
        "y_coord": x_embed[:, 1],
        "class": ys,
    })
    plot = sns.scatterplot(x="x_coord", y="y_coord", hue="class", data=df,
                           legend=False, palette="Set1")
    plot.set_xlabel("")
    plot.set_ylabel("")
    plot.get_xaxis().set_visible(False)
    plot.get_yaxis().set_visible(False)
    sns.despine(left=False, right=False, bottom=False, top=False)

    key, path = _get_key_and_makedirs(args, base_path="../figs")
    plot.get_figure().savefig("{}/fig_tsne_{}.{}".format(path, key, extension), bbox_inches='tight')
    plt.clf()


def plot_graph_layout(xs, ys, edge_index, edge_to_attention, args=None, extension="png", layout="tsne"):
    G = nx.Graph()
    G.add_edges_from([(i, j) for i, j in np.transpose(edge_index)])

    if layout == "tsne":
        x_embed = TSNE(n_components=2).fit_transform(xs)
        pos = {xid: x_embed[xid] for xid in range(len(xs))}
    else:
        pos = nx.layout.spring_layout(G)

    n_classes = len(np.unique(ys))

    node_sizes = 4
    node_cmap = plt.cm.get_cmap("Set1")
    class_to_node_color = {c: node_cmap(c / n_classes) for c in range(n_classes)}
    node_color_list = [class_to_node_color[y] for y in ys]

    nodes = nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_color_list, alpha=0.5)

    if edge_to_attention is not None:
        edge_color = [float(np.mean(edge_to_attention[tuple(sorted(e))])) for e in G.edges]
        edge_kwargs = dict(edge_color=edge_color, edge_cmap=plt.cm.Greys, width=1.25, alpha=0.5,
                           vmin=np.min(edge_color) / 2, vmax=np.max(edge_color) * 2)
    else:
        edge_kwargs = dict(edge_color="grey", width=0.5, alpha=0.3)

    edges = nx.draw_networkx_edges(G, pos, node_size=node_sizes, **edge_kwargs)

    ax = plt.gca()
    ax.set_axis_off()

    key, path = _get_key_and_makedirs(args, base_path="../figs")
    plt.savefig("{}/fig_glayout_{}.{}".format(path, key, extension), bbox_inches='tight')
    plt.clf()
