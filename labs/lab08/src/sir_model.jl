using ResumableFunctions
using ConcurrentSim
using Distributions
using DataFrames
using Random

mutable struct SIRPerson
    id::Int64
    status::Symbol
end

mutable struct SIRModel
    sim::ConcurrentSim.Simulation
    β::Float64
    c::Float64
    γ::Float64
    ta::Vector{Float64}
    Sa::Vector{Int64}
    Ia::Vector{Int64}
    Ra::Vector{Int64}
    allIndividuals::Vector{SIRPerson}
    deterministic_recovery::Bool
end

mutable struct SEIRModel
    sim::ConcurrentSim.Simulation
    β::Float64
    c::Float64
    σ::Float64
    γ::Float64
    ta::Vector{Float64}
    Sa::Vector{Int64}
    Ea::Vector{Int64}
    Ia::Vector{Int64}
    Ra::Vector{Int64}
    allIndividuals::Vector{SIRPerson}
end

function increment!(a::Vector{Int64})
    push!(a, last(a) + 1)
end

function decrement!(a::Vector{Int64})
    push!(a, last(a) - 1)
end

function carryover!(a::Vector{Int64})
    push!(a, last(a))
end

function record_sir!(sim::ConcurrentSim.Simulation, m::SIRModel; dS::Int64=0, dI::Int64=0, dR::Int64=0)
    push!(m.ta, ConcurrentSim.now(sim))
    push!(m.Sa, last(m.Sa) + dS)
    push!(m.Ia, last(m.Ia) + dI)
    push!(m.Ra, last(m.Ra) + dR)
end

function infection_update!(sim::ConcurrentSim.Simulation, m::SIRModel)
    record_sir!(sim, m; dS=-1, dI=1)
end

function recovery_update!(sim::ConcurrentSim.Simulation, m::SIRModel)
    record_sir!(sim, m; dI=-1, dR=1)
end

function MakeSIRModel(u0, p; deterministic_recovery::Bool=false)
    (S, I, R) = Int.(u0)
    (β, c, γ) = Float64.(p)
    N = S + I + R
    sim = ConcurrentSim.Simulation()
    allIndividuals = SIRPerson[]

    for i in 1:S
        push!(allIndividuals, SIRPerson(i, :S))
    end
    for i in (S + 1):(S + I)
        push!(allIndividuals, SIRPerson(i, :I))
    end
    for i in (S + I + 1):N
        push!(allIndividuals, SIRPerson(i, :R))
    end

    SIRModel(sim, β, c, γ, [0.0], [S], [I], [R], allIndividuals, deterministic_recovery)
end

function recovery_delay(m::SIRModel)
    m.deterministic_recovery ? 1 / m.γ : rand(Exponential(1 / m.γ))
end

@resumable function live(env::ConcurrentSim.Simulation, individual::SIRPerson, m::SIRModel)
    while individual.status == :S
        @yield timeout(env, rand(Exponential(1 / m.c)))

        alter = individual
        while alter == individual
            index = rand(DiscreteUniform(1, length(m.allIndividuals)))
            alter = m.allIndividuals[index]
        end

        if alter.status == :I && rand(Uniform(0, 1)) < m.β
            individual.status = :I
            infection_update!(env, m)
        end
    end

    if individual.status == :I
        @yield timeout(env, recovery_delay(m))
        individual.status = :R
        recovery_update!(env, m)
    end
end

function activate(m::SIRModel)
    [@process live(m.sim, individual, m) for individual in m.allIndividuals]
end

function sir_run(m::SIRModel, tf::Float64)
    ConcurrentSim.run(m.sim, tf)
end

function out(m::SIRModel)
    DataFrame(t=m.ta, S=m.Sa, I=m.Ia, R=m.Ra)
end

function run_sir(u0, p, tmax; seed::Int64=1234, deterministic_recovery::Bool=false)
    Random.seed!(seed)
    m = MakeSIRModel(u0, p; deterministic_recovery=deterministic_recovery)
    activate(m)
    sir_run(m, Float64(tmax))
    out(m)
end

function sir_metrics(data::DataFrame, u0)
    peak_i, peak_idx = findmax(data.I)
    total = sum(Int.(u0))
    (
        peak_I = peak_i,
        t_peak = data.t[peak_idx],
        final_R = last(data.R),
        final_R_share = last(data.R) / total,
        events = nrow(data) - 1,
    )
end

function assert_sir_invariants(data::DataFrame, u0)
    total = sum(Int.(u0))
    @assert all(data.S .>= 0)
    @assert all(data.I .>= 0)
    @assert all(data.R .>= 0)
    @assert all(diff(data.t) .>= 0)
    @assert all(data.S .+ data.I .+ data.R .== total)
    true
end

function record_seir!(sim::ConcurrentSim.Simulation, m::SEIRModel; dS::Int64=0, dE::Int64=0, dI::Int64=0, dR::Int64=0)
    push!(m.ta, ConcurrentSim.now(sim))
    push!(m.Sa, last(m.Sa) + dS)
    push!(m.Ea, last(m.Ea) + dE)
    push!(m.Ia, last(m.Ia) + dI)
    push!(m.Ra, last(m.Ra) + dR)
end

function MakeSEIRModel(u0, p)
    (S, E, I, R) = Int.(u0)
    (β, c, σ, γ) = Float64.(p)
    N = S + E + I + R
    sim = ConcurrentSim.Simulation()
    allIndividuals = SIRPerson[]

    for i in 1:S
        push!(allIndividuals, SIRPerson(i, :S))
    end
    for i in (S + 1):(S + E)
        push!(allIndividuals, SIRPerson(i, :E))
    end
    for i in (S + E + 1):(S + E + I)
        push!(allIndividuals, SIRPerson(i, :I))
    end
    for i in (S + E + I + 1):N
        push!(allIndividuals, SIRPerson(i, :R))
    end

    SEIRModel(sim, β, c, σ, γ, [0.0], [S], [E], [I], [R], allIndividuals)
end

@resumable function live_seir(env::ConcurrentSim.Simulation, individual::SIRPerson, m::SEIRModel)
    while individual.status == :S
        @yield timeout(env, rand(Exponential(1 / m.c)))

        alter = individual
        while alter == individual
            index = rand(DiscreteUniform(1, length(m.allIndividuals)))
            alter = m.allIndividuals[index]
        end

        if alter.status == :I && rand(Uniform(0, 1)) < m.β
            individual.status = :E
            record_seir!(env, m; dS=-1, dE=1)
        end
    end

    if individual.status == :E
        @yield timeout(env, rand(Exponential(1 / m.σ)))
        individual.status = :I
        record_seir!(env, m; dE=-1, dI=1)
    end

    if individual.status == :I
        @yield timeout(env, rand(Exponential(1 / m.γ)))
        individual.status = :R
        record_seir!(env, m; dI=-1, dR=1)
    end
end

function activate(m::SEIRModel)
    [@process live_seir(m.sim, individual, m) for individual in m.allIndividuals]
end

function seir_run(m::SEIRModel, tf::Float64)
    ConcurrentSim.run(m.sim, tf)
end

function out(m::SEIRModel)
    DataFrame(t=m.ta, S=m.Sa, E=m.Ea, I=m.Ia, R=m.Ra)
end

function run_seir(u0, p, tmax; seed::Int64=1234)
    Random.seed!(seed)
    m = MakeSEIRModel(u0, p)
    activate(m)
    seir_run(m, Float64(tmax))
    out(m)
end

@resumable function vaccinate(env::ConcurrentSim.Simulation, m::SIRModel, time::Float64, fraction::Float64)
    @yield timeout(env, time)
    candidates = [person for person in m.allIndividuals if person.status == :S]
    n = clamp(floor(Int, fraction * length(candidates)), 0, length(candidates))
    for person in candidates[1:n]
        person.status = :R
    end
    if n > 0
        record_sir!(env, m; dS=-n, dR=n)
    end
end

function run_sir_vaccination(u0, p, tmax; seed::Int64=1234, time::Float64=10.0, fraction::Float64=0.3)
    Random.seed!(seed)
    m = MakeSIRModel(u0, p)
    activate(m)
    @process vaccinate(m.sim, m, time, fraction)
    sir_run(m, Float64(tmax))
    out(m)
end

function demographic_sir(u0, p, tmax; seed::Int64=1234, μ::Float64=0.01, λ::Float64=5.0, dt::Float64=0.1)
    Random.seed!(seed)
    β, c, γ = Float64.(p)
    S, I, R = Int.(u0)
    t = Float64[0.0]
    Sa = Int64[S]
    Ia = Int64[I]
    Ra = Int64[R]

    steps = floor(Int, tmax / dt)
    for k in 1:steps
        n = max(S + I + R, 1)
        infections = rand(Binomial(S, clamp(β * c * I / n * dt, 0.0, 1.0)))
        recoveries = rand(Binomial(I, clamp(γ * dt, 0.0, 1.0)))
        deaths_s = rand(Binomial(S, clamp(μ * dt, 0.0, 1.0)))
        deaths_i = rand(Binomial(I, clamp(μ * dt, 0.0, 1.0)))
        deaths_r = rand(Binomial(R, clamp(μ * dt, 0.0, 1.0)))
        births = rand(Poisson(max(λ * dt, 0.0)))

        S = S - infections - deaths_s + births
        I = I + infections - recoveries - deaths_i
        R = R + recoveries - deaths_r

        push!(t, k * dt)
        push!(Sa, S)
        push!(Ia, I)
        push!(Ra, R)
    end

    DataFrame(t=t, S=Sa, I=Ia, R=Ra)
end
