"""
API Gateway Authentication System
Handles API key validation, rate limiting, and usage tracking
"""

import hashlib
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
import sqlite3
import os
from contextlib import contextmanager

from .models import APIKeyInfo, APIKeyStatus, UsageStats


class APIKeyManager:
    """
    API Key management system with SQLite backend
    Handles key generation, validation, rate limiting, and usage tracking
    """
    
    def __init__(self, db_path: str = "api_keys.db"):
        """Initialize API key manager with SQLite database"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with required tables"""
        with self.get_db_connection() as conn:
            # API Keys table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id TEXT PRIMARY KEY,
                    key_hash TEXT UNIQUE NOT NULL,
                    user_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    rate_limit_per_hour INTEGER DEFAULT 1000,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    last_used_at TIMESTAMP
                )
            """)
            
            # Usage tracking table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_usage (
                    id TEXT PRIMARY KEY,
                    api_key_id TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    service_name TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    response_time_ms INTEGER,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    FOREIGN KEY (api_key_id) REFERENCES api_keys (id)
                )
            """)
            
            # Rate limiting tracking table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rate_limits (
                    api_key_id TEXT NOT NULL,
                    hour_bucket TEXT NOT NULL,
                    request_count INTEGER DEFAULT 1,
                    PRIMARY KEY (api_key_id, hour_bucket),
                    FOREIGN KEY (api_key_id) REFERENCES api_keys (id)
                )
            """)
    
    @contextmanager
    def get_db_connection(self):
        """Get database connection context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def generate_api_key(self, user_id: str, rate_limit_per_hour: int = 1000, expires_days: Optional[int] = None) -> Tuple[str, str]:
        """
        Generate a new API key for a user
        Returns: (api_key, key_id)
        """
        key_id = str(uuid.uuid4())
        api_key = f"vcp_{uuid.uuid4().hex[:24]}"  # vcp = vectorized cpt
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        expires_at = None
        if expires_days:
            expires_at = datetime.now() + timedelta(days=expires_days)
        
        with self.get_db_connection() as conn:
            conn.execute("""
                INSERT INTO api_keys (id, key_hash, user_id, rate_limit_per_hour, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (key_id, key_hash, user_id, rate_limit_per_hour, expires_at))
        
        return api_key, key_id
    
    def validate_api_key(self, api_key: str) -> Tuple[bool, Optional[APIKeyInfo]]:
        """
        Validate API key and return key information
        Returns: (is_valid, key_info)
        """
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        with self.get_db_connection() as conn:
            cursor = conn.execute("""
                SELECT id, user_id, status, rate_limit_per_hour, created_at, expires_at, last_used_at
                FROM api_keys 
                WHERE key_hash = ?
            """, (key_hash,))
            
            row = cursor.fetchone()
            if not row:
                return False, None
            
            # Check if key is active
            if row['status'] != 'active':
                return False, None
            
            # Check if key has expired
            if row['expires_at']:
                expires_at = datetime.fromisoformat(row['expires_at'])
                if datetime.now() > expires_at:
                    return False, None
            
            key_info = APIKeyInfo(
                key_id=row['id'],
                user_id=row['user_id'],
                status=APIKeyStatus(row['status']),
                rate_limit_per_hour=row['rate_limit_per_hour'],
                created_at=datetime.fromisoformat(row['created_at']),
                expires_at=datetime.fromisoformat(row['expires_at']) if row['expires_at'] else None,
                last_used_at=datetime.fromisoformat(row['last_used_at']) if row['last_used_at'] else None
            )
            
            return True, key_info
    
    def check_rate_limit(self, key_id: str, rate_limit: int) -> Tuple[bool, int]:
        """
        Check if API key has exceeded rate limit
        Returns: (within_limit, current_hour_requests)
        """
        hour_bucket = datetime.now().strftime('%Y-%m-%d-%H')
        
        with self.get_db_connection() as conn:
            # Get current hour request count
            cursor = conn.execute("""
                SELECT request_count FROM rate_limits 
                WHERE api_key_id = ? AND hour_bucket = ?
            """, (key_id, hour_bucket))
            
            row = cursor.fetchone()
            current_count = row['request_count'] if row else 0
            
            if current_count >= rate_limit:
                return False, current_count
            
            # Increment request count
            conn.execute("""
                INSERT OR REPLACE INTO rate_limits (api_key_id, hour_bucket, request_count)
                VALUES (?, ?, COALESCE((SELECT request_count FROM rate_limits WHERE api_key_id = ? AND hour_bucket = ?), 0) + 1)
            """, (key_id, hour_bucket, key_id, hour_bucket))
            
            return True, current_count + 1
    
    def log_usage(self, key_id: str, endpoint: str, service_name: str, response_time_ms: int, success: bool, error_message: Optional[str] = None):
        """Log API usage for analytics and monitoring"""
        usage_id = str(uuid.uuid4())
        
        with self.get_db_connection() as conn:
            conn.execute("""
                INSERT INTO api_usage (id, api_key_id, endpoint, service_name, response_time_ms, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (usage_id, key_id, endpoint, service_name, response_time_ms, success, error_message))
            
            # Update last_used_at
            conn.execute("""
                UPDATE api_keys SET last_used_at = CURRENT_TIMESTAMP WHERE id = ?
            """, (key_id,))
    
    def get_usage_stats(self, key_id: str) -> UsageStats:
        """Get usage statistics for an API key"""
        hour_bucket = datetime.now().strftime('%Y-%m-%d-%H')
        
        with self.get_db_connection() as conn:
            # Total requests
            cursor = conn.execute("""
                SELECT COUNT(*) as total, 
                       SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful,
                       AVG(response_time_ms) as avg_time
                FROM api_usage WHERE api_key_id = ?
            """, (key_id,))
            totals = cursor.fetchone()
            
            # This hour requests
            cursor = conn.execute("""
                SELECT COALESCE(request_count, 0) as this_hour
                FROM rate_limits WHERE api_key_id = ? AND hour_bucket = ?
            """, (key_id, hour_bucket))
            this_hour = cursor.fetchone()
            
            return UsageStats(
                total_requests=totals['total'] or 0,
                requests_this_hour=this_hour['this_hour'] if this_hour else 0,
                successful_requests=totals['successful'] or 0,
                failed_requests=(totals['total'] or 0) - (totals['successful'] or 0),
                average_response_time_ms=totals['avg_time'] or 0.0
            )
    
    def deactivate_key(self, key_id: str) -> bool:
        """Deactivate an API key"""
        with self.get_db_connection() as conn:
            cursor = conn.execute("""
                UPDATE api_keys SET status = 'inactive' WHERE id = ?
            """, (key_id,))
            return cursor.rowcount > 0
    
    def list_user_keys(self, user_id: str) -> List[APIKeyInfo]:
        """List all API keys for a user"""
        with self.get_db_connection() as conn:
            cursor = conn.execute("""
                SELECT id, user_id, status, rate_limit_per_hour, created_at, expires_at, last_used_at
                FROM api_keys WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            
            keys = []
            for row in cursor.fetchall():
                keys.append(APIKeyInfo(
                    key_id=row['id'],
                    user_id=row['user_id'],
                    status=APIKeyStatus(row['status']),
                    rate_limit_per_hour=row['rate_limit_per_hour'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    expires_at=datetime.fromisoformat(row['expires_at']) if row['expires_at'] else None,
                    last_used_at=datetime.fromisoformat(row['last_used_at']) if row['last_used_at'] else None
                ))
            
            return keys


# Global API key manager instance
api_key_manager = APIKeyManager()