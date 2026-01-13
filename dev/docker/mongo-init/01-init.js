// MongoDB initialization script for OpenMark
// This script is executed when the MongoDB container is first started

// Switch to openmark database
db = db.getSiblingDB('openmark');

// Create users collection with indexes
db.createCollection('users');
db.users.createIndex({ username: 1 }, { unique: true });
db.users.createIndex({ email: 1 }, { sparse: true });

// Create annotations collection with indexes
db.createCollection('annotations');
db.annotations.createIndex({ document_id: 1 });
db.annotations.createIndex({ user_id: 1 });
db.annotations.createIndex({ created_at: -1 });

// Create revoked_tokens collection with TTL index
db.createCollection('revoked_tokens');
db.revoked_tokens.createIndex({ token_hash: 1 }, { unique: true });
db.revoked_tokens.createIndex({ expires_at: 1 }, { expireAfterSeconds: 0 });

// Create statistics collection
db.createCollection('statistics');
db.statistics.createIndex({ user_id: 1 });
db.statistics.createIndex({ timestamp: -1 });

// Create history collection
db.createCollection('history');
db.history.createIndex({ user_id: 1 });
db.history.createIndex({ document_id: 1 });
db.history.createIndex({ timestamp: -1 });

// Insert default users (password hashes are SHA-256)
// admin123 -> 240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9
// user123  -> e606e38b0d8c19b24cf0ee3808183162ea7cd63ff7912dbb22b5e803286b4446
db.users.insertMany([
    {
        username: 'admin',
        password_hash: '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9',
        role: 'admin',
        email: 'admin@openmark.local',
        created_at: new Date(),
        updated_at: new Date(),
        active: true
    },
    {
        username: 'user',
        password_hash: 'e606e38b0d8c19b24cf0ee3808183162ea7cd63ff7912dbb22b5e803286b4446',
        role: 'user',
        email: 'user@openmark.local',
        created_at: new Date(),
        updated_at: new Date(),
        active: true
    }
]);

print('OpenMark MongoDB initialization completed successfully!');
