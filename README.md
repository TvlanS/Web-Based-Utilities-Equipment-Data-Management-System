# Utilities PM V2

<img src="https://github.com/TvlanS/Web-Based-Utilities-Equipment-Data-Management-System/blob/8e339f0f303b907eabd4788dbea6db43aeb55f02/Media/Forms.png?raw=true" width="400"> | <img src="https://github.com/TvlanS/Web-Based-Utilities-Equipment-Data-Management-System/blob/8e339f0f303b907eabd4788dbea6db43aeb55f02/Media/Plot_2.png?raw=true" width="400">

## Industrial Equipment Monitoring, Made Clear

Utilities PM V2 is an improved and focused preventive-maintenance platform for monitoring compressor equipment, identifying abnormal conditions, and turning raw operating data into actionable insights.

It is a cleaner and more detailed version of its predecessor, designed to help maintenance and operations teams address three key challenges:

* Slow data collection
* Difficulty identifying abnormal machine conditions
* Labor-intensive visualization of equipment trends

### Table of Contents

* [1. Overview](#1-overview)

  * [1.1 Key Capabilities](#11-key-capabilities)
  * [1.2 Application Pages](#12-application-pages)
* [2. Anomaly Detection](#2-anomaly-detection)
* [3. Control Limits](#3-control-limits)
* [4. Technology Stack](#4-technology-stack)
* [5. Installation and Setup](#5-installation-and-setup)

  * [5.1 Prerequisites](#51-prerequisites)
  * [5.2 Clone the Repository](#52-clone-the-repository)
  * [5.3 Create a Virtual Environment](#53-create-a-virtual-environment)
  * [5.4 Install Dependencies](#54-install-dependencies)
  * [5.5 Supabase Database Configuration](#55-supabase-database-configuration)
  * [5.6 Run Database Migrations](#56-run-database-migrations)
  * [5.7 Start the Application](#57-start-the-application)
  * [5.8 Sample Dataset](#58-sample-dataset)
* [6. Application Routes](#6-application-routes)

---

# 1. Overview

Utilities PM V2 provides a centralized interface for recording, monitoring, filtering, analyzing, and exporting compressor operating data.

The platform combines structured data entry, equipment monitoring, interactive performance analysis, and automated anomaly detection into a single Django-based application.

## 1.1 Key Capabilities

The system provides the following capabilities:

* Record compressor operating measurements
* Monitor multiple compressor units
* Filter data by unit and date
* Sort readings by highest, lowest, or newest
* Visualize individual readings and daily averages
* Detect values outside upper and lower control limits
* Display clear alerts for affected parameters
* Temporarily adjust UCL and LCL values
* Export filtered records to Excel
* Maintain a responsive and consistent dashboard experience

## 1.2 Application Pages

### 1.2.1 Home

**Route:** `/home/`

The Home page serves as the operational starting point for the platform.

![Home Page](https://github.com/TvlanS/Web-Based-Utilities-Equipment-Data-Management-System/blob/be0b8570c6e252b1470725302a88f778e5b87ae2/Media/Screenshot%202026-08-30%20131104.png)

It provides quick access to:

* Enter compressor data
* Review equipment records
* Open performance analysis

### 1.2.2 Compressor Data Entry

**Route:** `/forms/compressor/`

The Compressor Data Entry page provides a structured form for recording compressor readings.

![Compressor Form](https://github.com/TvlanS/Web-Based-Utilities-Equipment-Data-Management-System/blob/be0b8570c6e252b1470725302a88f778e5b87ae2/Media/Forms.png)

The form captures:

* Unit and operating mode
* Chilled-water values
* Evaporator measurements
* Refrigerant pressure and temperature
* Flow status
* Expansion-valve measurements

Required fields are validated, while optional measurement fields can remain blank.

### 1.2.3 Equipment Monitoring

**Route:** `/filter/`

The Equipment Monitoring page provides a searchable table for reviewing historical equipment operating data.

![Monitoring Table](docs/images/filter-page.png)

Features include:

* Unit filtering
* Start and end date filtering
* Today shortcut
* Sortable columns
* Sticky identification columns
* Operating-status indicators
* Edit and delete actions
* Excel export

Column sorting follows a simple three-step interaction:

1. Highest or newest first
2. Lowest or oldest first
3. Return to newest-date default

### 1.2.4 Performance Analysis

**Route:** `/plot/`

The Performance Analysis page provides an interactive Plotly-based interface for understanding equipment behavior and identifying abnormal operating conditions.

![Performance Plot](https://github.com/TvlanS/Web-Based-Utilities-Equipment-Data-Management-System/blob/be0b8570c6e252b1470725302a88f778e5b87ae2/Media/Plot_2.png)

It displays:

* Chronologically connected individual readings
* Daily averages
* UCL and LCL control-limit lines
* Anomaly markers
* Latest-reading status
* Mean, minimum, maximum, and standard deviation
* Anomaly count and percentage
* Temporary control-limit adjustments

Every chart, statistic, alert, and anomaly marker is generated from the same filtered dataset to maintain consistency across the analysis.

---

# 2. Anomaly Detection

Each compressor reading is classified into one of three conditions:

![Performance Plot](https://github.com/TvlanS/Web-Based-Utilities-Equipment-Data-Management-System/blob/be0b8570c6e252b1470725302a88f778e5b87ae2/Media/Plot_1.png)

```text
Above UCL
Below LCL
Within Limits
```

The system uses strict comparisons:

```text
value > UCL  → Above UCL
value < LCL  → Below LCL
Otherwise    → Within Limits
```

Anomalies are distinguished using both color and marker shape to make abnormal conditions easier to identify.

## 2.1 Alert Panel

The alert panel provides a concise summary of detected anomalies.

For each affected reading, it:

* Identifies the affected unit
* Lists every parameter that exited its control limits
* Shows the measured value
* Indicates whether the value is above or below its limit

Alert ordering prioritizes:

1. Below LCL issues
2. Above UCL issues

This allows potentially low-value conditions to appear first in the alert summary.

---

# 3. Control Limits

Each monitored variable has its own configured default Upper Control Limit (UCL) and Lower Control Limit (LCL).

Users can temporarily apply new control limits while performing an analysis.

Temporary control-limit changes immediately update:

* Chart control-limit lines
* Anomaly classifications
* Statistics
* Latest-reading status
* Alerts

## 3.1 Temporary Limit Behavior

Temporary control-limit changes are **not saved to the database**.

They only apply to the current analysis session.

Clearing the temporary control limits restores the configured default UCL and LCL values.

---

# 4. Technology Stack

Utilities PM V2 uses a conventional Django architecture, with business logic handled primarily in Python and interactive visualization handled through Plotly.

| Technology  | Purpose                        |
| ----------- | ------------------------------ |
| Python      | Application and business logic |
| Django      | Web application framework      |
| PostgreSQL  | Database                       |
| Supabase    | PostgreSQL database hosting    |
| Bootstrap 5 | Responsive user interface      |
| Plotly      | Interactive data visualization |
| JavaScript  | Client-side interactions       |
| OpenPyXL    | Excel export                   |

---

# 5. Installation and Setup

## 5.1 Prerequisites

Before running Utilities PM V2, ensure the following are installed:

* Python
* Git
* A Supabase account and PostgreSQL database
* `pip` for Python package management

## 5.2 Clone the Repository

Clone the project repository and navigate into the project directory:

```bash
git clone <repository-url>

cd Web-Based-Utilities-Equipment-Data-Management-System
```

## 5.3 Create a Virtual Environment

Create and activate a Python virtual environment:

```bash
python -m venv venv
```

On Windows:

```bash
venv\Scripts\activate
```

## 5.4 Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Environment-variable support is provided using `python-dotenv`. If it is not already included in `requirements.txt`, install it separately:

```bash
pip install python-dotenv
```

---

## 5.5 Supabase Database Configuration

Utilities PM V2 uses **Supabase PostgreSQL** as its database.

### 5.5.1 Create the Environment File

Create a `.env` file in the project root:

```env
SUPABASE_DB_NAME=
SUPABASE_DB_USER=
SUPABASE_DB_PASSWORD=
SUPABASE_DB_HOST=
SUPABASE_DB_PORT=

DJANGO_KEY=
```

### 5.5.2 Obtain Supabase Database Credentials

The required database credentials can be found in:

```text
Supabase Dashboard
→ Project Settings
→ Database
→ Connection Information
```

Example configuration:

```env
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres.xxxxxxxxxxxxx
SUPABASE_DB_PASSWORD=your-database-password
SUPABASE_DB_HOST=aws-0-ap-southeast-1.pooler.supabase.com
SUPABASE_DB_PORT=6543

DJANGO_KEY=your-secure-django-secret-key
```

Replace the example values with the credentials for your Supabase project.

### 5.5.3 Protect Environment Variables

The `.env` file contains sensitive database credentials and must **never be committed to Git**.

Add the following entry to `.gitignore`:

```gitignore
.env
```

Do not share or commit your database password or Django secret key.

---

## 5.6 Run Database Migrations

Once the environment variables and database configuration have been set up, run the Django migrations:

```bash
python manage.py migrate
```

This creates and updates the required database tables.

---

## 5.7 Start the Application

Start the Django development server:

```bash
python manage.py runserver
```

Open the application at:

```text
http://127.0.0.1:8000/
```

The root URL redirects to:

```text
/home/
```

---

## 5.8 Sample Dataset

A sample dataset is provided in the repository:

```text
PM_Database.csv
```

For testing purposes, upload the dataset into the Supabase database under:

```text
PM_system_compressor
```

> **Note:** The dataset values provided with this project do not represent real equipment readings. They are provided solely for testing and demonstration purposes.

---

# 6. Application Routes

| Purpose               | Route                |
| --------------------- | -------------------- |
| Home                  | `/home/`             |
| Enter compressor data | `/forms/compressor/` |
| Filter equipment data | `/filter/`           |
| Analyze performance   | `/plot/`             |
| Export Excel data     | `/export/`           |
