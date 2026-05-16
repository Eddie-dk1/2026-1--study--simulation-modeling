```@meta
EditURL = "../../scripts/ross_literate.jl"
```

# Модель Росса

Модель описывает конечную популяцию машин, резерв, очередь ремонта и один или
несколько ремонтников. Падение происходит при отказе машины в момент, когда
резерв отсутствует.

````@example ross_literate
using DrWatson
@quickactivate "SimulationModelingLab07"

include(srcdir("SimulationModelingLab07.jl"))
using .SimulationModelingLab07
````

Базовые параметры: `N = 10`, `S = 3`, среднее время безотказной работы одной
машины `100` часов, среднее время ремонта `1` час.

````@example ross_literate
trace, base_metrics, runs = save_ross_outputs(projectdir())

println(base_metrics)
println(first(runs, 8))
````

---

*This page was generated using [Literate.jl](https://github.com/fredrikekre/Literate.jl).*

