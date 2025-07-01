import React from 'react';
import { Box, Typography } from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface HistoryEntry {
  season: number | string;
  overall: number;
}

interface PlayerTrendsChartProps {
  hittingHistory: HistoryEntry[];
  pitchingHistory?: HistoryEntry[];
  playerType: 'position_player' | 'pitcher' | 'two_way' | string;
}

const PlayerTrendsChart: React.FC<PlayerTrendsChartProps> = ({ hittingHistory, pitchingHistory, playerType }) => {
  // Prepare data for chart
  let chartData: any[] = [];
  if (playerType === 'two_way' && pitchingHistory) {
    // Merge by season
    const allSeasons = Array.from(new Set([
      ...hittingHistory.map(h => h.season),
      ...pitchingHistory.map(p => p.season),
    ])).sort();
    chartData = allSeasons.map(season => ({
      season,
      Hitting: hittingHistory.find(h => h.season === season)?.overall ?? null,
      Pitching: pitchingHistory.find(p => p.season === season)?.overall ?? null,
    }));
  } else {
    chartData = hittingHistory.map(h => ({ season: h.season, Overall: h.overall }));
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
          {playerType === 'two_way' && pitchingHistory ? (
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