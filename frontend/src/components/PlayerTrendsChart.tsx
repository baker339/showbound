import React from 'react';
import { Box, Typography } from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface HistoryEntry {
  season: number | string;
  overall: number;
}

interface PlayerTrendsChartProps {
  hittingHistory?: HistoryEntry[];
  pitchingHistory?: HistoryEntry[];
  playerType: 'position_player' | 'pitcher' | 'two_way' | string;
}

const PlayerTrendsChart: React.FC<PlayerTrendsChartProps> = ({ hittingHistory, pitchingHistory, playerType }) => {
  // Defensive: ensure arrays
  const safeHitting = Array.isArray(hittingHistory) ? hittingHistory : [];
  const safePitching = Array.isArray(pitchingHistory) ? pitchingHistory : [];

  // Prepare data for chart
  let chartData: any[] = [];
  if (playerType === 'two_way' && safePitching.length > 0) {
    // Merge by season
    const allSeasons = Array.from(new Set([
      ...safeHitting.map(h => h.season),
      ...safePitching.map(p => p.season),
    ])).sort();
    chartData = allSeasons.map(season => ({
      season,
      Hitting: safeHitting.find(h => h.season === season)?.overall ?? null,
      Pitching: safePitching.find(p => p.season === season)?.overall ?? null,
    }));
  } else {
    chartData = safeHitting.map(h => ({ season: h.season, Overall: h.overall }));
  }

  if (chartData.length === 0) {
    return (
      <Box sx={{ width: '100%', height: 120, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Typography color="text.secondary">No historical ratings data available.</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%', height: 320 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>
        Historical Overall Ratings
      </Typography>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="season" />
          <YAxis domain={[40, 99]} />
          <Tooltip />
          <Legend />
          {playerType === 'two_way' && safePitching.length > 0 ? (
            <>
              <Line type="monotone" dataKey="Hitting" stroke="#1976d2" strokeWidth={2} dot={{ r: 4 }} />
              <Line type="monotone" dataKey="Pitching" stroke="#d32f2f" strokeWidth={2} dot={{ r: 4 }} />
            </>
          ) : (
            <Line type="monotone" dataKey="Overall" stroke="#1976d2" strokeWidth={2} dot={{ r: 4 }} />
          )}
        </LineChart>
      </ResponsiveContainer>
    </Box>
  );
};

export default PlayerTrendsChart; 