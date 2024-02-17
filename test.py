import io
import os
import re
import sys
import time
import json
import base64

comment = sys.argv[2]
file_path = sys.argv[1]
multi_line_begin = "";
multi_line_end = "";
if len(sys.argv)>3:
	multi_line_begin = sys.argv[3];
if len(sys.argv)>4:
	multi_line_end = sys.argv[4];



temp_file_path = file_path + '.tmp'

begin_pattern = re.compile(f"^{multi_line_begin}pygen_begin\\((.*?)\\)")
end_pattern = re.compile(f"^pygen_end\\((.*?)\\){multi_line_begin}")
code_begin_pattern = re.compile(f"^{re.escape(comment)}pygen_code_begin\\s(.*)")
code_end_pattern = re.compile(f"^{re.escape(comment)}pygen_code_end(.*?)")
code_key = "" 

def gen_code(script):
	#thank you chatGPT
	capture = io.StringIO()
	generated = ""
	original_stdout = sys.stdout
	try:
		sys.stdout = capture
		exec(script)
		generated = capture.getvalue()
	finally:
		sys.stdout = original_stdout
	return generated

class Entry:
	def __init__(self):
		self.Begin = -1
		self.End = -1
		self.CodeBegin = -1
		self.CodeEnd = -1
		self.Code = ""
		self.Key = ""
	def __str__(self):
		return f"{self.Begin} {self.End} {self.CodeBegin} {self.CodeEnd} '{self.Code}' {self.Key}"

Entries = {}

with open(file_path, 'r') as file:
	lines = file.readlines()

#pass one, search for all pybeg/pyend
E = Entry()

line_keys = []
for x in range(0, len(lines)): #line in lines:
	line_keys.append("")

for x in range(0, len(lines)): #line in lines:
	line = lines[x]
	if E.Begin == -1:
		match_begin = begin_pattern.search(line)
		if match_begin:
			key = match_begin.group(1).strip()
			if "" == key:
				hashed = str(hash(str(abs(time.time()))))
				b = base64.b64encode(bytes(hashed, 'utf-8'))
				key = b.decode('utf-8')[:-10]

			E.Key = key
			E.Begin = x
	else:
		match_end = end_pattern.search(line)
		if match_end:
			E.End = x
			Entries[E.Key] = E
			E = Entry()

Dummy = Entry()
key = "" 
for x in range(0, len(lines)): #line in lines:
	line = lines[x]
	if Dummy.CodeBegin == -1:
		match_code_begin = code_begin_pattern.search(line)
		if match_code_begin:
			key = match_code_begin.group(1).strip()
			if key in Entries:
				Entries[key].CodeBegin = x
			else:
				print(f"unknown code key {key} - ignoring\n");
			Dummy.CodeBegin = x
			Dummy.Key = key
	else:
		match_code_end = code_end_pattern.search(line)
		if match_code_end:
			key = Dummy.Key
			if key in Entries:
				Entries[key].CodeEnd = x
			Dummy.Key = ""
			Dummy.CodeBegin = -1
			Dummy.CodeEnd = -1




#tag where we want to insert code
for k, v in Entries.items():
	if v.CodeBegin != -1:
		line_keys[v.CodeBegin] = v.Key
	else: 
		if v.End != -1: 
			line_keys[v.End] = v.Key
		if v.Begin != -1: 
			line_keys[v.Begin] = v.Key

for k, v in Entries.items():
	the_str = ''.join(lines[v.Begin+1:v.End])
	v.Code = gen_code(the_str)

# for x in range(0, len(lines)): #line in lines:
#	print(f"{line_keys[x]} :: {x} ::{lines[x]}")

with open(temp_file_path, 'w') as temp_file:
	x = 0
	while x < len(lines): #line in lines:
		line = lines[x]
		line_key = line_keys[x]
		if "" == line_key:
			temp_file.write(line)
		else:
			E = Entries[line_key]
			key = line_key
			if E.Begin == x:
				temp_file.write(f"{multi_line_begin}pygen_begin({key})\n")
			elif E.Code and E.End != -1:
				if x == E.End:
					temp_file.write(line)
					temp_file.write("\n\n")
				temp_file.write(f"{comment}pygen_code_begin {key}\n\n")
				temp_file.write(E.Code)
				temp_file.write(f"\n{comment}pygen_code_end\n")
				if x == E.CodeBegin:
					x += E.CodeEnd - E.CodeBegin
		x += 1

# Replace the original file with the temporary file
os.remove(file_path)
os.rename(temp_file_path, file_path)


"""pygen_begin()
for x in range(0,5):
	print(f"def foo{x}:")
	print("\t print(\"hello world{x}\")")
pygen_end()"""


"""pygen_begin()
for x in range(0,10):
	print("print(\"not very easter egg\")")
pygen_end()"""