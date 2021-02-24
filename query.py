import rdflib
from rdflib import Graph, Literal, RDF, Namespace, URIRef
from rdflib.namespace import SKOS
import csv

g = rdflib.Graph()

g.parse("paash_num.ttl", format = 'turtle')
g.bind('skos', SKOS)

#Labels
labels = g.query("""SELECT DISTINCT ?target ?targetLabel
	WHERE{
	?target skos:prefLabel ?targetLabel .
	}"""
	)

#Non-preferred terms with URIs
# results = g.query("""SELECT DISTINCT ?target ?targetLabel
# 	WHERE{
# 	?target skos:prefLabel ?targetLabel .
# 	?pref skos:altLabel ?targetLabel .
# 	}"""
# 	)

#Items with USE and rt or nt
#Do not remove rts
#Items whose pref label is an alt label for another AND have NT OR have RT

# results = g.query("""SELECT DISTINCT ?target ?targetLabel
# 	WHERE{
# 	?target skos:prefLabel ?targetLabel .
# 	?pref skos:altLabel ?targetLabel .
# 	?nonPref skos:prefLabel ?targetLabel .
# 	FILTER(!?target = ?nonPref)
# 	}"""
# 	)

# for result in results:
# 	print(result)

# top_level_count = g.query("""SELECT (COUNT(?s) as ?num)
# 	WHERE{
# 	?s skos:topConceptOf ?o .
# }"""
# )
# for item in top_level_count:
# 	print(item)

# notes = g.query("""SELECT ?s ?label ?note
# 	WHERE{
# 	?s skos:prefLabel ?label .
# 	?s skos:scopeNote ?note .
# }"""
# )

with open('labels.csv', 'w') as file:
	writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
	writer.writerow(['Item', 'Label'])
	for row in labels:
		writer.writerow(row)
