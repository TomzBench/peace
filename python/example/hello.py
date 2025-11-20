"""
Simple Qdrant hello world example that can be called from Rust via PyO3
"""

import logging

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

# Get logger for this module
logger = logging.getLogger(__name__)


def run_qdrant_example() -> str:
    """
    Creates an in-memory Qdrant collection, inserts some vectors, and performs a search.
    Returns a summary of the operations.
    """
    # Create an in-memory Qdrant client
    client = QdrantClient(":memory:")

    collection_name = "hello_qdrant"

    # Create a collection
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=4, distance=Distance.COSINE),
    )
    logger.info("Created collection: %s", collection_name)

    # Insert some sample vectors
    points = [
        PointStruct(id=1, vector=[0.05, 0.61, 0.76, 0.74], payload={"city": "Berlin"}),
        PointStruct(id=2, vector=[0.19, 0.81, 0.75, 0.11], payload={"city": "London"}),
        PointStruct(id=3, vector=[0.36, 0.55, 0.47, 0.94], payload={"city": "Moscow"}),
        PointStruct(id=4, vector=[0.18, 0.01, 0.85, 0.80], payload={"city": "Tokyo"}),
    ]

    client.upsert(collection_name=collection_name, points=points)
    logger.info("Inserted %d points", len(points))

    # Perform a search using query_points (newer API)
    query_vector = [0.2, 0.1, 0.9, 0.7]

    # Use query_points method (newer API)
    search_results = client.query_points(
        collection_name=collection_name, query=query_vector, limit=3
    ).points

    logger.info("Search results for query vector %s:", query_vector)
    for result in search_results:
        city = result.payload.get("city", "Unknown") if result.payload else "Unknown"
        logger.info("  - ID: %s, Score: %.4f, City: %s", result.id, result.score, city)

    # Get collection info
    collection_info = client.get_collection(collection_name=collection_name)
    logger.info("Collection has %d points", collection_info.points_count)

    return (
        f"Successfully completed Qdrant hello world example "
        f"with {len(search_results)} search results"
    )
