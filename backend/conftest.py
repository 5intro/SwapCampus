"""Pytest 根配置 — 注册 PyMySQL 作为 MySQLdb 的替代."""

import pymysql

pymysql.install_as_MySQLdb()
