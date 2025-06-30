// Utility to map backend grades to PlayerRatings interface

export interface PlayerRatings {
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
  // Pitcher tool ratings
  k_rating?: number;
  bb_rating?: number;
  gb_rating?: number;
  hr_rating?: number;
  command_rating?: number;
  durability_rating?: number;
  leverage_rating?: number;
}

/**
 * Map backend grades (20-80 scale, keys: hit, power, run, arm, field, overall) to PlayerRatings interface.
 * Fills missing fields with reasonable defaults or backend values where possible.
 */
export function mapBackendGradesToPlayerRatings(grades: any, extra?: { confidence?: number, potential?: number }): PlayerRatings {
  console.log('Backend grades:', grades, 'Extra:', extra);
  const mapped = {
    contact_left: grades.contact_left ?? 0,
    contact_right: grades.contact_right ?? 0,
    power_left: grades.power_left ?? 0,
    power_right: grades.power_right ?? 0,
    vision: grades.vision ?? 0,
    discipline: grades.discipline ?? 0,
    fielding: grades.fielding ?? 0,
    arm_strength: grades.arm_strength ?? 0,
    arm_accuracy: grades.arm_accuracy ?? 0,
    speed: grades.speed ?? 0,
    stealing: grades.stealing ?? 0,
    overall_rating: grades.overall_rating ?? 0,
    potential_rating: grades.potential_rating ?? 0,
    confidence_score: grades.confidence_score ?? 0,
    player_type: grades.player_type ?? undefined,
    // Pitcher tool ratings
    k_rating: grades.k_rating ?? undefined,
    bb_rating: grades.bb_rating ?? undefined,
    gb_rating: grades.gb_rating ?? undefined,
    hr_rating: grades.hr_rating ?? undefined,
    command_rating: grades.command_rating ?? undefined,
    durability_rating: grades.durability_rating ?? undefined,
    leverage_rating: grades.leverage_rating ?? undefined,
  };
  console.log('Mapped PlayerRatings:', mapped);
  return mapped;
} 