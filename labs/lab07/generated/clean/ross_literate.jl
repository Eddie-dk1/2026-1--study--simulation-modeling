using DrWatson
@quickactivate "SimulationModelingLab07"

include(srcdir("SimulationModelingLab07.jl"))
using .SimulationModelingLab07

trace, base_metrics, runs = save_ross_outputs(projectdir())

println(base_metrics)
println(first(runs, 8))

# This file was generated using Literate.jl, https://github.com/fredrikekre/Literate.jl
