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


#print(f"comments are '{comment}' '{multi_line_begin}' '{multi_line_end}' ")

temp_file_path = file_path + '.tmp'

begin_pattern = re.compile(f"^@pybeg")
end_pattern = re.compile(f"^@pyend")
code_begin_pattern = re.compile(f"^{re.escape(comment)}pygen_code_begin\\s(.*)")
code_end_pattern = re.compile(f"^{re.escape(comment)}pygen_code_end(.*?)")
comment_end_pattern = re.compile(f"^{re.escape(multi_line_end)}(.*?)")
code_key = "" 

ScriptTemp = {}
ScriptEntries = {}
CodeEntries = {}

def pyg(name):
	stream = io.StringIO()
	ScriptTemp[name] = stream
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
		self.ScriptKey = ScriptKey
	def __str__(self):
		return f"{self.Begin} {self.End} {self.Key} / {self.ScriptKey} /{self.Code} "

def gen_code(script, script_key):
	ScriptTemp.clear()
	capture = io.StringIO()
	generated = ""
	original_stdout = sys.stdout
	try:
		#sys.stdout = capture
		exec(script)
		generated = capture.getvalue()
		for k, v in ScriptTemp.items():
			# print(f"script key is : '{script_key}'")
			if k in CodeEntries:
				CodeEntries[k].Code = v.getvalue()
				CodeEntries[k].ScriptKey = script_key
			else:
				CodeEntries[k] = CodeEntry(k, v.getvalue(), script_key)
			#CodeEntries[k] = v
	finally:
		pass
		#sys.stdout = original_stdout
	return generated

def randomword(length):
   letters = string.ascii_lowercase
   return ''.join(random.choice(letters) for i in range(length))	



with open(file_path, 'r') as file:
	lines = file.readlines()


script_keys = []
code_keys = []
for x in range(0, len(lines)): #line in lines:
	script_keys.append("")
	code_keys.append("")



#search for script entries
SE = ScriptEntry()
for x in range(0, len(lines)): #line in lines:
	line = lines[x]

	if SE.ScriptBegin == -1:
		match_begin = begin_pattern.search(line)
		if match_begin:

			#key = match_begin.group(1).strip()
			#if "" == key:
			Key = randomword(16)
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


#generate code
for k, v in ScriptEntries.items():
	the_str = ''.join(lines[v.ScriptBegin+1:v.ScriptEnd])
	gen_code(the_str, k)


#search for existing code blocks.
CodeBegin = -1
CodeBeginKey = ""
for x in range(0, len(lines)): #line in lines:
	line = lines[x]
	if CodeBegin == -1:
		match_code_begin = code_begin_pattern.search(line)
		if match_code_begin:
			Key = match_code_begin.group(1).strip()
			
			if Key in CodeEntries:
				CodeEntries[Key].Begin = x
				CodeBegin = x
				CodeBeginKey = Key
			else:
				print(f"unknown code key {Key} - ignoring\n");
	else:

		match_code_end = code_end_pattern.search(line)
		if match_code_end:
			if CodeBeginKey in CodeEntries:
				CodeEntries[CodeBeginKey].End = x
				code_keys[CodeBegin] = CodeBeginKey
			else:
				print(f"failed")
				sys.exit(1)
			CodeBegin = -1
			CodeBeginKey = ""


CodeBegin = None
CodeBeginKey = ""

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

			temp_file.write(f"{comment}pygen_code_begin {CE.Key}\n")
			temp_file.write(CE.Code)
			if not CE.Code.endswith('\n'):
				temp_file.write('\n')
			temp_file.write(f"{comment}pygen_code_end\n")
			#skip previous code..
			x += CE.End - CE.Begin
		elif "" != script_key:
			# loop over all code entrie
			temp_file.write(line)
			while x + 1 < len(lines) and comment_end_pattern.search(lines[x+1]):
				x += 1
				temp_file.write(lines[x])

			for k, v in CodeEntries.items():
				if v.ScriptKey == script_key and v.Begin == -1: # new code, insert
					temp_file.write(f"\n")
					temp_file.write(f"{comment}pygen_code_begin {v.Key}\n")
					temp_file.write(v.Code)
					if not v.Code.endswith('\n'):
						temp_file.write('\n')
					temp_file.write(f"{comment}pygen_code_end\n")
		x += 1

# Replace the original file with the temporary file
os.remove(file_path)
os.rename(temp_file_path, file_path)


"""
@pybeg
o = pyg('defs')
f = pyg('fisk')
for x in range(0,2):
	o.write(f"def foo{x}:\n")
	o.write(f"\tprint(\"hello world{x}\")\n")
	f.write("#fisk!!")
@pyend
"""


"""
@pybeg
o = pyg('range')
for x in range(0,3):
	o.write("print(\"not very easter egg\")\n")
@pyend
"""