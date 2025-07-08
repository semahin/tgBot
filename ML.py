from sentence_transformers import SentenceTransformer, util
import numpy as np

model = SentenceTransformer("paraphrase-MiniLM-L6-v2")

semantic_query = "разработка программного обеспечения, создание сайта, внедрение ИТ-систем, сопровождение"
query_embedding = model.encode(semantic_query, convert_to_tensor=True)

# Фильтрация по смыслу
def filter_semantically(df, column="Наименование закупки", threshold=0.5):
    texts = df[column].fillna("").tolist()
    embeddings = model.encode(texts, convert_to_tensor=True)
    query_embedding = model.encode(semantic_query, convert_to_tensor=True)

    scores = util.cos_sim(query_embedding, embeddings)[0]

    bool_mask = (scores > threshold).cpu().numpy()  # вот это важно

    filtered = df[bool_mask].copy()
    filtered["semantic_score"] = scores[bool_mask].cpu().numpy()

    return filtered.sort_values("semantic_score", ascending=False)
