#!/bin/bash
dbname=$1
tblname=$2
destdbname=$3
desttblname=$4
sqlfile=${dbname}.${tblname}.sql
echo -e "create table if not exists ${destdbname}.${desttblname}(" > ${sqlfile}
impala-shell -i 10.126.134.22:25003 -d "${dbname}" -q "show create table ${tblname}" -B|sed "s/COMMENT '.\+'//g" |grep -v TBLPROPERTIES|grep -v "LOCATION 'hdfs" |grep -v "CREATE TABLE"  >> ${sqlfile}
