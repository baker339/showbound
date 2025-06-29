# Baseball Prospect Analysis System

A comprehensive baseball scouting and analysis platform that combines advanced machine learning with traditional scouting to evaluate prospects from high school, college, and minor leagues. The system provides MLB The Show style ratings, KNN player comparisons, and AI-powered success predictions.

## 🚀 Features

### Core Functionality
- **Advanced Player Ratings**: MLB The Show style ratings (40-99 scale) for all major skills
- **KNN Player Comparisons**: Find similar MLB players using machine learning algorithms
- **MLB Success Predictions**: AI-powered career projections and risk assessments
- **Comprehensive Data Pipeline**: Integration with Statcast, MiLB, NCAA, and HS data sources
- **Modern Web Interface**: Beautiful, responsive UI with interactive visualizations

### Technical Features
- **Machine Learning Models**: K-Nearest Neighbors for player similarity, Random Forest for ratings
- **Real-time Data Processing**: Live Statcast data ingestion and analysis
- **Advanced Statistics**: Exit velocity, launch angle, sprint speed, and more
- **Scouting Reports**: Digital scouting reports with tool grades and future value assessments
- **Search & Filter**: Advanced prospect search and filtering capabilities

## 🏗️ Architecture

### Backend (FastAPI + SQLAlchemy)
- **FastAPI**: High-performance web framework for APIs
- **SQLAlchemy**: Database ORM with PostgreSQL support
- **Scikit-learn**: Machine learning models for player analysis
- **PyBaseball**: Baseball data collection and processing
- **Alembic**: Database migrations and schema management

### Frontend (Next.js + Material-UI)
- **Next.js 15**: React framework with TypeScript
- **Material-UI**: Modern component library
- **Recharts**: Interactive data visualizations
- **SWR**: Data fetching and caching

### Database Schema
- **Players**: MLB players with advanced stats
- **Prospects**: HS, NCAA, and MiLB prospects
- **PlayerRatings**: MLB The Show style ratings
- **ScoutingReports**: Digital scouting reports
- **PlayerComparisons**: KNN similarity data
- **AdvancedStats**: Comprehensive statistical data

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Node.js 18+
- PostgreSQL 12+

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database credentials

# Initialize database
alembic upgrade head

# Run the server
uvicorn main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 📊 Data Sources

### Current Integrations
- **Statcast**: MLB pitch-by-pitch data
- **MiLB**: Minor league statistics
- **NCAA**: College baseball data
- **High School**: Prep prospect information
- **MLB Draft**: Draft pick data and analysis

### Data Pipeline
1. **Data Ingestion**: Automated collection from multiple sources
2. **Data Processing**: Cleaning and standardization
3. **Feature Engineering**: Creating ML-ready features
4. **Model Training**: KNN and rating models
5. **API Serving**: Real-time predictions and comparisons

## 🎯 Key Components

### Player Ratings System
The system calculates comprehensive ratings similar to MLB The Show:

- **Hitting**: Contact (L/R), Power (L/R), Vision, Discipline
- **Fielding**: Fielding, Arm Strength, Arm Accuracy, Speed
- **Overall**: Weighted average with confidence scoring
- **Potential**: Future projection based on age and development

### KNN Player Comparisons
- **Feature Vector**: 12-dimensional player profile
- **Similarity Scoring**: Euclidean distance with normalization
- **MLB Comparisons**: Find similar established MLB players
- **Explanation**: Provide reasoning for similarities

### Success Predictions
- **MLB Debut Probability**: Likelihood of reaching MLB
- **Career WAR Projection**: Expected career value
- **Risk Assessment**: Low/Medium/High risk factors
- **ETA**: Expected MLB debut year
- **Ceiling/Floor**: Best and worst-case scenarios

## 🔧 API Endpoints

### Prospects
- `GET /prospects` - List all prospects
- `GET /prospects/{id}` - Get detailed prospect information
- `GET /prospects/{id}/ratings` - Get MLB The Show style ratings
- `GET /prospects/{id}/similar` - Get similar MLB players
- `GET /prospects/{id}/prediction` - Get MLB success prediction
- `POST /prospects/{id}/scouting-report` - Create scouting report

### Players
- `GET /players` - List MLB players
- `GET /players/{id}/ratings` - Get player ratings
- `GET /players/{id}/similar` - Get similar players
- `GET /players/{id}/stats` - Get advanced statistics

## 🎨 Frontend Features

### Interactive Components
- **Player Cards**: MLB The Show style player cards with radar charts
- **Comparison Views**: Side-by-side player comparisons
- **Prediction Dashboard**: Success probability and career projections
- **Search & Filter**: Advanced prospect discovery
- **Responsive Design**: Works on desktop and mobile

### Visualizations
- **Radar Charts**: Skill ratings visualization
- **Progress Bars**: Rating comparisons
- **Color Coding**: Performance indicators
- **Interactive Tables**: Sortable prospect lists

## 🤖 Machine Learning Models

### K-Nearest Neighbors (KNN)
- **Purpose**: Find similar players
- **Features**: 12-dimensional player profile
- **Algorithm**: Ball Tree for efficient search
- **Output**: Similarity scores and player comparisons

### Random Forest
- **Purpose**: Overall rating prediction
- **Features**: Player statistics and demographics
- **Training**: Historical player data
- **Output**: 40-99 scale ratings

### Feature Engineering
- **Statistical Features**: Exit velocity, launch angle, etc.
- **Demographic Features**: Age, level, position
- **Derived Features**: Percentiles, ratios, trends
- **Normalization**: Standard scaling for ML models

## 📈 Performance Metrics

### Model Performance
- **KNN Accuracy**: Similarity validation with known comparisons
- **Rating Correlation**: Predicted vs. actual performance
- **Prediction Accuracy**: MLB success prediction validation

### System Performance
- **API Response Time**: < 200ms for most endpoints
- **Data Processing**: Real-time Statcast ingestion
- **Scalability**: Horizontal scaling support

## 🔮 Future Enhancements

### Planned Features
- **Advanced Analytics**: More sophisticated ML models
- **Real-time Updates**: Live game data integration
- **Mobile App**: Native iOS/Android applications
- **Scouting Tools**: Field scouting integration
- **Team Analytics**: Organization-level insights

### Data Expansions
- **International Prospects**: Global scouting data
- **Historical Analysis**: Long-term trend analysis
- **Injury Prediction**: Health and durability models
- **Market Value**: Financial impact projections

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **MLB Advanced Media**: For Statcast data
- **Baseball Reference**: For historical statistics
- **FanGraphs**: For advanced metrics inspiration
- **MLB The Show**: For rating system inspiration

## 📞 Support

For questions or support, please open an issue on GitHub or contact the development team.

---

**Built with ❤️ for the baseball community** 