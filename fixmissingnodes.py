import osm, bz2, urllib2, urlutil, osmmod, os, osmmod, sys
import xml.etree.ElementTree as ET

def WayIsComplete(way, nodes):
	for nodeId in way[0]:
		if nodeId not in nodes:
			return 0
	return 1

def GetLastKnownAttribs(nodeId):
	url = "http://fosm.org/api/0.6/node/"+str(nodeId)+"/history"
	f = urllib2.urlopen(url)
	dataXml = f.read()
	root = ET.fromstring(dataXml)
	attribData = None
	attribVer = None
	
	for el in root:
		#print el.tag, el.attrib
		if attribVer is None or int(el.attrib['version']) > attribVer:
			attribVer = int(el.attrib['version'])
			attribData = el.attrib

	return attribData

def FixWay(way, nodes, username, password):
	url = "http://fosm.org/api"
	cid = 0
	nodeMapping = {}
	wayId = way[2]['id']

	#Create replacement nodes
	for nodeId in way[0]:
		if nodeId not in nodes:
			print "Get last known position of node",nodeId
			lastKnown = GetLastKnownAttribs(nodeId)
			print lastKnown
			userpass = username+":"+password
			if cid == 0:
				cidRet = osmmod.CreateChangeSet(userpass, {'comment':"Fix way "+str(wayId)}, url, verbose=2)
				cid = cidRet[0]
				print "Created changeset", cid

			ret = osmmod.CreateNode(userpass, cid, url, lastKnown['lat'], lastKnown['lon'], {}, 2)
			print "Replacing node",nodeId,"with",ret

			nodeMapping[nodeId] = ret[0]

	if len(nodeMapping) > 0:

		#Update way with replacements
		filteredNds = []
		for nodeId in way[0]:
			if nodeId in nodeMapping:
				filteredNds.append(nodeMapping[nodeId])
			else:
				filteredNds.append(nodeId)
		way[0] = filteredNds

		#Upload new way
		assert cid != 0
		print "Uploading fixed way"
		osmmod.ModifiedWay(userpass, cid, url, way[0], way[1], wayId, way[2]['version'], verbose=2)
	
	#Close changeset
	if cid != 0:
		osmmod.CloseChangeSet(userpass, cid, url)
		print "Closed changeset", cid

def CheckAndFixWaysParsed(nodes, ways, username, password):

	for wayId in ways:
		if not WayIsComplete(ways[wayId], nodes):
			print wayId,"is incomplete"
		if not WayIsComplete(ways[wayId], nodes):
			FixWay(ways[wayId], nodes, username, password)

def CheckAndFixWay(wayId, username, password):

	print "Checking way",wayId
	f = urllib2.urlopen("http://fosm.org/api/0.6/way/"+str(wayId)+"/full")
	try:
		root = ET.fromstring(f.read())
	except ET.ParseError:
		print "Error: Invalid XML"
		return 0
	nodes, ways, relations = osm.ParseOsmToObjs(root)

	CheckAndFixWaysParsed(nodes, ways, username, password)
	return 1

def CheckFile(fiHandle, username, password):
	root = ET.fromstring(fiHandle.read())
	nodes, ways, relations = osm.ParseOsmToObjs(root)

	for wayId in ways:
		way = ways[wayId]

		if WayIsComplete(way, nodes):
			continue

		CheckAndFixWay(int(way[2]['id']), username, password)	

def WalkFiles(di, username, password):

	#username = "TimSCStreetViewImport" #raw_input("Username:")
	#password = raw_input("Password:")

	for fi in os.listdir(di):
		if os.path.isdir(di+"/"+fi):
			WalkFiles(di+"/"+fi, username, password)
		if os.path.isfile(di+"/"+fi):
			print di+"/"+fi

			CheckFile(bz2.BZ2File(di+"/"+fi), username, password)

if __name__=="__main__":
	fixTarget = str(55511190)
	if len(sys.argv) >= 2:
		fixTarget = sys.argv[1]

	if 1:
		username = raw_input("Username:") #"TimSCStreetViewImport"
		password = raw_input("Password:")
	else:
		userFile = open("/home/tim/Desktop/user.txt","rt").read()
		userData = userFile.split("\n")
		username = userData[0]
		password = userData[1]

	#CheckAndFixWay(33266879, username, password)
	
	#WalkFiles("existing/12", username, password)
	
	if os.path.isfile(fixTarget):
		CheckFile(open(fixTarget), username, password)
	else:
		wayId = int(fixTarget)
		CheckAndFixWay(wayId, username, password)




