from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from routers import accounts, audit, dashboard
from routers import property as property_router
from routers import shares as shares_router

# Create all tables on startup
Base.metadata.create_all(bind=engine)


def _run_migrations():
    """Safe ALTER TABLE migrations for SQLite (idempotent) and data migration from old mortgages table."""
    # Ensure new tables are created
    Base.metadata.create_all(bind=engine)
    
    with engine.connect() as conn:
        # accounts table
        acc_cols = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(accounts)")]
        if "initial_investment" not in acc_cols:
            conn.exec_driver_sql("ALTER TABLE accounts ADD COLUMN initial_investment REAL")
            conn.commit()

        # properties table
        prop_cols = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(properties)")]
        if "purchase_date" not in prop_cols:
            conn.exec_driver_sql("ALTER TABLE properties ADD COLUMN purchase_date DATETIME")
            conn.commit()

        # share_holdings table — new columns for stale-price persistence
        table_names_early = [row[0] for row in conn.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table'")]
        if "share_holdings" in table_names_early:
            sh_cols = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(share_holdings)")]
            if "last_price" not in sh_cols:
                conn.exec_driver_sql("ALTER TABLE share_holdings ADD COLUMN last_price REAL")
            if "last_price_currency" not in sh_cols:
                conn.exec_driver_sql("ALTER TABLE share_holdings ADD COLUMN last_price_currency TEXT")
            if "last_price_at" not in sh_cols:
                conn.exec_driver_sql("ALTER TABLE share_holdings ADD COLUMN last_price_at DATETIME")
            conn.commit()

        # Check if old tables exist and need data migration
        table_names = [row[0] for row in conn.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table'")]
        
        if "mortgages" in table_names and "properties" in table_names:
            prop_count = conn.exec_driver_sql("SELECT COUNT(*) FROM properties").fetchone()[0]
            mort_count = conn.exec_driver_sql("SELECT COUNT(*) FROM mortgages").fetchone()[0]
            
            if prop_count == 0 and mort_count > 0:
                print("Migrating data from mortgages to properties & mortgage_parts...")
                mortgages = conn.exec_driver_sql(
                    "SELECT id, name, property_address, lender, original_price, property_value, "
                    "outstanding_balance, ownership_percent, monthly_payment, interest_rate, notes, "
                    "is_active, created_at, updated_at FROM mortgages"
                ).fetchall()
                
                for m in mortgages:
                    m_id, name, addr, lender, orig_price, prop_val, out_bal, own_pct, m_pay, int_rate, notes, active, c_at, u_at = m
                    
                    # Insert into properties
                    conn.exec_driver_sql(
                        "INSERT INTO properties (id, name, property_address, original_price, property_value, ownership_percent, notes, is_active, created_at, updated_at) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (m_id, name, addr, orig_price, prop_val, own_pct, notes, active, c_at, u_at)
                    )
                    
                    # Insert into mortgage_parts (using same ID so audit logs line up)
                    conn.exec_driver_sql(
                        "INSERT INTO mortgage_parts (id, property_id, name, lender, outstanding_balance, interest_rate, mortgage_type, term_years, term_months, monthly_payment, notes, is_active, created_at, updated_at) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (m_id, m_id, "Main Mortgage", lender, out_bal, int_rate, "REPAYMENT", 25, 0, m_pay, "Migrated from single-mortgage tracker", active, c_at, u_at)
                    )
                
                # Migrate audit logs
                if "mortgage_audit_log" in table_names:
                    logs = conn.exec_driver_sql(
                        "SELECT id, mortgage_id, field_changed, previous_value, new_value, change_amount, note, recorded_at "
                        "FROM mortgage_audit_log"
                    ).fetchall()
                    for log in logs:
                        l_id, m_id, field, prev, new_val, change, note, rec_at = log
                        if field == "property_value":
                            conn.exec_driver_sql(
                                "INSERT INTO property_value_audit_log (property_id, previous_value, new_value, change_amount, note, recorded_at) "
                                "VALUES (?, ?, ?, ?, ?, ?)",
                                (m_id, prev, new_val, change, note, rec_at)
                            )
                        elif field == "outstanding_balance":
                            conn.exec_driver_sql(
                                "INSERT INTO mortgage_part_audit_log (part_id, previous_value, new_value, change_amount, note, recorded_at) "
                                "VALUES (?, ?, ?, ?, ?, ?)",
                                (m_id, prev, new_val, change, note, rec_at)
                            )
                conn.commit()
                print("Data migration complete!")


_run_migrations()

app = FastAPI(
    title="UK Account Tracker API",
    description="Local-first financial account tracking for UK residents",
    version="1.0.0",
)

# Allow the Vite dev server and local file access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(accounts.router)
app.include_router(audit.router)
app.include_router(dashboard.router)
app.include_router(property_router.router)
app.include_router(shares_router.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "account-tracker"}
