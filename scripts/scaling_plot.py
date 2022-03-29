import sqlite3
db = 'file:project/benchmarks/results.db?mode=ro'
con = sqlite3.connect(db, uri=True)

cur = con.cursor()
cur.execute("SELECT * FROM runs WHERE description LIKE '%scaling%'")
benchmark_id = 91

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import EngFormatter

cur.execute("SELECT description FROM runs WHERE id = ?", (benchmark_id,))
description = cur.fetchone()[0]
weak_scaling = (description == "weak scaling")

def fetch_data(benchmark_id, mode):
    cur.execute("SELECT time_ns, n_summands FROM results WHERE run_id=? AND ranks = 1 AND mode = ?", (benchmark_id,mode))
    r = cur.fetchone()
    sequential_time = r[0] * 1e-9

    cur.execute("""
    SELECT id, ranks, time_ns, messages_sent, avg_summands_per_message, output
    FROM results 
    LEFT JOIN messages ON id=messages.result_id
    WHERE run_id = ? AND ranks > 1 AND mode = ?
    ORDER BY ranks;
    """, (benchmark_id,mode))

    X = [1] # core count
    Y = [1] # speed-up
    T = [sequential_time] # absolute time
    ERROR_H = []
    ERROR_L = []
    MSG_SENT = [0] # messages sent
    AVG_SUMMANDS_PER_MESSAGE = [0]

    for row in cur.fetchall():
        result_id, ranks, time_ns, messages_sent, avg_summands_per_message, output = row
        
        duration_str = next(filter(lambda l: l.startswith('durations='), output.split("\n"))).split("=")[1]
        durations = list(map(lambda x: float(x) * 1e-9, duration_str.split(",")))
        #print(durations)
        
        X.append(ranks)
        parallel_time = np.median(durations)
        ERROR_H.append(np.quantile(durations, 0.95))
        ERROR_L.append(np.quantile(durations, 0.05))
        T.append(parallel_time)
        speedup = sequential_time / parallel_time
        if weak_scaling:
            speedup *= ranks
        Y.append(speedup)
        MSG_SENT.append(messages_sent)
        AVG_SUMMANDS_PER_MESSAGE.append(avg_summands_per_message)
    return X, Y, r[1], T, ERROR_H, ERROR_L
    
RX, RY, N, reproblasT, errReproblasH, errReproblasL = fetch_data(benchmark_id, 'reproblas')
TX, TY, _, treeT, errTreeH, errTreeL = fetch_data(benchmark_id, 'tree')
    
f, axs = plt.subplots(ncols=2, figsize=(9,4))

ax = axs[0]

ax.set_ylabel(("Scaled " if weak_scaling else "") + "Speedup")
#ax.set_title(f"{description} of N={N} elements")

ax.plot([0,max(RX)], [0,max(RX)], "--", color='gray')
ax.scatter(RX, RY, s=[6.0] * len(RX), c='cyan', label='ReproBLAS')
ax.scatter(RX, TY, s=[6.0] * len(RX), c='red', label='Binary Tree Summation')

ax.legend(loc='upper left')

ax = axs[1]
formatter0 = EngFormatter(unit='s', places=0)
ax.set_yscale('log')
ax.grid(axis='y', which='both', linewidth=0.2)
ax.set_ylabel("Median accumulation time")
ax.errorbar(RX[1:], reproblasT[1:], yerr=(errReproblasL, errReproblasH), fmt='.c', label='ReproBLAS', capsize=3.0)
ax.errorbar(RX[1:], treeT[1:], yerr=(errTreeL, errTreeH), fmt='.r', label='Binary Tree Summation', capsize=3.0)
#ax.scatter(RX, treeT, c='red', label='Tree')
ax.yaxis.set_major_formatter(formatter0)
for ax in axs:
    ax.set_xlabel("PEs")
    ax.set_xticks([1] + list(range(RX[1],max(RX),80)) + [max(RX)], rotation=30)
    ax.tick_params(axis='x', labelrotation=45)
print(RX)
#ax.set_ylim(top=950e-6,bottom=0)
ax.legend(loc='upper right')
f.tight_layout()
f.savefig("figures/scaling.pdf")
