# Prostate Cancer Patient Management System

## Overview

This is a comprehensive Flask-based web application for managing prostate cancer patients in a Vietnamese healthcare environment. The system provides complete patient record management, treatment tracking, blood test monitoring, medical event logging, TNM staging evaluation, pathology image management, and AI-powered risk assessment capabilities. It features a medical-grade user interface with Vietnamese language support, designed to optimize healthcare workflows. Key capabilities include AI prediction for biochemical recurrence (BCR), ADT benefit assessment, and adverse event risk warnings, alongside advanced follow-up scheduling, CTCAE-compliant adverse event tracking, and AI-powered PSA monitoring.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 with Flask
- **UI Framework**: Bootstrap 5.3.0 for responsive design
- **Icons**: Font Awesome 6.4.0 (medical and interface icons)
- **Typography**: Google Fonts (Roboto and Open Sans)
- **Styling**: Custom CSS with medical color scheme and Vietnamese interface support
- **JavaScript**: Chart.js for data visualization (PSA and testosterone tracking)

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database ORM**: SQLAlchemy with Flask-SQLAlchemy
- **Forms**: Flask-WTF with WTForms
- **Session Management**: Flask's built-in session handling with configurable secret key
- **Middleware**: ProxyFix for reverse proxies

### Database Design
- **ORM**: SQLAlchemy with declarative base model
- **Database Support**: SQLite (default) with PostgreSQL compatibility
- **Models**: Patient, Treatment, Medication, BloodTest, ImagingRecord, PatientEvent, AdverseEvent, and specialized treatment event models (Surgery, Radiation, Hormone Therapy, Chemotherapy, Systemic Therapy).
- **Relationships**: One-to-many between patients and related data; cascade deletion for integrity.

### Key Components
- **Core Models**: Patient, Treatment, BloodTest, ImagingRecord, PatientEvent, AdverseEvent, Treatment Event Models.
- **Form System**: Comprehensive forms for patient data, various treatments, medication, blood tests, imaging, medical events, follow-up scheduling, PSA analysis, adverse event reporting, and notification settings, all with Vietnamese field labels.
- **Internationalization**: Centralized Vietnamese translations and specialized medical vocabulary.
- **AI Prediction Module**: Biochemical Recurrence (BCR) prediction (2-year and 5-year), ADT Benefit Assessment, and Adverse Event Risk Warnings using Random Forest and Gradient Boosting models.
- **Follow-up and Adverse Event Management**: Advanced follow-up scheduling with reminders, CTCAE-compliant adverse event tracking, and AI-powered PSA monitoring (doubling time, velocity, alerts).
- **TNM Staging System**: Integration of clinical and pathological T, N, M classifications.
- **Pathology Image Upload**: Automated naming convention.
- **PDF Report Generation**: Comprehensive patient reports including administrative info, diagnosis, TNM staging, AI assessment, and blood test charts with full Vietnamese font support.
- **Data Management**: Bulk patient selection and deletion (admin-only) with comprehensive data cleanup.

## External Dependencies

### Frontend Dependencies
- **Bootstrap 5.3.0**: UI framework
- **Font Awesome 6.4.0**: Icon library
- **Google Fonts**: Typography
- **Chart.js**: Data visualization

### Backend Dependencies
- **Flask**: Core web framework
- **Flask-SQLAlchemy**: ORM integration
- **Flask-WTF**: Form handling and CSRF protection
- **WTForms**: Form validation
- **Werkzeug**: WSGI utilities
- **Scipy**: For statistical PSA analysis.
- **Twilio**: For SMS notifications.
- **SMTP**: For email notifications.
- **Google Gemini**: For AI risk assessment.

### Database Dependencies
- **SQLite**: Default (development)
- **PostgreSQL**: Production support

## Recent Changes (August 3, 2025)

✓ **Complete cPanel 122.0.16 Terminal Deployment Guide**: Created comprehensive 11-section deployment guide for shared hosting without SSH access
✓ **Advanced Terminal-Based Troubleshooting**: Built detailed troubleshooting guide with Terminal commands for common deployment issues
✓ **Production-Ready Database Setup**: Complete PostgreSQL/MySQL setup instructions with connection testing via Terminal
✓ **Python Package Installation via Terminal**: Step-by-step pip3 installation guide for shared hosting environments
✓ **Security and Performance Optimization**: Terminal-based monitoring, backup scripts, and maintenance procedures