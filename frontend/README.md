# AIDD Paper Tracker

A modern academic paper tracker for AI Drug Discovery research. Browse, filter, and organize papers from arXiv, bioRxiv, and ChemRxiv with relevance tagging.

## Features

- **Multi-source Integration**: Fetch papers from arXiv, bioRxiv, and ChemRxiv
- **Advanced Search**: Search by title, abstract, authors, or all fields
- **Smart Filtering**: Filter by source, category, date range, and relevance status
- **Relevance Tagging**: Mark papers as relevant, irrelevant, or untagged
- **Real-time Statistics**: View paper counts and distribution across sources
- **Responsive Design**: Works on desktop and mobile devices

## Tech Stack

- **Frontend**: React + TypeScript + Vite
- **Backend**: Python FastAPI
- **Database**: SQLite
- **UI**: Tailwind CSS + shadcn/ui components
- **State Management**: TanStack Query

## Getting Started

### Prerequisites

- Node.js 18+ 
- Python 3.8+
- npm or yarn

### Installation

1. Clone the repository
2. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```
3. Install backend dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

### Development

1. Start the backend server:
   ```bash
   cd backend
   python main.py
   ```

2. Start the frontend development server:
   ```bash
   cd frontend
   npm run dev
   ```

The application will be available at `http://localhost:5174`

## Usage

1. **Filter Papers**: Use the sidebar to filter by data sources, categories, relevance status, and date ranges
2. **Search**: Use the search bar with scope selection (title, abstract, authors, all fields)  
3. **Tag Relevance**: Click the relevance buttons on each paper card to mark them
4. **Update Papers**: Use the "Update Papers" button to fetch new papers from external sources
5. **Export**: Export filtered results (coming soon)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.