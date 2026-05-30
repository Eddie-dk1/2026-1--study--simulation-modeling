using DrWatson
@quickactivate "lab8"

using Literate

mkpath(scriptsdir())
mkpath(projectdir("notebooks"))
mkpath(projectdir("docs"))

source = projectdir("literate", "sir_literate.jl")
Literate.script(source, scriptsdir(); name="sir_literate_generated")
Literate.notebook(source, projectdir("notebooks"); name="sir_literate")
Literate.markdown(source, projectdir("docs"); name="sir_literate")
cp(projectdir("docs", "sir_literate.md"), projectdir("docs", "sir_literate.qmd"); force=true)

source_params = projectdir("literate", "sir_parameters.jl")
Literate.script(source_params, scriptsdir(); name="sir_parameters_generated")
Literate.notebook(source_params, projectdir("notebooks"); name="sir_parameters")
Literate.markdown(source_params, projectdir("docs"); name="sir_parameters")
cp(projectdir("docs", "sir_parameters.md"), projectdir("docs", "sir_parameters.qmd"); force=true)
