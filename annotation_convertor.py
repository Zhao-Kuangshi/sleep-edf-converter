# -*- coding: utf-8 -*-
"""
Created on Thu Aug  8 16:25:22 2019

@author: Zhao Kuangshi
"""
import os;
import re;
import sys;
import util;
import json;
import numpy;
import subprocess;
from datetime import datetime, timedelta;
from optparse import OptionParser;

def recognize_edf_or_edfx(path):
    # edf是True，edfx是False 2019-8-12
    out = None;
    if len(util.search_file(path, '.edf')[1]) != 0:
        out = False;
    elif len(util.search_file(path, '.rec')[1]) != 0:
        out = True;
    else:
        raise ValueError('Your input directory seems not a Sleep-EDF or Sleep-EDFx directory.');
    return out;

def get_list(is_sleep_edf, path):
    # 根据所给的路径和数据集类型，得到打好包的文件列表 2019-8-12
    out = None;
    if is_sleep_edf == True:
        rec = util.search_file(path, '0.rec$')[1];
        rec.sort();
        hyp = util.search_file(path, '0.hyp$')[1];
        hyp.sort();
        out = list(zip(rec, hyp));
    else:
        rec = util.search_file(path, '-PSG.edf$')[1];
        rec.sort();
        hyp = util.search_file(path, '-Hypnogram.edf$')[1];
        hyp.sort();
        out = list(zip(rec, hyp));
    return out;
 
def read_header(file):
    # 读取edf的文件头，并以dict返回 2019-8-12
    out = None;
    try:
        result = subprocess.run(['save2gdf', '-JSON', file], stdout = subprocess.PIPE);
        if result.returncode == 0: # 成功运行
            result = result.stdout.decode().replace('\n','').replace('\r','').replace('\t','').replace('inf','0'); # 去除所有的格式化换行符
            out = json.loads(result);
        else:
            raise ValueError('Please check if your input file is of EDF format.');
    except FileNotFoundError:
        raise FileNotFoundError('The required command `save2gdf` seems not appearing in your environment variables. Please check!');
    return out;

def get_start(file):
    # 读取data的开始时间，返回datetime 2019-8-12
    out = None;
    str_start = read_header(file)['StartOfRecording'];
    try:
        out = datetime.strptime(str_start, '%Y-%m-%d %H:%M:%S'); # '1989-04-24 16:13:00' '%Y-%m-%d %H:%M:%S'
    except ValueError:
        out = datetime.strptime(str_start, '%Y-%m-%d 24:%M:%S') + timedelta(days = 1); # '1989-04-24 16:13:00' '%Y-%m-%d %H:%M:%S'
    finally:
        return out;

def time_delta(label_timestamp, start):
    # 计算每个label距离记录开始的相对秒数 2019-8-12
    out = (label_timestamp - start).seconds
    return out;

def get_events(file):
    # 获取所有label，返回一个list。内部均为二元元组，为(时刻, 睡眠状态) 2019-8-12
    # !! 只开发了edfx
    out = [];
    events = read_header(file)['EVENT'];
    for event in events:
        try:
            time = datetime.strptime(event['TimeStamp'], '%Y-%b-%d %H:%M:%S'); # '1989-Apr-25 05:40:00' '%Y-%b-%d %H:%M:%S'
        except:
            time = datetime.strptime(event['TimeStamp'], '%Y-%b-%d 24:%M:%S') + timedelta(days = 1);
        stage = None;
        if re.search('1$', event['Description']) is not None: stage = '1';
        elif re.search('2$', event['Description']) is not None: stage = '2';
        elif re.search('3$', event['Description']) is not None: stage = '3';
        elif re.search('4$', event['Description']) is not None: stage = '4';
        elif re.search('W$', event['Description']) is not None: stage = 'W';
        elif re.search('R$', event['Description']) is not None: stage = 'R';
        elif re.search('M$', event['Description']) is not None: stage = 'M';
        else: stage = 'L';
        out.append((time, stage));
    return out;

def relative(start, events):
    # 计算每个标签相对于开始记录的秒数 2019-8-13
    out = [];
    for event in events:
        out.append([time_delta(event[0], start), event[0], event[1]]);
    out = numpy.array(out);
    return out;

def save(path, ori_fname, array):
    # 保存label的数据为npy格式
    fname = os.path.join(path, os.path.splitext(ori_fname)[0] + '.npy');
    numpy.save(fname, array);

def main():
    # POSIX主运行函数
    usage = 'usage: %prog [options] SOURCE DEST';
    parser = OptionParser(usage = usage);
    (options, args) = parser.parse_args();
    
    if len(args) != 2:
        parser.print_usage(file = sys.stderr);
        sys.stderr.write("\tUse '-h' for help\n\n");
        sys.exit(1);
    else:
        source, dest = args;
        if not(os.path.isdir(source)): raise ValueError('Your source path does not exist or is not a directory.');
        if not(os.path.isdir(dest)): raise ValueError('Your dest path does not exist or is not a directory.');
        data_entries = get_list(recognize_edf_or_edfx(source), source);
        for entry in data_entries:
            rec, hyp = entry;
            start = get_start(os.path.join(source, rec));
            events = get_events(os.path.join(source, hyp));
            array = relative(start, events);
            save(dest, rec, array);
        

if __name__ == '__main__':
    try:
        main();
    except KeyboardInterrupt:
        sys.exit(1);
    