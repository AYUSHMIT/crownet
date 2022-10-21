import os
from typing import Dict
from roveranalyzer.analysis.common import RunMap, Simulation, SimulationGroup, SuqcStudy
from roveranalyzer.analysis.omnetpp import CellOccupancy, HdfExtractor, OppAnalysis
from roveranalyzer.simulators.opp.provider.hdf.IHdfProvider import BaseHdfProvider
from roveranalyzer.utils.dataframe import FrameConsumer
from roveranalyzer.utils.plot import (
    PlotUtil,
    mult_locator,
    paper_rc,
    check_ax,
    plt_rc_same,
    tight_ax_grid,
)
from a_mf_1d import SimFactory, ts_x, ts_y
from itertools import chain
from copy import deepcopy
from omnetinireader.config_parser import ObjectValue
import pandas as pd
import numpy as np
import seaborn as sn
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, MultipleLocator, AutoMinorLocator
from pandas import IndexSlice as _i


class SimF(SimFactory):
    def __call__(self, sim: Simulation, **kwds) -> SimulationGroup:
        iat = sim.run_context.ini_get(
            "*.bonnMotionServer.traceFile", regex=r".*iat_(\d+)_.*", apply=int
        )
        if iat == 50:
            ts = ts_x
        elif iat == 25:
            ts = ts_y
        map_t = sim.run_context.ini_get(
            "*.misc[*].app[0].scheduler.generationInterval", r"^(\d+[a-z]*).*"
        )
        entropy_provider: ObjectValue = sim.run_context.ini_get(
            "*.globalDensityMap.entropyProvider"
        )
        attr = deepcopy(kwds.get("attr", {}))
        attr["gt_change_rate"] = entropy_provider["coefficients"][1]
        attr["transmission_interval_ms"] = int(map_t[0:-2])  # remove 'ms' unit

        attr[
            "lbl"
        ] = f"S4-{self.group_num}: Map $\Delta t = {map_t}$ Change rate= {attr['gt_change_rate']}"
        attr["lbl_short"] = f"S1-{self.group_num}-{map_t}-{attr['gt_change_rate']} "
        attr["ts"] = ts
        kwds["attr"] = attr
        ret = SimulationGroup(group_name=f"S4-{self.group_num}", **kwds)
        self.group_num += 1
        return ret


def get_run_map_single_run(output_dir) -> RunMap:
    run1 = SuqcStudy("/mnt/data1tb/results/mf_1d_bm_rate_chage/")
    sim_factory = SimF()
    run_map = run1.update_run_map(
        RunMap(output_dir),
        sim_per_group=20,
        id_offset=0,
        sim_group_factory=sim_factory,
    )
    return run_map


def plot_packet_loss_ratio_over_time(run_map: RunMap):
    loss = OppAnalysis.run_get_packet_loss(run_map)
    fig, ax = check_ax()
    sn.lineplot(data=loss.reset_index(), x="time", y="lost_relative", hue="rep")
    ax.set_title("Relative packet loss over time for each simulation")
    fig.savefig(run_map.path("packet_loss_time_series.pdf"))


def msce_with_lbl(run_map: RunMap) -> pd.DataFrame:
    data = OppAnalysis.get_mse_cell_data_for_study(
        run_map,
        hdf_path="cell_mse_no_missing.h5",
        cell_count=1,  # will be ignored for entropy maps
        pool_size=24,
    )
    data = data.to_frame()
    data = data.join(run_map.id_to_label_series(enumerate_run=True), on="run_id")
    return data


def msce_plot(run_map: RunMap, data, g_name, _ff):
    fig, ax = check_ax()
    ax: plt.Axes
    g = run_map[g_name]
    box = data.loc[_i[:, g_name], ["cell_mse"]]
    ax.scatter("simtime", "cell_mse", data=box.reset_index(), marker=".")
    for _f in _ff:
        _f(ax)
    ax.set_xlim(0, 1500)
    mult_locator(ax.xaxis, 200, 100)
    lbl = g.lbl
    print(f"create figure {lbl}")
    ax.set_title(f"Cell error over time for {lbl} (all seeds)")
    ax.set_xlabel("time in [s]")
    ax.set_ylabel("mean squared cell error (MSCE)")
    return fig, ax


def save_msce_interval_info(run_map: RunMap):
    data = msce_with_lbl(run_map)
    data = data.reset_index().set_index(["simtime", "label"])

    slice_05_a = slice(1248.0, 1382.0)
    group_05 = [
        g.group_name for g in run_map.values() if g.attr["gt_change_rate"] == 0.5
    ]
    for g_name in group_05:
        g = run_map[g_name]
        print(f"create figure: {g_name}")
        for sim in g:
            plot_msce_interval_info(sim, g.lbl, g_name, slice_05_a)

    slice_1_a = slice(622.0, 726.0)
    slice_1_b = slice(1272.0, 1282.0)
    group_1 = [
        g.group_name for g in run_map.values() if g.attr["gt_change_rate"] == 1.0
    ]
    for g_name in group_1:
        g = run_map[g_name]
        print(f"create figure: {g_name}")
        for sim in g:
            plot_msce_interval_info(sim, g.lbl, g_name, slice_1_a)
            plot_msce_interval_info(sim, g.lbl, g_name, slice_1_b)


def plot_msce_interval_info(sim: Simulation, lbl, group_name, t_slice: slice):
    hdf = sim.base_hdf(group_name="cell_measures")
    with hdf.query as ctx:
        data = ctx.select(
            key=hdf.group,
            where=f"(simtime>{t_slice.start}) & (simtime<{t_slice.stop})",
            columns=["cell_mse"],
        )
    t_i = f"[{t_slice.start}, {t_slice.stop}]"
    with plt.rc_context(plt_rc_same()):
        fig, (a, b, c) = plt.subplots(nrows=3, ncols=1, figsize=(16, 2 * 9))
        fig.suptitle(f" {lbl} for interval {t_i}")
        data.hist(ax=a)
        a.set_title(f"Histogram of MSCE of interval {t_i}")
        a.set_ylabel("count")
        a.set_xlabel("MSCE")
        a.xaxis.set_major_locator(MaxNLocator(10))
        d = data.reset_index("simtime", drop=True).reset_index()
        dd = d.pivot_table(
            values="cell_mse", aggfunc="mean", index="x", columns="y", fill_value=0
        )
        dd.reset_index().plot(x="x", y=205.0, kind="scatter", ax=b)
        b.set_title(f"mean MSCE for upper corridor (y=205) in interval {t_i} ")
        b.set_ylabel("mean squared cell error (MSCE)")
        b.set_xticks(np.arange(0, 450, 20))
        dd.reset_index().plot(x="x", y=180.0, kind="scatter", ax=c)
        c.set_title(f"mean MSCE for upper corridor (y=180) in interval {t_i} ")
        c.set_ylabel("mean squared cell error (MSCE)")
        c.set_xticks(np.arange(0, 450, 20))
        fig.tight_layout(rect=(0, 0, 1, 0.98))

        file_name = (
            f"MSCE_{group_name}_interval_{int(t_slice.start)}-{int(t_slice.stop)}.pdf"
        )
        fig.savefig(os.path.join(sim.data_root, file_name))

    print("break")


def get_msce_err(run_map: RunMap):

    data = msce_with_lbl(run_map)
    data = data.reset_index().set_index(["simtime", "label"])

    err_bars = data.groupby(["simtime", "label"])["cell_mse"].agg(["mean", "std"])
    lbl_to_rate = pd.DataFrame(
        [(n, g.attr["gt_change_rate"]) for n, g in run_map.items()],
        columns=["label", "rate"],
    )
    err_bars = err_bars.join(lbl_to_rate.set_index("label"), on="label", how="left")
    err_bars = (
        err_bars.reset_index().set_index(["simtime", "label", "rate"]).sort_index()
    )
    rates = err_bars.index.get_level_values("rate").unique().sort_values()

    ax_param = {
        0.01: [lambda ax: ax.set_ylim(0.0, 0.20)],
        0.1: [lambda ax: ax.set_ylim(0.0, 20.0)],
        0.5: [lambda ax: ax.set_ylim(0.0, 250)],
        1.0: [lambda ax: ax.set_ylim(0.0, 1000)],
    }

    with plt.rc_context(plt_rc_same(rc={"legend.fontsize": "small"})):
        fig, axes = plt.subplots(rates.shape[0], 1, figsize=(16, 16))

        for ax, rate in zip(axes, rates):
            df = err_bars.loc[_i[:, :, rate]].copy().reset_index()
            # zorder = rates[0] + 10
            x = 0
            for idx, (_, g) in enumerate(
                run_map.iter(lambda x: x.attr["gt_change_rate"] == rate)
            ):
                _m = df["label"] == g.group_name
                _d = df.loc[_m]
                lbl = f"{g.group_name}: Map $\\Delta t = {g.attr['transmission_interval_ms']}ms$"
                ax.plot(
                    _d["simtime"],
                    _d["mean"],
                    label=lbl,
                    color=PlotUtil.plot_colors[idx],
                )
                ax.fill_between(
                    _d["simtime"],
                    _d["mean"] - _d["std"],
                    _d["mean"] + _d["std"],
                    alpha=0.2,
                    color=PlotUtil.plot_colors[idx],
                )

            ax.text(
                1.05,
                1,
                f"Mean squared map error (MSME) \n for change rate {rate} s",
                horizontalalignment="left",
                verticalalignment="top",
                fontsize="xx-large",
                transform=ax.transAxes,
            )
            ax.set_ylabel("MSME")
            for f in ax_param[rate]:
                f(ax)
            ax.set_xticks(np.arange(0, 1600, 200))
            if rate == rates[-1]:
                ax.set_xlabel("Simtime in seconds")

        fig.suptitle("Mean squared map error over time")
        fig.tight_layout(pad=1.05, rect=(0, 0, 0.98, 0.98))
        for ax in axes:
            ax.legend(loc="center left", fontsize="large", bbox_to_anchor=(1.03, 0.4))
        fig.savefig(run_map.path("msme_over_time_zoom.pdf"))


def _remove_target_cells(df: pd.DataFrame) -> pd.DataFrame:
    # remove cells under target area
    xy = df.index.to_frame()
    mask = np.repeat(False, xy.shape[0])
    for x in [400, 405, 410]:
        y = 180.0
        mask = mask | (xy["x"] == x) & (xy["y"] == y)

    for x in [0.0, 5.0, 10.0]:
        y = 205.0
        mask = mask | (xy["x"] == x) & (xy["y"] == y)

    masked_index = df.index[~mask]
    return df.loc[masked_index].copy(deep=True)


def create_cell_occupation_ratio(run_map: RunMap):
    ret = CellOccupancy.sg_create_cell_occupation_info(
        run_map["S4-0"],
        interval_bin_size=100.0,
        same_mobility_seed=True,
        frame_c=_remove_target_cells,
    )
    CellOccupancy.plot_cell_occupation_info(
        ret, run_map.path("cell_occupation_info.pdf")
    )


def create_cell_knowledge_ratio(run_map: RunMap):
    h5 = BaseHdfProvider(run_map.path("cell_knowledge_ratio.h5"))
    if not h5.hdf_file_exists:
        CellOccupancy.run_create_cell_knowledge_ratio(
            run_map, hdf_path="cell_knowledge_ratio.h5", frame_c=_remove_target_cells
        )

    # df = CellOccupancy.sim_create_cell_value_knowledge_ratio(run_map["S4-20"][0], _remove_target_cells)
    fig, axes = tight_ax_grid(2, 2, figsize=(16, 9))
    fig2, axes2 = tight_ax_grid(2, 2, figsize=(16, 9))
    axes = list(chain(*axes))
    axes2 = list(chain(*axes2))

    for idx, rate in enumerate(
        np.unique([g.attr["gt_change_rate"] for g in run_map.values()])
    ):
        ax: plt.Axes = axes[idx]
        ax2: plt.Axes = axes2[idx]
        for g_name, g in run_map.items():
            if g.attr["gt_change_rate"] != rate:
                continue
            with h5.query as ctx:
                df = ctx.select(
                    key="knowledge_ratio", where=f"rep in {g.ids()}", columns=["a_c"]
                )
                df = df.groupby("simtime").agg(["mean", "std"]).droplevel(0, axis=1)
                ax.plot(df.index, df["mean"], label=g.lbl)
                ax.legend()
                ax.set_title(f"Cell knowledge ratio $a_C$ with change rate {rate} [s]")

                ax2.set_ylim(0.9, 1.0)
                ax2.set_xlim(400, 525)
                ax2.plot(df.index, df["mean"], label=g.lbl)
                ax2.legend()
                ax2.set_title(f"Cell knowledge ratio $a_C$ with change rate {rate} [s]")

    fig.tight_layout()
    fig.savefig(run_map.path("cell_knowledge_ratio.pdf"))
    fig2.savefig(run_map.path("cell_knowledge_ratio_zoom.pdf"))
    print("break")


if __name__ == "__main__":

    output_dir = "/mnt/data1tb/results/_density_map/04_rate_output/"
    run_map = RunMap.load_or_create(get_run_map_single_run, output_dir)
    get_msce_err(run_map)
    # save_msce_interval_info(run_map)
    # create_cell_occupation_ratio(run_map)
    # create_cell_knowledge_ratio(run_map)
    print("main done")
