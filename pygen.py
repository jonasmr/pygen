import io
import os
import re
import sys
import time
import json
import random
import string

comment = sys.argv[2]
file_path = sys.argv[1]
multi_line_begin = "";
multi_line_end = "";
if len(sys.argv)>3:
	multi_line_begin = sys.argv[3];
if len(sys.argv)>4:
	multi_line_end = sys.argv[4];


print(" comments are '{comment}' '{multi_line_begin}' '{multi_line_end}' ")
temp_file_path = file_path + '.tmp'

begin_pattern = re.compile(f"^@pybeg")
end_pattern = re.compile(f"^@pyend")
code_begin_pattern = re.compile(f"^{re.escape(comment)}pygen_code_begin\\s(.*)")
code_end_pattern = re.compile(f"^{re.escape(comment)}pygen_code_end(.*?)")
code_key = "" 

ScriptTemp = {}
ScriptEntries = {}
CodeEntries = {}


def pyg(name):
	stream = io.StringIO()
	script_dict[name] = stream
	return stream

class ScriptEntry:
	def __init__(self):
		self.ScriptBegin = -1
		self.ScriptEnd = -1
		self.Key = ""
	def __str__(self):
		return f"{self.ScriptBegin} {self.ScriptEnd} / {self.Key}"

class CodeEntry:
	def __init__(self, Key, Code = "", ScriptKey = ""):
		self.Begin = -1
		self.End = -1
		self.Code = Code
		self.Key = Key
	def __str__(self):
		return f"{self.Begin} {self.End} {self.Key} / {self.Code} "

def gen_code(script, script_key):
	ScriptTemp = {}
	capture = io.StringIO()
	generated = ""
	original_stdout = sys.stdout
	try:
		sys.stdout = capture
		exec(script)
		generated = capture.getvalue()

		for k, v in ScriptTemp:
			if k in CodeEntries:
				CodeEntries[k].Code = v
				CodeEntries[k].ScriptKey = script_key
				
			else:
				CodeEntries[k] = CodeEntry(k, v, script_key)
			CodeEntries[k] = v
	finally:
		sys.stdout = original_stdout
	return generated

def randomword(length):
   letters = string.ascii_lowercase
   return ''.join(random.choice(letters) for i in range(length))	






with open(file_path, 'r') as file:
	lines = file.readlines()

#pass one, search for all pybeg/pyend
E = Entry()

script_keys = []
code_keys = []
for x in range(0, len(lines)): #line in lines:
	script_keys.append("")
	code_keys.append("")



#search for script entries
ScriptEntry SE = ScriptEntry()
for x in range(0, len(lines)): #line in lines:
	line = lines[x]

	if SE.ScriptBegin == -1:
		match_begin = begin_pattern.search(line)
		if match_begin:
			key = match_begin.group(1).strip()
			if "" == key:
				key = randomword(16)
			SE.Key = Key
			SE.ScriptBegin = x
	else:
		match_end = end_pattern.search(line)
		if match_end:
			SE.ScriptEnd = x
			ScriptEntries[SE.Key] = SE
			script_keys[x] = SE.Key
			SE = ScriptEntry()

SE = None
#search for existing code blocks.
CodeEntry = CodeEntry()

for x in range(0, len(lines)): #line in lines:
	line = lines[x]
	if CodeEntry.CodeBegin == -1:
		match_code_begin = code_begin_pattern.search(line)
		if match_code_begin:
			key = match_code_begin.group(1).strip()
			if key in CodeEntries:
				CodeEntries[key].CodeBegin = x
				CodeEntry.CodeBegin = x
				CodeEntry.Key = key
			else:
				print(f"unknown code key {key} - ignoring\n");
	else:
		match_code_end = code_end_pattern.search(line)
		if match_code_end:
			key = CodeEntry.Key
			if key in CodeEntries:
				CodeEntries[key].CodeEnd = x
			else:
				print(f"failed")
				sys.exit(1)
			CodeEntry.Key = ""
			CodeEntry.CodeBegin = -1
			CodeEntry.CodeEnd = -1

CodeEntry = None

#generate code
for k, v in ScriptEntries.items():
	the_str = ''.join(lines[v.ScriptBegin+1:v.ScriptEnd])
	gen_code(the_str, v)




#tag where we want to insert code
#for k, v in Entries.items():
#	#if v.CodeBegin != -1:
#		line_keys[v.CodeBegin] = v.Key
#	else: 
#		if v.End != -1: 
#			line_keys[v.End] = v.Key
#		if v.Begin != -1: 
#			line_keys[v.Begin] = v.Key

for k, v in Entries.items():
	the_str = ''.join(lines[v.Begin+1:v.End])
	v.Code = gen_code(the_str)

# for x in range(0, len(lines)): #line in lines:
#	print(f"{line_keys[x]} :: {x} ::{lines[x]}")

with open(temp_file_path, 'w') as temp_file:
	x = 0
	while x < len(lines): #line in lines:
		line = lines[x]
		script_key = script_keys[x]
		code_key = code_keys[x]
		if "" == script_key and "" == code_key:
			temp_file.write(line)
		elif "" != code_key:
			# spit out code
			CE = CodeEntries[code_key]
			temp_file.write(f"{comment}pygen_code_begin {CE.key}\n")
			temp_file.write(CE.Code)
			temp_file.write(f"{comment}pygen_code_end\n")
			#skip previous code..
			x += E.End - E.Begin
		elif "" != script_key:
			# loop over all code entrie
			temp_file.write(line)
			x += 1
			# todo skip comments.
			for k, v in CodeEntries:
				if v.CodeBegin == -1: # new code, insert
					temp_file.write(f"\n")
					temp_file.write(f"{comment}pygen_code_begin {CE.key}\n")
					temp_file.write(CE.Code)
					temp_file.write(f"{comment}pygen_code_end\n")
		x += 1

# Replace the original file with the temporary file
# os.remove(file_path)
# os.rename(temp_file_path, file_path)


"""
@pybeg
o = pyg('defs')
for x in range(0,2):
	o.write(f"def foo{x}:\\n")
	o.write(f"\tprint(\"hello world{x}\")\\n")
@pyend
"""


"""
@pybeg
o = pyg('range')
for x in range(0,3):
	o.write("print(\"not very easter egg\")\\n")
@pyend
"""