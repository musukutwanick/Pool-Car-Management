# Email Notifications - Complete Setup Guide

## ✅ System is Configured and Ready!

**Django WILL send emails automatically** using the email addresses stored in your user accounts (managed via MIS Admin dashboard).

---

## 📧 How It Works

### Current Setup (Development Mode)
- **Email Backend**: Console (prints emails to terminal)
- **Password Required**: ❌ No (testing mode)
- **Emails Go To**: Console output (not actual inboxes)
- **User Emails**: ✅ All 7 users have email addresses configured

### Production Setup (Real Emails)
- **Email Backend**: SMTP (Outlook)
- **Password Required**: ✅ Yes (App Password from Microsoft)
- **Emails Go To**: Real email inboxes at addresses in database
- **User Emails**: Uses emails from User.email field (managed in admin)

---

## 🔄 Exact Email Workflow (As Requested)

### For GENERAL EMPLOYEES:
```
Employee submits request
    ↓
📧 Email → Immediate Supervisor
    ↓
Supervisor approves
    ↓
📧 Email → Respective GM (division-specific)
    ↓
GM approves
    ↓
📧 Email → Admin (ONLY - no employee notification yet)
    ↓
Admin assigns vehicle
    ↓
📧 Email → Employee (who requested the car)
```

### For MANAGERS:
```
Manager submits request
    ↓
📧 Email → CEO
    ↓
CEO approves
    ↓
📧 Email → Admin (ONLY - no manager notification yet)
    ↓
Admin assigns vehicle
    ↓
📧 Email → Manager (telling them request approved & vehicle assigned)
```

---

## ✅ What's Already Working

1. **Email Functions**: All notification functions created in `fleet/email_notifications.py`
2. **Signal Handlers**: Automatic triggers in `fleet/signals.py` fire emails at each approval step
3. **User Emails**: System pulls email addresses from `User.email` field (managed via admin dashboard)
4. **Testing Mode**: Currently set to console backend - emails print to terminal (no password needed)

---

## 🚀 To Enable Real Email Sending

### Option 1: Keep Testing Mode (Current)
**No changes needed!** Emails will print to terminal when you run the server.

### Option 2: Enable Real SMTP (Outlook)

#### Step 1: Get Outlook App Password

1. Go to: https://account.microsoft.com/security
2. Enable **Two-Factor Authentication** (if not already enabled)
3. Go to **App passwords** section
4. Click **Generate new app password**
5. Copy the **16-character password** (e.g., `abcd efgh ijkl mnop`)

#### Step 2: Create `.env` File

Create a file named `.env` in your project root (same folder as `manage.py`):

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Email Configuration - REAL EMAILS
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=poolcar@cellinsurance.com
EMAIL_HOST_PASSWORD=abcd efgh ijkl mnop
DEFAULT_FROM_EMAIL=poolcar@cellinsurance.com
```

**Important Notes:**
- Replace `poolcar@cellinsurance.com` with your actual Outlook email
- Replace `abcd efgh ijkl mnop` with the app password from Step 1
- Use the **app password**, NOT your regular Outlook password
- Keep the `.env` file private (it's in `.gitignore` by default)

#### Step 3: Restart Server

Stop the server (Ctrl+C) and restart:

```powershell
.venv\Scripts\python.exe manage.py runserver
```

---

## 🧪 Testing the Email Flow

### Test 1: Employee Request Flow

1. **Start Server** (keep terminal visible):
   ```powershell
   .venv\Scripts\python.exe manage.py runserver
   ```

2. **Submit Request** (as employee):
   - Login as employee
   - Go to "Request Vehicle"
   - Fill form and submit
   - ✅ Check terminal/inbox for **email to supervisor**

3. **Supervisor Approves**:
   - Login as supervisor/manager
   - Approve the request
   - ✅ Check terminal/inbox for **email to GM**

4. **GM Approves**:
   - Login as GM
   - Approve the request
   - ✅ Check terminal/inbox for **email to admin** (admin only, not employee yet)

5. **Admin Assigns Vehicle**:
   - Login as admin
   - Assign vehicle to request
   - ✅ Check terminal/inbox for **email to employee**

### Test 2: Manager Request Flow

1. **Manager submits** → ✅ Email to CEO
2. **CEO approves** → ✅ Email to admin (admin only)
3. **Admin assigns** → ✅ Email to manager

---

## 📁 Key Files

### Email Logic
- **`fleet/email_notifications.py`**: All email sending functions
- **`fleet/signals.py`**: Automatic triggers for approval workflow
- **`poolcar/settings.py`**: Email configuration (reads from `.env`)

### User Email Management
Users' email addresses are managed in the **Django admin** or **MIS Admin dashboard**:
- Go to: http://localhost:8000/admin/auth/user/
- Edit any user and set their **Email address** field
- These emails are automatically used by the notification system

---

## 🔍 Troubleshooting

### Emails Not Sending?

1. **Check email backend**:
   ```powershell
   .venv\Scripts\python.exe test_email_workflow.py
   ```
   Should show "Using CONSOLE backend" or "Using SMTP backend"

2. **Verify user emails**:
   - All approvers must have email addresses in database
   - Check via admin dashboard or run the test script above

3. **SMTP errors** (if using real emails):
   - Verify app password is correct (16 characters, may have spaces)
   - Ensure 2FA is enabled on Microsoft account
   - Check EMAIL_HOST_USER matches the account that generated the app password

4. **Check server logs**:
   - Emails are logged with `logger.info()` statements
   - Look for lines like "Email sent successfully to..."

### Emails Going to Wrong People?

- Email addresses are pulled from User.email field
- Update via: http://localhost:8000/admin/auth/user/
- Changes take effect immediately (no restart needed)

---

## 🎯 Summary

✅ **Django WILL send emails automatically** - configured and ready  
✅ **Uses emails from MIS Admin dashboard** - User.email field  
✅ **No manual email sending** - signals trigger automatically  
✅ **Current mode**: Console (testing) - no password needed  
✅ **Production mode**: Add Outlook credentials to `.env` file  

### Email Flow Confirmed:
- ✅ Employee → Supervisor → GM → Admin → Employee
- ✅ Manager → CEO → Admin → Manager
- ✅ No premature notifications (employee only notified after vehicle assignment)

---

## 📞 Quick Reference

### Run Tests
```powershell
.venv\Scripts\python.exe test_email_workflow.py
```

### Start Server
```powershell
.venv\Scripts\python.exe manage.py runserver
```

### Switch to Real Emails
Create `.env` file with SMTP settings (see Step 2 above)
