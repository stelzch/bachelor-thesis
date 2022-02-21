import os
print("Building C++ extension...")
cpp_dir = "project/jupyter/cpp"
os.system(f"cd {cpp_dir} && python3 setup.py build")

import sys
from glob import glob
sys.path.append(glob(f"{cpp_dir}/build/lib*/")[0])

from radtree import message_count, message_count_remainder_at_end
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import EngFormatter


def plot_message_count(p, maxN, message_count_func, ylim=None):
    X = np.arange(p, maxN, dtype=np.uint)
    Y = np.array(message_count_func(list(X), p))
    f = plt.figure()
    ax = f.subplots(1)
    ax.set_xlabel("Number of elements")
    ax.set_ylabel("Number of messages")
    
    if ylim is not None:
        ax.set_ylim(top=ylim)

    plt.plot(X, Y)
    
    return f


f1 = plot_message_count(256, 200_000, message_count, ylim=2500).savefig("figures/message_count_256.pdf")
f2 = plot_message_count(256, 200_000, message_count_remainder_at_end, ylim=2500).savefig("figures/message_count_256_remainder_at_end.pdf")
