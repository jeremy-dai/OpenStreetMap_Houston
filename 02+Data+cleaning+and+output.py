
# coding: utf-8

# # This notebook is used to transform the data and output into SQL

# In[2]:

import csv
import codecs
import cerberus
import schema
import re
import xml.etree.cElementTree as ET
from pprint import pprint as pp

#OSM_PATH = "houston_texas.osm"
OSM_PATH = "sample.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']



# In[3]:

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
END_NUMBER = re.compile(r'[0-9]$')

# This function is used to read tags
def tag_value(tag,element):
    '''
    - id: the top level node id attribute value
    - key: the full tag "k" attribute value if no colon is present or the characters after the colon if one is.
    - value: the tag "v" attribute value
    - type: either the characters before the colon in the tag "k" value or "regular" if a colon
        is not present.
    ''' 
    m = PROBLEMCHARS.search(tag.attrib['k'])
    n = END_NUMBER.search(tag.attrib['k'])
    att={}
    if (not m) and (not n): # Ignore the tag if the "k" value contains problematic characters
        att['id']=element.attrib['id']
        att['value']=tag.attrib['v']
        k=tag.attrib['k'].lower() # change the k" value to all lower cases
        '''
        if the tag "k" value contains a ":" 
            the characters before the ":" should be set as the tag type
            the characters after the ":" should be set as the tag key
        if there are additional ":" in the "k" value 
            ignore them and keep as part of the tag key. For example:
        '''
        m = LOWER_COLON.search(k)
        if m:
            words=k.split(':',1)
            att['type']=words[0]
            att['key']=words[1]
        else:
            att['key']=k
            att['type']='regular'
        '''
        The tiger:zip_left will read the leftmost zipcode
        The tiger:zip_right will read rightmose zipcode
        '''
        if att['key']=='zip_left':
            try:
                att['value']=int(att['value'])
                # if the zipcode is not for Houston area, print it out
                if att['value'] < 77000 or att['value'] > 77999:
                    print 'This zipcode is out of Greater Houston Area: ' + att['value'] 
            except ValueError:
                att['value']=re.split('[:;]',att['value']) [0]
                
        if att['key']=='zip_left':
            try:
                att['value']=int(att['value'])
                # if the zipcode is not for Houston area, print it out
                if att['value'] < 77000 or att['value'] > 77999:
                    print 'This zipcode is out of Greater Houston Area: ' + att['value'] 
            except ValueError:
                att['value']=re.split('[:;]',att['value']) [0]
        '''
        If the tag value is 'man_made':
        Change the key to 'amenity', type to 'man_made'
        '''
        if att['key']=='man_made':
            att['key']='amenity'
            att['type']='man_made'
        return att


# In[3]:

street_type_re = re.compile(r'\S+\.?$', re.IGNORECASE)
street_type_prefix = re.compile(r'^([NSWE])\s', re.IGNORECASE)
street_type_suffix = re.compile(r'\s([NSWE])$', re.IGNORECASE)
street_type_number = re.compile(r'\s#?\d+[a-zA-Z]?$', re.IGNORECASE)

mapping = { "Cir": "Circle","Ct": "Court",'Dr':'Drive','Ln':'Lane','Fwy':'Freeway',
           'Pkwy':"Parkway",'Pky':"Parkway","Ave": "Avenue", 'Blvd':'Boulevard','Hwy':'Highway',
           'Rd':'Road','St':'Street','Pl':'Place','Trl':"Trail",'Blvd.':'Boulevard',
           'Byp':'Bypass'}

direction={'N':'North','S':'South','W':'West','E':'East'}

def update_name(name, mapping):
    #if the name begins with a abbreviated direction, correct it
    p = street_type_prefix.search(name)
    if p:
        subwords=name.split()
        subwords[0]=direction[subwords[0]]
        name=' '.join(subwords)
        
    s = street_type_suffix.search(name)
    n = street_type_number.search(name)
    #If the name ends with a dirction or a number, check the second last word
    if s or n:
        #if the name ends with a abbreviated direction, correct it
        d=None #abbrevated direction
        number=None #ending number
        if s:
            subwords=name.split()
            d=subwords[-1]
            d=direction[d]
            name=' '.join(subwords[0:-1])
        #after removing the suffix, checking the number
        if street_type_number.search(name):
            number = name.split()[-1]
            name=(' ').join(name.split()[:-1])
        m=street_type_re.search(name)
        if m:
            subwords=name.split()
            lastword=subwords[-1]
            if lastword in mapping:
                subwords[-1]=mapping[lastword]
                name=' '.join(subwords)
        if number:
            name=' '.join([name,number])
        if d:
            name=' '.join([name,d])
    else:
        if street_type_re.search(name):
            subwords=name.split()
            lastword=subwords[-1]
            if lastword in mapping:
                subwords[-1]=mapping[lastword]
                name=' '.join(subwords)
    return name


# In[1]:

def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags=[]

    # YOUR CODE HERE
    if element.tag == 'node':
        valid = True # If we should output this element
        if len(element):
            for tag in element.iter('tag'):
                if tag.attrib['k'].lower()=='fixme':
                    valid=False #discard the node with fixme attributes
                    break 
                att=tag_value(tag,element)
                if not att: # Ignore the tag if the "k" value contains problematic characters
                    continue
                if att['key']=='street':
                    oldvalue=att['value']
                    att['value']=update_name(oldvalue,mapping)           
                tags.append(att)
        if valid:           
            for field in node_attr_fields:
                node_attribs[field]=element.attrib[field]
            return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        valid = True # If we should output this element
        if len(element):
            n=0
            for elem in element:
                if elem.tag=='tag':
                    if elem.attrib['k']=='fixme':
                        valid=False #discard the way with fixme attributes
                        break
                    att=tag_value(elem,element)
                    if not att: # Ignore the tag if the "k" value contains problematic characters
                        continue
                    if att['key']=='street':
                        oldvalue=att['value']
                        att['value']=update_name(oldvalue,mapping) 
                    tags.append(att)
                '''
                create way_nodes
                - id: the top level element (way) id
                - node_id: the ref attribute value of the nd tag
                - position: the index starting at 0 of the nd tag
                '''
                if elem.tag=='nd':
                    att={}
                    att['id']=element.attrib['id']
                    id_number=element.attrib['id']
                    att['node_id']=elem.attrib['ref']
                    att['position']=n
                    n+=1
                    way_nodes.append(att)  
        if valid:
            '''
            If both Tiger GPS address tag and name tag exist, ignore the Tiger GPS tag
            If only Tiger GPS address tag exists, compile the street name
            ''' 
            name_base,name_type,name_direction_prefix,name_direction_suffix=None,None,None,None
            ifname = False
            iftiger= False
            remove=[] # This list collects the name tags from Tiger GPS
            for i in tags:
                k = i['key'] 
                if k == 'name':
                    ifname= True
                elif k == 'name_base':
                    name_base=re.split('[:;]',i['value'])[0] 
                    iftiger= True
                    remove.append(i)
                elif k == 'name_type':
                    name_type=re.split('[:;]',i['value'])[0] 
                    remove.append(i)
                elif k == 'name_direction_prefix':
                    name_direction_prefix=re.split('[:;]',i['value'])[0] 
                    remove.append(i)
                elif k == 'name_direction_suffix':
                    name_direction_suffix=re.split('[:;]',i['value'])[0] 
                    remove.append(i)
            if (not ifname) and iftiger: 
                '''
                when there is only Tiger GPS street name:
                we compile the seperate items,
                update the name and set the tpye to 'tiger'
                '''
                att={}
                att['id']=id_number
                att['key']='street'
                streetlist=[name_direction_prefix,name_base,name_type,name_direction_suffix]
                att['value']=' '.join(filter(None,streetlist))
                att['value']= update_name(att['value'],mapping) 
                att['type']='tiger'
                tags.append(att)
            if ifname and iftiger: 
                '''
                when there are both name and Tiger GPS street name:
                remove the Tiger GPS items,
                change the name tag to street tag and update the name
                '''
                for i in remove:
                    tags.remove(i)
                for i in tags:
                    if i['key'] == 'name':
                        i['key'] = 'street' 
                        i['type']= 'addr' 
                        i['value']= update_name(i['value'],mapping)                       
            for field in way_attr_fields:
                way_attribs[field]=element.attrib[field]
            return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# In[5]:

def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """
    Utilize a schema and validation library to ensure the transformed data is in the correct format
    Raise ValidationError if element does not match schema
    """
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """
    Write each data structure to the appropriate .csv files
    Extend csv.DictWriter to handle Unicode input
    """

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file,          codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file,          codecs.open(WAYS_PATH, 'w') as ways_file,          codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file,          codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])                   

if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. 
    process_map(OSM_PATH, validate= False)


# In[ ]:



