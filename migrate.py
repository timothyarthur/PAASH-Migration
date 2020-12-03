from rdflib import Graph, Literal, RDF, Namespace, URIRef
from rdflib.namespace import SKOS
import re

test = False

#These lines will not be used to generate terms
#Rather, they will be written from this list to review.txt for manual review
#Will be filtered based on flags defined below
lines_to_review = []

#Generating graph and defining namespace
g = Graph()
g.bind('skos', SKOS)
paash = Namespace("paash#")

#Generating SKOS Concept Scheme as root node of graph
scheme_label = 'Provincial Archives of Alberta Subject Headings'
scheme_uri = paash['paash']
g.add((scheme_uri, RDF.type, SKOS.ConceptScheme))
g.add((scheme_uri, SKOS.prefLabel, Literal(scheme_label, lang='en')))

def get_uri(label):
	uri = g.value(None, SKOS.prefLabel, Literal(label, lang='en'), any=False)
	return uri

#Returns a URI generated based on label
def gen_uri(label):
	uri = get_uri(label)
	if not uri:
		uri = label.replace(' ', '_').lower()
		uri = paash[uri]
	return uri

# Returns the preferred label for URIs already in the graph
def get_label(uri):
	try:
		label = g.preferredLabel(uri)[0][1]
	except:
		label = None
	return label

def flag_for_review(item, flags):
	return any(substring in item.lower() for substring in flags) and not '~' in item

# Formats and appends line to review list
def add_review(item_label, parent_label=None):
	if parent_label == None:
		lines_to_review.append(f'{item_label}\n\n')
	else:
		lines_to_review.append(f'{parent_label}\n\t{item_label}\n\n')

#Removes relational prefix from label
def clean_label(label):
	if '~' in label:
		label = label.replace('~', '')
	if label.startswith('USE'):
		label = label.replace('USE ', '')
	elif label.startswith('NT'):
		label = label.replace('NT ', '')
	elif label.startswith('RT'):
		label = label.replace('RT ', '')
	elif label.startswith('UF'):
		label = label.replace('UF ', '')
	return label

# Constructs heading nodes and adds to graph
# Assigns basic properties possessed by all headings:
# i.e. type, preferred label and membership in the overall PAASH scheme
def construct_heading_node(label):
	uri = gen_uri(label)

	if not get_label(uri):
		g.add((uri, RDF.type, SKOS.Concept))
		g.add((uri, SKOS.prefLabel, Literal(label, lang='en')))
		g.add((uri, SKOS.inScheme, scheme_uri))

	return uri

# Constructs subheading and adds to graph, by calling the constructor appropriate given its relation to its parent
def construct_subheading(item, parent, check_flags = True):
	uri = None

	review_flags = ['[', 'subdiv', 'under', 'name', 'specific', 'when']

	if '--' in item and not flag_for_review(item, review_flags) and check_flags:
		construct_precoordinated(item)

	if item.startswith('USE'):
		review_flags = ['[', 'subdiv', 'under', 'name', 'NT', 'RT', 'specific', 'when']
		if flag_for_review(item, review_flags) and check_flags:
			add_review(item, get_label(parent))
		else:
			uri = construct_use(item, parent)

	elif item.startswith('NT'):
		review_flags = ['[', 'subdiv', 'under', 'name', 'RT', 'USE', 'specific']
		if flag_for_review(item, review_flags) and check_flags:
			add_review(item, get_label(parent))
		else:
			uri = construct_nt(item, parent)

	elif item.startswith('RT'):
		review_flags = ['[', 'subdiv', 'under', 'name', 'NT', 'USE', 'specific']
		if flag_for_review(item, review_flags) and check_flags:
			add_review(item, get_label(parent))
		else:
			uri = construct_rt(item, parent)

	elif item.startswith('UF'):
		review_flags = ['[', 'subdiv', 'under', 'name', 'RT', 'NT', 'specific']
		if flag_for_review(item, review_flags) and check_flags:
			add_review(item, get_label(parent))
		else:
			uri = construct_uf(item, parent)

	else:
		review_flags = ['[', 'subdiv', 'under', 'name']
		if flag_for_review(item, review_flags) and check_flags:
			add_review(item, get_label(parent))
		else:
			uri = construct_note(item, parent)

	return uri

def construct_precoordinated(coord_label):
	coord_label = clean_label(coord_label)
	coord_uri = get_uri(coord_label)

	if not coord_uri:
		split_labels = coord_label.rsplit(' -- ', 1)
		broader_label = split_labels[0]

		broader_uri = construct_heading_node(broader_label)
		narrower_uri = construct_heading_node(coord_label)

		g.add((broader_uri, SKOS.narrower, narrower_uri))
		g.add((narrower_uri, SKOS.broader, broader_uri))
		print(broader_uri, narrower_uri)

# Constructs subheadings with the USE relation
# When a subheading has a USE statement, it indicates that its parent is a non-preferred heading
# We add the parent's label as an alternative label so that the subheading specified by the USE statement can be accessed by those seeking the non-preferred version
# Non-preferred headings are kept in the graph to maintain relational integrity while generating new nodes, but we will later remove them
def construct_use(item, parent):
	parent_label = get_label(parent)
	item = clean_label(item)
	item_uri = construct_heading_node(item)

	g.add((item_uri, SKOS.altLabel, Literal(parent_label, lang='en')))

	return item_uri

# Constructs subheadings with the RT relation
# Applies the relation to and from the item and 'parent'
# (The usage of 'parent' here indicates only the hierarchy specified in the input, the item and 'parent' need not be related hierarchically in the data structure as such)
def construct_rt(item, parent):
	parent_label = get_label(parent)

	item = clean_label(item)
	item_uri = construct_heading_node(item)

	g.add((item_uri, SKOS.related, parent))
	g.add((parent, SKOS.related, item_uri))

	return item_uri

# Constructs subheadings with the NT relation
# Also applies the inverse, BT relation
def construct_nt(item, parent):
	parent_label = get_label(parent)
	item = clean_label(item)
	item_label = parent_label + ' -- ' + item

	item_uri = construct_heading_node(item_label)

	g.add((parent, SKOS.narrower, item_uri))
	g.add((item_uri, SKOS.broader, parent))

	return item_uri

# Constructs subheadings with the UF relation
# As the inverse of USE, UF effectively designates the item as a non-preferred alternative label for the parent
# This way the preferred term can be accessed via the non-preferred term
def construct_uf(item, parent):
	parent_label = get_label(parent)
	item = clean_label(item)
	g.add((parent, SKOS.altLabel, Literal(item, lang='en')))

# Constructs notes
# All subheadings without a valid prefix are assumed to be notes
def construct_note(item, parent):
	#Detect type of note?
	parent_label = get_label(parent)
	item = clean_label(item)
	g.add((parent, SKOS.note, Literal(item, lang='en')))

#Loading and parsing plaintext input, then storing terms a nested dictionary data structure
#End result is a dictionary of dictionaries of lists
if test:
	file_name = 'PAASH2020-test.txt'
else:
	file_name = 'PAASH2020-explicit.txt'

with open(file_name, 'r') as file:
	text = file.read()

lines = [line for line in text.split('\n')]

#Generates a dictionary of dictionaries of lists as an intermediate hierarchical representation of the vocabulary, to be used to generate the graph
#Strings for first order headings are keys for the below dictionary, whose values are a subdictionary whose keys are the second-order headings below them
#Finally, the values for this subdicitonary are a list of third-order headings under the second-order headings
struct = {}

n = 0

while n < len(lines):
	key = ''
	line = lines[n].strip()
	if len(line)>0 and not line.startswith('#'):
		key = line
		dic = {}
		n+=1
		while n < len(lines) - 1 and lines[n].startswith('\t'):
			vals = []
			key_2 = lines[n].strip()
			if lines[n+1].startswith('\t\t'):
				while n < len(lines) and lines[n+1].startswith('\t\t'):
					vals.append(lines[n+1].strip())
					n+=1
			dic[key_2] = vals
			n+=1
		struct[key] = dic
	n+=1

#Iterating through data structure to generate URIs and construct the graph
#To maintain the data structure during this process, will generate nodes for non-preferred headings as well as preferred
#These will be removed in a later step
#Subheadings are assigned to a new dictionary for storage, using the newly-generated URIs for the parent headings as keys
uri_dict = {}
# try:
	# This loop generates the first level of headings, i.e. those not preceded by tabs in the input file
for key in struct:
	#Headings containing these flags as substrings will not be used to generate nodes
	#Rather, they will be written to review.txt for manual review
	review_flags = ['[', 'subdivision', 'under', 'name']
	if flag_for_review(key, review_flags):
		add_review(key)
	#Constructing headings that do not contain the flags
	else:
		values = struct[key]

		key = clean_label(key)
		key_uri = construct_heading_node(key)

		#Storing subheadings under the newly-generated URI
		uri_dict[key_uri] = values

# This loop generates the second level of headings, i.e. those preceded by one tab in the input file
# Once again, dictionary keys for these headings are replaced with their newly generated URIs
# Their own subheadings are stored in a list under this new key
for key in uri_dict:
	sub_uri_dict = {}
	for sub_key in uri_dict[key]:
		values = uri_dict[key][sub_key]

		item = sub_key
		parent = key

		sub_uri = construct_subheading(item, parent)

		sub_uri_dict[sub_uri] = values
	uri_dict[key] = sub_uri_dict

# Finally, generating the third level of headings
# These are not stored under their URIs, as all nodes have now been generated, and the purpose of the intermediate dictionary is served
for key in uri_dict:
	sub_uri_dict = {}
	for sub_key in uri_dict[key]:
		for value in uri_dict[key][sub_key]:
			item = value
			parent = sub_key
			sub_uri = construct_subheading(item, parent)

# except Exception as e:
# 	print(e)
# 	print(f'Failed to generate:\n{get_label(parent)}\n\t{item}')

#Remove non-preferred headings from graph
#Uncomment after ensuring that flags are comprehensive
to_remove = g.query("""SELECT DISTINCT ?target
	WHERE{
	?target skos:prefLabel ?targetLabel .
	?pref skos:altLabel ?targetLabel .
	}""")

for row in to_remove:
	uri = row[0]
	g.remove((uri, None, None))
	g.remove((None, None, uri))

#SPARQL query to select all top concepts, i.e. concepts with no broader concepts
#These are then specified in the graph as skos:topConcepts of the scheme
top_concepts = g.query("""SELECT DISTINCT ?s
	WHERE{
		?s rdf:type skos:Concept .
			FILTER (
				!EXISTS {
					?s skos:broader ?o .
			}
		)
	}
	""")

for item in [row[0] for row in top_concepts]:
	uri = item
	g.add((uri, SKOS.topConceptOf, scheme_uri))
	g.add((scheme_uri, SKOS.hasTopConcept, uri))


#Writing the output to the indicated file, in the indicated RDF serialization format
if test:
	rdf_file = 'test.ttl'
else:
	rdf_file = 'PAASH.ttl'

g.serialize(destination=rdf_file, format='turtle')

#Writing lines for review to the indicated file in human-readable format
if test:
	review_file_name = 'review_test.txt'
else:
	review_file_name = 'review.txt'

with open(review_file_name, 'w') as review_file:
	review_file.writelines(lines_to_review)
