# -*- encoding: UTF8 -*-

from __future__ import print_function

import glob, sys, time, stat
pathToBuild = glob.glob('build/lib*')
if len(pathToBuild) > 0:
	versionString = "%d.%d" % (sys.version_info[0], sys.version_info[1])
	for i in pathToBuild:
		if versionString in i:
			sys.path.insert(0, i)

import P4
from P4 import P4Exception
import P4API
import unittest, os, types, shutil, stat
from subprocess import Popen, PIPE
import sys

def onRmTreeError( function, path, exc_info ):
	os.chmod( path, stat.S_IWRITE)
	os.remove( path )

class TestP4Python(unittest.TestCase):

	def setUp(self):
		self.setDirectories()
		self.p4d = "p4d"
		self.port = "rsh:%s -r \"%s\" -L log -vserver=3 -i" % ( self.p4d, self.server_root )
		self.p4 = P4.P4()
		self.p4.port = self.port

	def enableUnicode(self):
		cmd = [self.p4d, "-r", self.server_root, "-L", "log", "-vserver=3", "-xi"]
		f = Popen(cmd, stdout=PIPE).stdout
		for s in f.readlines():
		  pass
		f.close()
		
	def tearDown(self):
		if self.p4.connected():
			self.p4.disconnect()
		time.sleep( 1 )
		self.cleanupTestTree()

	def setDirectories(self):
		self.startdir = os.getcwd()
		self.server_root = os.path.join(self.startdir, 'testroot')
		self.client_root = os.path.join(self.server_root, 'client')

		self.cleanupTestTree()
		self.ensureDirectory(self.server_root)
		self.ensureDirectory(self.client_root)

	def cleanupTestTree(self):
		os.chdir(self.startdir)
		if os.path.isdir(self.server_root):
			shutil.rmtree(self.server_root, False, onRmTreeError)
				
	def ensureDirectory(self, directory):
		if not os.path.isdir(directory):
			os.mkdir(directory)

	
class TestP4(TestP4Python):
	
	def testInfo(self):
		self.assertTrue(self.p4 != None, "Could not create p4")
		self.p4.connect()
		self.assertTrue(self.p4.connected(), "Not connected")
		
		info = self.p4.run_info()
		self.assertTrue(isinstance(info, list), "run_info() does not return a list")
		info = info.pop()
		self.assertTrue(isinstance(info, dict), "run_info().pop() is not a dict")
		self.assertEqual(info['serverRoot'], self.server_root, "Server root incorrect")

	def testEnvironment(self):
		self.assertTrue(self.p4 != None, "Could not create p4")

		self.p4.charset			= "iso8859-1"	 
		self.p4.client			= "myclient"
		self.p4.host			= "myhost"
		self.p4.language		= "german"
		self.p4.maxresults		= 100000
		self.p4.maxscanrows		= 1000000
		self.p4.maxlocktime		= 10000
		self.p4.password		= "mypassword"
		self.p4.port			= "myserver:1666"
		self.p4.prog			= "myprogram"
		self.p4.tagged			= True
		self.p4.ticket_file		= "myticket"
		self.p4.user			= "myuser"

		self.assertEqual( self.p4.charset, "iso8859-1", "charset" )
		self.assertEqual( self.p4.client, "myclient", "client" )
		self.assertEqual( self.p4.host, "myhost", "host" )
		self.assertEqual( self.p4.language, "german", "language" )
		self.assertEqual( self.p4.maxresults, 100000, "maxresults" )
		self.assertEqual( self.p4.maxscanrows, 1000000, "maxscanrows" )
		self.assertEqual( self.p4.maxlocktime, 10000, "maxlocktime" )
		self.assertEqual( self.p4.password, "mypassword", "password" )
		self.assertEqual( self.p4.port, "myserver:1666", "port" )
		self.assertEqual( self.p4.tagged, 1, "tagged" )
		self.assertEqual( self.p4.ticket_file, "myticket", "ticket_file" )
		self.assertEqual( self.p4.user, "myuser", "user" )

	def testClient(self):
		self.p4.connect()
		self.assertTrue(self.p4.connected(), "Not connected")

		client = self.p4.fetch_client()
		self.assertTrue( isinstance(client, P4.Spec), "Client is not of type P4.Spec")

		client._root = self.client_root
		client._description = 'Some Test Client\n'

		try:
			self.p4.save_client(client)
		except P4.P4Exception:
			self.fail("Saving client caused exception")

		client2 = self.p4.fetch_client()

		self.assertEqual( client._root, client2._root, "Client root differs")
		self.assertEqual( client._description, client2._description, "Client description differs")
		
		try:
			client3 = self.p4.fetch_client('newtest')
			client3._view = [ '//depot/... //newtest/...']
			self.p4.save_client(client3)
		except P4.P4Exception:
				self.fail("Saving client caused exception")

	def createFiles(self, testDir):
		testAbsoluteDir = os.path.join(self.client_root, testDir)
		os.mkdir(testAbsoluteDir)
		
		# create a bunch of files
		files = ('foo.txt', 'bar.txt', 'baz.txt')
		for file in files:
			fname = os.path.join(testAbsoluteDir, file)
			f = open(fname, "w")
			f.write("Test Text")
			f.close()
			self.p4.run_add(testDir + "/" + file)
		
		self.assertEqual(len(self.p4.run_opened()), len(files), "Unexpected number of open files")
		return files
	
	def testFiles(self):
		self.p4.connect()
		self.assertTrue(self.p4.connected(), "Not connected")
		self._setClient()
		self.assertEqual(len(self.p4.run_opened()), 0, "Shouldn't have open files")
	
		testDir = 'test_files'
		files = self.createFiles(testDir)
		
		change = self.p4.fetch_change()
		self.assertTrue( isinstance(change, P4.Spec), "Change spec is not of type P4.Spec")
		change._description = "My Add Test"
		
		self._doSubmit("Failed to submit the add", change)
		
		# make sure there are no open files and all files are there
		
		self.assertEqual( len(self.p4.run_opened()), 0, "Still files in the open list")
		self.assertEqual( len(self.p4.run_files('...')), len(files), "Less files than expected")
		
		# edit the files
		
		self.assertEqual( len(self.p4.run_edit('...')), len(files), "Not all files open for edit")
		self.assertEqual( len(self.p4.run_opened()), len(files), "Not enough files open for edit")
		
		change = self.p4.fetch_change()
		change._description = "My Edit Test"
		self._doSubmit("Failed to submit the edit", change)
		self.assertEqual( len(self.p4.run_opened()), 0, "Still files in the open list")
		
		# branch testing
		
		branchDir = 'test_branch'
		try:
			result = self.p4.run_integ(testDir + '/...', branchDir + '/...')
			self.assertEqual(len(result), len(files), "Not all files branched")
		except P4.P4Exception:
			self.fail("Integration failed")
		
		change = self.p4.fetch_change()
		change._description = "My Branch Test"
		self._doSubmit("Failed to submit branch", change)
		
		# branch testing again
		
		branchDir = 'test_branch2'
		try:
			result = self.p4.run_integ(testDir + '/...', branchDir + '/...')
			self.assertEqual(len(result), len(files), "Not all files branched")
		except P4.P4Exception:
			self.fail("Integration failed")
		
		change = self.p4.fetch_change()
		change._description = "My Branch Test"
		self._doSubmit("Failed to submit branch", change)
		
		# filelog checks
		
		filelogs = self.p4.run_filelog( testDir + '/...' )
		self.assertEqual( len(filelogs), len(files) )
		
		df = filelogs[0]
		self.assertEqual( df.depotFile, "//depot/test_files/bar.txt", "Unexpected file in the filelog" )
		self.assertEqual( len(df.revisions), 2, "Unexpected number of revisions" )
		
		rev = df.revisions[0]
		self.assertEqual( rev.rev, 2, "Unexpected revision")
		self.assertEqual( len(rev.integrations), 2, "Unexpected number of integrations")
		self.assertEqual( rev.integrations[ 0 ].how, "branch into", "Unexpected how" )
		self.assertEqual( rev.integrations[ 0 ].file, "//depot/test_branch/bar.txt", "Unexpected target file" )

	def testShelves(self):
		self.p4.connect()
		self.assertTrue(self.p4.connected(), "Not connected")
		self._setClient()
		self.assertEqual(len(self.p4.run_opened()), 0, "Shouldn't have open files")
	
		if self.p4.server_level >= 28:
			testDir = 'test_shelves'
			files = self.createFiles(testDir)
			
			change = self.p4.fetch_change()
			self.assertTrue( isinstance(change, P4.Spec), "Change spec is not of type P4.Spec")
			change._description = "My Shelve Test"
			
			s = self.p4.save_shelve(change)
			c = s[0]['change']
			
			self.p4.run_revert('...');
			self.assertEqual(len(self.p4.run_opened()), 0, "Some files still opened")
			
			self.p4.run_unshelve('-s', c, '-f')
			self.assertEqual(len(self.p4.run_opened()), len(files), "Files not unshelved")
			
			self.p4.run_shelve('-d', '-c', c)
			self._doSubmit("Failed to submit after deleting shelve", change)
		else:
			print( "Need Perforce Server 2009.2 or greater to test shelving")
		
	def testPasswords(self):
		ticketFile = self.client_root + "/.p4tickets"
		password = "Password"
		self.p4.ticket_file = ticketFile
		self.assertEqual( self.p4.ticket_file, ticketFile, "Ticket file not set correctly")
		
		self.p4.connect()
		client = self.p4.fetch_client()
		client._root = self.client_root
		self.p4.save_client(client)
		
		try:
			self.p4.run_password( "", password )
		except P4.P4Exception:
			self.fail( "Failed to change the password" )
		
		self.p4.password = password
		self.assertEqual( self.p4.password, password, "Could not set password" )
		try:
			self.p4.run_login( )
		except P4.P4Exception:
			self.fail( "Failed to log on")
		
		try:
			self.p4.run_password( password, "" )
		except P4.P4Exception:
			self.fail( "Failed to reset the password" )
		
		self.assertTrue( os.path.exists(ticketFile), "Ticket file not found")
		
		tickets = self.p4.run_tickets()
		self.assertEqual(len(tickets), 1, "Expected only one ticket")
		self.assertEqual(len(tickets[0]), 3, "Expected exactly three entries in tickets")
		
	def testOutput(self):
		self.p4.connect()
		self._setClient()

		testDir = 'test_output'
		files = self.createFiles(testDir)
			   
		change = self.p4.fetch_change()
		self.assertTrue( isinstance(change, P4.Spec), "Change spec is not of type P4.Spec")
		change._description = "My Output Test"
		
		s = self.p4.run_submit(change)
		
		self.p4.exception_level = P4.P4.RAISE_NONE
		self.p4.run_sync();
		self.p4.run_sync();
		
		self.assertNotEqual( len(self.p4.warnings), 0, "No warnings reported")
		self.assertEqual( len(self.p4.errors), 0, "Errors reported")
		self.assertNotEqual( len(self.p4.messages), 0, "No messages reported")
		self.assertTrue( isinstance(self.p4.warnings[0],str), "Warning is not a string" )
		
		m = self.p4.messages[0]
		self.assertTrue( isinstance(m, P4API.P4Message), "First object of messages is not a P4Message")
		self.assertEqual( m.severity, P4.P4.E_WARN, "Severity was not E_WARN" )
		self.assertEqual( m.generic, P4.P4.EV_EMPTY, "Wasn't an empty message" )
		self.assertEqual( m.msgid, 6532, "Got the wrong message: %d" % m.msgid )

		
	def testExceptions(self):
		self.assertRaises(P4.P4Exception, self.p4.run_edit, "foo")
		
		self.p4.connect()
		self.assertRaises(P4.P4Exception, self.p4.run_edit, "foo")
		self.assertEqual( len(self.p4.errors), 1, "Did not find any errors")
		
		
	# father's little helpers
	
	def _setClient(self):
		"""Creates a client and makes sure it is set up"""
		self.assertTrue(self.p4.connected(), "Not connected")
		self.p4.cwd = self.client_root
		self.p4.client = "TestClient"
		client = self.p4.fetch_client()
		client._root = self.client_root
		self.p4.save_client(client)
		
	def _doSubmit(self, msg, *args):
		"""Submits the changes"""
		try:
			result = self.p4.run_submit(*args)
			self.assertTrue( 'submittedChange' in result[-1], msg)
		except P4.P4Exception as inst:
			self.fail("submit failed with exception ")
	
	def testResolve(self):
		testDir = 'test_resolve'
		testAbsoluteDir = os.path.join(self.client_root, testDir)
		os.mkdir(testAbsoluteDir)
		
		self.p4.connect()
		self.assertTrue(self.p4.connected(), "Not connected")
		self._setClient()
		self.assertEqual(len(self.p4.run_opened()), 0, "Shouldn't have open files")

		# create the file for testing resolve
		
		file = "foo"
		fname = os.path.join(testAbsoluteDir, file)
		f = open(fname, "w")
		f.write("First Line")
		f.close()
		textFile = testDir + "/" + file
		self.p4.run_add(textFile)
		
		file = "bin"
		bname = os.path.join(testAbsoluteDir, file)
		f = open(bname, "w")
		f.write("First Line")
		f.close()
		binFile = testDir + "/" + file
		self.p4.run_add("-tbinary", binFile)
		
		change = self.p4.fetch_change()
		change._description = "Initial"
		self._doSubmit("Failed to submit initial", change)
		
		# create a second revision
		
		self.p4.run_edit(textFile, binFile)
		with open(fname, "a") as f:
			f.write("Second Line")
		with open(bname, "a") as f:
			f.write("Second Line")
		
		change = self.p4.fetch_change()
		change._description = "Second"
		self._doSubmit("Failed to submit second", change)
		
		# now sync back to first revision
		
		self.p4.run_sync(textFile + "#1")
		
		# edit the first revision, thus setting up the conflict
		
		self.p4.run_edit(textFile)
		
		# sync back the head revision, this will schedule the resolve
		
		self.p4.run_sync(textFile)
		
		class TextResolver(P4.Resolver):
			def __init__(self, testObject):
				self.t = testObject
			
			def resolve(self, mergeData):
				self.t.assertEqual(mergeData.your_name, "//TestClient/test_resolve/foo", 
					"Unexpected your_name: %s" % mergeData.your_name)
				self.t.assertEqual(mergeData.their_name, "//depot/test_resolve/foo#2",
					"Unexpected their_name: %s" % mergeData.their_name)
				self.t.assertEqual(mergeData.base_name, "//depot/test_resolve/foo#1",
					"Unexpected base_name: %s" % mergeData.base_name)
				self.t.assertEqual(mergeData.merge_hint, "at", "Unexpected merge hint: %s" % mergeData.merge_hint)
				return "at"
		
		self.p4.run_resolve(resolver = TextResolver(self))
		
		# test binary file resolve which crashed previous version of P4Python
		
		self.p4.run_sync(binFile + "#1")
		self.p4.run_edit(binFile)
		self.p4.run_sync(binFile)
		
		class BinaryResolver(P4.Resolver):
			def __init__(self, testObject):
				self.t = testObject
			
			def resolve(self, mergeData):
				self.t.assertEqual(mergeData.your_name, "", 
					"Unexpected your_name: %s" % mergeData.your_name)
				self.t.assertEqual(mergeData.their_name, "",
					"Unexpected their_name: %s" % mergeData.their_name)
				self.t.assertEqual(mergeData.base_name, "",
					"Unexpected base_name: %s" % mergeData.base_name)
				self.t.assertNotEqual(mergeData.your_path, None,
					"YourPath is empty")
				self.t.assertNotEqual(mergeData.their_path, None,
					"TheirPath is empty")
				self.t.assertEqual(mergeData.base_path, None,
					"BasePath is not empty")
				self.t.assertEqual(mergeData.merge_hint, "at", "Unexpected merge hint: %s" % mergeData.merge_hint)
				return "at"
		
		self.p4.run_resolve(resolver = BinaryResolver(self))

		change = self.p4.fetch_change()
		change._description = "Third"
		self._doSubmit("Failed to submit third", change)
		
		if self.p4.server_level >= 31:
			self.p4.run_integrate("//TestClient/test_resolve/foo", "//TestClient/test_resolve/bar")
			self.p4.run_reopen("-t+w", "//TestClient/test_resolve/bar")
			self.p4.run_edit("-t+x", "//TestClient/test_resolve/foo")
			
			change = self.p4.fetch_change()
			change._description = "Fourth"
			self._doSubmit("Failed to submit fourth", change)
			
			self.p4.run_integrate("-3", "//TestClient/test_resolve/foo", "//TestClient/test_resolve/bar")
			result = self.p4.run_resolve("-n")
			
			self.assertEqual(len(result), 2, "No two resolves scheduled")
			
			class ActionResolver(P4.Resolver):
				def __init__(self, testObject):
					self.t = testObject
				
				def resolve(self, mergeData):
					self.t.assertEqual(mergeData.your_name, "//TestClient/test_resolve/bar",
						"Unexpected your_name: %s" % mergeData.your_name)
					self.t.assertEqual(mergeData.their_name, "//depot/test_resolve/foo#4",
						"Unexpected their_name: %s" % mergeData.their_name)
					self.t.assertEqual(mergeData.base_name, "//depot/test_resolve/foo#3",
						"Unexpected base_name: %s" % mergeData.base_name)
					self.t.assertEqual(mergeData.merge_hint, "at", "Unexpected merge hint: %s" % mergeData.merge_hint)
					return "at"
					
				def actionResolve(self, mergeData):
					self.t.assertEqual(mergeData.merge_action, "(text+wx)",
						"Unexpected mergeAction: '%s'" % mergeData.merge_action	 )
					self.t.assertEqual(mergeData.yours_action, "(text+w)",
						"Unexpected mergeAction: '%s'" % mergeData.yours_action	 )
					self.t.assertEqual(mergeData.their_action, "(text+x)",
						"Unexpected mergeAction: '%s'" % mergeData.their_action	 )
					self.t.assertEqual(mergeData.type, "Filetype resolve",
						"Unexpected type: '%s'" % mergeData.type)
	
					# check the info hash values
					self.t.assertTrue(mergeData.info['clientFile'].endswith(os.path.join('client','test_resolve', 'bar')),
						"Unexpected clientFile info: '%s'" % mergeData.info['clientFile'])
					self.t.assertEqual(mergeData.info['fromFile'], '//depot/test_resolve/foo',
						"Unexpected fromFile info: '%s'" % mergeData.info['fromFile'])
					self.t.assertEqual(mergeData.info['resolveType'], 'filetype',
						"Unexpected resolveType info: '%s'" % mergeData.info['resolveType'])
					
					return "am"
			
			self.p4.run_resolve(resolver=ActionResolver(self))
		
	def testMap(self):
		# don't need connection, simply test all the Map features
		
		map = P4.Map()
		self.assertEqual(map.count(), 0, "Map does not have count == 0")
		self.assertEqual(map.is_empty(), True, "Map is not empty")
		
		map.insert("//depot/main/... //ws/...")
		self.assertEqual(map.count(), 1, "Map does not have 1 entry")
		self.assertEqual(map.is_empty(), False, "Map is still empty")

		self.assertEqual(map.includes("//depot/main/foo"), True, "Map does not map //depot/main/foo")
		self.assertEqual(map.includes("//ws/foo", False), True, "Map does not map //ws/foo")

		map.insert("-//depot/main/exclude/... //ws/exclude/...")
		self.assertEqual(map.count(), 2, "Map does not have 2 entries")
		self.assertEqual(map.includes("//depot/main/foo"), True, "Map does not map foo anymore")
		self.assertEqual(map.includes("//depot/main/exclude/foo"), False, "Map still maps foo")
		self.assertEqual(map.includes("//ws/foo", False), True, "Map does not map foo anymore (reverse)")
		self.assertEqual(map.includes("//ws/exclude/foo"), False, "Map still maps foo (reverse)")
		
		map.clear()
		self.assertEqual(map.count(), 0, "Map has elements after clearing")
		self.assertEqual(map.is_empty(), True, "Map is still not empty after clearing")
		
		a = [ "//depot/main/... //ws/main/..." ,
			  "//depot/main/doc/... //ws/doc/..."]
		map = P4.Map(a)
		self.assertEqual(map.count(), 3, "Map does not contain 3 elements")
		
		map2 = P4.Map("//ws/...", "C:\Work\...")
		self.assertEqual(map2.count(), 1, "Map2 does not contain any elements")
		
		map3 = P4.Map.join(map, map2)
		self.assertEqual(map3.count(), 3, "Join did not produce three entries")

		map.clear()
		map.insert( '"//depot/dir with spaces/..." "//ws/dir with spaces/..."' )
		self.assertEqual( map.includes("//depot/dir with spaces/foo"), True, "Quotes not handled correctly" )
		
	def testThreads( self ):
			import threading
			
			class AsyncInfo( threading.Thread ):
					def __init__( self, port ):
							threading.Thread.__init__( self )
							self.p4 = P4.P4()
							self.p4.port = port
							
					def run( self ):
							self.p4.connect()
							info = self.p4.run_info()
							self.p4.disconnect()
			
			threads = []
			for i in range(1,10):
					threads.append( AsyncInfo(self.port) )
			for thread in threads:
					thread.start()
			for thread in threads:
					thread.join()

	def testArguments( self ):
		p4 = P4.P4(debug=3, port="9999", client="myclient")
		self.assertEqual(p4.debug, 3)
		self.assertEqual(p4.port, "9999")
		self.assertEqual(p4.client, "myclient")
	
	def testUnicode( self ):
		self.enableUnicode()
		
		testDir = 'test_files'
		testAbsoluteDir = os.path.join(self.client_root, testDir)
		os.mkdir(testAbsoluteDir)
		
		self.p4.charset = 'iso8859-1'
		self.p4.connect()
		self._setClient()
		
		# create a bunch of files
		tf = os.path.join(testDir, "unicode.txt")
		fname = os.path.join(self.client_root, tf)
	
		if sys.version_info < (3,0):
			with open(fname, "w") as f:
				f.write("This file cost \xa31")
		else:
			with open(fname, "wb") as f:
				f.write("This file cost \xa31".encode('iso8859-1'))

		self.p4.run_add('-t', 'unicode', tf)
		
		self.p4.run_submit("-d", "Unicode file")
 
		self.p4.run_sync('...#0')
		self.p4.charset = 'utf8'
		
		self.p4.run_sync()
		if sys.version_info < (3,0):
			with open(fname, 'r') as f:
				buf = f.read()
				self.assertTrue(buf == "This file cost \xc2\xa31", "File not found, UNICODE support broken?")
		else:
			with open(fname, 'rb') as f:
				buf = f.read()
				self.assertTrue(buf == "This file cost \xa31".encode('utf-8'), "File not found, UNICODE support broken?")
		
			ch = self.p4.run_changes(b'-m1')
			self.assertEqual(len(ch), 1, "Byte strings broken")
			
		self.p4.disconnect()
		
	def testTrack( self ):
		success = self.p4.track = 1
		self.assertTrue(success, "Failed to set performance tracking")
		self.p4.connect()
		self.assertTrue(self.p4.connected(), "Failed to connect")
		try: 
		  self.p4.track = 0
		  self.assertTrue(self.p4.track, "Changing performance tracking is not allowed")
		except P4Exception:
		  pass
		self.p4.run_info()
		self.assertTrue(len(self.p4.track_output), "No performance tracking reported")

	def testOutputHandler( self ):
		self.assertEqual( self.p4.handler, None )
		
		# create the standard iterator and try to set it
		h = P4.OutputHandler()
		self.p4.handler = h
		self.assertEqual( self.p4.handler, h )
		
		# test the resetting
		self.p4.handler = None
		self.assertEqual( self.p4.handler, None )
		self.assertEqual( sys.getrefcount(h), 2 )
		
		self.p4.connect()
		self._setClient()
		
		class MyOutputHandler(P4.OutputHandler):
			def __init__(self):
				P4.OutputHandler.__init__(self)
				self.statOutput = []
				self.infoOutput = []
				self.messageOutput = []
			
			def outputStat(self, stat):
				self.statOutput.append(stat)
				return P4.OutputHandler.HANDLED
			
			def outputInfo(self, info):
				self.infoOutput.append(info)
				return P4.OutputHandler.HANDLED
			
			def outputMessage(self, msg):
				self.messageOutput.append(msg)
				return P4.OutputHandler.HANDLED
		
		testDir = 'test-handler'
		files = self.createFiles(testDir)
		
		change = self.p4.fetch_change()
		change._description = "My Handler Test"
		
		self._doSubmit("Failed to submit the add", change)

		h = MyOutputHandler()
		self.assertEqual( sys.getrefcount(h), 2 )
		self.p4.handler = h

		self.assertEqual( len(self.p4.run_files('...')), 0, "p4 does not return empty list")
		self.assertEqual( len(h.statOutput), len(files), "Less files than expected")
		self.assertEqual( len(h.messageOutput), 0, "Messages unexpected")
		self.p4.handler = None
		self.assertEqual( sys.getrefcount(h), 2 )

	if False: # test currently disabled
		def testProgress( self ):
			self.p4.connect()
			self._setClient()
			testDir = "progress"
		
			testAbsoluteDir = os.path.join(self.client_root, testDir)
			os.mkdir(testAbsoluteDir)
		
			if self.p4.server_level >= 33:
				class TestProgress( P4.Progress ):
					def __init__(self):
						P4.Progress.__init__(self)
						self.invoked = 0
						self.types = []
						self.descriptions = []
						self.units = []
						self.totals = []
						self.positions = []
						self.dones = []
				
					def init(self, type):
						self.types.append(type)
					def setDescription(self, description, unit):
						self.descriptions.append(description)
						self.units.append(unit)
					def setTotal(self, total):
						self.totals.append(total)
					def update(self, position):
						self.positions.append(position)
					def done(self, fail):
						self.dones.append(fail)
			
				# first, test the submits
				self.p4.progress = TestProgress()
			
				# create a bunch of files, fill them with content, and add them
				total = 100
				for i in range(total):
					fname = os.path.join(testAbsoluteDir, "file%02d" % i)
					with open(fname, 'w') as f:
						f.write('A'*1024) # write 1024 'A' characters to create 1K file
						self.p4.run_add(fname)
				self.p4.run_submit('-dSome files')
			
				self.assertEqual(len(self.p4.progress.types), total, "Did not receive %d progress initialize calls" % total)
				self.assertEqual(len(self.p4.progress.descriptions), total, "Did not receive %d progress description calls" % total)
				self.assertEqual(len(self.p4.progress.totals), total, "Did not receive %d progress totals calls" % total)
				self.assertEqual(len(self.p4.progress.positions), total, "Did not receive %d progress positions calls" % total)
				self.assertEqual(len(self.p4.progress.dones), total, "Did not receive %d progress dones calls" % total)
			
				class TestOutputAndProgress( P4.Progress, P4.OutputHandler ):
					def __init__(self):
						P4.Progress.__init__(self)
						P4.OutputHandler.__init__(self)
						self.totalFiles = 0
						self.totalSizes = 0
					
					def outputStat(self, stat):
						if 'totalFileCount' in stat:
							self.totalFileCount = int(stat['totalFileCount'])
						if 'totalFileSize' in stat:
							self.totalFileSize = int(stat['totalFileSize'])
						return P4.OutputHandler.HANDLED
				
					def outputInfo(self, info):
						return P4.OutputHandler.HANDLED
				
					def outputMessage(self, msg):
						return P4.OutputHandler.HANDLED

					def init(self, type):
						self.type = type
					def setDescription(self, description, unit):
						pass
					def setTotal(self, total):
						pass
					def update(self, position):
						self.position = position
					def done(self, fail):
						self.fail = fail
			
				callback = TestOutputAndProgress()
				self.p4.run_sync('-f', '-q', '//...', progress=callback, handler=callback)

				self.assertEqual(callback.totalFileCount, callback.position, 
								"Total does not match position %d <> %d" % (callback.totalFileCount, callback.position))
				self.assertEqual(total, callback.position, 
								"Total does not match position %d <> %d" % (total, callback.position))
			else:
				print("Test case testProgress needs a 2012.2+ Perforce Server to run")
	
	def testStreams( self ):
		self.p4.connect()
		self._setClient()
		
		if self.p4.server_level >= 30:
			self.assertEqual( self.p4.streams, 1, "Streams are not enabled")
			
			# Create the streams depot
			
			d = self.p4.fetch_depot( "streams" )
			d._type = 'stream'
			self.p4.save_depot( d )
			
			# create a stream
			
			s = self.p4.fetch_stream( "//streams/main" )
			s._description = 'Main line stream'
			s._type = 'mainline'
			self.p4.save_stream( s )
			
			# check if stream exists
			# due to a server "feature" we need to disconnect and reconnect first
			
			self.p4.disconnect()
			self.p4.connect()
			
			streams = self.p4.run_streams()
			self.assertEqual( len(streams), 1, "Couldn't find any streams")
		else:
			print("Test case testStreams needs a 2010.2+ Perforce Server to run")
	
	def testSpecs( self ):
		self.p4.connect()
		# create a bunch of specs
		# try to iterate through them afterwards
		
		#		'clients'	:	('client', 'client'),
		#		'labels'	:	('label', 'label'),
		#		'branches'	:	('branch', 'branch'),
		#		'changes'	:	('change', 'change'),
		#		'streams'	:	('stream', 'Stream'),
		#		'jobs'		:	('job', 'Job'),
		#		'users'		:	('user', 'User'),
		#		'groups'	:	('group', 'group'),
		#		'depots'	:	('depot', 'name'),
		#		'servers'	:	('server', 'Name')

		clients = []
		c = self.p4.fetch_client('client1')
		self.p4.save_client(c)
		clients.append(c._client)
		c = self.p4.fetch_client('client2')
		self.p4.save_client(c)
		clients.append(c._client)
		
		for c in self.p4.iterate_clients():
			self.assertTrue(c._client in clients, "Cannot find client in iteration")
		
		labels = []
		l = self.p4.fetch_label('label1')
		self.p4.save_label(l)
		labels.append(l._label)
		l = self.p4.fetch_label('label2')
		self.p4.save_label(l)
		labels.append(l._label)
		
		for l in self.p4.iterate_labels():
			self.assertTrue(l._label in labels, "Cannot find labels in iteration")
	
	# P4.encoding is only available (and undoc'd) in Python 3
	
	if sys.version_info[0] >= 3:
		def testEncoding( self ):
			self.p4.connect()
			self.p4.encoding = 'raw'
			
			self.assertEqual(self.p4.encoding, 'raw', "Encoding is not raw")
			info = self.p4.run_info()[0]
			self.assertEqual(type(info['serverVersion']), bytes, "Type of string is not bytes")
		
if __name__ == '__main__':
	unittest.main()
