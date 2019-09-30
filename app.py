from flask import Flask, flash, redirect, render_template, request, session, abort
app = Flask(__name__)

# GridWiz
import zipfile
from glob import glob
from google_images_download import google_images_download
import re
import os, shutil
default_bundle = 'OriginalMulti.gridset'

def find_replace(bundle, images, updatemsgf=None, safeSearch=False):
    """Read a bundle. Find. Replace. Save bundle."""
    if updatemsgf != None:
        updatemsgf("Extract bundle")
    # 1. Sanity check. Check extension
    # 2. Unzip

    zip_ref = zipfile.ZipFile(bundle, 'r')
    zip_ref.extractall('bundle')
    zip_ref.close()
    
    # 3. Lets now get a file list. THIS IS A TERRIBLE BIT OF code    
    all_files = [y for x in os.walk('bundle/') for y in glob(os.path.join(x[0], '*.png'))]
    
    # Get a list of all starting items, and all similar 'win' items. Put them in a dict
    # WARNING: All pages need to be named something 999 and something 999 win for this to work
    r = re.compile("bundle[/\\\\]Grids[/\\\\]([a-zA-Z]+) ([0-9]+)[/\\\\]([0-9]+)-([0-9]+).jpg")
    startPages = list(filter(r.match, all_files))
    print(startPages)
    no_of_images = len(startPages)
    # 4. Now find the relevant 'win pages'

    if updatemsgf != None:
        updatemsgf("Search & Download")
    pageDict = dict()
    for p in startPages:
        # For each one - find the corresponding 'win' page
        m = re.search("bundle[/\\\\]Grids[/\\\\]([a-zA-Z]+) ([0-9]+)[/\\\\]([0-9]+)-([0-9]+).jpg", p)
        if m:
            pageDict['bundle/Grids/'+ m.group(1)+' '+m.group(2)+'/'+m.group(3)+'-'+m.group(4)+'.jpg'] = 'bundle/Grids/'+m.group(1) + ' '+ m.group(2) + ' win/0-0.jpg'
    
    # 5. Lets get some images from google. 
    
    response = google_images_download.googleimagesdownload()
    absolute_image_paths = response.download({"keywords":images,"limit":no_of_images,"s":">800*600","a":"wide","image_directory":"newImages",'format':'jpg',"print_paths":True,'safe_search':safeSearch})

    # 6. Now lets navigate the folder structure structure looking for each element and replacing it with the right image. 
        
    i = 0

    if updatemsgf != None:
        updatemsgf("Replace & Create new bundle")
    for mainImage, thumbImage in pageDict.items():
        if len(absolute_image_paths[images][i]) > 0:
            print("copy: ", absolute_image_paths[images][i], mainImage)
            shutil.copy(absolute_image_paths[images][i], mainImage)
            shutil.move(absolute_image_paths[images][i], thumbImage)
        i = i + 1   
        
    # 7. Zip it all up.
    new_name = "".join([c for c in images if c.isalpha() or c.isdigit() or c==' ']).rstrip()
    shutil.make_archive('Final.gridset', 'zip', 'bundle/')
    shutil.move('Final.gridset.zip', new_name+'.gridset')
    
def cleanup ():
    shutil.rmtree('bundle/', ignore_errors=True)




@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        searchTerm = request.form['searchStr']
        if 'cue' in request.form:
            cue = True
        else:
            cue = False
        
        if 'safe' in request.form:
            safeSearch = True
        else:
            safeSearch = False
        
        find_replace(default_bundle,searchTerm,None,safeSearch)
        cleanup()
        
    
        return render_template('test.html',posted=True,searchTerm=request.form['searchStr'])
    else:
        return render_template('test.html',posted=False)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)