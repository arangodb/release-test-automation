""" API tests test data helper """

import random


def create_documents_with_vector_field():
    docs = []
    for i in range(1, 1001):
        doc = dict()
        doc["vector"] = [random.random() for _ in range(20)]
        doc["val"] = i
        doc["nonStoredValue"] = i * 2
        doc["stringField"] = "type_A" if i % 3 == 0 else "type_B" if i % 3 == 1 else "type_C"
        doc["boolField"] = i % 2 == 0
        doc["arrayField"] = [i % 5, i % 7]
        doc["objectField"] = {"nested": i % 4, "category": "first_half" if i < 1000 / 2 else "second_half"}
        doc["floatField"] = i + 0.5
        docs.append(doc)
    return docs
