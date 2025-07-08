import React, { useEffect, useState, useRef } from 'react';
import PlayerCard from './PlayerCard';
import { mapBackendGradesToPlayerRatings } from '../lib/ratings';
import type { PlayerRatings } from './PlayerCard';
import { Box, Typography, Tabs, Tab } from '@mui/material';
import PlayerTrendsChart from './PlayerTrendsChart';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface PlayerDetailWithRatingsProps {
  playerId: number;
  name: string;
  position?: string;
  level?: string;
  organization?: string;
  onCardClick?: () => void;
}

interface TwoWayPlayerRatings {
  hitting: PlayerRatings;
  pitching: PlayerRatings;
  player_type: 'two_way';
  overall_rating: number;
}

const PlayerDetailWithRatings: React.FC<PlayerDetailWithRatingsProps> = ({
  playerId,
  name,
  position,
  level,
  organization,
  onCardClick,
}) => {
  const [ratings, setRatings] = useState<PlayerRatings | TwoWayPlayerRatings | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [tab, setTab] = React.useState<string>('ratings');
  const lastFetchedId = useRef<number | null>(null);

  useEffect(() => {
    if (lastFetchedId.current === playerId) return;
    lastFetchedId.current = playerId;
    setLoading(true);
    setError(null);
    fetch(`${API_BASE_URL}/player/${playerId}/ratings`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch player ratings');
        return res.json();
      })
      .then(data => {
        // Handle two-way player response
        if (data.grades && data.grades.hitting && data.grades.pitching) {
          setRatings({
            hitting: mapBackendGradesToPlayerRatings(data.grades.hitting, data),
            pitching: mapBackendGradesToPlayerRatings(data.grades.pitching, data),
            player_type: 'two_way',
            overall_rating: data.grades.hitting.overall_rating ?? data.grades.pitching.overall_rating ?? 0,
          });
        } else {
          setRatings(mapBackendGradesToPlayerRatings(data.grades, data));
        }
        setLoading(false);
      })
      .catch(err => {
        setError('Could not load ratings');
        setLoading(false);
      });
  }, [playerId]);

  // Set default tab based on player type when ratings change
  useEffect(() => {
    if (!ratings) return;
    if ((ratings as any).player_type === 'two_way') {
      setTab('batting');
    } else {
      setTab('ratings');
    }
  }, [ratings]);

  if (loading) return <div>Loading ratings...</div>;
  if (error || !ratings) return <div>{error || 'No ratings available.'}</div>;

  // Two-way player: render both charts in tabs
  if ((ratings as any).player_type === 'two_way') {
    const r = ratings as any;
    return (
      <div>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
            {name}
          </Typography>
          <Typography variant="h5" color="primary">
            Overall: {Math.round(r.overall_rating)}
          </Typography>
        </Box>
        <Tabs value={tab} onChange={(_, v) => setTab(v)}>
          <Tab label="Batting" value="batting" />
          <Tab label="Pitching" value="pitching" />
          <Tab label="Trends" value="trends" />
        </Tabs>
        <Box sx={{ mt: 2 }}>
          {tab === 'batting' && (
            <PlayerCard
              name={name + ' (Hitting)'}
              position={position}
              level={level}
              organization={organization}
              ratings={r.hitting}
              onCardClick={onCardClick}
            />
          )}
          {tab === 'pitching' && (
            <PlayerCard
              name={name + ' (Pitching)'}
              position={position}
              level={level}
              organization={organization}
              ratings={r.pitching}
              onCardClick={onCardClick}
            />
          )}
          {tab === 'trends' && (
            <PlayerTrendsChart
              hittingHistory={r.hitting.historical_overalls}
              pitchingHistory={r.pitching.historical_overalls}
              playerType="two_way"
            />
          )}
        </Box>
      </div>
    );
  }

  // One-way player: Ratings/Trends tabs
  return (
    <div>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>{name}</Typography>
      </Box>
      <Tabs value={tab} onChange={(_, v) => setTab(v)}>
        <Tab label="Ratings" value="ratings" />
        <Tab label="Trends" value="trends" />
      </Tabs>
      <Box sx={{ mt: 2 }}>
        {tab === 'ratings' && (
          <PlayerCard
            name={name}
            position={position}
            level={level}
            organization={organization}
            ratings={ratings as any}
            onCardClick={onCardClick}
          />
        )}
        {tab === 'trends' && (
          <PlayerTrendsChart
            hittingHistory={(ratings as any).historical_overalls}
            playerType={(ratings as any).player_type || 'position_player'}
          />
        )}
      </Box>
    </div>
  );
};

export default PlayerDetailWithRatings; 