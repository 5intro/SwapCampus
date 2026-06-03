"""SwapCampus 配置包.

初始化时注册 PyMySQL 作为 MySQLdb 的替代。
必须在 Django 尝试加载数据库后端之前执行。
"""

import pymysql

pymysql.install_as_MySQLdb()
