from django.db import models
from django.conf import settings
from django.utils import timezone


SUBSIDIARY_CHOICES = [
    ('cell_insurance', 'Cell Insurance'),
    ('cellmed', 'CellMed'),
    ('nectacare', 'Nectacare'),
]


class Vehicle(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('maintenance', 'Under Maintenance'),
        ('out_of_service', 'Out of Service'),
    ]

    reg_number = models.CharField(max_length=32, unique=True)
    vehicle_type = models.CharField(max_length=64, blank=True)
    model = models.CharField(max_length=128, blank=True)
    fuel_type = models.CharField(max_length=32, blank=True)
    engine_capacity = models.CharField(max_length=32, blank=True)
    image = models.ImageField(upload_to='vehicles/', null=True, blank=True)
    accessories = models.TextField(blank=True)
    service_interval_mileage = models.PositiveIntegerField(null=True, blank=True)
    current_mileage = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='available', db_index=True)
    subsidiary = models.CharField(max_length=32, choices=SUBSIDIARY_CHOICES, default='cell_insurance', db_index=True)
    branch = models.CharField(max_length=128, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['subsidiary']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.reg_number} — {self.model or self.vehicle_type}"
    
    @property
    def km_to_service(self):
        """Calculate kilometers remaining until next service."""
        if self.service_interval_mileage and self.current_mileage is not None:
            km_remaining = self.service_interval_mileage - self.current_mileage
            return km_remaining if km_remaining > 0 else 0
        return None
    
    @property
    def is_service_due(self):
        """Check if service is due or overdue."""
        if self.km_to_service is not None:
            return self.km_to_service <= 1000  # Alert when 1000km or less to service
        return False


class Profile(models.Model):
    USER_ROLES = [
        ('employee', 'Employee'),
        ('admin', 'Admin'),
        ('gm', 'GM'),
        ('ceo', 'CEO'),
        ('mis', 'MIS Admin'),
        ('driver', 'Driver'),
        ('ambulance_admin', 'Ambulance Admin'),
        ('ambulance_mis', 'Ambulance MIS Admin'),
        ('nectacare_head', 'Nectacare Head'),
    ]
    
    MODULE_CHOICES = [
        ('poolcar', 'Pool Car Manager'),
        ('ambulance', 'Ambulance Manager'),
        ('both', 'Both Modules'),
    ]
    
    EMPLOYEE_TYPE_CHOICES = [
        ('GENERAL_EMPLOYEE', 'General Employee'),
        ('MANAGER', 'Manager'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=32, choices=USER_ROLES, default='employee', db_index=True)
    module = models.CharField(max_length=32, choices=MODULE_CHOICES, default='poolcar', db_index=True, help_text='Which module(s) the user has access to')
    subsidiary = models.CharField(max_length=32, choices=SUBSIDIARY_CHOICES, default='cell_insurance', db_index=True)
    is_dedicated_driver = models.BooleanField(default=False, db_index=True)
    employee_type = models.CharField(max_length=32, choices=EMPLOYEE_TYPE_CHOICES, default='GENERAL_EMPLOYEE', help_text='Classification for approval routing')

    class Meta:
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['module']),
            models.Index(fields=['subsidiary']),
            models.Index(fields=['is_dedicated_driver']),
        ]

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
    
    @property
    def is_supervisor(self):
        """Check if this user can approve requests (Manager, GM, CEO, Admin roles)"""
        return self.role in ['admin', 'gm', 'ceo'] or self.employee_type == 'MANAGER'


class CarRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('assigned', 'Assigned'),
        ('completed', 'Completed'),
    ]

    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='car_requests')
    purpose = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True)
    out_of_town = models.BooleanField(default=False)
    needs_driver = models.BooleanField(default=False)
    subsidiary = models.CharField(max_length=32, choices=SUBSIDIARY_CHOICES, default='cell_insurance', db_index=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='pending', db_index=True)
    rejection_reason = models.TextField(blank=True, null=True, help_text='Reason for rejection if request was rejected')
    selected_supervisor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='supervised_requests', help_text='Supervisor selected by employee at request time')
    supervisor_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='supervisor_approvals', help_text='Supervisor approval for general employees')
    gm_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='gm_approvals', help_text='GM approval')
    ceo_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='ceo_approvals', help_text='CEO approval for managers')
    approver1 = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='approvals_level1', help_text='Legacy field - kept for backward compatibility')
    approver2 = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='approvals_level2', help_text='Legacy field - kept for backward compatibility')
    assigned_vehicle = models.ForeignKey(Vehicle, null=True, blank=True, on_delete=models.SET_NULL)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['subsidiary']),
            models.Index(fields=['requester', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status', 'assigned_vehicle']),
        ]

    def __str__(self):
        return f"Request {self.id} by {self.requester.username} ({self.status})"

    @property
    def request_code(self):
        """Return a zero-padded 4-digit request code (e.g. 0001)."""
        if self.id is None:
            return None
        return f"{self.id:04d}"
    
    @property
    def requester_employee_type(self):
        """Get the employee type of the requester."""
        if hasattr(self.requester, 'profile'):
            return self.requester.profile.employee_type
        return 'GENERAL_EMPLOYEE'  # Default
    
    @property
    def needs_supervisor_approval(self):
        """Determine if request needs supervisor approval (General Employees only)."""
        return self.requester_employee_type == 'GENERAL_EMPLOYEE'
    
    @property
    def needs_gm_approval(self):
        """Determine if request needs GM approval (General Employees only)."""
        return self.requester_employee_type == 'GENERAL_EMPLOYEE'
    
    @property
    def needs_ceo_approval(self):
        """Determine if request needs CEO approval (Managers only)."""
        return self.requester_employee_type == 'MANAGER'
    
    @property
    def is_fully_approved(self):
        """Check if request has completed all required approvals."""
        if self.requester_employee_type == 'GENERAL_EMPLOYEE':
            # General employees need Supervisor → GM approvals
            return self.supervisor_approved_by is not None and self.gm_approved_by is not None
        elif self.requester_employee_type == 'MANAGER':
            # Managers need only CEO approval
            return self.ceo_approved_by is not None
        return False
    
    @property
    def can_assign_vehicle(self):
        """Check if admin can assign vehicle (all approvals complete)."""
        return self.status == 'approved' and self.is_fully_approved
    
    @property
    def current_approval_stage(self):
        """Return the current stage in the approval workflow."""
        if self.status != 'pending':
            return self.status
        
        if self.requester_employee_type == 'GENERAL_EMPLOYEE':
            if not self.supervisor_approved_by:
                return 'awaiting_supervisor'
            elif not self.gm_approved_by:
                return 'awaiting_gm'
            else:
                return 'approved'
        elif self.requester_employee_type == 'MANAGER':
            if not self.ceo_approved_by:
                return 'awaiting_ceo'
            else:
                return 'approved'
        
        return 'pending'


class HandoverChecklist(models.Model):
    request = models.OneToOneField(CarRequest, on_delete=models.CASCADE, related_name='handover')
    
    # Return information
    return_mileage = models.PositiveIntegerField(null=True, blank=True)
    fuel_level = models.CharField(max_length=64, blank=True)
    condition_notes = models.TextField(blank=True)
    accessories_missing = models.TextField(blank=True)
    damages = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Detailed checklist items with YES/NO/COMMENTS
    alarm_system_functional = models.CharField(max_length=10, blank=True, null=True)
    alarm_system_comments = models.TextField(blank=True)
    
    lock_nuts_spanner = models.CharField(max_length=10, blank=True, null=True)
    lock_nuts_spanner_comments = models.TextField(blank=True)
    
    spare_wheel_hatchet = models.CharField(max_length=10, blank=True, null=True)
    spare_wheel_hatchet_comments = models.TextField(blank=True)
    
    seat_belts_functioning = models.CharField(max_length=10, blank=True, null=True)
    seat_belts_comments = models.TextField(blank=True)
    
    hand_brake_functioning = models.CharField(max_length=10, blank=True, null=True)
    hand_brake_comments = models.TextField(blank=True)
    
    view_mirrors_functioning = models.CharField(max_length=10, blank=True, null=True)
    view_mirrors_comments = models.TextField(blank=True)
    
    vehicle_insurance_disk = models.CharField(max_length=10, blank=True, null=True)
    vehicle_insurance_disk_comments = models.TextField(blank=True)
    
    aa_zimbabwe_card = models.CharField(max_length=10, blank=True, null=True)
    aa_zimbabwe_card_comments = models.TextField(blank=True)
    
    vehicle_licence_disk = models.CharField(max_length=10, blank=True, null=True)
    vehicle_licence_disk_comments = models.TextField(blank=True)
    
    brake_lights_functioning = models.CharField(max_length=10, blank=True, null=True)
    brake_lights_comments = models.TextField(blank=True)
    
    indicators_functioning = models.CharField(max_length=10, blank=True, null=True)
    indicators_comments = models.TextField(blank=True)
    
    park_lights_functioning = models.CharField(max_length=10, blank=True, null=True)
    park_lights_comments = models.TextField(blank=True)
    
    spare_wheel = models.CharField(max_length=10, blank=True, null=True)
    spare_wheel_comments = models.TextField(blank=True)
    
    jack = models.CharField(max_length=10, blank=True, null=True)
    jack_comments = models.TextField(blank=True)
    
    wheel_spanner = models.CharField(max_length=10, blank=True, null=True)
    wheel_spanner_comments = models.TextField(blank=True)
    
    tool_box = models.CharField(max_length=10, blank=True, null=True)
    tool_box_comments = models.TextField(blank=True)
    
    wheel_covers = models.CharField(max_length=10, blank=True, null=True)
    wheel_covers_comments = models.TextField(blank=True)
    
    seat_covers = models.CharField(max_length=10, blank=True, null=True)
    seat_covers_comments = models.TextField(blank=True)
    
    reflectors_installed = models.CharField(max_length=10, blank=True, null=True)
    reflectors_installed_comments = models.TextField(blank=True)
    
    car_radio = models.CharField(max_length=10, blank=True, null=True)
    car_radio_comments = models.TextField(blank=True)
    
    floor_mats = models.CharField(max_length=10, blank=True, null=True)
    floor_mats_comments = models.TextField(blank=True)
    
    # Fuel and mileage readings
    fuel_reading = models.CharField(max_length=20, blank=True)
    mileage_kms = models.PositiveIntegerField(null=True, blank=True)
    
    # Scratches and dents
    scratches_dents = models.TextField(blank=True)
    
    # Additional comments
    additional_comments = models.TextField(blank=True)
    
    # Attachments - support multiple file formats
    checklist_document = models.FileField(upload_to='handover_checklists/', null=True, blank=True, help_text='PDF, Image, or Scanned document')
    additional_photo1 = models.ImageField(upload_to='handover_photos/', null=True, blank=True)
    additional_photo2 = models.ImageField(upload_to='handover_photos/', null=True, blank=True)
    additional_photo3 = models.ImageField(upload_to='handover_photos/', null=True, blank=True)
    
    # Processing timestamps
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_handover')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Admin review
    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected - Issues Found'),
        ('needs_review', 'Needs Additional Review'),
    ]
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Handover for request {self.request.id}"


class ServiceRecord(models.Model):
    SERVICE_TYPE_CHOICES = [
        ('A Service', 'A Service'),
        ('B Service', 'B Service'),
        ('C Service', 'C Service'),
        ('Major Service', 'Major Service'),
        ('Oil Change', 'Oil Change'),
        ('Brake Service', 'Brake Service'),
        ('Tire Replacement', 'Tire Replacement'),
        ('General Repair', 'General Repair'),
        ('First Service', 'First Service'),
        ('Other', 'Other'),
    ]
    
    # Vehicle can be null for standalone service tracking
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='service_records', null=True, blank=True)
    
    # Standalone fields for vehicles not in the main system
    vehicle_reg_number = models.CharField(max_length=32, blank=True, help_text='Registration number for standalone tracking')
    vehicle_description = models.CharField(max_length=256, blank=True, help_text='Vehicle description for standalone tracking')
    driver_name = models.CharField(max_length=128, blank=True, help_text='Driver assigned to vehicle')
    current_mileage = models.PositiveIntegerField(null=True, blank=True, help_text='Current vehicle mileage')
    
    # Service tracking
    upload_month = models.CharField(max_length=20, blank=True, help_text='Month of upload (e.g., July 2025)')
    service_date = models.DateField()
    service_type = models.CharField(max_length=64, choices=SERVICE_TYPE_CHOICES)
    service_company = models.CharField(max_length=128)
    mileage_at_service = models.PositiveIntegerField()
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True, help_text='Additional details about the service')
    next_service_due = models.PositiveIntegerField(null=True, blank=True, help_text='Mileage when next service is due')
    invoice_number = models.CharField(max_length=64, blank=True)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='services_recorded')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-service_date', '-created_at']
    
    def __str__(self):
        if self.vehicle:
            return f"{self.vehicle.reg_number} - {self.service_type} on {self.service_date}"
        else:
            return f"{self.vehicle_reg_number} - {self.service_type} on {self.service_date}"


# ============================================
# AMBULANCE MANAGER MODELS
# ============================================

class Ambulance(models.Model):
    """Model for ambulance fleet management."""
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('on_call', 'On Call'),
        ('maintenance', 'Under Maintenance'),
        ('out_of_service', 'Out of Service'),
    ]

    reg_number = models.CharField(max_length=32, unique=True)
    model = models.CharField(max_length=128, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)
    chassis_number = models.CharField(max_length=64, blank=True)
    engine_number = models.CharField(max_length=64, blank=True)
    image = models.ImageField(upload_to='ambulances/', null=True, blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='available', db_index=True)
    service_interval_mileage = models.PositiveIntegerField(null=True, blank=True)
    current_mileage = models.PositiveIntegerField(default=0)
    base_location = models.CharField(max_length=128, blank=True, help_text='Primary station/location')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.reg_number} — {self.model}"
    
    @property
    def km_to_service(self):
        """Calculate kilometers remaining until next service."""
        if self.service_interval_mileage and self.current_mileage is not None:
            km_remaining = self.service_interval_mileage - self.current_mileage
            return km_remaining if km_remaining > 0 else 0
        return None
    
    @property
    def is_service_due(self):
        """Check if service is due or overdue."""
        if self.km_to_service is not None:
            return self.km_to_service <= 1000  # Alert when 1000km or less to service
        return False


class AmbulanceEquipment(models.Model):
    """Track equipment inventory for each ambulance."""
    EQUIPMENT_STATUS_CHOICES = [
        ('present', 'Present and Functional'),
        ('missing', 'Missing'),
        ('damaged', 'Damaged/Non-functional'),
        ('expired', 'Expired'),
    ]

    ambulance = models.ForeignKey(Ambulance, on_delete=models.CASCADE, related_name='equipment')
    equipment_name = models.CharField(max_length=128, help_text='e.g., Oxygen Cylinder, Stretcher, Defibrillator')
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=32, choices=EQUIPMENT_STATUS_CHOICES, default='present')
    expiry_date = models.DateField(null=True, blank=True, help_text='For items like oxygen, medications')
    notes = models.TextField(blank=True)
    last_checked = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['ambulance', 'equipment_name']

    def __str__(self):
        return f"{self.ambulance.reg_number} - {self.equipment_name}"


class AmbulanceServiceRecord(models.Model):
    """Service and maintenance records for ambulances."""
    SERVICE_TYPE_CHOICES = [
        ('routine_service', 'Routine Service'),
        ('major_service', 'Major Service'),
        ('oil_change', 'Oil Change'),
        ('brake_service', 'Brake Service'),
        ('tire_replacement', 'Tire Replacement'),
        ('equipment_calibration', 'Equipment Calibration'),
        ('body_repair', 'Body Repair'),
        ('general_repair', 'General Repair'),
        ('other', 'Other'),
    ]
    
    ambulance = models.ForeignKey(Ambulance, on_delete=models.CASCADE, related_name='service_records')
    service_date = models.DateField()
    service_type = models.CharField(max_length=64, choices=SERVICE_TYPE_CHOICES)
    service_company = models.CharField(max_length=128)
    mileage_at_service = models.PositiveIntegerField()
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True, help_text='Details about the service performed')
    next_service_due = models.PositiveIntegerField(null=True, blank=True, help_text='Mileage when next service is due')
    invoice_number = models.CharField(max_length=64, blank=True)
    receipt = models.FileField(upload_to='ambulance_receipts/', null=True, blank=True, help_text='Service receipt/invoice')
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='ambulance_services_recorded')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-service_date', '-created_at']
    
    def __str__(self):
        return f"{self.ambulance.reg_number} - {self.service_type} on {self.service_date}"


class AmbulanceUsageRecord(models.Model):
    """Track ambulance usage, mileage, and fuel consumption."""
    ambulance = models.ForeignKey(Ambulance, on_delete=models.CASCADE, related_name='usage_records')
    driver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='ambulance_trips')
    driver_name = models.CharField(max_length=255, blank=True, help_text='Name of the driver assigned')
    driver_phone = models.CharField(max_length=20, blank=True, help_text='Driver contact number')
    date = models.DateField(default=timezone.now)
    purpose = models.CharField(max_length=255, help_text='e.g., Emergency Response, Patient Transfer')
    start_location = models.CharField(max_length=255, blank=True)
    end_location = models.CharField(max_length=255, blank=True)
    start_mileage = models.PositiveIntegerField()
    end_mileage = models.PositiveIntegerField(null=True, blank=True)
    fuel_added = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text='Liters of fuel added')
    fuel_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fuel_receipt = models.FileField(upload_to='ambulance_fuel_receipts/', null=True, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.ambulance.reg_number} - {self.date} ({self.purpose})"
    
    @property
    def distance_covered(self):
        """Calculate distance covered in this trip."""
        return self.end_mileage - self.start_mileage if self.end_mileage and self.start_mileage else 0


class AmbulanceRequest(models.Model):
    """Ambulance usage request and approval workflow (if needed)."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]

    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ambulance_requests')
    purpose = models.TextField()
    requested_date = models.DateField()
    requested_time = models.TimeField(null=True, blank=True)
    location = models.CharField(max_length=255)
    patient_name = models.CharField(max_length=128, blank=True, help_text='Patient name (if applicable)')
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='pending', db_index=True)
    assigned_ambulance = models.ForeignKey(Ambulance, null=True, blank=True, on_delete=models.SET_NULL)
    assigned_driver = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='ambulance_assignments')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='ambulance_approvals')
    approval_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['requested_date']),
        ]

    def __str__(self):
        return f"Ambulance Request {self.id} by {self.requester.username} ({self.status})"
