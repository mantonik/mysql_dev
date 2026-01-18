Create a central location for delete data from multiple database 
Configuration table support.c_sup_cleanup_config 
login path to this db, 
oracle_tns_name
DB_Schema
Table_name
where condition - RETENSION 
retension_days
groups
slave_enable_disable
delete_limit

main scritp will connect to this db pull list of each confiugred cleanup base on group configuration 

select list of tables to cleanup with defined group value

create delete statement  using DB_schema, table_name and where_condition 

in where condition we will have a keyword RETENSION - replace that keyword with RETENSION_DAYS value 

Sample 
DB_SCHEMA: APP
table_name: trx
where_condition:   where trx_date < date_ad(curdate(), interval - RETENSION days)
RETENSION_DAYS:  300

final delete statement 
    delete from app.trx where trx_date < date_ad(curdate(), interval - 300 days)

connect to mysql using login-path and exeucte delete stament in limits, repeat this multiple times until we delete all records.
