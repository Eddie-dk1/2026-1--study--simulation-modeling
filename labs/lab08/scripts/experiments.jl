using DrWatson
@quickactivate "lab8"

include(srcdir("sir_model.jl"))

ENV["GKSwstype"] = "100"

using BenchmarkTools
using CSV
using DataFrames
using Random
using StatsPlots

mkpath(plotsdir())
mkpath(datadir("sims"))

tmax = 40.0
u0 = [990, 10, 0]
base_p = [0.05, 10.0, 0.25]
seed = 1234

function save_sir_plot(data, path, title)
    @df data plot(
        :t,
        [:S :I :R],
        labels=["S" "I" "R"],
        xlab="Время",
        ylab="Численность",
        title=title,
        linewidth=2,
    )
    savefig(path)
end

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
    CSV.write(datadir("sims", "sir_beta_$(β).csv"), data)
    save_sir_plot(data, plotsdir("sir_beta_$(β).png"), "SIR: β=$(β)")
    push!(metrics, merge((scenario="beta_$(β)", β=β, c=p[2], γ=p[3]), sir_metrics(data, u0)))
end

for c in [5.0, 10.0, 15.0]
    p = [base_p[1], c, base_p[3]]
    data = run_sir(u0, p, tmax; seed=seed)
    CSV.write(datadir("sims", "sir_c_$(c).csv"), data)
    save_sir_plot(data, plotsdir("sir_c_$(c).png"), "SIR: c=$(c)")
    push!(metrics, merge((scenario="c_$(c)", β=p[1], c=c, γ=p[3]), sir_metrics(data, u0)))
end

for γ in [0.15, 0.25, 0.35]
    p = [base_p[1], base_p[2], γ]
    data = run_sir(u0, p, tmax; seed=seed)
    CSV.write(datadir("sims", "sir_gamma_$(γ).csv"), data)
    save_sir_plot(data, plotsdir("sir_gamma_$(γ).png"), "SIR: γ=$(γ)")
    push!(metrics, merge((scenario="gamma_$(γ)", β=p[1], c=p[2], γ=γ), sir_metrics(data, u0)))
end

CSV.write(datadir("sims", "sensitivity_metrics.csv"), metrics)

stochastic = run_sir(u0, base_p, tmax; seed=seed, deterministic_recovery=false)
deterministic = run_sir(u0, base_p, tmax; seed=seed, deterministic_recovery=true)
CSV.write(datadir("sims", "sir_stochastic_recovery.csv"), stochastic)
CSV.write(datadir("sims", "sir_deterministic_recovery.csv"), deterministic)

plot(stochastic.t, stochastic.I, label="I, stochastic", xlab="Время", ylab="Инфицированные", title="Стохастическое и детерминированное выздоровление", linewidth=2)
plot!(deterministic.t, deterministic.I, label="I, deterministic", linewidth=2)
savefig(plotsdir("sir_recovery_compare.png"))

vaccinated = run_sir_vaccination(u0, base_p, tmax; seed=seed, time=10.0, fraction=0.3)
CSV.write(datadir("sims", "sir_vaccination.csv"), vaccinated)
save_sir_plot(vaccinated, plotsdir("sir_vaccination.png"), "SIR с вакцинацией 30% в t=10")

seir_data = run_seir([990, 0, 10, 0], [0.05, 10.0, 0.5, 0.25], tmax; seed=seed)
CSV.write(datadir("sims", "seir.csv"), seir_data)
@df seir_data plot(:t, [:S :E :I :R], labels=["S" "E" "I" "R"], xlab="Время", ylab="Численность", title="SEIR модель", linewidth=2)
savefig(plotsdir("seir.png"))

demographic_data = demographic_sir(u0, base_p, tmax; seed=seed, μ=0.01, λ=5.0, dt=0.1)
CSV.write(datadir("sims", "sir_demographic.csv"), demographic_data)
save_sir_plot(demographic_data, plotsdir("sir_demographic.png"), "SIR с демографическими событиями")

bench_model = MakeSIRModel([9990, 10, 0], base_p)
activate(bench_model)
bench = @benchmark sir_run($bench_model, $tmax) samples=1 evals=1
open(datadir("sims", "benchmark.txt"), "w") do io
    println(io, bench)
end

println(metrics)
println("Benchmark saved to data/sims/benchmark.txt")
