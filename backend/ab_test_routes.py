"""
A/B Testing Routes for Cookie Banner
API endpoints for managing and evaluating A/B tests
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import asyncpg
import hashlib
import json
from datetime import datetime, date
import math

router = APIRouter(prefix="/api/ab-tests", tags=["A/B Testing"])

# Global database pool (set by main.py)
db_pool = None


# ============================================================================
# Pydantic Models
# ============================================================================

class ABTestCreate(BaseModel):
    site_id: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    hypothesis: Optional[str] = None
    variant_a_config: Dict[str, Any]  # Control/Basis-Variante
    variant_b_config: Dict[str, Any]  # Test-Variante
    traffic_split: int = Field(default=50, ge=0, le=100)
    min_sample_size: int = Field(default=1000, ge=100)
    confidence_level: float = Field(default=0.95, ge=0.8, le=0.99)


class ABTestUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    hypothesis: Optional[str] = None
    variant_a_config: Optional[Dict[str, Any]] = None
    variant_b_config: Optional[Dict[str, Any]] = None
    traffic_split: Optional[int] = Field(default=None, ge=0, le=100)
    status: Optional[str] = None


class ABTestResult(BaseModel):
    test_id: int
    variant: str = Field(..., pattern="^[AB]$")
    impressions: int = Field(default=0, ge=0)
    accepted_all: int = Field(default=0, ge=0)
    accepted_partial: int = Field(default=0, ge=0)
    rejected_all: int = Field(default=0, ge=0)
    accepted_analytics: int = Field(default=0, ge=0)
    accepted_marketing: int = Field(default=0, ge=0)
    accepted_functional: int = Field(default=0, ge=0)
    avg_decision_time_ms: Optional[int] = None


# ============================================================================
# Helper Functions
# ============================================================================

async def get_db_connection():
    """Get database connection from app state"""
    global db_pool
    if db_pool is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return db_pool


def hash_visitor_id(visitor_id: str) -> str:
    """Hash visitor ID for consistent assignment"""
    return hashlib.sha256(visitor_id.encode()).hexdigest()


def calculate_z_score(rate_a: float, rate_b: float, n_a: int, n_b: int) -> float:
    """Calculate Z-score for statistical significance"""
    if n_a == 0 or n_b == 0:
        return 0.0
    
    pooled_rate = (rate_a * n_a + rate_b * n_b) / (n_a + n_b)
    
    if pooled_rate == 0 or pooled_rate == 1:
        return 0.0
    
    std_error = math.sqrt(pooled_rate * (1 - pooled_rate) * (1.0/n_a + 1.0/n_b))
    
    if std_error == 0:
        return 0.0
    
    return (rate_a - rate_b) / std_error


def z_to_p_value(z_score: float) -> float:
    """Convert Z-score to p-value (two-tailed)"""
    # Approximation using error function
    z = abs(z_score)
    t = 1.0 / (1.0 + 0.2316419 * z)
    d = 0.3989423 * math.exp(-z * z / 2)
    p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))))
    return 2 * p  # Two-tailed


def is_significant(z_score: float, confidence_level: float = 0.95) -> bool:
    """Check if result is statistically significant"""
    alpha = 1 - confidence_level
    p_value = z_to_p_value(z_score)
    return p_value < alpha


# ============================================================================
# A/B Test CRUD Endpoints
# ============================================================================

@router.post("")
async def create_ab_test(
    test: ABTestCreate,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Create a new A/B test
    
    Test starts in 'draft' status and must be activated separately.
    """
    try:
        # Check if there's already an active test for this site
        existing_query = """
            SELECT id FROM cookie_ab_tests 
            WHERE site_id = $1 AND status = 'running'
        """
        existing = await db_pool.fetchrow(existing_query, test.site_id)
        
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"There's already an active test for this site (ID: {existing['id']}). Please stop it first."
            )
        
        # Create test
        insert_query = """
            INSERT INTO cookie_ab_tests (
                site_id, name, description, hypothesis,
                variant_a_config, variant_b_config,
                traffic_split, min_sample_size, confidence_level,
                status
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'draft')
            RETURNING id, created_at
        """
        
        result = await db_pool.fetchrow(
            insert_query,
            test.site_id,
            test.name,
            test.description,
            test.hypothesis,
            json.dumps(test.variant_a_config),
            json.dumps(test.variant_b_config),
            test.traffic_split,
            test.min_sample_size,
            test.confidence_level
        )
        
        return {
            "success": True,
            "message": "A/B test created",
            "test_id": result['id'],
            "created_at": result['created_at'].isoformat(),
            "status": "draft"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating A/B test: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create test: {str(e)}")


@router.get("/{test_id}")
async def get_ab_test(
    test_id: int,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """Get A/B test details with current results"""
    try:
        # Get test
        test_query = """
            SELECT 
                id, site_id, name, description, hypothesis,
                variant_a_config, variant_b_config,
                traffic_split, status, winner,
                start_date, end_date,
                min_sample_size, confidence_level,
                created_at, updated_at
            FROM cookie_ab_tests
            WHERE id = $1
        """
        
        test = await db_pool.fetchrow(test_query, test_id)
        
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        
        # Get results summary
        results_query = """
            SELECT 
                variant,
                SUM(impressions) as impressions,
                SUM(accepted_all) as accepted_all,
                SUM(accepted_partial) as accepted_partial,
                SUM(rejected_all) as rejected_all,
                SUM(accepted_analytics) as accepted_analytics,
                SUM(accepted_marketing) as accepted_marketing,
                SUM(accepted_functional) as accepted_functional,
                AVG(avg_decision_time_ms) as avg_decision_time
            FROM cookie_ab_results
            WHERE test_id = $1
            GROUP BY variant
        """
        
        results = await db_pool.fetch(results_query, test_id)
        
        # Process results
        variant_a = {'impressions': 0, 'accepted_all': 0, 'rate': 0}
        variant_b = {'impressions': 0, 'accepted_all': 0, 'rate': 0}
        
        for r in results:
            data = {
                'impressions': int(r['impressions'] or 0),
                'accepted_all': int(r['accepted_all'] or 0),
                'accepted_partial': int(r['accepted_partial'] or 0),
                'rejected_all': int(r['rejected_all'] or 0),
                'accepted_analytics': int(r['accepted_analytics'] or 0),
                'accepted_marketing': int(r['accepted_marketing'] or 0),
                'accepted_functional': int(r['accepted_functional'] or 0),
                'avg_decision_time': int(r['avg_decision_time'] or 0),
            }
            data['rate'] = round(data['accepted_all'] / max(data['impressions'], 1) * 100, 2)
            
            if r['variant'] == 'A':
                variant_a = data
            else:
                variant_b = data
        
        # Calculate statistical significance
        z_score = calculate_z_score(
            variant_a['rate'] / 100,
            variant_b['rate'] / 100,
            variant_a['impressions'],
            variant_b['impressions']
        )
        p_value = z_to_p_value(z_score)
        significant = is_significant(z_score, test['confidence_level'])
        
        # Calculate improvement
        if variant_a['rate'] > 0:
            improvement = round((variant_b['rate'] - variant_a['rate']) / variant_a['rate'] * 100, 2)
        else:
            improvement = 0
        
        # Determine leading variant
        if variant_b['rate'] > variant_a['rate']:
            leading = 'B'
        elif variant_a['rate'] > variant_b['rate']:
            leading = 'A'
        else:
            leading = None
        
        # Check if minimum sample size reached
        sample_reached = (
            variant_a['impressions'] >= test['min_sample_size'] and
            variant_b['impressions'] >= test['min_sample_size']
        )
        
        return {
            "success": True,
            "test": {
                "id": test['id'],
                "site_id": test['site_id'],
                "name": test['name'],
                "description": test['description'],
                "hypothesis": test['hypothesis'],
                "variant_a_config": test['variant_a_config'],
                "variant_b_config": test['variant_b_config'],
                "traffic_split": test['traffic_split'],
                "status": test['status'],
                "winner": test['winner'],
                "start_date": test['start_date'].isoformat() if test['start_date'] else None,
                "end_date": test['end_date'].isoformat() if test['end_date'] else None,
                "min_sample_size": test['min_sample_size'],
                "confidence_level": float(test['confidence_level']),
                "created_at": test['created_at'].isoformat(),
                "updated_at": test['updated_at'].isoformat(),
            },
            "results": {
                "variant_a": variant_a,
                "variant_b": variant_b,
                "improvement_percent": improvement,
                "leading_variant": leading,
            },
            "statistics": {
                "z_score": round(z_score, 4),
                "p_value": round(p_value, 4),
                "is_significant": significant,
                "sample_reached": sample_reached,
                "confidence_level": float(test['confidence_level']),
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting A/B test: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get test: {str(e)}")


@router.get("/site/{site_id}")
async def get_site_tests(
    site_id: str,
    status: Optional[str] = None,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """Get all A/B tests for a site"""
    try:
        query = """
            SELECT 
                t.id, t.name, t.status, t.traffic_split,
                t.start_date, t.end_date, t.winner,
                t.created_at,
                COALESCE(SUM(r.impressions), 0) as total_impressions
            FROM cookie_ab_tests t
            LEFT JOIN cookie_ab_results r ON t.id = r.test_id
            WHERE t.site_id = $1
        """
        
        params = [site_id]
        
        if status:
            query += " AND t.status = $2"
            params.append(status)
        
        query += " GROUP BY t.id ORDER BY t.created_at DESC"
        
        rows = await db_pool.fetch(query, *params)
        
        tests = []
        for row in rows:
            tests.append({
                "id": row['id'],
                "name": row['name'],
                "status": row['status'],
                "traffic_split": row['traffic_split'],
                "start_date": row['start_date'].isoformat() if row['start_date'] else None,
                "end_date": row['end_date'].isoformat() if row['end_date'] else None,
                "winner": row['winner'],
                "total_impressions": int(row['total_impressions']),
                "created_at": row['created_at'].isoformat(),
            })
        
        return {
            "success": True,
            "site_id": site_id,
            "total": len(tests),
            "tests": tests
        }
        
    except Exception as e:
        print(f"Error getting site tests: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get tests: {str(e)}")


@router.patch("/{test_id}")
async def update_ab_test(
    test_id: int,
    update: ABTestUpdate,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """Update an A/B test (only allowed for draft tests)"""
    try:
        # Check test exists and status
        check_query = "SELECT status FROM cookie_ab_tests WHERE id = $1"
        test = await db_pool.fetchrow(check_query, test_id)
        
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        
        if test['status'] not in ['draft', 'paused'] and update.status is None:
            raise HTTPException(
                status_code=400, 
                detail="Can only update tests in 'draft' or 'paused' status"
            )
        
        # Build update query
        update_fields = []
        values = []
        param_idx = 1
        
        for field, value in update.dict(exclude_unset=True).items():
            if value is not None:
                if field in ['variant_a_config', 'variant_b_config']:
                    update_fields.append(f"{field} = ${param_idx}::jsonb")
                    values.append(json.dumps(value))
                else:
                    update_fields.append(f"{field} = ${param_idx}")
                    values.append(value)
                param_idx += 1
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        values.append(test_id)
        update_query = f"""
            UPDATE cookie_ab_tests SET
                {', '.join(update_fields)},
                updated_at = NOW()
            WHERE id = ${param_idx}
            RETURNING id
        """
        
        result = await db_pool.fetchrow(update_query, *values)
        
        return {
            "success": True,
            "message": "Test updated",
            "test_id": result['id']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating A/B test: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update test: {str(e)}")


@router.post("/{test_id}/start")
async def start_ab_test(
    test_id: int,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """Start an A/B test"""
    try:
        # Check test exists and status
        check_query = "SELECT site_id, status FROM cookie_ab_tests WHERE id = $1"
        test = await db_pool.fetchrow(check_query, test_id)
        
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        
        if test['status'] not in ['draft', 'paused']:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot start test in '{test['status']}' status"
            )
        
        # Check no other running test for this site
        active_query = """
            SELECT id FROM cookie_ab_tests 
            WHERE site_id = $1 AND status = 'running' AND id != $2
        """
        active = await db_pool.fetchrow(active_query, test['site_id'], test_id)
        
        if active:
            raise HTTPException(
                status_code=400, 
                detail=f"Another test is already running for this site (ID: {active['id']})"
            )
        
        # Start test
        update_query = """
            UPDATE cookie_ab_tests SET
                status = 'running',
                start_date = COALESCE(start_date, NOW()),
                updated_at = NOW()
            WHERE id = $1
            RETURNING start_date
        """
        
        result = await db_pool.fetchrow(update_query, test_id)
        
        return {
            "success": True,
            "message": "Test started",
            "test_id": test_id,
            "status": "running",
            "start_date": result['start_date'].isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error starting A/B test: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start test: {str(e)}")


@router.post("/{test_id}/stop")
async def stop_ab_test(
    test_id: int,
    winner: Optional[str] = None,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """Stop an A/B test and optionally declare a winner"""
    try:
        # Check test exists
        check_query = "SELECT status FROM cookie_ab_tests WHERE id = $1"
        test = await db_pool.fetchrow(check_query, test_id)
        
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        
        if test['status'] != 'running':
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot stop test in '{test['status']}' status"
            )
        
        # Validate winner
        if winner and winner not in ['A', 'B']:
            raise HTTPException(status_code=400, detail="Winner must be 'A' or 'B'")
        
        # Stop test
        update_query = """
            UPDATE cookie_ab_tests SET
                status = 'completed',
                winner = $2,
                end_date = NOW(),
                updated_at = NOW()
            WHERE id = $1
            RETURNING end_date
        """
        
        result = await db_pool.fetchrow(update_query, test_id, winner)
        
        return {
            "success": True,
            "message": "Test stopped",
            "test_id": test_id,
            "status": "completed",
            "winner": winner,
            "end_date": result['end_date'].isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error stopping A/B test: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop test: {str(e)}")


# ============================================================================
# Variant Assignment Endpoint (for Banner)
# ============================================================================

@router.get("/assign/{site_id}/{visitor_id}")
async def get_variant_assignment(
    site_id: str,
    visitor_id: str,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Get the banner variant for a visitor
    
    Returns the assigned variant and its configuration.
    Assignment is persistent (same visitor always gets same variant).
    """
    try:
        # Find active test for site
        test_query = """
            SELECT id, variant_a_config, variant_b_config, traffic_split
            FROM cookie_ab_tests
            WHERE site_id = $1 AND status = 'running'
            LIMIT 1
        """
        
        test = await db_pool.fetchrow(test_query, site_id)
        
        if not test:
            # No active test - return None
            return {
                "success": True,
                "has_test": False,
                "variant": None,
                "config": None
            }
        
        visitor_hash = hash_visitor_id(visitor_id)
        
        # Check existing assignment
        assignment_query = """
            SELECT variant FROM cookie_ab_assignments
            WHERE test_id = $1 AND visitor_hash = $2
        """
        
        assignment = await db_pool.fetchrow(assignment_query, test['id'], visitor_hash)
        
        if assignment:
            variant = assignment['variant']
        else:
            # Assign new variant based on hash (deterministic)
            hash_value = int(visitor_hash[:8], 16)
            threshold = test['traffic_split'] * (0xFFFFFFFF / 100)
            variant = 'A' if hash_value < threshold else 'B'
            
            # Store assignment
            insert_query = """
                INSERT INTO cookie_ab_assignments (test_id, visitor_hash, variant)
                VALUES ($1, $2, $3)
                ON CONFLICT (test_id, visitor_hash) DO NOTHING
            """
            await db_pool.execute(insert_query, test['id'], visitor_hash, variant)
        
        # Get config for variant
        config = test['variant_a_config'] if variant == 'A' else test['variant_b_config']
        
        return {
            "success": True,
            "has_test": True,
            "test_id": test['id'],
            "variant": variant,
            "config": config
        }
        
    except Exception as e:
        print(f"Error getting variant assignment: {e}")
        # Fallback: no test
        return {
            "success": False,
            "has_test": False,
            "variant": None,
            "config": None,
            "error": str(e)
        }


@router.post("/track")
async def track_ab_result(
    result: ABTestResult,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """
    Track an A/B test result (impression, conversion)
    
    Called by the cookie banner when a visitor interacts.
    """
    try:
        today = date.today()
        
        # Upsert result
        upsert_query = """
            INSERT INTO cookie_ab_results (
                test_id, variant, date,
                impressions, accepted_all, accepted_partial, rejected_all,
                accepted_analytics, accepted_marketing, accepted_functional,
                avg_decision_time_ms
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (test_id, variant, date) DO UPDATE SET
                impressions = cookie_ab_results.impressions + EXCLUDED.impressions,
                accepted_all = cookie_ab_results.accepted_all + EXCLUDED.accepted_all,
                accepted_partial = cookie_ab_results.accepted_partial + EXCLUDED.accepted_partial,
                rejected_all = cookie_ab_results.rejected_all + EXCLUDED.rejected_all,
                accepted_analytics = cookie_ab_results.accepted_analytics + EXCLUDED.accepted_analytics,
                accepted_marketing = cookie_ab_results.accepted_marketing + EXCLUDED.accepted_marketing,
                accepted_functional = cookie_ab_results.accepted_functional + EXCLUDED.accepted_functional,
                avg_decision_time_ms = (
                    cookie_ab_results.avg_decision_time_ms * cookie_ab_results.impressions + 
                    EXCLUDED.avg_decision_time_ms
                ) / (cookie_ab_results.impressions + 1),
                updated_at = NOW()
        """
        
        await db_pool.execute(
            upsert_query,
            result.test_id,
            result.variant,
            today,
            result.impressions,
            result.accepted_all,
            result.accepted_partial,
            result.rejected_all,
            result.accepted_analytics,
            result.accepted_marketing,
            result.accepted_functional,
            result.avg_decision_time_ms
        )
        
        return {
            "success": True,
            "message": "Result tracked"
        }
        
    except Exception as e:
        print(f"Error tracking A/B result: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to track result: {str(e)}")


@router.delete("/{test_id}")
async def delete_ab_test(
    test_id: int,
    db_pool: asyncpg.Pool = Depends(get_db_connection)
):
    """Delete an A/B test (only draft or completed tests)"""
    try:
        # Check test exists and status
        check_query = "SELECT status FROM cookie_ab_tests WHERE id = $1"
        test = await db_pool.fetchrow(check_query, test_id)
        
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        
        if test['status'] == 'running':
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete running test. Stop it first."
            )
        
        # Delete test (cascades to results and assignments)
        await db_pool.execute("DELETE FROM cookie_ab_tests WHERE id = $1", test_id)
        
        return {
            "success": True,
            "message": "Test deleted",
            "test_id": test_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting A/B test: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete test: {str(e)}")

