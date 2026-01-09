"""PostgreSQL authentication plugin with JWT tokens."""

import hashlib
from datetime import datetime, timedelta
from typing import Optional

from app.plugins.base import AuthenticationPlugin
from app.jwt_handler import get_jwt_handler

# Try to import psycopg2
try:
    import psycopg2
    from psycopg2 import pool
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


class PostgreSQLAuthPlugin(AuthenticationPlugin):
    """Authentication plugin using PostgreSQL for user storage with JWT tokens.
    
    Requires: pip install psycopg2-binary
    
    This plugin stores users in PostgreSQL and uses stateless JWT tokens
    for authentication. Token revocation is tracked in PostgreSQL for
    logout functionality across distributed instances.
    """
    
    # SQL statements for table creation
    CREATE_USERS_TABLE = '''
        CREATE TABLE IF NOT EXISTS {users_table} (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(64) NOT NULL,
            role VARCHAR(50) DEFAULT 'user',
            email VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            active BOOLEAN DEFAULT TRUE
        )
    '''
    
    CREATE_REVOKED_TOKENS_TABLE = '''
        CREATE TABLE IF NOT EXISTS {revoked_tokens_table} (
            id SERIAL PRIMARY KEY,
            token_hash VARCHAR(64) UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            revoked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    '''
    
    CREATE_INDEXES = '''
        CREATE INDEX IF NOT EXISTS idx_{revoked_tokens_table}_token_hash ON {revoked_tokens_table}(token_hash);
        CREATE INDEX IF NOT EXISTS idx_{revoked_tokens_table}_expires ON {revoked_tokens_table}(expires_at);
        CREATE INDEX IF NOT EXISTS idx_{users_table}_username ON {users_table}(username);
        CREATE INDEX IF NOT EXISTS idx_{users_table}_email ON {users_table}(email);
    '''
    
    def __init__(self, config: dict):
        """Initialize the PostgreSQL authentication plugin.
        
        Args:
            config: Plugin configuration with:
                - host: PostgreSQL host (default: localhost)
                - port: PostgreSQL port (default: 5432)
                - database: Database name (default: openmark)
                - user: Database user (default: openmark)
                - password: Database password (required)
                - users_table: Users table name (default: auth_users)
                - tokens_table: Active tokens table name (default: auth_tokens)
                - token_expiry_hours: Token validity duration (default: 24)
                - pool_min_conn: Minimum pool connections (default: 1)
                - pool_max_conn: Maximum pool connections (default: 10)
                - create_tables: Auto-create tables on startup (default: True)
                
                Alternative connection:
                - connection_string: Full PostgreSQL connection URI
        """
        super().__init__(config)
        
        if not PSYCOPG2_AVAILABLE:
            raise ImportError(
                "PostgreSQL authentication plugin requires psycopg2. "
                "Install it with: pip install psycopg2-binary"
            )
        
        # Connection parameters
        self.connection_string = config.get('connection_string')
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 5432)
        self.database = config.get('database', 'openmark')
        self.user = config.get('user', 'openmark')
        self.password = config.get('password')
        
        # Table names
        self.users_table = config.get('users_table', 'auth_users')
        self.revoked_tokens_table = config.get('revoked_tokens_table', 'revoked_tokens')
        
        # Token configuration
        self.token_expiry_hours = config.get('token_expiry_hours', 24)
        
        # Connection pool settings
        self.pool_min_conn = config.get('pool_min_conn', 1)
        self.pool_max_conn = config.get('pool_max_conn', 10)
        
        # Auto-create tables
        self.create_tables = config.get('create_tables', True)
        
        # Initialize connection pool
        self._pool = None
        self._connect()
    
    def _connect(self):
        """Establish connection pool to PostgreSQL."""
        try:
            if self.connection_string:
                self._pool = pool.ThreadedConnectionPool(
                    self.pool_min_conn,
                    self.pool_max_conn,
                    self.connection_string
                )
            else:
                self._pool = pool.ThreadedConnectionPool(
                    self.pool_min_conn,
                    self.pool_max_conn,
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password
                )
            
            if self.create_tables:
                self._setup_tables()
                
        except psycopg2.Error as e:
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}")
    
    def _get_connection(self):
        """Get a connection from the pool."""
        return self._pool.getconn()
    
    def _put_connection(self, conn):
        """Return a connection to the pool."""
        self._pool.putconn(conn)
    
    def _setup_tables(self):
        """Create necessary tables and indexes."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # Create users table
                cur.execute(self.CREATE_USERS_TABLE.format(
                    users_table=self.users_table
                ))
                
                # Create revoked tokens table for JWT blacklist
                cur.execute(self.CREATE_REVOKED_TOKENS_TABLE.format(
                    revoked_tokens_table=self.revoked_tokens_table
                ))
                
                # Create indexes
                for statement in self.CREATE_INDEXES.format(
                    users_table=self.users_table,
                    revoked_tokens_table=self.revoked_tokens_table
                ).split(';'):
                    if statement.strip():
                        cur.execute(statement)
                
                conn.commit()
                
                # Create default users if none exist
                cur.execute(f"SELECT COUNT(*) FROM {self.users_table}")
                if cur.fetchone()[0] == 0:
                    self._create_default_users(cur)
                    conn.commit()
                    
        finally:
            self._put_connection(conn)
    
    def _create_default_users(self, cursor):
        """Create default admin and user accounts."""
        default_users = [
            ('admin', self._hash_password('admin123'), 'admin', 'admin@example.com'),
            ('user', self._hash_password('user123'), 'user', 'user@example.com')
        ]
        
        cursor.executemany(
            f'''INSERT INTO {self.users_table} 
                (username, password_hash, role, email) 
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (username) DO NOTHING''',
            default_users
        )
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _hash_token(self, token: str) -> str:
        """Hash a token for storage in revocation list.
        
        Args:
            token: JWT token to hash
            
        Returns:
            Hashed token
        """
        return hashlib.sha256(token.encode()).hexdigest()
    
    def _cleanup_expired_revoked_tokens(self, cursor):
        """Remove expired tokens from the revocation list."""
        cursor.execute(
            f"DELETE FROM {self.revoked_tokens_table} WHERE expires_at < %s",
            (datetime.utcnow(),)
        )
    
    def _is_token_revoked(self, token: str) -> bool:
        """Check if a token has been revoked.
        
        Args:
            token: JWT token to check
            
        Returns:
            True if revoked, False otherwise
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                token_hash = self._hash_token(token)
                cur.execute(
                    f"SELECT 1 FROM {self.revoked_tokens_table} WHERE token_hash = %s",
                    (token_hash,)
                )
                return cur.fetchone() is not None
        except psycopg2.Error:
            return False
        finally:
            self._put_connection(conn)
    
    def authenticate(self, username: str, password: str) -> Optional[dict]:
        """Authenticate a user and return a JWT token.
        
        Args:
            username: The username
            password: The password
            
        Returns:
            Dict with 'token' (JWT) and 'expires_at' if successful, None otherwise
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Cleanup expired revoked tokens periodically
                self._cleanup_expired_revoked_tokens(cur)
                
                # Find user
                cur.execute(
                    f'''SELECT username, password_hash, role 
                        FROM {self.users_table} 
                        WHERE username = %s AND active = TRUE''',
                    (username,)
                )
                user = cur.fetchone()
                
                if not user:
                    conn.commit()
                    return None
                
                password_hash = self._hash_password(password)
                
                if user['password_hash'] != password_hash:
                    conn.commit()
                    return None
                
                conn.commit()
                
                # Generate JWT token using the global JWT handler
                jwt_handler = get_jwt_handler()
                if not jwt_handler:
                    raise RuntimeError("JWT handler not initialized")
                
                return jwt_handler.generate_auth_token(
                    username=username,
                    role=user['role'],
                    expires_in_hours=self.token_expiry_hours
                )
                
        except psycopg2.Error:
            conn.rollback()
            return None
        finally:
            self._put_connection(conn)
    
    def validate_token(self, token: str) -> Optional[dict]:
        """Validate a JWT authentication token.
        
        Args:
            token: The JWT authentication token
            
        Returns:
            User dict with 'username' and 'role' if valid, None otherwise
        """
        # Check if token is revoked in PostgreSQL
        if self._is_token_revoked(token):
            return None
        
        jwt_handler = get_jwt_handler()
        if not jwt_handler:
            return None
        
        token_data = jwt_handler.validate_auth_token(token)
        
        if not token_data:
            return None
        
        return {
            'username': token_data['username'],
            'role': token_data['role']
        }
    
    def invalidate_token(self, token: str) -> bool:
        """Invalidate a JWT authentication token (revoke it).
        
        Stores the token hash in PostgreSQL for distributed revocation.
        
        Args:
            token: The JWT authentication token
            
        Returns:
            True if successful, False otherwise
        """
        jwt_handler = get_jwt_handler()
        if not jwt_handler:
            return False
        
        # Get token expiry for cleanup
        expiry = jwt_handler.get_token_expiry(token)
        if not expiry:
            return False
        
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                token_hash = self._hash_token(token)
                cur.execute(
                    f'''INSERT INTO {self.revoked_tokens_table} 
                        (token_hash, expires_at) 
                        VALUES (%s, %s)
                        ON CONFLICT (token_hash) DO NOTHING''',
                    (token_hash, expiry)
                )
                conn.commit()
                return True
                
        except psycopg2.Error:
            conn.rollback()
            return False
        finally:
            self._put_connection(conn)
    
    # Additional utility methods
    
    def create_user(self, username: str, password: str, role: str = 'user',
                    email: Optional[str] = None) -> bool:
        """Create a new user.
        
        Args:
            username: The username
            password: The password
            role: User role (default: 'user')
            email: Optional email address
            
        Returns:
            True if successful, False otherwise
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f'''INSERT INTO {self.users_table} 
                        (username, password_hash, role, email) 
                        VALUES (%s, %s, %s, %s)''',
                    (username, self._hash_password(password), role, email)
                )
                conn.commit()
                return True
                
        except psycopg2.Error:
            conn.rollback()
            return False
        finally:
            self._put_connection(conn)
    
    def update_password(self, username: str, new_password: str) -> bool:
        """Update a user's password.
        
        Args:
            username: The username
            new_password: The new password
            
        Returns:
            True if successful, False otherwise
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f'''UPDATE {self.users_table} 
                        SET password_hash = %s, updated_at = %s 
                        WHERE username = %s''',
                    (self._hash_password(new_password), datetime.utcnow(), username)
                )
                updated = cur.rowcount > 0
                conn.commit()
                return updated
                
        except psycopg2.Error:
            conn.rollback()
            return False
        finally:
            self._put_connection(conn)
    
    def deactivate_user(self, username: str) -> bool:
        """Deactivate a user account.
        
        Args:
            username: The username
            
        Returns:
            True if successful, False otherwise
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # Deactivate user
                cur.execute(
                    f'''UPDATE {self.users_table} 
                        SET active = FALSE, updated_at = %s 
                        WHERE username = %s''',
                    (datetime.utcnow(), username)
                )
                updated = cur.rowcount > 0
                
                # Invalidate all tokens
                cur.execute(
                    f"DELETE FROM {self.tokens_table} WHERE username = %s",
                    (username,)
                )
                
                conn.commit()
                return updated
                
        except psycopg2.Error:
            conn.rollback()
            return False
        finally:
            self._put_connection(conn)
    
    def get_user(self, username: str) -> Optional[dict]:
        """Get user information.
        
        Args:
            username: The username
            
        Returns:
            User dict (without password_hash) if found, None otherwise
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f'''SELECT id, username, role, email, created_at, updated_at, active 
                        FROM {self.users_table} 
                        WHERE username = %s''',
                    (username,)
                )
                user = cur.fetchone()
                return dict(user) if user else None
                
        except psycopg2.Error:
            return None
        finally:
            self._put_connection(conn)
    
    def list_users(self, offset: int = 0, limit: int = 100) -> list:
        """List all users.
        
        Args:
            offset: Number of users to skip
            limit: Maximum number of users to return
            
        Returns:
            List of user dicts (without password_hash)
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f'''SELECT id, username, role, email, created_at, updated_at, active 
                        FROM {self.users_table} 
                        ORDER BY id 
                        OFFSET %s LIMIT %s''',
                    (offset, limit)
                )
                return [dict(row) for row in cur.fetchall()]
                
        except psycopg2.Error:
            return []
        finally:
            self._put_connection(conn)
    
    def close(self):
        """Close all connections in the pool."""
        if self._pool:
            self._pool.closeall()
