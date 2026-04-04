using DrWatson
@quickactivate "lab_04_agents_SIR"

using Agents
using DataFrames
using Plots
using JLD2

include(srcdir("sir_model.jl"))

params = Dict(
    :Ns => [1000, 1000, 1000],
    :beta_und => [0.5, 0.5, 0.5],
    :beta_det => [0.05, 0.05, 0.05],
    :infection_period => 14,
    :detection_time => 7,
    :death_rate => 0.02,
    :reinfection_probability => 0.1,
    :Is => [0, 0, 1],
    :seed => 42,
    :n_steps => 100,
)

model = initialize_sir(; params...)

times = Int[]
S_vals = Int[]
I_vals = Int[]
R_vals = Int[]
total_vals = Int[]

for step in 1:params[:n_steps]
    Agents.step!(model, 1)
    push!(times, step)
    push!(S_vals, susceptible_count(model))
    push!(I_vals, infected_count(model))
    push!(R_vals, recovered_count(model))
    push!(total_vals, total_count(model))
end

agent_df = DataFrame(time = times, susceptible = S_vals, infected = I_vals, recovered = R_vals)
model_df = DataFrame(time = times, total = total_vals)

plot(
    agent_df.time,
    agent_df.susceptible;
    label = "Susceptible",
    xlabel = "Days",
    ylabel = "Population",
)
plot!(agent_df.time, agent_df.infected; label = "Infected")
plot!(agent_df.time, agent_df.recovered; label = "Recovered")
plot!(agent_df.time, model_df.total; label = "Total", linestyle = :dash)
savefig(plotsdir("sir_basic_dynamics.png"))

@save datadir("sir_basic_agent.jld2") agent_df
@save datadir("sir_basic_model.jld2") model_df
