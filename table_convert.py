from impala.dbapi import connect
import re, sys, os

def to_list(list_tuple,n):
	rs=[]
	for l in range(len(list_tuple)): rs.append(list_tuple[l][n])
	return rs

def get_all_databases(cursor):
	cursor.execute('show databases') #execute a query
	results=cursor.fetchall()
	return to_list(results,0) #fitch the results

def get_tables(cursor, database_name):
	cursor.execute('use '+database_name)
	cursor.execute('show tables')
	results=cursor.fetchall()
	ts=to_list(results,0) #fitch the results
	#table full name
	tsf=[]
	for t in ts:
		tsf.append(database_name+'.'+t)
	return tsf

def get_table_info(cursor, table_name):
	cursor.execute('describe formatted '+table_name)
	results=cursor.fetchall()
	partition_columns=[]
	location=''
	table_type=''
	input_formate=''
	for l in range(len(results)):
		#try find partition info
		if results[l][0]=='# Partition Information':
			for i in range(l+3, len(results)):
				partition_columns.append(results[i][0])
				if results[i+1][0]=='': break
		#try get location info
		if results[l][0]=='Location:           ':
			location=results[l][1]
		#try get table type info
		if results[l][0]=='Table Type:         ':
			table_type=results[l][1]
		#try get table input format
		if results[l][0]=='InputFormat:        ':
			table_format=results[l][1]
		
	return [table_name,partition_columns,location,table_type,table_format]

def partition_statement(partition_columns):
	if len(partition_columns)<1:
		return ''
	else:
		l=",".join(str(i) for i in partition_columns)
		return 'partition('+l+') '
	
def convert_to_parquet(cursor, table_info):
	#whether parquet table
	matchObj1=re.match(r'.*parquet.*',table_info[4].lower())
	matchObj2=re.match(r'.*view.*',table_info[3].lower())
	if matchObj1:
		print table_info[0]+' is already a parquet table, skip.\n'
	elif matchObj2:
		print table_info[0]+' is a virtual view, skip.\n'
	else:
		print 'try convert '+table_info[0]+' to parquet table:'
		
		print 'creating a new same structure parquet table....'
		cursor.execute('create table if not exists '+table_info[0]+'_parquet like '+table_info[0]+' stored as parquet')
		
		#some setting
		cursor.execute('set COMPRESSION_CODEC=snappy')
		cursor.execute('set PARQUET_FILE_SIZE=256m')
		
		print 'getting partition information....'
		p_s=partition_statement(table_info[1])
		
		print 'insertint data into parquet table....'
		cursor.execute('insert overwrite table '+table_info[0]+'_parquet '+p_s+'select * from '+table_info[0])
		
		print 'deletint the original_table hdfs files'
		os.system('hdfs dfs -rm -r -skipTrash '+table_info[2])
		
		print 'dropping the original_table'
		cursor.execute('drop table '+table_info[0])
		
		print 'alter parquet table name back to original_table'
		cursor.execute('alter table '+table_info[0]+'_parquet rename to '+table_info[0])
		print 'convert successed\n'
		

def input_database_list(cursor):
	if len(sys.argv)<2:
		print 'Please input database name seperated by space\nor input: all \n to convert all databases!\n'
		sys.exit()
	elif sys.argv[1].lower()=='all':
		return get_all_databases(cursor)
	else:
		return sys.argv[1:]
		

conn = connect(host='localhost', port=21050) #create connection
cursor = conn.cursor() #create a cursor of this connection

#get input databases
database_list=input_database_list(cursor)
print str(database_list)
table_list=[]

#get all table's full name in all inputed databases
for db in database_list:
	table_list+=get_tables(cursor, db)
print 'table list:\n'+str(table_list)

#doing convert for each table
for t in table_list:
	#table_info is like [table_full_name,partition_columns,location,table_type,table_format]
	table_info=get_table_info(cursor, t)
	print table_info
	
	#try convert table to parquet format
	convert_to_parquet(cursor, table_info)
