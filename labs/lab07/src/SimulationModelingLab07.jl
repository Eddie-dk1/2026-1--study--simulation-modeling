module SimulationModelingLab07

using CSV
using DataFrames
using Distributions
using StableRNGs

export ensure_directories,
       mmc_analytics,
       simulate_mmc,
       mmc_event_trace,
       mmc_summary,
       save_mmc_outputs,
       ross_expected_crash_time,
       simulate_ross,
       simulate_ross_many,
       save_ross_outputs,
       save_parameter_outputs

const DEFAULT_DIRS = [
    "data",
    "plots",
    "generated",
    joinpath("generated", "clean"),
    joinpath("generated", "md"),
    joinpath("generated", "notebooks"),
    joinpath("generated", "qmd"),
    "report",
    "presentation",
    "deliverables",
]

avg(x) = length(x) == 0 ? 0.0 : sum(x) / length(x)

function ensure_directories(root::AbstractString = pwd())
    for dir in DEFAULT_DIRS
        mkpath(joinpath(root, dir))
    end
    return root
end

function mmc_analytics(lambda::Real, mu::Real, c::Integer)
    lambda > 0 || throw(ArgumentError("lambda must be positive"))
    mu > 0 || throw(ArgumentError("mu must be positive"))
    c >= 1 || throw(ArgumentError("c must be at least 1"))

    rho = lambda / (c * mu)
    rho < 1 || throw(ArgumentError("stationary M/M/c requires rho < 1"))

    offered = lambda / mu
    sum_part = sum(offered^n / factorial(big(n)) for n in 0:(c - 1))
    tail_part = offered^c / (factorial(big(c)) * (1 - rho))
    p0 = Float64(inv(sum_part + tail_part))
    p_wait = Float64(tail_part) * p0
    lq = rho * p_wait / (1 - rho)
    wq = lq / lambda
    w = wq + 1 / mu
    l = lambda * w

    return (
        lambda = Float64(lambda),
        mu = Float64(mu),
        c = Int(c),
        rho = Float64(rho),
        p0 = p0,
        p_wait = p_wait,
        lq = lq,
        wq = wq,
        w = w,
        l = l,
    )
end

function simulate_mmc(; lambda::Real = 0.9,
                      mu::Real = 0.5,
                      c::Integer = 2,
                      num_customers::Integer = 10_000,
                      seed::Integer = 123)
    rng = StableRNG(seed)
    arrival_dist = Exponential(1 / lambda)
    service_dist = Exponential(1 / mu)
    next_free = zeros(Float64, c)
    arrival_time = 0.0
    rows = NamedTuple[]

    for id in 1:num_customers
        arrival_time += rand(rng, arrival_dist)
        server = argmin(next_free)
        service_start = max(arrival_time, next_free[server])
        service_time = rand(rng, service_dist)
        departure_time = service_start + service_time
        next_free[server] = departure_time
        push!(rows, (
            customer = id,
            server = server,
            arrival_time = arrival_time,
            service_start = service_start,
            departure_time = departure_time,
            service_time = service_time,
            queue_wait = service_start - arrival_time,
            system_time = departure_time - arrival_time,
        ))
    end

    return DataFrame(rows)
end

function mmc_event_trace(customers::DataFrame)
    events = NamedTuple[]
    for row in eachrow(customers)
        queued = row.service_start > row.arrival_time + 1e-10
        push!(events, (time = row.arrival_time, priority = 3, d_system = 1, d_queue = queued ? 1 : 0))
        if queued
            push!(events, (time = row.service_start, priority = 2, d_system = 0, d_queue = -1))
        end
        push!(events, (time = row.departure_time, priority = 1, d_system = -1, d_queue = 0))
    end

    sorted = sort(DataFrame(events), [:time, :priority])
    system_size = 0
    queue_length = 0
    rows = NamedTuple[(time = 0.0, system_size = 0, queue_length = 0)]

    for row in eachrow(sorted)
        system_size += row.d_system
        queue_length += row.d_queue
        push!(rows, (
            time = Float64(row.time),
            system_size = system_size,
            queue_length = queue_length,
        ))
    end

    return DataFrame(rows)
end

function time_average(trace::DataFrame, column::Symbol)
    nrow(trace) >= 2 || return 0.0
    area = 0.0
    for i in 1:(nrow(trace) - 1)
        dt = trace.time[i + 1] - trace.time[i]
        area += trace[i, column] * dt
    end
    horizon = trace.time[end] - trace.time[1]
    return horizon > 0 ? area / horizon : 0.0
end

function mmc_summary(customers::DataFrame, trace::DataFrame; lambda::Real, mu::Real, c::Integer)
    analytic = mmc_analytics(lambda, mu, c)
    observed = (
        lambda = Float64(lambda),
        mu = Float64(mu),
        c = Int(c),
        customers = nrow(customers),
        observed_wait_probability = avg(customers.queue_wait .> 1e-10),
        observed_wq = avg(customers.queue_wait),
        observed_w = avg(customers.system_time),
        observed_lq = time_average(trace, :queue_length),
        observed_l = time_average(trace, :system_size),
    )
    return merge(analytic, observed)
end

function save_mmc_outputs(root::AbstractString = pwd())
    ensure_directories(root)
    customers = simulate_mmc()
    trace = mmc_event_trace(customers)
    summary = DataFrame([mmc_summary(customers, trace; lambda = 0.9, mu = 0.5, c = 2)])

    CSV.write(joinpath(root, "data", "mmc_customers.csv"), customers)
    CSV.write(joinpath(root, "data", "mmc_trace.csv"), trace)
    CSV.write(joinpath(root, "data", "mmc_summary.csv"), summary)

    sweep_rows = NamedTuple[]
    for c in 1:4
        for lambda in [0.25, 0.40, 0.70, 0.90, 1.20, 1.50]
            lambda < c * 0.5 || continue
            df = simulate_mmc(lambda = lambda, mu = 0.5, c = c, num_customers = 4_000, seed = 1000 + 100c + round(Int, 100lambda))
            tr = mmc_event_trace(df)
            push!(sweep_rows, mmc_summary(df, tr; lambda = lambda, mu = 0.5, c = c))
        end
    end
    sweep = DataFrame(sweep_rows)
    CSV.write(joinpath(root, "data", "mmc_sweep.csv"), sweep)
    return customers, trace, summary, sweep
end

function ross_expected_crash_time(; N::Integer = 10,
                                  S::Integer = 3,
                                  repairers::Integer = 1,
                                  failure_mean::Real = 100.0,
                                  repair_mean::Real = 1.0)
    N >= 1 || throw(ArgumentError("N must be positive"))
    S >= 0 || throw(ArgumentError("S must be non-negative"))
    repairers >= 1 || throw(ArgumentError("repairers must be positive"))

    states = collect(N:(N + S))
    m = length(states)
    A = zeros(Float64, m, m)
    b = ones(Float64, m)
    alpha = N / failure_mean

    for (idx, good) in enumerate(states)
        broken = N + S - good
        beta = good < N + S ? min(repairers, broken) / repair_mean : 0.0
        A[idx, idx] = alpha + beta
        if good > N
            A[idx, idx - 1] = -alpha
        end
        if good < N + S
            A[idx, idx + 1] = -beta
        end
    end

    solution = solve_dense(A, b)
    return solution[end]
end

function solve_dense(A::Matrix{Float64}, b::Vector{Float64})
    n = length(b)
    M = copy(A)
    rhs = copy(b)

    for k in 1:(n - 1)
        pivot = M[k, k]
        abs(pivot) > eps(Float64) || throw(ArgumentError("singular analytic system"))
        for i in (k + 1):n
            factor = M[i, k] / pivot
            M[i, k] = 0.0
            for j in (k + 1):n
                M[i, j] -= factor * M[k, j]
            end
            rhs[i] -= factor * rhs[k]
        end
    end

    x = zeros(Float64, n)
    for i in n:-1:1
        acc = rhs[i]
        for j in (i + 1):n
            acc -= M[i, j] * x[j]
        end
        x[i] = acc / M[i, i]
    end
    return x
end

function start_repair!(completion_times::Vector{Float64}, time::Float64, repair_mean::Real, rng)
    push!(completion_times, time + rand(rng, Exponential(repair_mean)))
    return completion_times
end

function simulate_ross(; N::Integer = 10,
                       S::Integer = 3,
                       repairers::Integer = 1,
                       failure_mean::Real = 100.0,
                       repair_mean::Real = 1.0,
                       seed::Integer = 150,
                       max_time::Real = Inf)
    rng = StableRNG(seed)
    time = 0.0
    spares = Int(S)
    queue = 0
    busy = 0
    completion_times = Float64[]
    next_failure = rand(rng, Exponential(failure_mean / N))

    rows = NamedTuple[(time = 0.0, event = "start", spares = spares, repair_queue = queue,
                       busy_repairers = busy, good_machines = N + spares)]
    area_queue = 0.0
    area_busy = 0.0
    area_good = 0.0
    last_time = 0.0
    crashed = false

    while time < max_time
        next_repair = isempty(completion_times) ? Inf : minimum(completion_times)
        event_time = min(next_failure, next_repair, Float64(max_time))
        dt = event_time - last_time
        area_queue += queue * dt
        area_busy += busy * dt
        area_good += (N + spares) * dt
        last_time = event_time
        time = event_time

        if time >= max_time && max_time < Inf && time < min(next_failure, next_repair)
            push!(rows, (time = time, event = "censored", spares = spares, repair_queue = queue,
                         busy_repairers = busy, good_machines = N + spares))
            break
        elseif next_failure <= next_repair
            if spares == 0
                crashed = true
                push!(rows, (time = time, event = "crash", spares = spares, repair_queue = queue,
                             busy_repairers = busy, good_machines = N + spares))
                break
            end

            spares -= 1
            queue += 1
            if busy < repairers
                queue -= 1
                busy += 1
                start_repair!(completion_times, time, repair_mean, rng)
            end
            next_failure = time + rand(rng, Exponential(failure_mean / N))
            push!(rows, (time = time, event = "failure", spares = spares, repair_queue = queue,
                         busy_repairers = busy, good_machines = N + spares))
        else
            idx = argmin(completion_times)
            deleteat!(completion_times, idx)
            busy -= 1
            spares += 1
            if queue > 0
                queue -= 1
                busy += 1
                start_repair!(completion_times, time, repair_mean, rng)
            end
            push!(rows, (time = time, event = "repair", spares = spares, repair_queue = queue,
                         busy_repairers = busy, good_machines = N + spares))
        end
    end

    horizon = max(time, eps(Float64))
    metrics = (
        N = Int(N),
        S = Int(S),
        repairers = Int(repairers),
        seed = Int(seed),
        crash_time = Float64(time),
        crashed = crashed,
        repairer_utilization = area_busy / (repairers * horizon),
        average_repair_queue = area_queue / horizon,
        average_good_machines = area_good / horizon,
        analytic_crash_time = ross_expected_crash_time(N = N, S = S, repairers = repairers,
                                                       failure_mean = failure_mean,
                                                       repair_mean = repair_mean),
    )
    return DataFrame(rows), metrics
end

function simulate_ross_many(; N::Integer = 10,
                            S::Integer = 3,
                            repairers::Integer = 1,
                            runs::Integer = 100,
                            first_seed::Integer = 150,
                            max_time::Real = Inf)
    rows = NamedTuple[]
    for offset in 0:(runs - 1)
        _, metrics = simulate_ross(N = N, S = S, repairers = repairers,
                                   seed = first_seed + offset, max_time = max_time)
        push!(rows, metrics)
    end
    return DataFrame(rows)
end

function aggregate_ross(df::DataFrame)
    return combine(groupby(df, [:N, :S, :repairers]),
        :crash_time => avg => :mean_crash_time,
        :crashed => avg => :crash_share,
        :repairer_utilization => avg => :mean_repairer_utilization,
        :average_repair_queue => avg => :mean_repair_queue,
        :average_good_machines => avg => :mean_good_machines,
        :analytic_crash_time => first => :analytic_crash_time,
    )
end

function save_ross_outputs(root::AbstractString = pwd())
    ensure_directories(root)
    trace, metrics = simulate_ross(N = 10, S = 3, repairers = 1, seed = 150)
    CSV.write(joinpath(root, "data", "ross_trace.csv"), trace)
    CSV.write(joinpath(root, "data", "ross_base_metrics.csv"), DataFrame([metrics]))

    runs = simulate_ross_many(N = 10, S = 3, repairers = 1, runs = 80, first_seed = 200)
    CSV.write(joinpath(root, "data", "ross_runs.csv"), runs)
    CSV.write(joinpath(root, "data", "ross_runs_summary.csv"), aggregate_ross(runs))
    return trace, DataFrame([metrics]), runs
end

function save_parameter_outputs(root::AbstractString = pwd())
    ensure_directories(root)

    rows = NamedTuple[]
    for N in [8, 10, 12, 14, 16]
        for repairers in [1, 2, 3]
            for offset in 0:39
                _, metrics = simulate_ross(N = N, S = 3, repairers = repairers,
                                           seed = 1000 + 100N + 10repairers + offset,
                                           max_time = repairers == 1 ? Inf : 50_000.0)
                push!(rows, metrics)
            end
        end
    end

    ross_params = DataFrame(rows)
    ross_params_summary = aggregate_ross(ross_params)
    CSV.write(joinpath(root, "data", "ross_params.csv"), ross_params)
    CSV.write(joinpath(root, "data", "ross_params_summary.csv"), ross_params_summary)
    return ross_params, ross_params_summary
end

end
