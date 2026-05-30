# # Анализ параметров SIR модели
#
# В этом литературном коде выполняется серия прогонов для разных значений
# параметров β, c и γ. Для каждого прогона сохраняются графики и ключевые
# метрики: пик числа инфицированных, время пика и итоговая доля переболевших.

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
base_p = [0.05, 10.0, 0.25]
seed = 1234

mkpath(plotsdir())
mkpath(datadir("sims"))

metrics = DataFrame(
    scenario=String[],
    β=Float64[],
    c=Float64[],
    γ=Float64[],
    peak_I=Int64[],
    t_peak=Float64[],
    final_R=Int64[],
    final_R_share=Float64[],
    events=Int64[],
)

for β in [0.03, 0.05, 0.07]
    p = [β, base_p[2], base_p[3]]
    data = run_sir(u0, p, tmax; seed=seed)
    push!(metrics, merge((scenario="beta_$(β)", β=p[1], c=p[2], γ=p[3]), sir_metrics(data, u0)))
end

for c in [5.0, 10.0, 15.0]
    p = [base_p[1], c, base_p[3]]
    data = run_sir(u0, p, tmax; seed=seed)
    push!(metrics, merge((scenario="c_$(c)", β=p[1], c=p[2], γ=p[3]), sir_metrics(data, u0)))
end

for γ in [0.15, 0.25, 0.35]
    p = [base_p[1], base_p[2], γ]
    data = run_sir(u0, p, tmax; seed=seed)
    push!(metrics, merge((scenario="gamma_$(γ)", β=p[1], c=p[2], γ=p[3]), sir_metrics(data, u0)))
end

CSV.write(datadir("sims", "sir_literate_parameter_metrics.csv"), metrics)
metrics
