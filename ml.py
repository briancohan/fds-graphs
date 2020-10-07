import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


def best_k(df: pd.DataFrame) -> int:

    z = df[['z']]
    max_k = len(df.z.unique())

    scores = []
    for i in range(2, max_k):
        kmeans = KMeans(n_clusters=i).fit(z)
        labels = kmeans.labels_
        scores.append({
            'k': i,
            'score': kmeans.score(z),
            'sil': silhouette_score(z, labels, metric='euclidean'),
        })

    best = scores[0]
    for score in scores[1:]:
        if score['sil'] > best['sil']:
            best = score
        else:
            break

    return best['k']


def get_levels(df: pd.DataFrame, k: int) -> pd.DataFrame:

    kmeans = KMeans(n_clusters=k).fit(df)
    labels = kmeans.labels_

    df['label'] = labels
    mapping = pd.DataFrame({
        'label': df.sort_values('z').label.unique(),
        'level': range(k),
    })
    df = df.merge(mapping, on='label')
    return df[[c for c in df.columns if c != 'label']].drop_duplicates()
