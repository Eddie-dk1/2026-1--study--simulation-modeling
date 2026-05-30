using DrWatson
@quickactivate "lab8"

include(srcdir("sir_model.jl"))

ENV["GKSwstype"] = "100"

using CSV
using DataFrames
using Dates
using Random
using StatsPlots

mkpath(plotsdir())
mkpath(datadir("sims"))

tmax = 40.0
u0 = [990, 10, 0]
p = [0.05, 10.0, 0.25]

Random.seed!(1234)
des_model = MakeSIRModel(u0, p)
activate(des_model)
sir_run(des_model, tmax)
data_des = out(des_model)
assert_sir_invariants(data_des, u0)

filename = "sir_$(u0[1])_$(u0[2])_$(p[1])_$(p[2])_$(p[3]).csv"
CSV.write(datadir("sims", filename), data_des)

@df data_des plot(
    :t,
    [:S :I :R],
    labels=["S" "I" "R"],
    xlab="Время",
    ylab="Численность",
    title="Дискретно-событийная SIR модель",
    linewidth=2,
)
savefig(plotsdir("sir_des.png"))

metrics = DataFrame([merge((scenario="base",), sir_metrics(data_des, u0))])
CSV.write(datadir("sims", "sir_base_metrics.csv"), metrics)
println(metrics)
