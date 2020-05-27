#!/usr/bin/python3
# import roveranalzer
# import logging # <-- runSim.py erzeuge logfile runSim.log
import os
import sys

import numpy
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd

from roveranalyzer.runner.opprunner import BaseRunner, process_as


class SimulationRun(BaseRunner):
    def __init__(self, working_dir, args):
        super().__init__(working_dir, args)

    @staticmethod
    def get_degree_informed_dataframe(filepath):
        df_r = pd.read_csv(filepath, delimiter=" ", header=[0], comment="#")
        dt = 0.4  # one time frame = 0.4s
        df_r = df_r.iloc[249:, :]
        df_r["timeStep"] = (
            dt * df_r["timeStep"] - 100.0
        )  # information dissemination starts at 100s
        df_r.index = df_r.index - 249
        return df_r

    @process_as({"prio": 20, "type": "post"})
    def degree_informed_extract(self):
        filename = "DegreeInformed.txt"
        # wait for file
        filepath = self.wait_for_file(
            os.path.join(self.result_base_dir(), "vadere.d", filename)
        )
        # replace it with file extraction
        df_r = self.get_degree_informed_dataframe(filepath)
        df_r.to_csv(
            os.path.join(os.path.dirname(filepath), "DegreeInformed_extract.txt"),
            sep=" ",
        )

        # plot
        plt.plot(df_r.iloc[:, 0], df_r.iloc[:, 3])
        plt.axhline(y=0.95, c="r")
        plt.xlabel("Time [s] (Time = 0s : start of information dissemination)")
        plt.ylabel("Percentage of pedestrians informed [%]")
        plt.title("Information degree")
        plt.savefig(os.path.join(os.path.dirname(filepath), "InformationDegree.png"))

    @process_as({"prio": 10, "type": "post"})
    def time_95_informed(self):
        filename = "DegreeInformed.txt"
        # wait for file
        filepath = self.wait_for_file(
            os.path.join(self.result_base_dir(), "vadere.d", filename),
        )

        # replace it with file extraction
        df_r = self.get_degree_informed_dataframe(filepath)

        dt = 0.4
        time95 = 0.0
        for perc in df_r.iloc[:, 3]:
            if perc >= 0.95:
                break
            time95 += dt

        f = open(os.path.join(os.path.dirname(filepath), "Time95Informed.txt"), "x")
        f.write(f" timeToInform95PercentAgents\n0 {time95}")
        f.close()

    @process_as({"prio": 30, "type": "post"})
    def PoissonParameter(self):
        filename = "numberPedsGen.txt"
        # wait for file
        filepath = self.wait_for_file(
            os.path.join(self.result_base_dir(), "vadere.d", filename),
        )

        # replace it with file extraction
        df_r = pd.read_csv(filepath, delimiter=" ", header=[0], comment="#")

        poisson_parameter = numpy.mean(df_r.iloc[:, 1])

        f = open(os.path.join(os.path.dirname(filepath), "PoissonParameter.txt"), "x")
        f.write(f" PoissonParameter\n0 {poisson_parameter}")
        f.close()



if __name__ == "__main__":


    runner = SimulationRun(
        os.getcwd(),
        [
            "--qoi",
            "DegreeInformed_extract.txt",
            "Time95Informed.txt",
            "PoissonParameter.txt",
            "--experiment-label",
            datetime.now().isoformat().replace(":", "").replace("-", ""),
            "--run-name",
            "run_0_0"
        ]
    )
    runner.run()
