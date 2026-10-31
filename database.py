import sqlite3
import pandas as pd
import os
import bcrypt
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

DB_PATH = "mtc_database.db"

def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables with all required columns"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Create Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Certificates table
    c.execute('''
        CREATE TABLE IF NOT EXISTS certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_id TEXT UNIQUE,
            supplier_name TEXT,
            material_grade TEXT,
            heat_number TEXT,
            yield_strength REAL,
            tensile_strength REAL,
            compliance_score REAL,
            status TEXT,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_fraud_risk BOOLEAN DEFAULT 0,
            risk_alerts TEXT,
            file_hash TEXT UNIQUE,
            verified_by TEXT,
            passport_id TEXT UNIQUE,
            standard TEXT,
            notes TEXT
        )
    ''')
    
    # Create Suppliers table
    c.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            total_certs INTEGER DEFAULT 0,
            passed_certs INTEGER DEFAULT 0,
            trust_score REAL DEFAULT 100.0,
            contact_email TEXT,
            last_verified DATE,
            risk_level TEXT DEFAULT 'LOW'
        )
    ''')
    
    conn.commit()
    
    # Create indexes
    try:
        c.execute('CREATE INDEX IF NOT EXISTS idx_heat_number ON certificates(heat_number)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_file_hash ON certificates(file_hash)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_supplier ON certificates(supplier_name)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_verified_by ON certificates(verified_by)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_status ON certificates(status)')
        conn.commit()
    except Exception as e:
        print(f"Index creation warning: {e}")
    
    conn.close()
    print("Database initialized successfully!")

# --- User Authentication Functions ---

def register_user(username: str, password: str, email: str = "") -> bool:
    """Register a new user with hashed password"""
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
        c.execute("""
            INSERT INTO users (username, password_hash, email) 
            VALUES (?, ?, ?)
        """, (username, hashed, email))
        
        conn.commit()
        return True
        
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username: str, password: str) -> bool:
    """Verify user login credentials"""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    
    if row and row['password_hash']:
        stored_hash = row['password_hash'].encode('utf-8')
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash)
    return False

def get_user_role(username: str) -> str:
    """Get user role for authorization"""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT role FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    
    return row['role'] if row else 'user'

def get_all_users() -> pd.DataFrame:
    """Get all registered users (admin only)"""
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("""
            SELECT id, username, email, role, created_at 
            FROM users 
            ORDER BY created_at DESC
        """, conn)
    except Exception as e:
        print(f"Error fetching users: {e}")
        df = pd.DataFrame()
    finally:
        conn.close()
    return df

def delete_user(username: str) -> bool:
    """Delete a user (admin only)"""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("DELETE FROM users WHERE username = ?", (username,))
    deleted = c.rowcount > 0
    conn.commit()
    conn.close()
    
    return deleted

# --- USER-SPECIFIC FUNCTIONS ---

def get_user_certificate_count(username: str) -> int:
    """Get number of certificates verified by specific user"""
    if not username:
        return 0
        
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('''
            SELECT COUNT(*) as count FROM certificates 
            WHERE verified_by = ?
        ''', (username,))
        result = c.fetchone()
        return result['count'] if result else 0
    except Exception as e:
        print(f"Error getting user cert count: {e}")
        return 0
    finally:
        conn.close()

def get_total_certificate_count() -> int:
    """Get total certificates in system"""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT COUNT(*) as count FROM certificates")
        row = c.fetchone()
        return row['count'] if row else 0
    except Exception as e:
        print(f"Error getting total cert count: {e}")
        return 0
    finally:
        conn.close()

def get_user_recent_certificates(username: str, limit: int = 5) -> pd.DataFrame:
    """Get recent certificates verified by user"""
    conn = get_db_connection()
    try:
        query = """
            SELECT material_id, supplier_name, material_grade, 
                   compliance_score, status, upload_date
            FROM certificates 
            WHERE verified_by = ?
            ORDER BY upload_date DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(username, limit))
        return df
    except Exception as e:
        print(f"Error getting user certs: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_user_stats(username: str) -> dict:
    """Get comprehensive user statistics"""
    if not username:
        return {"total": 0, "passed": 0, "failed": 0, "fraud": 0, "avg_score": 0}
        
    conn = get_db_connection()
    c = conn.cursor()
    try:
        # Total verified
        c.execute("SELECT COUNT(*) FROM certificates WHERE verified_by = ?", (username,))
        total = c.fetchone()[0]
        
        # Pass count
        c.execute("SELECT COUNT(*) FROM certificates WHERE verified_by = ? AND status = 'Pass'", (username,))
        passed = c.fetchone()[0]
        
        # Fail count
        c.execute("SELECT COUNT(*) FROM certificates WHERE verified_by = ? AND status = 'Fail'", (username,))
        failed = c.fetchone()[0]
        
        # Fraud detected
        c.execute("SELECT COUNT(*) FROM certificates WHERE verified_by = ? AND is_fraud_risk = 1", (username,))
        fraud = c.fetchone()[0]
        
        # Average compliance score
        c.execute("SELECT AVG(compliance_score) FROM certificates WHERE verified_by = ?", (username,))
        avg_score = c.fetchone()[0] or 0
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "fraud": fraud,
            "avg_score": round(avg_score, 2)
        }
    except Exception as e:
        print(f"Error getting user stats: {e}")
        return {"total": 0, "passed": 0, "failed": 0, "fraud": 0, "avg_score": 0}
    finally:
        conn.close()

# --- Certificate Operations ---

def add_certificate(cert_data: Dict[str, Any]) -> Optional[str]:
    """Save verified certificate to database with verified_by field"""
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        material_id = cert_data.get('material_id')
        status = cert_data.get('status', 'Pending')
        file_hash = cert_data.get('file_hash')
        verified_by = cert_data.get('verified_by')
        supplier_name = cert_data.get('supplier_name', 'Unknown')
        
        # Generate passport ID if not provided
        passport_id = cert_data.get('passport_id')
        if not passport_id:
            passport_id = f"PASS-{uuid.uuid4().hex[:8].upper()}"
        
        # Check for duplicate file
        if file_hash:
            c.execute("SELECT id FROM certificates WHERE file_hash = ?", (file_hash,))
            if c.fetchone():
                print(f"Duplicate file detected: {file_hash}")
                return None
        
        # Insert certificate with verified_by
        c.execute('''
            INSERT INTO certificates (
                material_id, supplier_name, material_grade, heat_number,
                yield_strength, tensile_strength, compliance_score, status,
                is_fraud_risk, risk_alerts, file_hash, verified_by,
                passport_id, standard, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            material_id,
            supplier_name,
            cert_data.get('material_grade', 'Unknown'),
            cert_data.get('heat_number', 'Unknown'),
            cert_data.get('yield_strength', 0.0),
            cert_data.get('tensile_strength', 0.0),
            cert_data.get('compliance_score', 0.0),
            status,
            1 if cert_data.get('is_fraud_risk') else 0,
            cert_data.get('risk_alerts', ''),
            file_hash,
            verified_by,
            passport_id,
            cert_data.get('standard', ''),
            cert_data.get('notes', '')
        ))
        
        # Update supplier statistics
        if supplier_name and supplier_name != 'Unknown':
            update_supplier_stats(supplier_name, status == 'Pass')
        
        conn.commit()
        print(f"✅ Certificate {material_id} saved with passport {passport_id}")
        return material_id
        
    except Exception as e:
        print(f"❌ Error adding certificate: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def update_supplier_stats(supplier_name: str, passed: bool):
    """Update supplier trust score based on verification result"""
    if not supplier_name or supplier_name == 'Unknown':
        return
        
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        # Check if supplier exists
        c.execute("SELECT id, total_certs, passed_certs FROM suppliers WHERE name = ?", (supplier_name,))
        supplier = c.fetchone()
        
        if supplier:
            # Update existing supplier
            total = supplier['total_certs'] + 1
            passed_count = supplier['passed_certs'] + (1 if passed else 0)
            trust_score = (passed_count / total) * 100 if total > 0 else 0
            
            # Determine risk level
            if trust_score >= 80:
                risk_level = 'LOW'
            elif trust_score >= 50:
                risk_level = 'MEDIUM'
            else:
                risk_level = 'HIGH'
            
            c.execute("""
                UPDATE suppliers 
                SET total_certs = ?, passed_certs = ?, trust_score = ?, 
                    risk_level = ?, last_verified = date('now')
                WHERE id = ?
            """, (total, passed_count, trust_score, risk_level, supplier['id']))
            
            print(f"✅ Supplier {supplier_name} updated: Total={total}, Trust={trust_score:.1f}%")
        else:
            # Create new supplier
            passed_count = 1 if passed else 0
            trust_score = 100.0 if passed else 0.0
            risk_level = 'LOW' if passed else 'HIGH'
            
            c.execute("""
                INSERT INTO suppliers (name, total_certs, passed_certs, trust_score, risk_level, last_verified)
                VALUES (?, 1, ?, ?, ?, date('now'))
            """, (supplier_name, passed_count, trust_score, risk_level))
            
            print(f"✅ New supplier created: {supplier_name} with trust {trust_score}%")
        
        conn.commit()
    except Exception as e:
        print(f"❌ Error updating supplier stats: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_certificate_by_hash(file_hash: str) -> Optional[Dict]:
    """Check if file was already verified"""
    if not file_hash:
        return None
    
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT * FROM certificates WHERE file_hash = ?", (file_hash,))
    row = c.fetchone()
    conn.close()
    
    return dict(row) if row else None

def check_duplicate_heat(heat_number: str) -> bool:
    """Check if heat number already exists (fraud detection)"""
    if not heat_number or heat_number == 'Unknown':
        return False
    
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT id FROM certificates WHERE heat_number = ?", (heat_number,))
    exists = c.fetchone() is not None
    conn.close()
    
    return exists

def get_certificate_by_heat(heat_number: str) -> Optional[Dict]:
    """Get certificate details by heat number"""
    if not heat_number:
        return None
        
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT * FROM certificates WHERE heat_number = ? ORDER BY upload_date DESC", (heat_number,))
    row = c.fetchone()
    conn.close()
    
    return dict(row) if row else None

def count_fraud_by_supplier(supplier_name: str) -> int:
    """Count fraudulent certificates for a supplier"""
    if not supplier_name:
        return 0
        
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("""
        SELECT COUNT(*) as fraud_count 
        FROM certificates 
        WHERE supplier_name = ? AND is_fraud_risk = 1
    """, (supplier_name,))
    
    row = c.fetchone()
    conn.close()
    
    return row['fraud_count'] if row else 0

def delete_certificate(material_id: str) -> bool:
    """Delete a certificate by material ID (admin only)"""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("DELETE FROM certificates WHERE material_id = ?", (material_id,))
    deleted = c.rowcount > 0
    conn.commit()
    conn.close()
    
    return deleted

# --- Dashboard and Statistics ---

def get_dashboard_stats() -> Dict[str, Any]:
    """Get statistics for dashboard"""
    conn = get_db_connection()
    
    try:
        # Get certificates data
        df_certs = pd.read_sql_query("SELECT * FROM certificates ORDER BY upload_date DESC", conn)
        df_suppliers = pd.read_sql_query("SELECT * FROM suppliers ORDER BY trust_score DESC", conn)
        
        # Calculate statistics
        total_certs = len(df_certs)
        pass_certs = len(df_certs[df_certs['status'] == 'Pass']) if not df_certs.empty else 0
        fail_certs = total_certs - pass_certs
        risk_alerts = len(df_certs[df_certs['is_fraud_risk'] == 1]) if not df_certs.empty else 0
        avg_score = df_certs['compliance_score'].mean() if not df_certs.empty else 0
        
        return {
            "total": total_certs,
            "pass": pass_certs,
            "fail": fail_certs,
            "risk_count": risk_alerts,
            "avg_compliance": round(avg_score, 2),
            "certs_df": df_certs,
            "suppliers_df": df_suppliers
        }
    except Exception as e:
        print(f"Error getting dashboard stats: {e}")
        return {
            "total": 0, "pass": 0, "fail": 0, "risk_count": 0,
            "avg_compliance": 0, "certs_df": pd.DataFrame(), "suppliers_df": pd.DataFrame()
        }
    finally:
        conn.close()

def get_all_certificates() -> pd.DataFrame:
    """Get all certificates for Material Passport"""
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("""
            SELECT material_id, supplier_name, material_grade, heat_number,
                   compliance_score, status, is_fraud_risk, upload_date, 
                   verified_by, passport_id
            FROM certificates 
            ORDER BY upload_date DESC
        """, conn)
        return df
    except Exception as e:
        print(f"Error fetching certificates: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_all_suppliers() -> pd.DataFrame:
    """Get all suppliers for Supplier Trust page - FIXED VERSION"""
    conn = get_db_connection()
    try:
        # First try to get from suppliers table
        df = pd.read_sql_query("""
            SELECT name, total_certs, passed_certs, 
                   ROUND(trust_score, 1) as trust_score, 
                   risk_level, last_verified
            FROM suppliers 
            WHERE total_certs > 0
            ORDER BY trust_score DESC
        """, conn)
        
        # If suppliers table is empty, get from certificates table
        if df.empty:
            print("⚠️ Suppliers table empty - getting data from certificates table")
            
            # Get unique suppliers from certificates
            df = pd.read_sql_query("""
                SELECT 
                    supplier_name as name,
                    COUNT(*) as total_certs,
                    SUM(CASE WHEN status = 'Pass' THEN 1 ELSE 0 END) as passed_certs,
                    ROUND(
                        (SUM(CASE WHEN status = 'Pass' THEN 1.0 ELSE 0.0 END) / COUNT(*)) * 100, 
                        1
                    ) as trust_score,
                    CASE 
                        WHEN (SUM(CASE WHEN status = 'Pass' THEN 1.0 ELSE 0.0 END) / COUNT(*)) * 100 >= 80 THEN 'LOW'
                        WHEN (SUM(CASE WHEN status = 'Pass' THEN 1.0 ELSE 0.0 END) / COUNT(*)) * 100 >= 50 THEN 'MEDIUM'
                        ELSE 'HIGH'
                    END as risk_level,
                    MAX(upload_date) as last_verified
                FROM certificates 
                WHERE supplier_name IS NOT NULL AND supplier_name != 'Unknown'
                GROUP BY supplier_name
                ORDER BY trust_score DESC
            """, conn)
            
            if not df.empty:
                print(f"✅ Found {len(df)} suppliers from certificates table")
                # Insert into suppliers table for future use
                insert_suppliers_from_certificates(conn)
        
        return df
        
    except Exception as e:
        print(f"❌ Error fetching suppliers: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def insert_suppliers_from_certificates(conn=None):
    """Insert supplier data from certificates into suppliers table"""
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True
    
    try:
        c = conn.cursor()
        
        # Get aggregated supplier data from certificates
        c.execute("""
            SELECT 
                supplier_name,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Pass' THEN 1 ELSE 0 END) as passed
            FROM certificates 
            WHERE supplier_name IS NOT NULL AND supplier_name != 'Unknown'
            GROUP BY supplier_name
        """)
        
        suppliers = c.fetchall()
        
        for s in suppliers:
            name = s['supplier_name']
            total = s['total']
            passed = s['passed']
            trust_score = (passed / total) * 100 if total > 0 else 0
            
            # Determine risk level
            if trust_score >= 80:
                risk_level = 'LOW'
            elif trust_score >= 50:
                risk_level = 'MEDIUM'
            else:
                risk_level = 'HIGH'
            
            # Insert or replace in suppliers table
            c.execute("""
                INSERT OR REPLACE INTO suppliers 
                (name, total_certs, passed_certs, trust_score, risk_level, last_verified)
                VALUES (?, ?, ?, ?, ?, date('now'))
            """, (name, total, passed, trust_score, risk_level))
        
        conn.commit()
        print(f"✅ Inserted/Updated {len(suppliers)} suppliers in suppliers table")
        
    except Exception as e:
        print(f"❌ Error inserting suppliers: {e}")
    finally:
        if should_close:
            conn.close()

def get_supplier_history(supplier_name: str) -> pd.DataFrame:
    """Get verification history for a specific supplier"""
    if not supplier_name:
        return pd.DataFrame()
        
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("""
            SELECT material_id, material_grade, heat_number, compliance_score,
                   status, is_fraud_risk, upload_date, verified_by
            FROM certificates 
            WHERE supplier_name = ?
            ORDER BY upload_date DESC
        """, conn, params=(supplier_name,))
    except Exception as e:
        print(f"Error fetching supplier history: {e}")
        df = pd.DataFrame()
    finally:
        conn.close()
    return df

def debug_supplier_data():
    """Debug function to check supplier data in both tables"""
    conn = get_db_connection()
    c = conn.cursor()
    
    print("\n" + "="*60)
    print("🔍 SUPPLIER DATA DEBUG")
    print("="*60)
    
    # Check certificates table
    c.execute("""
        SELECT supplier_name, COUNT(*) as count 
        FROM certificates 
        WHERE supplier_name IS NOT NULL AND supplier_name != 'Unknown'
        GROUP BY supplier_name
    """)
    cert_suppliers = c.fetchall()
    
    print("\n📋 Suppliers in CERTIFICATES table:")
    if cert_suppliers:
        for s in cert_suppliers:
            print(f"   • {s['supplier_name']}: {s['count']} certificates")
    else:
        print("   ❌ No suppliers found in certificates table!")
    
    # Check suppliers table
    c.execute("SELECT name, total_certs, passed_certs, trust_score FROM suppliers")
    suppliers = c.fetchall()
    
    print("\n📋 Suppliers in SUPPLIERS table:")
    if suppliers:
        for s in suppliers:
            print(f"   • {s['name']}: Total={s['total_certs']}, Passed={s['passed_certs']}, Trust={s['trust_score']:.1f}%")
    else:
        print("   ❌ Suppliers table is EMPTY!")
    
    print("="*60 + "\n")
    conn.close()
    
    return bool(cert_suppliers), bool(suppliers)

# --- Maintenance Functions ---

def backup_database(backup_path: str = "mtc_database_backup.db"):
    """Create a backup of the database"""
    import shutil
    try:
        if os.path.exists(DB_PATH):
            shutil.copy2(DB_PATH, backup_path)
            return True
    except Exception as e:
        print(f"Backup failed: {e}")
    return False

def reset_database(confirm: bool = False):
    """Reset database (delete all data) - USE WITH CAUTION"""
    if not confirm:
        return False
    
    try:
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        init_db()
        return True
    except Exception as e:
        print(f"Reset failed: {e}")
        return False

# Initialize database when module is imported
if __name__ != "__main__":
    # Only initialize if database doesn't exist
    if not os.path.exists(DB_PATH):
        init_db()
        print("Database created successfully!")