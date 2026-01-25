# Approval Workflow Documentation

## Overview
The approval system has been updated with inline approve/reject buttons and automatic routing between GMs and CEO.

## Approval Flow

### Local Requests (out_of_town = False)
1. **Employee** submits request
2. **GM** sees request on their pending approvals page
3. **GM** clicks "Approve" or "Reject" (inline buttons)
4. If approved → Status changes to `'approved'` and appears on Admin dashboard
5. **Admin** assigns vehicle from Vehicle Assignments page

### Out-of-Town Requests (out_of_town = True)
1. **Employee** submits request
2. **GM** sees request on their pending approvals page
3. **GM** clicks "Approve" or "Reject" (inline buttons)
4. If approved by GM → Request stays `'pending'` but has `approver1` set
5. **CEO** now sees the request on CEO pending approvals page
6. **CEO** clicks "Approve" or "Reject" (inline buttons)
7. If CEO approves → Status changes to `'approved'` and appears on Admin dashboard
8. **Admin** assigns vehicle from Vehicle Assignments page

## Button Actions

### GM Pending Approvals Page
**Location:** `/gm/approvals/`

**Buttons:**
- ✅ **Approve** (green) - Approves the request
  - Local requests: Sets status to 'approved'
  - Out-of-town: Sets approver1, keeps pending for CEO
- ❌ **Reject** (red) - Sets status to 'rejected'

### CEO Pending Approvals Page
**Location:** `/ceo/approvals/`

**Buttons:**
- ✅ **Approve** (green) - Sets status to 'approved' (ready for admin assignment)
- ❌ **Reject** (red) - Sets status to 'rejected'

## Admin Dashboard Updates

### New Alert Card
**Title:** "Approved Requests Ready for Assignment"

**Shows:** Count of requests with `status='approved'`

**Action:** Clicking the card navigates to Vehicle Assignments page

**Purpose:** Alerts admin when GM/CEO have approved requests that need vehicle assignment

## Technical Details

### View Changes
- `gm_approve_request()`: 
  - Now requires POST method
  - Routes differently based on `out_of_town` flag
  - Clear success messages indicate next steps

- `gm_reject_request()`:
  - Now requires POST method
  - Uses warning message for rejections

- `ceo_approve_request()`:
  - Now requires POST method
  - Always sets status to 'approved' (no conditional logic)
  - Clear success message

- `ceo_reject_request()`:
  - Now requires POST method
  - Uses warning message for rejections

- `admin_dashboard()`:
  - Added `approved_requests` count to context

### Template Changes
- **gm_pending_approvals.html**: Replaced single "Review" button with inline "Approve" and "Reject" buttons
- **ceo_pending_approvals.html**: Replaced single "Review" button with inline "Approve" and "Reject" buttons
- **admin/dashboard.html**: Added new alert card for approved requests

### Approval States

| Status    | Meaning                           | Visible To        |
|-----------|-----------------------------------|-------------------|
| pending   | Awaiting approval                 | GM or CEO         |
| approved  | Ready for vehicle assignment      | Admin             |
| assigned  | Vehicle assigned                  | Admin, Employee   |
| rejected  | Rejected by GM or CEO             | Employee          |
| completed | Trip completed, vehicle returned  | Admin, Employee   |
| cancelled | Cancelled by employee             | Employee          |

## User Experience

### For GMs
1. Navigate to Pending Approvals
2. Review request details in the table
3. Click "Approve" or "Reject" directly
4. Confirmation dialog appears
5. Success/warning message shows next step
6. Request disappears from pending list

### For CEO
1. Navigate to Pending Approvals (only out-of-town requests appear)
2. Review request details in the table
3. Click "Approve" or "Reject" directly
4. Confirmation dialog appears
5. Success/warning message shows approval
6. Request disappears from pending list

### For Admin
1. Dashboard shows count of approved requests
2. Click "Approved Requests Ready for Assignment" card
3. Navigate to Vehicle Assignments page
4. Assign vehicles to approved requests
