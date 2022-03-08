#!/usr/bin/env python
# coding: utf-8

# In[2]:

import matplotlib.pyplot as plt
import numpy as np
import sqlite3
from matplotlib.ticker import EngFormatter
from statistics import median

def fetch_data(run_id, mode):
    cur.execute(f"SELECT n_summands, datafile, time_ns, stddev, repetitions FROM results WHERE mode = ?" \
                "AND run_id = ? ORDER BY n_summands",
               (mode, run_id))
def xye(data):
    x = list(map(lambda x: x[0], data)) # n_summands
    y = list(map(lambda x: x[2] / 1e9, data)) # time_ns
    e = list(map(lambda x: x[3] / 1e9, data)) # stddev
    return x, y, e

def fetch_durations(run_id, datasetQuery='%'):
    plot_data = [[]]
    runs = cur.execute(f"SELECT id, mode, n_summands, datafile, ranks FROM results" \
                    " WHERE run_id = ? AND datafile LIKE ? ORDER BY n_summands, datafile, mode", (run_id,datasetQuery))
    prev_datafile = None
    for result_id, mode, n_summands, datafile, ranks in runs.fetchall():
        if mode == "baseline":
            continue

        if prev_datafile is not None and prev_datafile != datafile:
            plot_data.append([])
        cur.execute("SELECT time_ns / 1e9 FROM durations WHERE result_id = ?", (result_id,))
        
        durations = list(map(lambda x: x[0], cur.fetchall()))
        plot_data[-1].append({
            "mode": mode,
            "datafile": datafile,
            "n": n_summands,
            "m": ranks,
            "durations": durations
        })
        
        
        prev_datafile = datafile
    return plot_data


db = 'file:project/benchmarks/results.db?mode=ro'
con = sqlite3.connect(db, uri=True)
cur = con.cursor()

def scatter_plot(run_id):
    settings = {
        "allreduce": {
            "fmt": "bo",
            "label": "MPI_Allreduce",
            "include": True,
        },
        "tree": {
            "fmt": "ro",
            "label": "Tree Reduce",
            "include": True
        },
        "reproblas": {
            "fmt": "co",
            "label": "ReproBLAS",
            "include": True
        }
    }
    f = plt.figure()
    ax = f.subplots(1)
    ax.set_ylabel('Accumulate Time')
    ax.set_xlabel('number of summands')

    formatter0 = EngFormatter(unit='s', places=2)
    formatter1 = EngFormatter(places=2)
    ax.yaxis.set_major_formatter(formatter0)
    ax.xaxis.set_major_formatter(formatter1)

    for mode, v in settings.items():
        if not v["include"]:
            continue

        fetch_data(run_id, mode)
        data = cur.fetchall()

        ar_x, ar_y, ar_error = xye(data)
        ax.errorbar(ar_x, ar_y, yerr=ar_error, fmt=v["fmt"], label=v["label"], capsize=4.0)

        ticks = []
        for x in ar_x:
            lastX = ticks[-1] if len(ticks) > 0 else -1e10
            if x - lastX > 2e6:
                ticks.append(x)
        ax.xaxis.set_ticks(ticks)

    ax.legend(loc='upper left')

    ax.set_xlim(left=0)
    #ax.set_ylim(bottom=0)

    return f

def violin_plot(run_id, datasetQuery):
    plot_data = fetch_durations(run_id, datasetQuery)
    rows = len(plot_data)
    cols = max(map(lambda x: len(x), plot_data))
    formatter0 = EngFormatter(unit='s', places=2)

    f, axs = plt.subplots(nrows=rows, figsize=(7, 4 * rows))

    i = 0

    colorpalette = ["#034670ff", "#2f779dff", "#887006ff", "#ac360bff"]

    for dataset in plot_data:
        ax = axs[i] if rows > 1 else axs

        mode_durations = list(map(lambda x: x["durations"], dataset))

        ax.set_ylabel("Time")
        ax.yaxis.set_major_formatter(formatter0)
        ax.xaxis.can_zoom = False

        ax.get_xaxis().set_visible(True)

        # Ticks for each mode
        ax.get_xaxis().set_ticks(range(1, len(dataset)+1))

        medians = list(map(lambda d: median(d), mode_durations))
        labels = map(lambda x: x["mode"] + f" ({formatter0.format_eng(median(x['durations']))}s)", dataset)
        ax.get_xaxis().set_ticklabels(labels)


        #ax.yaxis.set_ticks(y_ticks)
        #ax.yaxis.set_ticks_position('both')
        #plt.setp(ax.get_yticklabels(), rotation=30, horizontalalignment='right')

        n = format(dataset[0]["n"], ",d").replace(",", " ")
        m = dataset[0]["m"]
        filename = dataset[0]["datafile"][5:]
        ax.set_title(f"{filename}, N={n}, p={m}")

        violins = ax.violinplot(mode_durations, showmedians=True, widths=0.5)
        for body, color in zip(violins["bodies"], colorpalette):
            body.set_color(color)

        i += 1
    margin_y = 0.08 / rows
    plt.subplots_adjust(left=0.15, bottom=0.0 + margin_y, right=0.98, top=1.0 - margin_y)
    return f

def slowdown_plot(run_id):
    plot_data = fetch_durations(run_id)
    formatter0 = EngFormatter(places=2)

    X = []
    slowdowns = []

    n_cores = plot_data[0][0]['m']
    for p in plot_data:
        n = p[0]['n']
        mode = lambda mode: (lambda x: x['mode'] == mode)
        tree_data = next(filter(mode('tree'), p))
        reproblas_data = next(filter(mode('reproblas'), p))

        tree_median = median(tree_data['durations'])
        reproblas_median = median(reproblas_data['durations'])

        slowdown = tree_median / reproblas_median
        X.append(n)
        slowdowns.append(slowdown)

    f, ax = plt.subplots(1)

    ax.set_title(f"Slowdown of Tree compared to ReproBLAS with p={n_cores} cores")
    ax.yaxis.set_label("Slowdown")
    ax.xaxis.set_label("number of summands")
    ax.xaxis.set_major_formatter(formatter0)

    ax.scatter(X, slowdowns)

    return f

def last_complete_benchmark(p=256):
    cur.execute("""
        SELECT run.id, COUNT(result.id) FROM runs run, results result
        WHERE result.run_id = run.id
            AND run.cluster_size = ?
            AND description NOT LIKE '%scaling%'
        GROUP BY run.id HAVING COUNT(result.datafile) = 10 * 3
        ORDER BY run.id DESC

        """, (p,))
    return cur.fetchone()[0]
    
last_complete = 69 # last_complete_benchmark()
print(f"Utilizing results from run {last_complete}")
scatter_plot(last_complete).savefig("figures/benchmarkScatter.pdf")
for dataset in ["354", "rokasA4", "rokasA8", "PeteD8", "rokasD1", "rokasD4", "rokasD7", "fusob", "multi100", "prim"]:
    violin_plot(last_complete, f"%{dataset}%").savefig(f"figures/violin{dataset.capitalize()}.pdf")
slowdown_plot(last_complete).savefig("figures/slowdownPlot.pdf")

# In[ ]:




