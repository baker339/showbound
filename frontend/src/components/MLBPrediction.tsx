import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
  Grid,
  Divider,
} from '@mui/material';
import { 
  TrendingUp, 
  Warning, 
  CheckCircle, 
  Timeline,
  Star,
  StarBorder 
} from '@mui/icons-material';

interface MLBPrediction {
  mlb_debut_probability: number;
  projected_career_war: number;
  current_career_war?: number;
  debut_date?: string;
  risk_factor: string;
  eta_mlb: number;
  ceiling_comparison: string;
  floor_comparison: string;
  hall_of_fame_probability?: number;
  debut_year?: number;
}

interface MLBPredictionProps {
  prediction: MLBPrediction;
  prospectName: string;
}

const MLBPrediction: React.FC<MLBPredictionProps> = ({
  prediction,
  prospectName,
}) => {
  const getRiskColor = (risk: string | null | undefined) => {
    if (!risk) return 'default';
    switch (risk.toLowerCase()) {
      case 'low': return 'success';
      case 'medium': return 'warning';
      case 'high': return 'error';
      default: return 'default';
    }
  };

  const getProbabilityColor = (prob: number) => {
    if (prob >= 0.8) return '#4CAF50';
    if (prob >= 0.6) return '#8BC34A';
    if (prob >= 0.4) return '#FFC107';
    return '#F44336';
  };

  const getWARColor = (war: number) => {
    if (war >= 20) return '#4CAF50'; // Hall of Fame level
    if (war >= 10) return '#8BC34A'; // All-Star level
    if (war >= 5) return '#FFC107';  // Good regular
    if (war >= 0) return '#FF9800';  // Average
    return '#F44336'; // Below average
  };

  const getWARLabel = (war: number) => {
    if (war >= 20) return 'Hall of Fame Caliber';
    if (war >= 10) return 'All-Star Level';
    if (war >= 5) return 'Good Regular';
    if (war >= 0) return 'Average Player';
    return 'Below Average';
  };

  return (
    <Card sx={{ minWidth: 400, maxWidth: 600 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Timeline sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6" component="div">
            MLB Success Prediction
          </Typography>
        </Box>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          AI-powered projection for {prospectName}'s MLB career
        </Typography>

        {/* Probability Section: Hall of Fame for MLBers, Debut for prospects */}
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="subtitle1">
              {typeof prediction.hall_of_fame_probability === 'number' ? 'Hall of Fame Probability' : 'MLB Debut Probability'}
            </Typography>
            <Typography variant="h6" sx={{ color: getProbabilityColor(typeof prediction.hall_of_fame_probability === 'number' ? prediction.hall_of_fame_probability : prediction.mlb_debut_probability) }}>
              {typeof prediction.hall_of_fame_probability === 'number'
                ? `${Math.round(prediction.hall_of_fame_probability * 100)}%`
                : `${Math.round(prediction.mlb_debut_probability * 100)}%`}
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={typeof prediction.hall_of_fame_probability === 'number'
              ? prediction.hall_of_fame_probability * 100
              : prediction.mlb_debut_probability * 100}
            sx={{
              height: 10,
              borderRadius: 5,
              backgroundColor: '#e0e0e0',
              '& .MuiLinearProgress-bar': {
                backgroundColor: getProbabilityColor(typeof prediction.hall_of_fame_probability === 'number' ? prediction.hall_of_fame_probability : prediction.mlb_debut_probability),
              },
            }}
          />
        </Box>

        <Divider sx={{ mb: 3 }} />

        {/* Career WAR Projection */}
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="subtitle1">
              Projected Career WAR
            </Typography>
            <Typography variant="h6" sx={{ color: getWARColor(prediction.projected_career_war) }}>
              {prediction.projected_career_war.toFixed(1)}
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            {getWARLabel(prediction.projected_career_war)}
          </Typography>
          <LinearProgress
            variant="determinate"
            value={Math.min(prediction.projected_career_war / 30 * 100, 100)}
            sx={{
              height: 8,
              borderRadius: 4,
              backgroundColor: '#e0e0e0',
              '& .MuiLinearProgress-bar': {
                backgroundColor: getWARColor(prediction.projected_career_war),
              },
            }}
          />
          {/* Current Career WAR */}
          {typeof prediction.current_career_war === 'number' && (
            <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="subtitle2" color="text.secondary">
                Current Career WAR:
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                {prediction.current_career_war.toFixed(1)}
              </Typography>
            </Box>
          )}
        </Box>

        <Divider sx={{ mb: 3 }} />

        {/* Key Metrics */}
        <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
          <Box sx={{ flex: 1, textAlign: 'center', p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
            <Typography variant="h6" color="primary">
              {/* Show debut_year if present, else eta_mlb or debut_date */}
              {prediction.debut_year || prediction.eta_mlb || prediction.debut_date || '—'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              MLB Debut Year
            </Typography>
          </Box>
          {/* Only show risk factor if present */}
          {prediction.risk_factor && (
            <Box sx={{ flex: 1, textAlign: 'center', p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
              <Chip
                label={prediction.risk_factor}
                color={getRiskColor(prediction.risk_factor)}
                variant="outlined"
              />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Risk Factor
              </Typography>
            </Box>
          )}
        </Box>

        <Divider sx={{ mb: 3 }} />

        {/* Ceiling and Floor */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle1" sx={{ mb: 2 }}>
            Career Outlook
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Star sx={{ color: '#FFD700', mr: 1 }} />
            <Box>
              <Typography variant="body2" fontWeight="bold">
                Ceiling: {prediction.ceiling_comparison}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Best-case scenario based on current tools and development trajectory
              </Typography>
            </Box>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <StarBorder sx={{ color: '#8B4513', mr: 1 }} />
            <Box>
              <Typography variant="body2" fontWeight="bold">
                Floor: {prediction.floor_comparison}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Realistic worst-case scenario if development stalls
              </Typography>
            </Box>
          </Box>
        </Box>

        <Box sx={{ mt: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
          <Typography variant="caption" color="text.secondary">
            Predictions are based on statistical modeling, scouting reports, and historical 
            player development patterns. Actual results may vary significantly.
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default MLBPrediction; 