
# coding: utf-8

# ## Import csv files into SQL database
# ```
# jeremydai ~ $  cd /Users/jeremydai/Dropbox/Udacity_Project/OpenStreetMap
# jeremydai OpenStreetMap $ sqlite3
# SQLite version 3.13.0 2016-05-18 10:57:30
# Enter ".help" for usage hints.
# Connected to a transient in-memory database.
# Use ".open FILENAME" to reopen on a persistent database.
# sqlite> .open houston.db
# sqlite> .read data_wrangling_schema.sql
# sqlite> .tables
# nodes       nodes_tags  ways        ways_nodes  ways_tags 
# sqlite> .mode csv
# sqlite> .import nodes.csv nodes
# sqlite> .import nodes_tags.csv nodes_tags
# sqlite> .import ways.csv ways
# sqlite> .import ways_nodes.csv ways_nodes
# sqlite> .import ways_tags.csv ways_tags
# 
# ```
# 
# 
# 
# ## Database Query

# In[43]:

import sqlite3
db = sqlite3.connect("/Users/jeremydai/Dropbox/Udacity_Project/OpenStreetMap/houston.db")
c = db.cursor()


# In[44]:

# Number of Nodes
c.execute("select count(*) from nodes;")
c.fetchall()[0][0]


# In[45]:

# Number of Ways
c.execute("select count(*) from ways;")
c.fetchall()[0][0]


# In[47]:

# Number of unique users
query = '''
select count(distinct user.uid) as n
from (select uid from nodes UNION ALL select uid from ways) as user
'''
c.execute(query)
n_users=c.fetchall()[0][0]
print n_users


# In[48]:

query = '''
SELECT u.uid, count(*) as n
FROM (select uid from nodes UNION ALL select uid from ways) as u
GROUP BY uid
ORDER BY n DESC
LIMIT 10;
'''
c.execute(query)
print 'u.uid', 'count'
contri=0
for row in c:
    print row
    contri+=row[1]

print 'Top 10 users contribute', contri,'items of nodes and ways'

query = '''
SELECT count(*) as n
FROM (select uid from nodes UNION ALL select uid from ways) as u
;
'''
c.execute(query)
total=c.fetchall()[0][0]

print 'They,',round(float(1000)/n_users,2), '% of total users, contribute', contri*100/total,'% of nodes and ways'


# In[49]:

#contributions per person histogram
query = '''
SELECT count(*) as n
FROM (select uid from nodes UNION ALL select uid from ways) as u
GROUP BY uid
'''
c.execute(query)

contri_list=[]
for row in c:
    contri_list.append(row[0])


# In[27]:

import matplotlib.pyplot as plt
get_ipython().magic('matplotlib inline')
import seaborn as sns
import numpy as np
sns.distplot(np.log10(contri_list),kde=True)


# In[50]:

query = '''
SELECT value, COUNT(*) as num
FROM nodes_tags
WHERE key='amenity'
GROUP BY value
ORDER BY num DESC
LIMIT 10;
'''
c.execute(query)
for row in c:
    print row


# In[51]:

query = '''
SELECT a.value, COUNT(*) as num
FROM nodes_tags as a, 
    (SELECT DISTINCT(id) FROM nodes_tags WHERE value='place_of_worship') as b
WHERE a.id=b.id
AND a.key='religion'
GROUP BY a.value
ORDER BY num DESC
LIMIT 3;
'''
c.execute(query)
for row in c:
    print row


# In[52]:

query = '''
SELECT a.value, COUNT(*) as num
FROM nodes_tags as a,
    (SELECT DISTINCT(id) FROM nodes_tags WHERE value='restaurant') as b
WHERE a.id=b.id
AND a.key='cuisine'
GROUP BY a.value
ORDER BY num DESC
LIMIT 10;
'''

c.execute(query)
for row in c:
    print row


# In[75]:

# What are in the nodes tags 
query = '''
SELECT DISTINCT key, COUNT(*) as n
FROM nodes_tags 
GROUP BY key
ORDER BY n DESC;
'''
c.execute(query)
for row in c:
    print row


# In[80]:

# What are in the ways tags 
query = '''
SELECT DISTINCT key, COUNT(*) as n
FROM ways_tags 
GROUP BY key
ORDER BY n DESC;
'''
c.execute(query)
for row in c:
    print row


# In[90]:

#Most Popular Leisure types
query = '''
SELECT a.value, COUNT(*) as n
FROM (SELECT key, value FROM nodes_tags UNION ALL SELECT key, value FROM ways_tags) as a
WHERE a.key ='leisure'
GROUP BY a.value
ORDER BY n DESC
Limit 10;
'''

c.execute(query)
for row in c:
    print row


# In[87]:

#Natural?
query = '''
SELECT a.value, COUNT(*) as n
FROM (SELECT key, value FROM nodes_tags UNION ALL SELECT key, value FROM ways_tags) as a
WHERE a.key ='natural'
GROUP BY a.value
ORDER BY n DESC
Limit 10;
'''

c.execute(query)
for row in c:
    print row


# In[ ]:

#Most popular shops
query = '''
SELECT DISTINCT value, COUNT(*) as n
FROM nodes_tags 
WHERE key ='shop'
GROUP BY value
ORDER BY n DESC
Limit 10;
'''
c.execute(query)
for row in c:
    print row


# In[54]:

# top street names
query = '''
SELECT value, COUNT(*) as num
FROM nodes_tags
WHERE key='street'
GROUP BY value
ORDER BY num DESC
LIMIT 1;
'''
c.execute(query)
for row in c:
    print row


# In[72]:

#explore these streets
query = '''
SELECT b.value,a.value,COUNT(a.value) as num
FROM nodes_tags as a,
    (SELECT DISTINCT(id),value FROM nodes_tags WHERE key = 'street' and value IN 
    ('Jason Street','Kingwood Drive')) as b
WHERE (a.key='name' or a.key='building')
AND a.id =b.id
GROUP BY a.value
ORDER BY num DESC;

'''
c.execute(query)
for row in c:
    print row


# In[ ]:

db.close()

