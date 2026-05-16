# # Модель M/M/c
#
# В этом сценарии выполняется дискретно-событийное моделирование очереди M/M/c и
# сравнение с аналитическими характеристиками стационарного режима.

using DrWatson
@quickactivate "SimulationModelingLab07"

include(srcdir("SimulationModelingLab07.jl"))
using .SimulationModelingLab07

# Параметры базовой модели совпадают с заданием: `lambda = 0.9`,
# `mu = 0.5`, `c = 2`.

customers, trace, summary, sweep = save_mmc_outputs(projectdir())

println(summary)
println(first(sweep, 8))
