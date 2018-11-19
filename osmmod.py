import urlutil
import argparse
import requests
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET
import xml.sax.saxutils as saxutils

def CreateChangeSet(user, passw, tags, baseurl, verbose=0, exe=1):
	#Create a changeset
	createChangeset = u"<?xml version='1.0' encoding='UTF-8'?>\n" +\
	u"<osm version='0.6' generator='py'>\n" +\
	u"  <changeset>\n"
	for k in tags:
		createChangeset += u'<tag k="{0}" v="{1}"/>\n'.format(saxutils.escape(k), saxutils.escape(tags[k]))
	createChangeset += u"  </changeset>\n" +\
	u"</osm>\n"

	if verbose >= 2:
		print createChangeset

	if exe:
		#response = urlutil.Put(baseurl+"/0.6/changeset/create",createChangeset,userpass)
		r = requests.put(baseurl+"/0.6/changeset/create", data=createChangeset.encode('utf-8'), auth=HTTPBasicAuth(user, passw))

		if verbose >= 1: print r.content
		if len(r.content) == 0:
			return (0,"Error creating changeset")
		cid = int(r.content)
		if r.status_code != 200: 
			print r.content
			return (0,"Error creating changeset")
	else:
		cid = 1001
	return (cid, "Done")

def CloseChangeSet(userpass, cid, baseurl, verbose=0, exe=1):
	#Close the changeset
	if exe:
		response = urlutil.Put(baseurl+"/0.6/changeset/"+str(cid)+"/close","",userpass)
		if verbose >= 1: print response
		if urlutil.HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error closing changeset")

def CreateNode(userpass, cid, baseurl, lat, lon, tags, verbose=0, exe=1):

	xml = "<?xml version='1.0' encoding='UTF-8'?>\n"
	xml += '<osmChange version="0.6" generator="py">\n<create>\n<node id="-1" lat="{0}" lon="{1}" changeset="{2}">\n'.format(lat, lon, cid)
	for k in tags:
		xml += '<tag k="{0}" v="{1}"/>\n'.format(saxutils.scape(k), saxutils.escape(tags[k])).encode('utf-8')
	xml += '</node>\n</create>\n</osmChange>\n'
	if verbose >= 2: print xml
	newId = None
	newVersion = None

	if exe:
		response = urlutil.Post(baseurl+"/0.6/changeset/"+str(cid)+"/upload",xml,userpass)
		if verbose >= 1: print response
		if urlutil.HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return None

		respRoot = ET.fromstring(response[0])
		for obj in respRoot:
			newId = obj.attrib['new_id']
			newVersion = obj.attrib['new_version']

	return int(newId), int(newVersion)

def ModifyNode(userpass, nid, cid, baseurl, lat, lon, tags, existingVersion, verbose=0, exe=1):

	xml = "<?xml version='1.0' encoding='UTF-8'?>\n"
	xml += '<osmChange version="0.6" generator="py">\n<modify>\n<node id="{4}" lat="{0}" lon="{1}" changeset="{2}" version="{3}">\n'.format(lat, lon, cid, existingVersion, nid)
	for k in tags:
		xml += '<tag k="{0}" v="{1}"/>\n'.format(saxutils.escape(k), saxutils.escape(tags[k])).encode('utf-8')
	xml += '</node>\n</modify>\n</osmChange>\n'
	if verbose >= 2: print xml
	newVersion = None

	if exe:
		response = urlutil.Post(baseurl+"/0.6/changeset/"+str(cid)+"/upload",xml,userpass)
		if verbose >= 1: print response
		if urlutil.HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error modifying node")

		respRoot = ET.fromstring(response[0])
		for obj in respRoot:
			newVersion = obj.attrib['new_version']

	return int(newVersion)

def CreateWay(userpass, cid, baseurl, nodeIds, tags, verbose=0, exe=1):

	xml = "<?xml version='1.0' encoding='UTF-8'?>\n"
	xml += '<osmChange version="0.6" generator="py">\n<create>\n<way id="-1" changeset="{0}">\n'.format(cid)
	for nid in nodeIds:
		xml += '<nd ref="{0}"/>\n'.format(nid)
	for k in tags:
		xml += '<tag k="{0}" v="{1}"/>\n'.format(saxutils.escape(k), saxutils.escape(tags[k])).encode('utf-8')
	xml += '</way>\n</create>\n</osmChange>\n'
	if verbose >= 2: print xml
	newId = None
	newVersion = None

	if exe:
		response = urlutil.Post(baseurl+"/0.6/changeset/"+str(cid)+"/upload",xml,userpass)
		if verbose >= 1: print response
		if urlutil.HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return None

		respRoot = ET.fromstring(response[0])
		for obj in respRoot:
			newId = obj.attrib['new_id']
			newVersion = obj.attrib['new_version']

	return int(newId), int(newVersion)

def ModifiedWay(userpass, cid, baseurl, nodeIds, tags, wid, existingVersion, verbose=0, exe=1):

	xml = "<?xml version='1.0' encoding='UTF-8'?>\n"
	xml += '<osmChange version="0.6" generator="py">\n<modify>\n<way id="{0}" changeset="{1}" version="{2}">\n'.format(wid, cid, existingVersion)
	for nid in nodeIds:
		xml += '<nd ref="{0}"/>\n'.format(nid)
	for k in tags:
		xml += '<tag k="{0}" v="{1}"/>\n'.format(saxutils.escape(k), saxutils.escape(tags[k])).encode('utf-8')
	xml += '</way>\n</modify>\n</osmChange>\n'
	if verbose >= 2: print xml
	newId = None
	newVersion = None

	if exe:
		response = urlutil.Post(baseurl+"/0.6/changeset/"+str(cid)+"/upload",xml,userpass)
		if verbose >= 1: print response
		if urlutil.HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return None

		respRoot = ET.fromstring(response[0])
		for obj in respRoot:
			newId = obj.attrib['new_id']
			newVersion = obj.attrib['new_version']

	return int(newId), int(newVersion)

if __name__=="__main__":

	parser = argparse.ArgumentParser(description='Fix broken ways.', add_help=False)

	parser.add_argument('--help', action='store_true', help='Print help message')
	parser.add_argument('--cred', help='Path to credentials file')
	parser.add_argument('--server', help='Server API URL')

	args = parser.parse_args()

	if args.help:
		parser.print_help()
		exit(0)

	#url = "http://api.openstreetmap.org/api"
	#url = "http://fosm.org/api"
	#url = "http://kinatomic/m/microcosm.php"
	url = "https://master.apis.dev.openstreetmap.org"
	if args.server:
		url = args.server

	if not args.cred:
		username = raw_input("Username:")
		password = raw_input("Password:")
	else:
		userFile = open(args.cred,"rt").read()
		userData = userFile.split("\n")
		username = userData[0]
		password = userData[1]

	userpass = username+":"+password

	cid, status = CreateChangeSet(username, password, {'comment':"Api Tests"}, url)
	print "Created changeset", cid
	assert cid > 0

	ret = CreateNode(userpass, cid, url, 51.0, -1.0, {}, 2)
	print ret
	assert ret is not None
	ndId, nvVer = ret

	ret = CreateNode(userpass, cid, url, 51.0, -1.00001, {}, 2)
	print ret
	assert ret is not None
	ndId2, nvVer2 = ret

	wayRet = CreateWay(userpass, cid, url, [ndId, ndId2], {'testk':'val1'})
	print wayRet

	wayRet2 = ModifiedWay(userpass, cid, url, [ndId, ndId2], {'testk':'val2'}, wayRet[0], wayRet[1])
	print wayRet2

	CloseChangeSet(userpass, cid, url)
	print "Closed changeset", cid

