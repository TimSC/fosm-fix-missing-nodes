from __future__ import print_function
from __future__ import unicode_literals
import argparse
import requests
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET
import xml.sax.saxutils as saxutils

class OsmMod(object):

	def __init__(self, baseurl, user, passw):
		self.baseurl = baseurl
		self.user = user
		self.passw = passw
		self.xmlHeaders = {'Content-type': 'text/xml; charset=utf-8'}
		self.verbose = 1
		self.exe = True

	def CreateChangeSet(self, tags):
		#Create a changeset
		createChangeset = u"<?xml version='1.0' encoding='UTF-8'?>\n" +\
		u"<osm version='0.6' generator='py'>\n" +\
		u"  <changeset>\n"
		for k in tags:
			createChangeset += u'<tag k="{0}" v="{1}"/>\n'.format(saxutils.escape(k), saxutils.escape(tags[k]))
		createChangeset += u"  </changeset>\n" +\
		u"</osm>\n"

		if self.verbose >= 2:
			print (createChangeset)

		if self.exe:
			
			r = requests.put(self.baseurl+"/0.6/changeset/create", data=createChangeset.encode('utf-8'), 
				auth=HTTPBasicAuth(self.user, self.passw),
				headers=self.xmlHeaders)

			if r.status_code != 200: 
				print (r.content)
				return (0,"Error creating changeset")
			if self.verbose >= 1: print (r.content)
			if len(r.content) == 0:
				return (0,"Error creating changeset")
			cid = int(r.content)
		else:
			cid = 1001
		return (cid, "Done")

	def CloseChangeSet(self, cid):
		#Close the changeset
		if self.exe:
			r = requests.put(self.baseurl+"/0.6/changeset/"+str(cid)+"/close", data="", 
				auth=HTTPBasicAuth(self.user, self.passw))
			if self.verbose >= 1: print (r.content)
			if r.status_code != 200: return (0,"Error closing changeset")

	def CreateNode(self, cid, lat, lon, tags):

		xml = u"<?xml version='1.0' encoding='UTF-8'?>\n"
		xml += u'<osmChange version="0.6" generator="py">\n<create>\n<node id="-1" lat="{0}" lon="{1}" changeset="{2}">\n'.format(lat, lon, cid)
		for k in tags:
			xml += u'<tag k="{0}" v="{1}"/>\n'.format(saxutils.scape(k), saxutils.escape(tags[k]))
		xml += u'</node>\n</create>\n</osmChange>\n'
		if self.verbose >= 2: print (xml)
		newId = None
		newVersion = None

		if self.exe:
			r = requests.post(self.baseurl+"/0.6/changeset/"+str(cid)+"/upload", data=xml.encode('utf-8'), 
				auth=HTTPBasicAuth(self.user, self.passw),
				headers=self.xmlHeaders)

			if self.verbose >= 1: print (r.content)
			if r.status_code != 200: return None

			respRoot = ET.fromstring(r.content)
			for obj in respRoot:
				newId = obj.attrib['new_id']
				newVersion = obj.attrib['new_version']

		return int(newId), int(newVersion)

	def ModifyNode(self, nid, cid, lat, lon, tags, existingVersion):

		xml = u"<?xml version='1.0' encoding='UTF-8'?>\n"
		xml += u'<osmChange version="0.6" generator="py">\n<modify>\n<node id="{4}" lat="{0}" lon="{1}" changeset="{2}" version="{3}">\n'.format(lat, lon, cid, existingVersion, nid)
		for k in tags:
			xml += u'<tag k="{0}" v="{1}"/>\n'.format(saxutils.escape(k), saxutils.escape(tags[k]))
		xml += u'</node>\n</modify>\n</osmChange>\n'
		if self.verbose >= 2: print (xml)
		newVersion = None

		if self.exe:
			r = requests.post(self.baseurl+"/0.6/changeset/"+str(cid)+"/upload", data=xml.encode('utf-8'), 
				auth=HTTPBasicAuth(self.user, self.passw),
				headers=self.xmlHeaders)

			if self.verbose >= 1: print (r.content)
			if r.status_code != 200: return (0,"Error modifying node")

			respRoot = ET.fromstring(r.content)
			for obj in respRoot:
				newVersion = obj.attrib['new_version']

		return int(newVersion)

	def CreateWay(self, cid, nodeIds, tags):

		xml = u"<?xml version='1.0' encoding='UTF-8'?>\n"
		xml += u'<osmChange version="0.6" generator="py">\n<create>\n<way id="-1" changeset="{0}">\n'.format(cid)
		for nid in nodeIds:
			xml += u'<nd ref="{0}"/>\n'.format(nid)
		for k in tags:
			xml += u'<tag k="{0}" v="{1}"/>\n'.format(saxutils.escape(k), saxutils.escape(tags[k]))
		xml += 'u</way>\n</create>\n</osmChange>\n'
		if self.verbose >= 2: print (xml)
		newId = None
		newVersion = None

		if self.exe:
			r = requests.post(self.baseurl+"/0.6/changeset/"+str(cid)+"/upload", data=xml.encode('utf-8'), 
				auth=HTTPBasicAuth(self.user, self.passw),
				headers=self.xmlHeaders)

			if self.verbose >= 1: print (r.content)
			if r.status_code != 200: return None

			respRoot = ET.fromstring(r.content)
			for obj in respRoot:
				newId = obj.attrib['new_id']
				newVersion = obj.attrib['new_version']

		return int(newId), int(newVersion)

	def ModifiedWay(self, cid, nodeIds, tags, wid, existingVersion):

		xml = u"<?xml version='1.0' encoding='UTF-8'?>\n"
		xml += u'<osmChange version="0.6" generator="py">\n<modify>\n<way id="{0}" changeset="{1}" version="{2}">\n'.format(wid, cid, existingVersion)
		for nid in nodeIds:
			xml += u'<nd ref="{0}"/>\n'.format(nid)
		for k in tags:
			xml += u'<tag k="{0}" v="{1}"/>\n'.format(saxutils.escape(k), saxutils.escape(tags[k]))
		xml += u'</way>\n</modify>\n</osmChange>\n'
		if self.verbose >= 2: print (xml)
		newId = None
		newVersion = None

		if self.exe:
			r = requests.post(self.baseurl+"/0.6/changeset/"+str(cid)+"/upload", data=xml.encode('utf-8'), 
				auth=HTTPBasicAuth(self.user, self.passw),
				headers=self.xmlHeaders)

			if self.verbose >= 1: print (r.content)
			if r.status_code != 200: return None

			respRoot = ET.fromstring(r.content)
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
	url = "https://master.apis.dev.openstreetmap.org/api"
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

	osmMod = OsmMod(url, username, password)

	cid, status = osmMod.CreateChangeSet({'comment':"Api Tests"})
	print ("Created changeset", cid)
	assert cid > 0

	ret = osmMod.CreateNode(cid, 51.0, -1.0, {})
	print (ret)
	assert ret is not None
	ndId, nvVer = ret

	ret = osmMod.CreateNode(cid, 51.0, -1.00001, {})
	print (ret)
	assert ret is not None
	ndId2, nvVer2 = ret

	wayRet = osmMod.CreateWay(cid, [ndId, ndId2], {'testk':'val1'})
	print (wayRet)

	wayRet2 = osmMod.ModifiedWay(cid, [ndId, ndId2], {'testk':'val2'}, wayRet[0], wayRet[1])
	print (wayRet2)

	osmMod.CloseChangeSet(cid)
	print ("Closed changeset", cid)

