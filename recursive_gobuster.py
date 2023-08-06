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
        self.children_nodes = []
    def append_child_dir(self, child_dir):
        self.children_dirs.append(child_dir)
    def append_child_node(self, child_node):
        self.children_nodes.append(child_node)
    def append_result(self, result):
        self.results.append(result)
    def __str__(self):
        return f"Depth = {self.depth} Base Path = {self.base_path} Results = {self.results} Children Dirs = {self.children_dirs}"
    def print_me(self):
        print("Base path = " + self.base_path)
        print("Printing Children Dirs")
        for child in self.children_dirs:
            print(child)
        print("Printing Results")
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


if os.path.isfile(outfile):
    print("ERROR OUTPUT FILE " + outfile + " ALREADY EXISTS")


f = open(outfile, "x")
f.close()

# f = open(outfile, "a")


base_url = '{host}:{port}'.format(host=host, port=port)


#track the depth of the search
depth = 0

#a tree like structure of the search will get created which helps for printing 
#a usefully formatted output file...
all_nodes = []

root_node = Node(depth, base_path, None)

current_node = root_node


import time

def search(current_node):
    global all_nodes
    global base_url
    global outfile

    time.sleep(1)

    #note that the base_path is based on the current node since this will change as the while loop 
    gobuster_full_url = '{host}:{port}/{base_path}'.format(host=host, port=port, base_path=current_node.base_path)
    gobuster_full_url = gobuster_full_url.replace("//", "/")

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

    print(full_command)

    os.system(full_command)

    #get the new found results for each file 
    with open(temp_file_name) as file:
        for line in file:
            #ignore empty lines
            if len(line.strip()) == 0 :
                continue
            elif "Status: 301" in line:
                current_node.append_child_dir(line.split(' ', 1)[0])
            else:
                current_node.append_result(line.replace("\n", ""))

    

    
    if len(current_node.children_dirs) == 0 and len(current_node.results) == 0:
        return
    
    f = open(outfile, "a")


    f.write("\t"*current_node.depth + base_url + current_node.base_path + "\n")

    for result in current_node.results:
        f.write("\t"*(current_node.depth + 1) + result + "\n")

    f.close()

    #only append nodes that have some form of result
    all_nodes.append(current_node)

    if len(current_node.children_dirs) == 0:
        return
    
    #only search deeper if there are actually nested directories to search
    for dir in current_node.children_dirs:
        new_node = Node(current_node.depth + 1, current_node.base_path + dir, current_node)
        current_node.append_child_node(new_node)
        search(new_node)



search(current_node)









# def write_to_file(file_to_write_to, current_node):

#     global base_url

#     file_to_write_to.write("\t"*current_node.depth + base_url + current_node.base_path + "\n")

#     for result in current_node.results:
#         file_to_write_to.write("\t"*(current_node.depth + 1) + result + "\n")

#     for node in current_node.children_nodes:
#         write_to_file(file_to_write_to, node)


# write_to_file(f, root_node)
    

    







