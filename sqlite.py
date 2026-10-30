import sqlite3

## connect to the sqlite3 db

connection = sqlite3.connect(
    database='student.db'
)


cursor = connection.cursor()

table_info = """
 create table STUDENT (NAME VARCHAR(25), CLASS VARCHAR(30),
 SECTION VARCHAR(25), MARKS INT
 )
"""

cursor.execute(table_info)


cursor.execute('''Insert into STUDENT values('Bimbo', 'UI/UX', 'A', 98)''')
cursor.execute('''Insert into STUDENT values('John', 'Data Science', 'B', 90)''')
cursor.execute('''Insert into STUDENT values('Vitinha', 'Data Science', 'A', 86)''')
cursor.execute('''Insert into STUDENT values('Jacob', 'AI', 'C', 78)''')
cursor.execute('''Insert into STUDENT values('Bokun', 'Graphics desing', 'A', 32)''')

# Display all records

print('Inserted records are: \n')
data = cursor.execute('''select * from STUDENT''')
for row in data.fetchall():
    print(row)


connection.commit()
connection.close()# I_amVictor@