"use client";
import React, { useEffect, useState } from "react";
import Link from "next/link";

interface PlayerRating {
  player_id: number;
  full_name: string;
  team: string;
  level: string;
  player_type: string;
  overall_rating: number;
  potential_rating: number;
}

const columns = [
  { key: "full_name", label: "Name" },
  { key: "team", label: "Team" },
  { key: "level", label: "Level" },
  { key: "player_type", label: "Type" },
  { key: "overall_rating", label: "Overall" },
  { key: "potential_rating", label: "Potential" },
];

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Responsive styles
const responsiveStyles = {
  controls: {
    display: 'flex',
    gap: 16,
    marginBottom: 16,
    flexWrap: 'wrap',
  } as React.CSSProperties,
  controlsMobile: {
    flexDirection: 'column' as const,
    gap: 8,
  },
  tableWrapper: {
    width: '100%',
    overflowX: 'auto' as const,
    WebkitOverflowScrolling: 'touch' as const,
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse' as const,
    minWidth: 600,
  },
  th: {
    cursor: 'pointer',
    borderBottom: '2px solid #ccc',
    padding: 8,
    background: undefined,
    fontSize: 16,
  },
  thMobile: {
    fontSize: 14,
    padding: 6,
  },
  td: {
    padding: 8,
    fontSize: 15,
  },
  tdMobile: {
    padding: 6,
    fontSize: 13,
  },
};

// Add color coding function (copied from PlayerCard)
const getRatingColor = (rating: number) => {
  if (rating >= 90) return '#4CAF50'; // Green for elite
  if (rating >= 80) return '#8BC34A'; // Light green for very good
  if (rating >= 70) return '#FFC107'; // Yellow for good
  if (rating >= 60) return '#FF9800'; // Orange for average
  return '#F44336'; // Red for below average
};

export default function AllPlayersRatingsPage() {
  const [players, setPlayers] = useState<PlayerRating[]>([]);
  const [search, setSearch] = useState("");
  const [filterLevel, setFilterLevel] = useState("");
  const [sortKey, setSortKey] = useState("overall_rating");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE_URL}/players/ratings`)
      .then((res) => res.json())
      .then((data) => setPlayers(data));
  }, []);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 600);
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const filtered = players
    .filter((p) =>
      p.full_name.toLowerCase().includes(search.toLowerCase()) &&
      (!filterLevel || p.level === filterLevel)
    )
    .sort((a, b) => {
      const aVal = a[sortKey as keyof PlayerRating];
      const bVal = b[sortKey as keyof PlayerRating];
      if (aVal === bVal) return 0;
      if (sortDir === "desc") return aVal < bVal ? 1 : -1;
      return aVal > bVal ? 1 : -1;
    });

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  };

  const uniqueLevels = Array.from(new Set(players.map((p) => p.level))).sort();

  return (
    <div style={{ padding: 24 }}>
      <h1>All Players & Ratings</h1>
      <div style={{
        ...responsiveStyles.controls,
        ...(isMobile ? responsiveStyles.controlsMobile : {}),
      }}>
        <input
          type="text"
          placeholder="Search by name..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ padding: 8, fontSize: 16 }}
        />
        <select
          value={filterLevel}
          onChange={(e) => setFilterLevel(e.target.value)}
          style={{ padding: 8, fontSize: 16 }}
        >
          <option value="">All Levels</option>
          {uniqueLevels.map((lvl) => (
            <option key={lvl} value={lvl}>
              {lvl}
            </option>
          ))}
        </select>
      </div>
      <div style={responsiveStyles.tableWrapper}>
      <table style={{
        ...responsiveStyles.table,
        minWidth: isMobile ? 400 : 600,
      }}>
        <thead>
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                onClick={() => handleSort(col.key)}
                style={{
                  ...responsiveStyles.th,
                  ...(isMobile ? responsiveStyles.thMobile : {}),
                  background: sortKey === col.key ? "#f0f0f0" : undefined,
                }}
              >
                {col.label}
                {sortKey === col.key ? (sortDir === "desc" ? " ↓" : " ↑") : ""}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {filtered.map((p) => (
            <tr key={p.player_id} style={{ borderBottom: "1px solid #eee" }}>
              <td style={{ ...responsiveStyles.td, ...(isMobile ? responsiveStyles.tdMobile : {}) }}>
                <Link
                  href={`/?playerId=${p.player_id}`}
                  style={{
                    color: 'inherit',
                    textDecoration: 'none',
                    fontWeight: 600,
                    cursor: 'pointer',
                    transition: 'background 0.2s, color 0.2s',
                    padding: '2px 4px',
                    borderRadius: 4,
                    display: 'inline-block',
                  }}
                  onMouseOver={e => (e.currentTarget.style.background = '#f5f5f5')}
                  onMouseOut={e => (e.currentTarget.style.background = 'transparent')}
                >
                  {p.full_name}
                </Link>
              </td>
              <td style={{ ...responsiveStyles.td, ...(isMobile ? responsiveStyles.tdMobile : {}) }}>{p.team}</td>
              <td style={{ ...responsiveStyles.td, ...(isMobile ? responsiveStyles.tdMobile : {}) }}>{p.level}</td>
              <td style={{ ...responsiveStyles.td, ...(isMobile ? responsiveStyles.tdMobile : {}) }}>
                {p.player_type === 'pitcher' ? 'Pitcher' :
                 p.player_type === 'position_player' ? 'Position Player' :
                 p.player_type === 'two_way' ? 'Two-Way' : p.player_type}
              </td>
              <td
                style={{
                  ...responsiveStyles.td,
                  ...(isMobile ? responsiveStyles.tdMobile : {}),
                  color: '#fff',
                  background: getRatingColor(p.overall_rating),
                  fontWeight: 700,
                  borderRadius: 4,
                  textAlign: 'center',
                  minWidth: 60,
                }}
              >
                {p.overall_rating.toFixed(1)}
              </td>
              <td style={{ ...responsiveStyles.td, ...(isMobile ? responsiveStyles.tdMobile : {}) }}>{p.potential_rating.toFixed(1)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
      {filtered.length === 0 && <div style={{ marginTop: 24 }}>No players found.</div>}
    </div>
  );
} 