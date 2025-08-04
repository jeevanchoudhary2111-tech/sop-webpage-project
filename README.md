#  User Management & SOP Tracking System

## Table of Contents

- [🚀 Features](#-features)
  - [🔐 Authentication & Security](#-authentication--security)
  - [👥 User Management](#-user-management)
  - [📋 SOP Tracking System](#-sop-tracking-system)
  - [📅 Shared Calendar](#-shared-calendar)
  - [📊 Advanced Reporting](#-advanced-reporting)
  - [⏰ Daily Reset & Automation](#-daily-reset--automation)
  - [🎨 Modern User Interface](#-modern-user-interface)
  - [🐳 Production Infrastructure](#-production-infrastructure)
- [🛠️ Tech Stack](#-tech-stack)
  - [Backend](#backend)
  - [Frontend](#frontend)
  - [Infrastructure](#infrastructure)
- [🚀 Quick Start](#-quick-start)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [🔑 Default Admin Account](#-default-admin-account)
- [📚 SOP System Usage](#-sop-system-usage)
  - [For Users](#for-users)
  - [For Admins](#for-admins)
- [🌐 Network Access & Production Deployment](#-network-access--production-deployment)
  - [Network Configuration](#network-configuration)
- [📊 API Documentation](#-api-documentation)
  - [Authentication Endpoints](#authentication-endpoints)
  - [User Endpoints](#user-endpoints)
  - [SOP Endpoints](#sop-endpoints)
  - [Shared Calendar Endpoints](#shared-calendar-endpoints)
  - [Admin Endpoints (Requires Admin Role)](#admin-endpoints-requires-admin-role)
  - [System Endpoints](#system-endpoints)
- [🏗️ Project Structure](#-project-structure)
- [🔒 Security Features](#-security-features)
  - [Authentication & Authorization](#authentication--authorization)
  - [Input Validation & Security](#input-validation--security)
  - [Infrastructure Security](#infrastructure-security)
- [📊 Daily Automation & Reporting](#-daily-automation--reporting)
  - [3 AM IST Daily Reset](#3-am-ist-daily-reset)
  - [Report Features](#report-features)
- [🚀 Production Deployment](#-production-deployment)
  - [Environment Configuration](#environment-configuration)
  - [Production Security Checklist](#production-security-checklist)
  - [Performance Optimization](#performance-optimization)
- [📊 Monitoring & Troubleshooting](#-monitoring--troubleshooting)
  - [Health Checks](#health-checks)
  - [Log Management](#log-management)
  - [Common Issues & Solutions](#common-issues--solutions)
  - [Database Management](#database-management)
- [🤝 Contributing](#-contributing)
  - [Development Guidelines](#development-guidelines)
- [📄 License](#-license)
- [🆘 Support](#-support)
- [🔄 Changelog](#-changelog)
  - [v3.0.0 (Current - Production Ready)](#v300-current---production-ready)
  - [v1.0.0 (Initial Release)](#v100-initial-release)

---

A comprehensive, production-ready user management and Standard Operating Procedures (SOP) tracking system built with FastAPI, MongoDB, and modern web technologies.

## 🚀 Features

### 🔐 **Authentication & Security**
- **JWT Authentication** - Secure token-based authentication with configurable expiration
- **Role-Based Access Control** - Admin and user roles with granular permissions
- **Password Security** - Bcrypt hashing with salt for maximum security
- **Session Management** - Secure token handling with automatic logout
- **CORS Protection** - Configurable cross-origin resource sharing

### 👥 **User Management**
- **Complete CRUD Operations** - Create, read, update, delete users
- **Admin Panel** - Comprehensive user management interface
- **Profile Management** - Users can update their own profiles
- **User Activity Tracking** - Monitor user actions and login history

### 📋 **SOP Tracking System**
- **Multiple SOP Types** - Support for various Standard Operating Procedures:
  - **GIFT SOP** - Financial trading system procedures
  - **GIFT Infrastructure** - Infrastructure management procedures
  - **MCX SOP** - Multi Commodity Exchange procedures
  - **MCX Position SOP** - Position monitoring and management procedures
  - **BSE Daily Files** - Bombay Stock Exchange file management
  - **US Position SOP** - US equity and derivatives markets position management
  - **Lease Line SOP** - Network connectivity and lease line management
- **Task Management** - Individual task tracking with completion status
- **Real-time Collaboration** - Multiple users can work on SOPs simultaneously
- **Task Locking** - Prevents conflicts by locking completed tasks
- **Progress Tracking** - Visual progress indicators and completion status

### 📅 **Shared Calendar**
- **Date Marking** - Users can mark specific dates with descriptions
- **Collaborative View** - See marked dates from all users
- **Shift Plan Integration** - View users grouped by their assigned shifts

### 📊 **Advanced Reporting**
- **SOP-Styled Reports** - Reports that match the visual appearance of actual SOP pages
- **Multiple Export Formats** - HTML (styled), HTML (standard), and CSV formats
- **User Attribution** - Track who completed each task and when
- **Comprehensive Analytics** - Activity summaries, completion rates, and user statistics
- **Daily Reports** - Automated daily report generation and archival
- **US Position Reports** - Dedicated reports for US Position data

### ⏰ **Daily Reset & Automation**
- **3 AM IST Reset** - Automatic daily reset at 3 AM Indian Standard Time
- **Data Archival** - Automatic archiving of daily activities to MongoDB
- **Report Generation** - Daily reports automatically generated and made available
- **Historical Preservation** - All data is preserved for audit and analysis
- **Admin Notifications** - Dashboard alerts when daily reports are available

### 🎨 **Modern User Interface**
- **Responsive Design** - Mobile-first approach with proper breakpoints
- **Real-time Updates** - Live clock, status indicators, and progress tracking
- **Professional Styling** - Clean, modern interface with Tailwind CSS
- **Interactive Elements** - Hover states, transitions, and micro-interactions
- **Accessibility** - WCAG compliant design with proper contrast and navigation

### 🐳 **Production Infrastructure**
- **Docker Support** - Complete containerization with Docker Compose
- **Nginx Integration** - Web server, reverse proxy, and load balancer
- **Health Monitoring** - Built-in health checks and monitoring endpoints
- **Network Flexibility** - Works with localhost and IP addresses
- **Scalable Architecture** - Designed for production deployment

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework with automatic API documentation
- **MongoDB** - NoSQL database with proper connection pooling and indexing
- **JWT** - JSON Web Tokens for secure authentication
- **Pydantic v2** - Data validation and serialization with type safety
- **Passlib** - Secure password hashing with bcrypt
- **Uvicorn** - High-performance ASGI server
- **Schedule** - Task scheduling for daily automation

### Frontend
- **Vanilla JavaScript** - No framework dependencies, lightweight and fast
- **Tailwind CSS** - Utility-first CSS framework for rapid UI development
- **Responsive Design** - Mobile-first approach with proper breakpoints
- **Modern ES6+** - Clean, maintainable JavaScript code

### Infrastructure
- **Docker & Docker Compose** - Containerization for easy deployment
- **Nginx** - Web server, reverse proxy, and load balancer
- **MongoDB** - Database with authentication and health checks
- **Automated Scheduling** - Background task processing

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Git for version control
- At least 4GB RAM available for production deployment

### Installation

1.  **Clone the repository**
    ```bash
    git clone <repository-url>
    cd user-management-system
    ```

2.  **Environment Setup**
    ```bash
    cp .env.example .env
    # Edit .env with your production configuration
    ```

3.  **Start the application**
    ```bash
    docker-compose up -d
    ```

4.  **Access the application**
    -   **Frontend**: `http://localhost:8080` or `http://YOUR_IP:8080`
    -   **Backend API**: `http://localhost:8000` or `http://YOUR_IP:8000`
    -   **API Documentation**: `http://localhost:8000/docs`
    -   **Alternative API Docs**: `http://localhost:8000/redoc`

### 🔑 Default Admin Account
-   **Username**: `sysadmin`
-   **Password**: `admin123`

⚠️ **CRITICAL**: Change the default admin password immediately in production!

## 📚 SOP System Usage

### For Users
1.  **Login** to your account
2.  **Select SOP** from the dashboard (GIFT, MCX, BSE, US Position, Lease Line, etc.)
3.  **Check tasks** as you complete them (tasks show yellow background)
4.  **Click Save** button to lock completed tasks (tasks turn green)
5.  **View progress** - locked tasks cannot be modified
6.  **Mark Dates** on the shared calendar for important events.

### For Admins
1.  **Access Admin Panel** from the dashboard
2.  **Monitor Activities** - View all user activities with filters
3.  **Generate Reports** - Download SOP-styled reports with completion details
4.  **Daily Reports** - Access automated daily reports (available after 3 AM IST)
5.  **User Management** - Create, update, and manage user accounts
6.  **SOP Definition Management** - Create, update, and delete SOP types.
7.  **Reset SOP Data** - Reset individual SOP types or all SOP data with backup generation.

## 🌐 Network Access & Production Deployment

The application supports both localhost and IP address access:

-   **Localhost**: `http://localhost:8080`
-   **IP Address**: `http://192.168.130.21:8080` (replace with your actual IP)
-   **LAN Access**: Accessible from other devices on the same network

### Network Configuration
If accessing via IP address, ensure:
1.  Your IP is added to `ALLOWED_ORIGINS` in `docker-compose.yml`
2.  Firewall allows traffic on ports `8080` and `8000`
3.  Docker containers can communicate properly

## 📊 API Documentation

### Authentication Endpoints
-   `POST /api/v1/login` - User login (returns JWT token)
-   `POST /api/v1/register` - User registration
-   `POST /api/v1/reset-password` - Reset current user's password

### User Endpoints
-   `GET /api/v1/profile` - Get current user profile
-   `PUT /api/v1/profile` - Update current user profile
-   `GET /api/v1/users/by-shift` - Get all users grouped by shift

### SOP Endpoints
-   `POST /api/v1/sop/activity` - Log SOP task completion
-   `GET /api/v1/sop/activities` - Get user's SOP activities
-   `GET /api/v1/sop/activities/today` - Get today's SOP activities for all users
-   `GET /api/v1/sop/today-activities/{sop_type}` - Get today's SOP activities for a specific SOP type
-   `GET /api/v1/sop/progress` - Get SOP progress and locked tasks
-   `POST /api/v1/sop/progress` - Save SOP progress
-   `POST /api/v1/sop/us-position-data` - Save US Position form data
-   `GET /api/v1/sop/us-position-data` - Get US Position form data for today

### Shared Calendar Endpoints
-   `POST /api/v1/marked-dates` - Mark a date on the shared calendar
-   `GET /api/v1/marked-dates` - Get all marked dates from all users
-   `DELETE /api/v1/marked-dates/{date}` - Remove a marked date (only user's own marks)

### Admin Endpoints (Requires Admin Role)
-   `GET /api/v1/admin/users` - List all users
-   `POST /api/v1/admin/users` - Create new user
-   `GET /api/v1/admin/users/{id}` - Get user by ID
-   `PUT /api/v1/admin/users/{id}` - Update user
-   `DELETE /api/v1/admin/users/{id}` - Delete user
-   `POST /api/v1/admin/users/{user_id}/shift` - Assign shift to user
-   `GET /api/v1/admin/sop/activities` - Get all SOP activities (with filters)
-   `GET /api/v1/admin/sop/report` - Download SOP reports
-   `GET /api/v1/admin/daily-report/check` - Check daily report availability
-   `GET /api/v1/admin/daily-report/download` - Download daily reports
-   `GET /api/v1/admin/us-position-activities` - Get US Position data formatted as SOP activities for admin view
-   `GET /api/v1/admin/us-position-report` - Download US Position data as an HTML report
-   `POST /api/v1/admin/reset-sop-type/{sop_type}` - Reset specific SOP type with backup generation
-   `POST /api/v1/admin/reset-all-sops` - Reset ALL SOP data
-   `DELETE /api/v1/admin/sop/activities/{activity_id}` - Delete specific SOP activity
-   `POST /api/v1/admin/sop-definitions` - Create a new SOP definition
-   `PUT /api/v1/admin/sop-definitions/{sop_id}` - Update an existing SOP definition
-   `DELETE /api/v1/admin/sop-definitions/{sop_id}` - Delete an SOP definition
-   `GET /api/v1/admin/sop-types` - Get all SOP types from definitions, enriched with activity counts and last activity dates

### System Endpoints
-   `GET /health` - Application health check
-   `GET /docs` - Interactive API documentation (Swagger UI)
-   `GET /redoc` - Alternative API documentation

## 🏗️ Project Structure

```
├── backend/                # Python FastAPI backend
│   ├── main.py             # Application entry point
│   ├── config.py           # Configuration management
│   ├── database.py         # MongoDB connection handling
│   ├── models.py           # Pydantic models and validation
│   ├── auth.py             # Authentication and authorization
│   ├── routes/             # API route handlers
│   │   ├── user.py         # User-related endpoints
│   │   └── admin.py        # Admin-only endpoints
│   ├── services/           # Business logic services
│   │   ├── admin.py        # Admin service functions
│   │   ├── daily_reset.py  # Daily reset and automation
│   │   └── report_utils.py # Utilities for report generation
│   └── requirements.txt    # Python dependencies
├── frontend/               # Static web frontend
│   ├── index.html          # Login page
│   ├── register.html       # User registration
│   ├── dashboard.html      # User dashboard
│   ├── admin.html          # Admin panel
│   ├── gift_sop.html       # GIFT SOP checklist
│   ├── gift_infra_sop.html # GIFT Infrastructure SOP
│   ├── mcx_sop.html        # MCX SOP checklist
│   ├── mcx_position_sop.html # MCX Position SOP checklist
│   ├── bse_daily_file_sop.html # BSE Daily Files SOP
│   ├── us_position_sop.html # US Position SOP checklist
│   ├── lease_line_sop.html # Lease Line SOP checklist
│   └── js/
│       └── api.js          # API client library
├── dockerfile              # Backend container definition
├── docker-compose.yml      # Multi-container orchestration
├── nginx.conf             # Nginx web server configuration
├── .env.example           # Environment variables template
└── README.md              # This documentation
```

## 🔒 Security Features

### Authentication & Authorization
-   **JWT Tokens**: Secure, stateless authentication with configurable expiration
-   **Password Hashing**: Bcrypt with salt for maximum password security
-   **Role-Based Access**: Admin and user roles with proper permissions
-   **Token Expiration**: Configurable token lifetime (default: 30 minutes)
-   **Session Security**: Automatic logout on token expiration

### Input Validation & Security
-   **Pydantic Validation**: Comprehensive input validation and sanitization
-   **SQL Injection Prevention**: MongoDB with parameterized queries
-   **XSS Protection**: Proper input escaping and validation
-   **CORS Configuration**: Configurable cross-origin resource sharing
-   **Rate Limiting**: Built-in FastAPI rate limiting capabilities

### Infrastructure Security
-   **Security Headers**: Nginx security headers (X-Frame-Options, etc.)
-   **Health Checks**: Container health monitoring
-   **Non-root User**: Docker containers run as non-root user
-   **Network Isolation**: Proper Docker network configuration

## 📊 Daily Automation & Reporting

### 3 AM IST Daily Reset
-   **Automatic Execution**: Runs every day at 3:00 AM Indian Standard Time
-   **Data Archival**: Previous day's activities archived to separate MongoDB collections
-   **Report Generation**: Daily reports automatically generated with completion statistics
-   **Data Preservation**: All historical data preserved for audit and compliance
-   **Admin Notification**: Dashboard alerts when daily reports are available

### Report Features
-   **SOP-Styled Reports**: Visual reports that match actual SOP page appearance
-   **User Attribution**: Shows who completed each task and when
-   **Completion Statistics**: Summary of activities, users, and completion rates
-   **Multiple Formats**: HTML (styled), HTML (standard), and CSV exports
-   **Historical Access**: Access to all previous daily reports
-   **US Position Reports**: Dedicated reports for US Position data.

## 🚀 Production Deployment

### Environment Configuration
Create a production `.env` file:
```bash
# Strong secret key (generate with: openssl rand -hex 32)
SECRET_KEY=your-very-long-and-random-secret-key-here

# Strong MongoDB password
MONGO_PASSWORD=your-strong-mongodb-password

# Your domain origins
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Production database name
MONGO_DB_NAME=production_db

# Access token expiration (in minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Production Security Checklist
- [ ] Change default admin password (`sysadmin/admin123`)
- [ ] Set strong `SECRET_KEY` (use `openssl rand -hex 32`)
- [ ] Configure strong MongoDB password
- [ ] Set up HTTPS with SSL certificates
- [ ] Configure proper CORS origins for your domain
- [ ] Enable MongoDB authentication in production
- [ ] Configure firewall rules (allow only necessary ports)
- [ ] Set up monitoring and logging
- [ ] Regular security updates
- [ ] Backup strategy implementation
- [ ] Configure proper timezone for daily resets

### Performance Optimization
- [ ] Enable Nginx gzip compression
- [ ] Configure proper caching headers
- [ ] Set up MongoDB indexes for frequently queried fields
- [ ] Monitor resource usage and scale as needed
- [ ] Implement rate limiting for API endpoints
- [ ] Configure log rotation
- [ ] Set up database connection pooling

## 📊 Monitoring & Troubleshooting

### Health Checks
- **Backend**: `GET /health` - Returns application status
- **Frontend**: `GET /health` - Returns Nginx status
- **Database**: Built-in MongoDB health checks in Docker
- **Daily Reset**: Automatic logging of daily reset operations

### Log Management
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs mongo

# Follow logs in real-time
docker-compose logs -f backend

# View daily reset logs
docker-compose logs backend | grep "daily_reset"
```

### Common Issues & Solutions

1. **"Cannot connect to backend"**
   - Check if backend container is running: `docker-compose ps`
   - Verify network connectivity: `docker-compose logs backend`
   - Ensure MongoDB is accessible: `docker-compose logs mongo`

2. **"Authentication failed"**
   - Verify JWT secret key configuration
   - Check token expiration settings
   - Validate user credentials in database

3. **"CORS errors when accessing via IP"**
   - Add your IP to `ALLOWED_ORIGINS` in docker-compose.yml
   - Restart containers: `docker-compose restart`

4. **"Database connection refused"**
   - Verify MongoDB container is running and healthy
   - Check MongoDB credentials in environment variables
   - Ensure database initialization completed

5. **"Daily reset not working"**
   - Check backend logs for scheduler errors
   - Verify timezone configuration
   - Ensure MongoDB has write permissions

### Database Management

**Connect to MongoDB**
```bash
docker exec -it mongodb mongosh -u admin -p admin --authenticationDatabase admin
```

**View Daily Archives**
```bash
# List archive collections
db.adminCommand("listCollections").cursor.firstBatch.filter(c => c.name.includes("archive"))

# View specific day's archive
db.sop_activities_archive_2024_01_15.find().pretty()
```

**Backup and Restore**
```bash
# Backup database
docker exec mongodb mongodump --username admin --password admin --authenticationDatabase admin --db appdb --out /backup

# Restore database
docker exec mongodb mongorestore --username admin --password admin --authenticationDatabase admin --db appdb /backup/appdb
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use meaningful commit messages
- Add docstrings to functions and classes
- Update documentation for new features
- Test your changes thoroughly
- Ensure all health checks pass


## 🆘 Support

For support and questions:
- **Issues**: Create an issue in the repository
- **Documentation**: Check this README and API docs at `/docs`
- **Logs**: Check application logs for error details

## 🔄 Changelog

### v3.0.0 (Current - Production Ready)
- **NEW**: Complete SOP tracking system
- **NEW**: Advanced admin dashboard with filtering
- **NEW**: Daily report generation and archival
- **NEW**: US Position data tracking and reporting
- **NEW**: Shared calendar for marking dates
- **NEW**: Shift plan view for user assignments
- **NEW**: SOP definition management (create, update, delete SOP types)
- **NEW**: Manual SOP reset for individual types or all data with backup generation
- **ENHANCED**: User management with comprehensive admin panel

### v2.0.0
- **NEW**: Complete SOP tracking system with 4 SOP types
- **NEW**: Task locking and collaborative editing
- **NEW**: Daily reset automation at 3 AM IST
- **NEW**: SOP-styled HTML reports with user attribution
- **NEW**: Advanced admin dashboard with filtering
- **NEW**: Daily report generation and archival
- **ENHANCED**: User management with comprehensive admin panel
- **ENHANCED**: Security with improved authentication and validation
- **ENHANCED**: UI/UX with modern responsive design
- **ENHANCED**: API documentation and error handling

### v1.0.0 (Initial Release)
- Basic user management system
- JWT authentication
- Docker containerization
- Simple web interface

---

**Made with ❤️ for efficient SOP management and user administration**