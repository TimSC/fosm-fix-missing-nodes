
from shapely.geometry import Polygon, MultiPolygon
from shapely.geos import PredicateError
from shapely.validation import explain_validity

def WayToPoly(wayId, ways, nodes):
	wayData = ways[wayId]
	wayNodes = wayData[0]
	if wayNodes[0] == wayNodes[-1]:
		tags = wayData[1]
		pts = []
		for nid in wayNodes:
			if int(nid) not in nodes:
				print "Warning: missing node", nid
				continue
			pts.append(nodes[int(nid)][0])

		#Require at least 3 points
		if len(pts) < 3:
			return None

		poly = Polygon(pts)
		if not poly.is_valid:
			print "Warning: polygon is not valid"
			print explain_validity(poly)
			poly = poly.buffer(0)
		return poly
	else:
		#Not implemented
		pass
	return None	

def ParseOsmToObjs(root):
	nodes = {}
	ways = {}
	relations = {}
	for child in root:
		tags = {}
		if child.tag == "node":
			for mem in child:
				if mem.tag == "tag":
					tags[mem.attrib['k']] = mem.attrib['v']

			nodes[int(child.attrib['id'])] = [map(float, [child.attrib['lat'], child.attrib['lon']]), tags, child.attrib]

		if child.tag == "way":
			memNodes = []
			for mem in child:
				#print mem.tag, mem.attrib
				if mem.tag == "nd":
					memNodes.append(int(mem.attrib['ref']))
				if mem.tag == "tag":
					tags[mem.attrib['k']] = mem.attrib['v']

			ways[int(child.attrib['id'])] = [memNodes, tags, child.attrib]

		if child.tag == "relation":
			memObjs = []
			for mem in child:
				#print mem.tag, mem.attrib
				if mem.tag == "member":
					memObjs.append(mem.attrib)
				if mem.tag == "tag":
					tags[mem.attrib['k']] = mem.attrib['v']

			relations[int(child.attrib['id'])] = [memObjs, tags, child.attrib]

		#print child.tag, child.attrib
	#print ways
	return nodes, ways, relations

def OsmToShapely(root):
	nodes, ways, relations = ParseOsmToObjs(root)

	outObjs = []
	for wayId in ways:
		poly = WayToPoly(wayId, ways, nodes)
		if poly is None: continue
		tags = ways[wayId][1]

		#Check tags
		match = False
		if 'landuse' in tags and tags['landuse'] == "forest": match = True
		if 'natural' in tags and tags['natural'] == "wood": match = True
		if not match: continue

		outObjs.append((poly, "way", wayId))

	for objId in relations:
		members = relations[objId][0]
		tags = relations[objId][1]

		#Check tags
		match = False
		if 'type' not in tags: continue
		if tags['type'] != "multipolygon": continue
		if 'landuse' in tags and tags['landuse'] == "forest": match = True
		if 'natural' in tags and tags['natural'] == "wood": match = True
		if not match: continue

		outerPolys = []
		innerPolys = []
		for mem in members:	
			if mem['role'] == "outer":
				ref = int(mem['ref'])
				if ref in ways:
					poly = WayToPoly(ref, ways, nodes)
					if poly is None: continue
					outerPolys.append(poly)
			if mem['role'] == "inner":
				ref = int(mem['ref'])
				if ref in ways:
					poly = WayToPoly(ref, ways, nodes)
					if poly is None: continue
					innerPolys.append(poly)

		outerPolyRings = []
		for outerPoly in outerPolys:

			matchingInteriorPolys = []
			for inPol in innerPolys:
				if outerPoly.contains(inPol):
					if isinstance(inPol, Polygon):
						matchingInteriorPolys.append(inPol.exterior.coords)
					else:
						for ply in inPol.geoms:
							matchingInteriorPolys.append(ply.exterior.coords)

			if isinstance(outerPoly, MultiPolygon):
				for ply in outerPoly.geoms:
					outerPolyRings.append((ply.exterior.coords, matchingInteriorPolys))
			if isinstance(outerPoly, Polygon):
				outerPolyRings.append((outerPoly.exterior.coords, matchingInteriorPolys))

		if len(outerPolyRings) > 0:
			outObjs.append((MultiPolygon(outerPolyRings), "relation", objId))

	return outObjs


