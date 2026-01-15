#!/usr/bin/env python3
"""
Lynx IDV Graph Visualization Web UI
Displays IDV data as graph visualization with node/edge relationships
and integrates insurance customer data from PostgreSQL.
"""

import os
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
CORS(app)

# Database connections
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://admin:mongopass123@mongodb:27017/')
POSTGRES_URI = os.getenv('POSTGRES_URI', 'postgresql://admin:postgrespass123@postgres:5432/insurance_db')

def get_mongo_connection():
    """Get MongoDB connection."""
    client = MongoClient(MONGO_URI)
    return client['idv_data']

def get_postgres_connection():
    """Get PostgreSQL connection."""
    return psycopg2.connect(POSTGRES_URI, cursor_factory=RealDictCursor)


@app.route('/')
def index():
    """Serve the main visualization page."""
    return render_template('index.html')


@app.route('/investigations')
def investigations_page():
    """Serve the investigations management page."""
    return render_template('investigations.html')


@app.route('/api/graph-data')
def get_graph_data():
    """
    Get IDV data formatted for graph visualization.
    Returns nodes (users, verifications, attempts) and edges (relationships).
    """
    try:
        db = get_mongo_connection()
        
        # Get user profiles
        users = list(db.user_profiles.find({}).limit(100))
        
        # Get verifications
        verifications = list(db.identity_verifications.find({}).limit(500))
        
        # Get verification attempts
        attempts = list(db.verification_attempts.find({}).limit(1000))
        
        nodes = []
        edges = []
        
        # Create user nodes
        for user in users:
            nodes.append({
                'id': user['userId'],
                'label': f"{user['firstName']} {user['lastName']}",
                'type': 'user',
                'group': 'user',
                'data': {
                    'userId': user['userId'],
                    'email': user['email'],
                    'firstName': user['firstName'],
                    'lastName': user['lastName'],
                    'dateOfBirth': user['dateOfBirth'],
                    'phone': user['phone'],
                    'address': user.get('address', {}),
                    'createdAt': user['createdAt']
                }
            })
        
        # Create verification nodes and edges to users
        for verification in verifications:
            status_color = {
                'approved': 'green',
                'rejected': 'red',
                'pending': 'yellow',
                'under_review': 'orange',
                'needs_additional_info': 'blue',
                'expired': 'gray',
                'cancelled': 'gray'
            }.get(verification['status'], 'gray')
            
            nodes.append({
                'id': verification['verificationId'],
                'label': f"Verification\\n{verification['status']}",
                'type': 'verification',
                'group': 'verification',
                'status': verification['status'],
                'statusColor': status_color,
                'data': {
                    'verificationId': verification['verificationId'],
                    'userId': verification['userId'],
                    'status': verification['status'],
                    'riskLevel': verification['riskLevel'],
                    'riskScore': verification.get('riskScore', 0),
                    'triggeredRules': verification.get('triggeredRules', []),
                    'verificationMethod': verification['verificationMethod'],
                    'attemptCount': verification.get('attemptCount', 1),
                    'submittedAt': verification['submittedAt'],
                    'reviewedAt': verification.get('reviewedAt'),
                    'flags': verification.get('flags', [])
                }
            })
            
            # Edge from user to verification
            edges.append({
                'id': f"user-ver-{verification['verificationId']}",
                'source': verification['userId'],
                'target': verification['verificationId'],
                'label': 'initiated',
                'type': 'user-verification'
            })
        
        # Create attempt nodes and edges to verifications
        attempt_count = {}
        for attempt in attempts:
            ver_id = attempt['verificationId']
            
            # Only show first 3 attempts per verification for clarity
            if ver_id not in attempt_count:
                attempt_count[ver_id] = 0
            
            if attempt_count[ver_id] < 3:
                nodes.append({
                    'id': attempt['attemptId'],
                    'label': f"Attempt #{attempt['attemptNumber']}",
                    'type': 'attempt',
                    'group': 'attempt',
                    'data': {
                        'attemptId': attempt['attemptId'],
                        'verificationId': attempt['verificationId'],
                        'attemptNumber': attempt['attemptNumber'],
                        'timestamp': attempt['timestamp'],
                        'ipAddress': attempt['ipAddress'],
                        'location': attempt.get('location', {}),
                        'duration': attempt['duration']
                    }
                })
                
                # Edge from verification to attempt
                edges.append({
                    'id': f"ver-att-{attempt['attemptId']}",
                    'source': attempt['verificationId'],
                    'target': attempt['attemptId'],
                    'label': f"attempt #{attempt['attemptNumber']}",
                    'type': 'verification-attempt'
                })
                
                attempt_count[ver_id] += 1
        
        return jsonify({
            'nodes': nodes,
            'edges': edges,
            'stats': {
                'totalUsers': len(users),
                'totalVerifications': len(verifications),
                'totalAttempts': len(attempts)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/node/<node_id>/insurance-data')
def get_insurance_data(node_id):
    """
    Get insurance data for a specific user node.
    This queries the PostgreSQL database for customer, policy, and claims data.
    """
    try:
        # First get the user from MongoDB to confirm it exists
        db = get_mongo_connection()
        user = db.user_profiles.find_one({'userId': node_id})
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Query PostgreSQL for insurance data
        conn = get_postgres_connection()
        cursor = conn.cursor()
        
        # Get customer data
        cursor.execute("""
            SELECT * FROM customers WHERE user_id = %s
        """, (node_id,))
        customer = cursor.fetchone()
        
        if not customer:
            return jsonify({
                'hasInsurance': False,
                'message': 'No insurance data found for this user'
            })
        
        customer_id = customer['customer_id']
        
        # Get policies
        cursor.execute("""
            SELECT p.*, pr.product_name, pr.product_category
            FROM policies p
            JOIN products pr ON p.product_id = pr.product_id
            WHERE p.customer_id = %s
            ORDER BY p.effective_date DESC
        """, (customer_id,))
        policies = cursor.fetchall()
        
        # Get claims
        cursor.execute("""
            SELECT c.*, p.policy_number, pr.product_name
            FROM claims c
            JOIN policies p ON c.policy_id = p.policy_id
            JOIN products pr ON p.product_id = pr.product_id
            WHERE c.customer_id = %s
            ORDER BY c.claim_date DESC
        """, (customer_id,))
        claims = cursor.fetchall()
        
        # Get recent payments
        cursor.execute("""
            SELECT py.*, p.policy_number
            FROM payments py
            JOIN policies p ON py.policy_id = p.policy_id
            WHERE py.customer_id = %s
            ORDER BY py.payment_date DESC
            LIMIT 10
        """, (customer_id,))
        payments = cursor.fetchall()
        
        # Get dependents
        cursor.execute("""
            SELECT * FROM dependents WHERE customer_id = %s
        """, (customer_id,))
        dependents = cursor.fetchall()
        
        # Calculate summary statistics
        total_premium = sum([p['premium_amount'] for p in policies if p['status'] == 'active'])
        total_claims_submitted = len(claims)
        total_claims_approved = len([c for c in claims if c['status'] in ['approved', 'paid']])
        total_claims_amount = sum([c['claim_amount'] for c in claims])
        total_paid_amount = sum([c['approved_amount'] for c in claims if c['approved_amount']])
        
        conn.close()
        
        return jsonify({
            'hasInsurance': True,
            'customer': dict(customer),
            'policies': [dict(p) for p in policies],
            'claims': [dict(c) for c in claims],
            'payments': [dict(p) for p in payments],
            'dependents': [dict(d) for d in dependents],
            'summary': {
                'totalMonthlyPremium': float(total_premium),
                'activePolicies': len([p for p in policies if p['status'] == 'active']),
                'totalPolicies': len(policies),
                'totalClaimsSubmitted': total_claims_submitted,
                'totalClaimsApproved': total_claims_approved,
                'totalClaimsAmount': float(total_claims_amount),
                'totalPaidAmount': float(total_paid_amount),
                'claimApprovalRate': (total_claims_approved / total_claims_submitted * 100) if total_claims_submitted > 0 else 0
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats')
def get_stats():
    """Get overall statistics from both databases."""
    try:
        # MongoDB stats
        db = get_mongo_connection()
        mongo_stats = {
            'users': db.user_profiles.count_documents({}),
            'verifications': db.identity_verifications.count_documents({}),
            'attempts': db.verification_attempts.count_documents({})
        }
        
        # PostgreSQL stats
        conn = get_postgres_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM customers")
        customers_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM policies WHERE status = 'active'")
        active_policies = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM claims")
        total_claims = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM claims WHERE status IN ('approved', 'paid')")
        approved_claims = cursor.fetchone()['count']
        
        conn.close()
        
        return jsonify({
            'idv': mongo_stats,
            'insurance': {
                'customers': customers_count,
                'activePolicies': active_policies,
                'totalClaims': total_claims,
                'approvedClaims': approved_claims
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/investigations', methods=['POST'])
def create_investigation():
    """Create a new investigation with selected nodes"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Investigation name is required'}), 400
        
        if not data.get('nodes') or len(data.get('nodes')) == 0:
            return jsonify({'error': 'At least one node must be selected'}), 400
        
        # Prepare investigation document
        investigation_doc = {
            'name': data['name'],
            'description': data.get('description', ''),
            'nodes': data['nodes'],
            'createdAt': data.get('createdAt'),
            'status': 'active'
        }
        
        # Insert into MongoDB
        db = get_mongo_connection()
        result = db.investigations.insert_one(investigation_doc)
        
        return jsonify({
            'success': True,
            'investigation_id': str(result.inserted_id),
            'message': 'Investigation created successfully'
        }), 201
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/investigations', methods=['GET'])
def list_investigations():
    """List all investigations"""
    try:
        db = get_mongo_connection()
        investigations = list(db.investigations.find())
        
        # Convert ObjectId to string
        for inv in investigations:
            inv['_id'] = str(inv['_id'])
        
        return jsonify({
            'investigations': investigations
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/investigations/<investigation_id>', methods=['GET'])
def get_investigation(investigation_id):
    """Get a specific investigation by ID"""
    try:
        from bson.objectid import ObjectId
        db = get_mongo_connection()
        
        investigation = db.investigations.find_one({'_id': ObjectId(investigation_id)})
        
        if not investigation:
            return jsonify({'error': 'Investigation not found'}), 404
        
        investigation['_id'] = str(investigation['_id'])
        
        return jsonify(investigation)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/investigations/<investigation_id>', methods=['PUT'])
def update_investigation(investigation_id):
    """Update an investigation"""
    try:
        from bson.objectid import ObjectId
        db = get_mongo_connection()
        data = request.json
        
        # Prepare update document
        update_fields = {}
        if 'name' in data:
            update_fields['name'] = data['name']
        if 'description' in data:
            update_fields['description'] = data['description']
        if 'status' in data:
            update_fields['status'] = data['status']
        if 'notes' in data:
            update_fields['notes'] = data['notes']
        
        update_fields['updatedAt'] = datetime.utcnow().isoformat()
        
        result = db.investigations.update_one(
            {'_id': ObjectId(investigation_id)},
            {'$set': update_fields}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Investigation not found'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Investigation updated successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/investigations/<investigation_id>/nodes', methods=['POST'])
def add_node_to_investigation(investigation_id):
    """Add a node to an investigation"""
    try:
        from bson.objectid import ObjectId
        db = get_mongo_connection()
        data = request.json
        
        node_data = {
            'nodeId': data['nodeId'],
            'nodeType': data['nodeType'],
            'label': data['label'],
            'data': data.get('data', {}),
            'addedAt': datetime.utcnow().isoformat()
        }
        
        result = db.investigations.update_one(
            {'_id': ObjectId(investigation_id)},
            {'$push': {'nodes': node_data}}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Investigation not found'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Node added to investigation'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/investigations/<investigation_id>/nodes/<node_id>', methods=['DELETE'])
def remove_node_from_investigation(investigation_id, node_id):
    """Remove a node from an investigation"""
    try:
        from bson.objectid import ObjectId
        db = get_mongo_connection()
        
        result = db.investigations.update_one(
            {'_id': ObjectId(investigation_id)},
            {'$pull': {'nodes': {'nodeId': node_id}}}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Investigation not found'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Node removed from investigation'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/investigations/<investigation_id>', methods=['DELETE'])
def delete_investigation(investigation_id):
    """Delete an investigation"""
    try:
        from bson.objectid import ObjectId
        db = get_mongo_connection()
        
        result = db.investigations.delete_one({'_id': ObjectId(investigation_id)})
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Investigation not found'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Investigation deleted successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/fraud-patterns/ip-velocity')
def get_ip_velocity_patterns():
    """
    Detect and return IP velocity patterns (multiple users from same IP).
    Returns IPs with high user counts and the users associated with them.
    """
    try:
        db = get_mongo_connection()
        
        # Aggregate to find IPs with multiple users
        pipeline = [
            {
                '$group': {
                    '_id': '$ipAddress',
                    'users': {'$addToSet': '$userId'},
                    'sessionCount': {'$sum': 1},
                    'avgRiskScore': {'$avg': '$riskScore'},
                    'isHighVelocityIP': {'$first': '$isHighVelocityIP'}
                }
            },
            {
                '$project': {
                    'ipAddress': '$_id',
                    'userCount': {'$size': '$users'},
                    'users': 1,
                    'sessionCount': 1,
                    'avgRiskScore': 1,
                    'isHighVelocityIP': 1
                }
            },
            {
                '$match': {
                    'userCount': {'$gt': 1}  # Only IPs with multiple users
                }
            },
            {
                '$sort': {'userCount': -1}
            },
            {
                '$limit': 100
            }
        ]
        
        results = list(db.login_sessions.aggregate(pipeline))
        
        return jsonify({
            'patterns': results,
            'totalHighVelocityIPs': len([r for r in results if r.get('isHighVelocityIP')])
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/fraud-patterns/user/<user_id>/sessions')
def get_user_sessions(user_id):
    """Get all login sessions for a specific user."""
    try:
        db = get_mongo_connection()
        
        sessions = list(db.login_sessions.find({'userId': user_id}).sort('timestamp', -1))
        
        # Convert ObjectId to string
        for session in sessions:
            session['_id'] = str(session['_id'])
        
        # Calculate velocity score for user
        unique_ips = len(set(s['ipAddress'] for s in sessions))
        high_velocity_sessions = len([s for s in sessions if s.get('isHighVelocityIP')])
        
        return jsonify({
            'userId': user_id,
            'sessions': sessions,
            'totalSessions': len(sessions),
            'uniqueIPs': unique_ips,
            'highVelocitySessions': high_velocity_sessions,
            'velocityRatio': high_velocity_sessions / len(sessions) if sessions else 0
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/fraud-patterns/users-by-filter')
def get_users_by_filter():
    """
    Get users filtered by fraud patterns.
    Filters: high_ip_velocity, suspicious_user_agent, high_risk
    """
    try:
        filter_type = request.args.get('filter', 'all')
        db = get_mongo_connection()
        
        if filter_type == 'high_ip_velocity':
            # Find users with sessions on high velocity IPs
            pipeline = [
                {
                    '$match': {
                        'isHighVelocityIP': True
                    }
                },
                {
                    '$group': {
                        '_id': '$userId',
                        'highVelocityCount': {'$sum': 1},
                        'totalSessions': {'$sum': 1}
                    }
                },
                {
                    '$match': {
                        'highVelocityCount': {'$gte': 3}  # At least 3 high velocity sessions
                    }
                }
            ]
            user_ids = [doc['_id'] for doc in db.login_sessions.aggregate(pipeline)]
            
        elif filter_type == 'high_risk':
            # Find users with high average risk scores
            pipeline = [
                {
                    '$group': {
                        '_id': '$userId',
                        'avgRiskScore': {'$avg': '$riskScore'}
                    }
                },
                {
                    '$match': {
                        'avgRiskScore': {'$gte': 0.7}
                    }
                }
            ]
            user_ids = [doc['_id'] for doc in db.login_sessions.aggregate(pipeline)]
            
        else:
            user_ids = []
        
        return jsonify({
            'filter': filter_type,
            'userIds': user_ids,
            'count': len(user_ids)
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/fraud-patterns/ip-nodes')
def get_ip_nodes():
    """
    Get IP address nodes and edges for high-velocity IP visualization.
    Returns IPs that have multiple users sharing them.
    """
    try:
        db = get_mongo_connection()
        
        # Aggregate to find shared IPs
        pipeline = [
            {
                '$group': {
                    '_id': '$ipAddress',
                    'users': {'$addToSet': '$userId'},
                    'sessionCount': {'$sum': 1},
                    'isHighVelocityIP': {'$first': '$isHighVelocityIP'}
                }
            },
            {
                '$match': {
                    '$expr': {
                        '$gt': [{'$size': '$users'}, 1]  # Only IPs with multiple users
                    }
                }
            },
            {
                '$project': {
                    'ipAddress': '$_id',
                    'users': 1,
                    'userCount': {'$size': '$users'},
                    'sessionCount': 1,
                    'isHighVelocityIP': 1
                }
            }
        ]
        
        ip_data = list(db.login_sessions.aggregate(pipeline))
        
        # Create nodes and edges
        nodes = []
        edges = []
        
        for ip_info in ip_data:
            ip_address = ip_info['ipAddress']
            user_count = ip_info['userCount']
            is_high_velocity = ip_info.get('isHighVelocityIP', False)
            
            # Create IP node
            nodes.append({
                'id': f"ip_{ip_address}",
                'label': f"{ip_address}\\n({user_count} users)",
                'type': 'ip',
                'ipAddress': ip_address,
                'userCount': user_count,
                'sessionCount': ip_info['sessionCount'],
                'isHighVelocityIP': is_high_velocity
            })
            
            # Create edges from users to this IP
            for user_id in ip_info['users']:
                edges.append({
                    'from': user_id,
                    'to': f"ip_{ip_address}",
                    'type': 'uses_ip'
                })
        
        return jsonify({
            'nodes': nodes,
            'edges': edges,
            'totalSharedIPs': len(nodes)
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
