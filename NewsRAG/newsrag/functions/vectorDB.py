from bson import ObjectId
# import tqdm
from tqdm.auto import tqdm
import numpy as np
from uuid import uuid1
from functions.logger import log_item_id, log_record_id_checker

def upsert_vectorDB(collection, index, text_splitter, embedder, sparse_embedder, batch_article_limit=3, log_processed_path='logs/ids_updated_vecDB.log'):
    """# Define the batch limit (number of articles to process in each batch)
    batch_article_limit = 3
    index=index
    log_processed_path="logs/ids_processed.log"
    """
    # Retrieve processed IDs from logs
    processed_ids = log_record_id_checker(log_processed_path)
    object_ids = [ObjectId(oid) for oid in list(set(processed_ids))]
    query = {'_id': {'$nin': object_ids}}
    projection = {'_id': 1}

    # Main loop for processing articles in batches
    acab = np.arange(0, 1+len(list(collection.find(query, projection))) // batch_article_limit)
    for _ in acab:
        processed_ids = log_record_id_checker(log_processed_path)
        object_ids = [ObjectId(oid) for oid in list(set(processed_ids))]
        query = {'_id': {'$nin': object_ids}}
        results = collection.find(query).limit(batch_article_limit)
        data = list(results)

        if not data:
            break

        texts = []
        metadatas = []
        for record in tqdm(data):
            metadata = {
                'doc_id': str(record['_id']),
            }
            record_texts = text_splitter.split_text(record['text'])
            record_metadatas = [{
                "chunk_no": j, "context": text, **metadata
            } for j, text in enumerate(record_texts)]
            texts.extend(record_texts)
            metadatas.extend(record_metadatas)

        if texts:
            ids = [str(uuid1()) for _ in range(len(texts))]
            embeds = embedder.encode(texts, device='cuda')
            ##############sparse_embeds = generate_sparse_vectors(texts)
            sparse_embeds = sparse_embedder.encode_documents(texts)
            # print(ids) # uncomment to debug
            # print(sparse_embeds) # uncomment to debug
            ##########################vectors = list(zip(ids, sparse_embeds, embeds, metadatas))+
            vectors = []
            for _id, sparse, dense, metadataa in zip(ids, sparse_embeds, embeds, metadatas):
                ### MODIFICARE SPARSE QUI
                # floats = [float(x) for x in list(sparse.values())]
                # sparse = dict({'indices': list(sparse.keys()), 'values': floats})
                # print(sparse)
                vectors.append({
                'id': _id,
                'sparse_values': sparse,
                'values': dense,
                'metadata': metadataa
                })
            # print(vectors) # uncomment to debug
            # Store the processed data in Pinecone
            index.upsert(vectors , async_req=True)# pero mi pare di capire che gli va dato un vettore alla volta allora andrebbe nel for di sopra (e quindi anche senza l'.append)

            for vec in vectors:
                item_id = str(vec['metadata']["doc_id"])
                chunk_no = str(vec['metadata']["chunk_no"])
                # print("item_id", item_id, '\n',
                #       "chunk_no", chunk_no, '\n',
                #       'chunk_id', vec['id'], '\n')
                log_item_id(item_id=item_id, chunk_no=chunk_no, chunk_id=str(vec['id'])
                            , log_file_path=log_processed_path)

        print(f"Total number of articles processed in this batch: {len(data)}")

    print(f"Total number of articles processed: {len(acab) * batch_article_limit -(batch_article_limit-1)}")
    return print("Update complete")  