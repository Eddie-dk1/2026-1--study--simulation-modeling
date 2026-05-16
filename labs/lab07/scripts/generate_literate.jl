using DrWatson
using Literate

@quickactivate "SimulationModelingLab07"

function main()
    clean_dir = projectdir("generated", "clean")
    md_dir = projectdir("generated", "md")
    notebook_dir = projectdir("generated", "notebooks")
    qmd_dir = projectdir("generated", "qmd")

    mkpath(clean_dir)
    mkpath(md_dir)
    mkpath(notebook_dir)
    mkpath(qmd_dir)

    for file in ["mmc_literate.jl", "ross_literate.jl", "params_literate.jl"]
        source = scriptsdir(file)
        Literate.script(source, clean_dir)
        Literate.markdown(source, md_dir)
        Literate.notebook(source, notebook_dir; execute = false)
        Literate.markdown(source, qmd_dir; flavor = Literate.QuartoFlavor())
    end
end

main()
