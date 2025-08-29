"""
Complyo Secure Database Service
Connection pooling, caching, and security enhancements
"""

import asyncio
import asyncpg
import redis
import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import hashlib
from dataclasses import dataclass

from config import settings

logger = logging.getLogger(__name__)

@dataclass
class QueryMetrics:
    """Query performance metrics"""
    query_hash: str
    execution_time: float
    rows_affected: int
    timestamp: datetime
    cache_hit: bool = False

class SecureDatabaseService:
    """
    Secure database service with connection pooling, caching, and monitoring
    """
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.redis_client: Optional[redis.Redis] = None
        self.is_connected = False
        self.query_metrics: List[QueryMetrics] = []
        
    async def connect(self) -> bool:
        """
        Initialize secure database connection with pooling
        """
        try:
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                settings.database_url,
                min_size=settings.db_min_connections,
                max_size=settings.db_max_connections,
                command_timeout=30,
                server_settings={
                    'application_name': 'complyo_backend',
                    'timezone': 'UTC'
                }
            )
            
            # Test connection
            async with self.pool.acquire() as conn:
                await conn.execute('SELECT 1')
            
            # Setup Redis for caching
            await self._setup_redis_cache()
            
            self.is_connected = True
            logger.info(f"✅ Database connected with pool: {settings.db_min_connections}-{settings.db_max_connections} connections")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            self.is_connected = False
            return False
    
    async def _setup_redis_cache(self):
        """Setup Redis for query caching"""
        try:
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                db=settings.redis_db,
                decode_responses=True
            )
            
            # Test Redis connection
            self.redis_client.ping()
            logger.info("✅ Redis cache connected")
            
        except Exception as e:
            logger.warning(f"⚠️ Redis cache unavailable: {e}")
            self.redis_client = None
    
    async def disconnect(self):
        """
        Cleanup database connections
        """
        if self.pool:
            await self.pool.close()
            self.is_connected = False
            logger.info("✅ Database pool closed")
    
    def _get_query_hash(self, query: str, params: tuple = None) -> str:
        """
        Generate cache key hash for query
        """
        cache_string = f"{query}:{str(params) if params else ''}"
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    async def _get_cached_result(self, query_hash: str) -> Optional[Any]:
        """
        Get cached query result from Redis
        """
        if not self.redis_client:
            return None
            
        try:
            cached = self.redis_client.get(f"query_cache:{query_hash}")
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache read failed: {e}")
        
        return None
    
    async def _cache_result(self, query_hash: str, result: Any, ttl: int = 300):
        """
        Cache query result in Redis
        """
        if not self.redis_client:
            return
            
        try:
            # Convert result to cacheable format
            if isinstance(result, list):
                cacheable = [dict(row) if hasattr(row, 'keys') else row for row in result]
            elif hasattr(result, 'keys'):
                cacheable = dict(result)
            else:
                cacheable = result
            
            self.redis_client.setex(
                f"query_cache:{query_hash}",
                ttl,
                json.dumps(cacheable, default=str)
            )
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")
    
    @asynccontextmanager
    async def get_connection(self):
        """
        Get database connection from pool with context manager
        """
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        async with self.pool.acquire() as conn:
            yield conn
    
    async def execute_query(
        self, 
        query: str, 
        params: tuple = None, 
        cache_ttl: int = 0
    ) -> bool:
        """
        Execute query (INSERT, UPDATE, DELETE) with optional caching
        """
        start_time = datetime.now()
        query_hash = self._get_query_hash(query, params)
        
        try:
            async with self.get_connection() as conn:
                if params:
                    result = await conn.execute(query, *params)
                else:
                    result = await conn.execute(query)
                
                # Parse rows affected from result string (e.g., "INSERT 0 1")
                rows_affected = int(result.split()[-1]) if result.split()[-1].isdigit() else 0
                
                # Record metrics
                execution_time = (datetime.now() - start_time).total_seconds()
                self._record_query_metrics(query_hash, execution_time, rows_affected)
                
                return rows_affected > 0
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self._record_query_metrics(query_hash, execution_time, 0)
            logger.error(f"Query execution failed: {e}")
            raise
    
    async def fetch_one(
        self, 
        query: str, 
        params: tuple = None, 
        cache_ttl: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch single row with optional caching
        """
        start_time = datetime.now()
        query_hash = self._get_query_hash(query, params)
        cache_hit = False
        
        # Check cache first
        if cache_ttl > 0:
            cached_result = await self._get_cached_result(query_hash)
            if cached_result is not None:
                cache_hit = True
                execution_time = (datetime.now() - start_time).total_seconds()
                self._record_query_metrics(query_hash, execution_time, 1, cache_hit)
                return cached_result
        
        try:
            async with self.get_connection() as conn:
                if params:
                    result = await conn.fetchrow(query, *params)
                else:
                    result = await conn.fetchrow(query)
                
                # Convert to dict
                result_dict = dict(result) if result else None
                
                # Cache result if requested
                if cache_ttl > 0 and result_dict:
                    await self._cache_result(query_hash, result_dict, cache_ttl)
                
                # Record metrics
                execution_time = (datetime.now() - start_time).total_seconds()
                self._record_query_metrics(query_hash, execution_time, 1 if result_dict else 0, cache_hit)
                
                return result_dict
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self._record_query_metrics(query_hash, execution_time, 0, cache_hit)
            logger.error(f"Query fetch_one failed: {e}")
            raise
    
    async def fetch_all(
        self, 
        query: str, 
        params: tuple = None, 
        cache_ttl: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Fetch multiple rows with optional caching
        """
        start_time = datetime.now()
        query_hash = self._get_query_hash(query, params)
        cache_hit = False
        
        # Check cache first
        if cache_ttl > 0:
            cached_result = await self._get_cached_result(query_hash)
            if cached_result is not None:
                cache_hit = True
                execution_time = (datetime.now() - start_time).total_seconds()
                self._record_query_metrics(query_hash, execution_time, len(cached_result), cache_hit)
                return cached_result
        
        try:
            async with self.get_connection() as conn:
                if params:
                    results = await conn.fetch(query, *params)
                else:
                    results = await conn.fetch(query)
                
                # Convert to list of dicts
                result_list = [dict(row) for row in results]
                
                # Cache result if requested
                if cache_ttl > 0:
                    await self._cache_result(query_hash, result_list, cache_ttl)
                
                # Record metrics
                execution_time = (datetime.now() - start_time).total_seconds()
                self._record_query_metrics(query_hash, execution_time, len(result_list), cache_hit)
                
                return result_list
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self._record_query_metrics(query_hash, execution_time, 0, cache_hit)
            logger.error(f"Query fetch_all failed: {e}")
            raise
    
    async def execute_transaction(self, queries: List[tuple]) -> bool:
        """
        Execute multiple queries in a transaction
        """
        try:
            async with self.get_connection() as conn:
                async with conn.transaction():
                    for query, params in queries:
                        if params:
                            await conn.execute(query, *params)
                        else:
                            await conn.execute(query)
                
                logger.info(f"✅ Transaction completed: {len(queries)} queries")
                return True
                
        except Exception as e:
            logger.error(f"❌ Transaction failed: {e}")
            return False
    
    def _record_query_metrics(
        self, 
        query_hash: str, 
        execution_time: float, 
        rows_affected: int, 
        cache_hit: bool = False
    ):
        """
        Record query performance metrics
        """
        metric = QueryMetrics(
            query_hash=query_hash,
            execution_time=execution_time,
            rows_affected=rows_affected,
            timestamp=datetime.now(),
            cache_hit=cache_hit
        )
        
        self.query_metrics.append(metric)
        
        # Keep only last 1000 metrics in memory
        if len(self.query_metrics) > 1000:
            self.query_metrics = self.query_metrics[-1000:]
        
        # Log slow queries
        if execution_time > 1.0 and not cache_hit:
            logger.warning(f"🐌 Slow query detected: {execution_time:.2f}s, hash: {query_hash}")
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get database performance statistics
        """
        if not self.query_metrics:
            return {"message": "No metrics available"}
        
        total_queries = len(self.query_metrics)
        cache_hits = sum(1 for m in self.query_metrics if m.cache_hit)
        avg_execution_time = sum(m.execution_time for m in self.query_metrics) / total_queries
        slow_queries = sum(1 for m in self.query_metrics if m.execution_time > 1.0)
        
        return {
            "total_queries": total_queries,
            "cache_hit_rate": f"{(cache_hits / total_queries) * 100:.1f}%",
            "average_execution_time": f"{avg_execution_time:.3f}s",
            "slow_queries_count": slow_queries,
            "pool_status": {
                "min_size": settings.db_min_connections,
                "max_size": settings.db_max_connections,
                "current_size": self.pool.get_size() if self.pool else 0,
                "idle_connections": self.pool.get_idle_size() if self.pool else 0
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Comprehensive database health check
        """
        try:
            start_time = datetime.now()
            
            # Test basic connectivity
            async with self.get_connection() as conn:
                await conn.execute('SELECT 1')
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Check Redis cache
            redis_status = "connected" if self.redis_client else "disconnected"
            if self.redis_client:
                try:
                    self.redis_client.ping()
                except:
                    redis_status = "error"
            
            return {
                "status": "healthy",
                "database": "connected",
                "response_time": f"{response_time:.3f}s",
                "cache": redis_status,
                "pool_size": self.pool.get_size() if self.pool else 0,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Global database service instance
secure_db = SecureDatabaseService()