module Paths

export projectdir, srcdir, scriptsdir, datadir, plotsdir

const PROJECT_ROOT = normpath(joinpath(@__DIR__, ".."))

projectdir(parts...) = joinpath(PROJECT_ROOT, parts...)
srcdir(parts...) = joinpath(PROJECT_ROOT, "src", parts...)
scriptsdir(parts...) = joinpath(PROJECT_ROOT, "scripts", parts...)
datadir(parts...) = joinpath(PROJECT_ROOT, "data", parts...)
plotsdir(parts...) = joinpath(PROJECT_ROOT, "plots", parts...)

end
