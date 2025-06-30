"use client";

import { Box, Typography, Card, CardContent } from '@mui/material';
import { useEffect, useState } from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export default function AboutPage() {
  const [metrics, setMetrics] = useState<{ r2?: number; rmse?: number }>({});
  const [metricsLoading, setMetricsLoading] = useState(false);
  const [metricsError, setMetricsError] = useState<string | null>(null);

  useEffect(() => {
    setMetricsLoading(true);
    fetch(`${API_BASE_URL}/model/metrics`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch model metrics');
        return res.json();
      })
      .then(data => {
        setMetrics(data);
        setMetricsLoading(false);
      })
      .catch(() => {
        setMetricsError('Could not load model metrics');
        setMetricsLoading(false);
      });
  }, []);

  return (
    <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
      <Card sx={{ maxWidth: 700, width: '100%' }}>
        <CardContent>
          <Typography variant="h4" gutterBottom>
            About Show Bound Analytics
          </Typography>
          <Typography variant="subtitle1" color="text.secondary" gutterBottom>
            Predicting the Path to The Show
          </Typography>
          <Typography variant="body1" paragraph>
            <b>Show Bound Analytics</b> is a modern baseball analytics platform built for robust player evaluation, advanced statistics, and machine learning insights. Our backend is fully normalized and based on canonical data from Baseball Reference, supporting real MLB player analytics, projections, and comparisons.
          </Typography>
          <Typography variant="body1" paragraph>
            <b>How does the model work?</b> Our machine learning model is <b>continuously retrained</b> as new player data is ingested daily. This means the ratings, projections, and comparisons you see are always up-to-date and reflect the latest available data. The model's performance is measured in real time and shown below.
          </Typography>
          <Typography variant="body1" paragraph>
            <b>How do player ratings work?</b>
            <br />
            <b>Show Bound Analytics</b> uses a modern, data-driven approach to player evaluation, inspired by professional scouting and MLB The Show. Ratings are calculated as follows:
          </Typography>
          <Box component="div" sx={{ mb: 2 }}>
            <ul>
              <li><b>Stat Ingestion:</b> We pull the latest MLB player stats from Baseball Reference, including advanced, value, and standard tables for batting, pitching, and fielding.</li>
              <li><b>Feature Extraction:</b> For each player, we extract a comprehensive set of features (e.g., exit velocity, home runs, strikeout rate, fielding metrics).</li>
              <li><b>Normalization:</b> Each stat is normalized using the 1st and 99th percentiles of all MLB players, so elite performances get full credit.</li>
              <li><b>PCA & Tool Ratings:</b> We use Principal Component Analysis (PCA) to identify the most important stats for each tool (contact, power, discipline, fielding, speed, pitching). Each tool rating is based on the most impactful stat(s) for that skill.</li>
              <li><b>Scout-Style Grades:</b> Ratings are mapped to the 40–99 (MLB The Show) scale, with 99 as the maximum. Only the very best MLB players approach the top of the scale.</li>
              <li><b>Player Type Awareness:</b> Pitchers, hitters, and two-way players are rated using the stats most relevant to their roles.</li>
            </ul>
            <Typography variant="body2" color="text.secondary">
              This system ensures that ratings are both statistically robust and intuitively meaningful—so you can compare players just like a pro scout or front office analyst.
            </Typography>
          </Box>
          <Box sx={{ mt: 3, mb: 2 }}>
            <Card variant="outlined" sx={{ bgcolor: '#f5f5f5' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Current Model Performance
                </Typography>
                {metricsLoading ? (
                  <Typography variant="body2">Loading model metrics...</Typography>
                ) : metricsError ? (
                  <Typography color="error" variant="body2">{metricsError}</Typography>
                ) : (
                  <>
                    <Typography variant="body2">
                      <b>R²:</b> {typeof metrics.r2 === 'number' && metrics.r2 !== null ? metrics.r2.toFixed(3) : 'N/A'}
                    </Typography>
                    <Typography variant="body2">
                      <b>RMSE:</b> {typeof metrics.rmse === 'number' && metrics.rmse !== null ? metrics.rmse.toFixed(3) : 'N/A'}
                    </Typography>
                  </>
                )}
              </CardContent>
            </Card>
          </Box>
          <Typography variant="body1" paragraph>
            <b>Features:</b>
          </Typography>
          <Box component="div" sx={{ mb: 2 }}>
            <ul>
              <li>Player list with search/filter</li>
              <li>Player detail page with ratings, comps, projections, and stats</li>
              <li>Canonical stat tables based on Baseball Reference</li>
              <li>ML-driven player ratings, comps, and projections</li>
              <li>Modern, responsive UI</li>
            </ul>
          </Box>
          <Typography variant="body2" color="text.secondary">
            Built with FastAPI, SQLAlchemy, scikit-learn, Next.js, and MUI. Data updates daily.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
} 