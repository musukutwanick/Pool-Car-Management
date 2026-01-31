# 🚀 Ambulance Manager - Quick Start Guide

## Getting Started in 3 Minutes

### Step 1: Access the System
1. Open your browser and go to: `http://localhost:8000/`
2. You'll see two module options:
   - **Pool Car Manager** (yellow theme)
   - **Ambulance Manager** (orange theme)

### Step 2: Login
Click on **Ambulance Manager** and use one of these test accounts:

**Ambulance Admin (Full Access):**
- Username: `ambulance_admin`
- Password: `admin123`

**Nectacare Head (Read-Only):**
- Username: `nectacare_head`
- Password: `head123`

### Step 3: Start Managing Your Fleet

#### As Ambulance Admin:

**Add Your First Ambulance:**
1. Click **"Add Ambulance"** in the sidebar
2. Fill in:
   - Registration Number (e.g., `AAA 1234`)
   - Model (e.g., `Toyota Hiace Ambulance`)
   - Status: `Available`
   - Current Mileage: `0`
3. Click **"Add Ambulance"**

**Record Usage:**
1. Click **"Record Usage"** in sidebar
2. Select the ambulance
3. Enter start and end mileage
4. Add fuel details (optional)
5. Upload receipt (optional)
6. Click **"Record Usage"**

**View Statistics:**
- Click **"Statistics"** to see:
  - Total trips in last 30/90 days
  - Total distance covered
  - Fuel costs
  - Per-ambulance breakdown

---

## 🎯 Key Features at a Glance

### Ambulance Admin Can:
✅ Add, edit, and manage ambulances  
✅ Record trip usage and mileage  
✅ Upload fuel and service receipts  
✅ Track service schedules  
✅ View comprehensive statistics  
✅ Manage equipment inventory  

### Nectacare Head Can:
✅ View fleet status (read-only)  
✅ View usage reports  
✅ View service history  
✅ Monitor availability  
❌ Cannot add/edit ambulances  

---

## 📊 Dashboard Overview

### Ambulance Admin Dashboard
**Quick Stats:**
- Total Ambulances
- Available Now (green)
- On Call (blue)  
- In Maintenance (red)

**Notifications:**
- Service due alerts
- Pending requests
- Recent usage

### Sidebar Menu:
- 🏠 Home
- 🚑 Manage Fleet
- ➕ Add Ambulance
- 📊 Record Usage
- 📈 Statistics

---

## 🎨 Color Scheme
The Ambulance Manager uses Cell Insurance's secondary colors:

**Primary Orange:** #f99c31 (buttons, icons, accents)  
**Secondary Blue:** #1c75bc (status indicators)  
**Light Orange:** #ffe4cc (backgrounds)

---

## 🔐 Module Access

**Who can access Ambulance Manager?**
- Users with `role='ambulance_admin'` OR `role='nectacare_head'`
- Users with `module='ambulance'` OR `module='both'`

**Switching Between Modules:**
1. Click your avatar (top-right)
2. Select "Module Selection"
3. Choose Pool Car or Ambulance Manager

---

## 📱 Common Tasks

### Adding Multiple Ambulances
Navigate to **Add Ambulance** and repeat for each vehicle. You can add:
- Registration number (required)
- Model and year
- Current mileage
- Service interval (e.g., 10000 km)
- Base location
- Photo

### Recording Daily Usage
1. **Before Trip:** Note start mileage
2. **After Trip:** 
   - Go to **Record Usage**
   - Select ambulance
   - Enter start/end mileage
   - Add fuel details if refueled
   - Upload receipt
   - Save

### Checking Service Due
The dashboard automatically shows ambulances that need service:
- Alerts appear when <1000 km to service interval
- Red badge on "Service Due" notification card

### Viewing Reports
Click **Statistics** to see:
- **30-Day Stats:** Recent activity
- **90-Day Stats:** Quarterly overview
- **Per-Ambulance:** Individual performance

---

## 🆘 Troubleshooting

**Can't login?**
→ Verify username/password. Check your profile has correct role and module.

**Don't see ambulance options?**
→ Ensure migrations are applied: `python manage.py migrate`

**Access denied error?**
→ Your user profile needs `module='ambulance'` or `module='both'`

**Dashboard shows zero stats?**
→ Add ambulances and record usage first!

---

## 🔄 Workflow Example

**Typical Daily Workflow:**

**Morning:**
1. Login as `ambulance_admin`
2. Check dashboard for service alerts
3. Review available ambulances

**During Day:**
1. Ambulance dispatched → Update status to "On Call"
2. Trip completed → Record usage with mileage
3. Refueled → Upload fuel receipt

**Evening:**
1. Review daily statistics
2. Update ambulance status back to "Available"
3. Check maintenance schedule

**Weekly:**
1. Review usage reports
2. Schedule services for ambulances due
3. Check equipment inventory

---

## 📞 Need Help?

1. Check `MULTI_MODULE_IMPLEMENTATION.md` for full details
2. Review Django logs: Check terminal for errors
3. Verify database migrations: `python manage.py showmigrations`
4. Test with fresh users: Run `python create_ambulance_users.py` again

---

## ✅ Quick Checklist

- [ ] Database migrations applied
- [ ] Test users created
- [ ] Can access landing page
- [ ] Can login to Ambulance Manager
- [ ] Can add an ambulance
- [ ] Can record usage
- [ ] Can view statistics
- [ ] Module separation works (Pool Car users blocked)
- [ ] Both roles work (admin & head)

---

## 🎓 Next Steps

1. **Add Real Ambulances:** Start adding your actual fleet
2. **Configure Equipment:** Set up equipment checklists
3. **Train Users:** Show team how to record usage
4. **Review Reports:** Check statistics weekly
5. **Optimize:** Adjust service intervals based on usage

---

**You're all set!** 🚑  
Start managing your ambulance fleet efficiently with the new Ambulance Manager module.

*For detailed technical documentation, see `MULTI_MODULE_IMPLEMENTATION.md`*
