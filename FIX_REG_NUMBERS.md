# Incomplete Vehicle Registration Numbers - Fix Guide

## Problem
Some vehicles in the database have incomplete registration numbers:
- **Incomplete**: AFG, AGV (just letters)
- **Complete**: AFG 1234, AGV 2893 (letters + numbers)

This is a **data issue** - the full registration numbers were never entered when the vehicles were added to the system.

## How to Fix

### Step 1: Identify Incomplete Registrations
Run the diagnostic script to see which vehicles need updating:
```bash
python fix_incomplete_reg_numbers.py
```

This will show you a list like:
```
⚠️  INCOMPLETE: ID=1  | Reg: 'AFG'      | Model: Toyota Corolla
⚠️  INCOMPLETE: ID=3  | Reg: 'AGV'      | Model: Toyota Fortuner
✓  COMPLETE:   ID=2  | Reg: 'AGV 2893' | Model: Mazda 6
```

### Step 2: Update Registration Numbers

For each vehicle with an incomplete registration:

1. **Login as Admin**
2. **Go to**: Admin Dashboard → Manage Vehicles
3. **Find the vehicle** with the incomplete reg number
4. **Click the Edit button** (pencil icon)
5. **Update the "Registration Number" field** with the complete number
   - Example: Change "AFG" to "AFG 5432"
   - Example: Change "AGV" to "AGV 7891"
6. **Click "Update Vehicle"**

### Step 3: Verify the Fix
- Go to Admin Dashboard → Handovers → Review Handovers
- Check the "Completed Handovers" table
- All registration numbers should now display completely

## Why This Happened
When vehicles were initially added to the system, only the letter prefix was entered in the "Registration Number" field, without the numeric portion. The system stores exactly what is entered, so "AFG" was saved as is.

## Prevention
When adding new vehicles, always enter the **complete registration number**:
- ✅ CORRECT: "AFG 5432", "AGV 2893", "ABC 1234"
- ❌ INCORRECT: "AFG", "AGV", "ABC"

The registration number field accepts up to 32 characters, so there's plenty of space for the full number.
