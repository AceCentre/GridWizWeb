#!/usr/bin/env python

# What this should do
#
# 1. Look through the bundle folder recursively for images
# 2. For each "Grids/folder" find the matching "Grids/folder win" folder
# 3. Look for duplicates in each folder - note the file names will be different. The method below looking at file sizes and hashes is neat
# 4. We want an array of file matches in each directory pair. 
# 5. What we will then later do is replace each match of images with a new image from Google search
#
#  It currently does 1 properly. It doesnt do the rest at all yet.. we need it too!  And then popping into the server app 
#
####

import sys
import os
import hashlib
from glob import glob
import re

# Grid3 Stuff 
def unzip_bundle(bundle):
    zip_ref = zipfile.ZipFile(bundle, 'r')
    zip_ref.extractall('bundle')
    zip_ref.close()
    
def get_all_image_paths(dirpath):
    # 3. Lets now get a file list. THIS IS A TERRIBLE BIT OF code   
    all_files = [y for x in os.walk(dirpath) for y in glob(os.path.join(x[0], '*.png'))]
        
    # Get a list of all starting items, and all similar 'win' items. Put them in a dict
    # WARNING: All pages need to be named something 999 and something 999 win for this to work
    r = re.compile("bundle[/\\\\]Grids[/\\\\]([a-zA-Z]+) ([0-9]+)[/\\\\]([0-9]+)-([0-9]+).png")
    startPages = list(filter(r.match, all_files))
    return startPages   

#Diff finder  
def chunk_reader(fobj, chunk_size=1024):
    """Generator that reads a file in chunks of bytes"""
    while True:
        chunk = fobj.read(chunk_size)
        if not chunk:
            return
        yield chunk


def get_hash(filename, first_chunk_only=False, hash=hashlib.sha1):
    hashobj = hash()
    file_object = open(filename, 'rb')

    if first_chunk_only:
        hashobj.update(file_object.read(1024))
    else:
        for chunk in chunk_reader(file_object):
            hashobj.update(chunk)
    hashed = hashobj.digest()

    file_object.close()
    return hashed


def check_for_duplicates(paths, hash=hashlib.sha1):
    hashes_by_size = {}
    hashes_on_1k = {}
    hashes_full = {}
    
    for path in paths:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                # Only want to search for images 
                extensions = {".jpg", ".png", ".jpeg"}
                if (any(filename.endswith(ext) for ext in extensions)):
                    full_path = os.path.join(dirpath, filename)
                    try:
                        # if the target is a symlink (soft one), this will 
                        # dereference it - change the value to the actual target file
                        full_path = os.path.realpath(full_path)
                        file_size = os.path.getsize(full_path)
                    except (OSError,):
                        # not accessible (permissions, etc) - pass on
                        continue

                    duplicate = hashes_by_size.get(file_size)

                    if duplicate:
                        hashes_by_size[file_size].append(full_path)
                    else:
                        hashes_by_size[file_size] = []  # create the list for this file size
                        hashes_by_size[file_size].append(full_path)

    # For all files with the same file size, get their hash on the 1st 1024 bytes
    for __, files in hashes_by_size.items():
        if len(files) < 2:
            continue    # this file size is unique, no need to spend cpy cycles on it

        for filename in files:
            try:
                small_hash = get_hash(filename, first_chunk_only=True)
            except (OSError,):
                # the file access might've changed till the exec point got here 
                continue

            duplicate = hashes_on_1k.get(small_hash)
            if duplicate:
                hashes_on_1k[small_hash].append(filename)
            else:
                hashes_on_1k[small_hash] = []          # create the list for this 1k hash
                hashes_on_1k[small_hash].append(filename)

    # For all files with the hash on the 1st 1024 bytes, get their hash on the full file - collisions will be duplicates
    for __, files in hashes_on_1k.items():
        if len(files) < 2:
            continue    # this hash of fist 1k file bytes is unique, no need to spend cpy cycles on it

        for filename in files:
            try: 
                full_hash = get_hash(filename, first_chunk_only=False)
            except (OSError,):
                # the file access might've changed till the exec point got here 
                continue

            duplicate = hashes_full.get(full_hash)
            if duplicate:
                print("Duplicate found: %s and %s" % (filename, duplicate))
            else:
                hashes_full[full_hash] = filename

if sys.argv[1:]:
    check_for_duplicates(sys.argv[1:])
else:
    print("Please pass the paths to check as parameters to the script" )