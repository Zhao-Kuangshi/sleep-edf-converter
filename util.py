# -*- coding: utf-8 -*-
"""
Created on Thu Aug  8 16:22:28 2019

@author: Zhao Kuangshi
"""

import os;
import re;

def recursively_search_file(pathname, filename):#参数1要搜索的路径，参数2要搜索的文件名，可以是正则表代式 
    """ Recursively search files in given path by filename regular expressions
    
    
    """
    out = [];
    for root,dirs,files in os.walk(pathname): 
        for file in files: 
            if re.search(filename,file): 
                out.append([root ,file]) ;
    return out;

def search_file(pathname, filename):#参数1要搜索的路径，参数2要搜索的文件名，可以是正则表代式 
    matchedFile =[];
    root,dirs,files = next(os.walk(pathname)); 
    for file in files: 
        if re.search(filename,file): 
            matchedFile.append(file);
    out = [pathname, matchedFile]
    return out;


