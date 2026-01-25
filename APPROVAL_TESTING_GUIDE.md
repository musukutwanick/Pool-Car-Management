# Approval Testing Guide

## Current Database State

The system now has approval requests properly set up for testing:

### CEO Dashboard Approvals
**URL:** `/ceo/approvals/`

**Filter:** `status='pending'` AND `out_of_town=True`

**Current Count:** 2 requests
- Request #3: Site Visit (cell_insurance)
- Request #4: Business trip to Bulawayo for client presentation (cell_insurance)

### GM Dashboard Approvals

#### Cell Insurance GM
**URL:** `/gm/approvals/?division=Cell%20Insurance`

**Filter:** `status='pending'` AND `out_of_town=False` AND `subsidiary='cell_insurance'`

**Current Count:** 1 request
- Request #5: Client meeting in Harare CBD

#### Cellmed GM
**URL:** `/gm/approvals/?division=Cellmed`

**Filter:** `status='pending'` AND `out_of_town=False` AND `subsidiary='cellmed'`

**Current Count:** 1 request
- Request #6: Cellmed office visit and equipment pickup

#### Nectacare GM
**URL:** `/gm/approvals/?division=Nectacare`

**Filter:** `status='pending'` AND `out_of_town=False` AND `subsidiary='nectacare'`

**Current Count:** 1 request
- Request #7: Nectacare facility inspection

## How to Test

1. **Test CEO Approvals:**
   - Sign in as a CEO user
   - Navigate to the CEO dashboard
   - Click "Pending Approvals" in the sidebar
   - You should see 2 requests (both marked "Out of Town")

2. **Test GM Approvals:**
   - Sign in as a GM user (or navigate to a specific GM dashboard)
   - For Cell Insurance GM: `/dashboard/gm-cellinsure/` → Click "Pending Approvals"
   - For Cellmed GM: `/dashboard/gm-cellmed/` → Click "Pending Approvals"
   - For Nectacare GM: `/dashboard/gm-nectacare/` → Click "Pending Approvals"
   - Each GM should see 1 request for their division

## Key Business Rules

1. **Out-of-town requests** (out_of_town=True) → CEO approval required
2. **Local requests** (out_of_town=False) → GM approval required (by subsidiary)
3. Only requests with `status='pending'` appear in approval queues
4. Once assigned or approved, requests disappear from pending lists

## Troubleshooting

If approvals don't appear:

1. **Check request status:**
   ```powershell
   python verify_requests.py
   ```

2. **Verify filters match:**
   - CEO sees: pending + out_of_town=True
   - GM sees: pending + out_of_town=False + matching subsidiary

3. **Clear browser cache** if templates don't update

## Utility Scripts

- `create_test_requests.py` - Creates sample approval requests
- `verify_requests.py` - Shows current database state

## Next Steps

After testing approvals, you can:
- Approve/reject requests using the "Review" button
- Assign vehicles to approved requests via the admin dashboard
- Clean up test data by deleting or marking requests as completed
