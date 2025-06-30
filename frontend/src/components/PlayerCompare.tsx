import React, { useEffect, useState } from 'react';
import { Box, Button, Card, CardContent, CircularProgress, FormControl, InputLabel, MenuItem, Select, Typography, Grid, Paper } from '@mui/material';
import PlayerCard from './PlayerCard';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

interface Player {
  id: number;
  name: string;
  position?: string;
  level?: string;
  organization?: string;
}

interface PlayerCompareResult {
  player1: {
    id: number;
    name: string;
    grades: any;
    confidence: number;
    potential: number;
  };
  player2: {
    id: number;
    name: string;
    grades: any;
    confidence: number;
    potential: number;
  };
  similarity: number;
  summary: string;
}

const PlayerCompare: React.FC = () => {
  const [players, setPlayers] = useState<Player[]>([]);
  const [player1Id, setPlayer1Id] = useState<number | ''>('');
  const [player2Id, setPlayer2Id] = useState<number | ''>('');
  const [result, setResult] = useState<PlayerCompareResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Fetch all players for selection
    fetch(`${API_BASE_URL}/prospects`)
      .then(res => res.json())
      .then(data => setPlayers(data))
      .catch(() => setPlayers([]));
  }, []);

  const handleCompare = () => {
    if (!player1Id || !player2Id || player1Id === player2Id) {
      setError('Please select two different players.');
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    fetch(`${API_BASE_URL}/ml/compare_players/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player1_id: player1Id, player2_id: player2Id })
    })
      .then(res => {
        if (!res.ok) throw new Error('Failed to compare players');
        return res.json();
      })
      .then(data => {
        setResult(data);
        setLoading(false);
      })
      .catch(() => {
        setError('Could not compare players');
        setLoading(false);
      });
  };

  return (
    <Card sx={{ maxWidth: 900, margin: 'auto', mt: 4 }}>
      <CardContent>
        <Typography variant="h5" gutterBottom>Compare Players</Typography>
        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>Player 1</InputLabel>
            <Select
              value={player1Id}
              label="Player 1"
              onChange={e => setPlayer1Id(e.target.value as number)}
            >
              {players.map(p => (
                <MenuItem key={p.id} value={p.id}>{p.name}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>Player 2</InputLabel>
            <Select
              value={player2Id}
              label="Player 2"
              onChange={e => setPlayer2Id(e.target.value as number)}
            >
              {players.map(p => (
                <MenuItem key={p.id} value={p.id}>{p.name}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <Button variant="contained" onClick={handleCompare} disabled={loading} sx={{ height: 56 }}>
            Compare
          </Button>
        </Box>
        {error && <Typography color="error" sx={{ mb: 2 }}>{error}</Typography>}
        {loading && <CircularProgress />}
        {result && (
          <Box sx={{ mt: 4 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={5}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6">{result.player1.name}</Typography>
                  <PlayerCard name={result.player1.name} ratings={{
                    contact_left: result.player1.grades.hit ?? 0,
                    contact_right: result.player1.grades.hit ?? 0,
                    power_left: result.player1.grades.power ?? 0,
                    power_right: result.player1.grades.power ?? 0,
                    vision: 50,
                    discipline: 50,
                    fielding: result.player1.grades.field ?? 0,
                    arm_strength: result.player1.grades.arm ?? 0,
                    arm_accuracy: result.player1.grades.arm ?? 0,
                    speed: result.player1.grades.run ?? 0,
                    stealing: 50,
                    overall_rating: result.player1.grades.overall ?? 0,
                    potential_rating: result.player1.potential ?? 50,
                    confidence_score: result.player1.confidence ?? 0.5,
                  }} />
                </Paper>
              </Grid>
              <Grid item xs={12} md={2}>
                <Box sx={{ textAlign: 'center', mt: 6 }}>
                  <Typography variant="h6">VS</Typography>
                  <Typography variant="body1" sx={{ mt: 2 }}>Similarity: {Math.round(result.similarity * 100)}%</Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={5}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6">{result.player2.name}</Typography>
                  <PlayerCard name={result.player2.name} ratings={{
                    contact_left: result.player2.grades.hit ?? 0,
                    contact_right: result.player2.grades.hit ?? 0,
                    power_left: result.player2.grades.power ?? 0,
                    power_right: result.player2.grades.power ?? 0,
                    vision: 50,
                    discipline: 50,
                    fielding: result.player2.grades.field ?? 0,
                    arm_strength: result.player2.grades.arm ?? 0,
                    arm_accuracy: result.player2.grades.arm ?? 0,
                    speed: result.player2.grades.run ?? 0,
                    stealing: 50,
                    overall_rating: result.player2.grades.overall ?? 0,
                    potential_rating: result.player2.potential ?? 50,
                    confidence_score: result.player2.confidence ?? 0.5,
                  }} />
                </Paper>
              </Grid>
            </Grid>
            <Box sx={{ mt: 4, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
              <Typography variant="subtitle1">Summary</Typography>
              <Typography variant="body2">{result.summary}</Typography>
            </Box>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default PlayerCompare; 