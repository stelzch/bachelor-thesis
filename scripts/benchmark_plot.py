#!/usr/bin/env python
# coding: utf-8

# In[2]:


import matplotlib.pyplot as plt
import numpy as np
import sqlite3
from matplotlib.ticker import EngFormatter

def fetch_data(run_id, mode):
    cur.execute(f"SELECT n_summands, datafile, time_ns, stddev, repetitions FROM results WHERE mode = ?" \
                "AND run_id = ? ORDER BY n_summands",
               (mode, run_id))

def xye(data):
    x = list(map(lambda x: x[0], data)) # n_summands
    y = list(map(lambda x: x[2] / 1e9, data)) # time_ns
    e = list(map(lambda x: x[3] / 1e9, data)) # stddev
    return x, y, e

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
    
    
scatter_plot(last_complete_benchmark()).savefig("figures/benchmarkScatter.pdf")

# In[ ]:




