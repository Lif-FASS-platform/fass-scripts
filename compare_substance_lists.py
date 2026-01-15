import json

import requests

from substances import substance_ids_list

ADDRESS = "https://cms.fass.dev.dev.fass.se/api/patient/substance/"


res = requests.get(ADDRESS)

# QUERY
# select distinct(ts.substance_id) from substance.t_substance ts
# 	join medicinalproduct.t_substance ts2 on ts.substance_id = ts2.substance_id
# 	join medicinalproduct.t_medicinal_product tmp on ts2.npl_id = tmp.npl_id
# where ts.type = 'MOTHER'
# 	and tmp.is_authorized = true
# 	and (ts2.applicable_for = 'HUMAN' or ts2.applicable_for = 'BOTH')


# Load the JSON data
substances = res.json()

# Extract substance IDs from the JSON data
json_substance_ids = [substance["substanceId"] for substance in substances]

# Find substance IDs not present in both lists
missing_in_json = [
    sub_id for sub_id in substance_ids_list if sub_id not in json_substance_ids
]
missing_in_list = [
    sub_id for sub_id in json_substance_ids if sub_id not in substance_ids_list
]

print("Substance IDs only in the search service:\n", missing_in_json)
print("Substance IDs only in the frontend:\n", missing_in_list)
