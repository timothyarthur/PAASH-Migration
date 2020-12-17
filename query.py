import rdflib
from rdflib import Graph, Literal, RDF, Namespace, URIRef
from rdflib.namespace import SKOS
import csv

g = rdflib.Graph()

g.parse("paash_num_test.ttl", format = 'turtle')
g.bind('skos', SKOS)


#TODO Items with USE that are USE for other items

#Items with USE and rt or nt
#Do not remove rts
#Items whose pref label is an alt label for another AND have NT OR have RT

results = g.query("""SELECT DISTINCT ?target ?targetLabel
	WHERE{
	?target skos:prefLabel ?targetLabel .
	?pref skos:altLabel ?targetLabel .
		FILTER(
			EXISTS{
				?target skos:related ?rt .
			}
			||
			EXISTS{
				?target skos:narrower ?nt .
			}
		)
	}"""
	)

for result in results:
	print(result)

# with open('results.csv', 'w') as file:
# 	writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
# 	writer.writerow(['Item', 'Label', 'altLabel'])
# 	for row in labels:
# 		writer.writerow(row)
