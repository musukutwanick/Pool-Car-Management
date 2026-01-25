# Copilot Instructions for Pool Car Management Project

## Project Overview
The Pool Car Management system is designed to streamline vehicle allocation, tracking, and reporting for fleet administrators. It consists of several dashboards and workflows for managing vehicles, drivers, assignments, and handovers.

### Key Components
1. **Templates**: HTML files located in `templates/admin/` define the structure and styling of dashboards.
   - Example: `manage_vehicles.html`, `statistics.html`
2. **Views**: Python files in `fleet/` handle backend logic and data processing.
   - Example: `views.py`
3. **Static Assets**: CSS and JavaScript files for styling and interactivity.
   - Example: `static/css/styles.css`
4. **Database Models**: Define the structure of data stored in the system.
   - Example: `models.py`

### Data Flow
- User interactions on the frontend (HTML templates) trigger requests handled by views.
- Views interact with models to fetch or update data.
- Responses are rendered back to templates for display.

## Developer Workflows
### Building and Testing
- **Run the application**: Use `python manage.py runserver`.
- **Run tests**: Use `python manage.py test`.
- **Debugging**: Add breakpoints in views or use Django's debug toolbar.

### Styling Updates
- CSS changes are primarily made in `static/css/styles.css`.
- Inline styles in templates should be avoided; migrate them to CSS files.

### Conventions
- Use `#fed41f` for primary yellow accents.
- Icons should have black text on light orange backgrounds.
- Follow Django's MVC pattern strictly.

## Integration Points
- **External Dependencies**: Ensure `requirements.txt` is up-to-date.
- **Cross-Component Communication**: Views interact with models and templates; ensure changes in one component are reflected in others.

## Examples
### Styling Example
To update button styles:
```html
<a href="{% url 'fleet:export_usage_report' %}?type=monthly" class="btn-download monthly" style="background-color: #fed41f; color: black;">
  Download Monthly Report
</a>
```

### View Example
To fetch vehicle data:
```python
def get_vehicle_data(request):
    vehicles = Vehicle.objects.all()
    return render(request, 'admin/manage_vehicles.html', {'vehicles': vehicles})
```

## Notes
- Avoid hardcoding values; use Django's template tags and context variables.
- Ensure all changes are tested before deployment.

Feel free to suggest updates or clarify sections as needed!