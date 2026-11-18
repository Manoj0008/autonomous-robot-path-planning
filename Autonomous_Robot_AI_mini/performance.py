
import matplotlib.pyplot as plt
import os


def plot_results(results):

    os.makedirs("results", exist_ok=True)

    names = [r["name"] for r in results]

    # Graph 1: Path Length
    path_lengths = [r["path"] for r in results]

    plt.figure(figsize=(8, 5))
    plt.bar(names, path_lengths)
    plt.title("Algorithm Comparison - Path Length")
    plt.xlabel("Algorithms")
    plt.ylabel("Path Length")
    plt.savefig("results/path_comparison.png")
    plt.show()

    # Graph 2: Nodes Explored
    nodes = [r["nodes"] for r in results]

    plt.figure(figsize=(8, 5))
    plt.bar(names, nodes)
    plt.title("Algorithm Comparison - Nodes Explored")
    plt.xlabel("Algorithms")
    plt.ylabel("Number of Nodes")
    plt.savefig("results/nodes_comparison.png")
    plt.show()

    # Graph 3: Execution Time
    times = [r["time"] for r in results]

    plt.figure(figsize=(8, 5))
    plt.bar(names, times)
    plt.title("Algorithm Comparison - Execution Time")
    plt.xlabel("Algorithms")
    plt.ylabel("Time (seconds)")
    plt.savefig("results/time_comparison.png")
    plt.show()

    print("Performance graphs saved successfully!")
