# QuickBuild Estimate - Construction Estimation System

## Overview

QuickBuild Estimate is a Flask-based web application designed for custom home builders to generate professional construction estimates quickly. The system combines AI-powered blueprint analysis, CSV data processing, and automated cost calculations to produce bank-ready estimates in under 15 seconds.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **Flask**: Python web framework serving as the core application
- **SQLAlchemy**: ORM for database operations with declarative base models
- **Session-based Authentication**: Simple admin login system using environment variables

### Frontend Architecture
- **Server-side Rendered Templates**: Jinja2 templates with Bootstrap 5 dark theme
- **Progressive Enhancement**: JavaScript for form validation and UI interactions
- **Responsive Design**: Mobile-first approach using Bootstrap grid system

### Database Design
- **SQLite**: Default local database with PostgreSQL support via environment configuration
- **Estimate-centric Schema**: Core entity with related material and labor items
- **JSON Storage**: Flexible schema for blueprint analysis results and CSV data
- **Usage Tracking**: OpenAI API spend monitoring and limits

## Key Components

### Core Models
- **Estimate**: Central entity containing project data, file references, cost calculations, and metadata
- **MaterialItem/LaborItem**: Cost line items linked to estimates with bundle categorization
- **OpenAIUsage**: Monthly spend tracking for API cost control

### AI Integration Services
- **Blueprint Analysis**: GPT-4 Vision API for area takeoff from PDF blueprints
- **CSV Schema Detection**: GPT-4 JSON mode for automatic column mapping and bundle inference
- **Proposal Generation**: AI-assisted summary writing for client-facing documents

### Cost Calculation Engine
- **Multi-layered Pricing**: Area-based PSF rates + unit items + profit + contingency
- **Bundle Management**: Dynamic cost groupings with toggle functionality
- **Category-based Rates**: Different PSF pricing for interior, exterior, and utility areas

### File Processing
- **PDF Handling**: Blueprint upload and Vision API processing
- **CSV Parsing**: Materials and labor data import with schema validation
- **Secure Upload**: File type validation and size limits (16MB max)

## Data Flow

1. **Project Creation**: User uploads PDF blueprint and CSV files with project name
2. **AI Processing**: 
   - Blueprint analyzed for room areas and categories
   - CSV files processed for schema detection and bundle inference
3. **Cost Calculation**: System applies layered pricing logic to generate estimates
4. **Interactive Review**: User can toggle bundles and adjust profit/contingency rates
5. **Output Generation**: Professional PDF proposals created with AI-generated summaries
6. **Historical Tracking**: Estimates saved with 90-day retention policy

## External Dependencies

### AI Services
- **OpenAI GPT-4**: Vision and text processing with $50 monthly spend cap
- **Environment Variables**: OPENAI_API_KEY and OPENAI_SPEND_CAP for cost control

### File Processing
- **ReportLab**: PDF generation for professional proposals
- **Werkzeug**: File upload handling and security utilities

### Frontend Libraries
- **Bootstrap 5**: Dark theme UI framework
- **Feather Icons**: Consistent iconography
- **Vanilla JavaScript**: Form validation and interactions

## Deployment Strategy

### Environment Configuration
- **Flask Development**: Debug mode enabled with host 0.0.0.0:5000
- **Database Flexibility**: SQLite default with PostgreSQL support via DATABASE_URL
- **Session Management**: Configurable secret key via SESSION_SECRET environment variable

### Security Measures
- **Admin Authentication**: Single password protection via ADMIN_PASSWORD
- **File Upload Security**: Type validation and secure filename handling
- **Proxy Support**: ProxyFix middleware for reverse proxy deployments

### Data Management
- **Automatic Cleanup**: 90-day retention with nightly purge functionality
- **Upload Organization**: Dedicated uploads directory with automatic creation
- **Database Initialization**: Automatic table creation on startup

### Cost Controls
- **API Spend Limits**: Monthly OpenAI usage caps with exception handling
- **Usage Tracking**: Per-month spend monitoring in database
- **Error Handling**: Graceful degradation when limits exceeded

The application follows a modular architecture with clear separation of concerns between authentication, file processing, AI services, cost calculations, and PDF generation. The system is designed for easy deployment and maintenance while providing robust cost estimation capabilities for construction professionals.