# Implementation Plan: Project Refactoring & Integration

**Objective:** Fix all identified issues and create a properly connected, production-ready codebase

**Estimated Time:** 2-3 hours  
**Priority:** HIGH

---

## Phase 1: Module Structure & Imports ⚙️

### Task 1.1: Create Python Package Structure
**Status:** 🔴 Not Started

**Action Items:**
- [ ] Create `src/__init__.py`
- [ ] Create `src/data/__init__.py`
- [ ] Create `src/database/__init__.py`
- [ ] Create `src/models/__init__.py`
- [ ] Create `src/visualization/__init__.py`
- [ ] Create `src/features/__init__.py`

**Expected Outcome:** Proper Python module imports work correctly

---

### Task 1.2: Remove Duplicate Code
**Status:** 🔴 Not Started

**Action Items:**
- [ ] Compare `src/data/build_features.py` vs `src/features/build_features.py`
- [ ] Keep `src/data/build_features.py` as canonical version
- [ ] Delete `src/features/build_features.py` OR repurpose for advanced features
- [ ] Update all imports referencing the removed file

**Expected Outcome:** Single source of truth for feature engineering

---

## Phase 2: Configuration Management 🔧

### Task 2.1: Create Centralized Config
**Status:** 🔴 Not Started

**Action Items:**
- [ ] Create `config.py` with all paths and constants
- [ ] Define PROJECT_ROOT, DATA_DIR, MODELS_DIR, etc.
- [ ] Create separate configs for dev/prod environments
- [ ] Replace all hardcoded paths with config references

**File to Create:**
```python
# config.py
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
DB_PATH = DATA_DIR / "transport.db"

# Add all configuration
```

---

### Task 2.2: Setup Environment File
**Status:** 🔴 Not Started

**Action Items:**
- [ ] Copy `.env.example` to `.env`
- [ ] Add placeholder API keys
- [ ] Document how to get API keys in README
- [ ] Add `.env` to `.gitignore`

---

## Phase 3: Database Standardization 🗄️

### Task 3.1: Standardize Column Names
**Status:** 🔴 Not Started

**Problem:** Inconsistent naming (snake_case in DB, PascalCase in data files)

**Decision:** Use **snake_case** everywhere (Python convention)

**Action Items:**
- [ ] Update `src/database/db_config.py` schema (already snake_case ✅)
- [ ] Update all data generation to use snake_case
- [ ] Update all queries to use snake_case
- [ ] Update app.py to use snake_case
- [ ] Update engine.py to use snake_case

**Files to Modify:**
1. `src/data/make_dataset.py` - Column names in DataFrame
2. `src/data/clean_data.py` - Column references
3. `src/data/build_features.py` - Column references
4. `src/models/train_model.py` - Feature names
5. `src/models/engine.py` - Field access
6. `src/database/queries.py` - Query column names
7. `app.py` - All dict key access

---

### Task 3.2: Fix Database Migration
**Status:** 🔴 Not Started

**Action Items:**
- [ ] Review `src/database/migrate_data.py`
- [ ] Ensure column mapping matches schema
- [ ] Add data validation
- [ ] Add rollback capability
- [ ] Test migration with sample data

---

## Phase 4: Pipeline Integration 🔗

### Task 4.1: Create Main Orchestrator
**Status:** 🔴 Not Started

**Action Items:**
- [ ] Create `main.py` in project root
- [ ] Implement step-by-step pipeline execution
- [ ] Add progress logging
- [ ] Add error handling for each step
- [ ] Add option to skip completed steps

**Pipeline Stages:**
```python
1. Generate Data (make_dataset.py)
2. Clean Data (clean_data.py)
3. Build Features (build_features.py)
4. Train Model (train_model.py)
5. Evaluate Model (evaluate_model.py)
6. Initialize Database (db_config.py)
7. Migrate Data (migrate_data.py)
8. Run Tests (optional)
```

---

### Task 4.2: Add Comprehensive Logging
**Status:** 🔴 Not Started

**Action Items:**
- [ ] Create `src/utils/logger.py`
- [ ] Configure logging levels (DEBUG, INFO, WARNING, ERROR)
- [ ] Add log rotation
- [ ] Add timestamps
- [ ] Log to both console and file

**File to Create:**
```python
# src/utils/logger.py
import logging
import sys
from pathlib import Path

def setup_logger(name, log_file=None, level=logging.INFO):
    # Logger configuration
    pass
```

---

## Phase 5: Code Quality & Testing 🧪

### Task 5.1: Add Error Handling
**Status:** 🔴 Not Started

**Action Items:**
- [ ] Add try-except blocks to all critical sections
- [ ] Create custom exception classes
- [ ] Add input validation
- [ ] Add file existence checks
- [ ] Add API response validation

**Files to Update:**
- All `src/` modules
- `app.py`

---

### Task 5.2: Create Integration Tests
**Status:** 🔴 Not Started

**Action Items:**
- [ ] Create `tests/` directory
- [ ] Create `tests/test_pipeline.py`
- [ ] Create `tests/test_api.py`
- [ ] Create `tests/test_database.py`
- [ ] Add pytest configuration

---

## Phase 6: Documentation 📚

### Task 6.1: Update README
**Status:** 🔴 Not Started

**Action Items:**
- [ ] Add detailed setup instructions
- [ ] Document API endpoints
- [ ] Add screenshots
- [ ] Add troubleshooting section
- [ ] Add contribution guidelines

---

### Task 6.2: Add Inline Documentation
**Status:** 🔴 Not Started

**Action Items:**
- [ ] Add docstrings to all classes
- [ ] Add docstrings to all functions
- [ ] Add type hints
- [ ] Add usage examples

---

## Phase 7: Final Integration & Testing ✅

### Task 7.1: End-to-End Testing
**Status:** 🔴 Not Started

**Action Items:**
- [ ] Run complete pipeline from scratch
- [ ] Test all Flask routes
- [ ] Test with different input combinations
- [ ] Verify database integrity
- [ ] Check model predictions

---

### Task 7.2: Performance Optimization
**Status:** 🔴 Not Started

**Action Items:**
- [ ] Profile slow functions
- [ ] Add database indexing
- [ ] Implement caching where appropriate
- [ ] Optimize ML model loading

---

## Implementation Order (Step-by-Step)

### 🚀 Immediate Actions (Next 30 minutes)
1. Create all `__init__.py` files
2. Create `config.py`
3. Create `.env` file
4. Standardize column names across all files

### ⚙️ Core Fixes (Next 1 hour)
5. Update all path references to use config
6. Fix database migration
7. Remove duplicate code
8. Add basic error handling

### 🔗 Integration (Next 30 minutes)
9. Create `main.py` orchestrator
10. Add logging system
11. Test pipeline end-to-end

### ✨ Polish (Final 30 minutes)
12. Update documentation
13. Add code comments
14. Final testing
15. Create deployment guide

---

## Success Criteria

✅ All Python modules import correctly  
✅ Single command runs entire pipeline  
✅ Database schema matches data  
✅ All Flask routes work  
✅ No hardcoded paths  
✅ Proper error messages  
✅ Comprehensive logging  
✅ Updated documentation  
✅ Zero critical bugs  

---

## Rollback Plan

If issues occur:
1. Git commit before each phase
2. Keep backup of original files
3. Test each change incrementally
4. Document any breaking changes

---

## Notes

- Maintain backward compatibility where possible
- Don't break existing functionality
- Test after each major change
- Keep user informed of progress

---

**Ready to Execute:** YES ✅

**Start Time:** [To be filled]  
**End Time:** [To be filled]  
**Status:** IN PROGRESS 🔄
