# n8n Workflow Popularity Tracker

A comprehensive system that tracks and analyzes the popularity of n8n workflows across multiple platforms. Built as a student project to demonstrate data collection, API development, and web analytics capabilities.

## ✨ Features

- **Multi-Platform Data Collection**: Gathers workflow data from YouTube, Google Trends, and n8n Forum
- **Real-Time Analytics Dashboard**: Interactive web interface with filtering and search capabilities  
- **REST API**: Full API access with pagination, sorting, and filtering options
- **Geographic Segmentation**: Tracks popularity across US and India markets
- **Evidence-Based Ranking**: Uses real metrics like views, likes, comments, and search volumes
- **Loading States**: Professional UX with "Please wait" loading indicators
- **Responsive Design**: Clean, minimal interface that works on all devices

## 🚀 Quick Start

1. **Clone and Install**
   ```bash
   git clone <your-repo>
   cd Project1
   pip install -r requirements.txt
   ```

2. **Set up Environment**
   
   Create a `.env` file with:
   
   ```env
   YOUTUBE_API_KEY=your_youtube_api_key
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
   PORT=5000
   ```

3. **Run the Application**
   
   ```bash
   python app.py
   ```

4. **Access Dashboard**
   
   Open <http://localhost:5000> in your browser

## 🎯 Usage

### Web Dashboard

- **Filter workflows** by platform (YouTube, Google Trends, Forum)
- **Sort results** by engagement score, views, or date
- **Search workflows** by name or keywords
- **View detailed metrics** for each workflow with evidence links
- **Export data** directly from the browser

### API Endpoints

- `GET /api/workflows` - Retrieve workflows with filtering options
  - Parameters: `platform`, `country`, `sort`, `limit`, `offset`
- `GET /api/stats` - Get platform and country statistics
- `POST /api/collect` - Trigger manual data collection
- `GET /api/health` - Check system status

## 📊 Data Collection & Results

**Automated Data Collection:**

- Run `python scheduler.py` for daily updates
- YouTube Data API v3 for real workflow video metrics
- Google Trends API (pytrends) for search interest and trend analysis
- Tracks keyword popularity changes over 3-month periods

**Results Achieved:**

- **180+ workflows collected** (exceeding 50+ requirement)
- **Platform segmentation:** YouTube (150), Google Trends (30)
- **Geographic segmentation:** US (86), India (94)
- **Rich evidence:** Real view counts, engagement metrics, search volumes

## 💾 Dataset Export

The complete dataset is available in `n8n_project_dataset.json` with:

- Full workflow data with popularity evidence
- Platform and country segmentation
- Engagement scores and metrics
- Source URLs for verification

## 🛠️ Technologies Used

- Python (Flask framework)
- MongoDB Atlas (cloud database)
- YouTube Data API v3
- Google Trends integration
- HTML/CSS/JavaScript frontend
- RESTful API design