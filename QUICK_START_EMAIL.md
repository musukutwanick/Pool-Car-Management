# Quick Start: Testing Email Notifications

## 1. Verify Setup (1 minute)
```bash
python test_email_setup.py
```
Should show:
- ✓ Signals registered
- ✓ Email backend configured
- ✓ Users have emails

## 2. Start Server
```bash
python manage.py runserver
```
**Important**: Keep this terminal window visible to see email output!

## 3. Test Complete Flow

### Step 1: Submit Request (Employee)
1. Login as employee: `employee1` / `password`
2. Navigate to "Request Vehicle"
3. Fill form:
   - Purpose: "Client meeting"
   - Destination: "Harare"
   - Start/End times: Tomorrow
   - Check "Out of Town" if testing CEO approval
4. Submit

**Expected**: Email to GM prints in server terminal

### Step 2: GM Approval
1. Logout, login as GM for that division:
   - Cell Insurance: `CellinsureGM` / `password`
   - CellMed: `CellmedGM` / `password`
   - Nectacare: `NectacareGM` / `password`
2. Go to "Pending Approvals"
3. Click "Approve"

**Expected**:
- If local trip: Email to Admin + Employee
- If out-of-town: Email to CEO

### Step 3: CEO Approval (if out-of-town)
1. Logout, login as CEO: `CEO` / `password`
2. Go to "Pending Approvals"
3. Click "Approve"

**Expected**: Email to Admin + Employee

### Step 4: Vehicle Assignment (Admin)
1. Logout, login as admin: `admin` / `password`
2. Go to "Vehicle Assignments"
3. Click "Assign" on the approved request
4. Select a vehicle
5. Submit

**Expected**: Email to Employee with vehicle details

## Sample Email Output

When working correctly, you'll see in terminal:
```
Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: 8bit
Subject: New Vehicle Request #0020 - Approval Required
From: noreply@cellinsurance.com
To: gm@example.com
Date: Mon, 16 Dec 2025 10:30:00 -0000
Message-ID: <...>

Hello CellInsure GM,

A new vehicle request has been submitted and requires your approval.

Request Details
Request ID: #0020
Requester: John Doe
Purpose: Client meeting
...
```

## Quick Fixes

### Not seeing emails?
```bash
# Check backend setting
python manage.py shell -c "from django.conf import settings; print(settings.EMAIL_BACKEND)"
```
Should output: `django.core.mail.backends.console.EmailBackend`

### Server errors?
```bash
python manage.py check
```

### Reset and retry?
```bash
# Clear test data
python delete_test_requests.py

# Create fresh test request
python create_test_requests.py
```

## What You Should See

✅ **On request submission**: GM notification email  
✅ **On GM approval (local)**: Admin + Employee emails  
✅ **On GM approval (out-of-town)**: CEO email  
✅ **On CEO approval**: Admin + Employee emails  
✅ **On vehicle assignment**: Employee email with vehicle details  

## Production Setup

Once testing is complete, to enable real emails:

1. Update `.env`:
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST_USER=your-outlook-email@company.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
```

2. Generate app password at: https://account.microsoft.com/security

3. Restart server

4. Test with real email addresses!

---

**Need help?** Check `EMAIL_NOTIFICATIONS.md` for detailed documentation.
