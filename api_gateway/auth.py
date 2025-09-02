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

from .models import APIKeyInfo, APIKeyStatus, UsageStats, TeamInfo, TeamTier, TeamUsageStats, FeatureFlag


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
            # Teams table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS teams (
                    id TEXT PRIMARY KEY,
                    team_name TEXT NOT NULL,
                    tier TEXT NOT NULL DEFAULT 'basic',
                    enabled_features TEXT NOT NULL DEFAULT '[]',
                    max_results_limit INTEGER DEFAULT 50,
                    rate_limit_multiplier REAL DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    contact_email TEXT
                )
            """)
            
            # API Keys table (updated with team_id)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id TEXT PRIMARY KEY,
                    key_hash TEXT UNIQUE NOT NULL,
                    user_id TEXT NOT NULL,
                    team_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    rate_limit_per_hour INTEGER DEFAULT 1000,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    last_used_at TIMESTAMP,
                    FOREIGN KEY (team_id) REFERENCES teams (id)
                )
            """)
            
            # Usage tracking table (enhanced)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_usage (
                    id TEXT PRIMARY KEY,
                    api_key_id TEXT NOT NULL,
                    team_id TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    service_name TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    response_time_ms INTEGER,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    FOREIGN KEY (api_key_id) REFERENCES api_keys (id),
                    FOREIGN KEY (team_id) REFERENCES teams (id)
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
            
            # Feature flags table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feature_flags (
                    flag_name TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    default_enabled BOOLEAN DEFAULT 0,
                    required_tier TEXT
                )
            """)
            
            # Initialize default feature flags
            self._initialize_default_features(conn)
    
    def _initialize_default_features(self, conn):
        """Initialize default feature flags"""
        default_features = [
            ("medical_extract", "Medical text extraction", True, None),
            ("cpt_search", "CPT code search", True, None),
            ("comprehensive_coding", "Comprehensive medical coding", False, "premium"),
            ("pdf_processing", "PDF document processing", False, "premium"),
            ("bulk_processing", "Bulk document processing", False, "enterprise"),
            ("advanced_analytics", "Advanced usage analytics", False, "enterprise"),
            ("debug_endpoints", "Debug and diagnostic endpoints", False, "internal"),
            ("priority_support", "Priority support and SLA", False, "enterprise")
        ]
        
        for flag_name, description, default_enabled, required_tier in default_features:
            conn.execute("""
                INSERT OR IGNORE INTO feature_flags (flag_name, description, default_enabled, required_tier)
                VALUES (?, ?, ?, ?)
            """, (flag_name, description, default_enabled, required_tier))
    
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
    
    def create_team(self, team_name: str, tier: TeamTier, contact_email: Optional[str] = None, 
                   enabled_features: Optional[List[str]] = None, max_results_limit: int = 50, 
                   rate_limit_multiplier: float = 1.0) -> str:
        """
        Create a new team
        Returns: team_id
        """
        import json
        
        team_id = str(uuid.uuid4())
        enabled_features = enabled_features or []
        
        with self.get_db_connection() as conn:
            conn.execute("""
                INSERT INTO teams (id, team_name, tier, enabled_features, max_results_limit, 
                                 rate_limit_multiplier, contact_email)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (team_id, team_name, tier.value, json.dumps(enabled_features), 
                  max_results_limit, rate_limit_multiplier, contact_email))
        
        return team_id
    
    def generate_api_key(self, team_id: str, user_id: str, rate_limit_per_hour: int = 1000, 
                        expires_days: Optional[int] = None) -> Tuple[str, str]:
        """
        Generate a new API key for a team/user
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
                INSERT INTO api_keys (id, key_hash, user_id, team_id, rate_limit_per_hour, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (key_id, key_hash, user_id, team_id, rate_limit_per_hour, expires_at))
        
        return api_key, key_id
    
    def validate_api_key(self, api_key: str) -> Tuple[bool, Optional[APIKeyInfo]]:
        """
        Validate API key and return key information with team details
        Returns: (is_valid, key_info)
        """
        import json
        
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        with self.get_db_connection() as conn:
            cursor = conn.execute("""
                SELECT ak.id, ak.user_id, ak.team_id, ak.status, ak.rate_limit_per_hour, 
                       ak.created_at, ak.expires_at, ak.last_used_at,
                       t.team_name, t.tier, t.enabled_features, t.max_results_limit, 
                       t.rate_limit_multiplier, t.contact_email, t.created_at as team_created_at
                FROM api_keys ak
                JOIN teams t ON ak.team_id = t.id
                WHERE ak.key_hash = ?
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
            
            # Parse team features
            enabled_features = json.loads(row['enabled_features'])
            
            # Create team info
            team_info = TeamInfo(
                team_id=row['team_id'],
                team_name=row['team_name'],
                tier=TeamTier(row['tier']),
                enabled_features=enabled_features,
                max_results_limit=row['max_results_limit'],
                rate_limit_multiplier=row['rate_limit_multiplier'],
                created_at=datetime.fromisoformat(row['team_created_at']),
                contact_email=row['contact_email']
            )
            
            # Adjust rate limit based on team multiplier
            effective_rate_limit = int(row['rate_limit_per_hour'] * row['rate_limit_multiplier'])
            
            key_info = APIKeyInfo(
                key_id=row['id'],
                user_id=row['user_id'],
                team_id=row['team_id'],
                status=APIKeyStatus(row['status']),
                rate_limit_per_hour=effective_rate_limit,
                created_at=datetime.fromisoformat(row['created_at']),
                expires_at=datetime.fromisoformat(row['expires_at']) if row['expires_at'] else None,
                last_used_at=datetime.fromisoformat(row['last_used_at']) if row['last_used_at'] else None,
                team_info=team_info
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
    
    def log_usage(self, key_id: str, team_id: str, endpoint: str, service_name: str, response_time_ms: int, success: bool, error_message: Optional[str] = None):
        """Log API usage for analytics and monitoring"""
        usage_id = str(uuid.uuid4())
        
        with self.get_db_connection() as conn:
            conn.execute("""
                INSERT INTO api_usage (id, api_key_id, team_id, endpoint, service_name, response_time_ms, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (usage_id, key_id, team_id, endpoint, service_name, response_time_ms, success, error_message))
            
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
    
    def get_team_usage_stats(self, team_id: str) -> TeamUsageStats:
        """Get comprehensive usage statistics for a team"""
        hour_bucket = datetime.now().strftime('%Y-%m-%d-%H')
        
        with self.get_db_connection() as conn:
            # Get team info
            team_cursor = conn.execute("""
                SELECT team_name FROM teams WHERE id = ?
            """, (team_id,))
            team_row = team_cursor.fetchone()
            
            if not team_row:
                raise ValueError(f"Team {team_id} not found")
            
            # Total requests and success metrics
            cursor = conn.execute("""
                SELECT COUNT(*) as total, 
                       SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful,
                       AVG(response_time_ms) as avg_time
                FROM api_usage WHERE team_id = ?
            """, (team_id,))
            totals = cursor.fetchone()
            
            # This hour requests
            cursor = conn.execute("""
                SELECT SUM(request_count) as this_hour
                FROM rate_limits rl
                JOIN api_keys ak ON rl.api_key_id = ak.id
                WHERE ak.team_id = ? AND rl.hour_bucket = ?
            """, (team_id, hour_bucket))
            this_hour = cursor.fetchone()
            
            # Active API keys count
            cursor = conn.execute("""
                SELECT COUNT(*) as active_keys
                FROM api_keys WHERE team_id = ? AND status = 'active'
            """, (team_id,))
            active_keys = cursor.fetchone()
            
            # Most used endpoints
            cursor = conn.execute("""
                SELECT endpoint, COUNT(*) as usage_count
                FROM api_usage 
                WHERE team_id = ?
                GROUP BY endpoint
                ORDER BY usage_count DESC
                LIMIT 5
            """, (team_id,))
            endpoints = [{"endpoint": row["endpoint"], "count": row["usage_count"]} 
                        for row in cursor.fetchall()]
            
            return TeamUsageStats(
                team_id=team_id,
                team_name=team_row['team_name'],
                total_requests=totals['total'] or 0,
                successful_requests=totals['successful'] or 0,
                failed_requests=(totals['total'] or 0) - (totals['successful'] or 0),
                requests_this_hour=this_hour['this_hour'] or 0,
                average_response_time_ms=totals['avg_time'] or 0.0,
                active_api_keys=active_keys['active_keys'] or 0,
                most_used_endpoints=endpoints
            )
    
    def check_feature_access(self, team_info: TeamInfo, feature_name: str) -> bool:
        """Check if a team has access to a specific feature"""
        # First check if feature is explicitly enabled for the team
        if feature_name in team_info.enabled_features:
            return True
            
        # Check feature flag requirements
        with self.get_db_connection() as conn:
            cursor = conn.execute("""
                SELECT default_enabled, required_tier
                FROM feature_flags WHERE flag_name = ?
            """, (feature_name,))
            
            row = cursor.fetchone()
            if not row:
                # Unknown feature - deny by default
                return False
            
            # Check if feature is enabled by default
            if row['default_enabled']:
                return True
            
            # Check tier requirement
            if row['required_tier']:
                required_tier = TeamTier(row['required_tier'])
                tier_hierarchy = {
                    TeamTier.basic: 0,
                    TeamTier.premium: 1,
                    TeamTier.enterprise: 2,
                    TeamTier.internal: 3
                }
                
                return tier_hierarchy.get(team_info.tier, 0) >= tier_hierarchy.get(required_tier, 0)
            
            return False
    
    def get_available_features(self, team_info: TeamInfo) -> List[FeatureFlag]:
        """Get all available features for a team"""
        available_features = []
        
        with self.get_db_connection() as conn:
            cursor = conn.execute("""
                SELECT flag_name, description, default_enabled, required_tier
                FROM feature_flags
            """)
            
            for row in cursor.fetchall():
                feature = FeatureFlag(
                    flag_name=row['flag_name'],
                    description=row['description'],
                    default_enabled=bool(row['default_enabled']),
                    required_tier=TeamTier(row['required_tier']) if row['required_tier'] else None
                )
                
                if self.check_feature_access(team_info, feature.flag_name):
                    available_features.append(feature)
        
        return available_features
    
    def get_team_info(self, team_id: str) -> Optional[TeamInfo]:
        """Get team information by team ID"""
        import json
        
        with self.get_db_connection() as conn:
            cursor = conn.execute("""
                SELECT id, team_name, tier, enabled_features, max_results_limit, 
                       rate_limit_multiplier, created_at, contact_email
                FROM teams WHERE id = ?
            """, (team_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return TeamInfo(
                team_id=row['id'],
                team_name=row['team_name'],
                tier=TeamTier(row['tier']),
                enabled_features=json.loads(row['enabled_features']),
                max_results_limit=row['max_results_limit'],
                rate_limit_multiplier=row['rate_limit_multiplier'],
                created_at=datetime.fromisoformat(row['created_at']),
                contact_email=row['contact_email']
            )
    
    def list_all_teams(self) -> List[TeamInfo]:
        """List all teams in the system"""
        import json
        
        teams = []
        with self.get_db_connection() as conn:
            cursor = conn.execute("""
                SELECT id, team_name, tier, enabled_features, max_results_limit, 
                       rate_limit_multiplier, created_at, contact_email
                FROM teams
                ORDER BY created_at DESC
            """)
            
            for row in cursor.fetchall():
                teams.append(TeamInfo(
                    team_id=row['id'],
                    team_name=row['team_name'],
                    tier=TeamTier(row['tier']),
                    enabled_features=json.loads(row['enabled_features']),
                    max_results_limit=row['max_results_limit'],
                    rate_limit_multiplier=row['rate_limit_multiplier'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    contact_email=row['contact_email']
                ))
        
        return teams


# Global API key manager instance
api_key_manager = APIKeyManager()