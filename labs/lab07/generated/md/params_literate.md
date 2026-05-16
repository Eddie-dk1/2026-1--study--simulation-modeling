```@meta
EditURL = "../../scripts/params_literate.jl"
```

# Параметрические прогоны

В параметрическом сценарии варьируется число основных машин и число
ремонтников. Для каждого набора параметров вычисляются имитационные и
аналитические характеристики.

````@example params_literate
using DrWatson
@quickactivate "SimulationModelingLab07"

include(srcdir("SimulationModelingLab07.jl"))
using .SimulationModelingLab07

ross_params, ross_params_summary = save_parameter_outputs(projectdir())

println(first(ross_params_summary, 15))
````

---

*This page was generated using [Literate.jl](https://github.com/fredrikekre/Literate.jl).*

