// MongoDB initialization script
db = db.getSiblingDB('idv_data');

// Create collections
db.createCollection('identity_verifications');
db.createCollection('verification_attempts');
db.createCollection('user_profiles');
db.createCollection('login_sessions');
db.createCollection('investigations');

// Create indexes
db.identity_verifications.createIndex({ "userId": 1 });
db.identity_verifications.createIndex({ "verificationId": 1 }, { unique: true });
db.identity_verifications.createIndex({ "timestamp": -1 });
db.identity_verifications.createIndex({ "status": 1 });

db.verification_attempts.createIndex({ "verificationId": 1 });
db.verification_attempts.createIndex({ "timestamp": -1 });

db.user_profiles.createIndex({ "userId": 1 }, { unique: true });
db.user_profiles.createIndex({ "email": 1 }, { unique: true });

// Indexes for login_sessions (IP velocity tracking)
db.login_sessions.createIndex({ "userId": 1 });
db.login_sessions.createIndex({ "ipAddress": 1 });
db.login_sessions.createIndex({ "timestamp": -1 });
db.login_sessions.createIndex({ "isHighVelocityIP": 1 });
db.login_sessions.createIndex({ "ipAddress": 1, "userId": 1 });

// Indexes for investigations
db.investigations.createIndex({ "createdAt": -1 });

print('MongoDB initialized successfully for IDV data');
