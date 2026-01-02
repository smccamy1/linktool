// MongoDB initialization script
db = db.getSiblingDB('idv_data');

// Create collections
db.createCollection('identity_verifications');
db.createCollection('verification_attempts');
db.createCollection('user_profiles');

// Create indexes
db.identity_verifications.createIndex({ "userId": 1 });
db.identity_verifications.createIndex({ "verificationId": 1 }, { unique: true });
db.identity_verifications.createIndex({ "timestamp": -1 });
db.identity_verifications.createIndex({ "status": 1 });

db.verification_attempts.createIndex({ "verificationId": 1 });
db.verification_attempts.createIndex({ "timestamp": -1 });

db.user_profiles.createIndex({ "userId": 1 }, { unique: true });
db.user_profiles.createIndex({ "email": 1 }, { unique: true });

print('MongoDB initialized successfully for IDV data');
