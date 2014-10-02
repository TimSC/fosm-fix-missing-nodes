
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

