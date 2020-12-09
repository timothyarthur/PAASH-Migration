import rdflib
from rdflib import Graph, Literal, RDF, Namespace, URIRef
from rdflib.namespace import SKOS
import csv

g = rdflib.Graph()

g.parse("paash_num.ttl", format = 'turtle')
g.bind('skos', SKOS)

labels = g.query("""SELECT ?item ?label ?altLabel
	WHERE{
	?item skos:prefLabel ?label .
	OPTIONAL {?item skos:altLabel ?altLabel}
	}
	GROUP BY ?item
	"""
	)

with open('labels.csv', 'w') as file:
	writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
	writer.writerow(['Item', 'Label', 'altLabel'])
	for row in labels:
		writer.writerow(row)

multi = g.query("""SELECT ?item (count(?label) as ?labelCount)
	WHERE{
	?item skos:prefLabel ?label .
	}
	GROUP BY ?item
	""")

with open('num_labels.csv', 'w') as file:
	writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
	writer.writerow(['Item', 'Num_labels'])
	for row in multi:
		writer.writerow(row)