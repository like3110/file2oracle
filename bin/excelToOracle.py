#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Usage:解析xlsx文件成指定分隔符的txt文件，通过sqlldr导入oracle

import xlrd
import cx_Oracle
import subprocess
import os
import logging
import argparse
import parseXml

logger = logging.getLogger('python-sqlldr-log')
logger.setLevel(logging.INFO)
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
consoleHandler.setFormatter(formatter)
logger.addHandler(consoleHandler)

script_path=os.path.realpath(__file__)
con_path = os.path.split(script_path)[0]
con_path = os.path.split(con_path)[0]
file_path = con_path+os.sep+'files'
tmp_path = con_path+os.sep+'tmp'
dat_path = con_path+os.sep+'dat'
log_path = con_path+os.sep+'log'

#sqlldr = globalVariables.sqlldr_path

# print script_path
# print con_path
# print file_path
# print tmp_path
# print log_path

#数据转换为字符串
def strs(row):
    values = ""
    for i in range(len(row)):
        if i == len(row) - 1:
            values = values + str(row[i])
        else:
            values = values + str(row[i]) + "@@"
    return values

# 执行sql
def conOracle(jdbcUrl,username,password,table,title):
    conn = cx_Oracle.connect(username, password, jdbcUrl.split('@')[1])
    cursor = conn.cursor()
    #判断表是否存在
    sql_exists = 'select count(1) from user_tables where table_name = \'%s\' ' % table.upper()
    cursor.execute(sql_exists)
    result = cursor.fetchall()
    flag = result[0][0]
    if flag == 0:
        fields = ['"' + i.replace(' ', '') + '"' + ' varchar2(2000)' for i in title]
        fields_str = ', '.join(fields)
        sql_create = 'create table %s (%s)' % (table, fields_str)
        #print sql_create
        cursor.execute(sql_create)
    else:
        print('%s is exists , need not to create !' %table)
    #获取表字段
    sql = 'select column_name||case data_type when \'DATE\' then \' DATE \'\'YYYY-MM-DD HH24:MI:SS\'\'\' else\' char(2000)\' END from user_tab_columns where table_name = \'%s\' order by column_id' % table.upper()
    cursor.execute(sql)
    result = cursor.fetchall()
    return result
    conn.commit()
    cursor.close()
    conn.close()

def rebulididx(jdbcUrl,username,password,table,title):
    conn = cx_Oracle.connect(username, password, jdbcUrl.split('@')[1])
    cursor = conn.cursor()
    #获取失效索引
    sql = 'select \'alter index \'||INDEX_NAME||\' rebuild online\' from User_Indexes where table_name = \'%s\' and status <> \'VALID\'' % table.upper()
    cursor.execute(sql)
    result = cursor.fetchall()
    for idx_sql in result:
      #print(idx_sql[0])
      cursor.execute(idx_sql[0])

#执行cmd并返回结果
def execute(cmd, errorMessage):
    exitCode = os.system(cmd)
    res = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=False)
    result=res.stdout.readlines()
    returnCode=res.wait()
    if exitCode!=0:
      logger.error(errorMessage)
      exit(1)
    return result

'''
--auth-id : 认证ID
--table : DB中的table
--file : 文件名称
'''

#数据库配置信息
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--auth-id' , dest = 'authID' , required=True)
    parser.add_argument('--table' , dest = 'table' , required=True)
    parser.add_argument('--file', dest='file', required=True)
    parser.add_argument('--mode', dest='mode', required=True)

    args = parser.parse_args()
    authID = args.authID
    table = args.table
    filename = args.file
    mode = args.mode
    #[jdbcURL,username,password]
    auth = parseXml.paramsInfo(authID)
    if auth and len(auth) == 3:
        jdbcUrl = auth[0]
        username = auth[1]
        password = auth[2]
    else:
        logger.error('No certification ID found !')
        exit(1)

    # 解析xlsx文件
    data = xlrd.open_workbook(file_path+os.sep+filename)
    sheet1 = data.sheet_by_index(0)
    title = sheet1.row_values(0)
    #sheet页对应表名
    for i in data.sheet_names():
        sheet = data.sheet_by_name(i)
        nrows = sheet.nrows  # 行数
        ncols = sheet.ncols  # 列数
        # 剔除非正常记录的sheet页
        if nrows == 1 and ncols == 1:
            exit(0)
        results = conOracle(jdbcUrl, username, password, table, title)
        # 打印出行数列数
        print("sheets:", table, "rows:", nrows, "cols:", ncols)
        # 拼接ctl文件
        datafile = open(dat_path + os.sep + table + ".dat", "w",encoding= 'utf8')  # 文件读写方式是覆盖写入
        arr = []
        for r in results:
            arr.append(r[0])
        fields_str = ', '.join(arr)
        #print "fields_str",fields_str
        cli = 'LOAD DATA CHARACTERSET UTF8 INFILE \'%s\' INTO TABLE %s APPEND  FIELDS TERMINATED BY \'@@\' trailing nullcols ' \
              '(%s) ' % (dat_path+os.sep+table+".dat",table,fields_str)
        ctlfile = open(tmp_path+os.sep+"ctl"+os.sep+table+".ctl", "w")
        ctlfile.writelines(cli)
        ctlfile.close()
        for ronum in range(1, nrows):
            row = sheet.row_values(ronum)
            values = strs(row) # 调用函数，将行数据拼接成字符串
            datafile.writelines(values.replace('\n','') + "\n") #将字符串写入新文件
        datafile.close() # 关闭写入的文件

        #执行导入
        errorMessage = 'fail job'
        #需要装有oracle的服务器执行
        #print(bytes.decode(password))
        if mode == 'normal':
            cmd = 'sqlldr %s/%s@%s control=%s log=%s bad=%s errors=9999999 rows=10000 bindsize=2000000000 readsize=2000000000 parallel=true' \
                        %(username,(bytes.decode(password)),jdbcUrl.split('@')[1],
                          tmp_path+os.sep+"ctl"+os.sep+table+".ctl",
                          log_path+os.sep+table+".log",
                          log_path+os.sep+"bad"+os.sep+table+".bad")
            print(cmd)
            result = execute(cmd, errorMessage)
        elif mode == 'direct':
            cmd = 'sqlldr %s/%s@%s control=%s log=%s bad=%s errors=9999999 bindsize=2000000000 readsize=2000000000 parallel=true skip_index_maintenance=TRUE direct=TRUE' \
                  % (username, (bytes.decode(password)), jdbcUrl.split('@')[1],
                     tmp_path + os.sep + "ctl" + os.sep + table + ".ctl",
                     log_path + os.sep + table + ".log",
                     log_path + os.sep + "bad" + os.sep + table + ".bad")
            print(cmd)
            result=execute(cmd, errorMessage)
            rebulididx(jdbcUrl, username, password, table, title)

if __name__ == '__main__':
    main()
