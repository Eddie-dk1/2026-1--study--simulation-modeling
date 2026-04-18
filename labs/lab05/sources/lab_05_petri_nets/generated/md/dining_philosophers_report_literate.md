```@meta
EditURL = "../../scripts/dining_philosophers_report_literate.jl"
```

# Final comparative plot

This script reuses the CSV files from the base experiment and focuses on
the `Eat_i` states because they illustrate the difference between the
deadlocking and non-deadlocking models most clearly.

````@example dining_philosophers_report_literate
ENV["GKSwstype"] = "100"

using CSV
using DataFrames
using Plots

include(joinpath(@__DIR__, "..", "src", "Paths.jl"))
using .Paths
````

## Data preparation

The helper function extracts the `Eat_i` columns into a matrix suitable
for direct plotting.

````@example dining_philosophers_report_literate
function eat_matrix(df::DataFrame, n::Int)
    cols = [Symbol("Eat_$i") for i in 1:n]
    return Matrix(df[:, cols]), string.(cols)
end
````

## Plot construction

The upper panel shows the classical network, the lower one the network
with an arbiter.

````@example dining_philosophers_report_literate
function main()
    mkpath(plotsdir())

    df_classic = CSV.read(datadir("dining_classic.csv"), DataFrame)
    df_arbiter = CSV.read(datadir("dining_arbiter.csv"), DataFrame)

    n = 5
    classic_eat, eat_names = eat_matrix(df_classic, n)
    arbiter_eat, _ = eat_matrix(df_arbiter, n)

    p1 = plot(
        df_classic.time,
        classic_eat;
        title = "Classical network: Eat_i",
        xlabel = "time",
        ylabel = "tokens",
        label = permutedims(eat_names),
        linewidth = 2,
    )
    p2 = plot(
        df_arbiter.time,
        arbiter_eat;
        title = "Network with arbiter: Eat_i",
        xlabel = "time",
        ylabel = "tokens",
        label = permutedims(eat_names),
        linewidth = 2,
    )

    figure = plot(p1, p2; layout = (2, 1), size = (1200, 900))
    savefig(figure, plotsdir("final_report.png"))

    println("Final comparative report saved to $(plotsdir("final_report.png"))")
end

main()
````

---

*This page was generated using [Literate.jl](https://github.com/fredrikekre/Literate.jl).*

