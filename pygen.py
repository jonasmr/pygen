import io
import os
import re
import sys
import time
import json

comment = sys.argv[1]
file_path = sys.argv[2]
temp_file_path = file_path + '.tmp'

begin_pattern = re.compile(r'^pygen_begin\((.*?)\)')
end_pattern = re.compile(r'^pygen_end\((.*?)\)')
code_begin_pattern = re.compile(f"^{re.escape(comment)}pygen_code_begin\\s(.*)")
code_end_pattern = re.compile(f"^{re.escape(comment)}pygen_code_end(.*?)")
code_key = "" 

class Entry:
	def __init__(self):
		self.Begin = -1
		self.End = -1
		self.CodeBegin = -1
		self.CodeEnd = -1
		self.Code = ""
		self.Key = ""
	def __str__(self):
		return f"{v.Begin} {v.End} {v.CodeBegin} {v.CodeEnd} '{v.Code}' {v.Key}"

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
				key = str(hash(str(time.time())))
			E.Key = key
			E.Begin = x
	else:
		match_end = end_pattern.search(line)
		if match_end:
			E.End = x
			Entries[E.Key] = E
			v = Entries[E.Key]
			print(f"ADD {v.Begin} {v.End} {v.CodeBegin} {v.CodeEnd} {v.Code} {v.Key} ")
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




def gen_code(script):
	print(f"generating for {script}\n")
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


#tag where we want to insert code
for k, v in Entries.items():
	if v.CodeBegin != -1:
		line_keys[v.CodeBegin] = v.Key
	else: 
		if v.End != -1: 
			line_keys[v.End] = v.Key

for k, v in Entries.items():
	the_str = ''.join(lines[v.Begin+1:v.End])
	v.Code = gen_code(the_str)

#sort reverse based on insertion point so we

with open(temp_file_path, 'w') as temp_file:
	x = 0
	while x < len(lines): #line in lines:
		line = lines[x]
		line_key = line_keys[x]
		if "" == line_key:
			temp_file.write(line)
		else:
			key = v.Key
			E = Entries[line_key]

			##temp_file.write(f"YO_STARTING {key} xxx {str(E)}\n")
			if v.Code and v.End != -1:
				if line == v.CodeEnd:
					#append after code block
					temp_file.write(line)
					temp_file.write("\n")
				temp_file.write(f"{comment}pygen_code_begin {key}\n")
				temp_file.write(v.Code)
				temp_file.write(f"{comment}pygen_code_end\n")

				if line == v.CodeBegin:
					#skip existing code.
					x += v.CodeEnd - v.CodeBegin -1
			##temp_file.write(f"YO_END {key}\n")
		x += 1

# Replace the original file with the temporary file
# os.remove(file_path)
#os.rename(temp_file_path, file_path)

print("File has been modified in place.")
print(temp_file_path)