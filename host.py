########################## HOST PROCESS ####################################
# host-id lan-id type time-to-start period
# host 10 2 sender 30 10 &
# Receiver work:send IGMP message in evry 20 sec
#				read lan file and copy data message to hin file
# Sender work:	send data message after every period time
import sys;
import threading,os,time;

TIME = 100;
IGMPTIME = 10;
###### Read attached lan for data lan-id host-lan-id and copy in hin
###### Send (write) IGMP message every 20 sec (to hout) on attached lan 
### [name hostid lanid]
def receiverRecSend(*args):
	OldPosition = 0;
	filenameLan = "lan"+str(args[2]);	# read from this file
	filenamehin = "hin"+str(args[1]);	# write to this file

	igmpMesg = 'receiver'+' '+str(args[2]);	# IGMP Message
	filenamehout = "hout"+str(args[1]);	# Host hout file
	fdHout = open (filenamehout,"a");	# Open hout file in append mode

	t0 = time.time();
	while((time.time() - t0) < (TIME + 20)):
		fdHout.write(str(igmpMesg)+"\n");	# Append IGMP message to hout file
		fdHout.flush();		# flush the buffer assocaited with hout file
		t1 = time.time();
		while ((time.time() - t1) < IGMPTIME):
			try:
				fdLan = open(filenameLan, 'r');
			except Exception, e:
				time.sleep(1);
				continue;
			fdHin = open(filenamehin, 'a');
			fdLan.seek(0,os.SEEK_END);
			size = fdLan.tell();
			fdLan.seek(OldPosition,os.SEEK_SET);
			CurrentPos =  fdLan.tell();
			
			while CurrentPos < size:
				line = fdLan.readline();
				line_str = line.strip();
				line = line.split();
				if (line[0] == 'data'):
					fdHin.write(str(line_str)+"\n");	# write received message to hin
					fdHin.flush();
				CurrentPos = fdLan.tell();
			###### END OF READ WHILE LOOP
			OldPosition = CurrentPos;
			time.sleep(0.5);	# SLEEP ------------------
		###### END OF IGMP WHILE LOOP
	###### END OF OUTER MAIN WHILE LOOP
	fdHout.close();
	fdHin.close();
	fdLan.close();


###### [name hostid lanid period time-to-start]
def sender(*args):
	multiCastMesg = 'data'+' '+str(args[2])+' '+str(args[2]);
	filenamehout = "hout"+str(args[1]);
	fdHout = open (filenamehout,"a");
	t0 = time.time();
	while ((time.time() - t0) < (TIME - args[4])):
		fdHout.write(str(multiCastMesg)+"\n");
		fdHout.flush();
		time.sleep(args[3]);	# Period time SLEEP ------------------
	fdHout.close();

if __name__ == '__main__':
	hostname = 'sender' if (sys.argv[3] == 'sender') else 'receiver';

	if (hostname == 'receiver'):
		receiverRecSend("receiver-" + str(sys.argv[1]), int(sys.argv[1]), int(sys.argv[2]));
	elif(hostname == 'sender'):
		time.sleep(int(sys.argv[4]));	#sleep for time-to-start
		sender("sender-" + str(sys.argv[1]),int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[5]), int(sys.argv[4]));
	print "HOST",sys.argv[1], " DONE";
