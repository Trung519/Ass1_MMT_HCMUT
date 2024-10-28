add = '1.1.1.1:8080'
add2 = '1.1.1.1:8081'
add3 = '1.1.1.1:8082'

my_set = {add, add2, add3}


# for item in my_set:
#     print(item)

peers = {
    "info_hash": [{'id': "12", "port": 12}],
    "info_hash2": [{'id': "12", "port": 12}],
}


for item in peers.items():
    print(item[1])
