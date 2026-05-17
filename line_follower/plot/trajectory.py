#!/usr/bin/env python3

import matplotlib.pyplot as plt


def main():

    x = []
    y = []

    try:
        with open("trajectory.csv", "r") as f:

            for line in f:

                a, b = line.split(",")

                x.append(float(a))
                y.append(float(b))

    except FileNotFoundError:
        print("trajectory.csv not found")
        return

    plt.plot(x, y)
    plt.title("Robot Trajectory")
    plt.xlabel("X (m)")
    plt.ylabel("Y (m)")
    plt.axis("equal")
    plt.grid()
    plt.show()


if __name__ == "__main__":
    main()