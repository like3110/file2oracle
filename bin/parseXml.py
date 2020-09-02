#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import logging
import passwdUtil

try:
    import xml.etree.cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)-8s %(filename)s %(funcName)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger("ParseXmlCfg")
logger.setLevel(logging.INFO)

FILE_PATH = os.path.realpath(__file__)
BIN_PATH = os.path.split(FILE_PATH)[0]
BIN_PATH = os.path.split(BIN_PATH)[0]
# 数据库参数集配置
# DB_CONFIG_PATH = ROOT_PATH + '\conf\dbParams'
CONFIG_PATH = BIN_PATH + os.sep + 'conf'

DB_CONFIG_PATH = CONFIG_PATH + os.sep + 'dbParams'

db_cfg_file = DB_CONFIG_PATH + os.sep + 'db_config.xml'


# 打印日志
def debug_print(s, flg=0):
    if flg == 1:
        logger.info(s)
    elif flg == 2:
        print(s)
    else:
        pass


'''
解析数据库参数集 根目录为：C:/Users/fcvan/PycharmProjects/pythonLearning/file2oracle/conf/dbParams
格式为：
<?xml version='1.0' encoding='utf-8'?>
<configuration>
  <auth id="ORACLE_SCOTT_LOCALHOST">
    <jdbc-url>jdbc:oracle:thin:@127.0.0.1:1521:orcl</jdbc-url>
    <username>scott</username>
    <password>MZAApK9H3csUMe2qkrO8bQmKKcvy8jEF1CEd4/BoUYK45SYhd5KdncttT1v5rAmNk84laPwY9XnfTNSmOfMf1w==</password>
  </auth>
 </configuration>
'''


def paramsInfo(authDbId):
    tree = etree.parse(db_cfg_file)
    elem = tree.find('auth[@id="%s"]' % authDbId)
    jdbcURL = elem.findtext('jdbc-url')
    username = elem.findtext('username')
    password = passwdUtil.decrypt(elem.findtext('password'))
    elem = [jdbcURL, username, password]
    return elem


if __name__ == '__main__':
    auth = paramsInfo('ORACLE187')
    print(auth)
    '''
    if auth:
        jdbcURL = auth.findtext('jdbc-url')
        username = auth.findtext('username')
        password = PasswordUtil.decrypt(auth.findtext('password'))
        print 'jdbcURL ' + auth[0]
        print 'username ' + auth[1]
        print 'password ' + auth[2]
    '''
