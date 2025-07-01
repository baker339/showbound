import React, { useEffect, useState } from 'react';
import PlayerCard from './PlayerCard';
import { mapBackendGradesToPlayerRatings } from '../lib/ratings';
import type { PlayerRatings } from './PlayerCard';
import { Box, Typography, Tabs, Tab } from '@mui/material';

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

  useEffect(() => {
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

  if (loading) return <div>Loading ratings...</div>;
  if (error || !ratings) return <div>{error || 'No ratings available.'}</div>;

  // Two-way player: render both charts in tabs
  if ((ratings as any).player_type === 'two_way') {
    const r = ratings as any;
    const [tab, setTab] = React.useState<'batting' | 'pitching'>('batting');
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
        </Box>
      </div>
    );
  }

  return (
    <PlayerCard
      name={name}
      position={position}
      level={level}
      organization={organization}
      ratings={ratings as any}
      onCardClick={onCardClick}
    />
  );
};

export default PlayerDetailWithRatings; 