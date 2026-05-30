using Test
using DrWatson
@quickactivate "lab8"

include(srcdir("sir_model.jl"))

@testset "SIR invariants" begin
    u0 = [90, 10, 0]
    p = [0.05, 4.0, 0.25]
    data = run_sir(u0, p, 10.0; seed=42)
    @test assert_sir_invariants(data, u0)
    @test names(data) == ["t", "S", "I", "R"]
end

@testset "SEIR output" begin
    data = run_seir([90, 0, 10, 0], [0.05, 4.0, 0.5, 0.25], 10.0; seed=42)
    @test names(data) == ["t", "S", "E", "I", "R"]
    @test all(diff(data.t) .>= 0)
    @test all(data.S .>= 0)
    @test all(data.E .>= 0)
    @test all(data.I .>= 0)
    @test all(data.R .>= 0)
end
