'use client';
import React, { useState, useEffect } from 'react';
import useSWR from 'swr';
import {
  Container,
  Typography,
  Box,
  Grid,
  TextField,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Paper,
  Divider,
} from '@mui/material';
import { Search, FilterList, TrendingUp, Timeline } from '@mui/icons-material';
import api from '../utils/api';
import PlayerCard from '../components/PlayerCard';
import PlayerComparison from '../components/PlayerComparison';
import MLBPrediction from '../components/MLBPrediction';
import PlayerDetailWithRatings from '../components/PlayerDetailWithRatings';
import LifetimeStatsTable from '../components/LifetimeStatsTable';

const fetcher = (url: string) => api.get(url).then(res => res.data);

interface Player {
  id: number;
  full_name: string;
  team: string;
  primary_position?: string;
  birth_date?: string;
  bats?: string;
  throws?: string;
  height?: string;
  weight?: string;
  source_url?: string;
  level?: string;
}

interface PlayerDetail {
  id: number;
  name: string;
  level: string;
  position?: string;
  organization?: string;
  graduation_year?: number;
  school?: string;
  mlb_show_ratings?: any;
  similar_players?: any[];
  mlb_success_prediction?: any;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// Canonical columns for each stat type
const battingColumns = [
  { key: 'season', label: 'Season' },
  { key: 'team', label: 'Team' },
  { key: 'lg', label: 'Lg' },
  { key: 'g', label: 'G' },
  { key: 'pa', label: 'PA' },
  { key: 'ab', label: 'AB' },
  { key: 'r', label: 'R' },
  { key: 'h', label: 'H' },
  { key: 'doubles', label: '2B' },
  { key: 'triples', label: '3B' },
  { key: 'hr', label: 'HR' },
  { key: 'rbi', label: 'RBI' },
  { key: 'sb', label: 'SB' },
  { key: 'cs', label: 'CS' },
  { key: 'bb', label: 'BB' },
  { key: 'so', label: 'SO' },
  { key: 'ba', label: 'AVG' },
  { key: 'obp', label: 'OBP' },
  { key: 'slg', label: 'SLG' },
  { key: 'ops', label: 'OPS' },
  { key: 'ops_plus', label: 'OPS+' },
];
const pitchingColumns = [
  { key: 'season', label: 'Season' },
  { key: 'team', label: 'Team' },
  { key: 'lg', label: 'Lg' },
  { key: 'g', label: 'G' },
  { key: 'gs', label: 'GS' },
  { key: 'w', label: 'W' },
  { key: 'l', label: 'L' },
  { key: 'era', label: 'ERA' },
  { key: 'ip', label: 'IP' },
  { key: 'h', label: 'H' },
  { key: 'r', label: 'R' },
  { key: 'er', label: 'ER' },
  { key: 'hr', label: 'HR' },
  { key: 'bb', label: 'BB' },
  { key: 'so', label: 'SO' },
  { key: 'whip', label: 'WHIP' },
  { key: 'era_plus', label: 'ERA+' },
];
const fieldingColumns = [
  { key: 'season', label: 'Season' },
  { key: 'team', label: 'Team' },
  { key: 'lg', label: 'Lg' },
  { key: 'pos', label: 'Pos' },
  { key: 'g', label: 'G' },
  { key: 'gs', label: 'GS' },
  { key: 'inn', label: 'Inn' },
  { key: 'po', label: 'PO' },
  { key: 'a', label: 'A' },
  { key: 'e', label: 'E' },
  { key: 'dp', label: 'DP' },
  { key: 'fld_pct', label: 'Fld%' },
  { key: 'rf9', label: 'RF/9' },
];

export default function PlayersPage() {
  const { data: players, error, isLoading } = useSWR('/players', fetcher);
  const [selectedPlayer, setSelectedPlayer] = useState<(Player & {
    primary_position?: string;
    birth_date?: string;
    bats?: string;
    throws?: string;
    height?: string;
    weight?: string;
    source_url?: string;
  }) | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLevel, setSelectedLevel] = useState('all');
  const [activeTab, setActiveTab] = useState(0);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [mlbComps, setMlbComps] = useState<any[] | null>(null);
  const [mlbCompsLoading, setMlbCompsLoading] = useState(false);
  const [mlbCompsError, setMlbCompsError] = useState<string | null>(null);
  const [prediction, setPrediction] = useState<any | null>(null);
  const [predictionLoading, setPredictionLoading] = useState(false);
  const [predictionError, setPredictionError] = useState<string | null>(null);
  const [battingStats, setBattingStats] = useState<any[]>([]);
  const [pitchingStats, setPitchingStats] = useState<any[]>([]);
  const [fieldingStats, setFieldingStats] = useState<any[]>([]);
  const [statsLoading, setStatsLoading] = useState(false);
  const [statsError, setStatsError] = useState<string | null>(null);
  const [statsLevelFilter, setStatsLevelFilter] = useState('all');

  const handlePlayerClick = async (player: Player) => {
    setLoadingDetail(true);
    try {
      const detail = await api.get(`/player/${player.id}/bio`);
      setSelectedPlayer({ id: detail.data.player_id, ...detail.data.bio });
      setActiveTab(0);
    } catch (error) {
      console.error('Error loading player detail:', error);
    }
    setLoadingDetail(false);
  };

  const levels = ['all', 'MLB', 'AAA', 'AA', 'A', 'Rookie', 'HS', 'NCAA'];

  const filteredPlayers = players?.filter((player: Player) => {
    const matchesSearch = player.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         player.team?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesLevel = selectedLevel === 'all' || (player.level && player.level.toLowerCase() === selectedLevel.toLowerCase());
    return matchesSearch && matchesLevel;
  }) || [];

  // Fetch MLB comps when Comparisons tab is active and a player is selected
  useEffect(() => {
    if (activeTab === 1 && selectedPlayer) {
      setMlbCompsLoading(true);
      setMlbCompsError(null);
      setMlbComps(null);
      fetch(`${API_BASE_URL}/player/${selectedPlayer.id}/mlb_comps`)
        .then(res => {
          if (!res.ok) throw new Error('Failed to fetch MLB comps');
          return res.json();
        })
        .then(data => {
          setMlbComps(data.comparisons);
          setMlbCompsLoading(false);
        })
        .catch(() => {
          setMlbCompsError('Could not load MLB comparisons');
          setMlbCompsLoading(false);
        });
    }
  }, [activeTab, selectedPlayer]);

  // Fetch prediction when Predictions tab is active and a player is selected
  useEffect(() => {
    if (activeTab === 2 && selectedPlayer) {
      setPredictionLoading(true);
      setPredictionError(null);
      setPrediction(null);
      fetch(`${API_BASE_URL}/player/${selectedPlayer.id}/prediction`)
        .then(res => {
          if (!res.ok) throw new Error('Failed to fetch prediction');
          return res.json();
        })
        .then(data => {
          setPrediction(data);
          setPredictionLoading(false);
        })
        .catch(() => {
          setPredictionError('Could not load MLB prediction');
          setPredictionLoading(false);
        });
    }
  }, [activeTab, selectedPlayer]);

  // Fetch stats when Stats tab is active and a player is selected
  useEffect(() => {
    if (activeTab === 3 && selectedPlayer && selectedPlayer.id) {
      setStatsLoading(true);
      setStatsError(null);
      Promise.all([
        fetch(`${API_BASE_URL}/player/${selectedPlayer.id}/standard_batting`).then(res => res.json()),
        fetch(`${API_BASE_URL}/player/${selectedPlayer.id}/standard_pitching`).then(res => res.json()),
        fetch(`${API_BASE_URL}/player/${selectedPlayer.id}/standard_fielding`).then(res => res.json()),
      ])
        .then(([batting, pitching, fielding]) => {
          setBattingStats(Array.isArray(batting) ? batting : []);
          setPitchingStats(Array.isArray(pitching) ? pitching : []);
          setFieldingStats(Array.isArray(fielding) ? fielding : []);
          setStatsLoading(false);
        })
        .catch(() => {
          setStatsError('Could not load stats');
          setStatsLoading(false);
        });
    }
  }, [activeTab, selectedPlayer]);

  // Filter stats by level
  const filterStatsByLevel = (stats: any[], level: string) => {
    if (level === 'all') {
      // For "all levels", sort by year then by level
      return stats.sort((a, b) => {
        // First sort by year (oldest to newest)
        const yearA = parseInt(a.season) || 0;
        const yearB = parseInt(b.season) || 0;
        if (yearA !== yearB) return yearA - yearB;
        
        // Then sort by level (lowest to highest)
        const levelOrder = ['Rookie', 'A', 'AA', 'AAA', 'MLB'];
        const levelA = getLevelFromLeague(a.lg);
        const levelB = getLevelFromLeague(b.lg);
        const indexA = levelOrder.indexOf(levelA);
        const indexB = levelOrder.indexOf(levelB);
        return indexA - indexB;
      });
    }
    
    // Map level to league codes
    const levelToLeagues: { [key: string]: string[] } = {
      'MLB': ['AL', 'NL'],
      'AAA': ['IL', 'PCL'],
      'AA': ['EL', 'SL', 'TL'],
      'A': ['LASE', 'SALL', 'CARL', 'FLOR', 'MIDW', 'NYPL', 'PION'],
      'Rookie': ['ARIZ', 'GULF', 'PION'],
      'HS': ['HS'],
      'NCAA': ['NCAA']
    };
    
    const targetLeagues = levelToLeagues[level] || [];
    const filteredStats = stats.filter(stat => targetLeagues.includes(stat.lg));
    
    // Sort filtered stats by year (oldest to newest)
    return filteredStats.sort((a, b) => {
      const yearA = parseInt(a.season) || 0;
      const yearB = parseInt(b.season) || 0;
      return yearA - yearB;
    });
  };

  // Helper function to get level from league code
  const getLevelFromLeague = (league: string): string => {
    const leagueToLevel: { [key: string]: string } = {
      'AL': 'MLB', 'NL': 'MLB',
      'IL': 'AAA', 'PCL': 'AAA',
      'EL': 'AA', 'SL': 'AA', 'TL': 'AA',
      'LASE': 'A', 'SALL': 'A', 'CARL': 'A', 'FLOR': 'A', 'MIDW': 'A', 'NYPL': 'A', 'PION': 'A',
      'ARIZ': 'Rookie', 'GULF': 'Rookie',
      'HS': 'HS',
      'NCAA': 'NCAA'
    };
    return leagueToLevel[league] || 'Unknown';
  };

  const filteredBattingStats = filterStatsByLevel(battingStats, statsLevelFilter);
  const filteredPitchingStats = filterStatsByLevel(pitchingStats, statsLevelFilter);
  const filteredFieldingStats = filterStatsByLevel(fieldingStats, statsLevelFilter);

  // Get unique levels from all stats
  const getAvailableLevels = (): string[] => {
    const allStats = [...battingStats, ...pitchingStats, ...fieldingStats];
    const leagues = new Set(allStats.map((stat: any) => stat.lg).filter(Boolean));
    
    const levels = new Set<string>();
    leagues.forEach((league: string) => {
      const level = getLevelFromLeague(league);
      if (level && level !== 'Unknown') levels.add(level);
    });
    
    return ['all', ...Array.from(levels).sort()];
  };

  if (isLoading) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4 }}>
        <Alert severity="error">Error loading players. Please try again.</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom sx={{ fontWeight: 'bold' }}>
          Baseball Player Analysis
        </Typography>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          Advanced scouting with MLB The Show style ratings, KNN comparisons, and AI predictions
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', gap: 3, flexDirection: { xs: 'column', md: 'row' } }}>
        {/* Left Panel - Player List */}
        <Box sx={{ width: { xs: '100%', md: '33%' } }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Players ({filteredPlayers.length})
              </Typography>
              
              {/* Search and Filters */}
              <Box sx={{ mb: 3 }}>
                <TextField
                  fullWidth
                  placeholder="Search players..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  InputProps={{
                    startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
                  }}
                  sx={{ mb: 2 }}
                />
                
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {levels.map((level) => (
                    <Chip
                      key={level}
                      label={level === 'all' ? 'All Levels' : level}
                      onClick={() => setSelectedLevel(level)}
                      color={selectedLevel === level ? 'primary' : 'default'}
                      variant={selectedLevel === level ? 'filled' : 'outlined'}
                      size="small"
                    />
                  ))}
                </Box>
              </Box>

              {/* Player List */}
              <Box sx={{ maxHeight: 600, overflow: 'auto' }}>
                {filteredPlayers.map((player: Player) => (
                  <Card
                    key={player.id}
                    sx={{
                      mb: 2,
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      '&:hover': {
                        transform: 'translateY(-2px)',
                        boxShadow: 2,
                      },
                      border: selectedPlayer?.id === player.id ? 2 : 0,
                      borderColor: 'primary.main',
                    }}
                    onClick={() => handlePlayerClick(player)}
                  >
                    <CardContent sx={{ py: 2 }}>
                      <Typography variant="subtitle1" fontWeight="bold">
                        {player.full_name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {player.team}
                      </Typography>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Box>

        {/* Right Panel - Player Detail */}
        <Box sx={{ flex: 1 }}>
          {selectedPlayer ? (
            <Card sx={{ maxWidth: 700, width: '100%' }}>
              <CardContent>
                {/* Player Header */}
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h4" gutterBottom>
                    {selectedPlayer.full_name}
                  </Typography>
                  {/* Enhanced Bio Info */}
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 1 }}>
                    {selectedPlayer.primary_position && (
                      <Typography variant="body2" color="text.secondary">
                        <b>Position:</b> {selectedPlayer.primary_position}
                      </Typography>
                    )}
                    {selectedPlayer.team && (
                      <Typography variant="body2" color="text.secondary">
                        <b>Team:</b> {selectedPlayer.team}
                      </Typography>
                    )}
                    {selectedPlayer.birth_date && (
                      <Typography variant="body2" color="text.secondary">
                        <b>Born:</b> {selectedPlayer.birth_date}
                      </Typography>
                    )}
                    {selectedPlayer.bats && (
                      <Typography variant="body2" color="text.secondary">
                        <b>Bats:</b> {selectedPlayer.bats}
                      </Typography>
                    )}
                    {selectedPlayer.throws && (
                      <Typography variant="body2" color="text.secondary">
                        <b>Throws:</b> {selectedPlayer.throws}
                      </Typography>
                    )}
                    {selectedPlayer.height && (
                      <Typography variant="body2" color="text.secondary">
                        <b>Height:</b> {selectedPlayer.height}
                      </Typography>
                    )}
                    {selectedPlayer.weight && (
                      <Typography variant="body2" color="text.secondary">
                        <b>Weight:</b> {selectedPlayer.weight}
                      </Typography>
                    )}
                    {selectedPlayer.source_url && (
                      <Typography variant="body2" color="text.secondary">
                        <b>Source:</b> <a href={selectedPlayer.source_url} target="_blank" rel="noopener noreferrer">Baseball Reference</a>
                      </Typography>
                    )}
                  </Box>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
                    {/* No level, position, organization, school for now */}
                  </Box>
                </Box>

                {/* Tabs */}
                <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
                  <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)}>
                    <Tab label="Details" />
                    <Tab label="Comparisons" />
                    <Tab label="Predictions" />
                    <Tab label="Stats" />
                  </Tabs>
                </Box>

                {/* Tab Content */}
                {activeTab === 0 && selectedPlayer && (
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      Stat-Based Ratings
                    </Typography>
                    <PlayerDetailWithRatings
                      playerId={selectedPlayer.id}
                      name={selectedPlayer.full_name}
                      position={selectedPlayer.primary_position}
                      level={undefined}
                      organization={selectedPlayer.team}
                    />
                  </Box>
                )}

                {activeTab === 1 && selectedPlayer && (
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      Similar MLB Players
                    </Typography>
                    {mlbCompsLoading && <CircularProgress />}
                    {mlbCompsError && <Typography color="error">{mlbCompsError}</Typography>}
                    {mlbComps && (
                      <PlayerComparison
                        comparisons={mlbComps}
                        prospectName={selectedPlayer.full_name}
                      />
                    )}
                  </Box>
                )}

                {activeTab === 2 && selectedPlayer && (
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      MLB Success Prediction
                    </Typography>
                    {predictionLoading && <CircularProgress />}
                    {predictionError && <Typography color="error">{predictionError}</Typography>}
                    {prediction && (
                      <MLBPrediction
                        prediction={prediction}
                        prospectName={selectedPlayer.full_name}
                      />
                    )}
                  </Box>
                )}

                {activeTab === 3 && selectedPlayer && selectedPlayer.id && (
                  statsLoading ? <div>Loading stats...</div>
                  : statsError ? <div>{statsError}</div>
                  : (
                    <>
                      {/* Stats Level Filter - moved to top */}
                      <Box sx={{ mb: 3 }}>
                        <Typography variant="h6" gutterBottom>
                          Filter by Level
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                          {getAvailableLevels().map((level: string) => (
                            <Chip
                              key={level}
                              label={level === 'all' ? 'All Levels' : level}
                              onClick={() => setStatsLevelFilter(level)}
                              color={statsLevelFilter === level ? 'primary' : 'default'}
                              variant={statsLevelFilter === level ? 'filled' : 'outlined'}
                              size="small"
                            />
                          ))}
                        </Box>
                      </Box>

                      <Typography variant="h6" sx={{ mt: 2 }}>Standard Batting</Typography>
                      <LifetimeStatsTable stats={filteredBattingStats || []} columns={battingColumns} />
                      <Typography variant="h6" sx={{ mt: 2 }}>Standard Pitching</Typography>
                      <LifetimeStatsTable stats={filteredPitchingStats || []} columns={pitchingColumns} />
                      <Typography variant="h6" sx={{ mt: 2 }}>Standard Fielding</Typography>
                      <LifetimeStatsTable stats={filteredFieldingStats || []} columns={fieldingColumns} />
                    </>
                  )
                )}

                {loadingDetail && (
                  <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                    <CircularProgress />
                  </Box>
                )}
              </CardContent>
            </Card>
          ) : (
            <Card sx={{ maxWidth: 700, width: '100%' }}>
              <CardContent>
                <Box sx={{ textAlign: 'center', py: 8 }}>
                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    Select a player to view detailed analysis
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Choose from the list on the left to see MLB The Show style ratings, 
                    similar player comparisons, and AI-powered success predictions.
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          )}
        </Box>
      </Box>
    </Container>
  );
}
