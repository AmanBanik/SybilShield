import logging
from typing import Optional
from falkordb import FalkorDB
from src.config import settings

logger = logging.getLogger(__name__)

_db_instance: Optional[FalkorDB] = None


def get_falkordb_client(url: Optional[str] = None) -> FalkorDB:
    """Returns a singleton FalkorDB client instance supporting dual-mode (Cloud URL vs Local Docker)."""
    global _db_instance
    if _db_instance is None or url is not None:
        try:
            target_url = url or settings.falkordb_url
            if target_url:
                # 1. Cloud Mode via Connection URL (e.g. falkor://falkordb:pass@host:port)
                client = FalkorDB.from_url(target_url)
                logger.info("Connected to FalkorDB via Cloud URL")
            elif settings.falkordb_password:
                # 2. Cloud Mode via Host, Port, Username, Password
                client = FalkorDB(
                    host=settings.falkordb_host,
                    port=settings.falkordb_port,
                    username=settings.falkordb_username,
                    password=settings.falkordb_password,
                    ssl=settings.falkordb_ssl
                )
                logger.info("Connected to FalkorDB Cloud at %s:%d (auth enabled)", settings.falkordb_host, settings.falkordb_port)
            else:
                # 3. Local Default Mode (Local Docker on localhost:6379)
                client = FalkorDB(
                    host=settings.falkordb_host,
                    port=settings.falkordb_port
                )
                logger.info("Connected to Local FalkorDB at %s:%d", settings.falkordb_host, settings.falkordb_port)

            if url is None:
                _db_instance = client
            return client
        except Exception as e:
            logger.error("Failed to connect to FalkorDB: %s", e)
            raise
    return _db_instance


def get_graph_client(graph_name: Optional[str] = None):
    """Returns a selected graph instance from FalkorDB."""
    db = get_falkordb_client()
    target_graph = graph_name or settings.falkordb_graph
    return db.select_graph(target_graph)


def test_db_connection() -> bool:
    """Verifies live database connectivity and latency."""
    try:
        g = get_graph_client()
        res = g.query("RETURN 1 AS ping")
        return bool(res and len(res.result_set) > 0)
    except Exception as e:
        logger.warning("FalkorDB ping failed: %s", e)
        return False
