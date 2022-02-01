import sqlite3
import os
import numpy as np
import matplotlib.pyplot as plt

def fetch_median(cur, result_id):
    cur.execute("SELECT time_ns FROM durations WHERE result_id = ?", (result_id,))
    return np.median(cur.fetchall())



def fetch_slowdown_data(cur,commit,min_core_count,slower_mode,comparison_mode):
    # select newest matching run
    cur.execute("SELECT id,date,hostname,description FROM runs WHERE revision = ? AND cluster_size >= ? ORDER BY date DESC LIMIT 1",
            (commit, min_core_count))
    result = cur.fetchone()
    if len(result) == 0:
        raise Exception("No benchmark run matched the specified criteria")

    run_id, date, hostname, description = result
    print(f"[INFO] Selecting run {run_id} from {date}, host {hostname}, description: {description}")

    cur.execute("""
    SELECT a.n_summands, a.id, b.id
    FROM results a, results b
    WHERE a.run_id = ? AND a.run_id = b.run_id AND a.mode = ? AND b.mode = ?
        AND a.datafile = b.datafile AND a.n_summands = b.n_summands
        AND a.repetitions = b.repetitions
    ORDER BY a.n_summands ASC
    """, (run_id,comparison_mode,slower_mode))

    X = [] # n summands
    Y = [] # slowdown
    for row in cur.fetchall():
        n, a_id, b_id = row
        slowdown = fetch_median(cur, b_id) / fetch_median(cur, a_id)
        X.append(n)
        Y.append(slowdown)
    print(X)
    print(Y)
    return X, Y

def plot_slowdown(output_path, data):
    f = plt.figure()
    plt.scatter(data[0], data[1])
    plt.savefig(output_path)



if __name__ == '__main__':
    con = sqlite3.connect("project/benchmarks/results.db")

    plot_slowdown("figures/slowdown_tree_reproblas.eps",
        fetch_slowdown_data(con.cursor(), "8cd9287c68401e48d103fdee2334342d65a438cc", 256, "tree", "reproblas"))



