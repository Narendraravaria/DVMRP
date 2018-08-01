########################## ROUTER PROCESS ####################################
### cmd i/p format: router-id lan-ID lan-ID lan-ID ...
### eg. 	router 0 0 1
###			router 1 1 2 3
### 		router 2 3
### create DV message and send to directly connected lans
### dv format : DV lan-id router-id d0 router0 d1 router1 d2 router2 . . . d9 router9
###             DV 0 0 0 0 0 0 10 None 10 None 10 None 10 None10 None ...10 None 10 None
### Data Message :	data lan-id host-lan-id
### IGMP Message :	receiver lan-id

from Lan import Lan;
import os, time, sys;

MAX = 10;
TIME = 100;
IGMPTIME = 20;

dirct = list();	 # contains direct connected lan
neigTabl = dict();	# key = direct lans ; value = set of router connected on that lan
LanObj = list(); # conatins lan objects
recvTabl = dict(); 	# key = reciever attached lan ; value = hold off time
neigRoutDisTabl = dict();	# key = neighbor router; value = its distance to all lan in network [0 - 9]


def convertToBin(num, len = 10):
	temp = [0]*len;
	for i in range(0,len):
		temp[len -1 - i] = '1' if (num & (1 << i)) else '0';
	return " ".join(temp);

def findBitValue(num, pos):
	return 1 if(num & (1 << pos)) else 0;

###### Not single router on attached Lan using current router as next hop to reach Lan i(source)
###### No receiver on attached Lan 
###### Then attached Lan is leaf and don't send packet comming from Lan i(source)

###### Find parent router and its distance to lan and based on it create childBitMap
### (rid, neigSet, source_lanIndex, index_dirct)
def createChildBitMap(rid, neigSet, lanInd, ind, recFlag = 0):
	global LanObj;
	global neigTabl;
	global neigRoutDisTabl;
	global dirct;

	parentRout = rid;
	parentDist = LanObj[lanInd].dist;
	###### decide who is parent router on direct attached lan(lid) 
	for v in neigSet:		# check distance of each router connected to dirct lan from source lan i
		if (neigRoutDisTabl.get(v)[lanInd] < parentDist):
			parentRout = v;
			parentDist = neigRoutDisTabl.get(v)[lanInd];
		elif (neigRoutDisTabl.get(v)[lanInd] == parentDist and v < parentRout):
			parentRout = v;
			parentDist = neigRoutDisTabl.get(v)[lanInd];

	###### If current router is elected as parent then add current dirctLan as child if packet comes form source lan i
	if (parentRout == rid):
		LanObj[lanInd].childBitMap = LanObj[lanInd].childBitMap | (1 << ind);
		# No router using me to reach lanId and no receiver on attached lan 
		if (len(LanObj[lanInd].isAnyRouterUsingMe[dirct[ind]]) == 0 and not recvTabl.has_key(dirct[ind])):
			LanObj[lanInd].leafBitMap = LanObj[lanInd].leafBitMap | (1 << ind);		
		else:
			LanObj[lanInd].leafBitMap = LanObj[lanInd].leafBitMap & (~(1 << ind));

		if (recFlag == 1):
			LanObj[lanInd].leafBitMap = LanObj[lanInd].leafBitMap & (~(1 << ind));
	else:
		LanObj[lanInd].childBitMap = LanObj[lanInd].childBitMap & (~(1 << ind));
		


###### Note down receiver lan in childBitMap of all lan
### [attached lan, source_lanID, rid]
def recordReceiver(lanid, ind, rid):
	global recvTabl;
	global LanObj;
	recvTabl[lanid] = time.time();			
	###### if lan containing receiver does not have any other router then rid is parent and hence add lan in child bit map of every lan in network
	###### else find parent of that lan
	if (len(neigTabl.get(lanid)) == 0):
		for i in range(0, MAX): 
			LanObj[i].childBitMap = LanObj[i].childBitMap | (1 << ind);
			LanObj[i].leafBitMap = LanObj[i].leafBitMap & (~(1 << ind));
	else:
		neigSet = neigTabl.get(lanid);
		for i in range(0, MAX):
			createChildBitMap(rid, neigSet, i, ind, 1)


###### Remove receiver from table if hold off time is expired
def removeReceiver():
	global recvTabl;
	global LanObj;
	global dirct;

	if (len(recvTabl) == 0):
		return;
	###### key = receiver lan id ; value = time
	for k,v in recvTabl.items():
		if ((time.time() - v) > 20):
			del recvTabl[k];
			ind = dirct.index(k);	# find lan index in direct connected lan list
			# No router using me to reach lan k and no receiver on lan k then make that lan as leaf
			if (len(LanObj[k].isAnyRouterUsingMe[dirct[ind]]) == 0):
				LanObj[i].leafBitMap = LanObj[i].leafBitMap | (1 << ind);	# clear bit

###### child 	leaf
######	1 		  0		(forward packet)
######	1 		  1 	(Do not forward packet)
######	0 		  X 	(Do not forward packet)
### [rout-file, lan-id, host-lan-id, rid]
def writeData(filename,lanid, hostlnid, rid):
	global neigTabl;
	global LanObj;
	global recvTabl;
	global dirct;

	fdRout = open(filename, 'a');
	nextHop = LanObj[hostlnid].nextHop; 

	###### check nextHop router is on the received data lan
	###### Hence forward only if data is coming from nextHop parent lan (i.e limited flooding)
	###### or coming from sender lan
	###### A packet is accepted if it comes from the LAN of its next-hop, regardless of which router sent it.
	if (nextHop in neigTabl.get(lanid) or lanid == hostlnid):	 

		###### send data to only those lan on which router is elected as parent and router or receiver want the data
		###### childBitMap indicates children for particular source lan
		flag = 1;	# '0' indicates don't send NMR, someone whats data
		for k in range(0, len(dirct)):
			c = findBitValue(LanObj[hostlnid].childBitMap, k);
			l = findBitValue(LanObj[hostlnid].leafBitMap, k);
			if (c == 1 and l == 0):
				if(LanObj[hostlnid].NMRRout[dirct[k]] != LanObj[hostlnid].isAnyRouterUsingMe[dirct[k]]):
					val = 1;
				else:
					val = 1 if (recvTabl.has_key(dirct[k])) else 0;
			else:
				val = 0;
			###### if childBit is 1, leafBit is 0 and child lan is not equal to current lan then forward
			if (val == 1 and dirct[k] != lanid):	
				dataMesg = "data"+" "+str(dirct[k])+" "+str(hostlnid);	# Change the lan-id to new lan-id
				fdRout.write(dataMesg + '\n');
				fdRout.flush();
					
			if (c == 1 and l == 0 ):
				if (recvTabl.has_key(dirct[k])):
					flag = 0;
				else:
					if (LanObj[hostlnid].NMRRout[dirct[k]] != LanObj[hostlnid].isAnyRouterUsingMe[dirct[k]]):
						flag = 0;
			
		###### SEND NMR DATA 
		if (flag == 1 and LanObj[hostlnid].NMRFlag == 0):
			writeNMR(fdRout, rid, hostlnid, LanObj[hostlnid].nextHop);
			LanObj[hostlnid].NMRFlag = 1;
	fdRout.close();

###### Remove NMR if timer expired
def removeNMR():
	global LanObj;
	
	for i in range(0, MAX):
		for k,v in LanObj[i].NMRDict.items():
			if ((time.time() - v[0]) > 20):
				del LanObj[i].NMRDict[k];
				LanObj[i].NMRRout[v[1]].discard(k);
				LanObj[i].NMRFlag = 0;


###### Build NMRDict and NMRRout dictionary
###### NMRDict use to look at hold of time
###### NNMRRout is used to decide, NMR received from all children or not
### [rid, attachedLanId, senderRid, hostLanId]
def noteNMR(rid, lanId, senderRid, hostLanId):
	global LanObj;
	# check NMR came from child (check router present in isAnyRouterUsingMe)
	# if NMR came from child then notedown 
	# Also check NMRRout[attachedLan] == isAnyRouerUsingMe[attachedLan] if same and No receiver on the lan then send NMR to parent

	if (senderRid in LanObj[hostLanId].isAnyRouterUsingMe[lanId]):
		LanObj[hostLanId].NMRDict[senderRid] = [time.time(), lanId];
		if (LanObj[hostLanId].NMRRout.has_key(lanId)):
			LanObj[hostLanId].NMRRout[lanId].add(senderRid);
		else:
			s = set();
			s.add(senderRid);
			LanObj[hostLanId].NMRRout[lanId] = s;
		
		if (LanObj[hostLanId].NMRRout[lanId] == LanObj[hostLanId].isAnyRouterUsingMe[lanId] and (not recvTabl.has_key(lanId))):
			# send NMR to parent
			LanObj[hostLanId].NMRFlag = 1;
			fd = open("rout"+str(rid), 'a');
			writeNMR(fd, rid, hostLanId, LanObj[hostLanId].nextHop);
			fd.flush();
			fd.close();


### [fd, rid, source_lan_id, nextHop_to_reach_srclan]
def writeNMR(fd, rid, hostLanId = None, nextHop = None):
	global neigTabl;
	global dirct;
	if (hostLanId != None and nextHop != None):
		for k,v in neigTabl.items():
			if nextHop in v:
				lanId = k;
				NMRMesg = "NMR" + " "+str(lanId) + " "+ str(rid) + " "+ str(hostLanId) + '\n';
				fd.write(NMRMesg);
	else:
		for i in range(0, MAX):
			if (LanObj[i].NMRFlag == 1):
				# find which lan is nextHop lan i.e. on which lan nextHop router is present
				for k,v in neigTabl.items():
					if LanObj[i].nextHop in v:
						lanId = k;
						NMRMesg = "NMR" + " "+str(lanId) + " "+ str(rid) + " "+ str(i) + '\n';
						fd.write(NMRMesg);




### args = [fd, rid]
def writeRoutx(fd, rid):
	global LanObj;

	for j in range(0,len(dirct)):
		DVMesgList = ["DV"];
		DVMesgList.append(str(dirct[j]));
		DVMesgList.append(str(rid));

		rlist = neigTabl.get(dirct[j]);
		for i in range(0,MAX):
			# DVMesgList.append(str(LanObj[i].dist));
			DVMesgList.append(str(10)) if (LanObj[i].nextHop in rlist) else DVMesgList.append(str(LanObj[i].dist));
			DVMesgList.append(str(LanObj[i].nextHop));

		DVMesg = " ".join(DVMesgList);
		# write DV message
		fd.write(DVMesg + '\n');
		fd.flush();
		del DVMesgList;
	

### Three type of Message: 	DV lan-id router-id d0 router0 d1 router1 d2 router2 . . . d9 router9
### 						data lan-id host-lan-id
### 						receive lan-id

### args = [rid, index_in_direct, currLanIndinDirct obj]
def readLanx(rid, ind, obj):
	global neigTabl;
	global LanObj;
	global recvTabl;
	global dirct;

	###### if router attached to lan 3 then filename will be lan3
	filename = "lan"+str(obj.id);
	try:
		FileHandle = open(filename, 'r');
	except Exception, e:
		return;

	FileHandle.seek(0,os.SEEK_END);
	size = FileHandle.tell();
	FileHandle.seek(obj.pos,os.SEEK_SET);
	CurrentPos =  FileHandle.tell();
	
	while CurrentPos < size:
		line = FileHandle.readline();
		line = line.strip();
		line = line.split();
		
		###### Build neighbor table
		# if (int(line[2]) != rid): # message is not from current router
		# 	neigTabl.get(int(line[1])).add(int(line[2]));

		###### DV message and not from same router then process it
		# DV lan-id router-id d0 router0 d1 router1 d2 router2 . . . d9 router9
		if (line[0] == "DV" and int(line[2]) != rid):
			j = 3;
			tempDist = [-1]*MAX;
			for i in range(0,MAX):		
				if (LanObj[i].dist > int(line[j]) + 1):		# current distance is greater, change the distance
					LanObj[i].dist = int(line[j]) + 1;
					LanObj[i].nextHop = int(line[2]);  
				elif (LanObj[i].dist == int(line[j]) + 1 and LanObj[i].nextHop > int(line[2])):# tie breaker
					LanObj[i].nextHop = int(line[2]);

				###### Build Neigbour router distance table, is used to decide children lans
				if (int(line[j]) == 10 and line[j + 1] == str(rid)):
					tempDist[i] = LanObj[i].dist + 1;
					LanObj[i].isAnyRouterUsingMe[dirct[ind]].add(int(line[2]));		# use to build leafBitMap and NMR
				else:
					tempDist[i] = int(line[j]);		
					LanObj[i].isAnyRouterUsingMe[dirct[ind]].discard(int(line[2]));
				j += 2;

			neigRoutDisTabl[int(line[2])] = tempDist; 
			neigTabl.get(int(line[1])).add(int(line[2]));	# router present on attached lan so add in neighbor table

			###### Create ChildBitMap
			neigSet = neigTabl.get(obj.id);
			for i in range(0, MAX):
				createChildBitMap(rid, neigSet, i, ind);

		if (line[0] == "data"):
			###### Forward only if comes from parent(next to reach Ls) on tree
			###### Change the lan-id to all other lan-id attached (except from incoming lan)
			###### copy the updated message to routx file
			writeData("rout"+str(rid),int(line[1]), int(line[2]), rid);

		if (line[0] == "receiver"):
			###### store inforamtion that on lan (filname) we have receiver
			###### If lan already in table then update the hold off time
			recordReceiver(obj.id, ind, rid);
		# NMR lan-id router-id host-lan-id	
		if (line[0] == "NMR"):
			###### NOTE DOWN NMR 
			noteNMR(rid, int(line[1]), int(line[2]),int(line[3]));

		CurrentPos = FileHandle.tell();
		time.sleep(1);
	FileHandle.close();
	obj.pos = CurrentPos;
		

if __name__ == '__main__':
	### cmd i/p format: router router-id lan-ID lan-ID lan-ID ...

	for i in range(2, len(sys.argv)):	###### direct connected lan and neighbor router on those links
		dirct.append(int(sys.argv[i]));
		neigTabl[int(sys.argv[i])] = set();

	###### LanObj -> id = None, dist = 10, nextHop = None, childLan = 0, leafLan = 0
	for i in range(0,MAX):
		useMeDict = dict();
		NMRRtemp = dict();
		for j in dirct:
			useMeDict[j] = set();
			NMRRtemp[j] = set();
		if (i in dirct):
			LanObj.append(Lan(id = i, dist = 0, nextHop = int(sys.argv[1]), isAnyRouterUsingMe= useMeDict, NMRRout = NMRRtemp));
		else:
			LanObj.append(Lan(id = i, dist = MAX, isAnyRouterUsingMe= useMeDict, NMRRout = NMRRtemp));

	filenameRout = "rout"+str(sys.argv[1]);
	fdrout = open(filenameRout, 'a');	# Open routx file

	t0 = time.time();
	while ((time.time() - t0) < TIME):	# Final
		removeReceiver();	###### remove recivers with expired hold off time
		removeNMR();		###### remove entry from NMRdict if hold-off-time > 20 sec
		t20 = time.time();
		while ((time.time() - t20) < IGMPTIME):	# IGMP check
			writeNMR(fdrout, int(sys.argv[1]));	### For NMR Message
			t10 = time.time();
			while ((time.time() - t10) < 10):	# NMR
				writeRoutx(fdrout, int(sys.argv[1]));	### For DV Message
				t5 = time.time();
				while ((time.time() - t5) < 5):	# DV
					for i in range (0,len(dirct)):
						readLanx(int(sys.argv[1]), i, LanObj[dirct[i]]);
					time.sleep(0.5);
	
	fdrout.close();
	
	# dirct.reverse();
	# fd = open("log"+str(sys.argv[1]), 'a');
	# fd.write(str(dirct) + '\n');
	# fd.write("dis "+str(LanObj[0].dist) + '\n');
	# fd.write("nextHop "+str(LanObj[0].nextHop) + '\n');
	# fd.write("child "+str(convertToBin(LanObj[0].childBitMap, len(dirct))) + '\n');
	# fd.write("leaf "+str(convertToBin(LanObj[0].leafBitMap, len(dirct))) + '\n');
	# fd.write(str(LanObj[0].isAnyRouterUsingMe) + '\n');
	# fd.write(str(recvTabl) +'\n');
	# fd.close();
	print "ROUTER",sys.arv[1]," DONE";

