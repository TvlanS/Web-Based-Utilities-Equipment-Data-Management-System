### 1) Web-Based Utilities Equipment Data Management System - Old Project from 2024 (new coming soon)

A Django-based web application for managing preventive maintenance data for industrial compressor units. The system allows data entry, filtering, export, and visualization of compressor performance metrics.

**Media:**
![alt text](https://raw.githubusercontent.com/TvlanS/Web-Based-Utilities-Equipment-Data-Management-System/refs/heads/main/Media/1.png)
![alt text](https://github.com/TvlanS/Web-Based-Utilities-Equipment-Data-Management-System/blob/main/Media/2.1.png)
![alt text](https://github.com/TvlanS/Web-Based-Utilities-Equipment-Data-Management-System/blob/main/Media/5.png)
![alt text](https://raw.githubusercontent.com/TvlanS/Web-Based-Utilities-Equipment-Data-Management-System/refs/heads/main/Media/SQL_Database.png)
[`System Images`](https://github.com/TvlanS/Web-Based-Utilities-Equipment-Data-Management-System/tree/main/Media)


## Features

- **Data Entry Form**: Add new compressor readings with validation and unit selection
- **Data Listing & Filtering**: View all entries with filtering by date range, unit, and parameters
- **Export to Excel**: Export filtered data to Excel format
- **Interactive Plots**: Visualize trends using Plotly scatter plots with statistical analysis
- **Upper/Lower Control Limits**: Automatically calculate and display control limits on plots
- **Statistical Metrics**: Display min, max, average, standard deviation, and out-of-control counts
- **Responsive UI**: Bootstrap 5 based interface with crispy-forms for better form layout

## Prerequisites

- Python 3.9 or higher
- PostgreSQL database
- pip (Python package manager)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd PM_project
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   If `requirements.txt` doesn't exist, install packages manually:
   ```bash
   pip install django==5.0.4
   pip install django-crispy-forms==2.0
   pip install crispy-bootstrap5==0.7
   pip install django-filter==23.0
   pip install django-plotly-dash==2.1.0
   pip install plotly==5.18.0
   pip install openpyxl==3.1.2
   pip install numpy==1.24.0
   pip install scikit-learn==1.3.0
   pip install psycopg2-binary==2.9.9
   ```

## Database Setup

1. **Create PostgreSQL database**
   ```sql
   CREATE DATABASE PM_DB;
   ```

2. **Update database credentials** in `PM_project/settings.py`:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'PM_DB',
           'USER': 'postgres',  # Your PostgreSQL username
           'PASSWORD': 'jesse',  # Your PostgreSQL password
           'HOST': 'localhost',
       }
   }
   ```

3. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

5. **Load initial data (optional)**
   - Use the Django admin at `/admin` to create CompressorUnit entries (Trane-1, Trane-2, Trane-3)
   - Or import data from `PM_Database.csv` using your preferred method

## Running the Application

1. **Start the development server**
   ```bash
   python manage.py runserver
   ```

2. **Access the application**
   - Open browser and go to `http://127.0.0.1:8000/`
   - The homepage redirects to the data entry form

## Usage Guide

### Navigation
The application has three main sections accessible via the top navigation bar:
- **Forms**: Data entry page for adding new compressor readings
- **List**: Filterable table view of all compressor data with export functionality
- **Plot**: Interactive visualization of compressor metrics over time

### 1. Data Entry (Forms)
- Fill in compressor readings including:
  - Unit selection (Trane-1, Trane-2, Trane-3)
  - Date of reading
  - Mode (Run/Offline)
  - Evaporator parameters (temperatures, pressures, flow status)
  - Expansion valve positions
  - Current readings
- Submit the form to save data to the database

### 2. Data Listing & Filtering
- View all compressor data in a table
- Filter by:
  - Date range
  - Unit (Trane-1, Trane-2, Trane-3)
  - Evaporator entering water temperature
- Export filtered data to Excel using the "Export" button

### 3. Interactive Plots
- Select a unit (or "All" for all units)
- Choose date range
- Select variable to plot from dropdown (8 available metrics)
- View interactive Plotly chart with:
  - Trendline (LOWESS smoothing)
  - Upper and Lower Control Limits (UCL/LCL)
  - Color-coded by unit

- Statistical metrics displayed below chart:
  - Minimum, Maximum, Average, Standard Deviation
  - Count of out-of-control points
  - Percentage of in-control points

## Project Structure

```
PM_project/
├── PM_project/          # Django project settings
│   ├── settings.py      # Configuration and database settings
│   ├── urls.py          # Main URL routing
│   └── ...
├── PM_system/           # Main application
│   ├── models.py        # Database models (Compressor, CompressorUnit)
│   ├── views.py         # Business logic and views
│   ├── forms.py         # Data entry forms with crispy-forms
│   ├── filters.py       # Data filtering with django-filters
│   ├── urls.py          # App URL routing
│   ├── templates/       # HTML templates
│   │   ├── PM_system/
│   │   │   ├── base.html           # Base template with navigation
│   │   │   ├── compressor_form.html # Data entry form
│   │   │   ├── compressor_list.html # Data listing
│   │   │   ├── compressor_filter.html # Filter interface
│   │   │   └── PM_plot.html        # Plot visualization
│   └── migrations/      # Database migrations
├── manage.py            # Django management script
├── PM_Database.csv      # Sample compressor data (if available)
├── compressor_data.xlsx # Sample Excel data
└── Media/               # Static media files
```

## Key Dependencies

- **Django 5.0.4**: Web framework
- **django-crispy-forms**: Enhanced form rendering
- **django-filter**: Data filtering
- **django-plotly-dash**: Plotly integration
- **Plotly**: Interactive visualization
- **Openpyxl**: Excel export
- **NumPy & Scikit-learn**: Statistical calculations
- **Psycopg2**: PostgreSQL adapter

## Configuration Notes

- **SECRET_KEY**: Change the default secret key in `settings.py` for production
- **DEBUG**: Set `DEBUG = False` in production
- **ALLOWED_HOSTS**: Configure appropriate hosts for production deployment
- **Static files**: For production, collect static files using `python manage.py collectstatic`

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running
- Verify database credentials in `settings.py`
- Check if the `PM_DB` database exists

### Missing Dependencies
- Ensure all packages are installed in the virtual environment
- Check Python version compatibility

### Plot Not Displaying
- Ensure Plotly and django-plotly-dash are installed
- Check browser console for JavaScript errors

## License

This project is for educational/internal use. Modify as needed for your organization.


