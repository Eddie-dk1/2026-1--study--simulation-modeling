using DrWatson
@quickactivate "lab_04_agents_SIR"

using Agents
using BlackBoxOptim
using Statistics
using JLD2

include(srcdir("sir_model.jl"))

function cost_multi(x)
    infected_frac(model) = count(a.status == :I for a in allagents(model)) / nagents(model)
    dead_count(model) = 3000 - nagents(model)

    replicates = 5
    peak_vals = Float64[]
    dead_vals = Int[]

    for rep in 1:replicates
        model = initialize_sir(;
            Ns = [1000, 1000, 1000],
            beta_und = fill(x[1], 3),
            beta_det = fill(x[1] / 10, 3),
            infection_period = 14,
            detection_time = round(Int, x[2]),
            death_rate = x[3],
            reinfection_probability = 0.1,
            Is = [0, 0, 1],
            seed = 42 + rep,
            n_steps = 100,
        )

        peak_infected = 0.0
        for _ in 1:100
            Agents.step!(model, 1)
            frac = infected_frac(model)
            if frac > peak_infected
                peak_infected = frac
            end
        end
        push!(peak_vals, peak_infected)
        push!(dead_vals, dead_count(model))
    end

    return (mean(peak_vals), mean(dead_vals) / 3000)
end

result = bboptimize(
    cost_multi;
    Method = :borg_moea,
    FitnessScheme = ParetoFitnessScheme{2}(is_minimizing = true),
    SearchRange = [
        (0.1, 1.0),
        (3.0, 14.0),
        (0.01, 0.1),
    ],
    NumDimensions = 3,
    MaxTime = 120,
    TraceMode = :compact,
)

best = best_candidate(result)
fitness = best_fitness(result)

println("Optimal parameters:")
println("beta_und = $(best[1])")
println("detection_time = $(round(Int, best[2]))")
println("death_rate = $(best[3])")
println("peak = $(fitness[1])")
println("deaths = $(fitness[2])")

@save datadir("optimization_result.jld2") best fitness
