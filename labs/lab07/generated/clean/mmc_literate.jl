using DrWatson
@quickactivate "SimulationModelingLab07"

include(srcdir("SimulationModelingLab07.jl"))
using .SimulationModelingLab07

customers, trace, summary, sweep = save_mmc_outputs(projectdir())

println(summary)
println(first(sweep, 8))

# This file was generated using Literate.jl, https://github.com/fredrikekre/Literate.jl
