from django import forms
from django.contrib.auth.models import User
from .models import Vehicle, CarRequest, HandoverChecklist, Profile, SUBSIDIARY_CHOICES, ServiceRecord


class VehicleForm(forms.ModelForm):
    """Form for adding/editing vehicles."""
    BRANCHES_BY_SUB = {
        'nectacare': [
            'Harare branch', 'Bulawayo branch', 'Mutare branch', 'SMH', 'Ngezi'
        ],
        'cellmed': [
            'Harare head office', 'Harare Town office', 'Bulawayo branch', 'Zvishavane branch', 'Mutare branch', 'Ngezi branch'
        ],
        'cell_insurance': [
            'Harare branch', 'Bulawayo branch', 'Mutare branch', 'SMH', 'Ngezi'
        ]
    }
    class Meta:
        model = Vehicle
        fields = [
            'reg_number', 'vehicle_type', 'model', 'fuel_type',
            'engine_capacity', 'image', 'accessories',
            'service_interval_mileage', 'current_mileage',
            'subsidiary', 'branch'
        ]
        widgets = {
            'reg_number': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g. ABC 123 GP'
            }),
            'vehicle_type': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g. Sedan, SUV, Hatchback'
            }),
            'model': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g. Toyota Corolla, BMW X3'
            }),
            'fuel_type': forms.Select(choices=[
                ('petrol', 'Petrol'),
                ('diesel', 'Diesel'),
                ('hybrid', 'Hybrid')
            ], attrs={'class': 'form-control'}),
            'engine_capacity': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g. 1.6L, 2.0L'
            }),
            'accessories': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'List vehicle accessories (GPS, Radio, etc.)'
            }),
            'service_interval_mileage': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g. 15000'
            }),
            'current_mileage': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Current odometer reading'
            }),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'subsidiary': forms.Select(attrs={'class': 'form-control', 'id': 'id_subsidiary'}),
            'branch': forms.Select(attrs={'class': 'form-control', 'id': 'id_branch'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate branch choices with the union of all branches; JS will filter based on subsidiary selection
        all_branches = []
        for k, v in self.BRANCHES_BY_SUB.items():
            for b in v:
                if b not in all_branches:
                    all_branches.append(b)

        branch_choices = [('', 'Select Branch')] + [(b, b) for b in all_branches]
        self.fields['branch'].widget = forms.Select(attrs={'class': 'form-control', 'id': 'id_branch'})
        self.fields['branch'].choices = branch_choices


class DriverAssignmentForm(forms.Form):
    """Form for assigning drivers to vehicles."""
    driver = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__role='driver'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select Driver"
    )
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.filter(status='available'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select Vehicle"
    )
    destination = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter destination'}),
        label="Destination"
    )
    reason = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter reason for assignment', 'rows': 4}),
        label="Reason for Assignment"
    )
    # Note: Admin assigns drivers via this screen; no dedicated toggle needed.

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Update querysets to get fresh data
        # 'driver' field shows only users with driver role
        from django.db.models import Q
        # Include any user with profile.role == 'driver' OR marked as a dedicated driver
        self.fields['driver'].queryset = User.objects.filter(
            Q(profile__role='driver') | Q(profile__is_dedicated_driver=True)
        ).select_related('profile')
        # Show friendly labels in the dropdown: 'Driver — Full Name' (fall back to username without underscores)
        def _label_from_instance(user_obj):
            full = (user_obj.get_full_name() or '').strip()
            if full:
                name = full
            else:
                # replace underscores and title-case username fallback
                name = user_obj.username.replace('_', ' ').title()
            return name

        self.fields['driver'].label_from_instance = _label_from_instance
        self.fields['vehicle'].queryset = Vehicle.objects.filter(
            status='available'
        )


class CarRequestApprovalForm(forms.ModelForm):
    """Form for approving/rejecting car requests."""
    class Meta:
        model = CarRequest
        fields = ['status', 'assigned_vehicle']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'assigned_vehicle': forms.Select(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_vehicle'].queryset = Vehicle.objects.filter(
            status='available'
        )
        self.fields['assigned_vehicle'].empty_label = "Select Vehicle"


class MileageUpdateForm(forms.Form):
    """Form for updating vehicle mileage."""
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select Vehicle"
    )
    new_mileage = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new mileage reading'
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Additional notes (optional)'
        })
    )


class HandoverChecklistReviewForm(forms.ModelForm):
    """Form for reviewing handover checklists."""
    APPROVAL_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected - Issues Found'),
        ('pending', 'Needs Additional Review')
    ]
    
    approval_status = forms.ChoiceField(
        choices=APPROVAL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    admin_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Admin review notes and feedback'
        })
    )

    class Meta:
        model = HandoverChecklist
        fields = ['reviewed_by']
        widgets = {
            'reviewed_by': forms.HiddenInput()
        }


class HandoverCompletionForm(forms.ModelForm):
    """Form for completing vehicle handover when driver returns."""
    # Allow admin to record return date/time manually in case vehicle is returned off-hours
    return_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Return Date'
    )
    return_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        label='Return Time'
    )
    class Meta:
        model = HandoverChecklist
        fields = [
            'return_mileage', 'fuel_level', 'condition_notes', 
            'accessories_missing', 'damages', 'notes',
            # Detailed checklist items
            'alarm_system_functional', 'alarm_system_comments',
            'lock_nuts_spanner', 'lock_nuts_spanner_comments',
            'spare_wheel_hatchet', 'spare_wheel_hatchet_comments',
            'seat_belts_functioning', 'seat_belts_comments',
            'hand_brake_functioning', 'hand_brake_comments',
            'view_mirrors_functioning', 'view_mirrors_comments',
            'vehicle_insurance_disk', 'vehicle_insurance_disk_comments',
            'aa_zimbabwe_card', 'aa_zimbabwe_card_comments',
            'vehicle_licence_disk', 'vehicle_licence_disk_comments',
            'brake_lights_functioning', 'brake_lights_comments',
            'indicators_functioning', 'indicators_comments',
            'park_lights_functioning', 'park_lights_comments',
            'spare_wheel', 'spare_wheel_comments',
            'jack', 'jack_comments',
            'wheel_spanner', 'wheel_spanner_comments',
            'tool_box', 'tool_box_comments',
            'wheel_covers', 'wheel_covers_comments',
            'seat_covers', 'seat_covers_comments',
            'reflectors_installed', 'reflectors_installed_comments',
            'car_radio', 'car_radio_comments',
            'floor_mats', 'floor_mats_comments',
            'fuel_reading', 'mileage_kms',
            'scratches_dents', 'additional_comments',
            'checklist_document', 'additional_photo1', 
            'additional_photo2', 'additional_photo3'
        ]
        widgets = {
            'return_mileage': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter odometer reading at return'
            }),
            'fuel_level': forms.Select(
                choices=[
                    ('', 'Select fuel level'),
                    ('full', 'Full Tank'),
                    ('3/4', '3/4 Tank'),
                    ('1/2', 'Half Tank'),
                    ('1/4', 'Quarter Tank'),
                    ('empty', 'Nearly Empty'),
                ],
                attrs={'class': 'form-control'}
            ),
            'condition_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Overall vehicle condition (cleanliness, general state, etc.)'
            }),
            'accessories_missing': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'List any missing accessories (leave blank if none)'
            }),
            'damages': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe any damages or issues (leave blank if none)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional notes or observations'
            }),
            # Detailed checklist items - YES/NO fields
            'alarm_system_functional': forms.Select(
                choices=[('', '---'), ('YES', 'YES'), ('NO', 'NO')],
                attrs={'class': 'form-control'}
            ),
            'alarm_system_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'lock_nuts_spanner': forms.Select(
                choices=[('', '---'), ('YES', 'YES'), ('NO', 'NO')],
                attrs={'class': 'form-control'}
            ),
            'lock_nuts_spanner_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'spare_wheel_hatchet': forms.Select(
                choices=[('', '---'), ('YES', 'YES'), ('NO', 'NO')],
                attrs={'class': 'form-control'}
            ),
            'spare_wheel_hatchet_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'seat_belts_functioning': forms.Select(
                choices=[('', '---'), ('YES', 'YES'), ('NO', 'NO')],
                attrs={'class': 'form-control'}
            ),
            'seat_belts_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'hand_brake_functioning': forms.Select(
                choices=[('', '---'), ('YES', 'YES'), ('NO', 'NO')],
                attrs={'class': 'form-control'}
            ),
            'hand_brake_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'view_mirrors_functioning': forms.Select(
                choices=[('', '---'), ('YES', 'YES'), ('NO', 'NO')],
                attrs={'class': 'form-control'}
            ),
            'view_mirrors_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'vehicle_insurance_disk': forms.Select(
                choices=[('', '---'), ('YES', 'YES'), ('NO', 'NO')],
                attrs={'class': 'form-control'}
            ),
            'vehicle_insurance_disk_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'aa_zimbabwe_card': forms.Select(
                choices=[('', '---'), ('YES', 'YES'), ('NO', 'NO')],
                attrs={'class': 'form-control'}
            ),
            'aa_zimbabwe_card_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'vehicle_licence_disk': forms.Select(
                choices=[('', '---'), ('YES', 'YES'), ('NO', 'NO')],
                attrs={'class': 'form-control'}
            ),
            'vehicle_licence_disk_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'brake_lights_functioning': forms.Select(
                choices=[('', '---'), ('YES', 'YES'), ('NO', 'NO')],
                attrs={'class': 'form-control'}
            ),
            'brake_lights_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'indicators_functioning': forms.Select(
                choices=[('', '---'), ('YES', 'YES'), ('NO', 'NO')],
                attrs={'class': 'form-control'}
            ),
            'indicators_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'park_lights_functioning': forms.Select(
                choices=[('', '---'), ('YES', 'YES'), ('NO', 'NO')],
                attrs={'class': 'form-control'}
            ),
            'park_lights_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'spare_wheel': forms.Select(
                choices=[('', '---'), ('YES', 'YES'), ('NO', 'NO')],
                attrs={'class': 'form-control'}
            ),
            'spare_wheel_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'jack': forms.Select(
                choices=[('', '---'), ('YES', 'YES'), ('NO', 'NO')],
                attrs={'class': 'form-control'}
            ),
            'jack_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'wheel_spanner': forms.Select(
                choices=[('', '---'), ('YES', 'YES'), ('NO', 'NO')],
                attrs={'class': 'form-control'}
            ),
            'wheel_spanner_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'tool_box': forms.Select(
                choices=[('', '---'), ('YES', 'YES'), ('NO', 'NO')],
                attrs={'class': 'form-control'}
            ),
            'tool_box_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'wheel_covers': forms.Select(
                choices=[('', '---'), ('YES', 'YES'), ('NO', 'NO')],
                attrs={'class': 'form-control'}
            ),
            'wheel_covers_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'seat_covers': forms.Select(
                choices=[('', '---'), ('YES', 'YES'), ('NO', 'NO')],
                attrs={'class': 'form-control'}
            ),
            'seat_covers_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'reflectors_installed': forms.Select(
                choices=[('', '---'), ('YES', 'YES'), ('NO', 'NO')],
                attrs={'class': 'form-control'}
            ),
            'reflectors_installed_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'car_radio': forms.Select(
                choices=[('', '---'), ('YES', 'YES'), ('NO', 'NO')],
                attrs={'class': 'form-control'}
            ),
            'car_radio_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'floor_mats': forms.Select(
                choices=[('', '---'), ('YES', 'YES'), ('NO', 'NO')],
                attrs={'class': 'form-control'}
            ),
            'floor_mats_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'fuel_reading': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 1/2 tank'}),
            'mileage_kms': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Mileage in KMs'}),
            'scratches_dents': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe any scratches or dents'}),
            'additional_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any additional comments'}),
            'checklist_document': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'additional_photo1': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'additional_photo2': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'additional_photo3': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
        labels = {
            'return_mileage': 'Return Mileage',
            'fuel_level': 'Fuel Level at Return',
            'condition_notes': 'Vehicle Condition',
            'accessories_missing': 'Missing Accessories',
            'damages': 'Damages/Issues',
            'notes': 'Additional Notes',
            # Detailed checklist labels
            'alarm_system_functional': 'Alarm System Functional',
            'alarm_system_comments': 'Comments',
            'lock_nuts_spanner': 'Lock Nuts Spanner',
            'lock_nuts_spanner_comments': 'Comments',
            'spare_wheel_hatchet': 'Spare Wheel Hatchet',
            'spare_wheel_hatchet_comments': 'Comments',
            'seat_belts_functioning': 'Seat Belts Functioning',
            'seat_belts_comments': 'Comments',
            'hand_brake_functioning': 'Hand Brake Functioning',
            'hand_brake_comments': 'Comments',
            'view_mirrors_functioning': 'View Mirrors Functioning',
            'view_mirrors_comments': 'Comments',
            'vehicle_insurance_disk': 'Vehicle Insurance Disk',
            'vehicle_insurance_disk_comments': 'Comments',
            'aa_zimbabwe_card': 'AA Zimbabwe Card',
            'aa_zimbabwe_card_comments': 'Comments',
            'vehicle_licence_disk': 'Vehicle Licence Disk',
            'vehicle_licence_disk_comments': 'Comments',
            'brake_lights_functioning': 'Brake Lights Functioning',
            'brake_lights_comments': 'Comments',
            'indicators_functioning': 'Indicators Functioning',
            'indicators_comments': 'Comments',
            'park_lights_functioning': 'Park Lights Functioning',
            'park_lights_comments': 'Comments',
            'spare_wheel': 'Spare Wheel',
            'spare_wheel_comments': 'Comments',
            'jack': 'Jack',
            'jack_comments': 'Comments',
            'wheel_spanner': 'Wheel Spanner',
            'wheel_spanner_comments': 'Comments',
            'tool_box': 'Tool Box',
            'tool_box_comments': 'Comments',
            'wheel_covers': 'Wheel Covers',
            'wheel_covers_comments': 'Comments',
            'seat_covers': 'Seat Covers',
            'seat_covers_comments': 'Comments',
            'reflectors_installed': 'Reflectors Installed',
            'reflectors_installed_comments': 'Comments',
            'car_radio': 'Car Radio',
            'car_radio_comments': 'Comments',
            'floor_mats': 'Floor Mats',
            'floor_mats_comments': 'Comments',
            'fuel_reading': 'Fuel Reading',
            'mileage_kms': 'Mileage (KMs)',
            'scratches_dents': 'Scratches/Dents',
            'additional_comments': 'Additional Comments',
            'checklist_document': 'Handover Checklist Document (PDF/Image)',
            'additional_photo1': 'Vehicle Photo 1 (Optional)',
            'additional_photo2': 'Vehicle Photo 2 (Optional)',
            'additional_photo3': 'Vehicle Photo 3 (Optional)'
        }


class UserProfileForm(forms.ModelForm):
    """Form for editing user profiles."""
    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField()

    class Meta:
        model = Profile
        fields = ['role', 'subsidiary', 'employee_type']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
            'subsidiary': forms.Select(attrs={'class': 'form-control'}),
            'employee_type': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['username'].initial = self.user.username
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email

        # Add form-control class to all fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


class BulkVehicleStatusForm(forms.Form):
    """Form for bulk updating vehicle statuses."""
    vehicles = forms.ModelMultipleChoiceField(
        queryset=Vehicle.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True
    )
    new_status = forms.ChoiceField(
        choices=Vehicle.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Reason for status change'
        })
    )


class UserManagementForm(forms.ModelForm):
    """Form for adding/editing system users."""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First name'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'user@cellinsurance.com'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter secure password'
        }),
        help_text='Password must be at least 8 characters long'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Passwords do not match')
        
        if password and len(password) < 8:
            raise forms.ValidationError('Password must be at least 8 characters long')

        return cleaned_data


class UserProfileManagementForm(forms.ModelForm):
    """Form for managing user profiles and roles.

    The role field intentionally excludes the 'driver' role so MIS
    admins cannot assign the system role 'driver' from the user
    management screen. Drivers are managed separately via the
    dedicated drivers workflow (`is_dedicated_driver`).
    """
    # Build role choices from the model but exclude the 'driver' option
    ROLE_CHOICES = [r for r in Profile.USER_ROLES if r[0] != 'driver']
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = Profile
        fields = ['role', 'subsidiary', 'employee_type']
        widgets = {
            'subsidiary': forms.Select(attrs={'class': 'form-control'}),
            'employee_type': forms.Select(attrs={'class': 'form-control'}),
        }


class PermanentDriverForm(forms.Form):
    """Form for adding drivers (no login required)."""
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Driver first name'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Driver last name'
        })
    )
    license_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Driver license number'
        })
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contact number (optional)'
        })
    )
    subsidiary = forms.ChoiceField(
        choices=SUBSIDIARY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Additional notes about the driver'
        })
    )


class PasswordResetForm(forms.Form):
    """Form for resetting user passwords."""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username'
        })
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password'
        }),
        help_text='Password must be at least 8 characters long'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError('Passwords do not match')
        
        if new_password and len(new_password) < 8:
            raise forms.ValidationError('Password must be at least 8 characters long')

        return cleaned_data

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError('User with this username does not exist')
        return username

class ServiceRecordForm(forms.ModelForm):
    """Form for adding vehicle service records."""
    class Meta:
        model = ServiceRecord
        fields = [
            'vehicle', 'vehicle_reg_number', 'vehicle_description', 'driver_name',
            'current_mileage', 'service_date', 'service_type', 'service_company',
            'mileage_at_service', 'cost', 'description', 'next_service_due',
            'invoice_number'
        ]
        widgets = {
            'vehicle': forms.Select(attrs={
                'class': 'form-control',
                'onchange': 'toggleManualEntry(this)'
            }),
            'vehicle_reg_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., AAA-1234 (for non-pool vehicles)'
            }),
            'vehicle_description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Toyota Corolla 2020'
            }),
            'driver_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Driver name or "Pool"'
            }),
            'current_mileage': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Current vehicle mileage'
            }),
            'service_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'service_type': forms.Select(attrs={'class': 'form-control'}),
            'service_company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Nissan Zimbabwe, Toyota Zimbabwe'
            }),
            'mileage_at_service': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Odometer reading at service'
            }),
            'cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Service cost (optional)',
                'step': '0.01'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional service details, parts replaced, etc.'
            }),
            'next_service_due': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Mileage when next service is due'
            }),
            'invoice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Invoice/Receipt number (optional)'
            }),
        }
        labels = {
            'vehicle': 'Select Pool Car (or leave blank for non-pool vehicle)',
            'vehicle_reg_number': 'Registration Number (Manual Entry)',
            'vehicle_description': 'Vehicle Description (Manual Entry)',
            'driver_name': 'Driver/User',
            'current_mileage': 'Current Vehicle Mileage',
            'service_date': 'Service Date',
            'service_type': 'Type of Service',
            'service_company': 'Service Company',
            'mileage_at_service': 'Mileage at Service',
            'cost': 'Cost (USD)',
            'description': 'Service Description',
            'next_service_due': 'Next Service Due (Mileage)',
            'invoice_number': 'Invoice Number'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make vehicle field not required (allow manual entry for non-pool vehicles)
        self.fields['vehicle'].required = False
        self.fields['vehicle'].empty_label = "--- Select Pool Car (or enter manually below) ---"
    
    def clean(self):
        cleaned_data = super().clean()
        vehicle = cleaned_data.get('vehicle')
        vehicle_reg_number = cleaned_data.get('vehicle_reg_number')
        
        # Either vehicle OR vehicle_reg_number must be provided
        if not vehicle and not vehicle_reg_number:
            raise forms.ValidationError(
                "Please either select a pool car or enter the registration number manually."
            )
        
        # If vehicle is selected, populate the manual fields from vehicle data
        if vehicle:
            cleaned_data['vehicle_reg_number'] = vehicle.reg_number
            cleaned_data['vehicle_description'] = f"{vehicle.model} {vehicle.vehicle_type}"
            cleaned_data['current_mileage'] = vehicle.current_mileage
        
        return cleaned_data
