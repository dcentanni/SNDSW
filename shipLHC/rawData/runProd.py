import os,subprocess,time,multiprocessing
import pwd
import ROOT
ncpus = multiprocessing.cpu_count() - 2

""" input runlist
     for each run in runlist. look for number of partitions
     for each partition, start conversion job.
     check consistency of output file
     copy optional file to EOS
     run as many jobs in parallel as cpus are available
""" 

def delProcesses(pname):
    username = pwd.getpwuid(os.getuid()).pw_name
    callstring = "ps -f -u " + username
    status = subprocess.check_output(callstring,shell=True)
    for x in str(status).split("\\n"):
         if not x.find(pname)<0:
            pid = x.split(' ')[2]
            os.system('kill '+pid)
         
class prodManager():

   def Init(self,options):
     self.Mext = ''  
     if options.FairTask_convRaw: 
        self.Mext = '_CPP'  
     self.options = options
     self.runNrs = []
   def count_python_processes(self,macroName):
      username = pwd.getpwuid(os.getuid()).pw_name
      callstring = "ps -f -u " + username
# only works if screen is wide enough to print full name!
      status = subprocess.check_output(callstring,shell=True)
      n=0
      for x in status.decode().split('\n'):
         if not x.find(macroName)<0 and not x.find('python') <0: n+=1
      return n
   def list_of_runs(self,macroName):
      lpruns = []
      username = pwd.getpwuid(os.getuid()).pw_name
      callstring = "ps -f -u " + username
      status = subprocess.check_output(callstring,shell=True)
      for x in status.decode().split('\n'):
         if not x.find(macroName)<0 and not x.find('python') <0: 
            i = x.find('-r')
            lpruns.append(int(x[i+3:].split(' ')[0]))
      return lpruns

   def getPartitions(self,runList,path):
      partitions = {}
      for r in runList:
          directory = path+"run_"+str(r).zfill(6)
          dirlist  = str( subprocess.check_output("xrdfs "+options.server+" ls "+directory,shell=True) )
          partitions[r] = []
          for x in dirlist.split('\\n'):
             if x.find('.root')<0: continue
             ix = x.rfind('data_')
             if ix<0: continue
             partitions[r].append( int(x[ix+5:ix+9]) )
      return partitions

   def convert(self,runList,path,partitions={}):
      if len(partitions)==0: partitions = self.getPartitions(runList,path)
      for r in partitions:
         runNr   = str(r).zfill(6)
    # find partitions
         for p in partitions[r]:
             self.runSinglePartition(path,runNr,str(p).zfill(4),EOScopy=True,check=True)

   def runDataQuality(self,latest):
      monitorCommand = "python $SNDSW_ROOT/shipLHC/scripts/run_Monitoring.py --server=$EOSSHIP \
                        -b 100000 -p "+pathConv+" -g ../geofile_sndlhc_TI18_V2_12July2022.root --ScifiResUnbiased 1 --batch --sudo "

      dqDataFiles = []
      hList = str( subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls /eos/experiment/sndlhc/www/offline",shell=True) )
      for x in hList.split('\\n'):
          if x.find('root')<0: continue
          run = x.split('/')[-1]
          dqDataFiles.append(int(run[3:9]))
      convDataFiles = self.getFileList(pathConv,latest,minSize=0)
      orderedCDF = list(convDataFiles.keys())
      lpruns = self.list_of_runs('run_Monitoring')
      print(lpruns)
      print(self.runNrs)
      for x in orderedCDF:
          r = x//10000
          if  (r in self.runNrs) or (r in lpruns): continue
          if r in dqDataFiles: continue
          self.runNrs.append(r)
          
      for r in self.runNrs: 
           print('executing DQ for run %i'%(r))
           os.system(monitorCommand + " -r "+str(r)+" &")
           while self.count_python_processes('run_Monitoring')>(ncpus-5) : time.sleep(1800)

   def check4NewFiles(self,latest):
      rawDataFiles = self.getFileList(path,latest,minSize=10E6)
      convDataFiles = self.getFileList(pathConv,latest,minSize=0)
      orderedRDF = list(rawDataFiles.keys())
      orderedCDF = list(convDataFiles.keys())
      orderedRDF.reverse(),orderedCDF.reverse()

      for x in orderedRDF: 
           if x in orderedCDF: continue
           lpruns = self.list_of_runs('convertRawData')
           if x in lpruns: continue
           r = x//10000 
           p = x%10000
           print('executing run %i and partition %i'%(r,p))
           self.runSinglePartition(path,str(r).zfill(6),str(p).zfill(4),EOScopy=True,check=True)

   def runSinglePartition(self,path,r,p,EOScopy=False,check=True):
       while self.count_python_processes('convertRawData')>ncpus or self.count_python_processes('runProd')>ncpus: time.sleep(300)
       try:
           pid = os.fork()
       except OSError:
           print("Could not create a child process")
       if not pid == 0: return    
       inFile = self.options.server+path+'run_'+ r+'/data_'+p+'.root'
       fI = ROOT.TFile.Open(inFile)
       if not fI:
         print('file not found',path,r,p)
         exit()
       if not fI.Get('event'):
         print('file corrupted',path,r,p)
         exit()
       command =   "python $SNDSW_ROOT/shipLHC/rawData/convertRawData.py  -r "+str(int(r))+ " -b 1000 -p "+path+" --server="+self.options.server
       if options.FairTask_convRaw:  command+= " -cpp "
       command += " -P "+str(int(p)) + " >log_"+r+'-'+p    
       print("execute ",command)
       os.system(command)
       if check:
          rc = self.checkFile(path,r,p)
          if rc<0: 
             print('converting failed',r,p,rc)
             exit()
       print('finished converting ',r,p)
       tmp = {int(r):[int(p)]}
       if EOScopy:  self.copy2EOS(path,tmp,self.options.overwrite)

       if pid == 0:  exit("Child process finished")
       

   def checkFile(self,path,r,p):
      print('checkfile',path,r,p)
      inFile = self.options.server+path+'run_'+ r+'/data_'+p+'.root'
      fI = ROOT.TFile.Open(inFile)
      Nraw = fI.event.GetEntries()
      outFile = 'sndsw_raw_'+r+'-'+p+self.Mext+'.root'
      fC = ROOT.TFile(outFile)
      test = fC.Get('rawConv')
      if not test:
          print('Error:',path,r,p,' rawConv not found')
          return -2       
      Nconv = fC.rawConv.GetEntries()
      if Nraw != Nconv: 
          print('Error:',path,r,p,':',Nraw,Nconv)
          return -1
      return 0

   def copy2EOS(self,path,success,overwrite):
     for i in success:
       r = str(i).zfill(6)
       for x in success[i]:
         p = str(x).zfill(4)
         outFile = 'sndsw_raw_'+r+'-'+p+self.Mext+'.root'
         tmp = path.split('raw_data')[1].replace('data/','')
         pathConv = os.environ['EOSSHIP']+"/eos/experiment/sndlhc/convertedData/"+tmp+"run_"+r+"/sndsw_raw-"+p+".root"
         print('copy '+outFile+' to '+tmp+"run_"+r+"/sndsw_raw-"+p+".root")
         command = 'xrdcp'
         if overwrite: command+=' -f '
         os.system(command+outFile+'  '+pathConv)
         os.system('rm '+outFile)

   def check(self,path,partitions):
     success = {}
     for r in partitions:
        success[r] = []
        runNr   = str(r).zfill(6)
        for x in partitions[r]:
           p = str(x).zfill(4)
           rc = checkFile(path,runNr,p)
           if rc==0: success[r].append(x)
     return success

   def getFileList(self,p,latest,minSize=10E6):
      inventory = {}
      dirList = str( subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls "+p,shell=True) )
      for x in dirList.split('\\n'):
          aDir = x[x.rfind('/')+1:]
          if not aDir.find('run')==0:continue
          runNr = int(aDir.split('_')[1])
          if not runNr > latest: continue
          fileList = str( subprocess.check_output("xrdfs "+os.environ['EOSSHIP']+" ls -l "+p+"/"+aDir,shell=True) )
          for z in fileList.split('\\n'):
               k = max(z.find('data_'),z.find('sndsw'))
               if not k>0: continue
               j = z.split(' /eos')[0].rfind(' ')
               size = int(z.split(' /eos')[0][j+1:])
               if size<minSize: continue
               tmp = z.split(' ')
               theDay = tmp[1] 
               theTime = tmp[2]
               fname = z[k:]
               run = int(aDir.split('_')[1])
               if run>900000: continue     # not a physical run
               k = fname.find('.root')
               partition = int(fname[k-4:k])
               d = theDay.split('-')
               t = theTime.split(':')
               gmt = time.mktime( (int(d[0]), int(d[1]), int(d[2]),  int(t[0]), int(t[1]), int(t[2]), 0, 0, 0 ) )
               inventory[run*10000+partition] = [aDir+"/"+fname,gmt]
      return inventory

   def getConvStats(self,runList):
     for run in runList:
       try: 
          f=ROOT.TFile.Open("sndsw_raw_"+str(run).zfill(6)+'.root')
          print(run,':',f.rawConv.GetEntries())
       except:
          print('problem:',run)
         
   def rawStats(self,runList):
      for run in runList:
         runNr   = str(run).zfill(6)
         r = ROOT.TFile.Open(os.environ['EOSSHIP']+path+"/run_"+runNr+"/data.root")
         raw = r.event.GetEntries()
         print(run,':',raw)

   def makeHistos(self,runList):
  # historic, used for H8 testbeam, use always DS tracks to survey US because of larger overlap
     for run in runList:
       command = "$SNDSW_ROOT/shipLHC/scripts/Survey-MufiScifi.py -r "+str(run)+" -p "+pathConv+" -g geofile_sndlhc_H6.root -c Mufi_Efficiency -n -1 -t DS"
       os.system("python "+command+ " &")
       while self.count_python_processes('Survey-MufiScifi')>ncpus:
          time.sleep(200)

   def mips(self):
  # historic, used for H8 testbeam, use always DS tracks to survey US because of larger overlap
     for run in runs:
       command = "Survey-MufiScifi.py -r "+str(run)+" -p "+pathConv+" -g geofile_sndlhc_H6.root -c mips"
       os.system("python "+command+ " &")
       while count_python_processes('Survey-MufiScifi')>multiprocessing.cpu_count()-2:
          time.sleep(200)

if __name__ == '__main__':

# use cases: H6, TI18
    from argparse import ArgumentParser
    parser = ArgumentParser()

    parser.add_argument("-r", "--runNumbers", dest="runNumbers", help="list of run numbers",required=False, type=str,default="")
    parser.add_argument("-P", "--production", dest="prod",       help="H6 / epfl / TI18"   ,required=False,default="TI18")
    parser.add_argument("-c", "--command", dest="command",       help="command", default=None)
    parser.add_argument("-o", "--overwrite", dest="overwrite",   action='store_true', help="overwrite EOS", default=False)
    parser.add_argument("-cpp", "--convRawCPP", action='store_true', dest="FairTask_convRaw", help="convert raw data using ConvRawData FairTask", default=False)
    parser.add_argument("--latest", dest="latest", help="last fully converted run", default=0,type=int)
    parser.add_argument("-A", "--auto", dest="auto", help="run in auto mode checking regularly for new files",default=False,action='store_true')
    parser.add_argument("--server", dest="server", help="xrootd server",default=os.environ["EOSSHIP"])
    parser.add_argument("-g", dest="geofile", help="geometry and alignment",default="geofile_sndlhc_TI18.root")

    options = parser.parse_args()
    M = prodManager()
    M.Init(options)

    runList = []
    if options.prod == "TI18":
       if options.server.find('eospublic')<0:
          path = "/mnt/raid1/data_online/" 
       else:
          path = "/eos/experiment/sndlhc/raw_data/commissioning/TI18/data/"
       pathConv = "/eos/experiment/sndlhc/convertedData/commissioning/TI18/"
       if options.runNumbers=="": 
          runList = [1,6,7,8,16,18,19,20,21,23,24,25,26,27]
          # 6,7,8   14,15,22 corrupted
          # 
    elif options.prod == "H6":
       path     = "/eos/experiment/sndlhc/raw_data/commissioning/TB_H6/data/"
       pathConv = "/eos/experiment/sndlhc/convertedData/commissioning/TB_H6/"
       if options.runNumbers=="": 
           runList = [273,276,283,284,285,286,295,296,290,294,298,301,298,292,23,27,34,35,39,40, 41, 42, 43, 44, 45, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 123, 146, 165, 184] 
    elif options.prod == "epfl":
         path = "/eos/experiment/sndlhc/raw_data/commissioning/scifi_cosmics_epfl/data/"   
         if options.runNumbers=="": 
             runList = [3,8]

    else:
        print("production not known. you are on your own",options.prod)

    if options.auto:
      while 1 > 0:
         M.check4NewFiles(options.latest)
         time.sleep(600)
      exit(0)

    if options.command == "DQ":
      while 1 > 0:
         M.runDataQuality(options.latest)  
         time.sleep(3600)
      exit(0)

    if options.command == "convert":
        for r in options.runNumbers.split(','):
            if r!= '': runList.append(int(r))
        M.convert(runList,path)    
   
    elif options.command:
       tmp = options.command.split(';')
       command = tmp[0]+"("
       for i in range(1,len(tmp)):
          if i<4: command+='"'+tmp[i]+'"'
          else:    command+=tmp[i]
          if i<len(tmp)-1: command+=","
       command+=")"
       print('executing ' + command )
       eval("M."+command)
