import pandas as pd
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, XSD

def convert_to_rdf():
    # Load cleaned dataset
    df = pd.read_excel("Data-startupticker.xlsx")
    df.replace("", None, inplace=True)

    # Namespaces
    EX = Namespace("http://example.org/ontology#")
    RES = Namespace("http://example.org/resource/")
    g = Graph()
    g.bind("ex", EX)

    for idx, row in df.iterrows():
        # Startup URI
        startup_uri = URIRef(RES + f"Startup_{idx}")
        g.add((startup_uri, RDF.type, EX.Startup))

        if pd.notnull(row.get("name")):
            g.add((startup_uri, EX.name, Literal(row["name"])))

        if pd.notnull(row.get("foun_date")):
            g.add((startup_uri, EX.foun_date, Literal(str(row["foun_date"]), datatype=XSD.date)))

        if pd.notnull(row.get("hghights")):
            g.add((startup_uri, EX.hghights, Literal(row["hghights"])))

        if pd.notnull(row.get("industry")):
            industry_uri = URIRef(RES + f"{row['industry'].replace(' ', '_')}")
            g.add((industry_uri, RDF.type, EX.Industry))
            g.add((startup_uri, EX.hasIndustry, industry_uri))

        # Location
        if pd.notnull(row.get("canton")):
            canton_uri = URIRef(RES + f"Canton_{row['canton'].replace(' ', '_')}")
            g.add((canton_uri, RDF.type, EX.Canton))
            g.add((startup_uri, EX.hasLocation, canton_uri))
            g.add((canton_uri, EX.name, Literal(row['canton'])))

        if pd.notnull(row.get("city")):
            city_uri = URIRef(RES + f"City_{row['city'].replace(' ', '_')}")
            g.add((city_uri, RDF.type, EX.City))
            g.add((canton_uri, EX.hasCity, city_uri))
            g.add((city_uri, EX.name, Literal(row['city'])))

        # FundingEvent
        if any(pd.notnull(row.get(col)) for col in ["Phase", "type", "amount", "valuation", "round_date", "investor"]):
            fund_uri = URIRef(RES + f"FundingEvent_{idx}")
            g.add((fund_uri, RDF.type, EX.FundingEvent))
            g.add((fund_uri, EX.belongsTo, startup_uri))

            if pd.notnull(row.get("Phase")):
                g.add((fund_uri, EX.Phase, Literal(row["Phase"])))
            if pd.notnull(row.get("type")):
                g.add((fund_uri, EX.type, Literal(row["type"])))
            if pd.notnull(row.get("amount")):
                g.add((fund_uri, EX.amount, Literal(float(row["amount"]), datatype=XSD.decimal)))
            if pd.notnull(row.get("valuation")):
                g.add((fund_uri, EX.valuation, Literal(float(row["valuation"]), datatype=XSD.decimal)))
            if pd.notnull(row.get("round_date")):
                g.add((fund_uri, EX.round_date, Literal(str(row["round_date"]), datatype=XSD.date)))
            if pd.notnull(row.get("investor")):
                g.add((fund_uri, EX.investor, Literal(row["investor"])))

    # Serialize the graph
    g.serialize("startups_graph.ttl", format="turtle")
    print("RDF conversion complete. Output saved to startups_graph.ttl")

if __name__ == "__main__":
    convert_to_rdf() 