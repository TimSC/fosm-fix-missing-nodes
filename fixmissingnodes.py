import osm, bz2, urllib2, urlutil, osmmod, os, osmmod, sys, argparse
import xml.etree.ElementTree as ET

def WayIsComplete(way, nodes):
	for nodeId in way[0]:
		if nodeId not in nodes:
			return 0
	return 1

def GetLastKnownAttribs(nodeId, server):
	url = server+"/0.6/node/"+str(nodeId)+"/history"
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

def FixWay(way, nodes, username, password, server):
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
				cidRet = osmmod.CreateChangeSet(userpass, {'comment':"Fix way "+str(wayId)}, server, verbose=2)
				cid = cidRet[0]
				print "Created changeset", cid

			ret = osmmod.CreateNode(userpass, cid, server, lastKnown['lat'], lastKnown['lon'], {}, 2)
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
		osmmod.ModifiedWay(userpass, cid, server, way[0], way[1], wayId, way[2]['version'], verbose=2)
	
	#Close changeset
	if cid != 0:
		osmmod.CloseChangeSet(userpass, cid, server)
		print "Closed changeset", cid

def CheckAndFixWaysParsed(nodes, ways, username, password):

	for wayId in ways:
		if not WayIsComplete(ways[wayId], nodes):
			print wayId,"is incomplete"
		if not WayIsComplete(ways[wayId], nodes):
			FixWay(ways[wayId], nodes, username, password)

def CheckAndFixWay(wayId, username, password, server):

	print "Checking way",wayId
	f = urllib2.urlopen(server+"/0.6/way/"+str(wayId)+"/full")
	try:
		root = ET.fromstring(f.read())
	except ET.ParseError:
		print "Error: Invalid XML"
		return 0
	nodes, ways, relations = osm.ParseOsmToObjs(root)

	CheckAndFixWaysParsed(nodes, ways, username, password)
	return 1

def CheckAndFixRelation(relationId, username, password, server):

	print "Checking relation",relationId
	f = urllib2.urlopen(server+"/0.6/relation/"+str(relationId)+"/full")
	try:
		root = ET.fromstring(f.read())
	except ET.ParseError:
		print "Error: Invalid XML"
		return 0
	nodes, ways, relations = osm.ParseOsmToObjs(root)

	CheckAndFixWaysParsed(nodes, ways, username, password)
	return 1

def CheckFile(fiHandle, username, password, server):
	root = ET.fromstring(fiHandle.read())
	nodes, ways, relations = osm.ParseOsmToObjs(root)

	for wayId in ways:
		way = ways[wayId]

		if WayIsComplete(way, nodes):
			continue

		CheckAndFixWay(int(way[2]['id']), username, password, server)	

def WalkFiles(di, username, password, server):

	for fi in os.listdir(di):
		if os.path.isdir(di+"/"+fi):
			WalkFiles(di+"/"+fi, username, password, server)
		if os.path.isfile(di+"/"+fi):
			fullFiNa = di+"/"+fi
			stub, ext = os.path.splitext(fullFiNa)
			if ext == ".bz2":
				print fullFiNa
				CheckFile(bz2.BZ2File(di+"/"+fi), username, password, server)
			if ext == ".osm":
				print fullFiNa
				CheckFile(open(di+"/"+fi, "rt"), username, password, server)

if __name__=="__main__":

	parser = argparse.ArgumentParser(description='Fix broken ways.', add_help=False)
	parser.add_argument('input', metavar='N', type=str, nargs='*',
		               help='inputs to process')
	parser.add_argument('--help', action='store_true', help='Print help message')
	parser.add_argument('--way', action='store_true', help='Treat input as way ids (default)')
	parser.add_argument('--relation', action='store_true', help='Treat input as relation ids')
	parser.add_argument('--file', action='store_true', help='Treat input as files')
	parser.add_argument('--path', action='store_true', help='Treat input as paths')

	parser.add_argument('--cred', help='Path to credentials file')
	parser.add_argument('--server', help='Server API URL')

	args = parser.parse_args()

	if args.help or len(args.input) == 0:
		parser.print_help()
		exit(0)

	if args.way and (args.file or args.path or args.relation):
		print "Only one input type may be specified"
		exit(0)

	if args.file and (args.way or args.path or args.relation):
		print "Only one input type may be specified"
		exit(0)

	if args.path and (args.way or args.file or args.relation):
		print "Only one input type may be specified"
		exit(0)

	if args.relation and (args.path or args.way or args.file):
		print "Only one input type may be specified"
		exit(0)

	if not args.path and not args.file and not args.relation:
		args.way = True

	server = "http://fosm.org/api"
	if args.server:
		server = args.server

	if not args.cred:
		username = raw_input("Username:")
		password = raw_input("Password:")
	else:
		userFile = open(args.cred,"rt").read()
		userData = userFile.split("\n")
		username = userData[0]
		password = userData[1]

	for inp in args.input:

		if args.file:
			if not os.path.isfile(inp):
				print "File not found:", inp
				continue
			CheckFile(open(inp, "rt"), username, password, server)
		if args.way:
			wayId = int(inp)
			CheckAndFixWay(wayId, username, password, server)

		if args.relation:
			relationId = int(inp)
			CheckAndFixRelation(relationId, username, password, server)

		if args.path:
			WalkFiles(inp, username, password, server)

