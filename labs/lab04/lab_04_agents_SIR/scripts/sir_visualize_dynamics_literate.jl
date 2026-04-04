# # Comprehensive Visualization of SIR Experiments
#
# This literate script loads the beta scan results and builds a combined figure
# with peak infected, deaths, and recovered fraction.

using DrWatson
@quickactivate "lab_04_agents_SIR"

using DataFrames
using Plots
using CSV

include(srcdir("sir_model.jl"))

df = CSV.read(datadir("beta_scan_all.csv"), DataFrame)

p1 = plot(df.beta, df.peak; label = "Peak", xlabel = "Beta", ylabel = "Infected fraction")
plot!(p1, df.beta, df.final_inf; label = "Final infected")

p2 = plot(df.beta, df.deaths; xlabel = "Beta", ylabel = "Deaths", label = "Deaths")
p3 = plot(df.beta, df.final_rec; xlabel = "Beta", ylabel = "Recovered fraction", label = "Recovered")

plot(p1, p2, p3; layout = (3, 1), size = (800, 900))
savefig(plotsdir("comprehensive_analysis.png"))
