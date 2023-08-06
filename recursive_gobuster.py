#this code performs a depth first recursive search using gobuster
#by depth first I mean the following, assume you have a tree like this
#my-web-app/
# ├
# ├─ public/
# │  ├─ robots.txt
# │  ├─ index.html
# │  ├─ assets/
# │  |   ├─ new.php
# │  |   ├─ old.php
# ├─ admin/
# │  ├─ admin.php
# │  ├─ index.js
# ├─ dev/
# │  ├─ test.php
# │  ├─ test2.php
#
#the code will first find public -> favicon.ico, public -> index.html, public -> assets -> new.php, public -> assets -> old.php
#then admin -> admin.php, admin -> index.js
#then dev -> test.php, dev -> test2.php
#
#so it first searches as deep as it can rather than covering the entirety of each depth
#level before proceeding


#TODO add verbose option (print dirs as well as their messy initial find)
#TODO add breadth or depth first as command line option rather than two separate files
#TODO add debugging as command line argument for users if they wwant to debug (otherwise just change logging level)


class Node:
    def __init__(self, depth, base_path, parent_node):
        self.depth = depth
        self.base_path = base_path
        self.parent_node = parent_node
        self.results = []
        self.children_dirs = []
    def append_child_dir(self, child_dir):
        self.children_dirs.append(child_dir)
    def append_result(self, result):
        self.results.append(result)
    def __str__(self):
        return f"Depth = {self.depth} Base Path = {self.base_path} Results = {self.results} Children Dirs = {self.children_dirs}"
    def print_me(self):
        print("Printing Children Dirs")
        print(self.children_dirs)
        for child in self.children_dirs:
            print(child)
        print("Printing Results")
        print(self.results)
        for result in self.results:
            print(result)


import sys
import os
import string
import random
import logging

#set up basic logging to debug...
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

#throughout this script we will need temp
#files to use as a scratchpad, get those 
#random names here
def get_random_name_for_tmp_file():
   return "/tmp/gobuster_scratchpad_"+str(''.join(random.choices(string.ascii_uppercase +
                             string.digits, k=12)))+".txt"


#Required args are:
#ip address
#port
#base path
#wordlist
#additional options
#final output file name/path

#6 actual user supplied args, but since the first arg
#is script name by default, there are 7 in total
num_required_args = 7

#if wrong  number of args, exit
if len(sys.argv) != num_required_args:
    print("Error, incorrect number of args")
    print("Usage = recursive_gobuster.py {IP/HOSTNAME} {PORT} {BASE PATH} {WORDLIST} {\"ADDITIONAL OPTIONS\" <--in quotes, use \"\" for none} {OUTPUT FILE NAME/PATH}")
    print("Example without additional args = python3 recursive_gobuster.py 192.168.0.1 80 /wp /usr/share/seclists/Discovery/Web-Content/common.txt \"\" ~/gobuster-notes/my-test-file.txt")
    print("Example with additional args = python3 recursive_gobuster.py 192.168.0.1 80 /wp /usr/share/seclists/Discovery/Web-Content/common.txt \"-x .php\" ~/gobuster-notes/my-test-file.txt")
    exit(1)

#show what options the program is running with
print("RUNNING: " + sys.argv[0])
print("With Args: " + " Host = " + sys.argv[1] + " Port = " + sys.argv[2]  + " Base Path = " + sys.argv[3] + " Wordlist = " + sys.argv[4] 
      + " Options = " + sys.argv[5] + " Output file = " + sys.argv[6])

#put the args to proper variables
host = sys.argv[1]
port = sys.argv[2]
base_path = sys.argv[3].lstrip("/")
wordlist = sys.argv[4]
options = sys.argv[5]
outfile = sys.argv[6]






#track the depth of the search
depth = 0

#a tree like structure of the search will get created which helps for printing 
#a usefully formatted output file...
all_nodes = []

root_node = Node(depth, base_path, None)

all_nodes.append(root_node)

current_node = root_node

#for the while loop, whether we still have nodes to search
searching = True 

while(searching):

    #note that the base_path is based on the current node since this will change as the while loop 
    gobuster_full_url = '{host}:{port}/{base_path}'.format(host=host, port=port, base_path=current_node.base_path)

    #temp file to track results from each run of gobuster and make sure names are 
    # unique for each call to avoid overwrite
    temp_file_name = ""
    temp_file_exists = True
    while(temp_file_exists):    
        temp_file_name = get_random_name_for_tmp_file()
        if os.path.isfile(temp_file_name):
            temp_file_exists = True
        else:
            temp_file_exists = False

    #create the new temp file to use as scratchpad
    open(temp_file_name, "x")

    logging.debug("The temp file name is " + temp_file_name + " for url = " + gobuster_full_url + " at depth = " + str(depth))

    full_command = 'gobuster dir -u {gobuster_full_url} -w {wordlist} {options} -o {tempfile}'.format(gobuster_full_url=gobuster_full_url,
                                                                                                    wordlist=wordlist, options=options, 
                                                                                                    tempfile=temp_file_name)
    
    new_paths = []

    print(full_command)

    os.system(full_command)

    #get the new found results for each file 
    with open(temp_file_name) as file:
        for line in file:
            #ignore empty lines
            if len(line.strip()) == 0 :
                continue
            elif "Status: 301" in line:
                print("Status 301")
                print(line.split(' ', 1)[0])
                current_node.append_child_dir(line.split(' ', 1)[0])
            else:
                print("Not Status 301")
                print(line.replace("\n", ""))
                current_node.append_result(line.replace("\n", ""))

    print("PRINTING CURRENT NODE")
    current_node.print_me()
    
    searching = False





def search(current_node):
    global all_nodes

    






