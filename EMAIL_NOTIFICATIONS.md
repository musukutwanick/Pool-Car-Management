# Email Notifications Setup Guide

## Overview
The Pool Car Management System now sends automatic email notifications at key workflow stages using Outlook SMTP.

## Email Triggers

### 1. Employee Submits Request → GM Notified
- **When**: Employee creates a new vehicle request
- **Recipient**: Division GM (based on subsidiary: Cell Insurance, Cellmed, or Nectacare)
- **Content**: Request details, purpose, destination, dates, driver requirement

### 2. GM Approves Long-Distance → CEO Notified
- **When**: GM approves an out-of-town request
- **Recipient**: CEO
- **Content**: Request details with GM approval confirmation

### 3. Final Approval → Admin & Employee Notified
- **When**: Request receives final approval (GM only for local, GM+CEO for long-distance)
- **Recipients**: 
  - All Fleet Admins (for vehicle assignment)
  - Employee (confirmation of approval)
- **Content**: 
  - Admin: Action required to assign vehicle
  - Employee: Approval confirmation

### 4. Vehicle Assigned → Employee Notified
- **When**: Admin assigns a vehicle to an approved request
- **Recipient**: Employee
- **Content**: Vehicle details (reg number, model, fuel type), pickup time

## Configuration

### Development Setup (Console Backend)
By default, emails print to the terminal for testing:

```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Run the server and watch the terminal for email output when triggers occur.

### Production Setup (Outlook SMTP)

1. **Update .env file**:
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-company-email@outlook.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-company-email@outlook.com
```

2. **Generate Outlook App Password**:
   - Go to https://account.microsoft.com/security
   - Enable 2-factor authentication if not enabled
   - Navigate to "Security" → "Advanced security options"
   - Under "App passwords", generate a new password
   - Use this app password in EMAIL_HOST_PASSWORD (not your regular password)

3. **For Microsoft 365/Office 365**:
   - May require admin to enable SMTP AUTH
   - Check with IT if smtp-mail.outlook.com doesn't work
   - Alternative host: smtp.office365.com

## User Email Requirements

For notifications to work, users must have valid email addresses:

1. **Employees**: Set email in Django admin or during user creation
2. **GMs**: Each subsidiary should have a GM with a valid email
3. **CEO**: CEO user must have email configured
4. **Admins**: All admin users will receive notifications

Check user emails in MIS Dashboard → Manage Users.

## Testing

### Test Email Flow
1. Start server: `python manage.py runserver`
2. Login as employee
3. Submit a vehicle request
4. Check terminal for email output (console backend) or inbox (SMTP backend)
5. Login as GM → approve request
6. Check for CEO notification (if out-of-town) or admin/employee notification
7. Login as admin → assign vehicle
8. Check employee receives vehicle assignment email

### Verify Signal Registration
```bash
python manage.py shell
```
```python
from django.db.models.signals import post_save
from fleet.models import CarRequest

# Check if signals are connected
print(post_save.receivers)  # Should show fleet.signals handlers
```

## Troubleshooting

### Emails not sending
1. Check EMAIL_BACKEND in .env (should be smtp for production)
2. Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are correct
3. Check logs for errors: `tail -f logs/django.log`
4. Ensure users have valid email addresses
5. For Outlook: confirm app password is being used

### Duplicate emails
- Signals are configured to prevent duplicates
- Only state changes trigger emails (not repeated saves with same values)

### SMTP Authentication Error
- Generate new app password from Microsoft account
- Verify 2FA is enabled
- Try smtp.office365.com instead of smtp-mail.outlook.com
- Contact IT if organizational policies block SMTP

### No GM/CEO found
- Ensure GM profile exists for each subsidiary (cell_insurance, cellmed, nectacare)
- Ensure CEO profile exists with role='ceo'
- Check in MIS Dashboard → Manage Users

## Files Created/Modified

- `fleet/email_notifications.py` - Email utility functions
- `fleet/signals.py` - Signal handlers for triggering emails
- `fleet/apps.py` - Signal registration in ready()
- `fleet/views.py` - Updated to use .save() for signal triggers
- `poolcar/settings.py` - Email configuration
- `.env.example` - Email configuration template

## Email Templates

HTML emails are generated inline in `email_notifications.py`. To customize:
1. Edit template strings in each notify_* function
2. Update colors, styling, or content
3. Restart server for changes to take effect

For production, consider:
- Moving templates to separate HTML files
- Using Django template system for email rendering
- Adding company logo to emails
- Customizing email styling to match branding
