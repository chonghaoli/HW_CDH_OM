# -*- coding: utf-8 -*-
"""
Spyder Editor
Transfer Impala lineage log to csv files for neo4j
"""

import json, os

def read_single_file(path):
    print('Reading: '+path+'\n')
    file_object = open(path,'r',encoding='UTF-8')
    contents = file_object.read()  #read contents     

    contents_list=contents.strip('\n').split('\n') #seperate contents into different json
    
    dict_list=[]
    #load each json
    for l in contents_list:
        dict_list.append(json.loads(l))

    file_object.close()
    #dict_list structure:
    #[dict1:{'queryText':string, 'hash':string, 'user':string, 'timestamp':int, 'endTime':int, 
    #'edges':[{'sources':[int, int ...], 'targets':[int, int ,...], 'edgeType':str},{},{}], 
    #'vertices':[{'id':int, 'vertexType':str, 'vertexId':"database.table.column"},{},{}]},
    #dict2:, dict3:, dict4:....]
        
    #one dict means one query or one lineage info
    return dict_list
  

def get_table_column_name(ids):
    db_tb_col=ids.split('.')
    
    if len(db_tb_col)!=3:
        return False
    
    db_tb=db_tb_col[0]+"."+db_tb_col[1]
    col=db_tb_col[2]
    
    return [db_tb,col]


dict_list=[]

rootdir='D:\working\impala_lineage\logs'

list = os.listdir(rootdir) 
for i in range(0,len(list)):
       path = os.path.join(rootdir,list[i])
       if os.path.isfile(path):
           dict_list=read_single_file(path)+dict_list

#table_list,column_list=get_tables_schema_and_columns(dict_list)

print('reading finished\n')
print('Total read '+str(len(dict_list))+' records.\nProcessing begin!')

#csv file schema
column_node='column_id,column_name,table_belong'
table_node='table_id,table_name'
edge_col_col='edge_id,source,target'
edge_tab_col='edge_id,source,target'
edge_tab_tab='edge_id,source,target'

table_column_list={} #{table_name:[column1,column2, ,,,]}
column_lineage_list={} #{column:[column1, column2, ,,,]}
table_lineage_list={} #{table_name:[table1, table2, ,,,]}

id=1

dict_id={} #for recorde the relationship between id and name

#open files
f_column=open('D:\\working\\impala_lineage\\neo4j_column_node.csv','w')
f_table=open('D:\\working\\impala_lineage\\neo4j_table_node.csv','w')
f_edge_cc=open('D:\\working\\impala_lineage\\neo4j_column_column_edge.csv','w')
f_edge_tc=open('D:\\working\\impala_lineage\\neo4j_table_column_edge.csv','w')
f_edge_tt=open('D:\\working\\impala_lineage\\neo4j_table_table_edge.csv','w')


for d in dict_list:
    #create verteies for columns
    for v in d['vertices']:
        #split the database, table, column
        db_tb_col=get_table_column_name(v['vertexId'])
        
        #there must have three part in vertexId
        if not db_tb_col:
            continue
        
        #database.table
        db_tb=db_tb_col[0]
        #column
        col=db_tb_col[1]
                
        #collect table and columns info and create node for them
        if db_tb in table_column_list.keys():
            if col not in table_column_list[db_tb]:
                table_column_list[db_tb].append(col)
                column_node+='\n'+str(id)+','+col+','+db_tb
                dict_id[v['vertexId']]=id
                id+=1

        else:
            table_column_list[db_tb]=[col]
            #column node
            column_node+='\n'+str(id)+','+col+','+db_tb
            dict_id[v['vertexId']]=id
            id+=1
            
            #table node
            table_node+='\n'+str(id)+','+db_tb
            dict_id[db_tb]=id
            id+=1
    
    #write down nodes and clear memory
    f_column.write(column_node)
    f_table.write(table_node)
    column_node=''
    table_node=''
    
    #create edge for column lineages
    for e in d['edges']:
        for source in e['sources']:
            db_tb_col=get_table_column_name(d['vertices'][source]['vertexId'])
            
            #there must have three part in vertexId
            if not db_tb_col:
                continue
            
            #database.table
            db_tb=db_tb_col[0]
            
            #create table lineage if parent table not exist
            if db_tb not in table_lineage_list.keys():
                table_lineage_list[db_tb]=[]
            
            #create column lineage if parent column not exist
            if d['vertices'][source]['vertexId'] not in column_lineage_list.keys():
                #new parent column found
                column_lineage_list[d['vertices'][source]['vertexId']]=[]
                for target in e['targets']:
                    db_tb_col_t=get_table_column_name(d['vertices'][target]['vertexId'])
                    
                    #there must have three part in vertexId
                    if not db_tb_col_t:
                        continue
                    #table name
                    db_tb_t=db_tb_col_t[0]
                    
                    #create table lineage if child table lineage is not exist
                    if db_tb_t not in table_lineage_list[db_tb]:
                        table_lineage_list[db_tb].append(db_tb_t)
                        
                    #create child column lineage
                    column_lineage_list[d['vertices'][source]['vertexId']].append(d['vertices'][target]['vertexId'])
                    
                    #write relationship between columns
                    edge_col_col+='\n'+str(id)+','+str(dict_id[d['vertices'][source]['vertexId']])+','+str(dict_id[d['vertices'][target]['vertexId']])
                    id+=1
            
            else:
                #old parent column found
                for target in e['targets']:
                    db_tb_col_t=get_table_column_name(d['vertices'][target]['vertexId'])
                    #there must have three part in vertexId
                    if not db_tb_col_t:
                        continue
                    #table name
                    db_tb_t=db_tb_col_t[0]
                    
                    #create table lineage if child table lineage is not exist
                    if db_tb_t not in table_lineage_list[db_tb]:
                        table_lineage_list[db_tb].append(db_tb_t)
                        
                    #create column lineage if child column is not exist
                    if d['vertices'][target]['vertexId'] not in column_lineage_list[d['vertices'][source]['vertexId']]:
                        column_lineage_list[d['vertices'][source]['vertexId']].append(d['vertices'][target]['vertexId'])
                        
                        #write relationship between columns
                        edge_col_col+='\n'+str(id)+','+str(dict_id[d['vertices'][source]['vertexId']])+','+str(dict_id[d['vertices'][target]['vertexId']])
                        id+=1
    
    #write down edge and clear memory
    f_edge_cc.write(edge_col_col)
    edge_col_col=''
                
#add relationship between tables
for tf in table_lineage_list.keys():
    for tt in table_lineage_list[tf]:
        edge_tab_tab+='\n'+str(id)+','+str(dict_id[tf])+','+str(dict_id[tt])
        id+=1
f_edge_tt.write(edge_tab_tab)


#add relationship between colum
for tf in table_column_list.keys():
    for colt in table_column_list[tf]:
        edge_tab_col+='\n'+str(id)+','+str(dict_id[tf])+','+str(dict_id[tf+'.'+colt])
        id+=1
f_edge_tc.write(edge_tab_col)
       

f_column.close()
f_table.close()
f_edge_cc.close()
f_edge_tc.close()
f_edge_tt.close()