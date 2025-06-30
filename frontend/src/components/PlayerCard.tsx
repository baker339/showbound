import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
  Avatar,
  Divider,
  Grid,
  Tooltip,
} from '@mui/material';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from 'recharts';

interface PlayerRatings {
  contact_left: number;
  contact_right: number;
  power_left: number;
  power_right: number;
  vision: number;
  discipline: number;
  fielding: number;
  arm_strength: number;
  arm_accuracy: number;
  speed: number;
  stealing: number;
  overall_rating: number;
  potential_rating: number;
  confidence_score: number;
  player_type?: string;
  k_rating?: number;
  bb_rating?: number;
  gb_rating?: number;
  hr_rating?: number;
  command_rating?: number;
  durability_rating?: number;
  leverage_rating?: number;
}

interface PlayerCardProps {
  name: string;
  position?: string;
  level?: string;
  organization?: string;
  ratings: PlayerRatings;
  onCardClick?: () => void;
}

const PlayerCard: React.FC<PlayerCardProps> = ({
  name,
  position,
  level,
  organization,
  ratings,
  onCardClick,
}) => {
  console.log('PlayerCard ratings prop:', ratings);
  // Prepare data for radar chart based on player type
  let radarData;
  if (ratings.player_type === 'pitcher') {
    radarData = [
      { attribute: 'K', value: ratings.k_rating ?? 0 },
      { attribute: 'BB', value: ratings.bb_rating ?? 0 },
      { attribute: 'GB', value: ratings.gb_rating ?? 0 },
      { attribute: 'HR', value: ratings.hr_rating ?? 0 },
      { attribute: 'Command', value: ratings.command_rating ?? 0 },
    ];
  } else if (ratings.player_type === 'dh') {
    radarData = [
      { attribute: 'Contact', value: (ratings.contact_left + ratings.contact_right) / 2 },
      { attribute: 'Power', value: (ratings.power_left + ratings.power_right) / 2 },
      { attribute: 'Vision', value: ratings.vision },
      { attribute: 'Discipline', value: ratings.discipline },
    ];
  } else {
    radarData = [
      { attribute: 'Contact', value: (ratings.contact_left + ratings.contact_right) / 2 },
      { attribute: 'Power', value: (ratings.power_left + ratings.power_right) / 2 },
      { attribute: 'Vision', value: ratings.vision },
      { attribute: 'Speed', value: ratings.speed },
      { attribute: 'Fielding', value: ratings.fielding },
      { attribute: 'Arm', value: (ratings.arm_strength + ratings.arm_accuracy) / 2 },
    ];
  }

  const getRatingColor = (rating: number) => {
    if (rating >= 90) return '#4CAF50'; // Green for elite
    if (rating >= 80) return '#8BC34A'; // Light green for very good
    if (rating >= 70) return '#FFC107'; // Yellow for good
    if (rating >= 60) return '#FF9800'; // Orange for average
    return '#F44336'; // Red for below average
  };

  // Use the same color scale for overall as for other ratings
  const getOverallColor = getRatingColor;

  return (
    <Card 
      sx={{ 
        minWidth: 350, 
        maxWidth: 400, 
        cursor: onCardClick ? 'pointer' : 'default',
        transition: 'transform 0.2s, box-shadow 0.2s',
        '&:hover': onCardClick ? {
          transform: 'translateY(-4px)',
          boxShadow: 4,
        } : {},
      }}
      onClick={onCardClick}
    >
      <CardContent>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Avatar sx={{ bgcolor: getOverallColor(ratings.overall_rating), mr: 2 }}>
            {name.charAt(0)}
          </Avatar>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h6" component="div">
              {name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {position} • {level} • {organization}
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" sx={{ color: getOverallColor(ratings.overall_rating), fontWeight: 'bold' }}>
              {Math.round(ratings.overall_rating)}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Overall
            </Typography>
          </Box>
        </Box>

        <Divider sx={{ mb: 2 }} />

        {/* Radar Chart */}
        <Box sx={{ height: 200, mb: 2 }}>
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="attribute" />
              <PolarRadiusAxis angle={90} domain={[0, 99]} />
              <Radar
                name="Ratings"
                dataKey="value"
                stroke={getRatingColor(ratings.overall_rating)}
                fill={getRatingColor(ratings.overall_rating)}
                fillOpacity={0.3}
              />
            </RadarChart>
          </ResponsiveContainer>
        </Box>

        {/* Key Ratings */}
        <Box sx={{ mb: 2 }}>
          {/* Show more ratings for position players */}
          {(ratings.player_type !== 'pitcher') && (
            <>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Typography variant="body2" sx={{ minWidth: 90 }}>Contact:</Typography>
                <LinearProgress variant="determinate" value={(ratings.contact_left + ratings.contact_right) / 2} sx={{ flexGrow: 1, height: 8, borderRadius: 4, backgroundColor: '#e0e0e0', '& .MuiLinearProgress-bar': { backgroundColor: getRatingColor((ratings.contact_left + ratings.contact_right) / 2) } }} />
                <Typography variant="body2" sx={{ ml: 1, minWidth: 30 }}>{Math.round((ratings.contact_left + ratings.contact_right) / 2)}</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Typography variant="body2" sx={{ minWidth: 90 }}>Power:</Typography>
                <LinearProgress variant="determinate" value={(ratings.power_left + ratings.power_right) / 2} sx={{ flexGrow: 1, height: 8, borderRadius: 4, backgroundColor: '#e0e0e0', '& .MuiLinearProgress-bar': { backgroundColor: getRatingColor((ratings.power_left + ratings.power_right) / 2) } }} />
                <Typography variant="body2" sx={{ ml: 1, minWidth: 30 }}>{Math.round((ratings.power_left + ratings.power_right) / 2)}</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Typography variant="body2" sx={{ minWidth: 90 }}>Discipline:</Typography>
                <LinearProgress variant="determinate" value={ratings.discipline} sx={{ flexGrow: 1, height: 8, borderRadius: 4, backgroundColor: '#e0e0e0', '& .MuiLinearProgress-bar': { backgroundColor: getRatingColor(ratings.discipline) } }} />
                <Typography variant="body2" sx={{ ml: 1, minWidth: 30 }}>{Math.round(ratings.discipline)}</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Typography variant="body2" sx={{ minWidth: 90 }}>Vision:</Typography>
                <LinearProgress variant="determinate" value={ratings.vision} sx={{ flexGrow: 1, height: 8, borderRadius: 4, backgroundColor: '#e0e0e0', '& .MuiLinearProgress-bar': { backgroundColor: getRatingColor(ratings.vision) } }} />
                <Typography variant="body2" sx={{ ml: 1, minWidth: 30 }}>{Math.round(ratings.vision)}</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Typography variant="body2" sx={{ minWidth: 90 }}>Speed:</Typography>
                <LinearProgress variant="determinate" value={ratings.speed} sx={{ flexGrow: 1, height: 8, borderRadius: 4, backgroundColor: '#e0e0e0', '& .MuiLinearProgress-bar': { backgroundColor: getRatingColor(ratings.speed) } }} />
                <Typography variant="body2" sx={{ ml: 1, minWidth: 30 }}>{Math.round(ratings.speed)}</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Typography variant="body2" sx={{ minWidth: 90 }}>Stealing:</Typography>
                <LinearProgress variant="determinate" value={ratings.stealing} sx={{ flexGrow: 1, height: 8, borderRadius: 4, backgroundColor: '#e0e0e0', '& .MuiLinearProgress-bar': { backgroundColor: getRatingColor(ratings.stealing) } }} />
                <Typography variant="body2" sx={{ ml: 1, minWidth: 30 }}>{Math.round(ratings.stealing)}</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Typography variant="body2" sx={{ minWidth: 90 }}>Fielding:</Typography>
                <LinearProgress variant="determinate" value={ratings.fielding} sx={{ flexGrow: 1, height: 8, borderRadius: 4, backgroundColor: '#e0e0e0', '& .MuiLinearProgress-bar': { backgroundColor: getRatingColor(ratings.fielding) } }} />
                <Typography variant="body2" sx={{ ml: 1, minWidth: 30 }}>{Math.round(ratings.fielding)}</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Typography variant="body2" sx={{ minWidth: 90 }}>Arm:</Typography>
                <LinearProgress variant="determinate" value={(ratings.arm_strength + ratings.arm_accuracy) / 2} sx={{ flexGrow: 1, height: 8, borderRadius: 4, backgroundColor: '#e0e0e0', '& .MuiLinearProgress-bar': { backgroundColor: getRatingColor((ratings.arm_strength + ratings.arm_accuracy) / 2) } }} />
                <Typography variant="body2" sx={{ ml: 1, minWidth: 30 }}>{Math.round((ratings.arm_strength + ratings.arm_accuracy) / 2)}</Typography>
              </Box>
            </>
          )}
          {/* Pitcher-specific ratings: only show granular tools */}
          {ratings.player_type === 'pitcher' && (
            <>
              {/* Pitcher Tool Ratings */}
              {typeof ratings.k_rating === 'number' && (
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Tooltip title="Strikeouts" arrow>
                    <Typography variant="body2" sx={{ minWidth: 90, cursor: 'help' }}>K:</Typography>
                  </Tooltip>
                  <LinearProgress
                    variant="determinate"
                    value={ratings.k_rating}
                    sx={{ flexGrow: 1, height: 8, borderRadius: 4, backgroundColor: '#e0e0e0', '& .MuiLinearProgress-bar': { backgroundColor: getRatingColor(ratings.k_rating!) } }}
                  />
                  <Typography variant="body2" sx={{ ml: 1, minWidth: 30 }}>{Math.round(ratings.k_rating!)}</Typography>
                </Box>
              )}
              {typeof ratings.bb_rating === 'number' && (
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Tooltip title="Control (Walks)" arrow>
                    <Typography variant="body2" sx={{ minWidth: 90, cursor: 'help' }}>BB:</Typography>
                  </Tooltip>
                  <LinearProgress
                    variant="determinate"
                    value={ratings.bb_rating}
                    sx={{ flexGrow: 1, height: 8, borderRadius: 4, backgroundColor: '#e0e0e0', '& .MuiLinearProgress-bar': { backgroundColor: getRatingColor(ratings.bb_rating!) } }}
                  />
                  <Typography variant="body2" sx={{ ml: 1, minWidth: 30 }}>{Math.round(ratings.bb_rating!)}</Typography>
                </Box>
              )}
              {typeof ratings.gb_rating === 'number' && (
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Tooltip title="Ground Ball Ability" arrow>
                    <Typography variant="body2" sx={{ minWidth: 90, cursor: 'help' }}>GB:</Typography>
                  </Tooltip>
                  <LinearProgress
                    variant="determinate"
                    value={ratings.gb_rating}
                    sx={{ flexGrow: 1, height: 8, borderRadius: 4, backgroundColor: '#e0e0e0', '& .MuiLinearProgress-bar': { backgroundColor: getRatingColor(ratings.gb_rating!) } }}
                  />
                  <Typography variant="body2" sx={{ ml: 1, minWidth: 30 }}>{Math.round(ratings.gb_rating!)}</Typography>
                </Box>
              )}
              {typeof ratings.hr_rating === 'number' && (
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Tooltip title="Home Run Suppression" arrow>
                    <Typography variant="body2" sx={{ minWidth: 90, cursor: 'help' }}>HR:</Typography>
                  </Tooltip>
                  <LinearProgress
                    variant="determinate"
                    value={ratings.hr_rating}
                    sx={{ flexGrow: 1, height: 8, borderRadius: 4, backgroundColor: '#e0e0e0', '& .MuiLinearProgress-bar': { backgroundColor: getRatingColor(ratings.hr_rating!) } }}
                  />
                  <Typography variant="body2" sx={{ ml: 1, minWidth: 30 }}>{Math.round(ratings.hr_rating!)}</Typography>
                </Box>
              )}
              {typeof ratings.command_rating === 'number' && (
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Tooltip title="Command (Run Prevention)" arrow>
                    <Typography variant="body2" sx={{ minWidth: 90, cursor: 'help' }}>Command:</Typography>
                  </Tooltip>
                  <LinearProgress
                    variant="determinate"
                    value={ratings.command_rating}
                    sx={{ flexGrow: 1, height: 8, borderRadius: 4, backgroundColor: '#e0e0e0', '& .MuiLinearProgress-bar': { backgroundColor: getRatingColor(ratings.command_rating!) } }}
                  />
                  <Typography variant="body2" sx={{ ml: 1, minWidth: 30 }}>{Math.round(ratings.command_rating!)}</Typography>
                </Box>
              )}
            </>
          )}
        </Box>

        {/* Potential and Confidence */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="body2" color="text.secondary">
              Potential: {Math.round(ratings.potential_rating)}
            </Typography>
          </Box>
          <Chip
            label={`${Math.round(ratings.confidence_score * 100)}% Confidence`}
            size="small"
            color={ratings.confidence_score > 0.8 ? 'success' : ratings.confidence_score > 0.6 ? 'warning' : 'error'}
          />
        </Box>
      </CardContent>
    </Card>
  );
};

export default PlayerCard;

export type { PlayerRatings }; 