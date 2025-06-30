import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Divider,
} from '@mui/material';
import { TrendingUp, Person } from '@mui/icons-material';

interface PlayerComparison {
  id: number;
  mlb_player_id: number;
  mlb_player_name: string;
  mlb_player_team?: string;
  similarity_score: number;
  comparison_reason: string;
  comp_date: string;
}

interface PlayerComparisonProps {
  comparisons: PlayerComparison[];
  prospectName: string;
}

const PlayerComparison: React.FC<PlayerComparisonProps> = ({
  comparisons,
  prospectName,
}) => {
  const getSimilarityColor = (score: number) => {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'warning';
    return 'error';
  };

  const getSimilarityLabel = (score: number) => {
    if (score >= 0.8) return 'Very Similar';
    if (score >= 0.6) return 'Similar';
    return 'Somewhat Similar';
  };

  return (
    <Card sx={{ minWidth: 400, maxWidth: 600 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <TrendingUp sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6" component="div">
            MLB Player Comparisons
          </Typography>
        </Box>
        
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Players most similar to {prospectName} based on ML analysis
        </Typography>

        <List sx={{ width: '100%', bgcolor: 'background.paper' }}>
          {comparisons.map((comparison, index) => (
            <React.Fragment key={comparison.id}>
              <ListItem alignItems="flex-start">
                <ListItemAvatar>
                  <Avatar sx={{ bgcolor: 'primary.main' }}>
                    <Person />
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <Typography variant="subtitle1" component="span">
                        {comparison.mlb_player_name}
                      </Typography>
                      <Chip
                        label={getSimilarityLabel(comparison.similarity_score)}
                        size="small"
                        color={getSimilarityColor(comparison.similarity_score)}
                        variant="outlined"
                      />
                    </Box>
                  }
                  secondary={
                    <React.Fragment>
                      <Typography
                        component="span"
                        variant="body2"
                        color="text.primary"
                        sx={{ display: 'block', mb: 1 }}
                      >
                        {comparison.mlb_player_team && `${comparison.mlb_player_team} • `}
                        Similarity: {Math.round(comparison.similarity_score * 100)}%
                      </Typography>
                      <Typography
                        component="span"
                        variant="body2"
                        color="text.secondary"
                      >
                        {comparison.comparison_reason}
                      </Typography>
                    </React.Fragment>
                  }
                />
              </ListItem>
              {index < comparisons.length - 1 && <Divider variant="inset" component="li" />}
            </React.Fragment>
          ))}
        </List>

        <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
          <Typography variant="caption" color="text.secondary">
            Similarity scores are calculated using K-Nearest Neighbors algorithm based on 
            hitting profile, athleticism, and statistical patterns.
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default PlayerComparison; 