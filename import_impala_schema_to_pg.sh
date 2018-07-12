#!/bin/bash
dbname=$1
tblname=$2
desttblname=$3
if [ $# -eq 4 ]; then
	distmode=$4
	diststr=`echo "${distmode}"|grep "-" && echo "distribute by replication" || echo  "distribute by hash(${distmode})"`
fi
sqlfile=$dbname.$tblname.sql

echo -e "create table if not exists ${desttblname} (" > $sqlfile
impala-shell -i 10.126.134.22:25003 -d "$dbname" -q "show create table $tblname" -B |egrep -v "CREATE TABLE|TBLPROPERTIES|LOCATION 'hdfs|STORED AS |WITH SERDEPROPERTIES"|sed "s/COMMENT '.\+'//g"|sed  's/ STRING/ text/g' |sed 's/ DOUBLE/ float8/g'|sed 's/ TINYINT/ smallint/g' >> $sqlfile
echo "${diststr}" >>  ${sqlfile}
#echo  "${diststr}"
