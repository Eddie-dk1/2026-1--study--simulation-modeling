# # Модель Росса
#
# Модель описывает конечную популяцию машин, резерв, очередь ремонта и один или
# несколько ремонтников. Падение происходит при отказе машины в момент, когда
# резерв отсутствует.

using DrWatson
@quickactivate "SimulationModelingLab07"

include(srcdir("SimulationModelingLab07.jl"))
using .SimulationModelingLab07

# Базовые параметры: `N = 10`, `S = 3`, среднее время безотказной работы одной
# машины `100` часов, среднее время ремонта `1` час.

trace, base_metrics, runs = save_ross_outputs(projectdir())

println(base_metrics)
println(first(runs, 8))
