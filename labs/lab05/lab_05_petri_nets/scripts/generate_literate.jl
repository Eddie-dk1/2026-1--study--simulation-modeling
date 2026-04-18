using Literate

include(joinpath(@__DIR__, "..", "src", "Paths.jl"))
using .Paths

function main()
    output_root = projectdir("generated")
    clean_dir = joinpath(output_root, "clean")
    md_dir = joinpath(output_root, "md")
    notebook_dir = joinpath(output_root, "notebooks")
    qmd_dir = joinpath(output_root, "qmd")

    mkpath(clean_dir)
    mkpath(md_dir)
    mkpath(notebook_dir)
    mkpath(qmd_dir)

    files = [
        "dining_philosophers_literate.jl",
        "dining_philosophers_animation_literate.jl",
        "dining_philosophers_report_literate.jl",
        "dining_philosophers_params_literate.jl",
    ]

    for file in files
        source = scriptsdir(file)
        Literate.script(source, clean_dir)
        Literate.markdown(source, md_dir)
        Literate.notebook(source, notebook_dir; execute = false)
        Literate.markdown(source, qmd_dir; flavor = Literate.QuartoFlavor())
    end

    println("Generated clean, markdown, notebook and qmd files in $(output_root)")
end

main()
