from __future__ import print_function
from __future__ import unicode_literals
import osm, bz2, requests, osmmod, os, sys, argparse
import xml.etree.ElementTree as ET

def WayIsComplete(way, nodes):
	for nodeId in way[0]:
		if nodeId not in nodes:
			return 0
	return 1

def GetLastKnownAttribs(nodeId, osmMod):
	url = osmMod.baseurl+"/0.6/node/"+str(nodeId)+"/history"
	r = requests.get(url)
	root = ET.fromstring(r.content)
	attribData = None
	attribVer = None
	
	for el in root:
		#print el.tag, el.attrib
		if attribVer is None or int(el.attrib['version']) > attribVer:
			attribVer = int(el.attrib['version'])
			attribData = el.attrib

	return attribData

def FixWay(way, nodes, osmMod):
	cid = 0
	nodeMapping = {}
	wayId = way[2]['id']

	#Create replacement nodes
	for nodeId in way[0]:
		if nodeId not in nodes:
			print ("Get last known position of node",nodeId)
			lastKnown = GetLastKnownAttribs(nodeId, osmMod)
			print (lastKnown)

			if cid == 0:
				cidRet = osmMod.CreateChangeSet({'comment':"Fix way "+str(wayId)})
				cid = cidRet[0]
				print ("Created changeset", cid)

			if lastKnown is not None:
				ret = osmMod.CreateNode(cid, lastKnown['lat'], lastKnown['lon'], {})
				print ("Replacing node",nodeId,"with",ret)

				nodeMapping[nodeId] = ret[0]
			else:
				nodeMapping[nodeId] = None

	if len(nodeMapping) > 0:

		#Update way with replacements
		filteredNds = []
		for nodeId in way[0]:
			if nodeId in nodeMapping:
				if nodeMapping[nodeId] is not None:
					filteredNds.append(nodeMapping[nodeId])
			else:
				filteredNds.append(nodeId)
		way[0] = filteredNds

		#Upload new way
		assert cid != 0
		if len(way[0]) >= 2:
			print ("Uploading fixed way")
			osmMod.ModifiedWay(cid, way[0], way[1], wayId, way[2]['version'])
		else:
			# Check if invalid way is member of a relation
			parentRels = osmMod.GetObjectRelations('way', wayId)
			if parentRels == 0:
				print ("Deleting way with insufficient nodes")
				osmMod.DeleteWay(cid, wayId, way[2]['version'])

			else:
				print ("Invalid way {} found as part of relation(s) {}".format(wayId, parentRels.keys()))

	#Close changeset
	if cid != 0:
		osmMod.CloseChangeSet(cid)
		print ("Closed changeset", cid)

def CheckAndFixWaysParsed(nodes, ways, osmMod):

	for wayId in ways:
		if not WayIsComplete(ways[wayId], nodes):
			print (wayId,"is incomplete")
		if not WayIsComplete(ways[wayId], nodes):
			FixWay(ways[wayId], nodes, osmMod)

def CheckAndFixWay(wayId, osmMod):

	print ("Checking way",wayId)

	r = requests.get(osmMod.baseurl+"/0.6/way/"+str(wayId)+"/full")
	if r.status_code != 200:
		if r.status_code == 410:
			return 0
		raise RuntimeError("Failed to get full way")

	try:
		root = ET.fromstring(r.content)
	except ET.ParseError:
		print ("Error: Invalid XML")
		return 0
	nodes, ways, relations = osm.ParseOsmToObjs(root)

	CheckAndFixWaysParsed(nodes, ways, osmMod)
	return 1

def CheckAndFixRelation(relationId, osmMod):

	print ("Checking relation",relationId)
	r = requests.get(osmMod.baseurl+"/0.6/relation/"+str(relationId)+"/full")

	try:
		root = ET.fromstring(f.content)
	except ET.ParseError:
		print ("Error: Invalid XML")
		return 0
	nodes, ways, relations = osm.ParseOsmToObjs(root)

	CheckAndFixWaysParsed(nodes, ways, osmMod)
	return 1

def CheckFile(fiHandle, osmMod):
	root = ET.fromstring(fiHandle.read())
	nodes, ways, relations = osm.ParseOsmToObjs(root)

	for wayId in ways:
		way = ways[wayId]

		if WayIsComplete(way, nodes):
			continue

		CheckAndFixWay(int(way[2]['id']), osmMod)	

def CheckFilename(fina, osmMod):
	stub, ext = os.path.splitext(fina)
	if ext == ".bz2":
		print (fina)
		CheckFile(bz2.BZ2File(fina), osmMod)
	if ext == ".osm":
		print (fina)
		CheckFile(open(fina, "rt"), osmMod)

def WalkFiles(di, osmMod):

	for fi in os.listdir(di):
		if os.path.isdir(di+"/"+fi):
			WalkFiles(di+"/"+fi, osmMod)
		if os.path.isfile(di+"/"+fi):
			fullFiNa = di+"/"+fi
			CheckFilename(fullFiNa, osmMod)

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
		print ("Only one input type may be specified")
		exit(0)

	if args.file and (args.way or args.path or args.relation):
		print ("Only one input type may be specified")
		exit(0)

	if args.path and (args.way or args.file or args.relation):
		print ("Only one input type may be specified")
		exit(0)

	if args.relation and (args.path or args.way or args.file):
		print ("Only one input type may be specified")
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

	osmMod = osmmod.OsmMod(server, username, password)

	for inp in args.input:

		if args.file:
			if not os.path.isfile(inp):
				print ("File not found:", inp)
				continue
			CheckFilename(inp, osmMod)
		if args.way:
			wayId = int(inp)
			CheckAndFixWay(wayId, osmMod)

		if args.relation:
			relationId = int(inp)
			CheckAndFixRelation(relationId, osmMod)

		if args.path:
			WalkFiles(inp, osmMod)

