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

def CheckAndOpenChangeset(osmMod, cid=[0]):
	if cid[0] == 0:
		cidRet = osmMod.CreateChangeSet({'comment':"Fix missing nodes in way (bot)"})
		cid[0] = cidRet[0]
		print ("Created changeset", cid[0])	

def CloseChangeset(osm, cid):
	#Close changeset
	if cid[0] != 0:
		osmMod.CloseChangeSet(cid[0])
		print ("Closed changeset", cid[0])

def RemoveObjectFromRelation(objType, objId, parentRelationId, osmMod, cid=[0]):

	nodes, ways, relations = osmMod.GetObject('relation', parentRelationId)
	rel = relations[parentRelationId]
	relMemObjs, relTags, relAttribs = rel
	objId = int(objId)
	
	filteredRelMemObjs = []
	for mem in relMemObjs:
		if mem['type'] == objType and int(mem['ref']) == objId:
			continue
		filteredRelMemObjs.append(mem)

	if len(relMemObjs) == len(filteredRelMemObjs):
		return False #No need to make changes.

	CheckAndOpenChangeset(osmMod, cid)

	ret = osmMod.ModifyRelation(cid[0], filteredRelMemObjs, relTags, parentRelationId, int(relAttribs['version']))
	print (ret)

def DeleteObjectAndRemoveFromParents(objType, objId, objVer, osmMod, cid=[0]):
	# Check if invalid way is member of a relation
	parentRels = osmMod.GetObjectRelations(objType, objId)
	if len(parentRels) > 0:
		print ("Invalid {} {} found as part of relation(s) {}".format(objType, objId, parentRels.keys()))
		for relId in parentRels.keys():
			RemoveObjectFromRelation(objType, objId, relId, osmMod, cid)

	CheckAndOpenChangeset(osmMod, cid)
	print ("Deleting invalid {} {}".format(objType, objId))
	osmMod.DeleteObject(cid[0], objType, objId, objVer)

def FixWay(way, nodes, osmMod, cid=[0]):

	nodeMapping = {}
	wayId = int(way[2]['id'])

	if len(way[0]) < 2:
		DeleteObjectAndRemoveFromParents('way', wayId, way[2]['version'], osmMod, cid)
		return

	#Create replacement nodes
	for nodeId in way[0]:
		if nodeId not in nodes:
			print ("Get last known position of node",nodeId)
			lastKnown = GetLastKnownAttribs(nodeId, osmMod)
			print (lastKnown)

			if lastKnown is not None:
				CheckAndOpenChangeset(osmMod, cid)

				ret = osmMod.CreateNode(cid[0], lastKnown['lat'], lastKnown['lon'], {})
				print ("Replacing node",nodeId,"with",ret)

				nodeMapping[nodeId] = ret[0]
			else:
				nodeMapping[nodeId] = None

	wayFixPlanned = False
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
		wayFixPlanned = True

	#Upload new way
	if len(way[0]) >= 2 and wayFixPlanned:
		CheckAndOpenChangeset(osmMod, cid)
		print ("Uploading fixed way")
		osmMod.ModifyWay(cid[0], way[0], way[1], wayId, way[2]['version'])
		return

	if len(way[0]) < 2:
		DeleteObjectAndRemoveFromParents('way', wayId, way[2]['version'], osmMod, cid)
		return

def CheckAndFixWaysParsed(nodes, ways, osmMod, cid=[0]):

	for wayId in ways:
		if not WayIsComplete(ways[wayId], nodes) or len(nodes) < 2:
			print (wayId,"is incomplete or too few nodes")
			FixWay(ways[wayId], nodes, osmMod, cid)

def CheckAndFixWay(wayId, osmMod, cid=[0]):

	print ("Checking way",wayId)

	try:
		nodes, ways, relations = osmMod.GetObject('way', wayId, full=True)
	except osmmod.ApiError as err:
		print (err)
		return False

	CheckAndFixWaysParsed(nodes, ways, osmMod, cid)

	return True

def CheckWayTooFewNodes(wayIds, osmMod, cid=[0]):

	nodes, ways, relations = osmMod.GetObjects('way', wayIds)
	print (len(ways))
	for wayId in ways:
		#TODO: check if visible?

		nids = ways[wayId][0]
		if len(nids) < 2:
			CheckAndFixWay(wayId, osmMod, cid)

	return True

def CheckRelationTooFewMembers(relIds, osmMod, cid=[0]):

	nodes, ways, relations = osmMod.GetObjects('relation', relIds)
	print (len(ways))
	for relId in relations:
		#TODO: check if visible?

		mems = relations[relId][0]
		if len(mems) == 0:
			#print ("Fixing relation {} with no members".format(relId))
			CheckAndFixMemsInRelation(relId, osmMod, cid)

	return True

def CheckAndFixMemsInRelation(relationId, osmMod, cid=[0], deleteEmptyRelations=False):

	try:
		nodes, ways, relations = osmMod.GetObject('relation', relationId, full=True)
	except osmmod.ApiError as err:
		print (err)
		return False

	memObjs, tags, attribs = relations[relationId]
	
	filtMemObjs = []
	for memObj in memObjs:
		memRef = int(memObj['ref'])
		memType = memObj['type']
		exists = False
		if memType == 'node':
			exists = memRef in nodes
			print (memObj, exists)
		elif memType == 'way':
			exists = memRef in ways
			print (memObj, exists)
		elif memType == 'relation':
			exists = memRef in relations
			print (memObj, exists)	
		if exists:
			filtMemObjs.append(memObj)

	if len(filtMemObjs) != len(memObjs) or (len(filtMemObjs) == 0 and deleteEmptyRelations):
		print ("Fixing relation", relationId)
		if cid[0] == 0:
			cidRet = osmMod.CreateChangeSet({'comment':"Fix missing members in relation (bot)"})
			cid[0] = cidRet[0]
	
		if len(filtMemObjs) > 0:
			osmMod.ModifyRelation(cid[0], filtMemObjs, tags, relationId, int(attribs['version']))
		elif deleteEmptyRelations:
			DeleteObjectAndRemoveFromParents('relation', relationId, int(attribs['version']), osmMod, cid)

	return 1

def CheckFile(fiHandle, osmMod, cid=[0]):
	root = ET.fromstring(fiHandle.read())
	nodes, ways, relations = osm.ParseOsmToObjs(root)

	for wayId in ways:
		way = ways[wayId]

		if WayIsComplete(way, nodes):
			continue

		CheckAndFixWay(int(way[2]['id']), osmMod, cid)	

def CheckFilename(fina, osmMod, cid=[0]):
	stub, ext = os.path.splitext(fina)
	if ext == ".bz2":
		print (fina)
		CheckFile(bz2.BZ2File(fina), osmMod)
	if ext == ".osm":
		print (fina)
		CheckFile(open(fina, "rt"), osmMod, cid)

def WalkFiles(di, osmMod, cid=[0]):

	for fi in os.listdir(di):
		if os.path.isdir(di+"/"+fi):
			WalkFiles(di+"/"+fi, osmMod, cid)
		if os.path.isfile(di+"/"+fi):
			fullFiNa = di+"/"+fi
			CheckFilename(fullFiNa, osmMod, cid)

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

	cid=[0]
	osmMod = osmmod.OsmMod(server, username, password)

	for inp in args.input:

		if args.file:
			if not os.path.isfile(inp):
				print ("File not found:", inp)
				continue
			CheckFilename(inp, osmMod, cid)
		if args.way:
			wayId = int(inp)
			CheckAndFixWay(wayId, osmMod, cid)

		if args.relation:
			relationId = int(inp)
			CheckAndFixWaysInRelation(relationId, osmMod, cid)

		if args.path:
			WalkFiles(inp, osmMod, cid)

	CloseChangeset(osmMod, cid)

