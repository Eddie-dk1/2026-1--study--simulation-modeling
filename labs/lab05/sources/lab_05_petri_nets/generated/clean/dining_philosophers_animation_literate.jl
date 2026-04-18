ENV["GKSwstype"] = "100"

using CSV
using DataFrames
using Plots

include(joinpath(@__DIR__, "..", "src", "Paths.jl"))
using .Paths

function main()
    mkpath(plotsdir())
    df = CSV.read(datadir("dining_arbiter.csv"), DataFrame)
    names = [name for name in propertynames(df) if name != :time]

    anim = @animate for row in eachrow(df)
        values = [row[name] for name in names]
        bar(
            1:length(values),
            values;
            title = "Petri net marking at t=$(round(row.time; digits = 2))",
            xlabel = "Places",
            ylabel = "Tokens",
            legend = false,
            xticks = (1:length(values), string.(names)),
            xrotation = 60,
            ylim = (0, maximum(values) + 1),
            size = (1400, 800),
        )
    end

    gif(anim, plotsdir("philosophers_simulation.gif"); fps = 2)
    println("Animation saved to $(plotsdir("philosophers_simulation.gif"))")
end

main()

# This file was generated using Literate.jl, https://github.com/fredrikekre/Literate.jl
