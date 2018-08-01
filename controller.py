import os,time,sys
from Node import Node;

NumOfLans = 10
ThreadList =[]
LockList = []
TIME = 100;
HostObj = [None]*10
RouterObj = [None]*10

HostArray =[]; RouterArray =[]; LanArray =[] # This value is filled from Command Line

def writeFile(line,lanid):
	
	filename = "lan"+lanid
	fd = open (filename,"a")
	fd.write(str(line)+"\n")
	fd.close()
	

def readFile(obj):
	OldPosition = obj.pos
	filename = obj.filename

	try:
		FileHandle = open(filename)
	except Exception, e:
		return

	FileHandle.seek(0,os.SEEK_END)
	size = FileHandle.tell()
	FileHandle.seek(OldPosition,os.SEEK_SET)
	CurrentPos =  FileHandle.tell()
	while CurrentPos < size:
		line = FileHandle.readline()
		line = line.strip()
		line_str = line
		line = line.split()
		LanID = line[1]
		writeFile(line_str,LanID) #This function writes the given file in lanX file
		CurrentPos =  FileHandle.tell()
	###### END OF INNER WHILE LOOP
	FileHandle.close()
	obj.pos =CurrentPos
###### END OF OUTER WHILE LOOP


if __name__ == '__main__':

	# Process the command line and create 3 arrays for host, router and lan
	CommandLine = sys.argv
	
	try:
		hostInd = CommandLine.index("host")
		routerInd = CommandLine.index("router")
		lanInd = CommandLine.index("lan")
	except Exception, e:
		print "Invalid Command Line Usage, try  again later"
		sys.exit()


	if (not(hostInd < routerInd < lanInd)):
		print "The order of command line is not maintained, try again later"
		sys.exit()
		
	HostArray = CommandLine[hostInd+1:routerInd]
	RouterArray = CommandLine[routerInd+1:lanInd]
	LanArray = CommandLine[lanInd+1:]

	for i in HostArray:
		obj = Node(i,"hout")
		HostObj[int(i)]=(obj)
	
	for i in RouterArray:
		obj = Node(i,"rout")
		RouterObj[int(i)]=(obj)
	
	t0 = time.time()
	while ((time.time() - t0) < TIME):
		for i in RouterArray:
			readFile(RouterObj[int(i)])

		for i in HostArray:
			readFile(HostObj[int(i)])	
		
		time.sleep(0.3);
	
	print "CONTROLLER  DONE";
