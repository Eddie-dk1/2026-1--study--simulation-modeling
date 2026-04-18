```@meta
EditURL = "../../scripts/dining_philosophers_literate.jl"
```

# Base experiment for the dining philosophers Petri net

This script runs the stochastic and deterministic experiments for the
classical network and the network with an arbiter. The generated CSV
files and plots are later reused in the report and the presentation.

````@example dining_philosophers_literate
ENV["GKSwstype"] = "100"

using CSV
using DataFrames
using Plots

include(joinpath(@__DIR__, "..", "src", "Paths.jl"))
include(Paths.srcdir("DiningPhilosophers.jl"))
using .Paths
using .DiningPhilosophers
````

## Helpers

We keep directory creation and summary export in small helper functions
to keep the main scenario compact.

````@example dining_philosophers_literate
function ensure_directories()
    mkpath(datadir())
    mkpath(datadir("previews"))
    mkpath(plotsdir())
end

function save_summary(path, classic_summary, arbiter_summary)
    open(path, "w") do io
        println(io, "network,deadlock,events,final_hungry,final_eat")
        println(
            io,
            "classic,$(classic_summary.deadlock),$(classic_summary.events)," *
            "$(classic_summary.final_hungry),$(classic_summary.final_eat)",
        )
        println(
            io,
            "arbiter,$(arbiter_summary.deadlock),$(arbiter_summary.events)," *
            "$(arbiter_summary.final_hungry),$(arbiter_summary.final_eat)",
        )
    end
end
````

## Main experiment

The classical network should demonstrate deadlock, while the arbiter
network should remain active on the full time interval.

````@example dining_philosophers_literate
function main()
    ensure_directories()
    default(size = (1200, 800), linewidth = 2, legendfontsize = 8)

    n = 5
    tmax = 50.0

    net_classic, u0_classic, _ = build_classical_network(n)
    net_arbiter, u0_arbiter, _ = build_arbiter_network(n)

    df_classic = simulate_stochastic(net_classic, u0_classic, tmax; seed = 123)
    df_arbiter = simulate_stochastic(net_arbiter, u0_arbiter, tmax; seed = 123)
    df_classic_det = simulate_deterministic(
        net_classic,
        u0_classic,
        tmax;
        savepath = datadir("dining_classic_deterministic.csv"),
    )
    df_arbiter_det = simulate_deterministic(
        net_arbiter,
        u0_arbiter,
        tmax;
        savepath = datadir("dining_arbiter_deterministic.csv"),
    )

    CSV.write(datadir("dining_classic.csv"), df_classic)
    CSV.write(datadir("dining_arbiter.csv"), df_arbiter)

    classic_summary = summarize_run(df_classic, net_classic, n)
    arbiter_summary = summarize_run(df_arbiter, net_arbiter, n)

    classic_plot = plot_marking_evolution(
        df_classic,
        n;
        title = "Classical Petri net",
        include_arbiter = false,
    )
    arbiter_plot = plot_marking_evolution(
        df_arbiter,
        n;
        title = "Petri net with arbiter",
        include_arbiter = true,
    )
    classic_det_plot = plot_marking_evolution(
        df_classic_det,
        n;
        title = "Classical deterministic model",
        include_arbiter = false,
    )
    arbiter_det_plot = plot_marking_evolution(
        df_arbiter_det,
        n;
        title = "Deterministic model with arbiter",
        include_arbiter = true,
    )

    savefig(classic_plot, plotsdir("classic_simulation.png"))
    savefig(arbiter_plot, plotsdir("arbiter_simulation.png"))
    savefig(classic_det_plot, plotsdir("classic_deterministic.png"))
    savefig(arbiter_det_plot, plotsdir("arbiter_deterministic.png"))

    save_dataframe_preview(datadir("previews", "dining_classic_preview.txt"), df_classic)
    save_dataframe_preview(datadir("previews", "dining_arbiter_preview.txt"), df_arbiter)
    save_dataframe_preview(
        datadir("previews", "dining_classic_deterministic_preview.txt"),
        df_classic_det,
    )
    save_dataframe_preview(
        datadir("previews", "dining_arbiter_deterministic_preview.txt"),
        df_arbiter_det,
    )
    save_summary(datadir("dining_summary.csv"), classic_summary, arbiter_summary)

    println("Base experiment completed.")
    println("Classic deadlock: $(classic_summary.deadlock)")
    println("Arbiter deadlock: $(arbiter_summary.deadlock)")
end

main()
````

---

*This page was generated using [Literate.jl](https://github.com/fredrikekre/Literate.jl).*

