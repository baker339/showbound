import React from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Typography } from '@mui/material';

interface StatRow {
  year: number | null;
  level: string;
  team: string | null;
  games?: number | null;
  at_bats?: number | null;
  hits?: number | null;
  home_runs?: number | null;
  batting_avg?: number | null;
  era?: number | null;
  innings_pitched?: number | null;
}

interface Column {
  key: string;
  label: string;
}

interface Props {
  stats: Array<Record<string, any>>;
  columns: Column[];
}

const formatHeader = (key: string) => {
  // Simple formatting: capitalize and replace underscores with spaces
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase());
};

const LifetimeStatsTable: React.FC<Props> = ({ stats, columns }) => {
  if (!stats || stats.length === 0) {
    return <Typography>No stats available.</Typography>;
  }
  return (
    <TableContainer
      component={Paper}
      sx={{
        width: '100%',
        overflowX: 'auto',
        maxWidth: '100%',
      }}
    >
      <Table size="small" sx={{ width: '100%' }}>
        <TableHead>
          <TableRow>
            {columns.map(col => (
              <TableCell key={col.key}>{col.label}</TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {stats.map((row, i) => (
            <TableRow key={i}>
              {columns.map(col => (
                <TableCell key={col.key}>
                  {row[col.key] !== undefined && row[col.key] !== null ? row[col.key] : ''}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default LifetimeStatsTable; 