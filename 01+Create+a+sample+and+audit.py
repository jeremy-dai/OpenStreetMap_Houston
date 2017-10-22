
# coding: utf-8

# # This notebook is used to create a samller sample data and audit the data

# In[1]:

# python 2 environment


import xml.etree.cElementTree as ET
from pprint import pprint as pp
import re
from collections import defaultdict

OSM_FILE = "houston_texas.osm" 
SAMPLE_FILE = "sample.osm"


# In[2]:

# Create Sample Data
k = 20 # Parameter: take every k-th top level element

def get_element(osm_file, tags=('node', 'way', 'relation')):
    context = iter(ET.iterparse(osm_file, events=('start', 'end')))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


with open(SAMPLE_FILE, 'wb') as output:
    output.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    output.write('<osm>\n  ')

    # Write every kth top level element
    for i, element in enumerate(get_element(OSM_FILE)):
        if i % k == 0:
            output.write(ET.tostring(element, encoding='utf-8'))

    output.write('</osm>')


# In[4]:

#Check the attributes of nodes and ways
#print them out if they do not following the following format
nom=re.compile(r'^([a-z]|_)+:?([a-z]|_)+$')

def check_attributes(f):
    
    node_attributes = defaultdict(int)
    way_attributes = defaultdict(int)  
    for event, elem in ET.iterparse(f, events=("start",)):
        if elem.tag == "node":
            for tag in elem.iter("tag"): #find children tags
                m = nom.search(tag.attrib['k'].lower())
                if not m:      
                    if tag.get('k') not in node_attributes:
                        node_attributes[tag.get('k')]=1
                    else:   
                        
                        node_attributes[tag.get('k')]+=1
                
        if elem.tag == "way":
            for tag in elem.iter("tag"): #find children tags
                m = nom.search(tag.attrib['k'].lower())
                if not m:   
                    if tag.get('k') not in node_attributes:
                        way_attributes[tag.get('k')]=1
                    else:   
                        way_attributes[tag.get('k')]+=1

    return node_attributes,way_attributes
        
node_attributes,way_attributes = check_attributes(SAMPLE_FILE)


# In[5]:

# print out the weird attributes of nodes
l=sorted( ((v,k) for k,v in node_attributes.iteritems()), reverse=True)
for v,k in l:
    print k,v


# In[6]:

# print out the weird attributes of ways
l=sorted( ((v,k) for k,v in way_attributes.iteritems()), reverse=True)
for v,k in l:
    print k,v


# In[24]:

# check if there are nodes/ways calling for fixes.
def checkfixme(file):
    for _, element in ET.iterparse(file):
        if element.tag == "tag":
            if 'fixme' in element.get('k', None) or 'FIXME' in element.get('k', None) :
                print element.attrib
        
checkfixme(SAMPLE_FILE)


# In[25]:

# checck if the nodes are within the Greater Houston Area
def checklocation():
    lat=set()
    lon=set()
    for _, element in ET.iterparse('sample.osm'):
        if element.tag == "node":
            lat.add(element.get('lat', None) )
            lon.add(element.get('lon', None) )
    return lat,lon
lat,lon=checklocation()

print min(lat),min(lon)
print max(lat),max(lon)


# In[26]:

# check zipcode, left and right
def checkzipcode():
    zip=set()
    for _, element in ET.iterparse('sample.osm'):
        if element.tag == "tag":
            if element.get('k', None)=='tiger:zip_left':
                n=element.get('v', None)
                zip.add(n)           
            if element.get('k', None)=='tiger:zip_right':
                n=element.get('v', None)
                zip.add(n) 
            if element.get('k', None)=='addr:postcode':
                n=element.get('v', None)
                zip.add(n)                 
    problemzip=[]
    for z in zip:
        try:
            z=int(z)
            # if the zipcode is not Houston area, add it into the list
            if z < 77000 or z > 77999:
                problemzip.append(z)
        except:
            problemzip.append(z)
                
    return problemzip

zip=checkzipcode()
pp(zip)


# In[27]:

# check the keys of Tiger GPS data
def checktiger(file):
    tigers=defaultdict(int)
    for _, element in ET.iterparse(file):
        if element.tag == "tag":
            if 'tiger' in element.get('k'):
                tigers[element.get('k')]+=1
    return tigers

tigers=checktiger(SAMPLE_FILE)

l=sorted( ((v,k) for k,v in tigers.iteritems()), reverse=True)
for v,k in l:
    print k,v


# In[28]:

# check if there will be tags of add:street and tiger:name_base under the same way element
def checkaddress(osmfile):
    osm_file = open(osmfile, "r")
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            n=0
            for tag in elem.iter("tag"): #find children tags
                if tag.get('k') =='addr:street' :
                    n+=1
                if tag.get('k') == 'tiger:name_base':
                    n+=1
            if n==2:
                print elem
        
    osm_file.close()

checkaddress(SAMPLE_FILE)


# In[36]:

#Audit Street Names

street_type_re = re.compile(r'\S+\.?$', re.IGNORECASE)
street_type_prefix = re.compile(r'^([NSWE])\s', re.IGNORECASE)
street_type_suffix = re.compile(r'\s([NSWE])$', re.IGNORECASE)
street_type_number = re.compile(r'\s#?\d+[a-zA-Z]?$', re.IGNORECASE)


expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons","Freeway","Highway",'Circle','Speedway','Way','Loop']

mapping = { "Cir": "Circle","Ct": "Court",'Dr':'Drive','Ln':'Lane','Fwy':'Freeway',
           'Pkwy':"Parkway",'Pky':"Parkway","Ave": "Avenue", 'Blvd':'Boulevard','Hwy':'Highway',
           'Rd':'Road','St':'Street','Pl':'Place','Trl':"Trail",'Blvd.':'Boulevard',
           'Byp':'Bypass'}

def update_name(name, mapping):
    subwords=name.split()
    lastword=subwords[-1]
    if lastword in mapping:
        subwords[-1]=mapping[lastword]
        name=' '.join(subwords)
    return name

def audit_street_type(street_types, street_name):
    #if there is a suffix, leave it out
    if street_type_suffix.search(street_name): 
        street_name=(' ').join(street_name.split()[:-1])
    #after moving the suffix, if there is a number, leave it out
    if street_type_number.search(street_name): 
        street_name=(' ').join(street_name.split()[:-1])
    #print out the street name if its updated last word is not in the mapping
    if street_type_re.search(street_name):
        street_name = update_name(street_name,mapping)
        street_type = street_type_re.search(street_name).group()
        if street_type not in expected:
            street_types[street_type].add(street_name)


def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)  #defaultdict
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            iftiger=False
            name_base,name_type,name_direction_prefix,name_direction_suffix=None,None,None,None
            for tag in elem.iter("tag"): #find children tags
                if tag.get('k') == 'addr:street':
                    audit_street_type(street_types, tag.attrib['v'])
                #complie the Tiger GPS name
                if tag.get('k') == 'tiger:name_base':
                    iftiger=True
                    name_base=re.split('[:;]',tag.get('v'))[0] 
                if tag.get('k') == 'tiger:name_type':
                    name_type=re.split('[:;]',tag.get('v'))[0] 
                if tag.get('k') == 'tiger:name_direction_prefix':
                    name_direction_prefix=re.split('[:;]',tag.get('v'))[0] 
                if tag.get('k') == 'tiger:name_direction_suffix':
                    name_direction_suffix=re.split('[:;]',tag.get('v'))[0] 
            if iftiger: 
                streetlist=[name_direction_prefix,name_base,name_type,name_direction_suffix]
                street=' '.join(filter(None,streetlist)) 
                audit_street_type(street_types,street)
    osm_file.close()
    return street_types



if __name__ == '__main__':
    st_types = audit(SAMPLE_FILE)
    pp(dict(st_types))

