using DrWatson
@quickactivate "lab8"

include(srcdir("sir_model.jl"))

ENV["GKSwstype"] = "100"

using CSV
using DataFrames
using Random
using StatsPlots

tmax = 40.0
u0 = [990, 10, 0]
p = [0.05, 10.0, 0.25]
seed = 1234

Random.seed!(seed)
model = MakeSIRModel(u0, p)
activate(model)
sir_run(model, tmax)
data = out(model)
assert_sir_invariants(data, u0)

mkpath(plotsdir())
mkpath(datadir("sims"))
CSV.write(datadir("sims", "sir_literate_base.csv"), data)

@df data plot(
    :t,
    [:S :I :R],
    labels=["S" "I" "R"],
    xlab="Время",
    ylab="Численность",
    title="Дискретно-событийная SIR модель",
    linewidth=2,
)
savefig(plotsdir("sir_literate_base.png"))

DataFrame([merge((scenario="literate_base",), sir_metrics(data, u0))])

# This file was generated using Literate.jl, https://github.com/fredrikekre/Literate.jl
