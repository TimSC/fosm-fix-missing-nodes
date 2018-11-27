from __future__ import print_function
from __future__ import unicode_literals
import argparse
import fixmissingnodes
import osmmod
from parse import parse #pip install parse

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

	fi = open(args.input[0], "rt")
	doneWays = set()
	for li in fi.readlines():
		nid, wid = parse('Node {} does not exist, but referenced by way: {}', li.strip())
		if wid in doneWays:
			continue

		fixmissingnodes.CheckAndFixWay(wid, osmMod)

		doneWays.add(wid)

