import ROOT
from argparse import ArgumentParser
import os

import SndlhcMuonReco

parser = ArgumentParser()
parser.add_argument("-f", "--inputFile", dest="inputFile", help="single input file", required=True)
parser.add_argument("-o", "--withOutput", dest="withOutput", help="persistent output", action='store_true',default=False)
parser.add_argument("-g", "--geoFile", dest="geoFile", help="geofile", required=True)
parser.add_argument("-n", "--nEvents", dest="nEvents",  type=int, help="number of events to process", default=100000)
parser.add_argument("-i", "--firstEvent",dest="firstEvent",  help="First event of input file to use", required=False,  default=0, type=int)
parser.add_argument("-t", "--tolerance", dest="tolerance",  type=float, help="How far away from Hough line hits assigned to the muon can be. In cm.", default=0.)
parser.add_argument("--use_scifi", dest="use_scifi",  help="Use SciFi hits. [Default]", action='store_true')
parser.add_argument("--no-use_scifi", dest="use_scifi",  help="Do not use SciFi hits.", action='store_false')
parser.set_defaults(use_scifi=True)
parser.add_argument("--use_mufi", dest="use_mufi",  help="Use Muon Filter hits. Muon tracks are required to have three DS Muon Filter planes hit. [Default]", action='store_true')
parser.add_argument("--no-use_mufi", dest="use_mufi",  help="Do not use Muon Filter hits. The triplet condition will be based on SciFi hits.", action='store_false')
parser.set_defaults(use_mufi=True)

options = parser.parse_args()

import SndlhcGeo
geo = SndlhcGeo.GeoInterface(options.geoFile)

lsOfGlobals = ROOT.gROOT.GetListOfGlobals()
lsOfGlobals.Add(geo.modules['Scifi'])
lsOfGlobals.Add(geo.modules['MuFilter'])

x = options.inputFile
filename = x[x.rfind('/')+1:]
outFileName = filename.replace('.root','_muonReco.root')

fullPath = options.inputFile
if options.inputFile.find('/eos')==0:
     fullPath = os.environ['EOSSHIP']+options.inputFile
F = ROOT.TFile.Open(fullPath)

if options.withOutput:
  outFile = ROOT.TFile(outFileName, 'RECREATE')
else:
  outFile = ROOT.TMemFile(outFileName,'CREATE')

run = ROOT.FairRunAna()
print("Initialized FairRunAna")

source = ROOT.FairFileSource(F)
run.SetSource(source)

sink = ROOT.FairRootFileSink(outFile)
run.SetSink(sink)

muon_reco_task = SndlhcMuonReco.MuonReco()
run.AddTask(muon_reco_task)

run.Init()

# The following lines must be *after* run.Init()
muon_reco_task.SetTolerance(options.tolerance)
muon_reco_task.SetUseSciFi(options.use_scifi)
muon_reco_task.SetUseMuFi(options.use_mufi)

run.Run(options.firstEvent, options.firstEvent + options.nEvents)
print("Done running")

