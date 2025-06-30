"use client";

import { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Card, 
  CardContent, 
  Autocomplete, 
  TextField, 
  Button, 
  Divider,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
  Alert
} from '@mui/material';
import { Player } from '@/types/player';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface PlayerComparison {
  player1: Player | null;
  player2: Player | null;
  player1Stats: any;
  player2Stats: any;
  player1Ratings: any;
  player2Ratings: any;
  player1Prediction: any;
  player2Prediction: any;
}

export default function ComparePage() {
  const [players, setPlayers] = useState<Player[]>([]);
  const [comparison, setComparison] = useState<PlayerComparison>({
    player1: null,
    player2: null,
    player1Stats: null,
    player2Stats: null,
    player1Ratings: null,
    player2Ratings: null,
    player1Prediction: null,
    player2Prediction: null
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPlayers();
  }, []);

  const fetchPlayers = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/players`);
      if (!response.ok) throw new Error('Failed to fetch players');
      const data = await response.json();
      setPlayers(data);
    } catch (err) {
      setError('Failed to load players');
    }
  };

  const fetchPlayerData = async (playerId: number, playerNum: 1 | 2) => {
    setLoading(true);
    try {
      const [statsRes, ratingsRes, predictionRes] = await Promise.all([
        fetch(`${API_BASE_URL}/player/${playerId}/standard_batting`),
        fetch(`${API_BASE_URL}/player/${playerId}/ratings`),
        fetch(`${API_BASE_URL}/player/${playerId}/prediction`)
      ]);

      const stats = statsRes.ok ? await statsRes.json() : null;
      const ratings = ratingsRes.ok ? await ratingsRes.json() : null;
      const prediction = predictionRes.ok ? await predictionRes.json() : null;

      setComparison(prev => ({
        ...prev,
        [`player${playerNum}Stats`]: stats,
        [`player${playerNum}Ratings`]: ratings,
        [`player${playerNum}Prediction`]: prediction
      }));
    } catch (err) {
      setError(`Failed to load data for player ${playerNum}`);
    } finally {
      setLoading(false);
    }
  };

  const handlePlayerSelect = (player: Player | null, playerNum: 1 | 2) => {
    setComparison(prev => ({
      ...prev,
      [`player${playerNum}`]: player
    }));

    if (player) {
      fetchPlayerData(player.id, playerNum);
    }
  };

  const getLatestStats = (stats: any[]) => {
    if (!stats || stats.length === 0) return null;
    return stats.sort((a, b) => b.season - a.season)[0];
  };

  const formatStat = (value: any, isPercentage = false) => {
    if (value === null || value === undefined) return 'N/A';
    if (isPercentage) return `${(value * 100).toFixed(1)}%`;
    if (typeof value === 'number') {
      // Round WAR and similar stats to 1 decimal place
      if (value > 10 || value < -10) {
        return value.toFixed(1);
      }
      // For smaller numbers, use 2 decimal places
      return value.toFixed(2);
    }
    return value;
  };

  const getRatingColor = (rating: number) => {
    if (rating >= 80) return 'success';
    if (rating >= 70) return 'warning';
    return 'error';
  };

  return (
    <Box sx={{ p: 3, maxWidth: 1400, mx: 'auto' }}>
      <Typography variant="h4" gutterBottom>
        Player Comparison
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Player Selection */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Select Players to Compare
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Box sx={{ flex: 1, minWidth: 300 }}>
              <Autocomplete
                options={players}
                getOptionLabel={(option) => `${option.full_name} (${option.team || 'N/A'})`}
                value={comparison.player1}
                onChange={(_, newValue) => handlePlayerSelect(newValue, 1)}
                renderInput={(params) => (
                  <TextField {...params} label="Player 1" placeholder="Search for a player..." />
                )}
              />
            </Box>
            <Box sx={{ flex: 1, minWidth: 300 }}>
              <Autocomplete
                options={players}
                getOptionLabel={(option) => `${option.full_name} (${option.team || 'N/A'})`}
                value={comparison.player2}
                onChange={(_, newValue) => handlePlayerSelect(newValue, 2)}
                renderInput={(params) => (
                  <TextField {...params} label="Player 2" placeholder="Search for a player..." />
                )}
              />
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Comparison Display */}
      {comparison.player1 && comparison.player2 && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {/* Player Info Cards */}
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Card sx={{ flex: 1, minWidth: 300 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {comparison.player1.full_name}
                </Typography>
                <Typography color="text.secondary" gutterBottom>
                  {comparison.player1.team} • {comparison.player1.level}
                </Typography>
                <Chip 
                  label={comparison.player1.primary_position || 'Unknown'} 
                  size="small" 
                  sx={{ mr: 1 }}
                />
                {comparison.player1.positions?.map((pos: string, idx: number) => (
                  <Chip key={idx} label={pos} size="small" sx={{ mr: 1 }} />
                ))}
              </CardContent>
            </Card>
            <Card sx={{ flex: 1, minWidth: 300 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {comparison.player2.full_name}
                </Typography>
                <Typography color="text.secondary" gutterBottom>
                  {comparison.player2.team} • {comparison.player2.level}
                </Typography>
                <Chip 
                  label={comparison.player2.primary_position || 'Unknown'} 
                  size="small" 
                  sx={{ mr: 1 }}
                />
                {comparison.player2.positions?.map((pos: string, idx: number) => (
                  <Chip key={idx} label={pos} size="small" sx={{ mr: 1 }} />
                ))}
              </CardContent>
            </Card>
          </Box>

          {/* Stats Comparison */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Latest Season Stats
              </Typography>
              {loading ? (
                <Box display="flex" justifyContent="center" p={3}>
                  <CircularProgress />
                </Box>
              ) : (
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Stat</TableCell>
                        <TableCell align="center">{comparison.player1.full_name}</TableCell>
                        <TableCell align="center">{comparison.player2.full_name}</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {(() => {
                        const stats1 = getLatestStats(comparison.player1Stats);
                        const stats2 = getLatestStats(comparison.player2Stats);
                        
                        if (!stats1 || !stats2) {
                          return (
                            <TableRow>
                              <TableCell colSpan={3} align="center">
                                No stats available for comparison
                              </TableCell>
                            </TableRow>
                          );
                        }

                        const statFields = [
                          { key: 'season', label: 'Season' },
                          { key: 'team', label: 'Team' },
                          { key: 'g', label: 'Games' },
                          { key: 'pa', label: 'PA' },
                          { key: 'ab', label: 'AB' },
                          { key: 'h', label: 'Hits' },
                          { key: 'hr', label: 'HR' },
                          { key: 'rbi', label: 'RBI' },
                          { key: 'bb', label: 'BB' },
                          { key: 'so', label: 'SO' },
                          { key: 'sb', label: 'SB' },
                          { key: 'ba', label: 'AVG', isPercentage: true },
                          { key: 'obp', label: 'OBP', isPercentage: true },
                          { key: 'slg', label: 'SLG', isPercentage: true },
                          { key: 'ops', label: 'OPS', isPercentage: true }
                        ];

                        return statFields.map(({ key, label, isPercentage }) => (
                          <TableRow key={key}>
                            <TableCell><strong>{label}</strong></TableCell>
                            <TableCell align="center">
                              {formatStat(stats1[key], isPercentage)}
                            </TableCell>
                            <TableCell align="center">
                              {formatStat(stats2[key], isPercentage)}
                            </TableCell>
                          </TableRow>
                        ));
                      })()}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>

          {/* Ratings Comparison */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Ratings Comparison
              </Typography>
              {loading ? (
                <Box display="flex" justifyContent="center" p={3}>
                  <CircularProgress />
                </Box>
              ) : (
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Rating</TableCell>
                        <TableCell align="center">{comparison.player1.full_name}</TableCell>
                        <TableCell align="center">{comparison.player2.full_name}</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {(() => {
                        const ratings1 = comparison.player1Ratings?.grades;
                        const ratings2 = comparison.player2Ratings?.grades;
                        
                        if (!ratings1 || !ratings2) {
                          return (
                            <TableRow>
                              <TableCell colSpan={3} align="center">
                                No ratings available for comparison
                              </TableCell>
                            </TableRow>
                          );
                        }

                        const ratingFields = [
                          'contact_left', 'power_left', 'discipline', 'vision',
                          'fielding', 'arm_strength', 'speed', 'stealing',
                          'overall_rating', 'potential_rating'
                        ];

                        return ratingFields.map((key) => (
                          <TableRow key={key}>
                            <TableCell><strong>{key.replace('_', ' ').toUpperCase()}</strong></TableCell>
                            <TableCell align="center">
                              <Chip 
                                label={ratings1[key]?.toFixed(1) || 'N/A'} 
                                color={getRatingColor(ratings1[key] || 0)}
                                size="small"
                              />
                            </TableCell>
                            <TableCell align="center">
                              <Chip 
                                label={ratings2[key]?.toFixed(1) || 'N/A'} 
                                color={getRatingColor(ratings2[key] || 0)}
                                size="small"
                              />
                            </TableCell>
                          </TableRow>
                        ));
                      })()}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>

          {/* Predictions Comparison */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Predictions Comparison
              </Typography>
              {loading ? (
                <Box display="flex" justifyContent="center" p={3}>
                  <CircularProgress />
                </Box>
              ) : (
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Metric</TableCell>
                        <TableCell align="center">{comparison.player1.full_name}</TableCell>
                        <TableCell align="center">{comparison.player2.full_name}</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {(() => {
                        const pred1 = comparison.player1Prediction;
                        const pred2 = comparison.player2Prediction;
                        
                        if (!pred1 || !pred2) {
                          return (
                            <TableRow>
                              <TableCell colSpan={3} align="center">
                                No predictions available for comparison
                              </TableCell>
                            </TableRow>
                          );
                        }

                        const predictionFields = [
                          { key: 'mlb_debut_probability', label: 'MLB Debut Probability' },
                          { key: 'projected_career_war', label: 'Projected Career WAR' },
                          { key: 'current_career_war', label: 'Current Career WAR' },
                          { key: 'ceiling_comparison', label: 'Ceiling' },
                          { key: 'floor_comparison', label: 'Floor' },
                          { key: 'eta_mlb', label: 'ETA MLB' }
                        ];

                        return predictionFields.map(({ key, label }) => (
                          <TableRow key={key}>
                            <TableCell><strong>{label}</strong></TableCell>
                            <TableCell align="center">
                              {key.includes('probability') 
                                ? `${(pred1[key] * 100).toFixed(1)}%`
                                : pred1[key] || 'N/A'
                              }
                            </TableCell>
                            <TableCell align="center">
                              {key.includes('probability') 
                                ? `${(pred2[key] * 100).toFixed(1)}%`
                                : pred2[key] || 'N/A'
                              }
                            </TableCell>
                          </TableRow>
                        ));
                      })()}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Instructions */}
      {(!comparison.player1 || !comparison.player2) && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              How to Compare Players
            </Typography>
            <Typography variant="body2" color="text.secondary">
              1. Select two players from the dropdown menus above
              2. The comparison will automatically load their stats, ratings, and predictions
              3. View side-by-side comparisons of their performance metrics
            </Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  );
} 