import pandas as pd
from sqlalchemy import create_engine
import re
import sqlite3
# Chemins vers tes fichiers
file_crunchbase = "Data-crunchbase.xlsx"
file_startupticker = "Data-startupticker.xlsx"
sqlite_db = "startups_clean.db"

# === Map des feuilles à traiter : nom_table -> (fichier, feuille_données, feuille_description)
sheets_to_process = {
    "startupticker_companies": (file_startupticker, "Companies", "Company description"),
    "startupticker_deals": (file_startupticker, "Deals", "Deal description"),
    "crunchbase_organizations": (file_crunchbase, "organizations", "organization description"),
    "crunchbase_funding_rounds": (file_crunchbase, "funding rounds", "funding round description")
}


def clean_string(s):
    if isinstance(s, str):
        s = s.lower()
        #s = re.sub(r'\s+', '', s)
        #s = re.sub(r'[^a-z0-9]', '', s)
    return s

def convert_columns_based_on_type(df1, df2):
    # On parcourt les colonnes de df1
    for col_name in df1.columns:
        # Chercher le type attendu dans df2 pour la colonne actuelle
        type_row = df2[df2['Data field'] == col_name]
        
        # Si un type est trouvé pour cette colonne, on effectue la conversion
        if not type_row.empty:
            expected_type = type_row['Data type'].values[0]  # Récupérer le type attendu

            # Conversion en fonction du type attendu
            if expected_type == 'int':
                df1[col_name] = pd.to_numeric(df1[col_name], errors='coerce')  # Conversion en int
            elif expected_type == 'char'or expected_type == 'char (classification)' :
                df1[col_name] = df1[col_name].astype(str)
                
                df1[col_name] = df1[col_name].apply(clean_string)  
            elif expected_type == 'bool':
                df1[col_name] = df1[col_name].astype(bool)  # Conversion en bool
            elif expected_type == 'numeric' : 
                df1[col_name] = df1[col_name].astype(float)
            elif expected_type == 'date' : 
                df1[col_name]= pd.to_datetime(df1[col_name], errors='coerce')
            elif expected_type == 'list' : 
                df1[col_name] = df1[col_name].astype(str)
            else:
                print(f"Type non pris en charge pour {col_name}: {expected_type}")
    df1 = df1.drop_duplicates()
    return df1

engine = create_engine(f"sqlite:///{sqlite_db}")

for table_name, (file, data_sheet, desc_sheet) in sheets_to_process.items():
    print(f"🔄 Traitement de {data_sheet} -> table `{table_name}`")

    df_data = pd.read_excel(file, sheet_name=data_sheet)
    df_desc = pd.read_excel(file, sheet_name=desc_sheet)

    

    df_data = convert_columns_based_on_type(df_data, df_desc)
    df_data = df_data.dropna(how="all").drop_duplicates()

    df_data.to_sql(table_name, con=engine, if_exists="replace", index=False)
if __name__ == "__main__":
    # Chemin vers ta base de données SQLite
    sqlite_db = 'startups_clean.db'

    # Connexion à la base de données SQLite
    conn = sqlite3.connect(sqlite_db)
    cursor = conn.cursor()

    # Exemple de requête SQL : récupérer toutes les lignes d'une table appelée "utilisateurs"
    cursor.execute("SELECT * FROM startupticker_companies Join startupticker_deals on startupticker_deals.Company = startupticker_companies.Title  WHERE Funded = False")

    # Récupérer tous les résultats de la requête
    resultats = cursor.fetchall()

    # Afficher les résultats
    for ligne in resultats:
        print(ligne)

    # Fermer la connexion
    conn.close()