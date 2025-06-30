"use client";
import './globals.css';
import { Inter } from 'next/font/google';
import { AppBar, Toolbar, Typography, Container, CssBaseline, Button, Box } from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import Link from 'next/link';

const inter = Inter({ subsets: ['latin'] });

const theme = createTheme({
  palette: {
    primary: {
      main: '#FF5C35', // FiveThirtyEight orange
      contrastText: '#fff',
    },
    background: {
      default: '#fff',
    },
    text: {
      primary: '#171717',
    },
  },
  typography: {
    fontFamily: 'Inter, Arial, Helvetica, sans-serif',
    h6: { fontWeight: 700 },
  },
});

const navLinks = [
  { label: 'Home', href: '/' },
  { label: 'Compare', href: '/compare' },
  { label: 'About', href: '/about' },
  // { label: 'Teams', href: '/teams' },
  // { label: 'Games', href: '/games' },
  // { label: 'Analytics', href: '/analytics' },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <title>Show Bound</title>
      </head>
      <body className={inter.className}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <AppBar position="static" color="inherit" elevation={1} sx={{ borderBottom: '2px solid #FF5C35' }}>
            <Toolbar sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box sx={{ width: 36, height: 36, position: 'relative', mr: 2 }}>
                {/* Orange baseball with white laces */}
                <svg width="36" height="36" viewBox="0 0 36 36">
                  <circle cx="18" cy="18" r="18" fill="#FF5C35" />
                  {/* Simple laces: two white arcs */}
                  <path d="M8 10 Q18 18 28 10" stroke="#fff" strokeWidth="2" fill="none" />
                  <path d="M8 26 Q18 18 28 26" stroke="#fff" strokeWidth="2" fill="none" />
                </svg>
              </Box>
              <Typography
                variant="h6"
                component={Link}
                href="/"
                sx={{ flexGrow: 1, fontWeight: 700, color: '#171717', letterSpacing: 1, textDecoration: 'none', cursor: 'pointer' }}
              >
                Show Bound
              </Typography>
              <Box sx={{ display: { xs: 'none', sm: 'flex' }, gap: 1 }}>
                {navLinks.map(link => (
                  <Button key={link.href} component={Link} href={link.href} color="primary" sx={{ fontWeight: 600, textTransform: 'none', fontSize: 16 }}>
                    {link.label}
                  </Button>
                ))}
              </Box>
            </Toolbar>
          </AppBar>
          <Container maxWidth="lg" sx={{ mt: 4 }}>
            {children}
          </Container>
        </ThemeProvider>
      </body>
    </html>
  );
}
