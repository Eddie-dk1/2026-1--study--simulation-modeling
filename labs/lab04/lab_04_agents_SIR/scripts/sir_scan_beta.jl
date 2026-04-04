using DrWatson
@quickactivate "lab_04_agents_SIR"

using Agents
using DataFrames
using Plots
using CSV
using Statistics

include(srcdir("sir_model.jl"))

function run_experiment(p)
    beta = p[:beta]
    beta_und = fill(beta, 3)
    beta_det = fill(beta / 10, 3)

    model = initialize_sir(;
        Ns = p[:Ns],
        beta_und = beta_und,
        beta_det = beta_det,
        infection_period = p[:infection_period],
        detection_time = p[:detection_time],
        death_rate = p[:death_rate],
        reinfection_probability = p[:reinfection_probability],
        Is = p[:Is],
        seed = p[:seed],
        n_steps = p[:n_steps],
    )

    infected_fraction(model) = count(a.status == :I for a in allagents(model)) / nagents(model)
    peak_infected = 0.0

    for _ in 1:p[:n_steps]
        agent_ids = collect(allids(model))
        for id in agent_ids
            agent = try
                model[id]
            catch
                nothing
            end
            if agent !== nothing
                sir_agent_step!(agent, model)
            end
        end
        frac = infected_fraction(model)
        if frac > peak_infected
            peak_infected = frac
        end
    end

    final_infected = infected_fraction(model)
    final_recovered = count(a.status == :R for a in allagents(model)) / nagents(model)
    total_deaths = sum(p[:Ns]) - nagents(model)

    return (
        peak = peak_infected,
        final_inf = final_infected,
        final_rec = final_recovered,
        deaths = total_deaths,
    )
end

beta_range = 0.1:0.1:1.0
seeds = [42, 43, 44]
params_list = Dict[]

for b in beta_range
    for s in seeds
        push!(params_list, Dict(
            :beta => b,
            :Ns => [1000, 1000, 1000],
            :infection_period => 14,
            :detection_time => 7,
            :death_rate => 0.02,
            :reinfection_probability => 0.1,
            :Is => [0, 0, 1],
            :seed => s,
            :n_steps => 100,
        ))
    end
end

results = []
for params in params_list
    data = run_experiment(params)
    push!(results, merge(params, Dict(pairs(data))))
end

df = DataFrame(results)
CSV.write(datadir("beta_scan_all.csv"), df)

grouped = combine(
    groupby(df, [:beta]),
    :peak => mean => :mean_peak,
    :final_inf => mean => :mean_final_inf,
    :deaths => mean => :mean_deaths,
)

plot(
    grouped.beta,
    grouped.mean_peak;
    label = "Peak",
    xlabel = "Beta",
    ylabel = "Fraction",
    marker = :circle,
    linewidth = 2,
)
plot!(grouped.beta, grouped.mean_final_inf; label = "Final infected", marker = :square)
plot!(grouped.beta, grouped.mean_deaths ./ 3000; label = "Deaths", marker = :diamond)
savefig(plotsdir("beta_scan.png"))
