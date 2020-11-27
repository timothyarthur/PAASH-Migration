import rdflib
from rdflib import Graph, Literal, RDF, Namespace, URIRef
from rdflib.namespace import SKOS

g = rdflib.Graph()

g.parse("PAASH.ttl", format = 'turtle')
g.bind('skos', SKOS)

to_remove = g.query("""SELECT DISTINCT ?target
	WHERE{
	?target skos:prefLabel ?targetLabel .
	?pref skos:altLabel ?targetLabel
	}""")

for row in to_remove:
	print(row)

