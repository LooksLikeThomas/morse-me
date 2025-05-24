# Morse-Me
**Learn Morse Code, One Friend at a Time!**

Turn dots and dashes into a global experience with Morse-Me. Get to meet new people and chat with friends across the world using real Morse code and learn together as you go. Whether you're a total beginner or brushing up your skills, Morse-Me makes learning fun, social, and totally unique. Start morsing, start connecting one dot at a time.

## Features

### Core Functionality
- [ ] **User Management**
  - [ ] Registration
  - [ ] Login
  - [ ] Profile Customization
- [ ] **Friend System**
- [ ] **Morse Code Channels**
  - [ ] Random person (No Login Required)
  - [ ] With friends

### Optional Features
- [ ] **Learning & Practice**

## Tech Stack

- **Frontend:** Nuxt.js
- **Backend:** FastAPI
- **Data Access Layer:** SQLModel
- **Database:** MySQL
- **Authentication:** Firebase

## Project Structure

```
morse-me/
├── backend/          # FastAPI application
├── frontend/         # Nuxt.js application
├── docs/            # Project documentation
└── README.md        # This file
```

## Getting Started

### Prerequisites
- Node.js (v18 or higher)
- Python (v3.9 or higher)
- MySQL
- Firebase account

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd morse-me
   ```

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   # Configure environment variables
   # Start the development server
   uvicorn app.main:app --reload
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   # Configure environment variables
   npm run dev
   ```

## Contributors

| Name | GitHub Account |
|------|----------------|----------------|
| Thomas | [@LooksLikeThomas](https://github.com/LooksLikeThomas) |
| Marius | [@lordw0lt3r](https://github.com/lordw0lt3r) |

## License

This project is developed as part of an academic project.