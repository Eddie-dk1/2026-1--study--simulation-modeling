module DiningPhilosophers

using CSV
using DataFrames
using OrdinaryDiffEq
using Plots

export PetriNet,
       SimpleRNG,
       build_classical_network,
       build_arbiter_network,
       simulate_deterministic,
       simulate_stochastic,
       detect_deadlock,
       plot_marking_evolution,
       summarize_run,
       save_dataframe_preview

struct PetriNet
    place_names::Vector{String}
    transition_names::Vector{String}
    pre::Matrix{Int}
    post::Matrix{Int}
    incidence::Matrix{Int}
    rates::Vector{Float64}
    n_places::Int
    n_transitions::Int
    has_arbiter::Bool
end

mutable struct SimpleRNG
    state::UInt64
end

function SimpleRNG(seed::Integer)
    seed == 0 && return SimpleRNG(0x9e3779b97f4a7c15)
    return SimpleRNG(UInt64(seed))
end

function rand_uniform!(rng::SimpleRNG)
    rng.state = rng.state * 6364136223846793005 + 1442695040888963407
    value = Float64(rng.state >> 11) / Float64(1 << 53)
    return clamp(value, eps(Float64), 1.0 - eps(Float64))
end

left_fork(i) = i
right_fork(i, n) = i == n ? 1 : i + 1

function build_dining_network(n::Int; with_arbiter::Bool = false)
    n >= 2 || throw(ArgumentError("Number of philosophers must be at least 2"))

    place_names = String[]
    append!(place_names, ["Think_$i" for i in 1:n])
    append!(place_names, ["Hungry_$i" for i in 1:n])
    append!(place_names, ["Eat_$i" for i in 1:n])
    append!(place_names, ["Fork_$i" for i in 1:n])
    if with_arbiter
        push!(place_names, "Arbiter")
    end

    transition_names = String[]
    append!(transition_names, ["TakeLeft_$i" for i in 1:n])
    append!(transition_names, ["TakeRight_$i" for i in 1:n])
    append!(transition_names, ["Release_$i" for i in 1:n])

    n_places = length(place_names)
    n_transitions = length(transition_names)
    pre = zeros(Int, n_places, n_transitions)
    post = zeros(Int, n_places, n_transitions)

    think_idx = Dict(i => i for i in 1:n)
    hungry_idx = Dict(i => n + i for i in 1:n)
    eat_idx = Dict(i => 2n + i for i in 1:n)
    fork_idx = Dict(i => 3n + i for i in 1:n)
    arbiter_idx = with_arbiter ? 4n + 1 : 0

    for i in 1:n
        take_left = i
        take_right = n + i
        release = 2n + i

        left = left_fork(i)
        right = right_fork(i, n)

        pre[think_idx[i], take_left] = 1
        pre[fork_idx[left], take_left] = 1
        if with_arbiter
            pre[arbiter_idx, take_left] = 1
        end
        post[hungry_idx[i], take_left] = 1

        pre[hungry_idx[i], take_right] = 1
        pre[fork_idx[right], take_right] = 1
        post[eat_idx[i], take_right] = 1

        pre[eat_idx[i], release] = 1
        post[think_idx[i], release] = 1
        post[fork_idx[left], release] = 1
        post[fork_idx[right], release] = 1
        if with_arbiter
            post[arbiter_idx, release] = 1
        end
    end

    incidence = post - pre
    rates = vcat(fill(1.0, n), fill(1.25, n), fill(0.85, n))

    u0 = zeros(Int, n_places)
    for i in 1:n
        u0[think_idx[i]] = 1
        u0[fork_idx[i]] = 1
    end
    if with_arbiter
        u0[arbiter_idx] = n - 1
    end

    net = PetriNet(
        place_names,
        transition_names,
        pre,
        post,
        incidence,
        rates,
        n_places,
        n_transitions,
        with_arbiter,
    )
    return net, u0, place_names
end

build_classical_network(n::Int) = build_dining_network(n; with_arbiter = false)
build_arbiter_network(n::Int) = build_dining_network(n; with_arbiter = true)

function transition_propensity(net::PetriNet, marking::AbstractVector{<:Real}, j::Int)
    value = net.rates[j]
    for i in 1:net.n_places
        need = net.pre[i, j]
        if need == 0
            continue
        end
        available = marking[i]
        if available + 1e-9 < need
            return 0.0
        end
        value *= available^need
    end
    return value
end

function is_enabled(net::PetriNet, marking::AbstractVector{<:Real}, j::Int; tol::Float64 = 1e-9)
    for i in 1:net.n_places
        need = net.pre[i, j]
        if need > 0 && marking[i] < need - tol
            return false
        end
    end
    return true
end

function simulate_deterministic(net::PetriNet, u0::AbstractVector{<:Real}, tmax::Real;
                                savepath::Union{Nothing, AbstractString} = nothing)
    function f!(du, u, _, _)
        fill!(du, 0.0)
        for j in 1:net.n_transitions
            propensity = transition_propensity(net, u, j)
            if propensity == 0
                continue
            end
            @inbounds for i in 1:net.n_places
                du[i] += net.incidence[i, j] * propensity
            end
        end
    end

    problem = ODEProblem(f!, Float64.(u0), (0.0, float(tmax)))
    solution = solve(problem, Tsit5(); saveat = 0.25)
    df = DataFrame(time = solution.t)
    for (i, name) in enumerate(net.place_names)
        df[!, Symbol(name)] = [u[i] for u in solution.u]
    end

    if !isnothing(savepath)
        CSV.write(savepath, df)
    end

    return df
end

function snapshot_row(time::Real, names::Vector{String}, marking::AbstractVector{<:Integer})
    row = Dict{Symbol, Any}(:time => float(time))
    for (name, value) in zip(names, marking)
        row[Symbol(name)] = value
    end
    return row
end

function simulate_stochastic(net::PetriNet, u0::Vector{Int}, tmax::Real;
                             seed::Integer = 123,
                             rng::Union{Nothing, SimpleRNG} = nothing,
                             max_events::Int = 10_000)
    rng === nothing && (rng = SimpleRNG(seed))
    time = 0.0
    marking = copy(u0)
    rows = Vector{Dict{Symbol, Any}}()
    push!(rows, snapshot_row(time, net.place_names, marking))

    for _ in 1:max_events
        propensities = zeros(Float64, net.n_transitions)
        total = 0.0
        for j in 1:net.n_transitions
            propensity = transition_propensity(net, marking, j)
            propensities[j] = propensity
            total += propensity
        end

        if total <= 0
            break
        end

        dt = -log(rand_uniform!(rng)) / total
        if time + dt > tmax
            time = float(tmax)
            push!(rows, snapshot_row(time, net.place_names, marking))
            break
        end

        threshold = rand_uniform!(rng) * total
        cumulative = 0.0
        chosen = 1
        for j in 1:net.n_transitions
            cumulative += propensities[j]
            if threshold <= cumulative
                chosen = j
                break
            end
        end

        marking .+= view(net.incidence, :, chosen)
        time += dt
        push!(rows, snapshot_row(time, net.place_names, marking))
    end

    return DataFrame(rows)
end

function detect_deadlock(net::PetriNet, state::AbstractVector{<:Real}; tol::Float64 = 1e-9)
    for j in 1:net.n_transitions
        if is_enabled(net, state, j; tol)
            return false
        end
    end
    return true
end

function detect_deadlock(df::DataFrame, net::PetriNet; tol::Float64 = 1e-9)
    state = [df[end, Symbol(name)] for name in net.place_names]
    return detect_deadlock(net, state; tol)
end

function place_matrix(df::DataFrame, prefix::String, n::Int)
    cols = [Symbol("$(prefix)_$i") for i in 1:n]
    return Matrix(df[:, cols]), string.(cols)
end

function plot_marking_evolution(df::DataFrame, n::Int;
                                title::AbstractString = "Dining philosophers",
                                include_arbiter::Bool = false)
    t = df.time
    think_m, think_names = place_matrix(df, "Think", n)
    hungry_m, hungry_names = place_matrix(df, "Hungry", n)
    eat_m, eat_names = place_matrix(df, "Eat", n)
    fork_m, fork_names = place_matrix(df, "Fork", n)

    p1 = plot(t, think_m; title = "Think_i", label = permutedims(think_names), linewidth = 2)
    p2 = plot(t, hungry_m; title = "Hungry_i", label = permutedims(hungry_names), linewidth = 2)
    p3 = plot(t, eat_m; title = "Eat_i", label = permutedims(eat_names), linewidth = 2)
    p4 = plot(t, fork_m; title = "Fork_i", label = permutedims(fork_names), linewidth = 2)

    panels = Any[p1, p2, p3, p4]
    layout = (2, 2)

    if include_arbiter && :Arbiter in propertynames(df)
        arbiter_values = reshape(Vector(df[:, :Arbiter]), :, 1)
        p5 = plot(
            t,
            arbiter_values;
            title = "Arbiter",
            label = ["Arbiter"],
            linewidth = 2,
            color = :black,
        )
        push!(panels, p5)
        layout = (3, 2)
    end

    figure = plot(
        panels...;
        layout,
        size = include_arbiter ? (1200, 900) : (1200, 700),
        xlabel = "time",
        ylabel = "tokens",
        plot_title = title,
    )
    return figure
end

function summarize_run(df::DataFrame, net::PetriNet, n::Int)
    final_hungry = sum(df[end, Symbol("Hungry_$i")] for i in 1:n)
    final_eat = sum(df[end, Symbol("Eat_$i")] for i in 1:n)
    return (
        deadlock = detect_deadlock(df, net),
        events = nrow(df),
        final_hungry = final_hungry,
        final_eat = final_eat,
    )
end

function save_dataframe_preview(path::AbstractString, df::DataFrame; rows::Int = 8)
    open(path, "w") do io
        show(io, "text/plain", first(df, min(rows, nrow(df))))
    end
end

end
