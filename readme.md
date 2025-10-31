# 🌐 Wendy - Telegram Data Collection System

Wendy is an automated data collection and processing system designed to gather and analyze data from Telegram channels and groups. It features a microservices architecture with workers for listening, reading, processing, and a web interface for management.

## 🏗️ Architecture

The system consists of four main components:

### 🔄 **Listener Worker** (Python)
- Monitors Telegram channels using Telethon library
- Downloads files and extracts text messages
- Uses dual client rotation for reliability
- Publishes file paths to Redis for processing

### 📖 **Reader Worker** (Python)
- Listens to Redis file channel
- Processes downloaded files and archives
- Applies regex rules for data filtering
- Stores processed data in organized structure

### 🖥️ **Web Backend** (Node.js/Express)
- REST API with JWT authentication
- PostgreSQL database for data storage
- User management and session handling
- Data retrieval endpoints

### 🎨 **Web Frontend** (Next.js/React)
- Modern responsive UI
- Authentication forms
- Dashboard for data visualization
- API proxy to backend services

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.8+ and pip
- **PostgreSQL** 13+
- **Redis** 6+
- **Docker** (optional, for easy setup)

### Option 1: Docker Setup (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd wendy

# Run setup script
chmod +x scripts/setup.sh
./scripts/setup.sh

# Start all services
chmod +x scripts/start.sh
./scripts/start.sh
```

### Option 2: Manual Setup

1. **Database Setup**
```bash
# Start PostgreSQL and Redis services
sudo service postgresql start
sudo service redis-server start

# Create database
createdb wendy_db
psql -d wendy_db -f backend/setup.sql
```

2. **Environment Configuration**
```bash
# Copy and edit environment files
cp backend/config.env.template backend/.env
# Edit backend/.env with your settings
```

3. **Install Dependencies**
```bash
# Backend
cd backend && npm install

# Frontend
cd ../frontend && npm install

# Python workers
cd ../listener && pip install -r requirements.txt
cd ../reader && pip install -r requirements.txt
```

4. **Configure Telegram API**
```bash
# Edit listener/config.ini with your Telegram API credentials
# You need to create Telegram apps at https://my.telegram.org/
```

5. **Start Services**
```bash
# Start all services
./scripts/start.sh
```

## 🔧 Configuration

### Backend Environment (.env)
```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=wendy_db
DB_USER=postgres
DB_PASSWORD=password

# JWT Secrets (generate strong random strings)
JWT_SECRET=your-super-secret-jwt-key-here
JWT_REFRESH_SECRET=your-super-secret-refresh-key-here

# Server
BACKEND_PORT=4141
DATA_PATH=../../dist

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Telegram Configuration
Edit `listener/config.ini` and `reader/config.ini`:

```ini
[TELE_API_1]
APP_ID=your_app_id_1
HASH_ID=your_api_hash_1
PHONE=+1234567890
USERNAME=@your_bot_username_1

[TELE_API_2]
APP_ID=your_app_id_2
HASH_ID=your_api_hash_2
PHONE=+0987654321
USERNAME=@your_bot_username_2
```

### Data Processing Rules

Edit `rules/rules.yaml` for data extraction patterns:
```yaml
line_rules:
  - name: credentials
    pattern: '[^\s:]+:[^\s:]+:[^\s]+'
  - name: urls
    pattern: 'https?://[^\s:]+:[^\s:]+:[^\s]+'
```

## 🎯 Usage

### First Time Setup

1. **Create Admin User**
```bash
# The first user registration creates an admin account
# Visit http://localhost:4000/register
```

2. **Login**
```bash
# Visit http://localhost:4000/login
```

3. **Access Dashboard**
```bash
# After login, you'll be redirected to the dashboard
# Click "Sync Data" to process collected data
```

### Worker Management

**Start Workers:**
```bash
# Listener Worker
cd listener && python telegram_listener.py

# Reader Worker
cd reader && python reader.py
```

**Monitor Logs:**
```bash
# View logs
tail -f logs/run.log
tail -f logs/error.log
```

## 📊 API Endpoints

### Authentication
- `POST /api/user/token` - Login
- `POST /api/user/init` - Register first user
- `GET /api/user/verify` - Verify token

### Data
- `GET /api/reader/read` - Sync data from files

## 🔍 Data Processing

### File Types Supported
- Text files (.txt)
- Archives: ZIP, RAR, 7Z, TAR, GZ

### Data Rules
The system uses regex patterns to extract:
- User credentials (user:pass:url)
- URLs and links
- Custom patterns defined in rules files

### Storage Structure
```
storage/           # Downloaded files from Telegram
dist/             # Processed data files (daily)
extract/          # Temporary extraction directory
logs/             # Application logs
sessions/         # Telegram session files
```

## 🔐 Security Features

- **JWT Authentication** with refresh tokens
- **Password Policy** (8+ chars, mixed case, numbers)
- **Session Management** with expiration
- **Role-based Access Control** (ACL system)
- **Secure Cookies** (httpOnly, secure flags)

## 🛠️ Development

### Project Structure
```
wendy/
├── backend/           # Node.js API server
├── frontend/          # Next.js web application
├── listener/          # Telegram listener worker
├── reader/            # File processing worker
├── rules/            # Data processing rules
├── scripts/          # Setup and startup scripts
└── docker-compose.yml # Docker configuration
```

### Adding New Rules

1. Edit `rules/rules.yaml` for data patterns
2. Edit `rules/links.yaml` for URL patterns
3. Restart reader worker

### Customizing UI

- Frontend uses **Tailwind CSS** for styling
- Components are in `frontend/src/app/components/`
- Pages are in `frontend/src/app/[page]/`

## 🐛 Troubleshooting

### Common Issues

**Database Connection Failed**
```bash
# Check PostgreSQL status
sudo service postgresql status
# Check connection
psql -h localhost -U postgres -d wendy_db
```

**Redis Connection Failed**
```bash
# Check Redis status
redis-cli ping
```

**Telegram API Errors**
- Verify API credentials in config files
- Check phone numbers and usernames
- Ensure Telegram apps are created correctly

**Worker Not Processing Files**
```bash
# Check Redis connectivity
redis-cli ping
# Check worker logs
tail -f logs/error.log
```

### Logs Location
- `logs/run.log` - General operations
- `logs/error.log` - Error messages
- Worker logs are also printed to console

## 📈 Monitoring

### Health Checks
- Backend: `GET /api/health` (if implemented)
- Database: Check PostgreSQL logs
- Redis: `redis-cli info`

### Performance Tuning
- Adjust worker timeouts in config files
- Monitor Redis memory usage
- Check file processing queue length

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is designed for legitimate data collection and research purposes. Users are responsible for complying with Telegram's Terms of Service and applicable laws regarding data collection and privacy.

---

**Built with ❤️ for automated data processing workflows**