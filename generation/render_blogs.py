# -*- coding: utf-8 -*-
"""
Created on Wed May  9 14:17:24 2018

@author: Joe
"""

import jinja2
import os
import datetime

def out_path(path):
    
    file_name = os.path.split(path)[1]
    file_name = file_name.lower()
    file_name = file_name.replace('_', '-')
    
    file_out = os.path.dirname(os.path.dirname(path))
    file_out = os.path.join(file_out, 'blog')
    file_out = os.path.join(file_out, file_name)
    file_out = os.path.splitext(file_out)[0] + '.html'
    return file_out

def load_template(path):
    with open(file_template, 'r') as f:
        template = f.readlines()
    
    return jinja2.Template(''.join(template))

def render_blog(markdown_file, template_file):
    template = load_template(template_file)
    document = doc_set()
    document.read_markdown(markdown_file)
    
    #print(document.__export_html__()[0])
    
    meta = {'date created' : datetime.datetime.isoformat(datetime.datetime.fromtimestamp(os.stat(test_path).st_mtime)),
            'title' : document.docs[0].title,
            'author' : 'Joe McGrath',
            'language' : 'en-GB',
            'type' : 'text',
            }
    print(meta)
    
    return template.render(doc_title = document.docs[0].title,
                           body_text = document.__export_html__()[0]
                           )

file_template = r'D:\Projects\GitHub_Page\josephmcgrath.github.io\generation\templates\blog.html'
file_inputs = r'D:\Projects\GitHub_Page\josephmcgrath.github.io\markdown'
test_path = r'D:\Projects\GitHub_Page\josephmcgrath.github.io\markdown\LiDAR_Data_and_Contours_in_QGIS.md'

with open(out_path(test_path), 'w') as f:
    f.write(render_blog(test_path, file_template))
