using DrWatson
@quickactivate "lab8"

mkpath(projectdir("release"))

files = [
    "report/report.qmd",
    "presentation/presentation.qmd",
    "README.md",
    "Project.toml",
    "Manifest.toml",
]

for file in files
    if isfile(projectdir(file))
        cp(projectdir(file), projectdir("release", basename(file)); force=true)
    end
end

for file in ["report.pdf", "report.docx"]
    src = projectdir("report", "_output", file)
    isfile(src) && cp(src, projectdir("release", file); force=true)
end

for file in ["presentation.pdf", "presentation.html"]
    src = projectdir("presentation", "_output", file)
    isfile(src) && cp(src, projectdir("release", file); force=true)
end

for file in ["sir_literate.html", "sir_literate.pdf", "sir_parameters.html", "sir_parameters.pdf"]
    src = projectdir("docs", "_output", file)
    isfile(src) && cp(src, projectdir("release", file); force=true)
end

println("Release files prepared in release/")
